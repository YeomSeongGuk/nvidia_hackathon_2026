# H1: `title_prompt_strict` (iter_01)

**Parent**: `iter_00_baseline` (`title_reasoning_leak_rate = 0.473`, `title_len_p90 = 891`, `title_newline_rate = 0.38`)

**Hypothesis**: The baseline title prompt asks the model to satisfy a numeric
constraint ("15-30자 이내"). Nemotron-Super interprets this as "please
self-verify and show your work", so it routinely appends "(22자)",
"**수정 사항:**", multi-line reasoning, and a rewritten title. That single
ask is responsible for 47% of the records hitting `title_reasoning_leak`
and 38% of records having a newline inside `product_title`.

**Change**: Rewrite `title_prompt` in `run_data_designer_stage()`:

- Remove the explicit "15-30자" count. Give a few good one-line examples
  instead (Uniqlo / Zara / Musinsa / H&M) — the model learns length
  from examples without being nudged to count.
- Add an explicit **do-not** list: "글자수 세기 금지", "설명 금지",
  "여러 줄 금지", "reasoning 출력 금지".
- Open with "한 줄로만 작성하세요" up front.

Expected movement:

- `stage_1_1.title_reasoning_leak_rate`: 0.473 → ≤ 0.15 (target ≤ 0.02
  is probably out of reach with prompt alone; H3 postprocessor will
  finish the job if leak drops but is non-zero).
- `stage_1_1.title_format_ok_rate`: 0.247 → ≥ 0.55.
- `stage_1_1.title_within_spec_rate`: 0.273 → ≥ 0.55.
- `quant.stage_1_1.title_len_p90`: 891 → ≤ 40.
- `quant.stage_1_1.title_newline_rate`: 0.38 → ≤ 0.05.

Non-goals for this iter:

- Not touching `attr_prompt` (H5 handles mode collapse).
- Not touching `review_prompt` (H8 handles persona binding).
- Not touching seed filter / rating sampler (H4, H7).
- Stage 1.2 retention stays at 0 because NonAlphaNumericFilter is
  still in place (H9 fixes that).
