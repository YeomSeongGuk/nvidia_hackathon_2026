"""Adapter that lets a local `vllm.LLM` object look like an OpenAI client.

Motivation
----------
The rest of the pipeline (`pipelines.stage_2_1_extract`, `stage_2_2_canonicalize`)
is written against an OpenAI-compatible SDK: it calls
`client.chat.completions.create(model=..., messages=..., ...)` and reads
`resp.choices[0].message.content`. That works for NIM / FriendliAI / a vLLM
OpenAI *server*, but NOT for an in-process `vllm.LLM` (offline inference).

This module wraps a live `vllm.LLM` so the same pipeline code can drive it
inside a Jupyter notebook on the GPU node without any network round-trip.

Usage (inside a notebook, after you did `llm = LLM(model=..., ...)`):

    from pipelines.vllm_adapter import VLLMOfflineClient
    from pipelines.stage_2_1_extract import extract_one
    from pipelines.schemas import CuratedDoc

    client = VLLMOfflineClient(llm, model_name="nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B-BF16")
    doc = CuratedDoc.model_validate_json(line)
    result = extract_one(client, client._llm_config.model, doc)

Batch helper:

    from pipelines.vllm_adapter import extract_batch_vllm_offline
    results = extract_batch_vllm_offline(llm, "nvidia/...-30B-A3B-BF16", docs)

The adapter performs ONE vLLM call per `create()`; it is correct, but at
scale you should prefer `extract_batch_vllm_offline` which feeds every doc
into a single `llm.chat([[...], [...], ...])` batch and lets vLLM pack the
GPU properly.
"""
from __future__ import annotations

import json
from types import SimpleNamespace
from typing import Any, Dict, List, Optional

from pipelines.config import LLMConfig
from pipelines.llm_client import _try_parse_json
from pipelines.prompts import EXTRACT_SYSTEM, EXTRACT_USER_TEMPLATE
from pipelines.schemas import Attributes, CuratedDoc, ExtractedIntent


# ---------------------------------------------------------------------------
# Duck-typed OpenAI response objects
# ---------------------------------------------------------------------------

def _fake_openai_response(
    content: str,
    model: str,
    finish_reason: str,
    prompt_tokens: int,
    completion_tokens: int,
):
    msg = SimpleNamespace(content=content, reasoning_content=None)
    choice = SimpleNamespace(message=msg, finish_reason=finish_reason)
    usage = SimpleNamespace(
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        total_tokens=prompt_tokens + completion_tokens,
    )
    return SimpleNamespace(choices=[choice], usage=usage, model=model)


# ---------------------------------------------------------------------------
# Client surface: chat.completions.create(...)
# ---------------------------------------------------------------------------

class _VLLMCompletions:
    def __init__(self, llm, default_model: str):
        self.llm = llm
        self.default_model = default_model

    def create(
        self,
        model: Optional[str] = None,
        messages: Optional[List[Dict[str, str]]] = None,
        temperature: float = 0.3,
        max_tokens: int = 2048,
        response_format: Optional[Dict[str, Any]] = None,  # noqa: ARG002
        extra_body: Optional[Dict[str, Any]] = None,  # noqa: ARG002
        **_kwargs: Any,
    ):
        from vllm import SamplingParams  # local import; vllm is heavy

        if not messages:
            raise ValueError("messages are required")
        sampling = SamplingParams(
            temperature=temperature,
            max_tokens=max_tokens,
        )
        # vllm.LLM.chat accepts a list-of-conversations; we send one batch of 1.
        outputs = self.llm.chat([messages], sampling_params=sampling)
        out = outputs[0]
        gen = out.outputs[0]
        content = gen.text or ""
        finish_reason = getattr(gen, "finish_reason", "stop") or "stop"
        return _fake_openai_response(
            content=content,
            model=model or self.default_model,
            finish_reason=finish_reason,
            prompt_tokens=len(out.prompt_token_ids or []),
            completion_tokens=len(gen.token_ids or []),
        )


class _VLLMChat:
    def __init__(self, llm, default_model: str):
        self.completions = _VLLMCompletions(llm, default_model)


class VLLMOfflineClient:
    """OpenAI-compatible facade over a live `vllm.LLM` object.

    Exposes `client.chat.completions.create(...)` exactly like the OpenAI
    SDK, and carries an `_llm_config` attribute so `pipelines.llm_client.
    call_json` can pick up `max_tokens` and `extra_body` defaults the same
    way it does for real OpenAI clients.
    """

    def __init__(
        self,
        llm,
        model_name: str,
        extra_body: Optional[Dict[str, Any]] = None,
        max_tokens: int = 2048,
    ):
        self.llm = llm
        self.chat = _VLLMChat(llm, model_name)
        self._llm_config = LLMConfig(
            provider="vllm",
            base_url="vllm://local",
            api_key=None,
            model=model_name,
            verify_ssl=True,
            extra_body=dict(extra_body or {}),
            max_tokens=max_tokens,
        )


# ---------------------------------------------------------------------------
# Batch helper: run Stage 2.1 over many docs in a SINGLE vLLM batch call.
# ---------------------------------------------------------------------------

def extract_batch_vllm_offline(
    llm,
    model_name: str,
    docs: List[CuratedDoc],
    temperature: float = 0.3,
    max_tokens: int = 2048,
) -> List[ExtractedIntent]:
    """One `llm.chat([[...], [...], ...])` call over all docs, returns Stage 2.1
    `ExtractedIntent` records with the usual `general_wear → null attrs`
    enforcement applied.

    Skips (logs) any doc whose response fails to parse as JSON; they do NOT
    appear in the returned list.
    """
    from vllm import SamplingParams

    # Avoid a circular import at module load time
    from pipelines.stage_2_1_extract import _sanitize_intent

    sampling = SamplingParams(temperature=temperature, max_tokens=max_tokens)
    messages_list = [
        [
            {"role": "system", "content": EXTRACT_SYSTEM},
            {
                "role": "user",
                "content": EXTRACT_USER_TEMPLATE.format(text=doc.clean_text),
            },
        ]
        for doc in docs
    ]
    outputs = llm.chat(messages_list, sampling_params=sampling)

    results: List[ExtractedIntent] = []
    for doc, out in zip(docs, outputs):
        gen = out.outputs[0]
        parsed = _try_parse_json(gen.text or "")
        if parsed is None:
            print(f"[vllm] parse_fail {doc.curated_id}")
            continue
        attrs_raw = parsed.get("attributes") or {}
        attrs = Attributes(
            material=attrs_raw.get("material"),
            fit=attrs_raw.get("fit"),
            color=attrs_raw.get("color"),
            style=attrs_raw.get("style"),
            season=attrs_raw.get("season"),
        )
        raw_intent = _sanitize_intent(parsed.get("raw_intent"))
        if raw_intent.lower() == "general_wear":
            attrs = Attributes()
        raw_kw = parsed.get("extracted_keywords")
        if isinstance(raw_kw, list):
            kw_list = [str(x) for x in raw_kw if x is not None]
        elif isinstance(raw_kw, str) and raw_kw.strip():
            kw_list = [raw_kw.strip()]
        else:
            kw_list = []
        results.append(
            ExtractedIntent(
                source_curated_id=doc.curated_id,
                raw_intent=raw_intent,
                attributes=attrs,
                sentiment=(parsed.get("sentiment") or "neutral").strip().lower(),
                extracted_keywords=kw_list,
                source_quality_score=doc.quality_score,
                llm_meta={
                    "model": model_name,
                    "tokens": len((out.prompt_token_ids or []))
                    + len((gen.token_ids or [])),
                    "finish_reason": getattr(gen, "finish_reason", "stop"),
                },
            )
        )
    return results


def write_jsonl(path, records: List[ExtractedIntent]) -> None:
    """Small convenience so the notebook can persist Stage 2.1 output
    without reimplementing the JSONL write."""
    from pathlib import Path

    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("w", encoding="utf-8") as fh:
        for r in records:
            fh.write(r.model_dump_json() + "\n")


# ---------------------------------------------------------------------------
# Batch helper: Stage 2.4 - expand canonical intents into natural queries
# ---------------------------------------------------------------------------

def expand_batch_vllm_offline(
    llm,
    model_name: str,
    intents,  # List[AnalyzedIntent]; avoided at module-scope for lazy import
    n_queries: int = 5,
    temperature: float = 0.7,
    max_tokens: int = 2048,
):
    """Stage 2.4: expand every canonical into N natural-language queries in
    a SINGLE `llm.chat(...)` batch. Returns `List[ExpandedIntent]`.

    Fails open: if the model returns non-JSON for a given intent, that
    intent still appears in the output with `natural_queries=[]` and a
    parse_fail note in `expansion_meta`.
    """
    import datetime as dt

    from vllm import SamplingParams

    from pipelines.prompts import (
        EXPAND_FEW_SHOTS,
        EXPAND_SYSTEM,
        EXPAND_USER_TEMPLATE,
    )
    from pipelines.schemas import ExpandedIntent
    from pipelines.stage_2_4_expand import _build_few_shot_block, _format_attrs_block

    system = EXPAND_SYSTEM + "\n\nEXAMPLES:\n" + _build_few_shot_block()
    sampling = SamplingParams(temperature=temperature, max_tokens=max_tokens)

    messages_list = [
        [
            {"role": "system", "content": system},
            {
                "role": "user",
                "content": EXPAND_USER_TEMPLATE.format(
                    intent_keyword=intent.intent_keyword,
                    attrs_block=_format_attrs_block(intent.mapped_attributes),
                    n=n_queries,
                ),
            },
        ]
        for intent in intents
    ]
    outputs = llm.chat(messages_list, sampling_params=sampling)

    now = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    results = []
    for intent, out in zip(intents, outputs):
        gen = out.outputs[0]
        parsed = _try_parse_json(gen.text or "")
        queries: List[str] = []
        parse_ok = False
        if parsed and isinstance(parsed.get("queries"), list):
            seen: set[str] = set()
            for q in parsed["queries"]:
                if not isinstance(q, str):
                    continue
                s = q.strip()
                if s and s not in seen:
                    seen.add(s)
                    queries.append(s)
            queries = queries[:n_queries]
            parse_ok = bool(queries)
        results.append(
            ExpandedIntent(
                intent_keyword=intent.intent_keyword,
                natural_queries=queries,
                mapped_attributes=intent.mapped_attributes,
                data_lineage=intent.data_lineage,
                last_updated=now,
                expansion_meta={
                    "model": model_name,
                    "tokens": len((out.prompt_token_ids or []))
                    + len((gen.token_ids or [])),
                    "finish_reason": getattr(gen, "finish_reason", "stop"),
                    "strategy": "vllm-offline-batch",
                    "parse_ok": parse_ok,
                },
            )
        )
    return results
