# Stage 1 Iterative Improvement Plan

**Branch**: `experiment/stage1-iterative-improvement`
**Parent commit (baseline)**: `cd17cd3`
**Time budget**: **12 hours** (hard cap, no early plateau stop)
**Records per iteration**: **50**
**Judge ensemble**: **GLM-5.1 + DeepSeek-V3.2 + Qwen3-235B** on Friendli
**Scope**: Stage 1 only. Stage 2 is frozen at baseline until Stage 1 quality crosses the promotion bar (see §6).

---

## 1. Goal

Improve the Stage-1 pipeline (sub-stages **1.0 seed / 1.1 synthesis /
1.1.5 dedup / 1.2 filter**) until every one of them clears the promotion
bar in §6 under a tri-judge ensemble, then hand back to Stage 2.

We drive down the 11 failure modes the Stage 1.1 judge emits
(`pipelines/eval/schemas.py::STAGE_1_1_FAILURE_MODES`) AND the 6
failure modes the Stage 1.2 judge emits (`STAGE_1_2_FAILURE_MODES`)
AND close the Stage 1.1.5 dedup gap, through a controlled, git-tracked
loop of:

    generate 4-stage outputs at 50 rec → tri-judge each stage → read
    the worst-K → hypothesise → patch → regenerate → compare

Every iteration is a self-contained folder under `experiments/` so a
reviewer can reconstruct what was tried and why, independently of the
agent's chat history.

## 2. Non-goals

- Big-N runs. **50 records per iteration is the default**; scaling is a
  separate problem once quality is acceptable.
- Stage 2 tuning. Stage 2 is promoted once Stage 1 passes §6.
- New judge rubrics. The four judge schemas are fixed for the run
  (otherwise we can't compare across iterations).

## 3. Ground rules

- All changes live on `experiment/stage1-iterative-improvement`. Each
  iteration is one commit whose subject line encodes the
  `iter_NN_<slug>` that corresponds to the experiment folder.
- `data/` on disk and per-iteration `output/` + `judge_raw/` are **never**
  committed (see `.gitignore`). The distilled numbers (`metrics.json`,
  `judge_report.md`, `comparison.md`, `hypothesis.md`, `run_log.txt`,
  `pipeline_script.py`) ARE committed so the history is reproducible.
- The baseline `data_pipeline_vllm.py` on coupang stays as-is; each
  iteration writes its own modified copy into
  `experiments/iter_NN_<slug>/pipeline_script.py` and runs it against
  the shared localhost vLLM endpoint (`localhost:5000/v1`, model `nemotron`).
- Pipeline scripts always set
  `LLM_EXTRA_BODY='{"chat_template_kwargs":{"enable_thinking":false}}'`
  so Nemotron-Super doesn't dump reasoning into content.

### 3a. Data versioning (simple copy model)

Each iteration's pipeline produces FOUR Stage-1 outputs (not one):

```
output/
├── stage_1_0_seed.jsonl           # Stage 1.0 seed extraction
├── stage_1_1_synthetic.jsonl      # Stage 1.1 Data Designer synthesis
├── stage_1_1_5_deduped.jsonl      # Stage 1.1.5 dedup survivors
└── stage_1_2_processed.jsonl      # Stage 1.2 quality filter survivors
```

All four land in `experiments/iter_NN_<slug>/output/` by plain `cp`.
No DVC, no S3, no tarballs. This directory is gitignored, so the Git
repo stays small; the data sits next to the git commit on local disk.

For reproducibility WITHOUT committing blobs:

- `metrics.json` (git-tracked) records the `sha256` + line count of each
  of the four jsonl files. A reviewer can hash their local copy and
  confirm they are looking at the exact data the metric row came from.
- The `pipeline_script.py` + `patch.diff` is enough to regenerate
  byte-identical output if the vLLM server is still serving the same
  model (seed is fixed inside the Data Designer config).

If a reviewer needs to carry data off-box, they copy
`experiments/iter_NN_<slug>/` wholesale; everything they need is there.

## 4. Metric sheet (success/regression detector)

Stage 1 has four sub-stages; every one of them is evaluated. `metrics.json`
per iteration rolls all four up into a single dictionary. Metrics come
from two sources: **LLM judge ensemble** (GLM-5.1 / DeepSeek-V3.2 / Qwen3-235B
on Friendli) and **deterministic probes** (pure Python, no LLM).

### 4a. Stage 1.0 — seed extraction quality
Input: raw `naver_shopping.txt` rows after `FASHION_KEYWORDS` filter.
Output: `stage_1_0_seed.jsonl` (usually 50 rows after sampling).
Judge: reuses `pipelines.eval.stage_1_2_judge` (same rubric shape
because a seed row is shaped like a curated doc).

| metric (per-judge + mean)          | direction | promote-threshold |
|------------------------------------|-----------|-------------------|
| `fashion_rate`                     | ↑         | ≥ 0.90            |
| `has_tpo_rate`                     | ↑         | ≥ 0.40 (seed is raw) |
| `avg_text_quality`                 | ↑         | ≥ 3.5 / 5         |
| `pii_rate`                         | ↓         | ≤ 0.02            |
| `noise_level_hist.high_rate`       | ↓         | ≤ 0.05            |

### 4b. Stage 1.1 — synthetic review quality  *(the hot spot)*
Input: the 50 seeds × persona dataset.
Output: `stage_1_1_synthetic.jsonl` (50 rows).
Judge: `pipelines.eval.stage_1_1_judge` (new in this run).

| metric (per-judge + mean)                 | direction | promote-threshold |
|-------------------------------------------|-----------|-------------------|
| `fashion_rate`                            | ↑         | ≥ 0.95            |
| `title_within_spec_rate`                  | ↑         | ≥ 0.80            |
| `title_format_ok_rate`                    | ↑         | ≥ 0.80            |
| `title_reasoning_leak_rate`               | ↓         | ≤ 0.02            |
| `raw_text_within_spec_rate`               | ↑         | ≥ 0.90            |
| `avg_raw_text_naturalness`                | ↑         | ≥ 4.0 / 5         |
| `avg_persona_reflection`                  | ↑         | ≥ 3.5 / 5         |
| `has_tpo_rate`                            | ↑         | ≥ 0.85            |
| `attr_grounded_rate`                      | ↑         | ≥ 0.70            |
| `rating_sentiment_consistent_rate`        | ↑         | ≥ 0.85            |
| failure_modes: `title_reasoning_leak`     | ↓         | ≤ 2 / 50          |
| failure_modes: `attr_mono_value`          | ↓         | ≤ 5 / 50          |
| failure_modes: `non_fashion_item`         | ↓         | ≤ 2 / 50          |

### 4c. Stage 1.1.5 — dedup effectiveness
Input: Stage 1.1 output. Output: `stage_1_1_5_deduped.jsonl`.

**Dedup implementation runs REMOTELY on coupang.** NeMo Curator's
`FuzzyDeduplicationWorkflow` and `TextSemanticDeduplicationWorkflow`
both require `cudf` (RAPIDS) + `ray`, which are Linux + CUDA only.
The baseline `data_pipeline_vllm.py` falls back to **exact dedup**
when `cudf` is missing — meaning on our current coupang venv the
dedup step is effectively a no-op (10 k → 9999 in the earlier run
because Data Designer outputs are all distinct strings).

**Dedup evaluation (LLM dedup-miss finder)** also runs on coupang for
locality; Friendli is called from the coupang box over the internet,
so the judge still uses the 3-model ensemble described in §4f.

| metric (per-judge + mean)                  | direction | promote-threshold |
|--------------------------------------------|-----------|-------------------|
| `dedup_in_count`                           | —         | informational     |
| `dedup_out_count`                          | —         | informational     |
| `dedup_reduction_rate`                     | ↑         | ≥ 0.05  (baseline = 0) |
| `mean_dedup_miss_rate`  (judge-avg missed / dedup_out_count) | ↓ | ≤ 0.05 |
| `largest_miss_cluster_size`                | ↓         | ≤ 3               |

Note: baseline iter_00 is expected to show
`dedup_reduction_rate ≈ 0` and `mean_dedup_miss_rate` roughly equal to
the natural near-duplicate rate in Stage 1.1 output (= the dedup
never fired). H10 (cudf + SemDedup) is the first hypothesis designed
to move these numbers.

### 4d. Stage 1.2 — quality-filter survivors
Input: Stage 1.1.5 output. Output: `stage_1_2_processed.jsonl`.
Judge: reuses `stage_1_2_judge`.

| metric (per-judge + mean)          | direction | promote-threshold |
|------------------------------------|-----------|-------------------|
| `retention_from_stage_1_1`         | ↑         | ≥ 0.85   (← broken today at 0.0125 because of Korean NonAlphaNum filter) |
| `fashion_rate`                     | ↑         | ≥ 0.95            |
| `has_tpo_rate`                     | ↑         | ≥ 0.85            |
| `avg_text_quality`                 | ↑         | ≥ 4.0 / 5         |
| `pii_rate`                         | ↓         | ≤ 0.02            |

### 4e. Deterministic / quantitative probes (no LLM, per iteration)
`scripts/quant_stage1_report.py`:

| metric                                     | stage   | direction | promote-threshold |
|--------------------------------------------|---------|-----------|-------------------|
| `rating_3_share`                           | 1.1     | ↑         | > 0               |
| `title_len_p90`                            | 1.1     | ↓         | ≤ 40              |
| `title_newline_rate`                       | 1.1     | ↓         | ≤ 0.02            |
| `style_top1_share`                         | 1.1     | ↓         | ≤ 0.60            |
| `color_top2_share` (화이트+블랙 합산)        | 1.1     | ↓         | ≤ 0.60            |
| `e2e_retention` (stage_1_2 / stage_1_0)    | pipeline| ↑         | ≥ 0.80            |

### 4f. Judge ensemble protocol

- Each record per stage is judged by **all three** models. Per-record
  JSONL stores three verdicts (`judge.<model>`) side-by-side under
  `judge_raw/stage_<X>__<model>.jsonl`.
- `metrics.json` reports every metric as `{glm: …, deepseek: …, qwen3: …, mean: …, range: …}`.
- Promotion is decided on the **mean**; `range > 0.15` on the headline
  metric marks the iteration `HIGH_VARIANCE` and it does not influence
  H-queue ordering.
- `agreement_rate` (fraction of records where all three judges agree on
  a boolean) is computed and reported for every boolean metric.

Cost envelope per iteration:
- Stage 1.0 + 1.1 + 1.2 = 3 × 50 records × 3 judges ≈ **450 judge calls**
- Stage 1.1.5 = 1 multi-record call × 3 judges ≈ **3 judge calls**
- Total ≈ 453 Friendli calls/iter × 12 iter ≈ **5.4 k calls, ~5-7 M tokens**.
  Well within Friendli serverless budget for the hackathon.

## 5. Hypothesis queue

Ordered roughly by expected yield × ease. The agent pulls one hypothesis
per iteration; failing hypotheses are still committed (important signal).

Each `affects` column shows which sub-stage's metrics the fix is expected
to move.

| # | slug                       | affects          | hypothesis                                                                                                     | patch target                                                                                                   |
|---|----------------------------|------------------|----------------------------------------------------------------------------------------------------------------|----------------------------------------------------------------------------------------------------------------|
| H1 | `title_prompt_strict`      | 1.1              | Reasoning-leak happens because model self-verifies the 15-30 char constraint. Relaxing + single-line guidance drops leak. | Rewrite `TITLE_PROMPT` in `data_pipeline_vllm.py`: drop explicit char count, require single line, show good/bad examples. |
| H2 | `title_max_tokens_short`   | 1.1              | Even with better prompt, title token budget 500 gives room for reasoning. Dropping to `max_tokens≈60` forces brevity. | Add per-column `max_tokens` override on the title column; leave raw_text at 500.                              |
| H3 | `title_postprocess`        | 1.1              | Regardless of prompt, a deterministic postprocessor (keep first line, trim <30 chars, strip `→`) removes leak at worst case. | New `_clean_title()` hook applied after Data Designer returns results.                                        |
| H4 | `seed_rating_3_injection`  | 1.0 → 1.1 → 1.2  | rating=3 dropout is a seed-sampling issue. Forcing a seed mix with rating 1-5 uniform restores the missing level. | Modify seed selection to stratify by rating before `FASHION_KEYWORDS` filter.                                 |
| H5 | `attr_diversity_prompt`    | 1.1              | `product_attributes` mode collapse comes from prompt asking "provide attributes" generically. Asking to vary per persona+product breaks collapse. | Rewrite `ATTR_PROMPT` to condition on persona age/occupation + title, and enumerate style space.              |
| H6 | `size_plausibility_filter` | 1.1 → 1.2        | size="13개월", "250" are baby/shoe sizes leaking through FASHION_KEYWORDS. Post-filter via an allow-list keeps only apparel sizes. | After generation, drop or relabel records whose size doesn't fit the allow-list (S/M/L/XL/FREE/85-120).       |
| H7 | `non_fashion_seed_filter`  | 1.0 → 1.1 → 1.2  | Non-fashion seed reviews ("신발 정리함") pass FASHION_KEYWORDS because "신발" is in the keyword list. Tighten the list + add a must-have pattern for apparel words. | Replace `FASHION_KEYWORDS` with a 2-layer filter (include + exclude).                                          |
| H8 | `persona_binding_prompt`   | 1.1              | Low persona_reflection (baseline ≈?) means persona fields are listed but not used. Stronger instruction + per-field binding improves score. | Update review prompt to explicitly require referring to 2 of {hobbies, occupation, province, age} by name.    |
| H9 | `korean_quality_filter`    | 1.2              | Stage 1.2 `NonAlphaNumericFilter(max=0.85)` counts Hangul as non-alpha → drops ~99% of Korean records. Swap for a Hangul-aware min-content filter. | Remove `NonAlphaNumericFilter` or replace with `min_korean_chars=20`.                                          |
| H10| `install_cudf_semdedup`    | 1.1.5            | Baseline Stage 1.1.5 is effectively no-op (cudf missing → exact dedup → no duplicates removed). `pip install cudf-cu12` + swap to `TextSemanticDeduplicationWorkflow` activates real near-duplicate removal. | On coupang: install `cudf-cu12`, replace `run_fuzzy_deduplication` with a thin wrapper around `TextSemanticDeduplicationWorkflow(text_field='raw_text', model_identifier='sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2', n_clusters=50, eps=0.05, perform_removal=True)`. Falls back to exact dedup on install failure. |

If metrics plateau before running out of hypotheses, the loop also
suggests **combinations** (H1 + H5, etc.) as secondary iterations.

## 6. Promotion bar to Stage 2

Stage 2 re-run only triggers when an iteration result satisfies **all four
sub-stages simultaneously** (mean across three judges):

**Stage 1.0** (seed):
- `fashion_rate ≥ 0.90`
- `avg_text_quality ≥ 3.5`

**Stage 1.1** (synthetic): *the hardest*
- `title_reasoning_leak_rate ≤ 0.02`
- `fashion_rate ≥ 0.95`
- `attr_grounded_rate ≥ 0.70`
- `avg_persona_reflection ≥ 3.5`
- `rating_3_share > 0`  (quantitative)

**Stage 1.1.5** (dedup):
- `mean_dedup_miss_rate ≤ 0.05`

**Stage 1.2** (filter):
- `retention_from_stage_1_1 ≥ 0.85`
- `fashion_rate ≥ 0.95`

Any iteration in `HIGH_VARIANCE` state (judge `range > 0.15` on a
headline metric) is **not** considered for promotion even if mean scores
pass. Reviewer can still decide to override after reading `comparison.md`.

## 7. Iteration folder shape

```
experiments/
├── PLAN.md                          # this document                          (git)
├── README.md                        # one-paragraph index                    (git)
├── summary.md                       # rolling leaderboard, updated post-iter (git)
├── iter_00_baseline/
│   ├── hypothesis.md                # "baseline, no changes"                 (git)
│   ├── pipeline_script.py           # frozen copy of data_pipeline_vllm.py   (git)
│   ├── metrics.json                 # §4 metrics + sha256 of outputs         (git)
│   ├── judge_report.md              # tri-judge ensemble narrative           (git)
│   ├── quant_report.md              # no-LLM quantitative summary            (git)
│   ├── run_log.txt                  # end-to-end command log                 (git)
│   ├── comparison.md                # vs previous iter                       (git; iter_00 has none)
│   ├── output/                      # raw jsonl outputs - SIZE HEAVY, not tracked (gitignore)
│   │   ├── stage_1_0_seed.jsonl
│   │   ├── stage_1_1_synthetic.jsonl
│   │   ├── stage_1_1_5_deduped.jsonl
│   │   └── stage_1_2_processed.jsonl
│   └── judge_raw/                   # per-judge per-record verdicts          (gitignore)
│       ├── stage_1_0__glm.jsonl
│       ├── stage_1_0__deepseek.jsonl
│       ├── stage_1_0__qwen3.jsonl
│       ├── stage_1_1__glm.jsonl
│       ├── stage_1_1__deepseek.jsonl
│       ├── stage_1_1__qwen3.jsonl
│       ├── stage_1_1_5__glm.jsonl      (dedup-miss finder)
│       ├── stage_1_1_5__deepseek.jsonl
│       ├── stage_1_1_5__qwen3.jsonl
│       ├── stage_1_2__glm.jsonl
│       ├── stage_1_2__deepseek.jsonl
│       └── stage_1_2__qwen3.jsonl
├── iter_01_title_prompt_strict/
│   ├── hypothesis.md
│   ├── patch.diff                   # git diff vs iter_00
│   ├── pipeline_script.py
│   ├── metrics.json
│   ├── judge_report.md
│   ├── quant_report.md
│   ├── comparison.md                # vs iter_00 — 3-col table + narrative
│   ├── run_log.txt
│   ├── output/                      (gitignore)
│   └── judge_raw/                   (gitignore)
├── iter_02_title_max_tokens_short/
│   └── ...
└── winners/                          (gitignore)
    └── iter_NN_<slug>/              # hard-copy of the promoted iter's folder
```

Every `comparison.md` is a 4-stage × N-metric table (`stage | metric |
prev | now | Δ | dir`) plus a 2-3 paragraph narrative. `summary.md` is
updated after every iteration so a reviewer reading only that file sees
the full arc.

`metrics.json` carries the content hashes so you can verify a local copy
of the `output/` matches the recorded numbers:

```json
{
  "iter_id": "iter_03_attr_diversity_prompt",
  "parent_iter": "iter_02_title_max_tokens_short",
  "timestamp": "2026-04-22T02:15:00Z",
  "output_hashes": {
    "stage_1_0_seed.jsonl":      "sha256:abcd...",
    "stage_1_1_synthetic.jsonl": "sha256:efgh...",
    "stage_1_1_5_deduped.jsonl": "sha256:ijkl...",
    "stage_1_2_processed.jsonl": "sha256:mnop..."
  },
  "stage_1_0": {
    "fashion_rate": {"glm": 0.92, "deepseek": 0.94, "qwen3": 0.90, "mean": 0.92, "range": 0.04},
    "avg_text_quality": {"glm": 3.6, "deepseek": 3.8, "qwen3": 3.4, "mean": 3.6, "range": 0.4},
    "..."
  },
  "stage_1_1": { "...": "..." },
  "stage_1_1_5": { "...": "..." },
  "stage_1_2": { "...": "..." },
  "quant": { "rating_3_share": 0.14, "title_len_p90": 31, "...": "..." },
  "e2e": {"input_rows": 200, "output_by_stage": [50, 50, 48, 42]},
  "high_variance": false,
  "promote": false,
  "notes": ""
}
```

## 8. Subagent allocation

The main agent (me) is the **orchestrator**. It does not run the
individual iterations; it only:

- decides which hypothesis to queue next
- keeps `summary.md` in sync
- enforces the promotion bar in §6

Per iteration, I dispatch exactly one `subagent_general` with a sealed
prompt that contains everything it needs. The subagent:

1. Reads `hypothesis.md` + the parent iteration's `metrics.json`.
2. Applies the patch to a copy of `data_pipeline_vllm.py` at
   `experiments/iter_NN_<slug>/pipeline_script.py`.
3. **Runs the four-stage pipeline REMOTELY on coupang** via
   `brev exec coupang "bash -c '...'"`. This is non-negotiable for
   Stage 1.1.5 (dedup) because `cudf`+`ray`+`nemo_curator` are
   Linux+CUDA only. It's also the cheapest place for Stage 1.1 (Data
   Designer calls the localhost vLLM Nemotron-Super). Uses a per-iter
   `$STAGE_DATA_ROOT=$HOME/experiments_data/iter_NN` so runs never
   clobber each other. All four outputs land in that folder on coupang.
4. `brev copy coupang:$STAGE_DATA_ROOT/iter_NN/ experiments/iter_NN_<slug>/output/`
   to pull the four JSONL outputs back to the local repo.
5. Runs the tri-judge ensemble **on coupang** (data is already there;
   judging from local means copying the judge prompts 450 times over
   SSH):
   - `stage_1_0` via `stage_1_2_judge` (curated-doc rubric, same shape)
   - `stage_1_1` via `stage_1_1_judge`
   - `stage_1_1_5` via `stage_1_1_5_judge` (new dedup-miss finder)
   - `stage_1_2` via `stage_1_2_judge`
   Each judge is invoked once per stage per model (`GLM / DeepSeek /
   Qwen3` on Friendli). Per-judge JSONLs land in `judge_raw/` on
   coupang, then pulled back via `brev copy`.
6. Runs `scripts/quant_stage1_report.py` on the four local outputs
   (deterministic Python, no GPU needed) — runs locally or on coupang,
   whichever is easier.
7. Writes `metrics.json` (with sha256), `judge_report.md`,
   `quant_report.md`, `comparison.md` (diff vs parent `metrics.json`),
   `run_log.txt` — all on the LOCAL repo because those are the
   git-tracked files.
8. Commits: `iter_NN: <slug> <headline metric Δ>`.

Context isolation is the whole point: each subagent has no memory of
previous iterations; it only sees `hypothesis.md` + the parent's
`metrics.json`. That way the orchestrator doesn't blow up its own
context window overnight.

A second flavour of subagent (`subagent_explore`, read-only) is used by
me at the top of each iteration to pick the next hypothesis: it reads
`summary.md` + the latest winner's `judge_report.md` and returns a short
recommendation. This is usually fast (< 2 min) and doesn't touch disk.

## 9. Safety rails

- **No Brev destructive ops** without my explicit go-ahead. Subagents
  can call `brev exec coupang "bash ..."` but not `brev reset|delete|stop`.
- Each iteration uses its own `$STAGE_DATA_ROOT=$HOME/experiments_data/iter_NN`
  on coupang so runs never clobber each other's data. This is NOT the
  shared `/home/nvidia/data/` used by the current main Stage 2 pipeline.
- LLM concurrency capped at **32 on Stage 1** (already our budget),
  judge concurrency = **4** (Friendli rate-limit friendly, 50 records ×
  3 stages × 3 models finishes in < 10 min).
- If vLLM throws 5xx > 5% on a run, the subagent aborts the iteration,
  writes `run_log.txt` with the failure, and returns; I requeue.
- If any single Friendli judge model hits rate limits, the subagent
  records the gap as `null` in `metrics.json` (rather than 0) and the
  `mean` / `range` treats null as missing data. Iteration is still
  committed but flagged `PARTIAL_JUDGES`.

## 10. Success / stop conditions

End-of-run conditions (priority order):

1. **Promotion**: any iteration passes §6 → write `promote.md`, stop the
   loop, flag Stage 2 as runnable.
2. **Budget exhausted**: **12 h wall clock**, irrespective of plateau →
   write `budget.md`, stop with the current best. (User explicitly
   requested plateau stop be disabled; keep iterating.)
3. **Blocker**: vLLM server dies, Friendli quota hit, Brev instance
   degrades → write `blocker.md`, stop and ping the user.

Any stop condition produces a final `summary.md` entry with a table of
all iterations sorted by tri-judge mean (or the single most-moved
metric) plus an honest "what we learned" paragraph.

## 11. Bootstrap checklist (before the first subagent launches)

- [x] `git init` + baseline commit on `main`  (cd17cd3)
- [x] `experiment/stage1-iterative-improvement` branch
- [x] `.gitignore` covers `data/`, `brev_snapshot/`, per-iteration
       `output/` + `judge_raw/`
- [x] `experiments/PLAN.md` + `experiments/README.md`
- [ ] **`pipelines/eval/stage_1_1_5_judge.py`** — new. LLM "dedup-miss
      finder": one call per judge across the full deduped set,
      returns `near_duplicate_groups = [[id, id, ...], ...]`.
- [ ] **`scripts/quant_stage1_report.py`** — non-LLM probe that emits
      §4e metrics reading all four JSONLs.
- [ ] **`scripts/tri_judge_run.py`** — wraps the 4 judges × 3 models
      into one driver: writes the 12 per-judge JSONLs, plus a merged
      `metrics_partial.json` with means/ranges/agreement.
- [ ] **`scripts/iter_run.py`** — sealed subagent driver. Applies patch,
      runs pipeline at 50 rec on coupang, copies outputs to iter
      folder, runs `tri_judge_run`, runs quant probe, writes the six
      git-tracked files from §7, commits.
- [ ] **`scripts/make_comparison.py`** — reads this iter's + parent's
      `metrics.json` and produces `comparison.md` + updates `summary.md`.
- [ ] `experiments/iter_00_baseline/` seeded from the current
       `data_pipeline_vllm.py`. Created on-demand by the first subagent
       call (not during setup), so timing is fair.
- [ ] Verify `FRIENDLI_API_KEY` works AND all three judge models respond
      (quick smoke call during the first subagent's prelude).
- [ ] Verify Stage 2 pipeline is done (or parked) so vLLM:5000 has
      headroom for the iteration loop.
- [ ] `~/coupang/.venv/bin/python -c "import nemo_curator"` **passes on
      coupang** (we installed it earlier; verify with a short smoke).
      `cudf` is NOT required for iter_00 (baseline's exact-dedup
      fallback path is fine); H10 is the iteration that `pip install`s
      cudf and only then the dedup stage does real work.

## 12. User-settled decisions (locked in)

Resolved at the start of the run:

- **Iteration size**: 50 records. Cheaper, more iterations possible
  within budget.
- **Judge**: tri-judge ensemble (GLM-5.1 + DeepSeek-V3.2 + Qwen3-235B)
  from iter_00 onward — no warm-up single-judge phase.
- **Budget**: 12 h hard cap; plateau stop disabled. Keep iterating.
- **Legacy PoC files**: kept in place (`collect_youtube.py`,
  `pipeline_v2.py`, `data_designer_poc.py`, `hackathon-*-plan.md`).
  They live on `main` as historical artefacts; the experiment branch
  inherits them untouched.
