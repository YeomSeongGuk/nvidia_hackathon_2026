# Comparison: iter_19_python_near_dedup vs iter_17_postgen_fashion_filter

- this   iter: `iter_19_python_near_dedup`
- parent iter: `iter_17_postgen_fashion_filter`
- this timestamp : 2026-04-21T21:53:53+00:00
- promote flag   : False  high_variance: False

## Metric diff

| metric | parent | this | Δ | direction |
|---|---|---|---|---|
| `e2e.e2e_retention` | 0.88 | 0.86 | -0.02 | ↓ bad |
| `e2e.input_rows_seed` | 50 | 50 | +0 | · |
| `e2e.output_rows_by_stage` | <list len=4> | <list len=4> | — | · |
| `quant.e2e.e2e_retention` | 0.88 | 0.86 | -0.02 | ↓ bad |
| `quant.e2e.input_rows_seed` | 50 | 50 | +0 | · |
| `quant.e2e.output_rows_by_stage` | <list len=4> | <list len=4> | — | · |
| `quant.stage_1_0.n` | 50 | 50 | +0 | · |
| `quant.stage_1_0.rating_3_share` | 0 | 0 | +0 | · |
| `quant.stage_1_0.rating_hist.1` | 10 | 10 | +0 | · |
| `quant.stage_1_0.rating_hist.2` | 16 | 16 | +0 | · |
| `quant.stage_1_0.rating_hist.4` | 3 | 3 | +0 | · |
| `quant.stage_1_0.rating_hist.5` | 21 | 21 | +0 | · |
| `quant.stage_1_1.color_top2_share` | 0.455 | 0.488 | +0.033 | ↑ bad |
| `quant.stage_1_1.color_unique` | 6 | 9 | +3 | ↑ good |
| `quant.stage_1_1.color_white_black_share` | 0.455 | 0.419 | -0.036 | ↓ good |
| `quant.stage_1_1.n` | 44 | 43 | -1 | ↓ bad |
| `quant.stage_1_1.rating_3_share` | 0.273 | 0.186 | -0.087 | ↓ bad |
| `quant.stage_1_1.rating_hist.1` | 6 | 15 | +9 | ↑ good |
| `quant.stage_1_1.rating_hist.2` | 12 | 7 | -5 | ↓ bad |
| `quant.stage_1_1.rating_hist.3` | 12 | 8 | -4 | ↓ bad |
| `quant.stage_1_1.rating_hist.4` | 3 | 9 | +6 | ↑ good |
| `quant.stage_1_1.rating_hist.5` | 11 | 4 | -7 | ↓ bad |
| `quant.stage_1_1.raw_text_len_max` | 274 | 277 | +3 | ↑ good |
| `quant.stage_1_1.raw_text_len_median` | 144 | 148 | +4 | ↑ good |
| `quant.stage_1_1.raw_text_len_min` | 108 | 96 | -12 | ↓ bad |
| `quant.stage_1_1.raw_text_len_p90` | 202 | 237 | +35 | ↑ good |
| `quant.stage_1_1.size_suspicious_rate` | 0.114 | 0.093 | -0.021 | ↓ good |
| `quant.stage_1_1.size_unique` | 11 | 8 | -3 | ↓ bad |
| `quant.stage_1_1.style_top1_share` | 0.568 | 0.535 | -0.033 | ↓ good |
| `quant.stage_1_1.style_top1_value` | 캐주얼 | 캐주얼 | — | · |
| `quant.stage_1_1.style_unique` | 7 | 8 | +1 | ↑ good |
| `quant.stage_1_1.title_len_max` | 30 | 30 | +0 | · |
| `quant.stage_1_1.title_len_median` | 23 | 20 | -3 | ↓ bad |
| `quant.stage_1_1.title_len_min` | 13 | 11 | -2 | ↓ bad |
| `quant.stage_1_1.title_len_p90` | 30 | 30 | +0 | · |
| `quant.stage_1_1.title_len_p99` | 30 | 30 | +0 | · |
| `quant.stage_1_1.title_newline_rate` | 0 | 0 | +0 | · |
| `quant.stage_1_1.title_reasoning_leak_rate` | 0 | 0 | +0 | · |
| `quant.stage_1_1_5.dedup_in_count` | 44 | 43 | -1 | ↓ bad |
| `quant.stage_1_1_5.dedup_out_count` | 44 | 43 | -1 | ↓ bad |
| `quant.stage_1_1_5.dedup_reduction_rate` | 0 | 0 | +0 | · |
| `quant.stage_1_2.n` | 44 | 43 | -1 | ↓ bad |
| `quant.stage_1_2.retention_from_stage_1_1_5` | 1 | 1 | +0 | · |
| `stage_1_0.avg_text_quality` | 2.793 | 2.76 | -0.033 | ↓ bad |
| `stage_1_0.failure_modes.duplicate_suspect` | 0 | 0 | +0 | · |
| `stage_1_0.failure_modes.language_issue` | 0 | 0 | +0 | · |
| `stage_1_0.failure_modes.noise_text` | 1 | 1 | +0 | · |
| `stage_1_0.failure_modes.non_fashion_item` | 10 | 8 | -2 | ↓ bad |
| `stage_1_0.failure_modes.non_fashion游戏副本` | 1 | 1 | +0 | · |
| `stage_1_0.failure_modes.pii_leak` | 0 | 0 | +0 | · |
| `stage_1_0.failure_modes.too_short` | 16 | 13 | -3 | ↓ bad |
| `stage_1_0.fashion_rate` | 0.873 | 0.893 | +0.02 | ↑ good |
| `stage_1_0.has_tpo_rate` | 0.273 | 0.307 | +0.034 | ↑ good |
| `stage_1_0.n_evaluated` | 50 | 50 | +0 | · |
| `stage_1_0.pii_rate` | 0.233 | 0.273 | +0.04 | ↑ bad |
| `stage_1_1.attr_grounded_rate` | 1 | 1 | +0 | · |
| `stage_1_1.avg_persona_reflection` | 4.553 | 4.453 | -0.1 | ↓ bad |
| `stage_1_1.avg_raw_text_naturalness` | 3.86 | 3.79 | -0.07 | ↓ bad |
| `stage_1_1.failure_modes.attr_mono_value` | 4 | 2 | -2 | ↓ bad |
| `stage_1_1.failure_modes.attr_ungrounded` | 3 | 2 | -1 | ↓ bad |
| `stage_1_1.failure_modes.language_issue` | 18 | 16 | -2 | ↓ bad |
| `stage_1_1.failure_modes.length_violation` | 3 | 1 | -2 | ↓ bad |
| `stage_1_1.failure_modes.missing_tpo` | 5 | 7 | +2 | ↑ good |
| `stage_1_1.failure_modes.non_fashion_item` | 4 | 5 | +1 | ↑ good |
| `stage_1_1.failure_modes.persona_drift` | 13 | 16 | +3 | ↑ good |
| `stage_1_1.failure_modes.rating_sentiment_mismatch` | 5 | 1 | -4 | ↓ bad |
| `stage_1_1.failure_modes.title_format_violation` | 28 | 34 | +6 | ↑ good |
| `stage_1_1.failure_modes.title_length_violation` | 26 | 24 | -2 | ↓ bad |
| `stage_1_1.failure_modes.title_reasoning_leak` | 5 | 7 | +2 | ↑ good |
| `stage_1_1.fashion_rate` | 0.953 | 0.963 | +0.01 | ↑ good |
| `stage_1_1.has_tpo_rate` | 0.967 | 0.97 | +0.003 | ↑ good |
| `stage_1_1.n_evaluated` | 44 | 43 | -1 | ↓ bad |
| `stage_1_1.rating_sentiment_consistent_rate` | 0.917 | 0.993 | +0.076 | ↑ good |
| `stage_1_1.raw_text_within_spec_rate` | 0.977 | 0.987 | +0.01 | ↑ good |
| `stage_1_1.title_format_ok_rate` | 0.443 | 0.32 | -0.123 | ↓ bad |
| `stage_1_1.title_reasoning_leak_rate` | 0.09 | 0.09 | +0 | · |
| `stage_1_1.title_within_spec_rate` | 0.487 | 0.463 | -0.024 | ↓ bad |
| `stage_1_1_5.dedup_in_count` | 44 | 43 | -1 | ↓ bad |
| `stage_1_1_5.dedup_miss_count` | 8 | 7 | -1 | ↓ good |
| `stage_1_1_5.dedup_miss_rate` | 0.167 | 0.124 | -0.043 | ↓ good |
| `stage_1_1_5.dedup_out_count` | 44 | 43 | -1 | ↓ bad |
| `stage_1_1_5.dedup_reduction_rate` | 0 | 0 | +0 | · |
| `stage_1_1_5.failure_modes.low_dedup_reduction` | 1 | 1 | +0 | · |
| `stage_1_1_5.failure_modes.near_duplicate_missed` | 7 | 5 | -2 | ↓ bad |
| `stage_1_1_5.failure_modes.wrong_removal` | 0 | 0 | +0 | · |
| `stage_1_1_5.largest_miss_cluster_size` | 3 | 3 | +0 | · |
| `stage_1_2.avg_text_quality` | 3.947 | 3.877 | -0.07 | ↓ bad |
| `stage_1_2.failure_modes.duplicate_suspect` | 0 | 0 | +0 | · |
| `stage_1_2.failure_modes.language_issue` | 0 | 1 | +1 | ↑ good |
| `stage_1_2.failure_modes.noise_text` | 0 | 0 | +0 | · |
| `stage_1_2.failure_modes.non_fashion_item` | 2 | 2 | +0 | · |
| `stage_1_2.failure_modes.non_fashion游戏副本_item` | — | 1 | — | · |
| `stage_1_2.failure_modes.pii_leak` | 21 | 25 | +4 | ↑ good |
| `stage_1_2.failure_modes.too_short` | 0 | 0 | +0 | · |
| `stage_1_2.fashion_rate` | 0.977 | 0.97 | -0.007 | ↓ bad |
| `stage_1_2.has_tpo_rate` | 0.737 | 0.72 | -0.017 | ↓ bad |
| `stage_1_2.n_evaluated` | 44 | 43 | -1 | ↓ bad |
| `stage_1_2.pii_rate` | 0.437 | 0.58 | +0.143 | ↑ bad |

## Output hashes

| file | sha256 |
|---|---|
| `stage_1_0_seed.jsonl` | `sha256:42dbc866bdb796968ee245e4fca0d480683ae7889fc81b44787e23c507f4c738` |
| `stage_1_1_synthetic.jsonl` | `sha256:89bf7a9290ac2eaf666cf4484d21a044550f30d961cbdc2b3e403d7b3951dc0d` |
| `stage_1_1_5_deduped.jsonl` | `sha256:89bf7a9290ac2eaf666cf4484d21a044550f30d961cbdc2b3e403d7b3951dc0d` |
| `stage_1_2_processed.jsonl` | `sha256:89bf7a9290ac2eaf666cf4484d21a044550f30d961cbdc2b3e403d7b3951dc0d` |