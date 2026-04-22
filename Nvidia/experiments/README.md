# Experiments

Overnight iterative improvement loop for **Stage 1 (four sub-stages:
1.0 seed / 1.1 synthesis / 1.1.5 dedup / 1.2 filter)**.
See **[PLAN.md](PLAN.md)** for the full contract (goal, metrics,
hypothesis queue, subagent protocol, stop conditions).

Branch: `experiment/stage1-iterative-improvement`  (forked from `main@cd17cd3`)

## Run parameters (locked in)

- **Records per iteration**: 50
- **Judge ensemble**: GLM-5.1 + DeepSeek-V3.2 + Qwen3-235B (Friendli)
- **Budget**: 12 h hard cap; plateau stop disabled
- **Legacy PoC files**: kept (not pruned)
- **Stage 2**: frozen until Stage 1 passes the promotion bar (PLAN §6)

## Code vs data versioning

- **Code** = Git. Every iteration is one commit on
  `experiment/stage1-iterative-improvement`; `main` stays frozen at the
  baseline.
- **Data** = plain file copies under `experiments/iter_NN_<slug>/`,
  gitignored. `metrics.json` (tracked) contains `sha256` of each JSONL
  so you can verify a local file without committing blobs.
- To ship an iteration off-box, `cp -r experiments/iter_NN_<slug>/`;
  the folder is self-contained.

## Current status

- **Iteration 00 — baseline**: not yet run. Produced by the first
  `subagent_general` dispatch once the current Stage 2 pipeline (the
  5.5 k-record run on coupang) releases vLLM:5000 bandwidth.

## How to read this folder

Each iteration has its own subfolder (`iter_NN_<slug>/`) with:

- `hypothesis.md`       — what we're trying and why                              (git)
- `patch.diff`          — git diff from the previous iteration's script          (git)
- `pipeline_script.py`  — the actual `data_pipeline_*.py` we ran                 (git)
- `judge_report.md`     — tri-judge ensemble narrative across all four stages    (git)
- `quant_report.md`     — no-LLM deterministic probe results                      (git)
- `metrics.json`        — full 4-stage judge+quant numbers + sha256 of outputs   (git)
- `comparison.md`       — 5-col diff table vs the previous iteration              (git)
- `run_log.txt`         — command log                                             (git)
- `output/`             — 4 JSONLs (stage_1_0_seed, 1_1_synthetic, 1_1_5_deduped, 1_2_processed)  (gitignore)
- `judge_raw/`          — 12 per-judge JSONLs (4 stages × 3 models)               (gitignore)

`summary.md` (to be created after iter_00) is the rolling leaderboard
of all iterations with promotion status.
