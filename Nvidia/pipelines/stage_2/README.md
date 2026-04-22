# Stage 2 Pipeline (unified one-file orchestrator)

Mirror of `pipelines/stage_1/data_pipeline_vllm.py`, but for Stage 2
(intent extraction → canonicalization → aggregation → expansion). The
whole flow runs as a single process that loads the vLLM model **once**
and walks through all four sub-stages in order.

## Flow

```
stage_1_2/*.jsonl
       │  (CuratedDoc[])
       ▼
 ┌─────────────────┐  stage_2_1/stage_2_1_extracted.jsonl
 │  2.1 extract    │  — per-doc {raw_intent, attributes}
 └─────────────────┘
       │  (ExtractedIntent[])
       ▼
 ┌─────────────────┐  stage_2_2/stage_2_2_clusters.jsonl
 │  2.2 canonical  │  — embed (BGE-M3) + cluster + LLM refine
 └─────────────────┘     + canonical naming + cross-merge
       │  (IntentCluster[])
       ▼
 ┌─────────────────┐  stage_2_3/analyzed_intents.jsonl
 │  2.3 aggregate  │  — pure Python; weighted attribute profile
 └─────────────────┘     per canonical cluster (no LLM)
       │  (AnalyzedIntent[])
       ▼
 ┌─────────────────┐  stage_2_4/expanded_intents.jsonl
 │  2.4 expand     │  — N natural_queries per canonical intent
 └─────────────────┘
       ▼
  (ExpandedIntent[])
```

## Usage

```bash
# Full pipeline, default paths
cd ~/stage2_work
python scripts/run_stage_2_pipeline_vllm.py \
    --input  /home/nvidia/data/stage_1_2 \
    --output-root /home/nvidia/data

# Equivalent (entry point is also directly runnable as a module):
python -m pipelines.stage_2.data_pipeline_stage2_vllm ...
```

### Stop early

```bash
# Only run 2.1
python scripts/run_stage_2_pipeline_vllm.py --stop-after extract

# Skip the expensive extract step and reuse its existing output
python scripts/run_stage_2_pipeline_vllm.py --skip-extract

# Skip every LLM-heavy step; just re-aggregate on existing artifacts
python scripts/run_stage_2_pipeline_vllm.py \
    --skip-extract --skip-canonicalize --skip-expand
```

### Tuning knobs

| flag | env var | default |
|---|---|---|
| `--model` | `VLLM_OFFLINE_MODEL` | `nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B-BF16` |
| `--dtype` | `VLLM_DTYPE` | `auto` |
| `--gpu-mem-util` | `VLLM_GPU_MEM_UTIL` | (let vLLM pick) |
| `--embed-model` | `EMBED_MODEL` | `BAAI/bge-m3` |
| `--cluster-threshold` | `CLUSTER_THRESHOLD` | `0.35` |
| `--refine-min-size` | `REFINE_MIN_SIZE` | `3` |
| `--n-queries` | `STAGE_N_QUERIES` | `5` (queries per canonical) |
| `--aggregate-top-k` | `AGGREGATE_TOP_K` | `3` |
| `--stage-limit` | `STAGE_LIMIT` | `0` (all docs) |

### Skip flags

- `--skip-refine` — disable LLM refine step in Stage 2.2
- `--skip-cross-merge` — disable LLM cross-cluster merge
- `--skip-general` — drop the `일반` / `general_wear` cluster at 2.3
- `--skip-extract` / `--skip-canonicalize` / `--skip-aggregate` /
  `--skip-expand` — skip individual stages (loads existing output if
  available)

## Why a unified pipeline matters

Previously Stage 2 was a collection of standalone drivers
(`scripts/run_stage_2_1_vllm.py`, `..._2.py`, `..._4.py`, plus
`pipelines/stage_2_3_aggregate.py`). Each loaded and tore down its own
vLLM session, costing 2–5 minutes per stage just for model warmup.

This orchestrator:

1. Loads vLLM once (single `vllm.LLM(...)` call, kept alive).
2. Reuses the same `VLLMOfflineClient` wrapper across stages 2.1, 2.2,
   2.4 via the existing `pipelines.vllm_adapter` / `pipelines.stage_2_2_canonicalize`
   library functions — no code duplication.
3. Chains outputs via canonical paths under `$STAGE_DATA_ROOT`, so
   intermediate files look identical to the original standalone runs
   (important for `iter_run_stage2.py` and the tri-judge eval).
4. Exposes per-stage skip / stop-after flags for fast iteration when
   debugging a specific stage.

## Output layout (no change from standalone drivers)

```
$STAGE_DATA_ROOT/
├── stage_2_1/stage_2_1_extracted.jsonl     (from 2.1)
├── stage_2_2/stage_2_2_clusters.jsonl      (from 2.2)
├── stage_2_3/analyzed_intents.jsonl        (from 2.3)
└── stage_2_4/expanded_intents.jsonl        (from 2.4)
```

Each file has the same schema as what the individual
`run_stage_2_N_vllm.py` drivers emit; the `iter_run_stage2.py` eval
loop will find and grade them without any change.

## Summary line

At the end of a run:

```
[pipeline] SUMMARY
                      extracted: 42
                       clusters: 15
                       analyzed: 15
                       expanded: 15
     expanded_natural_queries: 75
```

This is the quick "did everything flow" check — numbers should
monotonically funnel down from curated docs → extracted intents →
clusters → canonical intents, with `expanded_natural_queries` equal
to `n_queries × analyzed`.
