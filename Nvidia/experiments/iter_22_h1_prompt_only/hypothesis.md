# iter_22: iter_17 + H1 title_prompt only (no postprocessor over-reach)

**Parent**: `iter_17_postgen_fashion_filter` (best overall, 6/10 gates)

**Hypothesis**: iter_20 showed H1 prompt + H3v5 empty-fallback + min-10
filter together drove title_reasoning_leak to 0.01 ✅ but dropped
fashion_rate below 0.95 because fewer rows survived (44→34). iter_18
showed H3v4 prose-detection → "패션 상품" fallback collapsed
title_format_ok. BOTH demonstrate that the post-processor changes
introduced collateral damage.

iter_22 keeps iter_17's proven postprocessor (H3 regex + 30-char cap)
and post-gen filter UNTOUCHED, and ONLY changes the title_prompt to
H1 form. H1 alone (iter_01) moved leak 0.473 → 0.12 without any other
changes. Stacking H1 (prompt-side) on top of H3 (regex-side) should
push leak below 0.05 without the post-processor regressions.

**Changes vs iter_17**: exactly one — the `title_prompt` text, from
the baseline "15-30자" version to the iter_01 H1 "ONE-LINE, bad-example
block" version. Post-processor, post-gen filter, attr prompt, review
prompt, rating sampler — all identical to iter_17.

**Expected movement vs iter_17**:
- `stage_1_1.title_reasoning_leak_rate`: 0.09 → ≤ 0.05 (prompt fix).
- `stage_1_1.fashion_rate`: stays ~0.953 (row count ~44 preserved).
- `stage_1_1.title_format_ok_rate`: 0.443 → no regression (no
  fallback-string strategy introduced).
- Other metrics inherited from iter_17.

Best case: hits title_leak gate WHILE retaining stage_1_1.fashion_rate
gate — putting us at **7/10 gates** for the first time, with only
stage_1_0 (structural) and dedup (H14v2 / iter_21) remaining.
