# Combo: H3 + H9 + H5v2 + H8 + H4v2 + H11 (iter_13)

**Parent**: `iter_12_combo_all_plus_rating_sampler`

**Hypothesis**: iter_11 showed H8 persona_binding drags
`attr_grounded_rate` 0.51 → 0.353 because reviews now focus heavily on
persona context ("탄천 산책", "회계 사무원 출근복") at the expense of
mentioning product color/style/size. The judge requires the attr
values to literally appear in `raw_text` (`mentioned_in_text = TRUE`),
so a review that says "베이지 미니멀 크로스백이에요 M 사이즈" scores
3/3 grounded, while "산책용 크로스백, 주말 나들이용" scores 0/3.

**H11 change** — rewrite `review_prompt` once more:

1. Add an explicit rule #2 before the persona rule: "반드시 color /
   style / size 세 속성을 모두 자연스럽게 리뷰에 언급하라."
2. Give concrete examples of HOW to name each: color-word verbatim,
   size-with-fit-context, style-as-noun-phrase.
3. Replace the two good examples with ones that hit all three attr
   values + two persona fields simultaneously.
4. Tighten length envelope 50-150 → 60-140 (40 chars tighter, still
   enough room for attrs + 2 persona fields + tpo).

**Stacked in iter_13**:
- H3 title postprocessor
- H9 Korean-aware Stage 1.2 filter
- H5v2 attr_prompt with seed_review
- H8 persona binding (2+ persona field citations)
- H4v2 rating category sampler
- **H11 review forces color + style + size mention**

**Expected movement vs iter_11 (not iter_12 because same set plus
H4v2)**:

- `stage_1_1.attr_grounded_rate`: 0.353 → ≥ 0.65
  (recover from iter_11's regression; each record should hit ≥2/3).
- `stage_1_1.failure_modes.attr_ungrounded`: 38 → ≤ 15.
- Persona / rating_sentiment should hold (H8 + H4v2 rubric still in place).
- `title_reasoning_leak` / retention inherited unchanged.

If iter_13 still misses `attr_grounded_ge_0.70`, we may need to
change the attr generation strategy itself (e.g. derive attrs FROM
raw_text post-hoc rather than generating attrs before raw_text).
