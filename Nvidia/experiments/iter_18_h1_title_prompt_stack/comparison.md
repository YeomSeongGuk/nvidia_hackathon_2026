# Comparison: iter_18_h1_title_prompt_stack vs iter_17_postgen_fashion_filter

- this   iter: `iter_18_h1_title_prompt_stack`
- parent iter: `iter_17_postgen_fashion_filter`
- this timestamp : 2026-04-21T21:37:32+00:00
- promote flag   : False  high_variance: False

## Metric diff

| metric | parent | this | Δ | direction |
|---|---|---|---|---|
| `e2e.e2e_retention` | 0.88 | 0.82 | -0.06 | ↓ bad |
| `e2e.input_rows_seed` | 50 | 50 | +0 | · |
| `e2e.output_rows_by_stage` | <list len=4> | <list len=4> | — | · |
| `quant.e2e.e2e_retention` | 0.88 | 0.82 | -0.06 | ↓ bad |
| `quant.e2e.input_rows_seed` | 50 | 50 | +0 | · |
| `quant.e2e.output_rows_by_stage` | <list len=4> | <list len=4> | — | · |
| `quant.stage_1_0.n` | 50 | 50 | +0 | · |
| `quant.stage_1_0.rating_3_share` | 0 | 0 | +0 | · |
| `quant.stage_1_0.rating_hist.1` | 10 | 10 | +0 | · |
| `quant.stage_1_0.rating_hist.2` | 16 | 16 | +0 | · |
| `quant.stage_1_0.rating_hist.4` | 3 | 3 | +0 | · |
| `quant.stage_1_0.rating_hist.5` | 21 | 21 | +0 | · |
| `quant.stage_1_1.color_top2_share` | 0.455 | 0.488 | +0.033 | ↑ bad |
| `quant.stage_1_1.color_unique` | 6 | 7 | +1 | ↑ good |
| `quant.stage_1_1.color_white_black_share` | 0.455 | 0.488 | +0.033 | ↑ bad |
| `quant.stage_1_1.n` | 44 | 41 | -3 | ↓ bad |
| `quant.stage_1_1.rating_3_share` | 0.273 | 0.146 | -0.127 | ↓ bad |
| `quant.stage_1_1.rating_hist.1` | 6 | 7 | +1 | ↑ good |
| `quant.stage_1_1.rating_hist.2` | 12 | 10 | -2 | ↓ bad |
| `quant.stage_1_1.rating_hist.3` | 12 | 6 | -6 | ↓ bad |
| `quant.stage_1_1.rating_hist.4` | 3 | 13 | +10 | ↑ good |
| `quant.stage_1_1.rating_hist.5` | 11 | 5 | -6 | ↓ bad |
| `quant.stage_1_1.raw_text_len_max` | 274 | 220 | -54 | ↓ bad |
| `quant.stage_1_1.raw_text_len_median` | 144 | 147 | +3 | ↑ good |
| `quant.stage_1_1.raw_text_len_min` | 108 | 104 | -4 | ↓ bad |
| `quant.stage_1_1.raw_text_len_p90` | 202 | 185 | -17 | ↓ bad |
| `quant.stage_1_1.size_suspicious_rate` | 0.114 | 0.098 | -0.016 | ↓ good |
| `quant.stage_1_1.size_unique` | 11 | 7 | -4 | ↓ bad |
| `quant.stage_1_1.style_top1_share` | 0.568 | 0.439 | -0.129 | ↓ good |
| `quant.stage_1_1.style_top1_value` | 캐주얼 | 캐주얼 | — | · |
| `quant.stage_1_1.style_unique` | 7 | 7 | +0 | · |
| `quant.stage_1_1.title_len_max` | 30 | 30 | +0 | · |
| `quant.stage_1_1.title_len_median` | 23 | 16 | -7 | ↓ bad |
| `quant.stage_1_1.title_len_min` | 13 | 4 | -9 | ↓ bad |
| `quant.stage_1_1.title_len_p90` | 30 | 29 | -1 | ↓ good |
| `quant.stage_1_1.title_len_p99` | 30 | 30 | +0 | · |
| `quant.stage_1_1.title_newline_rate` | 0 | 0 | +0 | · |
| `quant.stage_1_1.title_reasoning_leak_rate` | 0 | 0 | +0 | · |
| `quant.stage_1_1_5.dedup_in_count` | 44 | 41 | -3 | ↓ bad |
| `quant.stage_1_1_5.dedup_out_count` | 44 | 41 | -3 | ↓ bad |
| `quant.stage_1_1_5.dedup_reduction_rate` | 0 | 0 | +0 | · |
| `quant.stage_1_2.n` | 44 | 41 | -3 | ↓ bad |
| `quant.stage_1_2.retention_from_stage_1_1_5` | 1 | 1 | +0 | · |
| `stage_1_0.avg_text_quality` | 2.793 | 2.8 | +0.007 | ↑ good |
| `stage_1_0.failure_modes.duplicate_suspect` | 0 | 0 | +0 | · |
| `stage_1_0.failure_modes.language_issue` | 0 | 0 | +0 | · |
| `stage_1_0.failure_modes.noise_text` | 1 | 1 | +0 | · |
| `stage_1_0.failure_modes.non_fashion_item` | 10 | 9 | -1 | ↓ bad |
| `stage_1_0.failure_modes.non_fashion游戏副本` | 1 | 1 | +0 | · |
| `stage_1_0.failure_modes.pii_leak` | 0 | 0 | +0 | · |
| `stage_1_0.failure_modes.too_short` | 16 | 19 | +3 | ↑ good |
| `stage_1_0.fashion_rate` | 0.873 | 0.893 | +0.02 | ↑ good |
| `stage_1_0.has_tpo_rate` | 0.273 | 0.307 | +0.034 | ↑ good |
| `stage_1_0.n_evaluated` | 50 | 50 | +0 | · |
| `stage_1_0.pii_rate` | 0.233 | 0.267 | +0.034 | ↑ bad |
| `stage_1_1.attr_grounded_rate` | 1 | 0.997 | -0.003 | ↓ bad |
| `stage_1_1.avg_persona_reflection` | 4.553 | 4.633 | +0.08 | ↑ good |
| `stage_1_1.avg_raw_text_naturalness` | 3.86 | 3.893 | +0.033 | ↑ good |
| `stage_1_1.failure_modes.attr_mono_value` | 4 | 0 | -4 | ↓ bad |
| `stage_1_1.failure_modes.attr_ungrounded` | 3 | 2 | -1 | ↓ bad |
| `stage_1_1.failure_modes.language_issue` | 18 | 12 | -6 | ↓ bad |
| `stage_1_1.failure_modes.length_violation` | 3 | 0 | -3 | ↓ bad |
| `stage_1_1.failure_modes.missing_tpo` | 5 | 11 | +6 | ↑ good |
| `stage_1_1.failure_modes.non_fashion_item` | 4 | 7 | +3 | ↑ good |
| `stage_1_1.failure_modes.persona_drift` | 13 | 9 | -4 | ↓ bad |
| `stage_1_1.failure_modes.rating_sentiment_mismatch` | 5 | 1 | -4 | ↓ bad |
| `stage_1_1.failure_modes.title_format_violation` | 28 | 40 | +12 | ↑ good |
| `stage_1_1.failure_modes.title_length_violation` | 26 | 34 | +8 | ↑ good |
| `stage_1_1.failure_modes.title_reasoning_leak` | 5 | 4 | -1 | ↓ bad |
| `stage_1_1.fashion_rate` | 0.953 | 0.943 | -0.01 | ↓ bad |
| `stage_1_1.has_tpo_rate` | 0.967 | 0.977 | +0.01 | ↑ good |
| `stage_1_1.n_evaluated` | 44 | 41 | -3 | ↓ bad |
| `stage_1_1.rating_sentiment_consistent_rate` | 0.917 | 0.993 | +0.076 | ↑ good |
| `stage_1_1.raw_text_within_spec_rate` | 0.977 | 1 | +0.023 | ↑ good |
| `stage_1_1.title_format_ok_rate` | 0.443 | 0.057 | -0.386 | ↓ bad |
| `stage_1_1.title_reasoning_leak_rate` | 0.09 | 0.057 | -0.033 | ↓ good |
| `stage_1_1.title_within_spec_rate` | 0.487 | 0.3 | -0.187 | ↓ bad |
| `stage_1_1_5.dedup_in_count` | 44 | 41 | -3 | ↓ bad |
| `stage_1_1_5.dedup_miss_count` | 8 | 5 | -3 | ↓ good |
| `stage_1_1_5.dedup_miss_rate` | 0.167 | 0.154 | -0.013 | ↓ good |
| `stage_1_1_5.dedup_out_count` | 44 | 41 | -3 | ↓ bad |
| `stage_1_1_5.dedup_reduction_rate` | 0 | 0 | +0 | · |
| `stage_1_1_5.failure_modes.low_dedup_reduction` | 1 | 1 | +0 | · |
| `stage_1_1_5.failure_modes.near_duplicate_missed` | 7 | 5 | -2 | ↓ bad |
| `stage_1_1_5.failure_modes.wrong_removal` | 0 | 0 | +0 | · |
| `stage_1_1_5.largest_miss_cluster_size` | 3 | 2 | -1 | ↓ good |
| `stage_1_2.avg_text_quality` | 3.947 | 3.967 | +0.02 | ↑ good |
| `stage_1_2.failure_modes.duplicate_suspect` | 0 | 0 | +0 | · |
| `stage_1_2.failure_modes.language_issue` | 0 | 0 | +0 | · |
| `stage_1_2.failure_modes.noise_text` | 0 | 1 | +1 | ↑ good |
| `stage_1_2.failure_modes.non_fashion_item` | 2 | 2 | +0 | · |
| `stage_1_2.failure_modes.pii_leak` | 21 | 22 | +1 | ↑ good |
| `stage_1_2.failure_modes.too_short` | 0 | 0 | +0 | · |
| `stage_1_2.fashion_rate` | 0.977 | 0.977 | +0 | · |
| `stage_1_2.has_tpo_rate` | 0.737 | 0.727 | -0.01 | ↓ bad |
| `stage_1_2.n_evaluated` | 44 | 41 | -3 | ↓ bad |
| `stage_1_2.pii_rate` | 0.437 | 0.503 | +0.066 | ↑ bad |

## Output hashes

| file | sha256 |
|---|---|
| `stage_1_0_seed.jsonl` | `sha256:42dbc866bdb796968ee245e4fca0d480683ae7889fc81b44787e23c507f4c738` |
| `stage_1_1_synthetic.jsonl` | `sha256:eb9d2335a4c1c94e7506f10ac9c6f14949ca1a9380d620402590538c2914f5ba` |
| `stage_1_1_5_deduped.jsonl` | `sha256:eb9d2335a4c1c94e7506f10ac9c6f14949ca1a9380d620402590538c2914f5ba` |
| `stage_1_2_processed.jsonl` | `sha256:eb9d2335a4c1c94e7506f10ac9c6f14949ca1a9380d620402590538c2914f5ba` |