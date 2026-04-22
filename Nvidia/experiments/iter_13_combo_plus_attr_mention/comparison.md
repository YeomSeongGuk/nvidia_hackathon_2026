# Comparison: iter_13_combo_plus_attr_mention vs iter_12_combo_all_plus_rating_sampler

- this   iter: `iter_13_combo_plus_attr_mention`
- parent iter: `iter_12_combo_all_plus_rating_sampler`
- this timestamp : 2026-04-21T20:26:31+00:00
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
| `quant.stage_1_1.color_top2_share` | 0.58 | 0.5 | -0.08 | ↓ good |
| `quant.stage_1_1.color_unique` | 6 | 8 | +2 | ↑ good |
| `quant.stage_1_1.color_white_black_share` | 0.56 | 0.38 | -0.18 | ↓ good |
| `quant.stage_1_1.n` | 50 | 50 | +0 | · |
| `quant.stage_1_1.rating_3_share` | 0.3 | 0.3 | +0 | · |
| `quant.stage_1_1.rating_hist.1` | 12 | 6 | -6 | ↓ bad |
| `quant.stage_1_1.rating_hist.2` | 11 | 9 | -2 | ↓ bad |
| `quant.stage_1_1.rating_hist.3` | 15 | 15 | +0 | · |
| `quant.stage_1_1.rating_hist.4` | 7 | 9 | +2 | ↑ good |
| `quant.stage_1_1.rating_hist.5` | 5 | 11 | +6 | ↑ good |
| `quant.stage_1_1.raw_text_len_max` | 399 | 255 | -144 | ↓ bad |
| `quant.stage_1_1.raw_text_len_median` | 144 | 161 | +17 | ↑ good |
| `quant.stage_1_1.raw_text_len_min` | 91 | 70 | -21 | ↓ bad |
| `quant.stage_1_1.raw_text_len_p90` | 201 | 228 | +27 | ↑ good |
| `quant.stage_1_1.size_suspicious_rate` | 0.1 | 0.1 | +0 | · |
| `quant.stage_1_1.size_unique` | 11 | 8 | -3 | ↓ bad |
| `quant.stage_1_1.style_top1_share` | 0.5 | 0.54 | +0.04 | ↑ bad |
| `quant.stage_1_1.style_top1_value` | 캐주얼 | 캐주얼 | — | · |
| `quant.stage_1_1.style_unique` | 7 | 8 | +1 | ↑ good |
| `quant.stage_1_1.title_len_max` | 30 | 30 | +0 | · |
| `quant.stage_1_1.title_len_median` | 23 | 23 | +0 | · |
| `quant.stage_1_1.title_len_min` | 6 | 12 | +6 | ↑ good |
| `quant.stage_1_1.title_len_p90` | 30 | 30 | +0 | · |
| `quant.stage_1_1.title_len_p99` | 30 | 30 | +0 | · |
| `quant.stage_1_1.title_newline_rate` | 0 | 0 | +0 | · |
| `quant.stage_1_1.title_reasoning_leak_rate` | 0 | 0 | +0 | · |
| `quant.stage_1_1_5.dedup_in_count` | 50 | 50 | +0 | · |
| `quant.stage_1_1_5.dedup_out_count` | 50 | 50 | +0 | · |
| `quant.stage_1_1_5.dedup_reduction_rate` | 0 | 0 | +0 | · |
| `quant.stage_1_2.n` | 50 | 50 | +0 | · |
| `quant.stage_1_2.retention_from_stage_1_1_5` | 1 | 1 | +0 | · |
| `stage_1_0.avg_text_quality` | 2.793 | 2.787 | -0.006 | ↓ bad |
| `stage_1_0.failure_modes.duplicate_suspect` | 0 | 0 | +0 | · |
| `stage_1_0.failure_modes.language_issue` | 0 | 0 | +0 | · |
| `stage_1_0.failure_modes.noise_text` | 1 | 1 | +0 | · |
| `stage_1_0.failure_modes.non_fashion_item` | 8 | 9 | +1 | ↑ good |
| `stage_1_0.failure_modes.non_fashion游戏副本` | 1 | 1 | +0 | · |
| `stage_1_0.failure_modes.pii_leak` | 0 | 0 | +0 | · |
| `stage_1_0.failure_modes.too_short` | 19 | 23 | +4 | ↑ good |
| `stage_1_0.fashion_rate` | 0.893 | 0.873 | -0.02 | ↓ bad |
| `stage_1_0.has_tpo_rate` | 0.333 | 0.26 | -0.073 | ↓ bad |
| `stage_1_0.n_evaluated` | 50 | 50 | +0 | · |
| `stage_1_0.pii_rate` | 0.253 | 0.227 | -0.026 | ↓ good |
| `stage_1_1.attr_grounded_rate` | 0.467 | 0.99 | +0.523 | ↑ good |
| `stage_1_1.avg_persona_reflection` | 4.693 | 4.553 | -0.14 | ↓ bad |
| `stage_1_1.avg_raw_text_naturalness` | 3.96 | 3.913 | -0.047 | ↓ bad |
| `stage_1_1.failure_modes.attr_mono_value` | 6 | 2 | -4 | ↓ bad |
| `stage_1_1.failure_modes.attr_ungrounded` | 33 | 4 | -29 | ↓ bad |
| `stage_1_1.failure_modes.language_issue` | 11 | 13 | +2 | ↑ good |
| `stage_1_1.failure_modes.length_violation` | 1 | 1 | +0 | · |
| `stage_1_1.failure_modes.missing_tpo` | 13 | 12 | -1 | ↓ bad |
| `stage_1_1.failure_modes.non_fashion_item` | 6 | 8 | +2 | ↑ good |
| `stage_1_1.failure_modes.persona_drift` | 6 | 16 | +10 | ↑ good |
| `stage_1_1.failure_modes.rating_sentiment_mismatch` | 2 | 2 | +0 | · |
| `stage_1_1.failure_modes.title_format_violation` | 39 | 40 | +1 | ↑ good |
| `stage_1_1.failure_modes.title_length_violation` | 30 | 34 | +4 | ↑ good |
| `stage_1_1.failure_modes.title_reasoning_leak` | 8 | 3 | -5 | ↓ bad |
| `stage_1_1.fashion_rate` | 0.9 | 0.873 | -0.027 | ↓ bad |
| `stage_1_1.has_tpo_rate` | 0.973 | 0.94 | -0.033 | ↓ bad |
| `stage_1_1.n_evaluated` | 50 | 50 | +0 | · |
| `stage_1_1.rating_sentiment_consistent_rate` | 0.973 | 0.973 | +0 | · |
| `stage_1_1.raw_text_within_spec_rate` | 0.993 | 0.993 | +0 | · |
| `stage_1_1.title_format_ok_rate` | 0.32 | 0.293 | -0.027 | ↓ bad |
| `stage_1_1.title_reasoning_leak_rate` | 0.127 | 0.053 | -0.074 | ↓ good |
| `stage_1_1.title_within_spec_rate` | 0.447 | 0.433 | -0.014 | ↓ bad |
| `stage_1_1_5.dedup_in_count` | 50 | 50 | +0 | · |
| `stage_1_1_5.dedup_miss_count` | 5 | 10 | +5 | ↑ bad |
| `stage_1_1_5.dedup_miss_rate` | 0.113 | 0.14 | +0.027 | ↑ bad |
| `stage_1_1_5.dedup_out_count` | 50 | 50 | +0 | · |
| `stage_1_1_5.dedup_reduction_rate` | 0 | 0 | +0 | · |
| `stage_1_1_5.failure_modes.low_dedup_reduction` | 1 | 1 | +0 | · |
| `stage_1_1_5.failure_modes.near_duplicate_missed` | 10 | 10 | +0 | · |
| `stage_1_1_5.failure_modes.wrong_removal` | 0 | 0 | +0 | · |
| `stage_1_1_5.largest_miss_cluster_size` | 2 | 2 | +0 | · |
| `stage_1_2.avg_text_quality` | 3.74 | 3.867 | +0.127 | ↑ good |
| `stage_1_2.failure_modes.duplicate_suspect` | 0 | 0 | +0 | · |
| `stage_1_2.failure_modes.language_issue` | 1 | 3 | +2 | ↑ good |
| `stage_1_2.failure_modes.noise_text` | 0 | 0 | +0 | · |
| `stage_1_2.failure_modes.non_fashion_item` | 4 | 7 | +3 | ↑ good |
| `stage_1_2.failure_modes.non_fashion游戏副本` | 3 | 1 | -2 | ↓ bad |
| `stage_1_2.failure_modes.pii_leak` | 18 | 28 | +10 | ↑ good |
| `stage_1_2.failure_modes.too_short` | 2 | 0 | -2 | ↓ bad |
| `stage_1_2.fashion_rate` | 0.92 | 0.907 | -0.013 | ↓ bad |
| `stage_1_2.has_tpo_rate` | 0.673 | 0.687 | +0.014 | ↑ good |
| `stage_1_2.n_evaluated` | 50 | 50 | +0 | · |
| `stage_1_2.pii_rate` | 0.44 | 0.513 | +0.073 | ↑ bad |

## Output hashes

| file | sha256 |
|---|---|
| `stage_1_0_seed.jsonl` | `sha256:42dbc866bdb796968ee245e4fca0d480683ae7889fc81b44787e23c507f4c738` |
| `stage_1_1_synthetic.jsonl` | `sha256:ccdc1d5c42dfb84ab27dbddf6a9a0d18131871aac3e047662664bb898df5febb` |
| `stage_1_1_5_deduped.jsonl` | `sha256:ccdc1d5c42dfb84ab27dbddf6a9a0d18131871aac3e047662664bb898df5febb` |
| `stage_1_2_processed.jsonl` | `sha256:ccdc1d5c42dfb84ab27dbddf6a9a0d18131871aac3e047662664bb898df5febb` |