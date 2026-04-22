# Stage 2 Iterative Improvement — Experiments

Parallel to `experiments/` (Stage 1 loop). Stage-1 output is frozen
at **iter_21_dedup_v2** and pinned as the Stage-2 input; every Stage-2
iter re-runs **all four Stage-2 sub-stages** (2.1 extract → 2.2
canonicalize → 2.3 aggregate → 2.4 expand) against it.

See **`PLAN.md`** for the full spec. This README is operational.

## Layout

```
experiments_stage2/
├── PLAN.md                          full spec
├── README.md                        this file
├── ENV.md                           coupang2 spec + routing decision
├── summary.md                       rolling leaderboard
├── stage1_pinned/                   (gitignored)
│   ├── stage_1_2_processed.jsonl    42 rows from iter_21
│   └── INPUT_SHA256                 hash verification
├── iter_00_baseline/                SD-off baseline; all 5 scripts frozen
│   ├── hypothesis.md
│   ├── pipeline_snapshot/           vendored copies of the 5 entry points
│   │   ├── stage_2_1_extract.py
│   │   ├── stage_2_1_5_semdedup.py  (pass-through for SD-off)
│   │   ├── stage_2_2_canonicalize.py
│   │   ├── stage_2_3_aggregate.py
│   │   └── stage_2_4_expand.py
│   ├── metrics.json                 5-stage ensemble + hashes
│   ├── judge_report.md
│   ├── quant_report.md              §4e probes
│   ├── comparison.md                (iter_00 has none)
│   ├── run_log.txt
│   ├── output/                      (gitignored; 5 JSONL + 1 stats)
│   └── judge_raw/                   (gitignored, 12 files)
├── iter_00a_semdedup_probe/         (one-shot, no pipeline run)
│   ├── semdedup_probe.json          PLAN §5a probe output
│   └── notes.md
├── iter_NN_<slug>/
│   ├── hypothesis.md                what & why
│   ├── patch.diff                   against iter_00 pipeline_snapshot/
│   ├── pipeline_snapshot/           per-iter vendored files (symlinks for
│   │                                unchanged entries)
│   ├── metrics.json
│   ├── judge_report.md
│   ├── quant_report.md
│   ├── comparison.md                delta vs parent
│   ├── run_log.txt
│   ├── output/                      (gitignored)
│   └── judge_raw/                   (gitignored, 12 files)
└── winners/                         (gitignored)
```

## Quick-start

```bash
# 1) branch
git checkout main
git pull
git checkout -b experiment/stage2-iterative-improvement

# 2) pin Stage-1 input  (already present in repo but re-create if missing)
mkdir -p experiments_stage2/stage1_pinned
cp experiments/iter_21_dedup_v2/output/stage_1_2_processed.jsonl \
   experiments_stage2/stage1_pinned/stage_1_2_processed.jsonl
sha256sum experiments_stage2/stage1_pinned/stage_1_2_processed.jsonl \
   > experiments_stage2/stage1_pinned/INPUT_SHA256

# 3) iter_00 baseline  (run after infra scripts below exist)
PYTHONPATH=. FRIENDLI_API_KEY=... .venv/bin/python \
    scripts/iter_run_stage2.py \
    --iter iter_00_baseline \
    --parent none \
    --semdedup off \
    --hypothesis "baseline, no changes; frozen pipeline from main@HEAD"

# 4) iter_00a semantic-dedup probe (PLAN §5a; no pipeline run)
.venv/bin/python scripts/quant_stage2_report.py \
    --mode semdedup-probe \
    --input experiments_stage2/iter_00_baseline/output/stage_2_1_extracted.jsonl \
    --thresholds 0.95,0.90,0.85,0.80,0.75,0.70 \
    --signature full \
    --out experiments_stage2/iter_00a_semdedup_probe/semdedup_probe.json

# 5) subsequent iter (e.g. SD1 — threshold taken from the probe)
.venv/bin/python scripts/iter_run_stage2.py \
    --iter iter_01_semdedup_intent_cosine_90 \
    --parent iter_00_baseline \
    --patch patches/SD1_semdedup_full_90.diff \
    --semdedup 0.90 \
    --hypothesis "SD1 full builder @ 0.90 (or probe-selected threshold)"
```

## New infra added for Stage 2

| script | role |
|---|---|
| `pipelines/stage_2_1_5_semdedup.py` | **new** Stage 2.1.5 embedding-based semantic dedup (runs on coupang2; SD-series hypothesis enabler). Supports `--signature-builder {full, signature_combo, intent_only}` per PLAN §5. |
| `scripts/tri_judge_run_stage2.py` | 4-stage × 3-judge orchestrator (mirror of `tri_judge_run.py`, input-file mapping swapped) |
| `scripts/quant_stage2_report.py` | two modes: `--mode iter` emits §4e deterministic probes (semdedup retention, canonical suffix / non-fashion / query dedup); `--mode semdedup-probe` runs PLAN §5a one-shot pre-SD probe across threshold grid |
| `scripts/iter_run_stage2.py` | sealed driver: patch → Stage 2.1 on coupang → Stage 2.1.5 semdedup on coupang2 → Stage 2.2 phase-1 on coupang2 → Stage 2.2 phase-2 on coupang → Stage 2.3 on coupang2 → Stage 2.4 on coupang → judge → quant → commit. Also builds per-iter `pipeline_snapshot/`. |

`scripts/make_comparison.py` is re-used as-is — `metrics.json` schema
is the same (`stage_2_*` namespaces instead of `stage_1_*`; SD just
adds new keys).

## Two-instance compute topology

`coupang` keeps serving vLLM Nemotron-Super 120B and is RAM/GPU
saturated. `coupang2` is a substantial instance dedicated to semantic
/ embedding workloads — enabling **embedding-based semantic dedup**
(Stage 2.1.5, previously blocked by `coupang` OOM), agglomerative
clustering, and any future heavy-compute ops. See PLAN §3b for
routing options and §8 for the 14-step per-iter recipe.

## Data flow per iter

```
experiments_stage2/stage1_pinned/stage_1_2_processed.jsonl  (42 rows)
        │
        │  brev copy → coupang:$STAGE_DATA_ROOT/stage_1_2/
        │
        ▼
[coupang vLLM]   Stage 2.1 extract     → stage_2_1_extracted.jsonl      (42)
        │
        │  brev copy ← coupang → local → brev copy → coupang2
        │
        ▼
[coupang2]       Stage 2.1.5 semdedup  → stage_2_1_5_deduped.jsonl      (~25-35)
                 BGE-M3 + cosine >= thr      + stage_2_1_5_stats.json
        │
        │  (if SD off: stage_2_1_5_deduped = stage_2_1_extracted)
        │
        ▼
[coupang2 CPU]   Stage 2.2 phase 1     → stage_2_2_clusters_raw.jsonl   (5-12)
                 embed + agglomerative
        │
        │  brev copy ← coupang2 → local → brev copy → coupang
        │
        ▼
[coupang vLLM]   Stage 2.2 phase 2     → stage_2_2_clusters.jsonl       (5-12)
                 refine + canonical naming + cross-merge
        │
        │  brev copy ← coupang → local → brev copy → coupang2
        │
        ▼
[coupang2 CPU]   Stage 2.3 aggregate   → stage_2_3_analyzed.jsonl       (5-12)
        │
        │  brev copy ← coupang2 → local → brev copy → coupang
        │
        ▼
[coupang vLLM]   Stage 2.4 expand      → stage_2_4_expanded.jsonl       (5-12 × 5)
        │
        │  brev copy ← coupang → local experiments_stage2/iter_NN/output/
        │
        ▼
[local / Friendli] tri_judge_run_stage2 → judge_raw/ (12 files, ~200 calls)
[local]           quant_stage2_report  → quant_report.md (+ semdedup_*)
[local]           make_comparison      → comparison.md
        │
        ▼
git commit: "iter_NN_<slug>: <one-liner> <Δ headline>"
```

If coupang2 ↔ coupang:5000 internal networking turns out to be reachable,
the driver collapses phase 1 + phase 2 onto coupang2 (PLAN §3b Option A).

## Cost envelope

- **~200 Friendli judge calls per iter** (vs ~90 in Stage 1).
- 15 iter × 200 = 3 k calls ≈ 3-4 M judge tokens, under serverless
  hackathon quota with margin.
- vLLM (Nemotron-Super on coupang) does every pipeline-side LLM call
  — no additional cost.
- `coupang2` is CPU/RAM only for Stage 2 (sentence-transformers +
  scipy linkage); no extra GPU hours beyond what the instance already
  provides.

## Promotion criteria (summary — full table in PLAN §6)

All four sub-stages' promotion bars must pass simultaneously:
- **2.1** grounding ≥ 4.0, intent valid ≥ 0.90, material concrete ≥ 0.80
- **2.2** coherent ≥ 0.85, canonical fit ≥ 4.0, non-fashion ≤ 5 %, duplicates ≤ 1
- **2.3** usefulness ≥ 4.0, attr fits ≥ 0.85, duplicate values ≤ 2
- **2.4** usefulness ≥ 4.0, natural ≥ 0.90, diversity ≥ 3.5, repeat ≤ 0.10, garbled = 0
