# Handoff — iter_01 onward

**Current branch**: `experiment/stage1-iterative-improvement`  (on commit `a5876f9`)
**Parent baseline**: `main@cd17cd3`
**iter_00 status**: DONE (see `experiments/iter_00_baseline/`).

## What iter_00 measured (50 records, tri-judge GLM+DeepSeek+Qwen3)

| metric | baseline | promote bar |
|---|---:|---:|
| stage_1_1 title_reasoning_leak_rate | **0.473** | ≤ 0.02 |
| stage_1_1 fashion_rate              | 0.853    | ≥ 0.95 |
| stage_1_1 attr_grounded_rate        | 0.467    | ≥ 0.70 |
| stage_1_1 avg_persona_reflection    | **3.62** | ≥ 3.5  ✅ only pass |
| stage_1_1 has_tpo_rate              | 0.947    | ≥ 0.85 ✅ (not in bar) |
| stage_1_1 raw_text_naturalness      | 3.98     | ≥ 4.0  (close) |
| quant   rating_3_share              | 0.0      | > 0 |
| quant   title_len_p90 / max         | n/a (in quant_metrics.json) | |
| stage_1_1_5 dedup_reduction_rate    | 0.0      | ≥ 0.05 |
| stage_1_1_5 mean_dedup_miss_rate    | ~0.15    | ≤ 0.05 |
| stage_1_2 retention_from_stage_1_1_5 | 0.04    | ≥ 0.85 |
| e2e retention                       | 0.04     | ≥ 0.80 |

Only `persona_reflection` passed. Everything else red.

## How to run iter_NN

```bash
cd /Users/sgyeom/Nvidia
source .venv/bin/activate

python scripts/iter_run.py \
    --iter-id 01 \
    --slug title_prompt_strict \
    --parent-iter iter_00_baseline \
    --hypothesis-file experiments/iter_01_title_prompt_strict/hypothesis.md \
    --patch experiments/iter_01_title_prompt_strict/patch.diff \
    --n-records 50 \
    --headline "H1: drop char-count self-verify; single-line title rule"
```

The driver:
1. copies `iter_00_baseline/pipeline_script.py` into `iter_01_title_prompt_strict/`
2. applies `patch.diff` against the copy (if given)
3. uploads to coupang, runs Stage 1 pipeline (~15 s)
4. pulls the 4 output JSONLs back
5. runs `tri_judge_run.py` on coupang (4 parallel, ~8-12 min)
6. runs `quant_stage1_report.py` locally
7. writes `metrics.json`, `judge_report.md`, `quant_report.md`, `comparison.md`
8. `git commit`

## Hypothesis queue (from PLAN §5)

Pull the next one from the top of this list.

| # | slug | affects | summary |
|---|---|---|---|
| **H1** | `title_prompt_strict` | 1.1 | drop char-count self-verify from TITLE_PROMPT; add "ONE LINE, no arrows, no self-check" |
| H2 | `title_max_tokens_short` | 1.1 | cap title column's max_tokens to 60 (budget starves reasoning) |
| H3 | `title_postprocess` | 1.1 | post-hoc `_clean_title()` keeps first line ≤ 30 chars, strips `→` / `글자` |
| H4 | `seed_rating_3_injection` | 1.0→1.1→1.2 | stratify seed sampling by rating 1-5 so rating=3 is present |
| H5 | `attr_diversity_prompt` | 1.1 | re-write ATTR_PROMPT to vary per persona+title, break 캐주얼 collapse |
| H6 | `size_plausibility_filter` | 1.1→1.2 | drop/relabel records with non-apparel sizes (13개월, 250) |
| H7 | `non_fashion_seed_filter` | 1.0→1.1→1.2 | 2-layer FASHION_KEYWORDS (include + exclude) |
| H8 | `persona_binding_prompt` | 1.1 | force REVIEW_PROMPT to cite 2 of {hobbies, occupation, province, age} |
| **H9** | `korean_quality_filter` | 1.2 | remove NonAlphaNumericFilter or replace with `min_korean_chars=20` |
| **H10** | `install_cudf_semdedup` | 1.1.5 | `pip install cudf-cu12` + swap FuzzyDedup → TextSemanticDeduplicationWorkflow |

Ordered roughly by expected yield × ease. H9 and H10 fix infra (Stage 1.2 and 1.1.5); H1-H3 attack the leak; H4-H5 attack mode collapse.

## For each iteration, produce

```
experiments/iter_NN_<slug>/
├── hypothesis.md         # what and why (1 paragraph)
├── patch.diff             # `git diff` against iter_NN-1/pipeline_script.py
├── pipeline_script.py     # iter_run.py fills this in
└── (iter_run.py writes the rest)
```

The `patch.diff` should be minimal — one hypothesis per iteration. If you
need to combine fixes, run them as separate iterations and the
leaderboard will show which contributed.

## Files to upload on coupang after any code change

The pipeline runs remotely on coupang, but `iter_run.py` does NOT sync
code for you. After editing `pipelines/eval/*` or `scripts/tri_judge_run.py`
on local, tar + brev copy + extract:

```bash
cd /Users/sgyeom/Nvidia
tar -cf /tmp/sync.tar scripts/tri_judge_run.py \
    pipelines/eval/common.py pipelines/eval/schemas.py \
    pipelines/eval/prompts.py pipelines/eval/stage_1_1_judge.py \
    pipelines/eval/stage_1_1_5_judge.py pipelines/eval/stage_1_2_judge.py \
    pipelines/eval/judge_client.py pipelines/eval/__main__.py
brev copy /tmp/sync.tar coupang:/tmp/sync.tar
brev exec coupang "cd /home/nvidia/stage2_work && tar -xf /tmp/sync.tar && rm -f /tmp/sync.tar"
```

Per-file `brev copy` takes ~25 s each because of handshake overhead;
tar-one-shot is ~30 s total.

## Known issues

1. **Stage 1.0 fashion_rate / avg_text_quality = missing** in iter_00_baseline
   because stage_1_2_judge crashed on seed format (`{rating, text}` vs
   `CuratedDoc`). FIXED in commit `a5876f9`; iter_01 will include Stage 1.0
   metrics. If you want iter_00 to have them too, re-run:
   ```bash
   rm -rf experiments/iter_00_baseline/judge_raw experiments/iter_00_baseline/judge_metrics.json
   python scripts/iter_run.py --iter-id 00 --slug baseline --skip-pipeline --headline "baseline re-eval with seed tolerance"
   ```
   (`--skip-pipeline` reuses existing output/ so this takes only ~8-10 min.)

2. **cudf** not installed on coupang. H10 iteration will `pip install cudf-cu12`;
   every other iteration falls back to exact dedup (no-op). So
   `dedup_reduction_rate` stays 0 until H10.

3. **FRIENDLI_API_KEY** is on coupang at `/home/nvidia/stage2_work/.env`.
   The local `.env` only has `NVIDIA_API_KEY`; iter_run.py routes judge
   calls to coupang so local key isn't needed.

## Leaderboard

`experiments/summary.md` is the rolling table. Do NOT edit by hand —
`scripts/make_comparison.py` upserts iter rows automatically.

## Commit messages

`iter_NN_<slug>: <hypothesis one-liner> <headline metric Δ>`

Example from iter_00: `iter_00_baseline: baseline, tri-judge parallel=4`.
