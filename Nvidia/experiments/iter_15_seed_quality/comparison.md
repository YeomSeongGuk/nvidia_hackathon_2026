# Comparison: iter_15_seed_quality vs iter_13_combo_plus_attr_mention

- this   iter: `iter_15_seed_quality`
- parent iter: `iter_13_combo_plus_attr_mention`
- this timestamp : 2026-04-21T20:56:13+00:00
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
| `quant.stage_1_0.rating_hist.1` | 10 | 12 | +2 | ↑ good |
| `quant.stage_1_0.rating_hist.2` | 16 | 17 | +1 | ↑ good |
| `quant.stage_1_0.rating_hist.4` | 3 | 4 | +1 | ↑ good |
| `quant.stage_1_0.rating_hist.5` | 21 | 17 | -4 | ↓ bad |
| `quant.stage_1_1.color_top2_share` | 0.5 | 0.52 | +0.02 | ↑ bad |
| `quant.stage_1_1.color_unique` | 8 | 11 | +3 | ↑ good |
| `quant.stage_1_1.color_white_black_share` | 0.38 | 0.4 | +0.02 | ↑ bad |
| `quant.stage_1_1.n` | 50 | 50 | +0 | · |
| `quant.stage_1_1.rating_3_share` | 0.3 | 0.22 | -0.08 | ↓ bad |
| `quant.stage_1_1.rating_hist.1` | 6 | 8 | +2 | ↑ good |
| `quant.stage_1_1.rating_hist.2` | 9 | 11 | +2 | ↑ good |
| `quant.stage_1_1.rating_hist.3` | 15 | 11 | -4 | ↓ bad |
| `quant.stage_1_1.rating_hist.4` | 9 | 8 | -1 | ↓ bad |
| `quant.stage_1_1.rating_hist.5` | 11 | 12 | +1 | ↑ good |
| `quant.stage_1_1.raw_text_len_max` | 255 | 313 | +58 | ↑ good |
| `quant.stage_1_1.raw_text_len_median` | 161 | 174 | +13 | ↑ good |
| `quant.stage_1_1.raw_text_len_min` | 70 | 109 | +39 | ↑ good |
| `quant.stage_1_1.raw_text_len_p90` | 228 | 227 | -1 | ↓ bad |
| `quant.stage_1_1.size_suspicious_rate` | 0.1 | 0.16 | +0.06 | ↑ bad |
| `quant.stage_1_1.size_unique` | 8 | 9 | +1 | ↑ good |
| `quant.stage_1_1.style_top1_share` | 0.54 | 0.4 | -0.14 | ↓ good |
| `quant.stage_1_1.style_top1_value` | 캐주얼 | 캐주얼 | — | · |
| `quant.stage_1_1.style_unique` | 8 | 9 | +1 | ↑ good |
| `quant.stage_1_1.title_len_max` | 30 | 30 | +0 | · |
| `quant.stage_1_1.title_len_median` | 23 | 27 | +4 | ↑ good |
| `quant.stage_1_1.title_len_min` | 12 | 12 | +0 | · |
| `quant.stage_1_1.title_len_p90` | 30 | 30 | +0 | · |
| `quant.stage_1_1.title_len_p99` | 30 | 30 | +0 | · |
| `quant.stage_1_1.title_newline_rate` | 0 | 0 | +0 | · |
| `quant.stage_1_1.title_reasoning_leak_rate` | 0 | 0 | +0 | · |
| `quant.stage_1_1_5.dedup_in_count` | 50 | 50 | +0 | · |
| `quant.stage_1_1_5.dedup_out_count` | 50 | 50 | +0 | · |
| `quant.stage_1_1_5.dedup_reduction_rate` | 0 | 0 | +0 | · |
| `quant.stage_1_2.n` | 50 | 50 | +0 | · |
| `quant.stage_1_2.retention_from_stage_1_1_5` | 1 | 1 | +0 | · |
| `stage_1_0.avg_text_quality` | 2.787 | 2.92 | +0.133 | ↑ good |
| `stage_1_0.failure_modes.duplicate_suspect` | 0 | 0 | +0 | · |
| `stage_1_0.failure_modes.language_issue` | 0 | 0 | +0 | · |
| `stage_1_0.failure_modes.noise_text` | 1 | 2 | +1 | ↑ good |
| `stage_1_0.failure_modes.non_fashion_item` | 9 | 11 | +2 | ↑ good |
| `stage_1_0.failure_modes.non_fashion游戏副本` | 1 | 1 | +0 | · |
| `stage_1_0.failure_modes.pii_leak` | 0 | 0 | +0 | · |
| `stage_1_0.failure_modes.too_short` | 23 | 11 | -12 | ↓ bad |
| `stage_1_0.fashion_rate` | 0.873 | 0.86 | -0.013 | ↓ bad |
| `stage_1_0.has_tpo_rate` | 0.26 | 0.253 | -0.007 | ↓ bad |
| `stage_1_0.n_evaluated` | 50 | 50 | +0 | · |
| `stage_1_0.pii_rate` | 0.227 | 0.213 | -0.014 | ↓ good |
| `stage_1_1.attr_grounded_rate` | 0.99 | 0.993 | +0.003 | ↑ good |
| `stage_1_1.avg_persona_reflection` | 4.553 | 4.693 | +0.14 | ↑ good |
| `stage_1_1.avg_raw_text_naturalness` | 3.913 | 3.753 | -0.16 | ↓ bad |
| `stage_1_1.failure_modes.attr_mono_value` | 2 | 5 | +3 | ↑ good |
| `stage_1_1.failure_modes.attr_ungrounded` | 4 | 8 | +4 | ↑ good |
| `stage_1_1.failure_modes.language_issue` | 13 | 16 | +3 | ↑ good |
| `stage_1_1.failure_modes.length_violation` | 1 | 1 | +0 | · |
| `stage_1_1.failure_modes.missing_tpo` | 12 | 6 | -6 | ↓ bad |
| `stage_1_1.failure_modes.non_fashion_item` | 8 | 14 | +6 | ↑ good |
| `stage_1_1.failure_modes.persona_drift` | 16 | 12 | -4 | ↓ bad |
| `stage_1_1.failure_modes.rating_sentiment_mismatch` | 2 | 3 | +1 | ↑ good |
| `stage_1_1.failure_modes.title_format_violation` | 40 | 37 | -3 | ↓ bad |
| `stage_1_1.failure_modes.title_length_violation` | 34 | 30 | -4 | ↓ bad |
| `stage_1_1.failure_modes.title_reasoning_leak` | 3 | 8 | +5 | ↑ good |
| `stage_1_1.fashion_rate` | 0.873 | 0.8 | -0.073 | ↓ bad |
| `stage_1_1.has_tpo_rate` | 0.94 | 0.953 | +0.013 | ↑ good |
| `stage_1_1.n_evaluated` | 50 | 50 | +0 | · |
| `stage_1_1.rating_sentiment_consistent_rate` | 0.973 | 0.96 | -0.013 | ↓ bad |
| `stage_1_1.raw_text_within_spec_rate` | 0.993 | 0.993 | +0 | · |
| `stage_1_1.title_format_ok_rate` | 0.293 | 0.353 | +0.06 | ↑ good |
| `stage_1_1.title_reasoning_leak_rate` | 0.053 | 0.12 | +0.067 | ↑ bad |
| `stage_1_1.title_within_spec_rate` | 0.433 | 0.407 | -0.026 | ↓ bad |
| `stage_1_1_5.dedup_in_count` | 50 | 50 | +0 | · |
| `stage_1_1_5.dedup_miss_count` | 10 | 11 | +1 | ↑ bad |
| `stage_1_1_5.dedup_miss_rate` | 0.14 | 0.153 | +0.013 | ↑ bad |
| `stage_1_1_5.dedup_out_count` | 50 | 50 | +0 | · |
| `stage_1_1_5.dedup_reduction_rate` | 0 | 0 | +0 | · |
| `stage_1_1_5.failure_modes.low_dedup_reduction` | 1 | 1 | +0 | · |
| `stage_1_1_5.failure_modes.near_duplicate_missed` | 10 | 10 | +0 | · |
| `stage_1_1_5.failure_modes.wrong_removal` | 0 | 0 | +0 | · |
| `stage_1_1_5.largest_miss_cluster_size` | 2 | 3 | +1 | ↑ bad |
| `stage_1_2.avg_text_quality` | 3.867 | 3.78 | -0.087 | ↓ bad |
| `stage_1_2.failure_modes.duplicate_suspect` | 0 | 0 | +0 | · |
| `stage_1_2.failure_modes.language_issue` | 3 | 3 | +0 | · |
| `stage_1_2.failure_modes.noise_text` | 0 | 1 | +1 | ↑ good |
| `stage_1_2.failure_modes.non_fashion_item` | 7 | 9 | +2 | ↑ good |
| `stage_1_2.failure_modes.non_fashion游戏副本` | 1 | 1 | +0 | · |
| `stage_1_2.failure_modes.pii_leak` | 28 | 25 | -3 | ↓ bad |
| `stage_1_2.failure_modes.too_short` | 0 | 0 | +0 | · |
| `stage_1_2.fashion_rate` | 0.907 | 0.88 | -0.027 | ↓ bad |
| `stage_1_2.has_tpo_rate` | 0.687 | 0.727 | +0.04 | ↑ good |
| `stage_1_2.n_evaluated` | 50 | 50 | +0 | · |
| `stage_1_2.pii_rate` | 0.513 | 0.493 | -0.02 | ↓ good |

## Output hashes

| file | sha256 |
|---|---|
| `stage_1_0_seed.jsonl` | `sha256:1d86edefdc1f48e5abfb1c4cec2878b3c4fd9d0439171d27c7f2e82eba6387f1` |
| `stage_1_1_synthetic.jsonl` | `sha256:828fbaf485e87c5ae8dec7bda11f9859566a272943973d46cbd1991e5ef3acf1` |
| `stage_1_1_5_deduped.jsonl` | `sha256:828fbaf485e87c5ae8dec7bda11f9859566a272943973d46cbd1991e5ef3acf1` |
| `stage_1_2_processed.jsonl` | `sha256:828fbaf485e87c5ae8dec7bda11f9859566a272943973d46cbd1991e5ef3acf1` |