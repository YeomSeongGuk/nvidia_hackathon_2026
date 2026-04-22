# Combo: H3 + H9 + H5v2 + H8 (iter_11)

**Parent**: `iter_10_combo_h3_h9_h5`

**Hypothesis**: Stack H8 (persona_binding_prompt) on top of iter_10
(H3+H9+H5v2) to add the persona/rating-sentiment gains validated in
iter_08 on top of the title/retention/attr-diversity combo of iter_10.

Note: H7 was DROPPED from the combo queue. iter_07 showed H7
regressed Stage 1.1 fashion_rate 0.853 → 0.787 and non_fashion_item
9 → 11 (plausibly noise at n=50, but no benefit). We skip it.

**Changes stacked in iter_11**:
- H3: `_clean_title()` postprocessor (leak → ~0.06, len_cap=30)
- H9: Korean-aware Stage 1.2 filter (retention → 1.0)
- H5v2: attr_prompt with seed_review context + no W/B banishment
- **H8: review_prompt forces 2+ persona field citations, widened
  length envelope 50-150, explicit per-rating sentiment rubric**

**Expected movement vs iter_10** (based on iter_08 standalone):
- `stage_1_1.avg_persona_reflection`: 3.97 → ≥ 4.5 (iter_08 hit 4.51)
- `stage_1_1.rating_sentiment_consistent_rate`: 0.78 → 1.0 (iter_08)
- `stage_1_1.failure_modes.persona_drift`: ≤ 13 (iter_08)
- `stage_1_1.failure_modes.rating_sentiment_mismatch`: → 0 (iter_08)
- `stage_1_1.failure_modes.length_violation`: ≤ 2 (iter_08)
- Other metrics unchanged from iter_10.

If iter_11 retains iter_10's title/retention gains AND picks up H8
persona/rating wins, it should clear most Stage 1.1 gates except:
- `title_leak_le_0.02` (stuck at ~0.06; iter_12+ may need prompt+postprocess combo)
- `attr_grounded_ge_0.70` (stuck at ~0.60; may need seed_review in
  attr_prompt with stronger grounding instruction)
- `rating_3_share_gt_0` (will stay 0 — requires H4v2 rating sampler)
- `dedup_miss_rate_le_0.05` (requires cudf+SemDedup on coupang)
