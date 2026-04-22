# Combo: H3 + H9 + H5v2 (iter_10)

**Parent**: `iter_09_combo_h3_h9`

**Hypothesis**: Stack H5v2 (attr_diversity_prompt, revised) on top of the
already-proven H3+H9 combo. H5v1 in iter_04 *over-corrected*:
`color_white_black_share` went 0.72 → 0.0 because the prompt listed
"화이트" as a bad example, and the model obeyed too literally.

**Changes in H5v2 vs H5v1**:

1. Drop the sentence "한 가지 값(예: 캐주얼, 화이트)에 편중되지 마라";
   replace with "선택 원칙: 상품명+리뷰 암시 속성 우선 반영".
2. **Add `{{ seed_review }}` to the attr_prompt** — this is critical
   for attr_grounded_rate. Currently the attr LLM only sees the
   generated title; adding the review text grounds style/color
   choices in actual product mentions.
3. Explicitly mark 화이트/블랙 as legitimate choices.
4. Size selection rule keyed to product category (shoes → numeric,
   clothes → S-XL).

**Combined expected movement vs iter_00**:

- `stage_1_1.title_reasoning_leak_rate`: ≈ 0.06 (H3).
- `stage_1_2.retention_from_stage_1_1_5`: ≥ 0.95 (H9).
- `quant.stage_1_1.style_top1_share`: 0.88 → ≤ 0.45 (H5v2).
- `quant.stage_1_1.color_white_black_share`: 0.72 → ~0.2-0.5
  (H5v2, moderated; NOT 0).
- `stage_1_1.attr_grounded_rate`: 0.47 → ≥ 0.65
  (critical: now sees seed_review).
- `stage_1_1.fashion_rate`: 0.86 → 0.88 (unchanged by H5v2).

Not addressed by this combo:
- `rating_3_share` (needs H4 = stratified seed; iter_11 will add).
- `stage_1_1.fashion_rate ≥ 0.95` (needs H7 = non-fashion exclude;
  iter_11 will add).
- `stage_1_1_5.dedup_miss_rate ≤ 0.05` (needs cudf+SemDedup H10,
  separate infra track).

