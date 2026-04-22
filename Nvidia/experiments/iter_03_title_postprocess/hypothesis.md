# H3: `title_postprocess` (iter_03)

**Parent**: `iter_00_baseline` (`title_reasoning_leak_rate = 0.473`, `title_newline_rate = 0.38`, `title_len_p90 = 891`)

**Hypothesis**: Even when the title prompt is good, Nemotron-Super occasionally
leaks reasoning. A deterministic post-hoc fix can paper over whatever
slips through. Because the fix is purely code (no LLM), its effect is
100% reproducible.

**Change**: After `DataDesignerStage` runs, iterate over `result_df`
and apply `_clean_title()` to every `product_title`:

1. Keep the first non-empty *line*. This alone removes the post-`\n\n`
   reasoning block in ~38% of records.
2. Drop anything after `→` / `->` / `=>` (model sometimes uses these
   as "here is the rewritten title" separators).
3. Regex-strip trailing char-count annotation: `\(\d+자\)` or `[\d+자]`.
4. Strip wrapping `*`, `_`, backticks, quotes.
5. Hard-truncate to 30 chars.

**Expected movement** (standalone vs iter_00 baseline):

- `quant.stage_1_1.title_newline_rate`: 0.38 → 0.0 (newlines are
  mechanically removed).
- `quant.stage_1_1.title_len_p90`: 891 → ≤ 30 (hard truncation).
- `stage_1_1.title_reasoning_leak_rate`: 0.47 → ≤ 0.10 (judges rate
  the cleaned string which has no "(22자)" or reasoning hint).
- `stage_1_1.title_format_ok_rate`: 0.25 → ≥ 0.55.

Because we chop to 30 chars, a title that would have been a perfectly
fine "유니클로 오버핏 니트 스웨터 (20자)" becomes "유니클로 오버핏 니트
스웨터" — which is a WIN (the judges dislike the "(20자)" part). But
"자라 울 블렌드 블랙 크롭 트러커 자켓 롱슬리브" would have been 28
chars and still get kept.

Non-goals:
- No prompt change. H1 is tested separately (iter_01).
- Stage 1.2 still broken (retention = 0). H9 fixes that (iter_02).
