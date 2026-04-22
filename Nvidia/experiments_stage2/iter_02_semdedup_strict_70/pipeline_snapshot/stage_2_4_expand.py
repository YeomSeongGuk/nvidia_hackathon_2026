"""Stage 2.4 - expand canonical intents into natural-language chatbot queries.

Each canonical from Stage 2.3 (e.g. "하객룩") gets expanded into N realistic
user queries that a shopping chatbot would receive (e.g. "결혼식 하객으로 갈 때 뭐
입지?"). This lets the retrieval layer match conversational queries to our
canonical intents without relying on exact keyword overlap.

Two implementations live under the same CLI:

  1. NeMo Data Designer path (default if `nemo_curator.synthetic` is
     importable) - uses `DataDesigner` + `SamplerColumn` + structured
     LLM column. This is the hackathon-sanctioned production path.

  2. Direct-call fallback - our plain `call_json` loop. Identical output,
     no extra dependency. Used automatically when NeMo Data Designer is
     not available (e.g. on macOS, or when the installed version does not
     expose the expected module).

Input:
  $STAGE_DATA_ROOT/stage_2_3/analyzed_intents.jsonl

Output:
  $STAGE_DATA_ROOT/stage_2_4/expanded_intents.jsonl

Usage:
  python -m pipelines.stage_2_4_expand                     # default 5 queries / intent
  python -m pipelines.stage_2_4_expand --n-queries 10
  python -m pipelines.stage_2_4_expand --provider friendli --force-fallback
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

from pipelines.config import Provider, data_root
from pipelines.llm_client import call_json, get_client, load_env
from pipelines.prompts import EXPAND_FEW_SHOTS, EXPAND_SYSTEM, EXPAND_USER_TEMPLATE
from pipelines.schemas import (
    AnalyzedIntent,
    DataLineage,
    ExpandedIntent,
    MappedAttribute,
)


# ---------------------------------------------------------------------------
# Helpers shared by both implementations
# ---------------------------------------------------------------------------

def _format_attrs_block(attrs: List[MappedAttribute]) -> str:
    if not attrs:
        return "(없음)"
    lines = []
    for a in attrs[:6]:  # cap the context so the prompt stays short
        lines.append(f"- {a.attribute_key}: {a.attribute_value} ({a.weight})")
    return "\n".join(lines)


def _load_analyzed(path: Path) -> List[AnalyzedIntent]:
    out: List[AnalyzedIntent] = []
    with path.open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            out.append(AnalyzedIntent.model_validate_json(line))
    return out


def _build_few_shot_block() -> str:
    """Inject the curated few-shots into the system prompt so the model
    sees real examples before producing JSON."""
    blocks = []
    for ex in EXPAND_FEW_SHOTS:
        blocks.append(
            f"Input:\n"
            f"  canonical intent: {ex['intent_keyword']}\n"
            f"  attrs: {ex['attrs_block']}\n"
            f"Output: "
            + json.dumps({"queries": ex["queries"]}, ensure_ascii=False)
        )
    return "\n\n".join(blocks)


# ---------------------------------------------------------------------------
# Fallback path: direct call_json per intent
# ---------------------------------------------------------------------------

def expand_one_intent_fallback(
    client,
    model: str,
    intent: AnalyzedIntent,
    n_queries: int,
) -> ExpandedIntent:
    user = EXPAND_USER_TEMPLATE.format(
        intent_keyword=intent.intent_keyword,
        attrs_block=_format_attrs_block(intent.mapped_attributes),
        n=n_queries,
    )
    system = EXPAND_SYSTEM + "\n\nEXAMPLES:\n" + _build_few_shot_block()
    parsed, meta = call_json(client, model, system, user, temperature=0.7)
    queries: List[str] = []
    if parsed and isinstance(parsed.get("queries"), list):
        queries = [
            str(q).strip()
            for q in parsed["queries"]
            if isinstance(q, str) and q.strip()
        ]
    # Ensure no duplicates, preserve order
    seen: set[str] = set()
    dedup: List[str] = []
    for q in queries:
        if q in seen:
            continue
        seen.add(q)
        dedup.append(q)
    return ExpandedIntent(
        intent_keyword=intent.intent_keyword,
        natural_queries=dedup[:n_queries],
        mapped_attributes=intent.mapped_attributes,
        data_lineage=intent.data_lineage,
        last_updated=dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        expansion_meta={
            "model": meta.get("model"),
            "tokens": meta.get("tokens"),
            "finish_reason": meta.get("finish_reason"),
            "strategy": "direct-call",
        },
    )


def run_fallback(
    intents: List[AnalyzedIntent],
    provider: Optional[Provider],
    n_queries: int,
) -> List[ExpandedIntent]:
    client, model = get_client(provider=provider)
    cfg = client._llm_config  # type: ignore[attr-defined]
    print(f"[stage_2_4][fallback] {cfg.describe()}", flush=True)
    out: List[ExpandedIntent] = []
    for i, intent in enumerate(intents):
        print(
            f"[{i + 1}/{len(intents)}] expanding {intent.intent_keyword!r}",
            flush=True,
        )
        out.append(expand_one_intent_fallback(client, model, intent, n_queries))
    return out


# ---------------------------------------------------------------------------
# NeMo Data Designer path (best-effort; uses whatever symbols 1.1.x exposes)
# ---------------------------------------------------------------------------

def _try_datadesigner(
    intents: List[AnalyzedIntent],
    provider: Optional[Provider],
    n_queries: int,
) -> Optional[List[ExpandedIntent]]:
    """Return None when the NeMo Data Designer API is not available.

    On success, returns the same `List[ExpandedIntent]` the fallback would
    produce, so downstream callers do not care which path was used.
    """
    try:
        # NeMo Curator ≥1.1 groups synthetic-data helpers under
        # `nemo_curator.synthetic`. The exact class names have changed
        # across releases, so we probe a few well-known ones.
        from nemo_curator import synthetic as _synth  # type: ignore
    except Exception as exc:  # noqa: BLE001
        print(f"[stage_2_4] nemo_curator.synthetic unavailable: {exc}", flush=True)
        return None

    DataDesigner = getattr(_synth, "DataDesigner", None)
    SamplerColumn = getattr(_synth, "SamplerColumn", None)
    LLMStructuredColumn = getattr(_synth, "LLMStructuredColumn", None)
    if not all([DataDesigner, SamplerColumn, LLMStructuredColumn]):
        print(
            "[stage_2_4] NeMo Data Designer classes not found on this nemo_curator"
            " build; falling back to direct call_json path.",
            flush=True,
        )
        return None

    # We drive Data Designer with our own OpenAI-compatible client so all
    # three providers (nim/friendli/vllm-offline) work uniformly.
    client, model = get_client(provider=provider)

    try:
        dd = DataDesigner(llm_client=client, llm_model=model)  # type: ignore[call-arg]
    except TypeError:
        # Older DataDesigner may want positional args; try a minimal form.
        dd = DataDesigner()  # type: ignore[call-arg]

    intent_values = [i.intent_keyword for i in intents]
    attrs_values = [_format_attrs_block(i.mapped_attributes) for i in intents]
    system = EXPAND_SYSTEM + "\n\nEXAMPLES:\n" + _build_few_shot_block()

    try:
        dd.add_column(SamplerColumn(name="intent_keyword", values=intent_values))
        dd.add_column(SamplerColumn(name="attrs_block", values=attrs_values))
        dd.add_column(
            LLMStructuredColumn(
                name="queries_obj",
                system=system,
                prompt=EXPAND_USER_TEMPLATE.replace("{n}", str(n_queries)),
                schema={
                    "type": "object",
                    "properties": {
                        "queries": {
                            "type": "array",
                            "items": {"type": "string"},
                            "minItems": n_queries,
                            "maxItems": n_queries,
                        }
                    },
                    "required": ["queries"],
                },
            )
        )
        records = dd.run(num_samples=len(intent_values))  # type: ignore[call-arg]
    except Exception as exc:  # noqa: BLE001
        print(
            f"[stage_2_4] DataDesigner API mismatch ({exc!s}); falling back.",
            flush=True,
        )
        return None

    # records is an iterable of row-dicts. Align back to the intents.
    out: List[ExpandedIntent] = []
    for intent, row in zip(intents, records):
        qobj = row.get("queries_obj") if isinstance(row, dict) else None
        queries: List[str] = []
        if isinstance(qobj, dict) and isinstance(qobj.get("queries"), list):
            queries = [str(q).strip() for q in qobj["queries"] if str(q).strip()]
        out.append(
            ExpandedIntent(
                intent_keyword=intent.intent_keyword,
                natural_queries=queries[:n_queries],
                mapped_attributes=intent.mapped_attributes,
                data_lineage=intent.data_lineage,
                last_updated=dt.datetime.now(dt.timezone.utc).strftime(
                    "%Y-%m-%dT%H:%M:%SZ"
                ),
                expansion_meta={
                    "model": model,
                    "strategy": "nemo-data-designer",
                },
            )
        )
    return out


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main(argv: List[str] | None = None) -> int:
    root = data_root()
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--input",
        default=str(root / "stage_2_3" / "analyzed_intents.jsonl"),
    )
    parser.add_argument(
        "--output",
        default=str(root / "stage_2_4" / "expanded_intents.jsonl"),
    )
    parser.add_argument(
        "--provider",
        choices=["nim", "friendli", "vllm"],
        default=None,
        help="LLM provider; falls back to $LLM_PROVIDER or nim",
    )
    parser.add_argument(
        "--n-queries",
        type=int,
        default=5,
        help="natural-language queries per canonical (default 5)",
    )
    parser.add_argument(
        "--force-fallback",
        action="store_true",
        help="skip the NeMo Data Designer path even if it is importable",
    )
    args = parser.parse_args(argv)

    load_env()

    in_path = Path(args.input)
    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    intents = _load_analyzed(in_path)
    print(f"[stage_2_4] loaded {len(intents)} analyzed intents", flush=True)
    if not intents:
        return 0

    results: Optional[List[ExpandedIntent]] = None
    if not args.force_fallback:
        results = _try_datadesigner(intents, args.provider, args.n_queries)
    if results is None:
        results = run_fallback(intents, args.provider, args.n_queries)

    with out_path.open("w", encoding="utf-8") as fh:
        for r in results:
            fh.write(r.model_dump_json() + "\n")

    print(f"\n[stage_2_4] saved {len(results)} expanded intents -> {out_path}", flush=True)
    for r in results:
        print(f"\n{r.intent_keyword}")
        for q in r.natural_queries:
            print(f"  - {q}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
