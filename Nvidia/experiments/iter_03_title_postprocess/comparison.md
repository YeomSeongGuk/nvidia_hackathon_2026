# Comparison: iter_03_title_postprocess vs iter_00_baseline

- this   iter: `iter_03_title_postprocess`
- parent iter: `iter_00_baseline`
- this timestamp : 2026-04-21T17:57:48+00:00
- promote flag   : False  high_variance: True

## Metric diff

| metric | parent | this | Δ | direction |
|---|---|---|---|---|
| `e2e.e2e_retention` | 0 | 0.02 | +0.02 | ↑ good |
| `e2e.input_rows_seed` | 50 | 50 | +0 | · |
| `e2e.output_rows_by_stage` | <list len=4> | <list len=4> | — | · |
| `quant.e2e.e2e_retention` | 0 | 0.02 | +0.02 | ↑ good |
| `quant.e2e.input_rows_seed` | 50 | 50 | +0 | · |
| `quant.e2e.output_rows_by_stage` | <list len=4> | <list len=4> | — | · |
| `quant.stage_1_0.n` | 50 | 50 | +0 | · |
| `quant.stage_1_0.rating_3_share` | 0 | 0 | +0 | · |
| `quant.stage_1_0.rating_hist.1` | 10 | 10 | +0 | · |
| `quant.stage_1_0.rating_hist.2` | 16 | 16 | +0 | · |
| `quant.stage_1_0.rating_hist.4` | 3 | 3 | +0 | · |
| `quant.stage_1_0.rating_hist.5` | 21 | 21 | +0 | · |
| `quant.stage_1_1.color_top2_share` | 0.72 | 0.633 | -0.087 | ↓ good |
| `quant.stage_1_1.color_unique` | 8 | 7 | -1 | ↓ bad |
| `quant.stage_1_1.color_white_black_share` | 0.72 | 0.633 | -0.087 | ↓ good |
| `quant.stage_1_1.n` | 50 | 49 | -1 | ↓ bad |
| `quant.stage_1_1.rating_3_share` | 0 | 0 | +0 | · |
| `quant.stage_1_1.rating_hist.1` | 12 | 12 | +0 | · |
| `quant.stage_1_1.rating_hist.2` | 17 | 17 | +0 | · |
| `quant.stage_1_1.rating_hist.4` | 3 | 3 | +0 | · |
| `quant.stage_1_1.rating_hist.5` | 18 | 17 | -1 | ↓ bad |
| `quant.stage_1_1.raw_text_len_max` | 864 | 262 | -602 | ↓ bad |
| `quant.stage_1_1.raw_text_len_median` | 94 | 92 | -2 | ↓ bad |
| `quant.stage_1_1.raw_text_len_min` | 41 | 52 | +11 | ↑ good |
| `quant.stage_1_1.raw_text_len_p90` | 189 | 191 | +2 | ↑ good |
| `quant.stage_1_1.size_suspicious_rate` | 0 | 0.02 | +0.02 | ↑ bad |
| `quant.stage_1_1.size_unique` | 4 | 5 | +1 | ↑ good |
| `quant.stage_1_1.style_top1_share` | 0.88 | 0.898 | +0.018 | ↑ bad |
| `quant.stage_1_1.style_top1_value` | 캐주얼 | 캐주얼 | — | · |
| `quant.stage_1_1.style_unique` | 6 | 3 | -3 | ↓ bad |
| `quant.stage_1_1.title_len_max` | 926 | 30 | -896 | ↓ good |
| `quant.stage_1_1.title_len_median` | 27 | 24 | -3 | ↓ bad |
| `quant.stage_1_1.title_len_min` | 14 | 10 | -4 | ↓ bad |
| `quant.stage_1_1.title_len_p90` | 891 | 30 | -861 | ↓ good |
| `quant.stage_1_1.title_len_p99` | 916 | 30 | -886 | ↓ good |
| `quant.stage_1_1.title_newline_rate` | 0.38 | 0 | -0.38 | ↓ good |
| `quant.stage_1_1.title_reasoning_leak_rate` | 0.38 | 0 | -0.38 | ↓ good |
| `quant.stage_1_1_5.dedup_in_count` | 50 | 49 | -1 | ↓ bad |
| `quant.stage_1_1_5.dedup_out_count` | 50 | 49 | -1 | ↓ bad |
| `quant.stage_1_1_5.dedup_reduction_rate` | 0 | 0 | +0 | · |
| `quant.stage_1_2.n` | 0 | 1 | +1 | ↑ good |
| `quant.stage_1_2.retention_from_stage_1_1_5` | 0 | 0.02 | +0.02 | ↑ good |
| `stage_1_1.attr_grounded_rate` | 0.467 | 0.473 | +0.006 | ↑ good |
| `stage_1_1.avg_persona_reflection` | 3.62 | 3.967 | +0.347 | ↑ good |
| `stage_1_1.avg_raw_text_naturalness` | 3.98 | 4.137 | +0.157 | ↑ good |
| `stage_1_1.failure_modes.attr_mono_value` | 6 | 5 | -1 | ↓ bad |
| `stage_1_1.failure_modes.attr_ungrounded` | 23 | 31 | +8 | ↑ good |
| `stage_1_1.failure_modes.language_issue` | 7 | 7 | +0 | · |
| `stage_1_1.failure_modes.length_violation` | 12 | 8 | -4 | ↓ bad |
| `stage_1_1.failure_modes.missing_tpo` | 17 | 11 | -6 | ↓ bad |
| `stage_1_1.failure_modes.non_fashion_item` | 9 | 9 | +0 | · |
| `stage_1_1.failure_modes.persona_drift` | 19 | 14 | -5 | ↓ bad |
| `stage_1_1.failure_modes.rating_sentiment_mismatch` | 12 | 17 | +5 | ↑ good |
| `stage_1_1.failure_modes.title_format_violation` | 41 | 36 | -5 | ↓ bad |
| `stage_1_1.failure_modes.title_length_violation` | 39 | 30 | -9 | ↓ bad |
| `stage_1_1.failure_modes.title_reasoning_leak` | 25 | 8 | -17 | ↓ bad |
| `stage_1_1.fashion_rate` | 0.853 | 0.86 | +0.007 | ↑ good |
| `stage_1_1.has_tpo_rate` | 0.947 | 0.967 | +0.02 | ↑ good |
| `stage_1_1.n_evaluated` | 50 | 49 | -1 | ↓ bad |
| `stage_1_1.rating_sentiment_consistent_rate` | 0.78 | 0.663 | -0.117 | ↓ bad |
| `stage_1_1.raw_text_within_spec_rate` | 0.86 | 0.9 | +0.04 | ↑ good |
| `stage_1_1.title_format_ok_rate` | 0.247 | 0.35 | +0.103 | ↑ good |
| `stage_1_1.title_reasoning_leak_rate` | 0.473 | 0.06 | -0.413 | ↓ good |
| `stage_1_1.title_within_spec_rate` | 0.273 | 0.44 | +0.167 | ↑ good |
| `stage_1_1_5.dedup_in_count` | 50 | 49 | -1 | ↓ bad |
| `stage_1_1_5.dedup_miss_count` | 10 | 7 | -3 | ↓ good |
| `stage_1_1_5.dedup_miss_rate` | 0.167 | 0.109 | -0.058 | ↓ good |
| `stage_1_1_5.dedup_out_count` | 50 | 49 | -1 | ↓ bad |
| `stage_1_1_5.dedup_reduction_rate` | 0 | 0 | +0 | · |
| `stage_1_1_5.failure_modes.low_dedup_reduction` | 1 | 1 | +0 | · |
| `stage_1_1_5.failure_modes.near_duplicate_missed` | 8 | 7 | -1 | ↓ bad |
| `stage_1_1_5.failure_modes.wrong_removal` | 0 | 0 | +0 | · |
| `stage_1_1_5.largest_miss_cluster_size` | 3 | 2 | -1 | ↓ good |
| `stage_1_2.avg_text_quality` | — | 4 | — | · |
| `stage_1_2.failure_modes.duplicate_suspect` | 0 | 0 | +0 | · |
| `stage_1_2.failure_modes.language_issue` | 0 | 0 | +0 | · |
| `stage_1_2.failure_modes.noise_text` | 0 | 0 | +0 | · |
| `stage_1_2.failure_modes.non_fashion_item` | 0 | 0 | +0 | · |
| `stage_1_2.failure_modes.pii_leak` | 0 | 0 | +0 | · |
| `stage_1_2.failure_modes.too_short` | 0 | 0 | +0 | · |
| `stage_1_2.fashion_rate` | 0 | 1 | +1 | ↑ good |
| `stage_1_2.has_tpo_rate` | 0 | 0.667 | +0.667 | ↑ good |
| `stage_1_2.n_evaluated` | 0 | 1 | +1 | ↑ good |
| `stage_1_2.pii_rate` | 0 | 0.333 | +0.333 | ↑ bad |

## Output hashes

| file | sha256 |
|---|---|
| `stage_1_0_seed.jsonl` | `sha256:42dbc866bdb796968ee245e4fca0d480683ae7889fc81b44787e23c507f4c738` |
| `stage_1_1_synthetic.jsonl` | `sha256:631f145f708b03269d23a5a544d3c000f20e1c47b7fb0552343c3fff8ed5fb49` |
| `stage_1_1_5_deduped.jsonl` | `sha256:631f145f708b03269d23a5a544d3c000f20e1c47b7fb0552343c3fff8ed5fb49` |
| `stage_1_2_processed.jsonl` | `sha256:d9b4234568003c8914acaf2348204dce05af1ea61a55b0035daed8bf985e5587` |