# Stage 1 Pipeline (adopted from iter_21_dedup_v2, 8/10 promote gates)

This is the canonical Stage 1 pipeline for the personalized fashion
review corpus. It was promoted to `main` from
`experiments/iter_21_dedup_v2/pipeline_script.py` after 23 iterations
of the iterative improvement loop documented in
`experiments/REPORT.md`.

A later follow-up wave (iter_24–iter_27, see REPORT.md §10) added a
semantic-dedup step that runs on a separate GPU instance `coupang2`
because `coupang` vLLM owns the full 2×H100 memory footprint. Use
`scripts/run_semantic_dedup_v2.py` with
`--emb-mode title_attrs --eps 0.18` to insert that step between
Stage 1.1 and Stage 1.2; iter_27 reaches **7/10 gates stably** with
this two-instance topology.

## What it does

1. **Stage 1.0 — Seed extraction**: loads Naver shopping reviews,
   applies `FASHION_KEYWORDS` filter, samples N rows.
2. **Stage 1.1 — Synthetic generation** (NeMo Data Designer):
   - injects a random Naver review as context per row
   - **samples rating from CategorySampler(values=[1,2,3,4,5])**
     (H4v2: the Naver corpus has zero rating=3 rows, so we decouple
     synthetic rating from the seed)
   - generates `product_title` via LLM-text column
   - generates `product_attributes` (color/style/size) via LLM-structured column — prompt now references `{{ seed_review }}` for grounding (H5v2)
   - generates `raw_text` review — prompt forces 2+ persona field
     citations (H8) AND explicit color/style/size mention (H11)
   - applies deterministic title postprocessor (H3+H3v3) to strip
     reasoning-leak patterns: `(Nの자)`, bare `N자`, parenthetical
     size notes, markdown `**수정 사항:**` blocks
   - applies post-gen fashion filter (H12) to drop synthetic records
     whose titles contain non-fashion keywords (정리함, 옷걸이, 기저귀, …)
3. **Stage 1.1.5 — Dedup**: wraps NeMo Curator fuzzy dedup with a
   Python Jaccard-bigram near-dedup fallback when `cudf` is missing
   (H14v2). See hypothesis limitations below.
4. **Stage 1.2 — Quality filter**: Korean-aware Hangul filter (H9)
   replacing NeMo Curator's `NonAlphaNumericFilter` which treated
   Hangul as non-alphanumeric and dropped ~99% of Korean reviews.

## Promote-gate status at adoption

On a 50-record run (iter_21) this pipeline passes 8 of the 10
promote-bar gates defined in `experiments/PLAN.md §6`:

Pass:
- `stage_1_0.fashion_rate ≥ 0.90` (0.90, borderline)
- `stage_1_1.title_reasoning_leak_rate ≤ 0.02` (0.013)
- `stage_1_1.fashion_rate ≥ 0.95` (0.97)
- `stage_1_1.attr_grounded_rate ≥ 0.70` (0.99)
- `stage_1_1.avg_persona_reflection ≥ 3.5` (4.66)
- `quant.rating_3_share > 0` (0.26)
- `stage_1_2.retention_from_stage_1_1_5 ≥ 0.85` (1.0)
- `stage_1_2.fashion_rate ≥ 0.95` (0.97)

Not passing (structural):
- `stage_1_0.avg_text_quality ≥ 3.5` (≈ 2.83 — the Naver corpus
  ceiling; requires a curated seed set to clear)
- `stage_1_1_5.dedup_miss_rate ≤ 0.05` (≈ 0.15 — the Python Jaccard
  fallback fires but doesn't actually remove records because judge-
  flagged near-dups share semantic content, not string tokens. The
  proper fix is H10 = `pip install cudf-cu12` on coupang + switching
  to `TextSemanticDeduplicationWorkflow`. An alternative
  signature-based exact dedup is staged but unrun at
  `experiments/iter_23_signature_dedup/`.)

## How to run

On coupang (the production location):

```bash
export LLM_EXTRA_BODY='{"chat_template_kwargs":{"enable_thinking":false}}'
/home/nvidia/coupang/.venv/bin/python pipelines/stage_1/data_pipeline_vllm.py \
    --data-path /home/nvidia/stage1_work/data/naver_shopping.txt \
    --generate-size 50
```

This writes:
- `data/stage_1_0/seed_data.jsonl`
- `data/stage_1_1/synthetic_data.jsonl`
- `data/stage_1_1_5/deduped.jsonl`
- `data/stage_1_2/processed_reviews.jsonl`

## How to evaluate

```bash
python scripts/tri_judge_run.py \
    --output-dir    <wherever the 4 jsonls are> \
    --stage-data-root $STAGE_DATA_ROOT \
    --judge-raw-dir ./judge_raw \
    --metrics-out   ./judge_metrics.json \
    --provider friendli \
    --run-id my_run --tag my_tag
python scripts/quant_stage1_report.py \
    --output-dir <wherever the 4 jsonls are> \
    --json-out ./quant_metrics.json \
    --md-out ./quant_report.md
```

## Further reading

- `experiments/REPORT.md` — end-of-run iteration report (23 iters)
- `experiments/PLAN.md` — the original plan for the iterative loop
- `experiments/summary.md` — rolling leaderboard
- `experiments/iter_NN_<slug>/` — per-iteration artifacts for any
  iteration referenced in the report
