# Customer Driven Discovery — NeMo Curator Hackathon PoC

**Korean fashion reviews → canonical TPO intents → attribute-aware queries.**
An NVIDIA-stack-powered curation pipeline that mines the *semantic bridge*
between how shoppers talk (*"내일 하객 갈 때 입을 옷"*) and how the
catalog is indexed (material / fit / color).

Key stack: **NeMo Curator** · **NeMo Data Designer** (+ 7-field Korean
persona) · **Nemotron-Super 120B FP8** on vLLM / Brev H100 ·
**Friendli tri-judge ensemble** (GLM-5.1 + DeepSeek-V3.2 + Qwen3-235B-A22B).

**Headline result (Stage 1, best iter_21_dedup_v2)**: 10 promote gates,
8/10 passed, up from 1/10 at baseline. 260 canonical TPO intents from
10 K Korean reviews.

---

## Quick start `(3 commands after setup)`

```bash
# 0. environment (detailed setup below)
uv venv --python 3.12 .venv && source .venv/bin/activate
uv pip install --native-tls -r requirements.txt
echo "NVIDIA_API_KEY=...\nFRIENDLI_API_KEY=..." > .env

# 1. run Stage 2 end-to-end on the already-curated iter_21 seed (42 rows)
export LLM_PROVIDER=vllm VLLM_BASE_URL=http://localhost:5000/v1 VLLM_MODEL=nemotron
python -m pipelines.stage_2_1_extract      --input experiments/iter_21_dedup_v2/output/stage_1_2_processed.jsonl
python -m pipelines.stage_2_2_canonicalize --refine --cross-merge --embed-device cpu
python -m pipelines.stage_2_3_aggregate
python -m pipelines.stage_2_4_expand       --n-queries 5

# 2. evaluate with tri-judge ensemble  (needs FRIENDLI_API_KEY)
python scripts/tri_judge_run_stage2.py --output-dir data/stage_2_run

# 3. inspect
cat data/stage_2_run/metrics.json          # all tri-judge + quant probes
cat data/stage_2_run/judge_report.md       # human-readable summary
cat experiments/REPORT.md                  # full 23-iter story (Stage 1)
```

---

## What's in this repository

```
Nvidia/
├── pipelines/                   # pipeline + eval modules
│   ├── stage_1/                 # Stage 1: seed → synth → dedup → filter
│   ├── stage_2/                 # Stage 2 helper modules
│   ├── stage_2_1_extract.py     # 2.1 per-doc extract
│   ├── stage_2_1_5_semdedup.py  # 2.1.5 semantic dedup (SD-series)
│   ├── stage_2_2_canonicalize.py# 2.2 embed + cluster + refine + canonical + cross-merge
│   ├── stage_2_3_aggregate.py   # 2.3 attribute aggregation
│   ├── stage_2_4_expand.py      # 2.4 natural-language query expansion
│   ├── eval/                    # 7 judge modules (one per sub-stage)
│   ├── config.py                # provider / env / data_root resolution
│   ├── llm_client.py            # OpenAI-compatible client (NIM / Friendli / vLLM)
│   ├── vllm_adapter.py          # in-process vLLM batching
│   ├── prompts.py               # Korean prompt templates
│   └── schemas.py               # Pydantic IO schemas for every stage
├── scripts/
│   ├── iter_run.py              # Stage 1 iteration driver (pipeline → judge → commit)
│   ├── iter_run_stage2.py       # Stage 2 iteration driver
│   ├── tri_judge_run.py         # Stage 1 tri-judge ensemble orchestrator
│   ├── tri_judge_run_stage2.py  # Stage 2 tri-judge ensemble orchestrator
│   ├── quant_stage1_report.py   # deterministic probes for Stage 1
│   ├── quant_stage2_report.py   # deterministic probes for Stage 2
│   ├── make_comparison.py       # iter_NN vs parent iter diff report
│   ├── make_curated_sample.py   # build curated_sample.jsonl from raw reviews
│   ├── run_stage_2_*_vllm.py    # in-process vLLM variants for GPU box
│   └── demo_es_search*          # Elasticsearch demo (for demo time)
├── experiments/                 # Stage 1 iter_00 → iter_27, one folder per iter
│   ├── PLAN.md                  # Stage 1 iteration plan
│   ├── REPORT.md                # 23-iter narrative + outcomes
│   └── iter_NN_<slug>/          # per-iter artefacts (see §"Results inspection")
├── experiments_stage2/          # Stage 2 iteration branch (running)
│   ├── PLAN.md                  # 14-step per-iter recipe, SD+C+E+A+X queue
│   └── README.md                # operational quick-start
├── data/                        # runtime JSONL artefacts (gitignored)
├── presentation/                # hackathon deck + scripts (this section is separate)
├── .env                         # NVIDIA_API_KEY / FRIENDLI_API_KEY (not committed)
├── requirements.txt
└── requirements-lock.txt        # exact CPU venv reproduction
```

---

## End-to-end pipeline

```
[raw Korean reviews, 10K]   ← Naver Shopping + Musinsa + YouTube
        │
        ▼
Stage 1  ▌ NeMo Curator on Brev H100, Nemotron-Super 120B FP8
  1.0    ▌ seed                      ← judge: text_quality, diversity
  1.1    ▌ NeMo Data Designer synth  ← 7-field Korean persona conditioning
  1.1.5  ▌ dedup                     ← probe: dedup_miss_rate
  1.2    ▌ filter + format           ← judge: retention, fashion_rate, attr_grounded
        │                              5 497 curated synthetic reviews
        ▼
Stage 2  ▌ same vLLM backend
  2.1    ▌ per-doc intent + attr extract      ← judge: intent_groundedness, attr_concrete
  2.1.5  ▌ semantic dedup (optional, SD-series) ← probe: retention, avg_cosine
  2.2    ▌ embed + cluster + refine +          ← judge: coherent, canonical_fit, non-fashion
         ▌ canonical naming + cross-merge
  2.3    ▌ weighted attribute aggregation     ← judge: overall_usefulness, attr_fits
  2.4    ▌ natural-language query expansion   ← judge: natural_rate, query_diversity
        │                              260 canonical TPO intents × 5 queries
        ▼
[Semantic Bridge output]   analyzed_intents.jsonl + expanded_intents.jsonl
```

**Stage 1** has already been curated into `main` at its `iter_21_dedup_v2`
best-known pipeline (see `experiments/REPORT.md`). For Stage 2 iteration
work, Stage 1's output is **pinned** at
`experiments/iter_21_dedup_v2/output/stage_1_2_processed.jsonl`.

---

## Environment setup

### Prerequisites
- Python 3.12
- `uv` for dependency management (`brew install uv`)
- An NVIDIA NIM API key (Nemotron Cloud) OR a running vLLM server
- A Friendli API key (for the tri-judge ensemble)

### Local / macOS (CPU path)

```bash
uv venv --python 3.12 .venv
source .venv/bin/activate

# loose requirements
uv pip install --native-tls -r requirements.txt

# OR exactly reproduce the CPU venv used for the demo
uv pip install --native-tls -r requirements-lock.txt

# credentials (not committed)
cat > .env <<EOF
NVIDIA_API_KEY=<nim-key>
FRIENDLI_API_KEY=<friendli-key>
LLM_PROVIDER=nim          # or friendli, vllm
EOF
```

### Brev GPU image (Ubuntu + CUDA + NeMo Curator)

The hackathon image ships `nemo-curator 1.1.0`, CUDA-torch, ray, pyarrow,
openai, pydantic, huggingface_hub in `~/.venv`. Two gotchas:

1. **New shells do not export `VIRTUAL_ENV`.** The interpreter at
   `~/.venv/bin/python` works, but `pip` writes to user-site. Always
   `source ~/.venv/bin/activate` first.
2. **`pip install` short-circuits** on user-site duplicates; use
   `--ignore-installed`.

```bash
source ~/.venv/bin/activate
python -m pip install --ignore-installed -r requirements.txt
python -c "import openai, pydantic, sentence_transformers, sklearn, nemo_curator; print('ok')"
```

### Self-hosted vLLM (Nemotron-Super 120B FP8)

This is the configuration used for every reported result.

```bash
# on the GPU node (coupang / H100 NVL × 2)
vllm serve nvidia/NVIDIA-Nemotron-3-Super-120B-A12B-FP8 \
    --trust-remote-code --dtype auto --tensor-parallel-size 2 \
    --port 5000 --served-model-name nemotron \
    --enable-reasoning --reasoning-parser nemotron \
    --guided-decoding-backend outlines

# from any client
export LLM_PROVIDER=vllm
export VLLM_BASE_URL=http://<gpu-host>:5000/v1
export VLLM_MODEL=nemotron
export LLM_EXTRA_BODY='{"chat_template_kwargs":{"enable_thinking":false}}'
```

**Critical**: `enable_thinking=false` is required. Nemotron-Super returns
an empty `content` field with the answer in a separate `reasoning` field
otherwise. This env var propagates through both ModelProvider and
per-request params in `pipelines.config`.

### Provider switching cheat sheet

| Provider | Base URL | Required env | Typical use |
|---|---|---|---|
| `nim` | `https://integrate.api.nvidia.com/v1` | `NVIDIA_API_KEY` | quick local dev |
| `friendli` | `https://api.friendli.ai/serverless/v1` | `FRIENDLI_API_KEY` | **tri-judge ensemble** (always) |
| `vllm` | `$VLLM_BASE_URL` (e.g. `http://localhost:5000/v1`) | `VLLM_MODEL` | production pipeline runs |

### Corporate network / SSL interception

```bash
# one-time macOS keychain export
security find-certificate -a -p /Library/Keychains/System.keychain \
    > /tmp/sys_certs.pem
security find-certificate -a -p \
    /System/Library/Keychains/SystemRootCertificates.keychain \
    >> /tmp/sys_certs.pem

export SSL_CERT_FILE=/tmp/sys_certs.pem
export REQUESTS_CA_BUNDLE=/tmp/sys_certs.pem
export LLM_VERIFY_SSL=0      # OpenAI SDK skip-verify (hackathon network only)
```

---

## Running the pipeline

### Stage 1 (if re-running from scratch)

Stage 1 is already promoted into `main` as the **iter_21_dedup_v2**
pipeline. To re-run it end-to-end:

```bash
# bundled driver that replays Stage 1's best pipeline from scratch
python scripts/run_stage1_generator_local.py \
    --n 50 --output data/stage_1/
```

Artefacts land at:
```
data/stage_1/
├── stage_1_0_seed.jsonl
├── stage_1_1_synthetic.jsonl
├── stage_1_1_5_deduped.jsonl
└── stage_1_2_processed.jsonl
```

### Stage 2 (the main pipeline)

```bash
# sample the Stage 1 output (or use experiments/iter_21_dedup_v2/output/)
export STAGE_DATA_ROOT=data/stage_2_run

# 2.1 per-doc extraction (async, ~5s per doc)
python -m pipelines.stage_2_1_extract \
    --input experiments/iter_21_dedup_v2/output/stage_1_2_processed.jsonl \
    --output $STAGE_DATA_ROOT/stage_2_1_extracted.jsonl

# 2.1.5 semantic dedup (optional, SD-series hypothesis)
python -m pipelines.stage_2_1_5_semdedup \
    --input     $STAGE_DATA_ROOT/stage_2_1_extracted.jsonl \
    --output    $STAGE_DATA_ROOT/stage_2_1_5_deduped.jsonl \
    --threshold 0.90 \
    --embed-model BAAI/bge-m3

# 2.2 canonicalize  (embed + cluster + LLM refine + LLM canonical + cross-merge)
python -m pipelines.stage_2_2_canonicalize \
    --input  $STAGE_DATA_ROOT/stage_2_1_5_deduped.jsonl \
    --output $STAGE_DATA_ROOT/stage_2_2_clusters.jsonl \
    --threshold 0.35 --refine --cross-merge --embed-device cpu

# 2.3 attribute aggregation
python -m pipelines.stage_2_3_aggregate \
    --input  $STAGE_DATA_ROOT/stage_2_2_clusters.jsonl \
    --output $STAGE_DATA_ROOT/stage_2_3_analyzed_intents.jsonl

# 2.4 expand each canonical into N natural-language queries
python -m pipelines.stage_2_4_expand --n-queries 5 \
    --input  $STAGE_DATA_ROOT/stage_2_3_analyzed_intents.jsonl \
    --output $STAGE_DATA_ROOT/stage_2_4_expanded_intents.jsonl
```

### Full end-to-end on GPU with in-process vLLM

```bash
# convenience wrappers that batch via in-process vLLM (offline mode)
VLLM_OFFLINE_MODEL=nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B-BF16 \
    python scripts/run_stage_2_pipeline_vllm.py
```

---

## Evaluation

Evaluation runs **independently of the pipeline**, after it finishes.
Two layers:

### 1. LLM-as-Judge · tri-judge ensemble (Wisdom of the Crowd)

Every stage has a dedicated Pydantic-typed judge module under
`pipelines/eval/`. Each one is run by three **foreign** judges hosted
on Friendli serverless — no model ever grades its own output.

| Judge | Vendor | Friendli model id |
|---|---|---|
| GLM-5.1 | Z.AI | `zai-org/GLM-5.1` |
| DeepSeek-V3.2 | DeepSeek | `deepseek-ai/DeepSeek-V3.2` |
| Qwen3-235B-A22B | Alibaba | `Qwen/Qwen3-235B-A22B-Instruct-2507` |

Run the ensemble for all four Stage 2 sub-stages in one shot:

```bash
python scripts/tri_judge_run_stage2.py \
    --output-dir data/stage_2_run \
    --parallel 4
```

Writes per-judge raw outputs to `data/stage_2_run/judge_raw/`
(12 files = 4 stages × 3 judges) and aggregates into `metrics.json`
and `judge_report.md`.

Stage 1 has its own driver `scripts/tri_judge_run.py` (3 stages × 3
judges).

Individual-stage judges can also run standalone:

```bash
python -m pipelines.eval.stage_2_2_judge \
    --input data/stage_2_run/stage_2_2_clusters.jsonl \
    --provider friendli --judge-model deepseek-ai/DeepSeek-V3.2
```

### 2. Deterministic quant probes

Catch regressions LLMs miss (character-level leaks, dedup ratio, format):

```bash
python scripts/quant_stage2_report.py --output-dir data/stage_2_run
```

Probes include `semdedup_retention_rate`, `canonical_non_fashion_rate`,
`canonical_suffix_compliance_rate`, `query_non_hangul_chars_rate`,
`query_dedup_ratio` — see `experiments_stage2/PLAN.md §4e` for the
full probe list.

### 3. Promotion gates

A run "passes" only when the **tri-judge mean AND the quant probes**
cross their thresholds. Stage 1 had 10 gates (see
`experiments/PLAN.md §6`), Stage 2 has 12 across the four sub-stages
(`experiments_stage2/PLAN.md §6`).

**`HIGH_VARIANCE`** (range > 0.15 across the three judges on a
headline metric) blocks auto-promote — reviewer decides manually.

### 4. One-shot iteration driver

`scripts/iter_run_stage2.py` chains everything:
patch apply → pipeline → tri-judge → quant probes → comparison → commit.
This is how the iteration loop actually runs:

```bash
python scripts/iter_run_stage2.py \
    --iter iter_01_semdedup_cosine_90 \
    --parent iter_00_baseline \
    --patch patches/SD1_intent_cosine_90.diff \
    --hypothesis "embed Stage 2.1 rows and drop cosine >= 0.90 duplicates"
```

---

## Results inspection

### Per-iter folder (the canonical unit of work)

```
experiments/iter_21_dedup_v2/
├── hypothesis.md                one-paragraph: what we're testing
├── patch.diff                   minimal code delta vs parent iter
├── pipeline_script.py           frozen pipeline snapshot (reruns verbatim)
├── metrics.json                 tri-judge ensemble + quant probes + sha256
├── judge_report.md              human-readable judge summary
├── quant_report.md              deterministic probes report
├── comparison.md                delta table vs parent
├── run_log.txt                  iteration stdout
└── output/                      (gitignored) JSONL artefacts
    ├── stage_1_0_seed.jsonl
    ├── stage_1_1_synthetic.jsonl
    ├── stage_1_1_5_deduped.jsonl
    └── stage_1_2_processed.jsonl
```

### `metrics.json` schema (Stage 1 example)

```json
{
  "iter_id": "iter_21_dedup_v2",
  "parent_iter": "iter_20_title_fix_stack",
  "output_hashes": { "stage_1_2_processed.jsonl": "5e513bc7…" },
  "stage_1_0": { "avg_text_quality": {"glm": 2.8, "deepseek": 2.9, "qwen3": 2.7, "mean": 2.80, "range": 0.2}, ... },
  "stage_1_1": { ... },
  "stage_1_2": { ... },
  "quant": { "title_reasoning_leak_rate": 0.013, ... },
  "promote": true,
  "promote_checks": { "passed": 8, "total": 10, "failed": ["avg_text_quality", "dedup_miss_rate"] },
  "high_variance": []
}
```

### Higher-level narratives

| Document | What's in it |
|---|---|
| `experiments/PLAN.md` | Stage 1 hypothesis queue, metric thresholds, iteration plan |
| `experiments/REPORT.md` | **23-iter full narrative** — wins, losses, blockers, scaling story |
| `experiments/summary.md` | rolling leaderboard across all iters |
| `experiments_stage2/PLAN.md` | Stage 2 hypothesis queue (SD + C + E + A + X) |
| `experiments_stage2/README.md` | Stage 2 operational quick-start |
| `presentation/` | hackathon deck + scripts (see `presentation/README` files for deck vs briefing) |

### Browse the best-known iter

```bash
# the best Stage 1 pipeline to date
cat experiments/iter_21_dedup_v2/metrics.json     | jq .promote_checks
cat experiments/iter_21_dedup_v2/judge_report.md
cat experiments/iter_21_dedup_v2/comparison.md
```

---

## Example final output (50-doc sample)

```
[캐주얼]   (evidence=12)  cotton 0.117, 린넨 0.071, 길이감 0.071, loose 0.067, ...
[하객룩]   (evidence=2)   material=tweed 0.91, fit=neat 0.46, fit=tailored 0.45
[오피스룩] (evidence=2)   material=linen blend 0.44, fit=relaxed 0.44, color=light beige 0.44
[홈웨어]   (evidence=2)   fit=이상한 재단 0.3
[스크린골프] (evidence=3) style=기능성 0.55, fit=slim 0.45, material=stretch 0.33
[필라테스 레이어] (evidence=2) fit=slim 0.6, style=layered 0.5
[일반]     (evidence=22)  general-wear fallback bucket
```

Stage 2.4 then expands each of these into 5 natural-language queries:

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
  "data_lineage": {"total_evidence_count": 6, "source_doc_ids": ["rv-wed-001", ...]}
}
```

---

## Known limitations

1. **`stage_1_0.avg_text_quality ≥ 3.5`** — the raw Naver corpus is
   structurally low-quality (all three judges score seeds 2.7–2.9
   regardless of sampling). Clearing this requires a curated seed
   corpus, which was out of scope for a hackathon.
2. **`stage_1_1_5.dedup_miss_rate ≤ 0.05`** — pure-Python Jaccard
   fallbacks fired zero removals. The real fix is semantic dedup,
   now queued in Stage 2.1.5 (SD-series) and running on the Stage 2
   iteration branch.
3. **NeMo Data Designer API skew** — Stage 2.4 prefers the structured
   `SamplerColumn → LLMStructuredColumn` path, but falls back to a
   direct-call loop when the Curator synthetic API signature drifts.
   Force the fallback with `--force-fallback`.

---

## CLI reference (reference only — see §Running the pipeline above for typical use)

### `pipelines.stage_2_1_extract`

| flag | default | meaning |
|---|---|---|
| `--input` | `data/curated_sample.jsonl` | curated JSONL |
| `--output` | `data/stage_2_1_extracted.jsonl` | |
| `--limit` | `0` | 0 = every input |
| `--sleep` | `0.3` | seconds between async calls |

### `pipelines.stage_2_1_5_semdedup` *(new)*

| flag | default | meaning |
|---|---|---|
| `--input` | `data/stage_2_1_extracted.jsonl` | |
| `--output` | `data/stage_2_1_5_deduped.jsonl` | + writes `stage_2_1_5_stats.json` side-car |
| `--threshold` | `0.90` | cosine threshold; higher = more conservative |
| `--embed-model` | `BAAI/bge-m3` | |
| `--signature-builder` | `full` | `full` = intent + keywords + attrs; `signature_combo` = intent + attrs |

### `pipelines.stage_2_2_canonicalize`

| flag | default | meaning |
|---|---|---|
| `--input` | `data/stage_2_1_extracted.jsonl` | |
| `--output` | `data/stage_2_2_clusters.jsonl` | |
| `--embed-model` | `BAAI/bge-m3` | |
| `--threshold` | `0.35` | cosine distance cutoff for Agglomerative clustering |
| `--refine` | off | LLM splits over-merged clusters |
| `--cross-merge` | off | LLM merges duplicate canonicals |
| `--skip-canonical` | off | skip LLM canonical naming |
| `--stage` | `full` | `full` \| `embed_cluster_only` \| `llm_finalize` (phase-split mode) |

### `pipelines.stage_2_3_aggregate`

| flag | default | meaning |
|---|---|---|
| `--top-k` | `3` | top-N attribute values per key |
| `--skip-general` | off | drop the "일반" cluster |

### `pipelines.stage_2_4_expand`

| flag | default | meaning |
|---|---|---|
| `--n-queries` | `5` | queries per canonical |
| `--force-fallback` | off | skip Data Designer path, always use direct call |
| `--provider` | `$LLM_PROVIDER` | `nim` / `friendli` / `vllm` |

---

## Further reading

- **`experiments/PLAN.md`** + **`experiments/REPORT.md`** — Stage 1
  iteration plan and its 23-iter outcome narrative
- **`experiments_stage2/PLAN.md`** — Stage 2 iteration plan
  (SD + C + E + A + X hypothesis queues)
- **`presentation/`** — hackathon deck (9 slides) + 5-min pitch script
  (Korean) + 10-min expert briefing (English) + 1.5-min walk-through
  card (English)
