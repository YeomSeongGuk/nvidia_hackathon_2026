# Comparison: iter_16_tighter_leak_regex vs iter_13_combo_plus_attr_mention

- this   iter: `iter_16_tighter_leak_regex`
- parent iter: `iter_13_combo_plus_attr_mention`
- this timestamp : 2026-04-21T21:12:37+00:00
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
| `quant.stage_1_1.color_top2_share` | 0.5 | 0.44 | -0.06 | ↓ good |
| `quant.stage_1_1.color_unique` | 8 | 9 | +1 | ↑ good |
| `quant.stage_1_1.color_white_black_share` | 0.38 | 0.42 | +0.04 | ↑ bad |
| `quant.stage_1_1.n` | 50 | 50 | +0 | · |
| `quant.stage_1_1.rating_3_share` | 0.3 | 0.26 | -0.04 | ↓ bad |
| `quant.stage_1_1.rating_hist.1` | 6 | 9 | +3 | ↑ good |
| `quant.stage_1_1.rating_hist.2` | 9 | 10 | +1 | ↑ good |
| `quant.stage_1_1.rating_hist.3` | 15 | 13 | -2 | ↓ bad |
| `quant.stage_1_1.rating_hist.4` | 9 | 10 | +1 | ↑ good |
| `quant.stage_1_1.rating_hist.5` | 11 | 8 | -3 | ↓ bad |
| `quant.stage_1_1.raw_text_len_max` | 255 | 256 | +1 | ↑ good |
| `quant.stage_1_1.raw_text_len_median` | 161 | 156 | -5 | ↓ bad |
| `quant.stage_1_1.raw_text_len_min` | 70 | 92 | +22 | ↑ good |
| `quant.stage_1_1.raw_text_len_p90` | 228 | 214 | -14 | ↓ bad |
| `quant.stage_1_1.size_suspicious_rate` | 0.1 | 0.08 | -0.02 | ↓ good |
| `quant.stage_1_1.size_unique` | 8 | 10 | +2 | ↑ good |
| `quant.stage_1_1.style_top1_share` | 0.54 | 0.54 | +0 | · |
| `quant.stage_1_1.style_top1_value` | 캐주얼 | 캐주얼 | — | · |
| `quant.stage_1_1.style_unique` | 8 | 7 | -1 | ↓ bad |
| `quant.stage_1_1.title_len_max` | 30 | 30 | +0 | · |
| `quant.stage_1_1.title_len_median` | 23 | 23 | +0 | · |
| `quant.stage_1_1.title_len_min` | 12 | 13 | +1 | ↑ good |
| `quant.stage_1_1.title_len_p90` | 30 | 30 | +0 | · |
| `quant.stage_1_1.title_len_p99` | 30 | 30 | +0 | · |
| `quant.stage_1_1.title_newline_rate` | 0 | 0 | +0 | · |
| `quant.stage_1_1.title_reasoning_leak_rate` | 0 | 0 | +0 | · |
| `quant.stage_1_1_5.dedup_in_count` | 50 | 50 | +0 | · |
| `quant.stage_1_1_5.dedup_out_count` | 50 | 50 | +0 | · |
| `quant.stage_1_1_5.dedup_reduction_rate` | 0 | 0 | +0 | · |
| `quant.stage_1_2.n` | 50 | 50 | +0 | · |
| `quant.stage_1_2.retention_from_stage_1_1_5` | 1 | 1 | +0 | · |
| `stage_1_0.avg_text_quality` | 2.787 | 2.807 | +0.02 | ↑ good |
| `stage_1_0.failure_modes.duplicate_suspect` | 0 | 0 | +0 | · |
| `stage_1_0.failure_modes.language_issue` | 0 | 0 | +0 | · |
| `stage_1_0.failure_modes.noise_text` | 1 | 1 | +0 | · |
| `stage_1_0.failure_modes.non_fashion_item` | 9 | 8 | -1 | ↓ bad |
| `stage_1_0.failure_modes.non_fashion游戏副本` | 1 | 3 | +2 | ↑ good |
| `stage_1_0.failure_modes.pii_leak` | 0 | 0 | +0 | · |
| `stage_1_0.failure_modes.too_short` | 23 | 17 | -6 | ↓ bad |
| `stage_1_0.fashion_rate` | 0.873 | 0.88 | +0.007 | ↑ good |
| `stage_1_0.has_tpo_rate` | 0.26 | 0.293 | +0.033 | ↑ good |
| `stage_1_0.n_evaluated` | 50 | 50 | +0 | · |
| `stage_1_0.pii_rate` | 0.227 | 0.247 | +0.02 | ↑ bad |
| `stage_1_1.attr_grounded_rate` | 0.99 | 0.983 | -0.007 | ↓ bad |
| `stage_1_1.avg_persona_reflection` | 4.553 | 4.493 | -0.06 | ↓ bad |
| `stage_1_1.avg_raw_text_naturalness` | 3.913 | 3.873 | -0.04 | ↓ bad |
| `stage_1_1.failure_modes.attr_mono_value` | 2 | 3 | +1 | ↑ good |
| `stage_1_1.failure_modes.attr_ungrounded` | 4 | 7 | +3 | ↑ good |
| `stage_1_1.failure_modes.language_issue` | 13 | 15 | +2 | ↑ good |
| `stage_1_1.failure_modes.length_violation` | 1 | 0 | -1 | ↓ bad |
| `stage_1_1.failure_modes.missing_tpo` | 12 | 8 | -4 | ↓ bad |
| `stage_1_1.failure_modes.non_fashion_item` | 8 | 8 | +0 | · |
| `stage_1_1.failure_modes.persona_drift` | 16 | 14 | -2 | ↓ bad |
| `stage_1_1.failure_modes.rating_sentiment_mismatch` | 2 | 3 | +1 | ↑ good |
| `stage_1_1.failure_modes.title_format_violation` | 40 | 36 | -4 | ↓ bad |
| `stage_1_1.failure_modes.title_length_violation` | 34 | 30 | -4 | ↓ bad |
| `stage_1_1.failure_modes.title_reasoning_leak` | 3 | 3 | +0 | · |
| `stage_1_1.fashion_rate` | 0.873 | 0.867 | -0.006 | ↓ bad |
| `stage_1_1.has_tpo_rate` | 0.94 | 0.967 | +0.027 | ↑ good |
| `stage_1_1.n_evaluated` | 50 | 50 | +0 | · |
| `stage_1_1.rating_sentiment_consistent_rate` | 0.973 | 0.98 | +0.007 | ↑ good |
| `stage_1_1.raw_text_within_spec_rate` | 0.993 | 0.993 | +0 | · |
| `stage_1_1.title_format_ok_rate` | 0.293 | 0.38 | +0.087 | ↑ good |
| `stage_1_1.title_reasoning_leak_rate` | 0.053 | 0.04 | -0.013 | ↓ good |
| `stage_1_1.title_within_spec_rate` | 0.433 | 0.48 | +0.047 | ↑ good |
| `stage_1_1_5.dedup_in_count` | 50 | 50 | +0 | · |
| `stage_1_1_5.dedup_miss_count` | 10 | 9 | -1 | ↓ good |
| `stage_1_1_5.dedup_miss_rate` | 0.14 | 0.147 | +0.007 | ↑ bad |
| `stage_1_1_5.dedup_out_count` | 50 | 50 | +0 | · |
| `stage_1_1_5.dedup_reduction_rate` | 0 | 0 | +0 | · |
| `stage_1_1_5.failure_modes.low_dedup_reduction` | 1 | 1 | +0 | · |
| `stage_1_1_5.failure_modes.near_duplicate_missed` | 10 | 8 | -2 | ↓ bad |
| `stage_1_1_5.failure_modes.wrong_removal` | 0 | 0 | +0 | · |
| `stage_1_1_5.largest_miss_cluster_size` | 2 | 3 | +1 | ↑ bad |
| `stage_1_2.avg_text_quality` | 3.867 | 3.88 | +0.013 | ↑ good |
| `stage_1_2.failure_modes.duplicate_suspect` | 0 | 0 | +0 | · |
| `stage_1_2.failure_modes.language_issue` | 3 | 3 | +0 | · |
| `stage_1_2.failure_modes.noise_text` | 0 | 0 | +0 | · |
| `stage_1_2.failure_modes.non_fashion_item` | 7 | 6 | -1 | ↓ bad |
| `stage_1_2.failure_modes.non_fashion游戏副本` | 1 | 2 | +1 | ↑ good |
| `stage_1_2.failure_modes.pii_leak` | 28 | 23 | -5 | ↓ bad |
| `stage_1_2.failure_modes.too_short` | 0 | 1 | +1 | ↑ good |
| `stage_1_2.fashion_rate` | 0.907 | 0.927 | +0.02 | ↑ good |
| `stage_1_2.has_tpo_rate` | 0.687 | 0.667 | -0.02 | ↓ bad |
| `stage_1_2.n_evaluated` | 50 | 50 | +0 | · |
| `stage_1_2.pii_rate` | 0.513 | 0.507 | -0.006 | ↓ good |

## Output hashes

| file | sha256 |
|---|---|
| `stage_1_0_seed.jsonl` | `sha256:42dbc866bdb796968ee245e4fca0d480683ae7889fc81b44787e23c507f4c738` |
| `stage_1_1_synthetic.jsonl` | `sha256:f600d6f01c931d64653262b1960bb40157623741b52acf1baf92f7c972b9cbc4` |
| `stage_1_1_5_deduped.jsonl` | `sha256:f600d6f01c931d64653262b1960bb40157623741b52acf1baf92f7c972b9cbc4` |
| `stage_1_2_processed.jsonl` | `sha256:f600d6f01c931d64653262b1960bb40157623741b52acf1baf92f7c972b9cbc4` |