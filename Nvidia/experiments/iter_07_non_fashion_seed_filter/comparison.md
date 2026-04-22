# Comparison: iter_07_non_fashion_seed_filter vs iter_00_baseline

- this   iter: `iter_07_non_fashion_seed_filter`
- parent iter: `iter_00_baseline`
- this timestamp : 2026-04-21T18:51:06+00:00
- promote flag   : False  high_variance: False

## Metric diff

| metric | parent | this | Δ | direction |
|---|---|---|---|---|
| `e2e.e2e_retention` | 0 | 0 | +0 | · |
| `e2e.input_rows_seed` | 50 | 50 | +0 | · |
| `e2e.output_rows_by_stage` | <list len=4> | <list len=4> | — | · |
| `quant.e2e.e2e_retention` | 0 | 0 | +0 | · |
| `quant.e2e.input_rows_seed` | 50 | 50 | +0 | · |
| `quant.e2e.output_rows_by_stage` | <list len=4> | <list len=4> | — | · |
| `quant.stage_1_0.n` | 50 | 50 | +0 | · |
| `quant.stage_1_0.rating_3_share` | 0 | 0 | +0 | · |
| `quant.stage_1_0.rating_hist.1` | 10 | 9 | -1 | ↓ bad |
| `quant.stage_1_0.rating_hist.2` | 16 | 15 | -1 | ↓ bad |
| `quant.stage_1_0.rating_hist.4` | 3 | 3 | +0 | · |
| `quant.stage_1_0.rating_hist.5` | 21 | 23 | +2 | ↑ good |
| `quant.stage_1_1.color_top2_share` | 0.72 | 0.74 | +0.02 | ↑ bad |
| `quant.stage_1_1.color_unique` | 8 | 7 | -1 | ↓ bad |
| `quant.stage_1_1.color_white_black_share` | 0.72 | 0.74 | +0.02 | ↑ bad |
| `quant.stage_1_1.n` | 50 | 50 | +0 | · |
| `quant.stage_1_1.rating_3_share` | 0 | 0 | +0 | · |
| `quant.stage_1_1.rating_hist.1` | 12 | 9 | -3 | ↓ bad |
| `quant.stage_1_1.rating_hist.2` | 17 | 12 | -5 | ↓ bad |
| `quant.stage_1_1.rating_hist.4` | 3 | 3 | +0 | · |
| `quant.stage_1_1.rating_hist.5` | 18 | 26 | +8 | ↑ good |
| `quant.stage_1_1.raw_text_len_max` | 864 | 347 | -517 | ↓ bad |
| `quant.stage_1_1.raw_text_len_median` | 94 | 100 | +6 | ↑ good |
| `quant.stage_1_1.raw_text_len_min` | 41 | 39 | -2 | ↓ bad |
| `quant.stage_1_1.raw_text_len_p90` | 189 | 203 | +14 | ↑ good |
| `quant.stage_1_1.size_suspicious_rate` | 0 | 0 | +0 | · |
| `quant.stage_1_1.size_unique` | 4 | 3 | -1 | ↓ bad |
| `quant.stage_1_1.style_top1_share` | 0.88 | 0.9 | +0.02 | ↑ bad |
| `quant.stage_1_1.style_top1_value` | 캐주얼 | 캐주얼 | — | · |
| `quant.stage_1_1.style_unique` | 6 | 6 | +0 | · |
| `quant.stage_1_1.title_len_max` | 926 | 1015 | +89 | ↑ bad |
| `quant.stage_1_1.title_len_median` | 27 | 29 | +2 | ↑ good |
| `quant.stage_1_1.title_len_min` | 14 | 13 | -1 | ↓ bad |
| `quant.stage_1_1.title_len_p90` | 891 | 869 | -22 | ↓ good |
| `quant.stage_1_1.title_len_p99` | 916 | 928 | +12 | ↑ bad |
| `quant.stage_1_1.title_newline_rate` | 0.38 | 0.3 | -0.08 | ↓ good |
| `quant.stage_1_1.title_reasoning_leak_rate` | 0.38 | 0.3 | -0.08 | ↓ good |
| `quant.stage_1_1_5.dedup_in_count` | 50 | 50 | +0 | · |
| `quant.stage_1_1_5.dedup_out_count` | 50 | 50 | +0 | · |
| `quant.stage_1_1_5.dedup_reduction_rate` | 0 | 0 | +0 | · |
| `quant.stage_1_2.n` | 0 | 0 | +0 | · |
| `quant.stage_1_2.retention_from_stage_1_1_5` | 0 | 0 | +0 | · |
| `stage_1_1.attr_grounded_rate` | 0.467 | 0.47 | +0.003 | ↑ good |
| `stage_1_1.avg_persona_reflection` | 3.62 | 4.067 | +0.447 | ↑ good |
| `stage_1_1.avg_raw_text_naturalness` | 3.98 | 4.113 | +0.133 | ↑ good |
| `stage_1_1.failure_modes.attr_mono_value` | 6 | 7 | +1 | ↑ good |
| `stage_1_1.failure_modes.attr_ungrounded` | 23 | 25 | +2 | ↑ good |
| `stage_1_1.failure_modes.language_issue` | 7 | 6 | -1 | ↓ bad |
| `stage_1_1.failure_modes.length_violation` | 12 | 6 | -6 | ↓ bad |
| `stage_1_1.failure_modes.missing_tpo` | 17 | 16 | -1 | ↓ bad |
| `stage_1_1.failure_modes.non_fashion_item` | 9 | 11 | +2 | ↑ good |
| `stage_1_1.failure_modes.persona_drift` | 19 | 11 | -8 | ↓ bad |
| `stage_1_1.failure_modes.rating_sentiment_mismatch` | 12 | 8 | -4 | ↓ bad |
| `stage_1_1.failure_modes.title_format_violation` | 41 | 38 | -3 | ↓ bad |
| `stage_1_1.failure_modes.title_length_violation` | 39 | 30 | -9 | ↓ bad |
| `stage_1_1.failure_modes.title_reasoning_leak` | 25 | 22 | -3 | ↓ bad |
| `stage_1_1.fashion_rate` | 0.853 | 0.787 | -0.066 | ↓ bad |
| `stage_1_1.has_tpo_rate` | 0.947 | 0.96 | +0.013 | ↑ good |
| `stage_1_1.n_evaluated` | 50 | 50 | +0 | · |
| `stage_1_1.rating_sentiment_consistent_rate` | 0.78 | 0.847 | +0.067 | ↑ good |
| `stage_1_1.raw_text_within_spec_rate` | 0.86 | 0.887 | +0.027 | ↑ good |
| `stage_1_1.title_format_ok_rate` | 0.247 | 0.28 | +0.033 | ↑ good |
| `stage_1_1.title_reasoning_leak_rate` | 0.473 | 0.393 | -0.08 | ↓ good |
| `stage_1_1.title_within_spec_rate` | 0.273 | 0.327 | +0.054 | ↑ good |
| `stage_1_1_5.dedup_in_count` | 50 | 50 | +0 | · |
| `stage_1_1_5.dedup_miss_count` | 10 | 11 | +1 | ↑ bad |
| `stage_1_1_5.dedup_miss_rate` | 0.167 | 0.14 | -0.027 | ↓ good |
| `stage_1_1_5.dedup_out_count` | 50 | 50 | +0 | · |
| `stage_1_1_5.dedup_reduction_rate` | 0 | 0 | +0 | · |
| `stage_1_1_5.failure_modes.low_dedup_reduction` | 1 | 1 | +0 | · |
| `stage_1_1_5.failure_modes.near_duplicate_missed` | 8 | 9 | +1 | ↑ good |
| `stage_1_1_5.failure_modes.wrong_removal` | 0 | 0 | +0 | · |
| `stage_1_1_5.largest_miss_cluster_size` | 3 | 3 | +0 | · |
| `stage_1_2.failure_modes.duplicate_suspect` | 0 | 0 | +0 | · |
| `stage_1_2.failure_modes.language_issue` | 0 | 0 | +0 | · |
| `stage_1_2.failure_modes.noise_text` | 0 | 0 | +0 | · |
| `stage_1_2.failure_modes.non_fashion_item` | 0 | 0 | +0 | · |
| `stage_1_2.failure_modes.pii_leak` | 0 | 0 | +0 | · |
| `stage_1_2.failure_modes.too_short` | 0 | 0 | +0 | · |
| `stage_1_2.fashion_rate` | 0 | 0 | +0 | · |
| `stage_1_2.has_tpo_rate` | 0 | 0 | +0 | · |
| `stage_1_2.n_evaluated` | 0 | 0 | +0 | · |
| `stage_1_2.pii_rate` | 0 | 0 | +0 | · |

## Output hashes

| file | sha256 |
|---|---|
| `stage_1_0_seed.jsonl` | `sha256:3fa9d8042fe53cd6ef404112caa5c81ab532fc86fa8984988fa7d7352aa13675` |
| `stage_1_1_synthetic.jsonl` | `sha256:7b1d8556cef51ab0388e6bde946d9e858e8fc930d4f46d7426d74a8c5b326a64` |
| `stage_1_1_5_deduped.jsonl` | `sha256:7b1d8556cef51ab0388e6bde946d9e858e8fc930d4f46d7426d74a8c5b326a64` |
| `stage_1_2_processed.jsonl` | `sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |