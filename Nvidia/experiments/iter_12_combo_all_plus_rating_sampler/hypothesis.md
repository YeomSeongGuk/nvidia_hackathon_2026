# Combo: H3 + H9 + H5v2 + H8 + H4v2 (iter_12)

**Parent**: `iter_11_combo_h3_h9_h5_h8`

**Hypothesis**: Stack H4v2 (rating category sampler override) on top of
iter_11 (H3+H9+H5v2+H8) to finally pass the `rating_3_share_gt_0`
promotion gate. iter_06 proved that seed-side rating stratification
cannot work because the raw Naver corpus has ZERO rating=3 reviews.
So decouple synthetic rating from seed_rating entirely.

**H4v2 change**:
1. Add a Data Designer `CATEGORY` sampler for `rating` BEFORE
   `raw_text` (so the value is available in review_prompt).
2. Remove the legacy `builder.add_column(name="rating", column_type="expression", expr="{{ seed_rating }}")`.
3. Update review_prompt to reference `{{ rating }}` (not seed_rating)
   and add an explicit per-rating rubric (1점 강한 불만 ... 5점 강한
   만족).

**Changes stacked in iter_12**:
- H3 title postprocessor
- H9 Korean-aware Stage 1.2 filter
- H5v2 attr_prompt with seed_review context
- H8 review_prompt with 2+ persona fields + examples
- **H4v2 rating category sampler (uniform 1-5) + per-rating rubric**

**Expected movement vs iter_11**:
- `quant.stage_1_1.rating_3_share`: 0 → ~0.18 (uniform 1-5 → ~10/50).
- `promote_checks.quant.rating_3_share_gt_0`: false → **true**.
- `stage_1_1.rating_sentiment_consistent_rate`: expect 1.0 (H8 held
  this in iter_08; new explicit rubric should keep it).
- Inherits all iter_11 metrics.

If this iter still doesn't promote, the remaining gates are all
"hard" infra ones:
- `title_leak_le_0.02` (stuck at ~0.06 with H3 alone; would need
  stricter postprocessor e.g. reject & re-sample).
- `attr_grounded_ge_0.70` (H5v2 added seed_review but may need
  stronger grounding instruction or column re-ordering).
- `stage_1_1_5.dedup_miss_rate_le_0.05` (requires cudf+SemDedup — H10).
