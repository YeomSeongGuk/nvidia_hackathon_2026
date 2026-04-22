# iter_00a_semdedup_probe — §5a BGE-M3 threshold sweep on iter_00_baseline

Pre-SD probe to decide what θ the SD-series iters should use. No pipeline run;
just a deterministic cosine sweep on the 42 rows in
`experiments_stage2/iter_00_baseline/output/stage_2_1_extracted.jsonl`
(i.e. the stage_2_1 extracted intents *before* stage_2_1_5 dedup).

## Configuration

- **device**: `cuda` (ran on coupang; local .venv hit an httpx/HF-Hub client error
  during BAAI/bge-m3 download, so fell back to `brev exec coupang`)
- **embed model**: `BAAI/bge-m3` (PLAN §5a default)
- **signature builder**: `full` (intent + utterances + entities + relations, per §5a)
- **input rows**: 42

## Sweep

| threshold | pairs_above | removed / 42 | removed_rate | avg_cos_kept |
|-----------|-------------|--------------|--------------|--------------|
| 0.95      | 0           | 0            | 0.000        | 0.7309       |
| 0.90      | 0           | 0            | 0.000        | 0.7309       |
| 0.85      | 2           | 2            | 0.048        | 0.7174       |
| 0.80      | 2           | 2            | 0.048        | 0.7174       |
| 0.75      | 14          | 5            | 0.119        | 0.7020       |
| 0.70      | 52          | 16           | 0.381        | 0.6727       |

**Recommended threshold**: **0.75** (smallest θ with removed_rate in the
informative [0.10, 0.25] band per §5a rule).

## Interpretation

SemDedup at the PLAN default θ=0.90 would remove **0/42** rows on this
baseline — a complete no-op, providing no signal. Lowering to θ=0.85 or 0.80
removes only 2/42 (4.8%), still below the informative [0.10, 0.25] band.
At θ=0.75 we remove 5/42 (11.9%), which is inside the band and should give SD
a real chance to demonstrate a pruning effect. θ=0.70 (16/42 = 38%) is too
aggressive and would likely destroy diversity.

## Implication for SD iters

**SD1 should use θ=0.75** (the probe-recommended value), not the PLAN default
θ=0.90. At 0.90 the intervention is a no-op vs iter_00_baseline and contributes
no evidence about whether SemDedup helps or hurts tri-judge scores on this
scale. SD2/SD3 (if any) should sweep neighboring values (e.g. 0.80, 0.70) to
bracket 0.75 and measure sensitivity.
