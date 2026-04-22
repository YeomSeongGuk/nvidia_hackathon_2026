# iter_20: title leak fix without format regression

**Parent**: `iter_17_postgen_fashion_filter` (NOT iter_18 — iter_18
regressed title_format_ok 0.44 → 0.06 due to 4-char fallback "패션
상품" violating min-length spec).

**Hypothesis**: Combine (a) H1 title prompt that tells the model
explicitly NOT to produce reasoning, and (b) H3v5 postprocessor that
detects any residual prose-reasoning patterns and returns an **empty
string**, which the H12 post-gen filter then drops (now with a
min-length guard of 10 chars, not just `== "패션 상품"` equality).

**Changes vs iter_17**:

1. **Title prompt** (H1): added "절대 하지 말 것" block with bad
   examples including "브랜드명이 제공되지 않았다" pattern. Tells
   Nemotron-Super explicitly to stop verifying its own work.
2. **Title postprocessor** (H3v5): when prose-reasoning triggers fire
   ("제공되지 않", "일반적인 패션", "가상의 브랜드", etc.), return ""
   instead of a string fallback. No more short-title format
   violations.
3. **H12 post-gen filter**: drops titles where `len < 10` (not just
   exact-match "패션 상품"). This catches empty returns from H3v5
   AND any other odd residuals.

**Expected movement vs iter_17**:

- `stage_1_1.title_reasoning_leak_rate`: 0.09 → ≤ 0.03 (both
  prompt-side H1 and regex-side H3v5 stacked).
- `stage_1_1.title_format_ok_rate`: 0.443 → ≥ 0.55 (no format
  violations from short fallback).
- `stage_1_1.fashion_rate`: stays ~0.95 (H12 filter unchanged).
- `stage_1_1.attr_grounded_rate`: stays ~1.0.
- `e2e.output_rows_by_stage`: [50, ~40-44, ~40-44, ~40-44] (a bit
  fewer than iter_17's 44 because empty titles drop extra rows).

If title_leak gate passes, combined with iter_19's H14 dedup fix
(if that works), iter_21 stacking both would reach **8-9/10 gates**.
Remaining structural gates: stage_1_0.avg_text_quality (~2.79 —
Naver seed quality limit) and stage_1_0.fashion_rate (~0.87 —
sample variance).
