# Analyzed-Data Pipeline (Hackathon PoC)

**Customer Driven Discovery using NeMo Curator** — a proof-of-concept pipeline
that turns curated Korean/English fashion reviews into a *Semantic Bridge*:
canonical TPO (Time/Place/Occasion) intents mapped to concrete product
attributes with data-lineage back to the source documents.

This repository owns the **analyzed-data generation** stage of the hackathon
project. It takes the output of the upstream NeMo Curator curation pipeline
and produces analyzed records such as:

```json
{
  "intent_keyword": "하객룩",
  "mapped_attributes": [
    {"attribute_key": "material", "attribute_value": "tweed", "weight": 0.91},
    {"attribute_key": "fit",      "attribute_value": "neat",  "weight": 0.46},
    {"attribute_key": "fit",      "attribute_value": "tailored", "weight": 0.45}
  ],
  "data_lineage": {
    "total_evidence_count": 2,
    "source_doc_ids": ["curated_blog_en_001", "curated_rv_en_003"]
  },
  "last_updated": "2026-04-21T05:49:32Z"
}
```

## Why this is interesting

- **Cross-lingual intent merging** — the English phrases "wedding" and
  "wedding guest look" and the Korean phrase "사무실룩" all land in the correct
  Korean canonical intents ("하객룩" and "오피스룩").
- **Synonym collapsing** — "데일리 캐주얼", "스트리트 캐주얼", "일상캐주얼",
  "캐주얼", and the English "everyday casual" collapse into the single
  canonical intent "캐주얼".
- **Two-stage LLM refinement** — an embedding-based first pass handles obvious
  duplicates quickly; a second LLM pass splits over-merged clusters and merges
  semantically equivalent but embedding-distant clusters.

## Pipeline overview

This project owns **Stage 2** (analysis). Stage 1 (data collection + NeMo
Curator curation) lives in a different session / repo; we only consume its
output at `/data/stage_1_2/`.

```
(upstream - out of scope)
  Stage 1.1: raw collection
  Stage 1.2: NeMo Curator curation
          │
          ▼
/data/stage_1_2/*.jsonl            (CuratedDoc: curated_id, clean_text, pipeline_metadata)
          │
          ▼
  Stage 2.1: stage_2_1_extract.py         (per-document LLM extraction)
     - async batch (default concurrency=10)
     - provider: NIM / Friendli / vLLM  (OpenAI-compatible)
          │
          ▼
/data/stage_2_1/stage_2_1_extracted.jsonl  (ExtractedIntent per doc)
          │
          ▼
  Stage 2.2: stage_2_2_canonicalize.py    (dedup & canonicalize intents)
     2.2a embed     (sentence-transformers, CUDA when available, default BGE-M3)
     2.2b cluster   (sklearn Agglomerative, cosine)
     2.2c refine    (LLM splits heterogeneous clusters)
     2.2d canonical (LLM picks one Korean name per cluster)
     2.2e cross-merge (LLM merges duplicate canonicals across clusters)
          │
          ▼
/data/stage_2_2/stage_2_2_clusters.jsonl   (canonical intents + source doc ids)
          │
          ▼
  Stage 2.3: stage_2_3_aggregate.py       (attribute aggregation)
     2.3a merge-by-canonical (post-hoc safety net)
     2.3b rank attribute-values by quality-weighted frequency
          │
          ▼
/data/stage_2_3/analyzed_intents.jsonl     (final analyzed data, demo-ready)
          │
          ▼
  Stage 2.4: stage_2_4_expand.py          (natural-language query expansion)
     - expand each canonical into N realistic chatbot queries
     - NeMo Data Designer path if available, else direct LLM call
          │
          ▼
/data/stage_2_4/expanded_intents.jsonl     (canonical → list of natural user queries)
```

### LLM backends

Stage 2.1 / 2.2 share `pipelines.config` to switch between OpenAI-compatible
endpoints. Select via `--provider` flag or `LLM_PROVIDER` env var:

| Provider   | Base URL                                         | Required env                                                  |
|------------|--------------------------------------------------|---------------------------------------------------------------|
| `nim`      | `https://integrate.api.nvidia.com/v1`            | `NVIDIA_API_KEY`                                              |
| `friendli` | `https://api.friendli.ai/serverless/v1`          | `FRIENDLI_API_KEY`                                            |
| `vllm`     | `$VLLM_BASE_URL` (default `http://localhost:8000/v1`) | `VLLM_MODEL` (served model id); `VLLM_API_KEY` optional  |

Model id can be overridden via `LLM_MODEL`, `NIM_MODEL`, `FRIENDLI_MODEL`, or
`VLLM_MODEL` depending on provider, or via the `--llm-model` CLI flag.

### Self-hosted vLLM (Nemotron-3 Nano 30B A3B)

The full extraction + eval pipeline can target a vLLM OpenAI-compatible
server on the GPU node. Nemotron-3 Nano is a **reasoning model** and emits
a `reasoning_content` pass by default; `pipelines.config` recognises this
family and auto-injects `chat_template_kwargs.enable_thinking=False` on
every call, so extraction and judge JSON comes back clean.

Start the vLLM server on the GPU box:

```bash
# BF16 (higher quality, ~60GB VRAM)
vllm serve nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B-BF16 \
    --trust-remote-code --dtype auto --port 8000 \
    --enable-reasoning --reasoning-parser nemotron \
    --guided-decoding-backend outlines

# FP8 (faster, ~30GB VRAM)
vllm serve nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B-FP8 \
    --trust-remote-code --dtype auto --port 8000 \
    --enable-reasoning --reasoning-parser nemotron \
    --guided-decoding-backend outlines
```

Point the pipeline / eval scripts at it:

```bash
export LLM_PROVIDER=vllm
export VLLM_BASE_URL=http://<gpu-host>:8000/v1
export VLLM_MODEL=nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B-BF16   # or -FP8
# export VLLM_API_KEY=<only-if-you-configured-one>             # optional

# extraction (async)
python -m pipelines.stage_2_1_extract

# canonicalization + aggregation (use same provider for the LLM refine/canonical calls)
python -m pipelines.stage_2_2_canonicalize --refine --cross-merge
python -m pipelines.stage_2_3_aggregate

# eval (per-stage judges; default provider=nim unless you pass --provider vllm)
python -m pipelines.eval.stage_2_1_judge --provider vllm \
    --judge-model nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B-BF16
```

Notes:
- `--enable-reasoning --reasoning-parser nemotron` lets vLLM surface the
  thinking pass in a separate `reasoning_content` field; combined with the
  baked-in `enable_thinking=False`, content stays JSON and cheap to parse.
- `--guided-decoding-backend outlines` enables strict JSON mode via
  `response_format={"type":"json_object"}` (the extraction stage relies on
  this to keep output shape stable).
- For the judge model you can either point to the same vLLM-served
  Nemotron-Nano, or keep the judge on NIM Cloud (Nemotron-Ultra / Llama-3.3)
  so that the judge and the extractor are different models (less self-bias).

### Algorithm parity with NeMo Curator SemDeDup

Stage 2.2 implements the same `embed → cluster → within-cluster similarity
threshold` algorithm that `nemo_curator.modules.SemDedup` uses on GPU. The
default embedding model is `BAAI/bge-m3` (1024-d multilingual) and runs on
CUDA when available (override with `--embed-device cpu`). Inline markers
`# [NEMO-CURATOR]` in `pipelines/stage_2_2_canonicalize.py` show where to
swap `sentence-transformers` for `nemo_curator.EmbeddingCreator` +
`ClusteringModel` when moving to true multi-GPU scale.

## Layout

```
Nvidia/
├── pipelines/
│   ├── __init__.py
│   ├── schemas.py                    # Pydantic models for every stage's IO
│   ├── prompts.py                    # LLM prompt templates (Korean by design)
│   ├── llm_client.py                 # NIM / Friendli / vLLM client + load_env
│   ├── config.py                     # provider/env resolution, data_root()
│   ├── vllm_adapter.py               # in-process vLLM offline adapter + batch helpers
│   ├── stage_2_1_extract.py          # Stage 2.1 - per-doc extraction
│   ├── stage_2_2_canonicalize.py     # Stage 2.2 - embed/cluster/refine/canonical/cross-merge
│   ├── stage_2_3_aggregate.py        # Stage 2.3 - attribute aggregation
│   ├── stage_2_4_expand.py           # Stage 2.4 - canonical → natural queries
│   └── eval/                         # Stage 2 LLM-as-Judge tooling (separate session)
├── scripts/
│   ├── make_curated_sample.py        # build curated_sample.jsonl from raw reviews
│   ├── tune_threshold.py             # sweep agglomerative thresholds
│   ├── run_stage_2_1_vllm.py         # Stage 2.1 via in-process vLLM (GPU node)
│   ├── run_stage_2_2_vllm.py         # Stage 2.2 via in-process vLLM (GPU node)
│   └── run_stage_2_4_vllm.py         # Stage 2.4 via in-process vLLM (GPU node)
├── data/                             # all JSONL artefacts live here
├── .env                              # NVIDIA_API_KEY / FRIENDLI_API_KEY (not committed)
└── README.md
```

## Prerequisites

- Python 3.12 (the project was developed with the venv `/Users/sgyeom/Nvidia/.venv`)
- `uv` for dependency management
- Hackathon NIM Cloud API key exported as `NVIDIA_API_KEY`

## Setup

### Local / macOS (CPU path)

```bash
uv venv --python 3.12 .venv
source .venv/bin/activate

# Loose requirements (recommended for local dev)
uv pip install --native-tls -r requirements.txt

# OR reproduce the exact CPU venv used to produce the demo output
uv pip install --native-tls -r requirements-lock.txt

# Put the NIM key in .env (or export it before running the stages)
echo "NVIDIA_API_KEY=<your-key>" > .env
```

### Brev GPU image (Ubuntu + CUDA + NeMo Curator pre-installed)

The Brev hackathon image ships a Python 3.12 venv at `~/.venv` together with:

- `nemo-curator 1.1.0`
- `torch` (CUDA build, originally CUDA 12.6)
- `ray`, `pyarrow`
- `openai`, `pydantic`, `huggingface_hub`

It is missing the embedding + clustering stack. Two non-obvious gotchas:

1. New shells do **not** export `VIRTUAL_ENV`. The interpreter at
   `~/.venv/bin/python` works, but `pip` will write to the Python 3.10
   user-site instead of the venv. You must `source` the activate script.
2. Even with the venv active, `pip install` will see the same package in
   user-site and short-circuit. Use `--ignore-installed`.

```bash
# 1) activate the pre-shipped venv so VIRTUAL_ENV is exported
source ~/.venv/bin/activate

# 2) install client + Stage 2 deps into the venv
python -m pip install --ignore-installed -r requirements.txt

# 3) sanity check imports
python -c "import openai, pydantic, httpx, sentence_transformers, sklearn, numpy, nemo_curator; print('ok')"
```

`requirements.txt` intentionally omits `nemo-curator` and `torch` so it stays
safe on both the laptop (CPU, `nemo-curator` is Linux-only) and the Brev
image (GPU, already provisioned).

**CUDA version note**: installing `sentence-transformers` may pull a newer
torch that bundles CUDA 13 wheels (`nvidia-*-cu13`), which conflicts with
the image's CUDA 12.6. If you need to keep the Curator GPU stack working,
pin torch instead:

```bash
python -m pip install --ignore-installed -r requirements.txt   torch==2.11.0
```

### Corporate network / SSL interception

Stage 1/2/3 each read HTTP certificates from env vars so that corporate TLS
interception does not break the HuggingFace Hub download or the NIM request.

```bash
# macOS keychain export is a one-time step
security find-certificate -a -p /Library/Keychains/System.keychain           > /tmp/sys_certs.pem
security find-certificate -a -p /System/Library/Keychains/SystemRootCertificates.keychain         >> /tmp/sys_certs.pem

export SSL_CERT_FILE=/tmp/sys_certs.pem
export REQUESTS_CA_BUNDLE=/tmp/sys_certs.pem
export LLM_VERIFY_SSL=0   # OpenAI SDK skips TLS verify (hackathon network only)
```

## Running the pipeline

```bash
# 0. build a 50-doc sample from raw Naver shopping reviews (+ English blog seeds)
python3 scripts/make_curated_sample.py --n-korean 45

# 2.1 per-document extraction (~5s per doc with Nemotron-3 Nano)
python3 -m pipelines.stage_2_1_extract

# 2.2 canonicalization (embed + cluster + LLM refine + cross-cluster merge)
python3 -m pipelines.stage_2_2_canonicalize \
    --threshold 0.35 --refine --cross-merge

# 2.3 attribute aggregation and final analyzed-data JSONL
python3 -m pipelines.stage_2_3_aggregate

# 2.4 expand each canonical into 5 natural-language chatbot queries
python3 -m pipelines.stage_2_4_expand --n-queries 5
```

### Stage 2.4 - why we need it

Everything up to Stage 2.3 produces *canonical* intents like `하객룩`,
`오피스룩`, `캠핑룩`. These are compact and great for indexing, but a
shopping chatbot receives conversational queries like **"결혼식에 뭐 입지?"**
or **"주말 피크닉 갈 때 입기 좋은 옷 추천해줘"**. Stage 2.4 closes that
gap: for each canonical, the LLM generates N realistic user queries, which
the retrieval layer indexes alongside the canonical itself.

Output shape (one record per canonical):

```json
{
  "intent_keyword": "하객룩",
  "natural_queries": [
    "결혼식 하객으로 갈 때 뭐 입지?",
    "하객룩 추천해줘, 너무 튀지 않게",
    "친구 결혼식에 트위드 원피스 어때?",
    "웨딩 게스트로 갈 때 네이비 컬러 코디 알려줘",
    "하객으로 갈 때 실례 안 되는 옷"
  ],
  "mapped_attributes": [
    {"attribute_key": "material", "attribute_value": "트위드", "weight": 0.67},
    {"attribute_key": "color",    "attribute_value": "네이비", "weight": 0.67}
  ],
  "data_lineage": {"total_evidence_count": 6, "source_doc_ids": ["rv-wed-001", ...]},
  "last_updated": "2025-04-21T00:00:00Z",
  "expansion_meta": {"model": "...", "tokens": 675, "strategy": "direct-call"}
}
```

Two execution paths live behind the same CLI and produce identical output:

1. **NeMo Data Designer** (`pipelines.stage_2_4_expand` picks this first)
   — `SamplerColumn(intent_keyword) → SamplerColumn(attrs) → LLMStructuredColumn(queries)`.
   Skipped automatically when `nemo_curator.synthetic` is missing or its API
   does not expose the expected classes.
2. **Direct fallback** — plain `pipelines.llm_client.call_json` loop per
   canonical. Works identically on NIM / Friendli / vLLM OpenAI-compatible
   endpoints. Forced with `--force-fallback`.

For the full-fidelity GPU path (in-process vLLM offline batching), use
`scripts/run_stage_2_4_vllm.py`:

```bash
VLLM_OFFLINE_MODEL=nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B-BF16 \
  STAGE_N_QUERIES=5 \
  python scripts/run_stage_2_4_vllm.py
```

## CLI options

### `pipelines.stage_2_1_extract`

| flag          | default                                | meaning                          |
|---------------|-----------------------------------------|----------------------------------|
| `--input`     | `data/curated_sample.jsonl`             | curated JSONL                    |
| `--output`    | `data/stage_2_1_extracted.jsonl`        |                                  |
| `--model`     | `nvidia/nemotron-3-nano-30b-a3b`        | NIM Cloud model id               |
| `--limit`     | `0`                                     | 0 = process every input          |
| `--sleep`     | `0.3`                                   | seconds between calls            |

### `pipelines.stage_2_2_canonicalize`

| flag                | default                                                           | meaning                                              |
|---------------------|-------------------------------------------------------------------|------------------------------------------------------|
| `--input`           | `data/stage_2_1_extracted.jsonl`                                 |                                                      |
| `--output`          | `data/stage_2_2_clusters.jsonl`                                  |                                                      |
| `--embed-model`     | `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`    | local embedding model                                |
| `--threshold`       | `0.35`                                                            | cosine distance cutoff for Agglomerative clustering  |
| `--refine`          | off                                                               | LLM splits over-merged clusters into clean subgroups |
| `--refine-min-size` | `3`                                                               | only refine clusters of this size or larger          |
| `--cross-merge`     | off                                                               | LLM merges canonicals that mean the same thing       |
| `--skip-canonical`  | off                                                               | skip LLM canonical naming (shortest member as name)  |

### `pipelines.stage_2_3_aggregate`

| flag              | default                           | meaning                                |
|-------------------|-----------------------------------|----------------------------------------|
| `--top-k`         | `3`                            | top-N attribute values per key         |
| `--skip-general`  | off                            | drop the "일반" cluster from output     |

### `pipelines.stage_2_4_expand`

| flag                | default                                            | meaning                                                            |
|---------------------|----------------------------------------------------|--------------------------------------------------------------------|
| `--input`           | `$STAGE_DATA_ROOT/stage_2_3/analyzed_intents.jsonl` | Stage 2.3 output                                                   |
| `--output`          | `$STAGE_DATA_ROOT/stage_2_4/expanded_intents.jsonl` |                                                                    |
| `--provider`        | `$LLM_PROVIDER` (default nim)                      | `nim` / `friendli` / `vllm`                                        |
| `--n-queries`       | `5`                                                | queries generated per canonical                                    |
| `--force-fallback`  | off                                                | skip NeMo Data Designer path even when it is importable            |

## Example final output (50-doc sample)

```
[캐주얼]   (evidence=12)  cotton 0.117, 린넨 0.071, 길이감 0.071, loose 0.067, ...
[하객룩]   (evidence=2)   material=tweed 0.91, fit=neat 0.46, fit=tailored 0.45
[오피스룩] (evidence=2)   material=linen blend 0.44, fit=relaxed 0.44, color=light beige 0.44, style=casual 0.44, season=summer 0.44
[홈웨어]   (evidence=2)   fit=이상한 재단 0.3
[여름룩]   (evidence=1)   fit=just right length 0.95, season=summer 0.95
[겨울룩]   (evidence=1)   material=부드러운 0.95, fit=이쁜 0.95, season=겨울 0.95
[교복]     (evidence=1)   fit=좁은 0.5, style=셔츠 0.5
[운동룩]   (evidence=1)   fit=작음 0.6
[운동복]   (evidence=1)   fit=small chest 0.6
[언더웨어] (evidence=1)   fit=타이트함 0.6
[일반]     (evidence=22)  general-wear fallback bucket
```

## Next steps

- Increase input scale (500+ curated docs) to exercise cross-cluster merge at scale
- Wire Stage 2.4 `expanded_intents.jsonl` into the retrieval index so chatbot
  queries like "결혼식 갈 때 뭐 입지?" route to the canonical "하객룩"
- When GPU is available, swap Stage 2 embedding and clustering for
  `nemo_curator.SemDedup` at the `# [NEMO-CURATOR]` comment markers
- Pin the exact NeMo Data Designer API once confirmed in the hackathon
  internal docs, so Stage 2.4 prefers the structured-column path over the
  direct-call fallback
- Add the judge module (`pipelines/eval/`) to the pipeline once its API is stable
