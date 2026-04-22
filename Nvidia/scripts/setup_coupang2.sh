#!/bin/bash
# coupang2 환경 구축: cudf + RAPIDS + nemo_curator + sentence-transformers
# 실행: brev exec coupang2 @scripts/setup_coupang2.sh
# 또는: brev copy scripts/setup_coupang2.sh coupang2:/tmp/ && brev exec coupang2 "bash /tmp/setup_coupang2.sh"

set -euo pipefail
set -x

echo "=== coupang2 environment setup for semantic dedup ==="
echo "Hostname: $(hostname)"
date

# --- GPU / driver sanity ---
nvidia-smi | head -20 || true
echo "---"

# --- Python venv ---
VENV=/home/nvidia/dedup/.venv
if [ ! -d "$VENV" ]; then
    mkdir -p /home/nvidia/dedup
    python3 -m venv "$VENV"
fi
source "$VENV/bin/activate"
python --version

# --- Upgrade core tooling ---
pip install -U pip wheel setuptools

# --- Install RAPIDS (cudf + dask-cudf) for CUDA 12.x ---
# Using the rapidsai stable channel via pip. Takes 3-5 minutes.
pip install --extra-index-url=https://pypi.nvidia.com \
    "cudf-cu12==25.02.*" \
    "dask-cudf-cu12==25.02.*" \
    "cuml-cu12==25.02.*" \
    "rmm-cu12==25.02.*"

# --- NeMo Curator (same version as coupang) ---
pip install "nemo-curator[text]>=1.1.0"

# --- sentence-transformers (with torch CUDA 12) ---
pip install --extra-index-url https://download.pytorch.org/whl/cu121 torch
pip install sentence-transformers

# --- Ray (used by NeMo Curator's RayActorPoolExecutor) ---
pip install "ray[default]"

# --- Quick sanity ---
python -c "import cudf; print(f'cudf OK {cudf.__version__}')"
python -c "import cuml; print(f'cuml OK {cuml.__version__}')"
python -c "from nemo_curator.stages.deduplication.semantic.workflow import SemanticDeduplicationWorkflow; print('SemanticDeduplicationWorkflow importable OK')"
python -c "from sentence_transformers import SentenceTransformer; m = SentenceTransformer('sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2', device='cuda'); print(f'sentence-transformer OK, device={m.device}')"

# --- Working dirs ---
mkdir -p /home/nvidia/dedup/data
mkdir -p /home/nvidia/dedup/output
mkdir -p /home/nvidia/dedup/cache

echo "=== SETUP COMPLETE ==="
date
