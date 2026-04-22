# Comparison: iter_09_combo_h3_h9 vs iter_03_title_postprocess

- this   iter: `iter_09_combo_h3_h9`
- parent iter: `iter_03_title_postprocess`
- this timestamp : 2026-04-21T19:18:43+00:00
- promote flag   : False  high_variance: True

## Metric diff

| metric | parent | this | Δ | direction |
|---|---|---|---|---|
| `e2e.e2e_retention` | 0.02 | 1 | +0.98 | ↑ good |
| `e2e.input_rows_seed` | 50 | 50 | +0 | · |
| `e2e.output_rows_by_stage` | <list len=4> | <list len=4> | — | · |
| `quant.e2e.e2e_retention` | 0.02 | 1 | +0.98 | ↑ good |
| `quant.e2e.input_rows_seed` | 50 | 50 | +0 | · |
| `quant.e2e.output_rows_by_stage` | <list len=4> | <list len=4> | — | · |
| `quant.stage_1_0.n` | 50 | 50 | +0 | · |
| `quant.stage_1_0.rating_3_share` | 0 | 0 | +0 | · |
| `quant.stage_1_0.rating_hist.1` | 10 | 10 | +0 | · |
| `quant.stage_1_0.rating_hist.2` | 16 | 16 | +0 | · |
| `quant.stage_1_0.rating_hist.4` | 3 | 3 | +0 | · |
| `quant.stage_1_0.rating_hist.5` | 21 | 21 | +0 | · |
| `quant.stage_1_1.color_top2_share` | 0.633 | 0.7 | +0.067 | ↑ bad |
| `quant.stage_1_1.color_unique` | 7 | 8 | +1 | ↑ good |
| `quant.stage_1_1.color_white_black_share` | 0.633 | 0.7 | +0.067 | ↑ bad |
| `quant.stage_1_1.n` | 49 | 50 | +1 | ↑ good |
| `quant.stage_1_1.rating_3_share` | 0 | 0 | +0 | · |
| `quant.stage_1_1.rating_hist.1` | 12 | 12 | +0 | · |
| `quant.stage_1_1.rating_hist.2` | 17 | 17 | +0 | · |
| `quant.stage_1_1.rating_hist.4` | 3 | 3 | +0 | · |
| `quant.stage_1_1.rating_hist.5` | 17 | 18 | +1 | ↑ good |
| `quant.stage_1_1.raw_text_len_max` | 262 | 209 | -53 | ↓ bad |
| `quant.stage_1_1.raw_text_len_median` | 92 | 96 | +4 | ↑ good |
| `quant.stage_1_1.raw_text_len_min` | 52 | 56 | +4 | ↑ good |
| `quant.stage_1_1.raw_text_len_p90` | 191 | 182 | -9 | ↓ bad |
| `quant.stage_1_1.size_suspicious_rate` | 0.02 | 0.02 | +0 | · |
| `quant.stage_1_1.size_unique` | 5 | 4 | -1 | ↓ bad |
| `quant.stage_1_1.style_top1_share` | 0.898 | 0.88 | -0.018 | ↓ good |
| `quant.stage_1_1.style_top1_value` | 캐주얼 | 캐주얼 | — | · |
| `quant.stage_1_1.style_unique` | 3 | 5 | +2 | ↑ good |
| `quant.stage_1_1.title_len_max` | 30 | 30 | +0 | · |
| `quant.stage_1_1.title_len_median` | 24 | 24 | +0 | · |
| `quant.stage_1_1.title_len_min` | 10 | 14 | +4 | ↑ good |
| `quant.stage_1_1.title_len_p90` | 30 | 30 | +0 | · |
| `quant.stage_1_1.title_len_p99` | 30 | 30 | +0 | · |
| `quant.stage_1_1.title_newline_rate` | 0 | 0 | +0 | · |
| `quant.stage_1_1.title_reasoning_leak_rate` | 0 | 0 | +0 | · |
| `quant.stage_1_1_5.dedup_in_count` | 49 | 50 | +1 | ↑ good |
| `quant.stage_1_1_5.dedup_out_count` | 49 | 50 | +1 | ↑ good |
| `quant.stage_1_1_5.dedup_reduction_rate` | 0 | 0 | +0 | · |
| `quant.stage_1_2.n` | 1 | 50 | +49 | ↑ good |
| `quant.stage_1_2.retention_from_stage_1_1_5` | 0.02 | 1 | +0.98 | ↑ good |
| `stage_1_0.avg_text_quality` | — | 2.82 | — | · |
| `stage_1_0.failure_modes.duplicate_suspect` | — | 0 | — | · |
| `stage_1_0.failure_modes.language_issue` | — | 0 | — | · |
| `stage_1_0.failure_modes.noise_text` | — | 1 | — | · |
| `stage_1_0.failure_modes.non_fashion_item` | — | 10 | — | · |
| `stage_1_0.failure_modes.non_fashion游戏副本` | — | 1 | — | · |
| `stage_1_0.failure_modes.pii_leak` | — | 0 | — | · |
| `stage_1_0.failure_modes.too_short` | — | 19 | — | · |
| `stage_1_0.fashion_rate` | — | 0.867 | — | · |
| `stage_1_0.has_tpo_rate` | — | 0.267 | — | · |
| `stage_1_0.n_evaluated` | — | 50 | — | · |
| `stage_1_0.pii_rate` | — | 0.207 | — | · |
| `stage_1_1.attr_grounded_rate` | 0.473 | 0.357 | -0.116 | ↓ bad |
| `stage_1_1.avg_persona_reflection` | 3.967 | 3.82 | -0.147 | ↓ bad |
| `stage_1_1.avg_raw_text_naturalness` | 4.137 | 4.053 | -0.084 | ↓ bad |
| `stage_1_1.failure_modes.attr_mono_value` | 5 | 5 | +0 | · |
| `stage_1_1.failure_modes.attr_ungrounded` | 31 | 33 | +2 | ↑ good |
| `stage_1_1.failure_modes.language_issue` | 7 | 6 | -1 | ↓ bad |
| `stage_1_1.failure_modes.length_violation` | 8 | 10 | +2 | ↑ good |
| `stage_1_1.failure_modes.missing_tpo` | 11 | 20 | +9 | ↑ good |
| `stage_1_1.failure_modes.non_fashion_item` | 9 | 11 | +2 | ↑ good |
| `stage_1_1.failure_modes.persona_drift` | 14 | 15 | +1 | ↑ good |
| `stage_1_1.failure_modes.rating_sentiment_mismatch` | 17 | 14 | -3 | ↓ bad |
| `stage_1_1.failure_modes.title_format_violation` | 36 | 40 | +4 | ↑ good |
| `stage_1_1.failure_modes.title_length_violation` | 30 | 34 | +4 | ↑ good |
| `stage_1_1.failure_modes.title_reasoning_leak` | 8 | 14 | +6 | ↑ good |
| `stage_1_1.fashion_rate` | 0.86 | 0.82 | -0.04 | ↓ bad |
| `stage_1_1.has_tpo_rate` | 0.967 | 0.96 | -0.007 | ↓ bad |
| `stage_1_1.n_evaluated` | 49 | 50 | +1 | ↑ good |
| `stage_1_1.rating_sentiment_consistent_rate` | 0.663 | 0.74 | +0.077 | ↑ good |
| `stage_1_1.raw_text_within_spec_rate` | 0.9 | 0.873 | -0.027 | ↓ bad |
| `stage_1_1.title_format_ok_rate` | 0.35 | 0.287 | -0.063 | ↓ bad |
| `stage_1_1.title_reasoning_leak_rate` | 0.06 | 0.16 | +0.1 | ↑ bad |
| `stage_1_1.title_within_spec_rate` | 0.44 | 0.38 | -0.06 | ↓ bad |
| `stage_1_1_5.dedup_in_count` | 49 | 50 | +1 | ↑ good |
| `stage_1_1_5.dedup_miss_count` | 7 | 16 | +9 | ↑ bad |
| `stage_1_1_5.dedup_miss_rate` | 0.109 | 0.22 | +0.111 | ↑ bad |
| `stage_1_1_5.dedup_out_count` | 49 | 50 | +1 | ↑ good |
| `stage_1_1_5.dedup_reduction_rate` | 0 | 0 | +0 | · |
| `stage_1_1_5.failure_modes.low_dedup_reduction` | 1 | 1 | +0 | · |
| `stage_1_1_5.failure_modes.near_duplicate_missed` | 7 | 10 | +3 | ↑ good |
| `stage_1_1_5.failure_modes.wrong_removal` | 0 | 0 | +0 | · |
| `stage_1_1_5.largest_miss_cluster_size` | 2 | 4 | +2 | ↑ bad |
| `stage_1_2.avg_text_quality` | 4 | 3.707 | -0.293 | ↓ bad |
| `stage_1_2.failure_modes.duplicate_suspect` | 0 | 0 | +0 | · |
| `stage_1_2.failure_modes.language_issue` | 0 | 1 | +1 | ↑ good |
| `stage_1_2.failure_modes.noise_text` | 0 | 1 | +1 | ↑ good |
| `stage_1_2.failure_modes.non_fashion_item` | 0 | 9 | +9 | ↑ good |
| `stage_1_2.failure_modes.non_fashion游戏副本` | — | 1 | — | · |
| `stage_1_2.failure_modes.pii_leak` | 0 | 3 | +3 | ↑ good |
| `stage_1_2.failure_modes.too_short` | 0 | 4 | +4 | ↑ good |
| `stage_1_2.fashion_rate` | 1 | 0.893 | -0.107 | ↓ bad |
| `stage_1_2.has_tpo_rate` | 0.667 | 0.687 | +0.02 | ↑ good |
| `stage_1_2.n_evaluated` | 1 | 50 | +49 | ↑ good |
| `stage_1_2.pii_rate` | 0.333 | 0.173 | -0.16 | ↓ good |

## Output hashes

| file | sha256 |
|---|---|
| `stage_1_0_seed.jsonl` | `sha256:42dbc866bdb796968ee245e4fca0d480683ae7889fc81b44787e23c507f4c738` |
| `stage_1_1_synthetic.jsonl` | `sha256:55b93e947b0e220a4ad4fc1ba9f826f8c1eac96469df63726b792f3f4d4ddda8` |
| `stage_1_1_5_deduped.jsonl` | `sha256:55b93e947b0e220a4ad4fc1ba9f826f8c1eac96469df63726b792f3f4d4ddda8` |
| `stage_1_2_processed.jsonl` | `sha256:55b93e947b0e220a4ad4fc1ba9f826f8c1eac96469df63726b792f3f4d4ddda8` |