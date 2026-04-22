# Comparison: iter_26_semantic_dedup vs iter_21_dedup_v2

- this   iter: `iter_26_semantic_dedup`
- parent iter: `iter_21_dedup_v2`
- this timestamp : 2026-04-22T01:19:14+00:00
- promote flag   : False  high_variance: False

## Metric diff

| metric | parent | this | Δ | direction |
|---|---|---|---|---|
| `e2e.e2e_retention` | 0.84 | 0.66 | -0.18 | ↓ bad |
| `e2e.input_rows_seed` | 50 | 50 | +0 | · |
| `e2e.output_rows_by_stage` | <list len=4> | <list len=4> | — | · |
| `quant.e2e.e2e_retention` | 0.84 | 0.66 | -0.18 | ↓ bad |
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
| `quant.stage_1_1_5.dedup_out_count` | 42 | 33 | -9 | ↓ bad |
| `quant.stage_1_1_5.dedup_reduction_rate` | 0 | 0.214 | +0.214 | ↑ good |
| `quant.stage_1_2.n` | 42 | 33 | -9 | ↓ bad |
| `quant.stage_1_2.retention_from_stage_1_1_5` | 1 | 1 | +0 | · |
| `stage_1_0.avg_text_quality` | 2.827 | 2.847 | +0.02 | ↑ good |
| `stage_1_0.failure_modes.duplicate_suspect` | 0 | 0 | +0 | · |
| `stage_1_0.failure_modes.language_issue` | 0 | 0 | +0 | · |
| `stage_1_0.failure_modes.noise_text` | 2 | 1 | -1 | ↓ bad |
| `stage_1_0.failure_modes.non_fashion_item` | 7 | 10 | +3 | ↑ good |
| `stage_1_0.failure_modes.non_fashion游戏副本` | 2 | 2 | +0 | · |
| `stage_1_0.failure_modes.pii_leak` | 0 | 0 | +0 | · |
| `stage_1_0.failure_modes.too_short` | 16 | 16 | +0 | · |
| `stage_1_0.fashion_rate` | 0.9 | 0.88 | -0.02 | ↓ bad |
| `stage_1_0.has_tpo_rate` | 0.22 | 0.333 | +0.113 | ↑ good |
| `stage_1_0.n_evaluated` | 50 | 50 | +0 | · |
| `stage_1_0.pii_rate` | 0.167 | 0.273 | +0.106 | ↑ bad |
| `stage_1_1.attr_grounded_rate` | 0.99 | 0.99 | +0 | · |
| `stage_1_1.avg_persona_reflection` | 4.66 | 4.7 | +0.04 | ↑ good |
| `stage_1_1.avg_raw_text_naturalness` | 3.833 | 3.883 | +0.05 | ↑ good |
| `stage_1_1.failure_modes.attr_mono_value` | 1 | 2 | +1 | ↑ good |
| `stage_1_1.failure_modes.attr_ungrounded` | 3 | 2 | -1 | ↓ bad |
| `stage_1_1.failure_modes.language_issue` | 14 | 19 | +5 | ↑ good |
| `stage_1_1.failure_modes.length_violation` | 0 | 1 | +1 | ↑ good |
| `stage_1_1.failure_modes.missing_tpo` | 5 | 3 | -2 | ↓ bad |
| `stage_1_1.failure_modes.non_fashion_item` | 3 | 2 | -1 | ↓ bad |
| `stage_1_1.failure_modes.persona_drift` | 13 | 12 | -1 | ↓ bad |
| `stage_1_1.failure_modes.rating_sentiment_mismatch` | 2 | 2 | +0 | · |
| `stage_1_1.failure_modes.title_format_violation` | 29 | 28 | -1 | ↓ bad |
| `stage_1_1.failure_modes.title_length_violation` | 22 | 25 | +3 | ↑ good |
| `stage_1_1.failure_modes.title_reasoning_leak` | 1 | 2 | +1 | ↑ good |
| `stage_1_1.fashion_rate` | 0.97 | 0.97 | +0 | · |
| `stage_1_1.has_tpo_rate` | 0.983 | 0.993 | +0.01 | ↑ good |
| `stage_1_1.n_evaluated` | 42 | 42 | +0 | · |
| `stage_1_1.rating_sentiment_consistent_rate` | 0.97 | 0.97 | +0 | · |
| `stage_1_1.raw_text_within_spec_rate` | 1 | 0.993 | -0.007 | ↓ bad |
| `stage_1_1.title_format_ok_rate` | 0.39 | 0.393 | +0.003 | ↑ good |
| `stage_1_1.title_reasoning_leak_rate` | 0.013 | 0.03 | +0.017 | ↑ bad |
| `stage_1_1.title_within_spec_rate` | 0.563 | 0.563 | +0 | · |
| `stage_1_1_5.dedup_in_count` | 42 | 42 | +0 | · |
| `stage_1_1_5.dedup_miss_count` | 9 | 8 | -1 | ↓ good |
| `stage_1_1_5.dedup_miss_rate` | 0.151 | 0.182 | +0.031 | ↑ bad |
| `stage_1_1_5.dedup_out_count` | 42 | 33 | -9 | ↓ bad |
| `stage_1_1_5.dedup_reduction_rate` | 0 | 0.214 | +0.214 | ↑ good |
| `stage_1_1_5.failure_modes.low_dedup_reduction` | 1 | 0 | -1 | ↓ bad |
| `stage_1_1_5.failure_modes.near_duplicate_missed` | 8 | 7 | -1 | ↓ bad |
| `stage_1_1_5.failure_modes.wrong_removal` | 0 | 0 | +0 | · |
| `stage_1_1_5.largest_miss_cluster_size` | 3 | 3 | +0 | · |
| `stage_1_2.avg_text_quality` | 3.937 | 4.03 | +0.093 | ↑ good |
| `stage_1_2.failure_modes.duplicate_suspect` | 0 | 0 | +0 | · |
| `stage_1_2.failure_modes.language_issue` | 0 | 0 | +0 | · |
| `stage_1_2.failure_modes.noise_text` | 0 | 1 | +1 | ↑ good |
| `stage_1_2.failure_modes.non_fashion_item` | 2 | 1 | -1 | ↓ bad |
| `stage_1_2.failure_modes.pii_leak` | 24 | 18 | -6 | ↓ bad |
| `stage_1_2.failure_modes.too_short` | 1 | 0 | -1 | ↓ bad |
| `stage_1_2.fashion_rate` | 0.97 | 0.97 | +0 | · |
| `stage_1_2.has_tpo_rate` | 0.717 | 0.707 | -0.01 | ↓ bad |
| `stage_1_2.n_evaluated` | 42 | 33 | -9 | ↓ bad |
| `stage_1_2.pii_rate` | 0.473 | 0.453 | -0.02 | ↓ good |

## Output hashes

| file | sha256 |
|---|---|
| `stage_1_0_seed.jsonl` | `sha256:42dbc866bdb796968ee245e4fca0d480683ae7889fc81b44787e23c507f4c738` |
| `stage_1_1_synthetic.jsonl` | `sha256:5e513bc75b3e3133546abfc72529f59850812e9fc133708610916b846fb640b6` |
| `stage_1_1_5_deduped.jsonl` | `sha256:49dde5e8e4340fe3a229c012fbb0aca2395a56eac75b8fc3af74e46d76149ba5` |
| `stage_1_2_processed.jsonl` | `sha256:49dde5e8e4340fe3a229c012fbb0aca2395a56eac75b8fc3af74e46d76149ba5` |