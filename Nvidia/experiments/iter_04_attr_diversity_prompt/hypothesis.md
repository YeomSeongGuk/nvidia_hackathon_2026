# H5: `attr_diversity_prompt` (iter_04)

**Parent**: `iter_00_baseline`
(`quant.stage_1_1.style_top1_share = 0.88` on 캐주얼,
 `style_unique = 6`,
 `color_white_black_share = 0.72`,
 `color_unique = 8`,
 `stage_1_1.attr_grounded_rate = 0.467`)

**Hypothesis**: Baseline `attr_prompt` is a single English sentence
with 3 style examples ("캐주얼, 포멀, 스트릿"). Nemotron-Super defaults
to the first / easiest option ("캐주얼") 88% of the time and rejoices
in "화이트"/"블랙" 72% of the time. Two interventions together:

1. Enumerate ~15 styles × ~25 colors so the model sees a broad space.
2. Condition on persona age/occupation/sex and product title so
   selection varies per record (a 70대 무직 노인 with a 코트 should
   look different from a 25세 디자이너 with a 스니커즈).

**Change**: Rewrite `attr_prompt` in `run_data_designer_stage()`.
Keep the structured-output schema (`ProductAttributes`) unchanged;
only the prompt text is new. Also the prompt is now Korean (baseline
was English + Korean mix) to give the LLM a single-language target.

Expected movement (standalone vs iter_00):

- `quant.stage_1_1.style_top1_share`: 0.88 → ≤ 0.55.
- `quant.stage_1_1.style_unique`: 6 → ≥ 9.
- `quant.stage_1_1.color_white_black_share`: 0.72 → ≤ 0.45.
- `quant.stage_1_1.color_unique`: 8 → ≥ 12.
- `stage_1_1.attr_grounded_rate`: 0.467 → ≥ 0.60.

Non-goals:
- title_reasoning_leak stays ≈ 0.47 (no change to title prompt).
- stage_1_2 retention stays at 0 (H9 fixes).
- No change to review prompt.
