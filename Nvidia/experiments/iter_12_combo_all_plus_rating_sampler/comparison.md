# Comparison: iter_12_combo_all_plus_rating_sampler vs iter_11_combo_h3_h9_h5_h8

- this   iter: `iter_12_combo_all_plus_rating_sampler`
- parent iter: `iter_11_combo_h3_h9_h5_h8`
- this timestamp : 2026-04-21T20:11:29+00:00
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
| `quant.stage_1_1.color_top2_share` | 0.56 | 0.58 | +0.02 | ↑ bad |
| `quant.stage_1_1.color_unique` | 9 | 6 | -3 | ↓ bad |
| `quant.stage_1_1.color_white_black_share` | 0.44 | 0.56 | +0.12 | ↑ bad |
| `quant.stage_1_1.n` | 50 | 50 | +0 | · |
| `quant.stage_1_1.rating_3_share` | 0 | 0.3 | +0.3 | ↑ good |
| `quant.stage_1_1.rating_hist.1` | 12 | 12 | +0 | · |
| `quant.stage_1_1.rating_hist.2` | 17 | 11 | -6 | ↓ bad |
| `quant.stage_1_1.rating_hist.3` | — | 15 | — | · |
| `quant.stage_1_1.rating_hist.4` | 3 | 7 | +4 | ↑ good |
| `quant.stage_1_1.rating_hist.5` | 18 | 5 | -13 | ↓ bad |
| `quant.stage_1_1.raw_text_len_max` | 275 | 399 | +124 | ↑ good |
| `quant.stage_1_1.raw_text_len_median` | 143 | 144 | +1 | ↑ good |
| `quant.stage_1_1.raw_text_len_min` | 85 | 91 | +6 | ↑ good |
| `quant.stage_1_1.raw_text_len_p90` | 196 | 201 | +5 | ↑ good |
| `quant.stage_1_1.size_suspicious_rate` | 0.1 | 0.1 | +0 | · |
| `quant.stage_1_1.size_unique` | 8 | 11 | +3 | ↑ good |
| `quant.stage_1_1.style_top1_share` | 0.56 | 0.5 | -0.06 | ↓ good |
| `quant.stage_1_1.style_top1_value` | 캐주얼 | 캐주얼 | — | · |
| `quant.stage_1_1.style_unique` | 7 | 7 | +0 | · |
| `quant.stage_1_1.title_len_max` | 30 | 30 | +0 | · |
| `quant.stage_1_1.title_len_median` | 24 | 23 | -1 | ↓ bad |
| `quant.stage_1_1.title_len_min` | 14 | 6 | -8 | ↓ bad |
| `quant.stage_1_1.title_len_p90` | 30 | 30 | +0 | · |
| `quant.stage_1_1.title_len_p99` | 30 | 30 | +0 | · |
| `quant.stage_1_1.title_newline_rate` | 0 | 0 | +0 | · |
| `quant.stage_1_1.title_reasoning_leak_rate` | 0 | 0 | +0 | · |
| `quant.stage_1_1_5.dedup_in_count` | 50 | 50 | +0 | · |
| `quant.stage_1_1_5.dedup_out_count` | 50 | 50 | +0 | · |
| `quant.stage_1_1_5.dedup_reduction_rate` | 0 | 0 | +0 | · |
| `quant.stage_1_2.n` | 50 | 50 | +0 | · |
| `quant.stage_1_2.retention_from_stage_1_1_5` | 1 | 1 | +0 | · |
| `stage_1_0.avg_text_quality` | 2.8 | 2.793 | -0.007 | ↓ bad |
| `stage_1_0.failure_modes.duplicate_suspect` | 0 | 0 | +0 | · |
| `stage_1_0.failure_modes.language_issue` | 2 | 0 | -2 | ↓ bad |
| `stage_1_0.failure_modes.noise_text` | 1 | 1 | +0 | · |
| `stage_1_0.failure_modes.non_fashion_item` | 8 | 8 | +0 | · |
| `stage_1_0.failure_modes.non_fashion游戏副本` | 1 | 1 | +0 | · |
| `stage_1_0.failure_modes.pii_leak` | 0 | 0 | +0 | · |
| `stage_1_0.failure_modes.too_short` | 18 | 19 | +1 | ↑ good |
| `stage_1_0.fashion_rate` | 0.893 | 0.893 | +0 | · |
| `stage_1_0.has_tpo_rate` | 0.3 | 0.333 | +0.033 | ↑ good |
| `stage_1_0.n_evaluated` | 50 | 50 | +0 | · |
| `stage_1_0.pii_rate` | 0.247 | 0.253 | +0.006 | ↑ bad |
| `stage_1_1.attr_grounded_rate` | 0.353 | 0.467 | +0.114 | ↑ good |
| `stage_1_1.avg_persona_reflection` | 4.633 | 4.693 | +0.06 | ↑ good |
| `stage_1_1.avg_raw_text_naturalness` | 3.94 | 3.96 | +0.02 | ↑ good |
| `stage_1_1.failure_modes.attr_mono_value` | 6 | 6 | +0 | · |
| `stage_1_1.failure_modes.attr_ungrounded` | 38 | 33 | -5 | ↓ bad |
| `stage_1_1.failure_modes.language_issue` | 5 | 11 | +6 | ↑ good |
| `stage_1_1.failure_modes.length_violation` | 1 | 1 | +0 | · |
| `stage_1_1.failure_modes.missing_tpo` | 18 | 13 | -5 | ↓ bad |
| `stage_1_1.failure_modes.non_fashion_item` | 9 | 6 | -3 | ↓ bad |
| `stage_1_1.failure_modes.persona_drift` | 9 | 6 | -3 | ↓ bad |
| `stage_1_1.failure_modes.rating_sentiment_mismatch` | 2 | 2 | +0 | · |
| `stage_1_1.failure_modes.title_format_violation` | 40 | 39 | -1 | ↓ bad |
| `stage_1_1.failure_modes.title_length_violation` | 30 | 30 | +0 | · |
| `stage_1_1.failure_modes.title_reasoning_leak` | 5 | 8 | +3 | ↑ good |
| `stage_1_1.fashion_rate` | 0.853 | 0.9 | +0.047 | ↑ good |
| `stage_1_1.has_tpo_rate` | 0.94 | 0.973 | +0.033 | ↑ good |
| `stage_1_1.n_evaluated` | 50 | 50 | +0 | · |
| `stage_1_1.rating_sentiment_consistent_rate` | 0.967 | 0.973 | +0.006 | ↑ good |
| `stage_1_1.raw_text_within_spec_rate` | 0.993 | 0.993 | +0 | · |
| `stage_1_1.title_format_ok_rate` | 0.327 | 0.32 | -0.007 | ↓ bad |
| `stage_1_1.title_reasoning_leak_rate` | 0.073 | 0.127 | +0.054 | ↑ bad |
| `stage_1_1.title_within_spec_rate` | 0.447 | 0.447 | +0 | · |
| `stage_1_1_5.dedup_in_count` | 50 | 50 | +0 | · |
| `stage_1_1_5.dedup_miss_count` | 12 | 5 | -7 | ↓ good |
| `stage_1_1_5.dedup_miss_rate` | 0.2 | 0.113 | -0.087 | ↓ good |
| `stage_1_1_5.dedup_out_count` | 50 | 50 | +0 | · |
| `stage_1_1_5.dedup_reduction_rate` | 0 | 0 | +0 | · |
| `stage_1_1_5.failure_modes.low_dedup_reduction` | 1 | 1 | +0 | · |
| `stage_1_1_5.failure_modes.near_duplicate_missed` | 9 | 10 | +1 | ↑ good |
| `stage_1_1_5.failure_modes.wrong_removal` | 0 | 0 | +0 | · |
| `stage_1_1_5.largest_miss_cluster_size` | 3 | 2 | -1 | ↓ good |
| `stage_1_2.avg_text_quality` | 3.58 | 3.74 | +0.16 | ↑ good |
| `stage_1_2.failure_modes.duplicate_suspect` | 0 | 0 | +0 | · |
| `stage_1_2.failure_modes.language_issue` | 1 | 1 | +0 | · |
| `stage_1_2.failure_modes.noise_text` | 0 | 0 | +0 | · |
| `stage_1_2.failure_modes.non_fashion_item` | 9 | 4 | -5 | ↓ bad |
| `stage_1_2.failure_modes.non_fashion游戏副本` | 3 | 3 | +0 | · |
| `stage_1_2.failure_modes.pii_leak` | 27 | 18 | -9 | ↓ bad |
| `stage_1_2.failure_modes.too_short` | 4 | 2 | -2 | ↓ bad |
| `stage_1_2.fashion_rate` | 0.893 | 0.92 | +0.027 | ↑ good |
| `stage_1_2.has_tpo_rate` | 0.66 | 0.673 | +0.013 | ↑ good |
| `stage_1_2.n_evaluated` | 50 | 50 | +0 | · |
| `stage_1_2.pii_rate` | 0.507 | 0.44 | -0.067 | ↓ good |

## Output hashes

| file | sha256 |
|---|---|
| `stage_1_0_seed.jsonl` | `sha256:42dbc866bdb796968ee245e4fca0d480683ae7889fc81b44787e23c507f4c738` |
| `stage_1_1_synthetic.jsonl` | `sha256:d519dd40f005af7eb1633a3fedddb45d41fcabb551fae1416c12c1fbf75a1bfc` |
| `stage_1_1_5_deduped.jsonl` | `sha256:d519dd40f005af7eb1633a3fedddb45d41fcabb551fae1416c12c1fbf75a1bfc` |
| `stage_1_2_processed.jsonl` | `sha256:d519dd40f005af7eb1633a3fedddb45d41fcabb551fae1416c12c1fbf75a1bfc` |