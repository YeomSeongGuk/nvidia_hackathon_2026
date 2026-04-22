"""Stage 2.1 - per-document intent/attribute extraction.

Stage 2 is the analysis phase; within it, Stage 2.1 does one LLM call per
curated doc to extract a customer-surface intent plus concrete attributes.

Supports three OpenAI-compatible LLM backends via `pipelines.config`:
  - nim         (NVIDIA NIM Cloud)
  - friendli    (FriendliAI serverless)
  - vllm        (self-hosted vLLM on the GPU node)

At scale we process many curated docs concurrently via asyncio. The sync
path is kept for small smoke tests.

Input:
  --input can be either a .jsonl file OR a directory; in the directory
  case we glob every *.jsonl inside it. Default is
  `$STAGE_DATA_ROOT/stage_1_2/` (Stage 1.2 writes its curated output here).

Output:
  A single JSONL file at --output. Default is
  `$STAGE_DATA_ROOT/stage_2_1/stage_2_1_extracted.jsonl`.

Post-hoc enforcement:
  If the LLM says `raw_intent == "general_wear"` but still fills in
  attribute values, we zero the attributes out. Some models (e.g. GLM-5.1)
  can not help themselves and will hallucinate attrs even when the text
  is clearly non-fashion; we make the rule unambiguous in code.

Usage:
  # small smoke test, one-at-a-time
  python -m pipelines.stage_2_1_extract --limit 5 --sync

  # full async batch run (default concurrency 10)
  python -m pipelines.stage_2_1_extract
  python -m pipelines.stage_2_1_extract --provider friendli --concurrency 20
"""
from __future__ import annotations

import argparse
import asyncio
import json
import sys
import time
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

import httpx
from openai import AsyncOpenAI
from pydantic import ValidationError

from pipelines.config import Provider, data_root, resolve_config
from pipelines.llm_client import _try_parse_json, call_json, get_client, load_env
from pipelines.prompts import EXTRACT_SYSTEM, EXTRACT_USER_TEMPLATE
from pipelines.schemas import Attributes, CuratedDoc, ExtractedIntent


def iter_curated(path: Path) -> Iterable[CuratedDoc]:
    """Yield CuratedDoc from a single .jsonl file or every .jsonl in a directory."""
    if path.is_dir():
        files = sorted(path.glob("*.jsonl"))
        if not files:
            raise FileNotFoundError(f"no .jsonl files under {path}")
    else:
        files = [path]
    for f in files:
        with f.open(encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                yield CuratedDoc.model_validate_json(line)


def _sanitize_intent(value: Optional[str]) -> str:
    """Reject ellipsis / punctuation-only / empty; fall back to general_wear."""
    if not value:
        return "general_wear"
    v = value.strip().strip("\"'`")
    if not v:
        return "general_wear"
    has_meaningful = any(ch.isalnum() or "\uac00" <= ch <= "\ud7a3" for ch in v)
    return v if has_meaningful else "general_wear"


def _to_extracted(
    doc: CuratedDoc,
    parsed: Dict[str, Any],
    meta: Dict[str, Any],
) -> ExtractedIntent:
    """Build an ExtractedIntent and enforce the 'general_wear → null attrs' rule."""
    attrs_raw = parsed.get("attributes") or {}
    attrs = Attributes(
        material=attrs_raw.get("material"),
        fit=attrs_raw.get("fit"),
        color=attrs_raw.get("color"),
        style=attrs_raw.get("style"),
        season=attrs_raw.get("season"),
    )
    raw_intent = _sanitize_intent(parsed.get("raw_intent"))
    # Post-hoc: if the LLM reported "general_wear" but still filled any
    # attribute, treat those as hallucinations and drop them.
    if raw_intent.lower() == "general_wear":
        attrs = Attributes()
    # LLMs occasionally return `extracted_keywords` as a single string or a
    # dict instead of a list; coerce into List[str] so a malformed output
    # only costs us that one doc's keywords, not the entire batch.
    raw_kw = parsed.get("extracted_keywords")
    if isinstance(raw_kw, list):
        kw_list = [str(x) for x in raw_kw if x is not None]
    elif isinstance(raw_kw, str) and raw_kw.strip():
        kw_list = [raw_kw.strip()]
    else:
        kw_list = []
    return ExtractedIntent(
        source_curated_id=doc.curated_id,
        raw_intent=raw_intent,
        attributes=attrs,
        sentiment=(parsed.get("sentiment") or "neutral").strip().lower(),
        extracted_keywords=kw_list,
        source_quality_score=doc.quality_score,
        llm_meta=meta,
    )


# --- sync path ---------------------------------------------------------------

def extract_one(client, model: str, doc: CuratedDoc) -> ExtractedIntent:
    user = EXTRACT_USER_TEMPLATE.format(text=doc.clean_text)
    parsed, meta = call_json(client, model, EXTRACT_SYSTEM, user)
    if parsed is None:
        raise RuntimeError(f"failed to parse JSON for {doc.curated_id}")
    return _to_extracted(doc, parsed, meta)


# --- async path --------------------------------------------------------------

def _build_async_client(provider: Optional[Provider] = None):
    cfg = resolve_config(provider=provider)
    http_client = httpx.AsyncClient(verify=cfg.verify_ssl, timeout=60.0)
    client = AsyncOpenAI(
        base_url=cfg.base_url,
        api_key=cfg.api_key or "dummy",
        http_client=http_client,
    )
    return client, cfg


async def _call_async(
    client: AsyncOpenAI,
    model: str,
    system: str,
    user: str,
    max_tokens: int,
    extra_body: Optional[Dict[str, Any]],
):
    kwargs: Dict[str, Any] = {
        "model": model,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        "temperature": 0.3,
        "max_tokens": max_tokens,
        "response_format": {"type": "json_object"},
    }
    if extra_body:
        kwargs["extra_body"] = extra_body
    resp = await client.chat.completions.create(**kwargs)
    content = resp.choices[0].message.content or ""
    meta = {
        "model": model,
        "tokens": getattr(resp.usage, "total_tokens", None) if resp.usage else None,
        "finish_reason": resp.choices[0].finish_reason,
    }
    return _try_parse_json(content), meta


async def extract_one_async(
    sem: asyncio.Semaphore,
    client: AsyncOpenAI,
    cfg,
    doc: CuratedDoc,
) -> ExtractedIntent | Exception:
    user = EXTRACT_USER_TEMPLATE.format(text=doc.clean_text)
    async with sem:
        try:
            parsed, meta = await _call_async(
                client,
                cfg.model,
                EXTRACT_SYSTEM,
                user,
                max_tokens=cfg.max_tokens,
                extra_body=cfg.extra_body or None,
            )
        except Exception as exc:  # noqa: BLE001
            return exc
    if parsed is None:
        return RuntimeError(f"failed to parse JSON for {doc.curated_id}")
    return _to_extracted(doc, parsed, meta)


async def run_async(
    input_path: Path,
    output_path: Path,
    provider: Optional[Provider],
    concurrency: int,
    limit: int,
) -> tuple[int, int]:
    client, cfg = _build_async_client(provider=provider)
    try:
        docs = list(iter_curated(input_path))
        if limit:
            docs = docs[:limit]
        print(
            f"[stage_2_1] {cfg.describe()} docs={len(docs)} concurrency={concurrency}",
            flush=True,
        )
        sem = asyncio.Semaphore(concurrency)
        tasks = [extract_one_async(sem, client, cfg, d) for d in docs]

        ok = fail = 0
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with output_path.open("w", encoding="utf-8") as out_fh:
            for i, coro in enumerate(asyncio.as_completed(tasks)):
                result = await coro
                if isinstance(result, BaseException):
                    fail += 1
                    print(f"[{i + 1:04d}] ERR {result}", flush=True)
                else:
                    out_fh.write(result.model_dump_json() + "\n")
                    out_fh.flush()
                    ok += 1
                    if (ok + fail) % 50 == 0 or (ok + fail) == len(tasks):
                        print(
                            f"[{ok + fail:04d}/{len(tasks)}] ok={ok} fail={fail}",
                            flush=True,
                        )
        return ok, fail
    finally:
        await client.close()


# --- CLI ---------------------------------------------------------------------

def main(argv: List[str] | None = None) -> int:
    root = data_root()
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--input",
        default=str(root / "stage_1_2"),
        help="path to a .jsonl file OR a directory of .jsonl files",
    )
    parser.add_argument(
        "--output",
        default=str(root / "stage_2_1" / "stage_2_1_extracted.jsonl"),
        help="output JSONL path",
    )
    parser.add_argument(
        "--provider",
        choices=["nim", "friendli", "vllm"],
        default=None,
        help="LLM provider; falls back to $LLM_PROVIDER or nim",
    )
    parser.add_argument("--limit", type=int, default=0, help="0 = all")
    parser.add_argument(
        "--concurrency", type=int, default=10, help="async in-flight requests"
    )
    parser.add_argument(
        "--sync",
        action="store_true",
        help="run one-at-a-time (useful for debugging)",
    )
    parser.add_argument(
        "--sleep",
        type=float,
        default=0.0,
        help="seconds between calls in --sync mode (rate-limit guard)",
    )
    args = parser.parse_args(argv)

    load_env()

    in_path = Path(args.input)
    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    if args.sync:
        client, model = get_client(provider=args.provider)
        cfg = client._llm_config  # type: ignore[attr-defined]
        print(f"[stage_2_1] SYNC {cfg.describe()}", flush=True)

        ok = fail = 0
        t0 = time.time()
        with out_path.open("w", encoding="utf-8") as out_fh:
            for i, doc in enumerate(iter_curated(in_path)):
                if args.limit and i >= args.limit:
                    break
                try:
                    extracted = extract_one(client, model, doc)
                    out_fh.write(extracted.model_dump_json() + "\n")
                    out_fh.flush()
                    ok += 1
                    print(
                        f"[{i + 1:04d}] OK  {doc.curated_id} -> intent={extracted.raw_intent!r}",
                        flush=True,
                    )
                except (ValidationError, RuntimeError, Exception) as exc:
                    fail += 1
                    print(f"[{i + 1:04d}] ERR {doc.curated_id}: {exc}", flush=True)
                if args.sleep:
                    time.sleep(args.sleep)
        print(f"\nsync done: ok={ok} fail={fail} time={time.time() - t0:.1f}s", flush=True)
        return 0 if fail == 0 else 2

    # async path (default)
    ok, fail = asyncio.run(
        run_async(
            in_path,
            out_path,
            provider=args.provider,
            concurrency=args.concurrency,
            limit=args.limit,
        )
    )
    print(f"\ndone: ok={ok} fail={fail} -> {out_path}", flush=True)
    return 0 if fail == 0 else 2


if __name__ == "__main__":
    sys.exit(main())
