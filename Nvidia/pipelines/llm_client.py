"""NIM / Friendli / vLLM client wrapper using the OpenAI-compatible SDK.

`get_client()` returns an `(OpenAI, model_id)` tuple using the provider
chosen via `pipelines.config.resolve_config`. The caller just does:

    client, model = get_client()
    parsed, meta = call_json(client, model, system, user)

Provider-specific tweaks (e.g. `extra_body` to disable GLM's thinking mode,
or bumping `max_tokens` for reasoning models) are carried on the client
as `client._llm_config` and applied automatically inside `call_json`.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

import httpx
from openai import OpenAI

from pipelines.config import LLMConfig, Provider, resolve_config


def load_env(path: Path = Path(".env")) -> None:
    """Minimal .env loader; never overrides already-set env vars."""
    if not path.exists():
        return
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        os.environ.setdefault(k.strip(), v.strip())


def get_client(
    provider: Optional[Provider] = None,
    model_override: Optional[str] = None,
) -> Tuple[OpenAI, str]:
    """Build an OpenAI-compatible client for the selected provider.

    Returns (client, default_model). The resolved `LLMConfig` is stashed
    on the client as `client._llm_config` so `call_json` can pick up the
    provider-specific `extra_body` and `max_tokens` without forcing every
    caller to thread them through.
    """
    cfg = resolve_config(provider=provider, model_override=model_override)
    http_client = httpx.Client(verify=cfg.verify_ssl, timeout=60.0)
    client = OpenAI(
        base_url=cfg.base_url,
        api_key=cfg.api_key or "dummy",
        http_client=http_client,
    )
    client._llm_config = cfg  # type: ignore[attr-defined]
    return client, cfg.model


def call_json(
    client: OpenAI,
    model: str,
    system: str,
    user: str,
    temperature: float = 0.3,
    max_tokens: Optional[int] = None,
    response_format_json: bool = True,
    extra_body: Optional[Dict[str, Any]] = None,
) -> Tuple[Optional[Dict[str, Any]], Dict[str, Any]]:
    """Call the model and parse JSON. Returns (parsed_or_None, meta).

    `max_tokens` and `extra_body` default to whatever the client's
    `LLMConfig` says, so callers can usually just pass (client, model,
    system, user).
    """
    cfg: Optional[LLMConfig] = getattr(client, "_llm_config", None)
    if max_tokens is None:
        max_tokens = cfg.max_tokens if cfg else 2048
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
    if response_format_json:
        kwargs["response_format"] = {"type": "json_object"}
    if merged_extra:
        kwargs["extra_body"] = merged_extra

    resp = client.chat.completions.create(**kwargs)
    content = resp.choices[0].message.content or ""
    meta = {
        "model": model,
        "tokens": getattr(resp.usage, "total_tokens", None) if resp.usage else None,
        "finish_reason": resp.choices[0].finish_reason,
    }
    parsed = _try_parse_json(content)
    return parsed, meta


def _try_parse_json(text: str) -> Optional[Dict[str, Any]]:
    """Attempt to parse JSON; tolerate common wrapping like ```json ... ```."""
    text = text.strip()
    if not text:
        return None
    if text.startswith("```"):
        lines = text.splitlines()
        if lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].startswith("```"):
            lines = lines[:-1]
        text = "\n".join(lines).strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1 and end > start:
            try:
                return json.loads(text[start : end + 1])
            except json.JSONDecodeError:
                return None
        return None
