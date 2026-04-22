# Comparison: iter_22_h1_prompt_only vs iter_17_postgen_fashion_filter

- this   iter: `iter_22_h1_prompt_only`
- parent iter: `iter_17_postgen_fashion_filter`
- this timestamp : 2026-04-21T23:59:11+00:00
- promote flag   : False  high_variance: False

## Metric diff

| metric | parent | this | Δ | direction |
|---|---|---|---|---|
| `e2e.e2e_retention` | 0.88 | 0.88 | +0 | · |
| `e2e.input_rows_seed` | 50 | 50 | +0 | · |
| `e2e.output_rows_by_stage` | <list len=4> | <list len=4> | — | · |
| `quant.e2e.e2e_retention` | 0.88 | 0.88 | +0 | · |
| `quant.e2e.input_rows_seed` | 50 | 50 | +0 | · |
| `quant.e2e.output_rows_by_stage` | <list len=4> | <list len=4> | — | · |
| `quant.stage_1_0.n` | 50 | 50 | +0 | · |
| `quant.stage_1_0.rating_3_share` | 0 | 0 | +0 | · |
| `quant.stage_1_0.rating_hist.1` | 10 | 10 | +0 | · |
| `quant.stage_1_0.rating_hist.2` | 16 | 16 | +0 | · |
| `quant.stage_1_0.rating_hist.4` | 3 | 3 | +0 | · |
| `quant.stage_1_0.rating_hist.5` | 21 | 21 | +0 | · |
| `quant.stage_1_1.color_top2_share` | 0.455 | 0.5 | +0.045 | ↑ bad |
| `quant.stage_1_1.color_unique` | 6 | 7 | +1 | ↑ good |
| `quant.stage_1_1.color_white_black_share` | 0.455 | 0.409 | -0.046 | ↓ good |
| `quant.stage_1_1.n` | 44 | 44 | +0 | · |
| `quant.stage_1_1.rating_3_share` | 0.273 | 0.25 | -0.023 | ↓ bad |
| `quant.stage_1_1.rating_hist.1` | 6 | 6 | +0 | · |
| `quant.stage_1_1.rating_hist.2` | 12 | 8 | -4 | ↓ bad |
| `quant.stage_1_1.rating_hist.3` | 12 | 11 | -1 | ↓ bad |
| `quant.stage_1_1.rating_hist.4` | 3 | 11 | +8 | ↑ good |
| `quant.stage_1_1.rating_hist.5` | 11 | 8 | -3 | ↓ bad |
| `quant.stage_1_1.raw_text_len_max` | 274 | 236 | -38 | ↓ bad |
| `quant.stage_1_1.raw_text_len_median` | 144 | 147 | +3 | ↑ good |
| `quant.stage_1_1.raw_text_len_min` | 108 | 110 | +2 | ↑ good |
| `quant.stage_1_1.raw_text_len_p90` | 202 | 171 | -31 | ↓ bad |
| `quant.stage_1_1.size_suspicious_rate` | 0.114 | 0.091 | -0.023 | ↓ good |
| `quant.stage_1_1.size_unique` | 11 | 9 | -2 | ↓ bad |
| `quant.stage_1_1.style_top1_share` | 0.568 | 0.477 | -0.091 | ↓ good |
| `quant.stage_1_1.style_top1_value` | 캐주얼 | 캐주얼 | — | · |
| `quant.stage_1_1.style_unique` | 7 | 7 | +0 | · |
| `quant.stage_1_1.title_len_max` | 30 | 30 | +0 | · |
| `quant.stage_1_1.title_len_median` | 23 | 15 | -8 | ↓ bad |
| `quant.stage_1_1.title_len_min` | 13 | 8 | -5 | ↓ bad |
| `quant.stage_1_1.title_len_p90` | 30 | 29 | -1 | ↓ good |
| `quant.stage_1_1.title_len_p99` | 30 | 30 | +0 | · |
| `quant.stage_1_1.title_newline_rate` | 0 | 0 | +0 | · |
| `quant.stage_1_1.title_reasoning_leak_rate` | 0 | 0 | +0 | · |
| `quant.stage_1_1_5.dedup_in_count` | 44 | 44 | +0 | · |
| `quant.stage_1_1_5.dedup_out_count` | 44 | 44 | +0 | · |
| `quant.stage_1_1_5.dedup_reduction_rate` | 0 | 0 | +0 | · |
| `quant.stage_1_2.n` | 44 | 44 | +0 | · |
| `quant.stage_1_2.retention_from_stage_1_1_5` | 1 | 1 | +0 | · |
| `stage_1_0.avg_text_quality` | 2.793 | 2.773 | -0.02 | ↓ bad |
| `stage_1_0.failure_modes.duplicate_suspect` | 0 | 0 | +0 | · |
| `stage_1_0.failure_modes.language_issue` | 0 | 0 | +0 | · |
| `stage_1_0.failure_modes.noise_text` | 1 | 2 | +1 | ↑ good |
| `stage_1_0.failure_modes.non_fashion_item` | 10 | 10 | +0 | · |
| `stage_1_0.failure_modes.non_fashion游戏副本` | 1 | 2 | +1 | ↑ good |
| `stage_1_0.failure_modes.pii_leak` | 0 | 0 | +0 | · |
| `stage_1_0.failure_modes.too_short` | 16 | 21 | +5 | ↑ good |
| `stage_1_0.fashion_rate` | 0.873 | 0.867 | -0.006 | ↓ bad |
| `stage_1_0.has_tpo_rate` | 0.273 | 0.24 | -0.033 | ↓ bad |
| `stage_1_0.n_evaluated` | 50 | 50 | +0 | · |
| `stage_1_0.pii_rate` | 0.233 | 0.173 | -0.06 | ↓ good |
| `stage_1_1.attr_grounded_rate` | 1 | 0.983 | -0.017 | ↓ bad |
| `stage_1_1.avg_persona_reflection` | 4.553 | 4.463 | -0.09 | ↓ bad |
| `stage_1_1.avg_raw_text_naturalness` | 3.86 | 3.75 | -0.11 | ↓ bad |
| `stage_1_1.failure_modes.attr_mono_value` | 4 | 2 | -2 | ↓ bad |
| `stage_1_1.failure_modes.attr_ungrounded` | 3 | 3 | +0 | · |
| `stage_1_1.failure_modes.language_issue` | 18 | 18 | +0 | · |
| `stage_1_1.failure_modes.length_violation` | 3 | 0 | -3 | ↓ bad |
| `stage_1_1.failure_modes.missing_tpo` | 5 | 12 | +7 | ↑ good |
| `stage_1_1.failure_modes.non_fashion_item` | 4 | 8 | +4 | ↑ good |
| `stage_1_1.failure_modes.persona_drift` | 13 | 12 | -1 | ↓ bad |
| `stage_1_1.failure_modes.rating_sentiment_mismatch` | 5 | 3 | -2 | ↓ bad |
| `stage_1_1.failure_modes.title_format_violation` | 28 | 39 | +11 | ↑ good |
| `stage_1_1.failure_modes.title_length_violation` | 26 | 35 | +9 | ↑ good |
| `stage_1_1.failure_modes.title_reasoning_leak` | 5 | 4 | -1 | ↓ bad |
| `stage_1_1.fashion_rate` | 0.953 | 0.9 | -0.053 | ↓ bad |
| `stage_1_1.has_tpo_rate` | 0.967 | 0.97 | +0.003 | ↑ good |
| `stage_1_1.n_evaluated` | 44 | 44 | +0 | · |
| `stage_1_1.rating_sentiment_consistent_rate` | 0.917 | 0.953 | +0.036 | ↑ good |
| `stage_1_1.raw_text_within_spec_rate` | 0.977 | 0.983 | +0.006 | ↑ good |
| `stage_1_1.title_format_ok_rate` | 0.443 | 0.12 | -0.323 | ↓ bad |
| `stage_1_1.title_reasoning_leak_rate` | 0.09 | 0.047 | -0.043 | ↓ good |
| `stage_1_1.title_within_spec_rate` | 0.487 | 0.347 | -0.14 | ↓ bad |
| `stage_1_1_5.dedup_in_count` | 44 | 44 | +0 | · |
| `stage_1_1_5.dedup_miss_count` | 8 | 5 | -3 | ↓ good |
| `stage_1_1_5.dedup_miss_rate` | 0.167 | 0.114 | -0.053 | ↓ good |
| `stage_1_1_5.dedup_out_count` | 44 | 44 | +0 | · |
| `stage_1_1_5.dedup_reduction_rate` | 0 | 0 | +0 | · |
| `stage_1_1_5.failure_modes.low_dedup_reduction` | 1 | 1 | +0 | · |
| `stage_1_1_5.failure_modes.near_duplicate_missed` | 7 | 4 | -3 | ↓ bad |
| `stage_1_1_5.failure_modes.wrong_removal` | 0 | 0 | +0 | · |
| `stage_1_1_5.largest_miss_cluster_size` | 3 | 3 | +0 | · |
| `stage_1_2.avg_text_quality` | 3.947 | 3.937 | -0.01 | ↓ bad |
| `stage_1_2.failure_modes.duplicate_suspect` | 0 | 0 | +0 | · |
| `stage_1_2.failure_modes.language_issue` | 0 | 0 | +0 | · |
| `stage_1_2.failure_modes.noise_text` | 0 | 0 | +0 | · |
| `stage_1_2.failure_modes.non_fashion_item` | 2 | 2 | +0 | · |
| `stage_1_2.failure_modes.pii_leak` | 21 | 18 | -3 | ↓ bad |
| `stage_1_2.failure_modes.too_short` | 0 | 2 | +2 | ↑ good |
| `stage_1_2.fashion_rate` | 0.977 | 0.967 | -0.01 | ↓ bad |
| `stage_1_2.has_tpo_rate` | 0.737 | 0.69 | -0.047 | ↓ bad |
| `stage_1_2.n_evaluated` | 44 | 44 | +0 | · |
| `stage_1_2.pii_rate` | 0.437 | 0.4 | -0.037 | ↓ good |

## Output hashes

| file | sha256 |
|---|---|
| `stage_1_0_seed.jsonl` | `sha256:42dbc866bdb796968ee245e4fca0d480683ae7889fc81b44787e23c507f4c738` |
| `stage_1_1_synthetic.jsonl` | `sha256:9c86b98827b797a7479d4681b1cd29be44477dd62bc25aeac31646797d737c03` |
| `stage_1_1_5_deduped.jsonl` | `sha256:9c86b98827b797a7479d4681b1cd29be44477dd62bc25aeac31646797d737c03` |
| `stage_1_2_processed.jsonl` | `sha256:9c86b98827b797a7479d4681b1cd29be44477dd62bc25aeac31646797d737c03` |