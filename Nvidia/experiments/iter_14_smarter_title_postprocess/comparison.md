# Comparison: iter_14_smarter_title_postprocess vs iter_13_combo_plus_attr_mention

- this   iter: `iter_14_smarter_title_postprocess`
- parent iter: `iter_13_combo_plus_attr_mention`
- this timestamp : 2026-04-21T20:41:45+00:00
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
| `quant.stage_1_1.color_top2_share` | 0.5 | 0.56 | +0.06 | ↑ bad |
| `quant.stage_1_1.color_unique` | 8 | 8 | +0 | · |
| `quant.stage_1_1.color_white_black_share` | 0.38 | 0.52 | +0.14 | ↑ bad |
| `quant.stage_1_1.n` | 50 | 50 | +0 | · |
| `quant.stage_1_1.rating_3_share` | 0.3 | 0.26 | -0.04 | ↓ bad |
| `quant.stage_1_1.rating_hist.1` | 6 | 6 | +0 | · |
| `quant.stage_1_1.rating_hist.2` | 9 | 9 | +0 | · |
| `quant.stage_1_1.rating_hist.3` | 15 | 13 | -2 | ↓ bad |
| `quant.stage_1_1.rating_hist.4` | 9 | 9 | +0 | · |
| `quant.stage_1_1.rating_hist.5` | 11 | 13 | +2 | ↑ good |
| `quant.stage_1_1.raw_text_len_max` | 255 | 370 | +115 | ↑ good |
| `quant.stage_1_1.raw_text_len_median` | 161 | 165 | +4 | ↑ good |
| `quant.stage_1_1.raw_text_len_min` | 70 | 103 | +33 | ↑ good |
| `quant.stage_1_1.raw_text_len_p90` | 228 | 230 | +2 | ↑ good |
| `quant.stage_1_1.size_suspicious_rate` | 0.1 | 0.1 | +0 | · |
| `quant.stage_1_1.size_unique` | 8 | 8 | +0 | · |
| `quant.stage_1_1.style_top1_share` | 0.54 | 0.5 | -0.04 | ↓ good |
| `quant.stage_1_1.style_top1_value` | 캐주얼 | 캐주얼 | — | · |
| `quant.stage_1_1.style_unique` | 8 | 7 | -1 | ↓ bad |
| `quant.stage_1_1.title_len_max` | 30 | 45 | +15 | ↑ bad |
| `quant.stage_1_1.title_len_median` | 23 | 22 | -1 | ↓ bad |
| `quant.stage_1_1.title_len_min` | 12 | 5 | -7 | ↓ bad |
| `quant.stage_1_1.title_len_p90` | 30 | 32 | +2 | ↑ bad |
| `quant.stage_1_1.title_len_p99` | 30 | 40 | +10 | ↑ bad |
| `quant.stage_1_1.title_newline_rate` | 0 | 0 | +0 | · |
| `quant.stage_1_1.title_reasoning_leak_rate` | 0 | 0 | +0 | · |
| `quant.stage_1_1_5.dedup_in_count` | 50 | 50 | +0 | · |
| `quant.stage_1_1_5.dedup_out_count` | 50 | 50 | +0 | · |
| `quant.stage_1_1_5.dedup_reduction_rate` | 0 | 0 | +0 | · |
| `quant.stage_1_2.n` | 50 | 50 | +0 | · |
| `quant.stage_1_2.retention_from_stage_1_1_5` | 1 | 1 | +0 | · |
| `stage_1_0.avg_text_quality` | 2.787 | 2.787 | +0 | · |
| `stage_1_0.failure_modes.duplicate_suspect` | 0 | 0 | +0 | · |
| `stage_1_0.failure_modes.language_issue` | 0 | 0 | +0 | · |
| `stage_1_0.failure_modes.noise_text` | 1 | 1 | +0 | · |
| `stage_1_0.failure_modes.non_fashion_item` | 9 | 7 | -2 | ↓ bad |
| `stage_1_0.failure_modes.non_fashion游戏副本` | 1 | 1 | +0 | · |
| `stage_1_0.failure_modes.pii_leak` | 0 | 0 | +0 | · |
| `stage_1_0.failure_modes.too_short` | 23 | 20 | -3 | ↓ bad |
| `stage_1_0.fashion_rate` | 0.873 | 0.907 | +0.034 | ↑ good |
| `stage_1_0.has_tpo_rate` | 0.26 | 0.267 | +0.007 | ↑ good |
| `stage_1_0.n_evaluated` | 50 | 50 | +0 | · |
| `stage_1_0.pii_rate` | 0.227 | 0.213 | -0.014 | ↓ good |
| `stage_1_1.attr_grounded_rate` | 0.99 | 0.99 | +0 | · |
| `stage_1_1.avg_persona_reflection` | 4.553 | 4.46 | -0.093 | ↓ bad |
| `stage_1_1.avg_raw_text_naturalness` | 3.913 | 3.84 | -0.073 | ↓ bad |
| `stage_1_1.failure_modes.attr_mono_value` | 2 | 6 | +4 | ↑ good |
| `stage_1_1.failure_modes.attr_ungrounded` | 4 | 7 | +3 | ↑ good |
| `stage_1_1.failure_modes.language_issue` | 13 | 22 | +9 | ↑ good |
| `stage_1_1.failure_modes.length_violation` | 1 | 2 | +1 | ↑ good |
| `stage_1_1.failure_modes.missing_tpo` | 12 | 7 | -5 | ↓ bad |
| `stage_1_1.failure_modes.non_fashion_item` | 8 | 10 | +2 | ↑ good |
| `stage_1_1.failure_modes.persona_drift` | 16 | 16 | +0 | · |
| `stage_1_1.failure_modes.rating_sentiment_mismatch` | 2 | 4 | +2 | ↑ good |
| `stage_1_1.failure_modes.raw_text_naturalness` | — | 1 | — | · |
| `stage_1_1.failure_modes.title_format_violation` | 40 | 38 | -2 | ↓ bad |
| `stage_1_1.failure_modes.title_length_violation` | 34 | 32 | -2 | ↓ bad |
| `stage_1_1.failure_modes.title_reasoning_leak` | 3 | 6 | +3 | ↑ good |
| `stage_1_1.fashion_rate` | 0.873 | 0.847 | -0.026 | ↓ bad |
| `stage_1_1.has_tpo_rate` | 0.94 | 0.967 | +0.027 | ↑ good |
| `stage_1_1.n_evaluated` | 50 | 50 | +0 | · |
| `stage_1_1.rating_sentiment_consistent_rate` | 0.973 | 0.953 | -0.02 | ↓ bad |
| `stage_1_1.raw_text_within_spec_rate` | 0.993 | 0.987 | -0.006 | ↓ bad |
| `stage_1_1.title_format_ok_rate` | 0.293 | 0.307 | +0.014 | ↑ good |
| `stage_1_1.title_reasoning_leak_rate` | 0.053 | 0.093 | +0.04 | ↑ bad |
| `stage_1_1.title_within_spec_rate` | 0.433 | 0.4 | -0.033 | ↓ bad |
| `stage_1_1_5.dedup_in_count` | 50 | 50 | +0 | · |
| `stage_1_1_5.dedup_miss_count` | 10 | 9 | -1 | ↓ good |
| `stage_1_1_5.dedup_miss_rate` | 0.14 | 0.14 | +0 | · |
| `stage_1_1_5.dedup_out_count` | 50 | 50 | +0 | · |
| `stage_1_1_5.dedup_reduction_rate` | 0 | 0 | +0 | · |
| `stage_1_1_5.failure_modes.low_dedup_reduction` | 1 | 1 | +0 | · |
| `stage_1_1_5.failure_modes.near_duplicate_missed` | 10 | 8 | -2 | ↓ bad |
| `stage_1_1_5.failure_modes.wrong_removal` | 0 | 0 | +0 | · |
| `stage_1_1_5.largest_miss_cluster_size` | 2 | 3 | +1 | ↑ bad |
| `stage_1_2.avg_text_quality` | 3.867 | 3.82 | -0.047 | ↓ bad |
| `stage_1_2.failure_modes.duplicate_suspect` | 0 | 0 | +0 | · |
| `stage_1_2.failure_modes.language_issue` | 3 | 1 | -2 | ↓ bad |
| `stage_1_2.failure_modes.noise_text` | 0 | 0 | +0 | · |
| `stage_1_2.failure_modes.non_fashion_item` | 7 | 5 | -2 | ↓ bad |
| `stage_1_2.failure_modes.non_fashion游戏副本` | 1 | 1 | +0 | · |
| `stage_1_2.failure_modes.pii_leak` | 28 | 27 | -1 | ↓ bad |
| `stage_1_2.failure_modes.too_short` | 0 | 1 | +1 | ↑ good |
| `stage_1_2.fashion_rate` | 0.907 | 0.927 | +0.02 | ↑ good |
| `stage_1_2.has_tpo_rate` | 0.687 | 0.72 | +0.033 | ↑ good |
| `stage_1_2.n_evaluated` | 50 | 50 | +0 | · |
| `stage_1_2.pii_rate` | 0.513 | 0.527 | +0.014 | ↑ bad |

## Output hashes

| file | sha256 |
|---|---|
| `stage_1_0_seed.jsonl` | `sha256:42dbc866bdb796968ee245e4fca0d480683ae7889fc81b44787e23c507f4c738` |
| `stage_1_1_synthetic.jsonl` | `sha256:7fac91c3ec4fecbf063794c7b8fe510700a8b263b2237d91ab95571c2fa5434e` |
| `stage_1_1_5_deduped.jsonl` | `sha256:7fac91c3ec4fecbf063794c7b8fe510700a8b263b2237d91ab95571c2fa5434e` |
| `stage_1_2_processed.jsonl` | `sha256:7fac91c3ec4fecbf063794c7b8fe510700a8b263b2237d91ab95571c2fa5434e` |