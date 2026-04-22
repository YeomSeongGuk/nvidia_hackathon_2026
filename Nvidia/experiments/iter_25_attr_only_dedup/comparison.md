# Comparison: iter_25_attr_only_dedup vs iter_17_postgen_fashion_filter

- this   iter: `iter_25_attr_only_dedup`
- parent iter: `iter_17_postgen_fashion_filter`
- this timestamp : 2026-04-22T00:54:34+00:00
- promote flag   : False  high_variance: False

## Metric diff

| metric | parent | this | Δ | direction |
|---|---|---|---|---|
| `e2e.e2e_retention` | 0.88 | 0.62 | -0.26 | ↓ bad |
| `e2e.input_rows_seed` | 50 | 50 | +0 | · |
| `e2e.output_rows_by_stage` | <list len=4> | <list len=4> | — | · |
| `quant.e2e.e2e_retention` | 0.88 | 0.62 | -0.26 | ↓ bad |
| `quant.e2e.input_rows_seed` | 50 | 50 | +0 | · |
| `quant.e2e.output_rows_by_stage` | <list len=4> | <list len=4> | — | · |
| `quant.stage_1_0.n` | 50 | 50 | +0 | · |
| `quant.stage_1_0.rating_3_share` | 0 | 0 | +0 | · |
| `quant.stage_1_0.rating_hist.1` | 10 | 10 | +0 | · |
| `quant.stage_1_0.rating_hist.2` | 16 | 16 | +0 | · |
| `quant.stage_1_0.rating_hist.4` | 3 | 3 | +0 | · |
| `quant.stage_1_0.rating_hist.5` | 21 | 21 | +0 | · |
| `quant.stage_1_1.color_top2_share` | 0.455 | 0.512 | +0.057 | ↑ bad |
| `quant.stage_1_1.color_unique` | 6 | 8 | +2 | ↑ good |
| `quant.stage_1_1.color_white_black_share` | 0.455 | 0.349 | -0.106 | ↓ good |
| `quant.stage_1_1.n` | 44 | 43 | -1 | ↓ bad |
| `quant.stage_1_1.rating_3_share` | 0.273 | 0.233 | -0.04 | ↓ bad |
| `quant.stage_1_1.rating_hist.1` | 6 | 6 | +0 | · |
| `quant.stage_1_1.rating_hist.2` | 12 | 12 | +0 | · |
| `quant.stage_1_1.rating_hist.3` | 12 | 10 | -2 | ↓ bad |
| `quant.stage_1_1.rating_hist.4` | 3 | 6 | +3 | ↑ good |
| `quant.stage_1_1.rating_hist.5` | 11 | 9 | -2 | ↓ bad |
| `quant.stage_1_1.raw_text_len_max` | 274 | 260 | -14 | ↓ bad |
| `quant.stage_1_1.raw_text_len_median` | 144 | 160 | +16 | ↑ good |
| `quant.stage_1_1.raw_text_len_min` | 108 | 96 | -12 | ↓ bad |
| `quant.stage_1_1.raw_text_len_p90` | 202 | 201 | -1 | ↓ bad |
| `quant.stage_1_1.size_suspicious_rate` | 0.114 | 0.116 | +0.002 | ↑ bad |
| `quant.stage_1_1.size_unique` | 11 | 8 | -3 | ↓ bad |
| `quant.stage_1_1.style_top1_share` | 0.568 | 0.512 | -0.056 | ↓ good |
| `quant.stage_1_1.style_top1_value` | 캐주얼 | 캐주얼 | — | · |
| `quant.stage_1_1.style_unique` | 7 | 8 | +1 | ↑ good |
| `quant.stage_1_1.title_len_max` | 30 | 30 | +0 | · |
| `quant.stage_1_1.title_len_median` | 23 | 22 | -1 | ↓ bad |
| `quant.stage_1_1.title_len_min` | 13 | 11 | -2 | ↓ bad |
| `quant.stage_1_1.title_len_p90` | 30 | 30 | +0 | · |
| `quant.stage_1_1.title_len_p99` | 30 | 30 | +0 | · |
| `quant.stage_1_1.title_newline_rate` | 0 | 0 | +0 | · |
| `quant.stage_1_1.title_reasoning_leak_rate` | 0 | 0 | +0 | · |
| `quant.stage_1_1_5.dedup_in_count` | 44 | 43 | -1 | ↓ bad |
| `quant.stage_1_1_5.dedup_out_count` | 44 | 31 | -13 | ↓ bad |
| `quant.stage_1_1_5.dedup_reduction_rate` | 0 | 0.279 | +0.279 | ↑ good |
| `quant.stage_1_2.n` | 44 | 31 | -13 | ↓ bad |
| `quant.stage_1_2.retention_from_stage_1_1_5` | 1 | 1 | +0 | · |
| `stage_1_0.avg_text_quality` | 2.793 | 2.82 | +0.027 | ↑ good |
| `stage_1_0.failure_modes.duplicate_suspect` | 0 | 0 | +0 | · |
| `stage_1_0.failure_modes.language_issue` | 0 | 0 | +0 | · |
| `stage_1_0.failure_modes.noise_text` | 1 | 2 | +1 | ↑ good |
| `stage_1_0.failure_modes.non_fashion_item` | 10 | 8 | -2 | ↓ bad |
| `stage_1_0.failure_modes.non_fashion游戏副本` | 1 | 3 | +2 | ↑ good |
| `stage_1_0.failure_modes.pii_leak` | 0 | 0 | +0 | · |
| `stage_1_0.failure_modes.too_short` | 16 | 18 | +2 | ↑ good |
| `stage_1_0.fashion_rate` | 0.873 | 0.873 | +0 | · |
| `stage_1_0.has_tpo_rate` | 0.273 | 0.307 | +0.034 | ↑ good |
| `stage_1_0.n_evaluated` | 50 | 50 | +0 | · |
| `stage_1_0.pii_rate` | 0.233 | 0.247 | +0.014 | ↑ bad |
| `stage_1_1.attr_grounded_rate` | 1 | 0.99 | -0.01 | ↓ bad |
| `stage_1_1.avg_persona_reflection` | 4.553 | 4.45 | -0.103 | ↓ bad |
| `stage_1_1.avg_raw_text_naturalness` | 3.86 | 3.677 | -0.183 | ↓ bad |
| `stage_1_1.failure_modes.attr_mono_value` | 4 | 1 | -3 | ↓ bad |
| `stage_1_1.failure_modes.attr_ungrounded` | 3 | 0 | -3 | ↓ bad |
| `stage_1_1.failure_modes.language_issue` | 18 | 22 | +4 | ↑ good |
| `stage_1_1.failure_modes.length_violation` | 3 | 3 | +0 | · |
| `stage_1_1.failure_modes.missing_tpo` | 5 | 4 | -1 | ↓ bad |
| `stage_1_1.failure_modes.non_fashion_item` | 4 | 4 | +0 | · |
| `stage_1_1.failure_modes.persona_drift` | 13 | 13 | +0 | · |
| `stage_1_1.failure_modes.rating_sentiment_mismatch` | 5 | 1 | -4 | ↓ bad |
| `stage_1_1.failure_modes.title_format_violation` | 28 | 30 | +2 | ↑ good |
| `stage_1_1.failure_modes.title_length_violation` | 26 | 22 | -4 | ↓ bad |
| `stage_1_1.failure_modes.title_reasoning_leak` | 5 | 8 | +3 | ↑ good |
| `stage_1_1.fashion_rate` | 0.953 | 0.967 | +0.014 | ↑ good |
| `stage_1_1.has_tpo_rate` | 0.967 | 0.983 | +0.016 | ↑ good |
| `stage_1_1.n_evaluated` | 44 | 43 | -1 | ↓ bad |
| `stage_1_1.rating_sentiment_consistent_rate` | 0.917 | 0.987 | +0.07 | ↑ good |
| `stage_1_1.raw_text_within_spec_rate` | 0.977 | 0.96 | -0.017 | ↓ bad |
| `stage_1_1.title_format_ok_rate` | 0.443 | 0.337 | -0.106 | ↓ bad |
| `stage_1_1.title_reasoning_leak_rate` | 0.09 | 0.133 | +0.043 | ↑ bad |
| `stage_1_1.title_within_spec_rate` | 0.487 | 0.5 | +0.013 | ↑ good |
| `stage_1_1_5.dedup_in_count` | 44 | 43 | -1 | ↓ bad |
| `stage_1_1_5.dedup_miss_count` | 8 | 5 | -3 | ↓ good |
| `stage_1_1_5.dedup_miss_rate` | 0.167 | 0.172 | +0.005 | ↑ bad |
| `stage_1_1_5.dedup_out_count` | 44 | 31 | -13 | ↓ bad |
| `stage_1_1_5.dedup_reduction_rate` | 0 | 0.279 | +0.279 | ↑ good |
| `stage_1_1_5.failure_modes.low_dedup_reduction` | 1 | 0 | -1 | ↓ bad |
| `stage_1_1_5.failure_modes.near_duplicate_missed` | 7 | 5 | -2 | ↓ bad |
| `stage_1_1_5.failure_modes.wrong_removal` | 0 | 0 | +0 | · |
| `stage_1_1_5.largest_miss_cluster_size` | 3 | 2 | -1 | ↓ good |
| `stage_1_2.avg_text_quality` | 3.947 | 3.933 | -0.014 | ↓ bad |
| `stage_1_2.failure_modes.duplicate_suspect` | 0 | 0 | +0 | · |
| `stage_1_2.failure_modes.language_issue` | 0 | 1 | +1 | ↑ good |
| `stage_1_2.failure_modes.noise_text` | 0 | 0 | +0 | · |
| `stage_1_2.failure_modes.non_fashion_item` | 2 | 1 | -1 | ↓ bad |
| `stage_1_2.failure_modes.non_fashion游戏副本` | — | 1 | — | · |
| `stage_1_2.failure_modes.pii_leak` | 21 | 13 | -8 | ↓ bad |
| `stage_1_2.failure_modes.too_short` | 0 | 1 | +1 | ↑ good |
| `stage_1_2.fashion_rate` | 0.977 | 0.98 | +0.003 | ↑ good |
| `stage_1_2.has_tpo_rate` | 0.737 | 0.73 | -0.007 | ↓ bad |
| `stage_1_2.n_evaluated` | 44 | 31 | -13 | ↓ bad |
| `stage_1_2.pii_rate` | 0.437 | 0.44 | +0.003 | ↑ bad |

## Output hashes

| file | sha256 |
|---|---|
| `stage_1_0_seed.jsonl` | `sha256:42dbc866bdb796968ee245e4fca0d480683ae7889fc81b44787e23c507f4c738` |
| `stage_1_1_synthetic.jsonl` | `sha256:e0c7f04f73b8628c96a5ac8e260f727710f92e7f11dd50629c283e444d9bbbeb` |
| `stage_1_1_5_deduped.jsonl` | `sha256:4b5cb8af45684860ad3e3d896784e53fc84f107d8534b40b99e48a4eee615376` |
| `stage_1_2_processed.jsonl` | `sha256:4b5cb8af45684860ad3e3d896784e53fc84f107d8534b40b99e48a4eee615376` |