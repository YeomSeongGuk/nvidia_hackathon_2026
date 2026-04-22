# H2: `title_max_tokens_short` (iter_05)

**Parent**: `iter_00_baseline`
(`quant.stage_1_1.title_len_p90 = 891`,
 `title_len_max = 926`,
 `title_newline_rate = 0.38`,
 `title_reasoning_leak_rate = 0.473`)

**Hypothesis**: Even with the same baseline prompt, the reasoning leak
only fits in the output because `max_tokens=500` leaves room for a full
reasoning trace + multi-line rewrite. Capping the title column's
`max_tokens` to 80 starves the leak: the model has no budget to
output "(18자)\n\n**수정 사항:**..."; it must truncate to a title.
Also drop temperature from 0.8 → 0.3 since title generation shouldn't
benefit from sampling diversity (it should be grounded on the seed
review).

**Change**: Introduce a *second* `ModelConfig` alias
`nemotron_short` with `max_tokens=80, temperature=0.3` pointing at the
same underlying `nemotron` model. Use it on the `product_title`
column only; leave `raw_text` and `product_attributes` on the default
500-token / 0.8-temp config.

Expected movement:

- `quant.stage_1_1.title_len_p90`: 891 → ≤ 60 (hard cap).
- `quant.stage_1_1.title_len_max`: 926 → ≤ ~250 (tight budget
  + Korean char ≈ 2-4 tokens each).
- `quant.stage_1_1.title_newline_rate`: 0.38 → ≤ 0.10 (token budget
  is usually exhausted on the main title before the reasoning block).
- `stage_1_1.title_reasoning_leak_rate`: 0.47 → ≤ 0.20.
- `stage_1_1.title_format_ok_rate`: 0.25 → ≥ 0.50.

Non-goals:
- No prompt change. H1 tests that separately.
- Stage 1.2 still broken. H9 fixes.
