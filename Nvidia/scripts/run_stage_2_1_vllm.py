"""Run Stage 2.1 (extract) with in-process vLLM offline inference.

This is the GPU-node equivalent of `python -m pipelines.stage_2_1_extract`,
except we do NOT go through an OpenAI-compatible endpoint; we load the
vLLM model in-process and batch everything through `llm.chat(...)`.

Typical use:

    cd ~/stage2_work
    python scripts/run_stage_2_1_vllm.py

Env knobs (all optional, defaults sensible for Brev A100 / Nemotron Nano):
    STAGE_INPUT   path to a .jsonl file OR a directory of .jsonl files
                  default: $STAGE_DATA_ROOT/stage_1_2  (= ~/data/stage_1_2)
    STAGE_OUTPUT  output JSONL path
                  default: $STAGE_DATA_ROOT/stage_2_1/stage_2_1_extracted.jsonl
    VLLM_OFFLINE_MODEL   HF model id for the local LLM
                         default: nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B-BF16
    VLLM_DTYPE           vLLM dtype (default "auto")
    VLLM_GPU_MEM_UTIL    0.0-1.0 (default let vLLM pick)
    STAGE_LIMIT          cap on # of input docs (default 0 = all)
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

# Make `pipelines.*` importable when run as `python scripts/run_stage_2_1_vllm.py`
HERE = Path(__file__).resolve().parent
PROJECT_ROOT = HERE.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from pipelines.config import data_root  # noqa: E402
from pipelines.llm_client import load_env  # noqa: E402
from pipelines.schemas import CuratedDoc  # noqa: E402
from pipelines.vllm_adapter import (  # noqa: E402
    extract_batch_vllm_offline,
    write_jsonl,
)


def _resolve_paths() -> tuple[Path, Path]:
    root = data_root()
    input_path = Path(os.environ.get("STAGE_INPUT") or (root / "stage_1_2"))
    output_path = Path(
        os.environ.get("STAGE_OUTPUT")
        or (root / "stage_2_1" / "stage_2_1_extracted.jsonl")
    )
    return input_path, output_path


def _iter_docs(input_path: Path) -> list[CuratedDoc]:
    if input_path.is_dir():
        files = sorted(input_path.glob("*.jsonl"))
        if not files:
            raise FileNotFoundError(f"no .jsonl files under {input_path}")
    else:
        files = [input_path]
    docs: list[CuratedDoc] = []
    for f in files:
        for line in f.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            docs.append(CuratedDoc.model_validate_json(line))
    return docs


def main() -> int:
    load_env()
    input_path, output_path = _resolve_paths()

    model_id = os.environ.get(
        "VLLM_OFFLINE_MODEL",
        "nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B-BF16",
    )
    dtype = os.environ.get("VLLM_DTYPE", "auto")
    gpu_util = os.environ.get("VLLM_GPU_MEM_UTIL")
    limit = int(os.environ.get("STAGE_LIMIT", "0"))

    print(f"[stage_2_1] input  : {input_path}", flush=True)
    print(f"[stage_2_1] output : {output_path}", flush=True)
    print(f"[stage_2_1] model  : {model_id} dtype={dtype}", flush=True)

    docs = _iter_docs(input_path)
    if limit:
        docs = docs[:limit]
    print(f"[stage_2_1] loaded {len(docs)} CuratedDoc(s)", flush=True)
    if not docs:
        print("[stage_2_1] nothing to do", flush=True)
        return 0

    # Load vLLM lazily so the script imports cleanly even without a GPU
    from vllm import LLM  # noqa: E402

    kwargs: dict = {
        "model": model_id,
        "trust_remote_code": True,
        "dtype": dtype,
    }
    if gpu_util:
        kwargs["gpu_memory_utilization"] = float(gpu_util)
    print("[stage_2_1] loading vLLM ...", flush=True)
    llm = LLM(**kwargs)
    print("[stage_2_1] vLLM ready", flush=True)

    results = extract_batch_vllm_offline(llm, model_id, docs)
    print(f"[stage_2_1] extracted {len(results)}/{len(docs)}", flush=True)

    write_jsonl(output_path, results)
    print(f"[stage_2_1] saved -> {output_path}", flush=True)

    # Quick preview
    for r in results[:5]:
        attrs_filled = sum(1 for v in r.attributes.model_dump().values() if v)
        print(
            f"  {r.source_curated_id[:24]:<24}  intent={r.raw_intent!r:<22} "
            f"attrs={attrs_filled}/5",
            flush=True,
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
