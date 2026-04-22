# Comparison: iter_02_korean_quality_filter vs iter_00_baseline

- this   iter: `iter_02_korean_quality_filter`
- parent iter: `iter_00_baseline`
- this timestamp : 2026-04-21T17:46:22+00:00
- promote flag   : False  high_variance: False

## Metric diff

| metric | parent | this | Δ | direction |
|---|---|---|---|---|
| `e2e.e2e_retention` | 0 | 1 | +1 | ↑ good |
| `e2e.input_rows_seed` | 50 | 50 | +0 | · |
| `e2e.output_rows_by_stage` | <list len=4> | <list len=4> | — | · |
| `quant.e2e.e2e_retention` | 0 | 1 | +1 | ↑ good |
| `quant.e2e.input_rows_seed` | 50 | 50 | +0 | · |
| `quant.e2e.output_rows_by_stage` | <list len=4> | <list len=4> | — | · |
| `quant.stage_1_0.n` | 50 | 50 | +0 | · |
| `quant.stage_1_0.rating_3_share` | 0 | 0 | +0 | · |
| `quant.stage_1_0.rating_hist.1` | 10 | 10 | +0 | · |
| `quant.stage_1_0.rating_hist.2` | 16 | 16 | +0 | · |
| `quant.stage_1_0.rating_hist.4` | 3 | 3 | +0 | · |
| `quant.stage_1_0.rating_hist.5` | 21 | 21 | +0 | · |
| `quant.stage_1_1.color_top2_share` | 0.72 | 0.76 | +0.04 | ↑ bad |
| `quant.stage_1_1.color_unique` | 8 | 9 | +1 | ↑ good |
| `quant.stage_1_1.color_white_black_share` | 0.72 | 0.76 | +0.04 | ↑ bad |
| `quant.stage_1_1.n` | 50 | 50 | +0 | · |
| `quant.stage_1_1.rating_3_share` | 0 | 0 | +0 | · |
| `quant.stage_1_1.rating_hist.1` | 12 | 12 | +0 | · |
| `quant.stage_1_1.rating_hist.2` | 17 | 17 | +0 | · |
| `quant.stage_1_1.rating_hist.4` | 3 | 3 | +0 | · |
| `quant.stage_1_1.rating_hist.5` | 18 | 18 | +0 | · |
| `quant.stage_1_1.raw_text_len_max` | 864 | 244 | -620 | ↓ bad |
| `quant.stage_1_1.raw_text_len_median` | 94 | 90 | -4 | ↓ bad |
| `quant.stage_1_1.raw_text_len_min` | 41 | 45 | +4 | ↑ good |
| `quant.stage_1_1.raw_text_len_p90` | 189 | 154 | -35 | ↓ bad |
| `quant.stage_1_1.size_suspicious_rate` | 0 | 0.04 | +0.04 | ↑ bad |
| `quant.stage_1_1.size_unique` | 4 | 5 | +1 | ↑ good |
| `quant.stage_1_1.style_top1_share` | 0.88 | 0.9 | +0.02 | ↑ bad |
| `quant.stage_1_1.style_top1_value` | 캐주얼 | 캐주얼 | — | · |
| `quant.stage_1_1.style_unique` | 6 | 4 | -2 | ↓ bad |
| `quant.stage_1_1.title_len_max` | 926 | 918 | -8 | ↓ good |
| `quant.stage_1_1.title_len_median` | 27 | 25 | -2 | ↓ bad |
| `quant.stage_1_1.title_len_min` | 14 | 14 | +0 | · |
| `quant.stage_1_1.title_len_p90` | 891 | 829 | -62 | ↓ good |
| `quant.stage_1_1.title_len_p99` | 916 | 883 | -33 | ↓ good |
| `quant.stage_1_1.title_newline_rate` | 0.38 | 0.3 | -0.08 | ↓ good |
| `quant.stage_1_1.title_reasoning_leak_rate` | 0.38 | 0.3 | -0.08 | ↓ good |
| `quant.stage_1_1_5.dedup_in_count` | 50 | 50 | +0 | · |
| `quant.stage_1_1_5.dedup_out_count` | 50 | 50 | +0 | · |
| `quant.stage_1_1_5.dedup_reduction_rate` | 0 | 0 | +0 | · |
| `quant.stage_1_2.n` | 0 | 50 | +50 | ↑ good |
| `quant.stage_1_2.retention_from_stage_1_1_5` | 0 | 1 | +1 | ↑ good |
| `stage_1_1.attr_grounded_rate` | 0.467 | 0.43 | -0.037 | ↓ bad |
| `stage_1_1.avg_persona_reflection` | 3.62 | 3.807 | +0.187 | ↑ good |
| `stage_1_1.avg_raw_text_naturalness` | 3.98 | 4.02 | +0.04 | ↑ good |
| `stage_1_1.failure_modes.attr_mono_value` | 6 | 7 | +1 | ↑ good |
| `stage_1_1.failure_modes.attr_ungrounded` | 23 | 33 | +10 | ↑ good |
| `stage_1_1.failure_modes.language_issue` | 7 | 7 | +0 | · |
| `stage_1_1.failure_modes.length_violation` | 12 | 9 | -3 | ↓ bad |
| `stage_1_1.failure_modes.missing_tpo` | 17 | 12 | -5 | ↓ bad |
| `stage_1_1.failure_modes.non_fashion_item` | 9 | 7 | -2 | ↓ bad |
| `stage_1_1.failure_modes.persona_drift` | 19 | 17 | -2 | ↓ bad |
| `stage_1_1.failure_modes.rating_sentiment_mismatch` | 12 | 13 | +1 | ↑ good |
| `stage_1_1.failure_modes.title_format_violation` | 41 | 41 | +0 | · |
| `stage_1_1.failure_modes.title_length_violation` | 39 | 32 | -7 | ↓ bad |
| `stage_1_1.failure_modes.title_reasoning_leak` | 25 | 22 | -3 | ↓ bad |
| `stage_1_1.fashion_rate` | 0.853 | 0.86 | +0.007 | ↑ good |
| `stage_1_1.has_tpo_rate` | 0.947 | 0.947 | +0 | · |
| `stage_1_1.n_evaluated` | 50 | 50 | +0 | · |
| `stage_1_1.rating_sentiment_consistent_rate` | 0.78 | 0.74 | -0.04 | ↓ bad |
| `stage_1_1.raw_text_within_spec_rate` | 0.86 | 0.86 | +0 | · |
| `stage_1_1.title_format_ok_rate` | 0.247 | 0.313 | +0.066 | ↑ good |
| `stage_1_1.title_reasoning_leak_rate` | 0.473 | 0.393 | -0.08 | ↓ good |
| `stage_1_1.title_within_spec_rate` | 0.273 | 0.353 | +0.08 | ↑ good |
| `stage_1_1_5.dedup_in_count` | 50 | 50 | +0 | · |
| `stage_1_1_5.dedup_miss_count` | 10 | 16 | +6 | ↑ bad |
| `stage_1_1_5.dedup_miss_rate` | 0.167 | 0.227 | +0.06 | ↑ bad |
| `stage_1_1_5.dedup_out_count` | 50 | 50 | +0 | · |
| `stage_1_1_5.dedup_reduction_rate` | 0 | 0 | +0 | · |
| `stage_1_1_5.failure_modes.low_dedup_reduction` | 1 | 1 | +0 | · |
| `stage_1_1_5.failure_modes.near_duplicate_missed` | 8 | 8 | +0 | · |
| `stage_1_1_5.failure_modes.wrong_removal` | 0 | 0 | +0 | · |
| `stage_1_1_5.largest_miss_cluster_size` | 3 | 6 | +3 | ↑ bad |
| `stage_1_2.avg_text_quality` | — | 3.747 | — | · |
| `stage_1_2.failure_modes.duplicate_suspect` | 0 | 0 | +0 | · |
| `stage_1_2.failure_modes.language_issue` | 0 | 0 | +0 | · |
| `stage_1_2.failure_modes.noise_text` | 0 | 0 | +0 | · |
| `stage_1_2.failure_modes.non_fashion_item` | 0 | 5 | +5 | ↑ good |
| `stage_1_2.failure_modes.non_fashion游戏副本` | — | 1 | — | · |
| `stage_1_2.failure_modes.pii_leak` | 0 | 1 | +1 | ↑ good |
| `stage_1_2.failure_modes.too_short` | 0 | 3 | +3 | ↑ good |
| `stage_1_2.fashion_rate` | 0 | 0.94 | +0.94 | ↑ good |
| `stage_1_2.has_tpo_rate` | 0 | 0.727 | +0.727 | ↑ good |
| `stage_1_2.n_evaluated` | 0 | 50 | +50 | ↑ good |
| `stage_1_2.pii_rate` | 0 | 0.16 | +0.16 | ↑ bad |

## Output hashes

| file | sha256 |
|---|---|
| `stage_1_0_seed.jsonl` | `sha256:42dbc866bdb796968ee245e4fca0d480683ae7889fc81b44787e23c507f4c738` |
| `stage_1_1_synthetic.jsonl` | `sha256:7150437053eda963e7bea71d84c6ea7c5615511df6233c248d137db90ec60072` |
| `stage_1_1_5_deduped.jsonl` | `sha256:7150437053eda963e7bea71d84c6ea7c5615511df6233c248d137db90ec60072` |
| `stage_1_2_processed.jsonl` | `sha256:7150437053eda963e7bea71d84c6ea7c5615511df6233c248d137db90ec60072` |