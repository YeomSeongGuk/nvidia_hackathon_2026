"""Unified Stage 2 pipeline driver (Stage 1-style one-file entry).

Thin wrapper around `pipelines.stage_2.data_pipeline_stage2_vllm` so a
Stage 2 run looks the same shape as a Stage 1 run:

    # Stage 1 (pipelines/stage_1/data_pipeline_vllm.py)
    python pipelines/stage_1/data_pipeline_vllm.py ...

    # Stage 2 (this file):
    python scripts/run_stage_2_pipeline_vllm.py ...

All CLI flags are forwarded to the underlying orchestrator. See
`pipelines/stage_2/data_pipeline_stage2_vllm.py` for the full list.

Typical use on the GPU box:

    cd ~/stage2_work
    python scripts/run_stage_2_pipeline_vllm.py \\
        --input  /home/nvidia/data/stage_1_2 \\
        --output-root $HOME/data

    # Re-run only Stage 2.3 + 2.4 (skip the slow extract + canonicalize)
    python scripts/run_stage_2_pipeline_vllm.py \\
        --skip-extract --skip-canonicalize

    # Stop early for sanity-check before the 2.4 expansion LLM pass
    python scripts/run_stage_2_pipeline_vllm.py --stop-after aggregate
"""
from __future__ import annotations

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
PROJECT_ROOT = HERE.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from pipelines.stage_2.data_pipeline_stage2_vllm import main  # noqa: E402


if __name__ == "__main__":
    sys.exit(main())
