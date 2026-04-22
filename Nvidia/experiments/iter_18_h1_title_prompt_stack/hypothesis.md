# H1 title_prompt + H3v4 prose-reasoning regex (iter_18)

**Parent**: `iter_17_postgen_fashion_filter`

**Hypothesis**: Looking at iter_16 leaky titles, the remaining leak
comes from **prose reasoning** like "브랜드명이 제공되지 않았으므로,
일반적인 패션 브랜드" — the model explains instead of naming a product.
The 30-char cap catches length but not semantics. Two-pronged fix:

**H1 (already validated in iter_01: leak 0.47 → 0.12)**: rewrite
`title_prompt` to explicitly forbid reasoning output. Add a "절대 하지
말 것" block with concrete bad examples including the "브랜드명이
제공되지 않았다" pattern.

**H3v4 prose-reasoning regex**: on top of H3v3, detect prose-style
reasoning in titles and replace with fallback "패션 상품":
- triggers: 제공되지 않, 알 수 없, 따라서, 그러므로, 일반적인 패션,
  가상의 브랜드, 주어지지 않, 명시되지 않, 유추할 수, 해당 상품의,
  이 상품의 제목
- also: titles starting with "이 상품", "해당 상품", "리뷰에서", "브랜드가"

Combined: H1 kills most of these at generation time; H3v4 catches the
residual that slips through. The H12 post-gen fashion filter then
drops the "패션 상품" fallback rows (only truly fashion records survive).

**Changes vs iter_17**:
1. Rewrite `title_prompt` (H1-style).
2. Add prose-reasoning patterns to `_clean_title()` (H3v4).

**Expected movement vs iter_17**:
- `stage_1_1.title_reasoning_leak_rate`: ~0.04 → ≤ 0.02 (promote gate).
- `stage_1_1.failure_modes.title_reasoning_leak`: ≤ 1.
- `stage_1_1.title_format_ok_rate`: → ≥ 0.55.
- Other metrics inherited: attr_grounded, persona, rating_3, retention,
  fashion_rate.

If this iter combines with iter_17's fashion wins, we should see
**5-6/10 gates passing**. title_leak + fashion_rate gates may both
pass, leaving only stage_1_0.avg_text_quality (structural) and
dedup_miss_rate (H10 territory) as remaining blockers.
