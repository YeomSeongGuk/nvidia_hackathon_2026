# H4: `seed_rating_3_injection` (iter_06)

**Parent**: `iter_00_baseline`
(`quant.stage_1_0.rating_hist = {1: 10, 2: 16, 4: 3, 5: 21}`, NO rating=3)

**Hypothesis**: The baseline `DataFrame.sample(n=50, random_state=42)` on
the FASHION-filtered Naver corpus happens to skip rating=3 entirely.
Data Designer copies `seed_rating` verbatim into the synthetic row's
`rating` field, so no rating=3 synthetic review is ever produced.
A stratified sample (10 per rating 1..5) guarantees rating=3 is in
the seed, which propagates to Stage 1.1.

**Change**: Rewrite `extract_seed_data()` in `pipeline_script.py`:

- after FASHION_KEYWORDS filter, bucket by `rating`
- take `seed_data_size // 5` from each bucket (deterministic `random_state`)
- fill remainder from leftover pool if any bucket was sparse
- shuffle the final concatenation

Expected movement:

- `quant.stage_1_0.rating_3_share`: 0 → ≥ 0.15.
- `quant.stage_1_1.rating_3_share`: 0 → ≥ 0.10 (inherited).
- `promote_checks.quant.rating_3_share_gt_0`: false → true.

Non-goals:
- No change to Stage 1.1 prompts.
- Stage 1.2 still broken by NonAlphaNumericFilter (H9 fixes).
- `title_reasoning_leak_rate` stays ≈ 0.47.
