# H7: `non_fashion_seed_filter` (iter_07)

**Parent**: `iter_00_baseline`
(`stage_1_1.fashion_rate = 0.853`, 9/50 records flagged as `non_fashion_item`)

**Hypothesis**: Baseline `FASHION_KEYWORDS` is an include-list. Rows
like "신발 정리 수납함 2단 선반형" contain "신발" (a fashion keyword)
but are storage accessories, not apparel. Once these enter the seed,
Data Designer generates a synthetic review for a storage box with a
fashion persona attached → the judge correctly flags as
`non_fashion_item`. An exclude-list second pass drops them at Stage 1.0.

**Change**:
1. Add `FASHION_EXCLUDE_KEYWORDS` covering
   - storage / organizer terms: 정리함, 수납함, 신발장, 행거, ...
   - cleaning / maintenance: 세탁볼, 세제, 탈취제, ...
   - tools: 드라이기, 고데기, 면도기
   - pet / baby non-apparel: 기저귀 가방, 반려견 가방
2. Update `extract_seed_data` to compute `include_mask & ~exclude_mask`.

Expected movement:

- `stage_1_0.fashion_rate`: (n/a in baseline; judge crashed) → ≥ 0.90.
- `stage_1_1.fashion_rate`: 0.853 → ≥ 0.92.
- `stage_1_1.failure_modes.non_fashion_item`: 9/50 → ≤ 2/50.

Non-goals:
- No prompt changes.
- Stage 1.2 still broken by NonAlphaNumericFilter (H9 fixes).
- `title_reasoning_leak_rate` stays ≈ 0.47.
