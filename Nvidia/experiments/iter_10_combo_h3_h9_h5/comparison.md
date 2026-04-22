# Comparison: iter_10_combo_h3_h9_h5 vs iter_09_combo_h3_h9

- this   iter: `iter_10_combo_h3_h9_h5`
- parent iter: `iter_09_combo_h3_h9`
- this timestamp : 2026-04-21T19:31:56+00:00
- promote flag   : False  high_variance: False

## Metric diff

| metric | parent | this | Δ | direction |
|---|---|---|---|---|
| `e2e.e2e_retention` | 1 | 1 | +0 | · |
| `e2e.input_rows_seed` | 50 | 50 | +0 | · |
| `e2e.output_rows_by_stage` | <list len=4> | <list len=4> | — | · |
| `quant.e2e.e2e_retention` | 1 | 1 | +0 | · |
| `quant.e2e.input_rows_seed` | 50 | 50 | +0 | · |
| `quant.e2e.output_rows_by_stage` | <list len=4> | <list len=4> | — | · |
| `quant.stage_1_0.n` | 50 | 50 | +0 | · |
| `quant.stage_1_0.rating_3_share` | 0 | 0 | +0 | · |
| `quant.stage_1_0.rating_hist.1` | 10 | 10 | +0 | · |
| `quant.stage_1_0.rating_hist.2` | 16 | 16 | +0 | · |
| `quant.stage_1_0.rating_hist.4` | 3 | 3 | +0 | · |
| `quant.stage_1_0.rating_hist.5` | 21 | 21 | +0 | · |
| `quant.stage_1_1.color_top2_share` | 0.7 | 0.54 | -0.16 | ↓ good |
| `quant.stage_1_1.color_unique` | 8 | 7 | -1 | ↓ bad |
| `quant.stage_1_1.color_white_black_share` | 0.7 | 0.48 | -0.22 | ↓ good |
| `quant.stage_1_1.n` | 50 | 50 | +0 | · |
| `quant.stage_1_1.rating_3_share` | 0 | 0 | +0 | · |
| `quant.stage_1_1.rating_hist.1` | 12 | 12 | +0 | · |
| `quant.stage_1_1.rating_hist.2` | 17 | 17 | +0 | · |
| `quant.stage_1_1.rating_hist.4` | 3 | 3 | +0 | · |
| `quant.stage_1_1.rating_hist.5` | 18 | 18 | +0 | · |
| `quant.stage_1_1.raw_text_len_max` | 209 | 334 | +125 | ↑ good |
| `quant.stage_1_1.raw_text_len_median` | 96 | 92 | -4 | ↓ bad |
| `quant.stage_1_1.raw_text_len_min` | 56 | 41 | -15 | ↓ bad |
| `quant.stage_1_1.raw_text_len_p90` | 182 | 159 | -23 | ↓ bad |
| `quant.stage_1_1.size_suspicious_rate` | 0.02 | 0.08 | +0.06 | ↑ bad |
| `quant.stage_1_1.size_unique` | 4 | 9 | +5 | ↑ good |
| `quant.stage_1_1.style_top1_share` | 0.88 | 0.4 | -0.48 | ↓ good |
| `quant.stage_1_1.style_top1_value` | 캐주얼 | 캐주얼 | — | · |
| `quant.stage_1_1.style_unique` | 5 | 7 | +2 | ↑ good |
| `quant.stage_1_1.title_len_max` | 30 | 30 | +0 | · |
| `quant.stage_1_1.title_len_median` | 24 | 22 | -2 | ↓ bad |
| `quant.stage_1_1.title_len_min` | 14 | 11 | -3 | ↓ bad |
| `quant.stage_1_1.title_len_p90` | 30 | 30 | +0 | · |
| `quant.stage_1_1.title_len_p99` | 30 | 30 | +0 | · |
| `quant.stage_1_1.title_newline_rate` | 0 | 0 | +0 | · |
| `quant.stage_1_1.title_reasoning_leak_rate` | 0 | 0 | +0 | · |
| `quant.stage_1_1_5.dedup_in_count` | 50 | 50 | +0 | · |
| `quant.stage_1_1_5.dedup_out_count` | 50 | 50 | +0 | · |
| `quant.stage_1_1_5.dedup_reduction_rate` | 0 | 0 | +0 | · |
| `quant.stage_1_2.n` | 50 | 50 | +0 | · |
| `quant.stage_1_2.retention_from_stage_1_1_5` | 1 | 1 | +0 | · |
| `stage_1_0.avg_text_quality` | 2.82 | 2.793 | -0.027 | ↓ bad |
| `stage_1_0.failure_modes.duplicate_suspect` | 0 | 0 | +0 | · |
| `stage_1_0.failure_modes.language_issue` | 0 | 0 | +0 | · |
| `stage_1_0.failure_modes.noise_text` | 1 | 1 | +0 | · |
| `stage_1_0.failure_modes.non_fashion_item` | 10 | 9 | -1 | ↓ bad |
| `stage_1_0.failure_modes.non_fashion游戏副本` | 1 | 1 | +0 | · |
| `stage_1_0.failure_modes.pii_leak` | 0 | 0 | +0 | · |
| `stage_1_0.failure_modes.too_short` | 19 | 17 | -2 | ↓ bad |
| `stage_1_0.fashion_rate` | 0.867 | 0.88 | +0.013 | ↑ good |
| `stage_1_0.has_tpo_rate` | 0.267 | 0.3 | +0.033 | ↑ good |
| `stage_1_0.n_evaluated` | 50 | 50 | +0 | · |
| `stage_1_0.pii_rate` | 0.207 | 0.247 | +0.04 | ↑ bad |
| `stage_1_1.attr_grounded_rate` | 0.357 | 0.51 | +0.153 | ↑ good |
| `stage_1_1.avg_persona_reflection` | 3.82 | 3.827 | +0.007 | ↑ good |
| `stage_1_1.avg_raw_text_naturalness` | 4.053 | 4.067 | +0.014 | ↑ good |
| `stage_1_1.failure_modes.attr_mono_value` | 5 | 7 | +2 | ↑ good |
| `stage_1_1.failure_modes.attr_ungrounded` | 33 | 35 | +2 | ↑ good |
| `stage_1_1.failure_modes.language_issue` | 6 | 6 | +0 | · |
| `stage_1_1.failure_modes.length_violation` | 10 | 9 | -1 | ↓ bad |
| `stage_1_1.failure_modes.missing_tpo` | 20 | 16 | -4 | ↓ bad |
| `stage_1_1.failure_modes.non_fashion_item` | 11 | 8 | -3 | ↓ bad |
| `stage_1_1.failure_modes.persona_drift` | 15 | 15 | +0 | · |
| `stage_1_1.failure_modes.rating_sentiment_mismatch` | 14 | 15 | +1 | ↑ good |
| `stage_1_1.failure_modes.title_format_violation` | 40 | 39 | -1 | ↓ bad |
| `stage_1_1.failure_modes.title_length_violation` | 34 | 28 | -6 | ↓ bad |
| `stage_1_1.failure_modes.title_reasoning_leak` | 14 | 5 | -9 | ↓ bad |
| `stage_1_1.fashion_rate` | 0.82 | 0.867 | +0.047 | ↑ good |
| `stage_1_1.has_tpo_rate` | 0.96 | 0.947 | -0.013 | ↓ bad |
| `stage_1_1.n_evaluated` | 50 | 50 | +0 | · |
| `stage_1_1.rating_sentiment_consistent_rate` | 0.74 | 0.713 | -0.027 | ↓ bad |
| `stage_1_1.raw_text_within_spec_rate` | 0.873 | 0.86 | -0.013 | ↓ bad |
| `stage_1_1.title_format_ok_rate` | 0.287 | 0.267 | -0.02 | ↓ bad |
| `stage_1_1.title_reasoning_leak_rate` | 0.16 | 0.067 | -0.093 | ↓ good |
| `stage_1_1.title_within_spec_rate` | 0.38 | 0.473 | +0.093 | ↑ good |
| `stage_1_1_5.dedup_in_count` | 50 | 50 | +0 | · |
| `stage_1_1_5.dedup_miss_count` | 16 | 9 | -7 | ↓ good |
| `stage_1_1_5.dedup_miss_rate` | 0.22 | 0.153 | -0.067 | ↓ good |
| `stage_1_1_5.dedup_out_count` | 50 | 50 | +0 | · |
| `stage_1_1_5.dedup_reduction_rate` | 0 | 0 | +0 | · |
| `stage_1_1_5.failure_modes.low_dedup_reduction` | 1 | 1 | +0 | · |
| `stage_1_1_5.failure_modes.near_duplicate_missed` | 10 | 7 | -3 | ↓ bad |
| `stage_1_1_5.failure_modes.wrong_removal` | 0 | 0 | +0 | · |
| `stage_1_1_5.largest_miss_cluster_size` | 4 | 4 | +0 | · |
| `stage_1_2.avg_text_quality` | 3.707 | 3.9 | +0.193 | ↑ good |
| `stage_1_2.failure_modes.duplicate_suspect` | 0 | 1 | +1 | ↑ good |
| `stage_1_2.failure_modes.language_issue` | 1 | 1 | +0 | · |
| `stage_1_2.failure_modes.noise_text` | 1 | 1 | +0 | · |
| `stage_1_2.failure_modes.non_fashion_item` | 9 | 5 | -4 | ↓ bad |
| `stage_1_2.failure_modes.non_fashion游戏副本` | 1 | 1 | +0 | · |
| `stage_1_2.failure_modes.pii_leak` | 3 | 2 | -1 | ↓ bad |
| `stage_1_2.failure_modes.too_short` | 4 | 4 | +0 | · |
| `stage_1_2.fashion_rate` | 0.893 | 0.947 | +0.054 | ↑ good |
| `stage_1_2.has_tpo_rate` | 0.687 | 0.7 | +0.013 | ↑ good |
| `stage_1_2.n_evaluated` | 50 | 50 | +0 | · |
| `stage_1_2.pii_rate` | 0.173 | 0.18 | +0.007 | ↑ bad |

## Output hashes

| file | sha256 |
|---|---|
| `stage_1_0_seed.jsonl` | `sha256:42dbc866bdb796968ee245e4fca0d480683ae7889fc81b44787e23c507f4c738` |
| `stage_1_1_synthetic.jsonl` | `sha256:5daec15873ccdc09fd6ce31f61653b31310f082accedfb86e05dba1489992f76` |
| `stage_1_1_5_deduped.jsonl` | `sha256:5daec15873ccdc09fd6ce31f61653b31310f082accedfb86e05dba1489992f76` |
| `stage_1_2_processed.jsonl` | `sha256:5daec15873ccdc09fd6ce31f61653b31310f082accedfb86e05dba1489992f76` |