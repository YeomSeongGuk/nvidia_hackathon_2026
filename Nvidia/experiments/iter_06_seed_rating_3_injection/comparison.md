# Comparison: iter_06_seed_rating_3_injection vs iter_00_baseline

- this   iter: `iter_06_seed_rating_3_injection`
- parent iter: `iter_00_baseline`
- this timestamp : 2026-04-21T18:35:25+00:00
- promote flag   : False  high_variance: False

## Metric diff

| metric | parent | this | Δ | direction |
|---|---|---|---|---|
| `e2e.e2e_retention` | 0 | — | — | · |
| `e2e.input_rows_seed` | 50 | 0 | -50 | ↓ bad |
| `e2e.output_rows_by_stage` | <list len=4> | <list len=4> | — | · |
| `quant.e2e.e2e_retention` | 0 | — | — | · |
| `quant.e2e.input_rows_seed` | 50 | 0 | -50 | ↓ bad |
| `quant.e2e.output_rows_by_stage` | <list len=4> | <list len=4> | — | · |
| `quant.stage_1_0.n` | 50 | 0 | -50 | ↓ bad |
| `quant.stage_1_0.rating_3_share` | 0 | — | — | · |
| `quant.stage_1_0.rating_hist.1` | 10 | — | — | · |
| `quant.stage_1_0.rating_hist.2` | 16 | — | — | · |
| `quant.stage_1_0.rating_hist.4` | 3 | — | — | · |
| `quant.stage_1_0.rating_hist.5` | 21 | — | — | · |
| `quant.stage_1_1.color_top2_share` | 0.72 | 0.68 | -0.04 | ↓ good |
| `quant.stage_1_1.color_unique` | 8 | 9 | +1 | ↑ good |
| `quant.stage_1_1.color_white_black_share` | 0.72 | 0.68 | -0.04 | ↓ good |
| `quant.stage_1_1.n` | 50 | 50 | +0 | · |
| `quant.stage_1_1.rating_3_share` | 0 | 0 | +0 | · |
| `quant.stage_1_1.rating_hist.1` | 12 | 8 | -4 | ↓ bad |
| `quant.stage_1_1.rating_hist.2` | 17 | 14 | -3 | ↓ bad |
| `quant.stage_1_1.rating_hist.4` | 3 | 10 | +7 | ↑ good |
| `quant.stage_1_1.rating_hist.5` | 18 | 18 | +0 | · |
| `quant.stage_1_1.raw_text_len_max` | 864 | 265 | -599 | ↓ bad |
| `quant.stage_1_1.raw_text_len_median` | 94 | 106 | +12 | ↑ good |
| `quant.stage_1_1.raw_text_len_min` | 41 | 52 | +11 | ↑ good |
| `quant.stage_1_1.raw_text_len_p90` | 189 | 185 | -4 | ↓ bad |
| `quant.stage_1_1.size_suspicious_rate` | 0 | 0.08 | +0.08 | ↑ bad |
| `quant.stage_1_1.size_unique` | 4 | 8 | +4 | ↑ good |
| `quant.stage_1_1.style_top1_share` | 0.88 | 0.88 | +0 | · |
| `quant.stage_1_1.style_top1_value` | 캐주얼 | 캐주얼 | — | · |
| `quant.stage_1_1.style_unique` | 6 | 4 | -2 | ↓ bad |
| `quant.stage_1_1.title_len_max` | 926 | 888 | -38 | ↓ good |
| `quant.stage_1_1.title_len_median` | 27 | 30 | +3 | ↑ good |
| `quant.stage_1_1.title_len_min` | 14 | 17 | +3 | ↑ good |
| `quant.stage_1_1.title_len_p90` | 891 | 828 | -63 | ↓ good |
| `quant.stage_1_1.title_len_p99` | 916 | 866 | -50 | ↓ good |
| `quant.stage_1_1.title_newline_rate` | 0.38 | 0.34 | -0.04 | ↓ good |
| `quant.stage_1_1.title_reasoning_leak_rate` | 0.38 | 0.34 | -0.04 | ↓ good |
| `quant.stage_1_1_5.dedup_in_count` | 50 | 50 | +0 | · |
| `quant.stage_1_1_5.dedup_out_count` | 50 | 50 | +0 | · |
| `quant.stage_1_1_5.dedup_reduction_rate` | 0 | 0 | +0 | · |
| `quant.stage_1_2.n` | 0 | 1 | +1 | ↑ good |
| `quant.stage_1_2.retention_from_stage_1_1_5` | 0 | 0.02 | +0.02 | ↑ good |
| `stage_1_1.attr_grounded_rate` | 0.467 | 0.51 | +0.043 | ↑ good |
| `stage_1_1.avg_persona_reflection` | 3.62 | 4.107 | +0.487 | ↑ good |
| `stage_1_1.avg_raw_text_naturalness` | 3.98 | 4.133 | +0.153 | ↑ good |
| `stage_1_1.failure_modes.attr_mono_value` | 6 | 6 | +0 | · |
| `stage_1_1.failure_modes.attr_ungrounded` | 23 | 26 | +3 | ↑ good |
| `stage_1_1.failure_modes.language_issue` | 7 | 7 | +0 | · |
| `stage_1_1.failure_modes.length_violation` | 12 | 8 | -4 | ↓ bad |
| `stage_1_1.failure_modes.missing_tpo` | 17 | 11 | -6 | ↓ bad |
| `stage_1_1.failure_modes.non_fashion_item` | 9 | 5 | -4 | ↓ bad |
| `stage_1_1.failure_modes.persona_drift` | 19 | 11 | -8 | ↓ bad |
| `stage_1_1.failure_modes.rating_sentiment_mismatch` | 12 | 10 | -2 | ↓ bad |
| `stage_1_1.failure_modes.title_format_violation` | 41 | 36 | -5 | ↓ bad |
| `stage_1_1.failure_modes.title_length_violation` | 39 | 31 | -8 | ↓ bad |
| `stage_1_1.failure_modes.title_reasoning_leak` | 25 | 22 | -3 | ↓ bad |
| `stage_1_1.fashion_rate` | 0.853 | 0.92 | +0.067 | ↑ good |
| `stage_1_1.has_tpo_rate` | 0.947 | 1 | +0.053 | ↑ good |
| `stage_1_1.n_evaluated` | 50 | 50 | +0 | · |
| `stage_1_1.rating_sentiment_consistent_rate` | 0.78 | 0.827 | +0.047 | ↑ good |
| `stage_1_1.raw_text_within_spec_rate` | 0.86 | 0.913 | +0.053 | ↑ good |
| `stage_1_1.title_format_ok_rate` | 0.247 | 0.427 | +0.18 | ↑ good |
| `stage_1_1.title_reasoning_leak_rate` | 0.473 | 0.413 | -0.06 | ↓ good |
| `stage_1_1.title_within_spec_rate` | 0.273 | 0.32 | +0.047 | ↑ good |
| `stage_1_1_5.dedup_in_count` | 50 | 50 | +0 | · |
| `stage_1_1_5.dedup_miss_count` | 10 | 5 | -5 | ↓ good |
| `stage_1_1_5.dedup_miss_rate` | 0.167 | 0.093 | -0.074 | ↓ good |
| `stage_1_1_5.dedup_out_count` | 50 | 50 | +0 | · |
| `stage_1_1_5.dedup_reduction_rate` | 0 | 0 | +0 | · |
| `stage_1_1_5.failure_modes.low_dedup_reduction` | 1 | 1 | +0 | · |
| `stage_1_1_5.failure_modes.near_duplicate_missed` | 8 | 5 | -3 | ↓ bad |
| `stage_1_1_5.failure_modes.wrong_removal` | 0 | 0 | +0 | · |
| `stage_1_1_5.largest_miss_cluster_size` | 3 | 2 | -1 | ↓ good |
| `stage_1_2.avg_text_quality` | — | 3.667 | — | · |
| `stage_1_2.failure_modes.duplicate_suspect` | 0 | 0 | +0 | · |
| `stage_1_2.failure_modes.language_issue` | 0 | 0 | +0 | · |
| `stage_1_2.failure_modes.noise_text` | 0 | 0 | +0 | · |
| `stage_1_2.failure_modes.non_fashion_item` | 0 | 0 | +0 | · |
| `stage_1_2.failure_modes.pii_leak` | 0 | 0 | +0 | · |
| `stage_1_2.failure_modes.too_short` | 0 | 0 | +0 | · |
| `stage_1_2.fashion_rate` | 0 | 1 | +1 | ↑ good |
| `stage_1_2.has_tpo_rate` | 0 | 0.667 | +0.667 | ↑ good |
| `stage_1_2.n_evaluated` | 0 | 1 | +1 | ↑ good |
| `stage_1_2.pii_rate` | 0 | 0.333 | +0.333 | ↑ bad |

## Output hashes

| file | sha256 |
|---|---|
| `stage_1_0_seed.jsonl` | `` |
| `stage_1_1_synthetic.jsonl` | `sha256:988838bb0068f3d185effea1294df25249e71b29bbae1e2ba0b3dfc1dfcf7470` |
| `stage_1_1_5_deduped.jsonl` | `sha256:988838bb0068f3d185effea1294df25249e71b29bbae1e2ba0b3dfc1dfcf7470` |
| `stage_1_2_processed.jsonl` | `sha256:875267748b099d50e76d432456112130b2a7ed6ea6dffe8bc87480820b3560e0` |