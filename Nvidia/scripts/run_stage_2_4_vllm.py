"""Run Stage 2.4 (expand canonical intents to natural-language queries)
with in-process vLLM offline inference.

GPU-node equivalent of `python -m pipelines.stage_2_4_expand` that skips
the OpenAI-compatible endpoint and feeds every canonical intent into a
single `llm.chat([[...], [...], ...])` batch.

Typical use:

    cd ~/stage2_work
    python scripts/run_stage_2_4_vllm.py

Env knobs (all optional):
    STAGE_INPUT    input jsonl path
                   default: $STAGE_DATA_ROOT/stage_2_3/analyzed_intents.jsonl
    STAGE_OUTPUT   output jsonl path
                   default: $STAGE_DATA_ROOT/stage_2_4/expanded_intents.jsonl
    VLLM_OFFLINE_MODEL   HF model id (default Nemotron-Nano-30B-BF16)
    VLLM_DTYPE           vLLM dtype (default "auto")
    VLLM_GPU_MEM_UTIL    0.0-1.0
    STAGE_N_QUERIES      queries per canonical (default 5)
"""
from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import List

HERE = Path(__file__).resolve().parent
PROJECT_ROOT = HERE.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from pipelines.config import data_root  # noqa: E402
from pipelines.llm_client import load_env  # noqa: E402
from pipelines.schemas import AnalyzedIntent  # noqa: E402
from pipelines.vllm_adapter import expand_batch_vllm_offline  # noqa: E402


def _resolve_paths() -> tuple[Path, Path]:
    root = data_root()
    input_path = Path(
        os.environ.get("STAGE_INPUT")
        or (root / "stage_2_3" / "analyzed_intents.jsonl")
    )
    output_path = Path(
        os.environ.get("STAGE_OUTPUT")
        or (root / "stage_2_4" / "expanded_intents.jsonl")
    )
    return input_path, output_path


def _load_analyzed(path: Path) -> List[AnalyzedIntent]:
    out: List[AnalyzedIntent] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        out.append(AnalyzedIntent.model_validate_json(line))
    return out


def main() -> int:
    load_env()
    input_path, output_path = _resolve_paths()

    model_id = os.environ.get(
        "VLLM_OFFLINE_MODEL",
        "nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B-BF16",
    )
    dtype = os.environ.get("VLLM_DTYPE", "auto")
    gpu_util = os.environ.get("VLLM_GPU_MEM_UTIL")
    n_queries = int(os.environ.get("STAGE_N_QUERIES", "5"))

    print(f"[stage_2_4] input  : {input_path}", flush=True)
    print(f"[stage_2_4] output : {output_path}", flush=True)
    print(f"[stage_2_4] model  : {model_id} dtype={dtype}", flush=True)
    print(f"[stage_2_4] n_queries per canonical: {n_queries}", flush=True)

    intents = _load_analyzed(input_path)
    print(f"[stage_2_4] loaded {len(intents)} AnalyzedIntent(s)", flush=True)
    if not intents:
        return 0

    from vllm import LLM  # noqa: E402

    kwargs: dict = {
        "model": model_id,
        "trust_remote_code": True,
        "dtype": dtype,
    }
    if gpu_util:
        kwargs["gpu_memory_utilization"] = float(gpu_util)
    print("[stage_2_4] loading vLLM ...", flush=True)
    llm = LLM(**kwargs)
    print("[stage_2_4] vLLM ready", flush=True)

    results = expand_batch_vllm_offline(
        llm, model_id, intents, n_queries=n_queries
    )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as fh:
        for r in results:
            fh.write(r.model_dump_json() + "\n")
    print(f"[stage_2_4] saved {len(results)} expanded intents -> {output_path}", flush=True)

    for r in results:
        print(f"\n{r.intent_keyword}  (parse_ok={r.expansion_meta.get('parse_ok')})")
        for q in r.natural_queries:
            print(f"  - {q}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
