# Comparison: iter_04_attr_diversity_prompt vs iter_00_baseline

- this   iter: `iter_04_attr_diversity_prompt`
- parent iter: `iter_00_baseline`
- this timestamp : 2026-04-21T18:09:26+00:00
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
| `quant.stage_1_0.rating_hist.1` | 10 | 10 | +0 | · |
| `quant.stage_1_0.rating_hist.2` | 16 | 16 | +0 | · |
| `quant.stage_1_0.rating_hist.4` | 3 | 3 | +0 | · |
| `quant.stage_1_0.rating_hist.5` | 21 | 21 | +0 | · |
| `quant.stage_1_1.color_top2_share` | 0.72 | 0.76 | +0.04 | ↑ bad |
| `quant.stage_1_1.color_unique` | 8 | 6 | -2 | ↓ bad |
| `quant.stage_1_1.color_white_black_share` | 0.72 | 0 | -0.72 | ↓ good |
| `quant.stage_1_1.n` | 50 | 50 | +0 | · |
| `quant.stage_1_1.rating_3_share` | 0 | 0 | +0 | · |
| `quant.stage_1_1.rating_hist.1` | 12 | 12 | +0 | · |
| `quant.stage_1_1.rating_hist.2` | 17 | 17 | +0 | · |
| `quant.stage_1_1.rating_hist.4` | 3 | 3 | +0 | · |
| `quant.stage_1_1.rating_hist.5` | 18 | 18 | +0 | · |
| `quant.stage_1_1.raw_text_len_max` | 864 | 335 | -529 | ↓ bad |
| `quant.stage_1_1.raw_text_len_median` | 94 | 108 | +14 | ↑ good |
| `quant.stage_1_1.raw_text_len_min` | 41 | 39 | -2 | ↓ bad |
| `quant.stage_1_1.raw_text_len_p90` | 189 | 195 | +6 | ↑ good |
| `quant.stage_1_1.size_suspicious_rate` | 0 | 0.08 | +0.08 | ↑ bad |
| `quant.stage_1_1.size_unique` | 4 | 8 | +4 | ↑ good |
| `quant.stage_1_1.style_top1_share` | 0.88 | 0.34 | -0.54 | ↓ good |
| `quant.stage_1_1.style_top1_value` | 캐주얼 | 클래식 | — | · |
| `quant.stage_1_1.style_unique` | 6 | 10 | +4 | ↑ good |
| `quant.stage_1_1.title_len_max` | 926 | 976 | +50 | ↑ bad |
| `quant.stage_1_1.title_len_median` | 27 | 29 | +2 | ↑ good |
| `quant.stage_1_1.title_len_min` | 14 | 11 | -3 | ↓ bad |
| `quant.stage_1_1.title_len_p90` | 891 | 839 | -52 | ↓ good |
| `quant.stage_1_1.title_len_p99` | 916 | 938 | +22 | ↑ bad |
| `quant.stage_1_1.title_newline_rate` | 0.38 | 0.38 | +0 | · |
| `quant.stage_1_1.title_reasoning_leak_rate` | 0.38 | 0.38 | +0 | · |
| `quant.stage_1_1_5.dedup_in_count` | 50 | 50 | +0 | · |
| `quant.stage_1_1_5.dedup_out_count` | 50 | 50 | +0 | · |
| `quant.stage_1_1_5.dedup_reduction_rate` | 0 | 0 | +0 | · |
| `quant.stage_1_2.n` | 0 | 0 | +0 | · |
| `quant.stage_1_2.retention_from_stage_1_1_5` | 0 | 0 | +0 | · |
| `stage_1_1.attr_grounded_rate` | 0.467 | 0.593 | +0.126 | ↑ good |
| `stage_1_1.avg_persona_reflection` | 3.62 | 3.973 | +0.353 | ↑ good |
| `stage_1_1.avg_raw_text_naturalness` | 3.98 | 3.98 | +0 | · |
| `stage_1_1.failure_modes.attr_mono_value` | 6 | 4 | -2 | ↓ bad |
| `stage_1_1.failure_modes.attr_ungrounded` | 23 | 23 | +0 | · |
| `stage_1_1.failure_modes.language_issue` | 7 | 8 | +1 | ↑ good |
| `stage_1_1.failure_modes.length_violation` | 12 | 5 | -7 | ↓ bad |
| `stage_1_1.failure_modes.missing_tpo` | 17 | 9 | -8 | ↓ bad |
| `stage_1_1.failure_modes.non_fashion_item` | 9 | 6 | -3 | ↓ bad |
| `stage_1_1.failure_modes.persona_drift` | 19 | 13 | -6 | ↓ bad |
| `stage_1_1.failure_modes.rating_sentiment_mismatch` | 12 | 14 | +2 | ↑ good |
| `stage_1_1.failure_modes.title_format_violation` | 41 | 35 | -6 | ↓ bad |
| `stage_1_1.failure_modes.title_length_violation` | 39 | 35 | -4 | ↓ bad |
| `stage_1_1.failure_modes.title_reasoning_leak` | 25 | 22 | -3 | ↓ bad |
| `stage_1_1.fashion_rate` | 0.853 | 0.88 | +0.027 | ↑ good |
| `stage_1_1.has_tpo_rate` | 0.947 | 0.973 | +0.026 | ↑ good |
| `stage_1_1.n_evaluated` | 50 | 50 | +0 | · |
| `stage_1_1.rating_sentiment_consistent_rate` | 0.78 | 0.72 | -0.06 | ↓ bad |
| `stage_1_1.raw_text_within_spec_rate` | 0.86 | 0.933 | +0.073 | ↑ good |
| `stage_1_1.title_format_ok_rate` | 0.247 | 0.4 | +0.153 | ↑ good |
| `stage_1_1.title_reasoning_leak_rate` | 0.473 | 0.42 | -0.053 | ↓ good |
| `stage_1_1.title_within_spec_rate` | 0.273 | 0.313 | +0.04 | ↑ good |
| `stage_1_1_5.dedup_in_count` | 50 | 50 | +0 | · |
| `stage_1_1_5.dedup_miss_count` | 10 | 11 | +1 | ↑ bad |
| `stage_1_1_5.dedup_miss_rate` | 0.167 | 0.16 | -0.007 | ↓ good |
| `stage_1_1_5.dedup_out_count` | 50 | 50 | +0 | · |
| `stage_1_1_5.dedup_reduction_rate` | 0 | 0 | +0 | · |
| `stage_1_1_5.failure_modes.low_dedup_reduction` | 1 | 1 | +0 | · |
| `stage_1_1_5.failure_modes.near_duplicate_missed` | 8 | 8 | +0 | · |
| `stage_1_1_5.failure_modes.wrong_removal` | 0 | 0 | +0 | · |
| `stage_1_1_5.largest_miss_cluster_size` | 3 | 4 | +1 | ↑ bad |
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
| `stage_1_0_seed.jsonl` | `sha256:42dbc866bdb796968ee245e4fca0d480683ae7889fc81b44787e23c507f4c738` |
| `stage_1_1_synthetic.jsonl` | `sha256:1d99a26f2f6cf76340e4f556c162344e3543bf6fb4c62c2c244b9c490dee34ff` |
| `stage_1_1_5_deduped.jsonl` | `sha256:1d99a26f2f6cf76340e4f556c162344e3543bf6fb4c62c2c244b9c490dee34ff` |
| `stage_1_2_processed.jsonl` | `sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |