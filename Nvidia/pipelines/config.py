"""LLM provider configuration + data-root helper.

Supports three OpenAI-compatible backends:

- `nim`      : NVIDIA NIM Cloud API (Nemotron family, ~1k free credits)
- `friendli` : FriendliAI serverless endpoints (GLM, Llama, Mixtral, etc.)
- `vllm`     : self-hosted vLLM on the GPU node (any HF model)

Friendli's reasoning models (e.g. GLM-5.1) emit a large
`reasoning_content` field by default; if we keep the default budget,
`content` can be truncated mid-JSON. The config exposes `extra_body`
so callers can disable thinking for extraction tasks:

    extra_body = {"chat_template_kwargs": {"enable_thinking": False}}

This is automatically injected for Friendli + any GLM model; override via
`LLM_EXTRA_BODY` env var (JSON-encoded) if needed.

Required env vars per provider:
  nim:
    NVIDIA_API_KEY          (required)
  friendli:
    FRIENDLI_API_KEY        (required)
    FRIENDLI_BASE_URL       (optional, default https://api.friendli.ai/serverless/v1)
  vllm:
    VLLM_BASE_URL           (optional, default http://localhost:8000/v1)
    VLLM_API_KEY            (optional, default "dummy")
    VLLM_MODEL              (required)

Shared:
  LLM_MODEL                 overrides model for any provider
  LLM_EXTRA_BODY            JSON-encoded dict, merged on top of provider defaults
  LLM_VERIFY_SSL=0          disables TLS verify (corp network hack)

Data-root:
  STAGE_DATA_ROOT           directory that holds /stage_1_2/, /stage_2_1/, ...
                            default = ~/data
"""
from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Literal, Optional

Provider = Literal["nim", "friendli", "vllm"]


@dataclass
class LLMConfig:
    provider: Provider
    base_url: str
    api_key: Optional[str]
    model: str
    verify_ssl: bool = True
    extra_body: Dict[str, Any] = field(default_factory=dict)
    max_tokens: int = 2048

    def describe(self) -> str:
        masked = (self.api_key[:8] + "...") if self.api_key else "<none>"
        extra = f"extra_body={self.extra_body}" if self.extra_body else ""
        return (
            f"provider={self.provider} base_url={self.base_url} "
            f"model={self.model} api_key={masked} "
            f"max_tokens={self.max_tokens} verify_ssl={self.verify_ssl} {extra}"
        ).strip()


_DEFAULT_NIM_MODEL = "nvidia/nemotron-3-nano-30b-a3b"
_DEFAULT_FRIENDLI_MODEL = "meta-llama-3.1-8b-instruct"
_DEFAULT_FRIENDLI_BASE = "https://api.friendli.ai/serverless/v1"
_DEFAULT_VLLM_BASE = "http://localhost:8000/v1"


def _env_bool(name: str, default: bool) -> bool:
    raw = os.environ.get(name)
    if raw is None:
        return default
    return raw not in ("0", "false", "False", "")


def _parse_extra_body_env() -> Dict[str, Any]:
    raw = os.environ.get("LLM_EXTRA_BODY")
    if not raw:
        return {}
    try:
        val = json.loads(raw)
        return val if isinstance(val, dict) else {}
    except json.JSONDecodeError:
        return {}


# Model-id fragments (lowercase) that identify a reasoning-style model that
# emits a `reasoning_content` pass by default and benefits from being
# explicitly told to skip it. Covers NIM, Friendli and vLLM-served variants.
#
# Important: "nemotron-mini" and "nemotron-4-340b-instruct" are NOT reasoning
# models; only the Nano-A3B and llama-derived Nemotron-Super/Ultra lines are.
_REASONING_MODEL_FRAGMENTS = (
    "nemotron-3-nano",                  # NIM: nemotron-3-nano-30b-a3b
                                         # vLLM: NVIDIA-Nemotron-3-Nano-30B-A3B-BF16/FP8
    "nemotron-3-super",                 # vLLM: NVIDIA-Nemotron-3-Super-120B-A12B-FP8
    "llama-3.1-nemotron-ultra",         # NIM nvidia/llama-3.1-nemotron-ultra-*
    "llama-3.3-nemotron-super",         # NIM nvidia/llama-3.3-nemotron-super-*
    "llama-3.1-nemotron-70b-instruct",
    "glm",                              # Friendli GLM-5 / GLM-5.1 (reasoning_content)
    "deepseek-v3",                      # Friendli deepseek-ai/DeepSeek-V3.2 (thinking variant)
    "qwen3",                            # Friendli Qwen/Qwen3-235B-A22B-* (enable_thinking)
    "exaone",                           # Friendli LGAI-EXAONE/K-EXAONE-* (reasoning)
)


def is_reasoning_model(model: str) -> bool:
    """True when the model requires `enable_thinking=False` for clean JSON out.

    Case-insensitive substring match on the model id. Shared by every client
    (extraction + eval) so the reasoning-mode workaround is applied exactly
    once, in one place.
    """
    m = (model or "").lower()
    return any(frag in m for frag in _REASONING_MODEL_FRAGMENTS)


def _default_extra_body(provider: Provider, model: str) -> Dict[str, Any]:
    """Baked-in per-model tweaks so callers do not have to remember them.

    The main baked-in tweak is `chat_template_kwargs.enable_thinking=False`
    for reasoning models (GLM, Nemotron-3 Nano, Nemotron-Super/Ultra). The
    `chat_template_kwargs` channel is a convention understood by Friendli's
    gateway, vLLM's `--enable-auto-tool-choice`-equivalent chat templates,
    and several Nemotron deployments; passing it to NIM is a no-op when the
    gateway does not recognise it.
    """
    if is_reasoning_model(model):
        return {"chat_template_kwargs": {"enable_thinking": False}}
    return {}


def resolve_config(
    provider: Optional[Provider] = None,
    model_override: Optional[str] = None,
) -> LLMConfig:
    """Resolve an `LLMConfig` from arguments + env vars.

    Raises RuntimeError if the chosen provider is missing its API key.
    """
    prov = (
        provider
        or os.environ.get("LLM_PROVIDER")
        or "nim"
    ).lower()

    if prov not in ("nim", "friendli", "vllm"):
        raise ValueError(
            f"unknown LLM provider {prov!r}; expected one of: nim, friendli, vllm"
        )

    verify = _env_bool("LLM_VERIFY_SSL", True)
    shared_model = os.environ.get("LLM_MODEL") or model_override

    if prov == "nim":
        model = shared_model or os.environ.get("NIM_MODEL") or _DEFAULT_NIM_MODEL
        cfg = LLMConfig(
            provider="nim",
            base_url="https://integrate.api.nvidia.com/v1",
            api_key=os.environ.get("NVIDIA_API_KEY"),
            model=model,
            verify_ssl=verify,
        )
        if not cfg.api_key:
            raise RuntimeError(
                "NVIDIA_API_KEY is not set; required for LLM_PROVIDER=nim"
            )
    elif prov == "friendli":
        model = (
            shared_model
            or os.environ.get("FRIENDLI_MODEL")
            or _DEFAULT_FRIENDLI_MODEL
        )
        cfg = LLMConfig(
            provider="friendli",
            base_url=os.environ.get("FRIENDLI_BASE_URL") or _DEFAULT_FRIENDLI_BASE,
            api_key=os.environ.get("FRIENDLI_API_KEY"),
            model=model,
            verify_ssl=verify,
        )
        if not cfg.api_key:
            raise RuntimeError(
                "FRIENDLI_API_KEY is not set; required for LLM_PROVIDER=friendli"
            )
    else:  # vllm
        model = shared_model or os.environ.get("VLLM_MODEL") or ""
        cfg = LLMConfig(
            provider="vllm",
            base_url=os.environ.get("VLLM_BASE_URL") or _DEFAULT_VLLM_BASE,
            api_key=os.environ.get("VLLM_API_KEY") or "dummy",
            model=model,
            verify_ssl=verify,
        )
        if not cfg.model:
            raise RuntimeError(
                "VLLM_MODEL (or LLM_MODEL) must be set so the pipeline can send "
                "it as `model=` to the vLLM server"
            )

    # Provider-default extra_body (e.g. GLM thinking off), then env overrides.
    extra = dict(_default_extra_body(cfg.provider, cfg.model))
    extra.update(_parse_extra_body_env())
    cfg.extra_body = extra
    return cfg


# ---------------------------------------------------------------------------
# Data-root helper: every stage reads/writes under $STAGE_DATA_ROOT.
# ---------------------------------------------------------------------------

def data_root() -> Path:
    """Return the base directory that holds /stage_1_2/, /stage_2_1/, ..."""
    raw = os.environ.get("STAGE_DATA_ROOT") or str(Path.home() / "data")
    return Path(raw).expanduser()
