# Comparison: iter_27_semdedup_aggressive vs iter_21_dedup_v2

- this   iter: `iter_27_semdedup_aggressive`
- parent iter: `iter_21_dedup_v2`
- this timestamp : 2026-04-22T01:35:41+00:00
- promote flag   : False  high_variance: False

## Metric diff

| metric | parent | this | Δ | direction |
|---|---|---|---|---|
| `e2e.e2e_retention` | 0.84 | 0.48 | -0.36 | ↓ bad |
| `e2e.input_rows_seed` | 50 | 50 | +0 | · |
| `e2e.output_rows_by_stage` | <list len=4> | <list len=4> | — | · |
| `quant.e2e.e2e_retention` | 0.84 | 0.48 | -0.36 | ↓ bad |
| `quant.e2e.input_rows_seed` | 50 | 50 | +0 | · |
| `quant.e2e.output_rows_by_stage` | <list len=4> | <list len=4> | — | · |
| `quant.stage_1_0.n` | 50 | 50 | +0 | · |
| `quant.stage_1_0.rating_3_share` | 0 | 0 | +0 | · |
| `quant.stage_1_0.rating_hist.1` | 10 | 10 | +0 | · |
| `quant.stage_1_0.rating_hist.2` | 16 | 16 | +0 | · |
| `quant.stage_1_0.rating_hist.4` | 3 | 3 | +0 | · |
| `quant.stage_1_0.rating_hist.5` | 21 | 21 | +0 | · |
| `quant.stage_1_1.color_top2_share` | 0.571 | 0.571 | +0 | · |
| `quant.stage_1_1.color_unique` | 8 | 8 | +0 | · |
| `quant.stage_1_1.color_white_black_share` | 0.476 | 0.476 | +0 | · |
| `quant.stage_1_1.n` | 42 | 42 | +0 | · |
| `quant.stage_1_1.rating_3_share` | 0.262 | 0.262 | +0 | · |
| `quant.stage_1_1.rating_hist.1` | 3 | 3 | +0 | · |
| `quant.stage_1_1.rating_hist.2` | 9 | 9 | +0 | · |
| `quant.stage_1_1.rating_hist.3` | 11 | 11 | +0 | · |
| `quant.stage_1_1.rating_hist.4` | 9 | 9 | +0 | · |
| `quant.stage_1_1.rating_hist.5` | 10 | 10 | +0 | · |
| `quant.stage_1_1.raw_text_len_max` | 314 | 314 | +0 | · |
| `quant.stage_1_1.raw_text_len_median` | 143 | 143 | +0 | · |
| `quant.stage_1_1.raw_text_len_min` | 88 | 88 | +0 | · |
| `quant.stage_1_1.raw_text_len_p90` | 201 | 201 | +0 | · |
| `quant.stage_1_1.size_suspicious_rate` | 0.095 | 0.095 | +0 | · |
| `quant.stage_1_1.size_unique` | 8 | 8 | +0 | · |
| `quant.stage_1_1.style_top1_share` | 0.595 | 0.595 | +0 | · |
| `quant.stage_1_1.style_top1_value` | 캐주얼 | 캐주얼 | — | · |
| `quant.stage_1_1.style_unique` | 7 | 7 | +0 | · |
| `quant.stage_1_1.title_len_max` | 30 | 30 | +0 | · |
| `quant.stage_1_1.title_len_median` | 20 | 20 | +0 | · |
| `quant.stage_1_1.title_len_min` | 11 | 11 | +0 | · |
| `quant.stage_1_1.title_len_p90` | 29 | 29 | +0 | · |
| `quant.stage_1_1.title_len_p99` | 30 | 30 | +0 | · |
| `quant.stage_1_1.title_newline_rate` | 0 | 0 | +0 | · |
| `quant.stage_1_1.title_reasoning_leak_rate` | 0 | 0 | +0 | · |
| `quant.stage_1_1_5.dedup_in_count` | 42 | 42 | +0 | · |
| `quant.stage_1_1_5.dedup_out_count` | 42 | 24 | -18 | ↓ bad |
| `quant.stage_1_1_5.dedup_reduction_rate` | 0 | 0.429 | +0.429 | ↑ good |
| `quant.stage_1_2.n` | 42 | 24 | -18 | ↓ bad |
| `quant.stage_1_2.retention_from_stage_1_1_5` | 1 | 1 | +0 | · |
| `stage_1_0.avg_text_quality` | 2.827 | 2.833 | +0.006 | ↑ good |
| `stage_1_0.failure_modes.duplicate_suspect` | 0 | 0 | +0 | · |
| `stage_1_0.failure_modes.language_issue` | 0 | 0 | +0 | · |
| `stage_1_0.failure_modes.noise_text` | 2 | 1 | -1 | ↓ bad |
| `stage_1_0.failure_modes.non_fashion_item` | 7 | 8 | +1 | ↑ good |
| `stage_1_0.failure_modes.non_fashion游戏副本` | 2 | — | — | · |
| `stage_1_0.failure_modes.pii_leak` | 0 | 0 | +0 | · |
| `stage_1_0.failure_modes.too_short` | 16 | 18 | +2 | ↑ good |
| `stage_1_0.fashion_rate` | 0.9 | 0.893 | -0.007 | ↓ bad |
| `stage_1_0.has_tpo_rate` | 0.22 | 0.307 | +0.087 | ↑ good |
| `stage_1_0.n_evaluated` | 50 | 50 | +0 | · |
| `stage_1_0.pii_rate` | 0.167 | 0.24 | +0.073 | ↑ bad |
| `stage_1_1.attr_grounded_rate` | 0.99 | 0.99 | +0 | · |
| `stage_1_1.avg_persona_reflection` | 4.66 | 4.58 | -0.08 | ↓ bad |
| `stage_1_1.avg_raw_text_naturalness` | 3.833 | 3.857 | +0.024 | ↑ good |
| `stage_1_1.failure_modes.attr_mono_value` | 1 | 2 | +1 | ↑ good |
| `stage_1_1.failure_modes.attr_ungrounded` | 3 | 2 | -1 | ↓ bad |
| `stage_1_1.failure_modes.language_issue` | 14 | 18 | +4 | ↑ good |
| `stage_1_1.failure_modes.length_violation` | 0 | 0 | +0 | · |
| `stage_1_1.failure_modes.missing_tpo` | 5 | 8 | +3 | ↑ good |
| `stage_1_1.failure_modes.non_fashion_item` | 3 | 3 | +0 | · |
| `stage_1_1.failure_modes.persona_drift` | 13 | 12 | -1 | ↓ bad |
| `stage_1_1.failure_modes.rating_sentiment_mismatch` | 2 | 2 | +0 | · |
| `stage_1_1.failure_modes.title_format_violation` | 29 | 28 | -1 | ↓ bad |
| `stage_1_1.failure_modes.title_length_violation` | 22 | 23 | +1 | ↑ good |
| `stage_1_1.failure_modes.title_reasoning_leak` | 1 | 1 | +0 | · |
| `stage_1_1.fashion_rate` | 0.97 | 0.97 | +0 | · |
| `stage_1_1.has_tpo_rate` | 0.983 | 0.977 | -0.006 | ↓ bad |
| `stage_1_1.n_evaluated` | 42 | 42 | +0 | · |
| `stage_1_1.rating_sentiment_consistent_rate` | 0.97 | 0.97 | +0 | · |
| `stage_1_1.raw_text_within_spec_rate` | 1 | 1 | +0 | · |
| `stage_1_1.title_format_ok_rate` | 0.39 | 0.397 | +0.007 | ↑ good |
| `stage_1_1.title_reasoning_leak_rate` | 0.013 | 0.02 | +0.007 | ↑ bad |
| `stage_1_1.title_within_spec_rate` | 0.563 | 0.557 | -0.006 | ↓ bad |
| `stage_1_1_5.dedup_in_count` | 42 | 42 | +0 | · |
| `stage_1_1_5.dedup_miss_count` | 9 | 4 | -5 | ↓ good |
| `stage_1_1_5.dedup_miss_rate` | 0.151 | 0.181 | +0.03 | ↑ bad |
| `stage_1_1_5.dedup_out_count` | 42 | 24 | -18 | ↓ bad |
| `stage_1_1_5.dedup_reduction_rate` | 0 | 0.429 | +0.429 | ↑ good |
| `stage_1_1_5.failure_modes.low_dedup_reduction` | 1 | 0 | -1 | ↓ bad |
| `stage_1_1_5.failure_modes.near_duplicate_missed` | 8 | 5 | -3 | ↓ bad |
| `stage_1_1_5.failure_modes.wrong_removal` | 0 | 0 | +0 | · |
| `stage_1_1_5.largest_miss_cluster_size` | 3 | 2 | -1 | ↓ good |
| `stage_1_2.avg_text_quality` | 3.937 | 3.987 | +0.05 | ↑ good |
| `stage_1_2.failure_modes.duplicate_suspect` | 0 | 0 | +0 | · |
| `stage_1_2.failure_modes.language_issue` | 0 | 0 | +0 | · |
| `stage_1_2.failure_modes.noise_text` | 0 | 0 | +0 | · |
| `stage_1_2.failure_modes.non_fashion_item` | 2 | 1 | -1 | ↓ bad |
| `stage_1_2.failure_modes.pii_leak` | 24 | 11 | -13 | ↓ bad |
| `stage_1_2.failure_modes.too_short` | 1 | 1 | +0 | · |
| `stage_1_2.fashion_rate` | 0.97 | 0.973 | +0.003 | ↑ good |
| `stage_1_2.has_tpo_rate` | 0.717 | 0.71 | -0.007 | ↓ bad |
| `stage_1_2.n_evaluated` | 42 | 24 | -18 | ↓ bad |
| `stage_1_2.pii_rate` | 0.473 | 0.407 | -0.066 | ↓ good |

## Output hashes

| file | sha256 |
|---|---|
| `stage_1_0_seed.jsonl` | `sha256:42dbc866bdb796968ee245e4fca0d480683ae7889fc81b44787e23c507f4c738` |
| `stage_1_1_synthetic.jsonl` | `sha256:5e513bc75b3e3133546abfc72529f59850812e9fc133708610916b846fb640b6` |
| `stage_1_1_5_deduped.jsonl` | `sha256:369d54cfc3d783f295bc00b0e6e5681154f2db9197d87fb57a7cc89f97e0abc4` |
| `stage_1_2_processed.jsonl` | `sha256:369d54cfc3d783f295bc00b0e6e5681154f2db9197d87fb57a7cc89f97e0abc4` |