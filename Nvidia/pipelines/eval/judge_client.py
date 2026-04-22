"""Judge-side LLM client, built on top of `pipelines.llm_client`.

Why this wrapper exists:

- NVIDIA Nemotron reasoning models (Nemotron-3 Nano, Nemotron-Super,
  Nemotron-Ultra, served via NIM Cloud, Friendli, or vLLM) return
  `content=None` under json_object response-format mode on the NIM gateway
  and emit a large `reasoning_content` pass on Friendli. They all respect a
  `detailed thinking off` system-prompt prefix AND the
  `chat_template_kwargs.enable_thinking=False` extra_body option (the
  provider-default is already wired in `pipelines.config._default_extra_body`).

- Llama / Mixtral / standard instruct models accept the standard json_object
  response format as-is.

So: this wrapper inspects the judge model id via the shared
`pipelines.config.is_reasoning_model` helper, picks the right call shape,
and exposes `raw_content` in meta so the runner can log truncated outputs.
Every stage judge goes through `call_json_judge`.
"""
from __future__ import annotations

import json
from typing import Any, Dict, Optional, Tuple

from openai import OpenAI

from pipelines.config import is_reasoning_model
from pipelines.llm_client import _try_parse_json  # shared fence-tolerant parser

# Re-export so callers can introspect without touching pipelines.config.
__all__ = ["call_json_judge", "is_reasoning_model"]


# ---------------------------------------------------------------------------
# Main entry
# ---------------------------------------------------------------------------

def call_json_judge(
    client: OpenAI,
    model: str,
    system: str,
    user: str,
    temperature: float = 0.1,
    max_tokens: int = 1536,
    extra_body: Optional[Dict[str, Any]] = None,
) -> Tuple[Optional[Dict[str, Any]], Dict[str, Any]]:
    """Single-shot judge call; parses JSON.

    Returns (parsed_or_None, meta). meta includes raw_content so callers can
    log truncated/malformed outputs without poking at the OpenAI response.
    """
    # Merge provider-level extra_body (e.g. chat_template_kwargs.enable_thinking)
    cfg = getattr(client, "_llm_config", None)
    merged_extra: Dict[str, Any] = {}
    if cfg and cfg.extra_body:
        merged_extra.update(cfg.extra_body)
    if extra_body:
        merged_extra.update(extra_body)

    kwargs: Dict[str, Any] = {
        "model": model,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    # Reasoning models: skip the response_format=json_object channel because
    # the gateway truncates content to null. The prompt itself demands JSON.
    if not is_reasoning_model(model):
        kwargs["response_format"] = {"type": "json_object"}
    if merged_extra:
        kwargs["extra_body"] = merged_extra

    resp = client.chat.completions.create(**kwargs)
    content = resp.choices[0].message.content
    tokens = getattr(resp.usage, "total_tokens", None) if resp.usage else None
    finish = resp.choices[0].finish_reason
    meta = {
        "model": model,
        "tokens": tokens,
        "finish_reason": finish,
        "raw_content": content,
    }
    parsed = _try_parse_json(content or "")
    return parsed, meta
