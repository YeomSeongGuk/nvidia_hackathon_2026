# Combo: H3 + H9 (iter_09)

**Parent**: `iter_03_title_postprocess` (proven: H3 dropped leak 0.47 → 0.06)

**Hypothesis**: H3 (deterministic title postprocessor) and H9 (Korean-aware
quality filter) are orthogonal. Stacking them should preserve H3's Stage
1.1 title gains *and* recover Stage 1.2 retention from 0.02 → ≥0.85.

This is a sanity combo: two independent, already-validated wins should
simply add. If this iter produces promote-checks passing on BOTH
`stage_1_1.title_leak_le_0.02`-ish (we expect ~0.06, still above gate)
AND `stage_1_2.retention_ge_0.85`, we know the rest of the combos
(H5, H7, H4, H8 stacked in) will just chip away at the remaining gates.

**Change**: iter_09's `pipeline_script.py` = iter_03's postprocessor patch + iter_02's `run_quality_filtering()` patch, stacked.

Expected movement vs baseline (iter_00):

- `stage_1_1.title_reasoning_leak_rate`: ≈ 0.06 (H3 effect).
- `quant.stage_1_1.title_len_max`: ≈ 30, `title_newline_rate`: 0.
- `stage_1_2.retention_from_stage_1_1_5`: 0.0 → ~0.95 (H9 effect).
- `stage_1_2.fashion_rate`: → 0.90+ (propagates from Stage 1.1 since
   no real content filter now).
- `e2e.e2e_retention`: 0 → ~0.95.

Not addressed by this combo (will need more iters):
- `attr_grounded_rate` (still 0.47, targets H5).
- `rating_3_share` (still 0, targets H4).
- `fashion_rate ≥ 0.95` on Stage 1.1 (likely 0.83-0.86, H7 may help).
- `avg_persona_reflection` is already at 3.97 — close to 4.0 target
  from H3 alone (the persona binding seems less title-coupled now).
- Stage 1.1.5 dedup (still 0, targets H10 = cudf install).
