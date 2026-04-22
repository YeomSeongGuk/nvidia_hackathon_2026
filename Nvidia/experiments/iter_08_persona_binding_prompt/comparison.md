# Comparison: iter_08_persona_binding_prompt vs iter_00_baseline

- this   iter: `iter_08_persona_binding_prompt`
- parent iter: `iter_00_baseline`
- this timestamp : 2026-04-21T19:04:22+00:00
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
| `quant.stage_1_1.color_top2_share` | 0.72 | 0.72 | +0 | · |
| `quant.stage_1_1.color_unique` | 8 | 8 | +0 | · |
| `quant.stage_1_1.color_white_black_share` | 0.72 | 0.72 | +0 | · |
| `quant.stage_1_1.n` | 50 | 50 | +0 | · |
| `quant.stage_1_1.rating_3_share` | 0 | 0 | +0 | · |
| `quant.stage_1_1.rating_hist.1` | 12 | 12 | +0 | · |
| `quant.stage_1_1.rating_hist.2` | 17 | 17 | +0 | · |
| `quant.stage_1_1.rating_hist.4` | 3 | 3 | +0 | · |
| `quant.stage_1_1.rating_hist.5` | 18 | 18 | +0 | · |
| `quant.stage_1_1.raw_text_len_max` | 864 | 277 | -587 | ↓ bad |
| `quant.stage_1_1.raw_text_len_median` | 94 | 137 | +43 | ↑ good |
| `quant.stage_1_1.raw_text_len_min` | 41 | 35 | -6 | ↓ bad |
| `quant.stage_1_1.raw_text_len_p90` | 189 | 210 | +21 | ↑ good |
| `quant.stage_1_1.size_suspicious_rate` | 0 | 0 | +0 | · |
| `quant.stage_1_1.size_unique` | 4 | 4 | +0 | · |
| `quant.stage_1_1.style_top1_share` | 0.88 | 0.88 | +0 | · |
| `quant.stage_1_1.style_top1_value` | 캐주얼 | 캐주얼 | — | · |
| `quant.stage_1_1.style_unique` | 6 | 6 | +0 | · |
| `quant.stage_1_1.title_len_max` | 926 | 892 | -34 | ↓ good |
| `quant.stage_1_1.title_len_median` | 27 | 26 | -1 | ↓ bad |
| `quant.stage_1_1.title_len_min` | 14 | 11 | -3 | ↓ bad |
| `quant.stage_1_1.title_len_p90` | 891 | 866 | -25 | ↓ good |
| `quant.stage_1_1.title_len_p99` | 916 | 891 | -25 | ↓ good |
| `quant.stage_1_1.title_newline_rate` | 0.38 | 0.28 | -0.1 | ↓ good |
| `quant.stage_1_1.title_reasoning_leak_rate` | 0.38 | 0.28 | -0.1 | ↓ good |
| `quant.stage_1_1_5.dedup_in_count` | 50 | 50 | +0 | · |
| `quant.stage_1_1_5.dedup_out_count` | 50 | 50 | +0 | · |
| `quant.stage_1_1_5.dedup_reduction_rate` | 0 | 0 | +0 | · |
| `quant.stage_1_2.n` | 0 | 0 | +0 | · |
| `quant.stage_1_2.retention_from_stage_1_1_5` | 0 | 0 | +0 | · |
| `stage_1_1.attr_grounded_rate` | 0.467 | 0.417 | -0.05 | ↓ bad |
| `stage_1_1.avg_persona_reflection` | 3.62 | 4.507 | +0.887 | ↑ good |
| `stage_1_1.avg_raw_text_naturalness` | 3.98 | 3.833 | -0.147 | ↓ bad |
| `stage_1_1.failure_modes.attr_mono_value` | 6 | 6 | +0 | · |
| `stage_1_1.failure_modes.attr_ungrounded` | 23 | 32 | +9 | ↑ good |
| `stage_1_1.failure_modes.language_issue` | 7 | 16 | +9 | ↑ good |
| `stage_1_1.failure_modes.length_violation` | 12 | 2 | -10 | ↓ bad |
| `stage_1_1.failure_modes.missing_tpo` | 17 | 12 | -5 | ↓ bad |
| `stage_1_1.failure_modes.non_fashion_item` | 9 | 10 | +1 | ↑ good |
| `stage_1_1.failure_modes.persona_drift` | 19 | 13 | -6 | ↓ bad |
| `stage_1_1.failure_modes.rating_sentiment_mismatch` | 12 | 0 | -12 | ↓ bad |
| `stage_1_1.failure_modes.title_format_violation` | 41 | 39 | -2 | ↓ bad |
| `stage_1_1.failure_modes.title_length_violation` | 39 | 33 | -6 | ↓ bad |
| `stage_1_1.failure_modes.title_reasoning_leak` | 25 | 23 | -2 | ↓ bad |
| `stage_1_1.fashion_rate` | 0.853 | 0.84 | -0.013 | ↓ bad |
| `stage_1_1.has_tpo_rate` | 0.947 | 0.927 | -0.02 | ↓ bad |
| `stage_1_1.n_evaluated` | 50 | 50 | +0 | · |
| `stage_1_1.rating_sentiment_consistent_rate` | 0.78 | 1 | +0.22 | ↑ good |
| `stage_1_1.raw_text_within_spec_rate` | 0.86 | 0.98 | +0.12 | ↑ good |
| `stage_1_1.title_format_ok_rate` | 0.247 | 0.313 | +0.066 | ↑ good |
| `stage_1_1.title_reasoning_leak_rate` | 0.473 | 0.427 | -0.046 | ↓ good |
| `stage_1_1.title_within_spec_rate` | 0.273 | 0.3 | +0.027 | ↑ good |
| `stage_1_1_5.dedup_in_count` | 50 | 50 | +0 | · |
| `stage_1_1_5.dedup_miss_count` | 10 | 16 | +6 | ↑ bad |
| `stage_1_1_5.dedup_miss_rate` | 0.167 | 0.227 | +0.06 | ↑ bad |
| `stage_1_1_5.dedup_out_count` | 50 | 50 | +0 | · |
| `stage_1_1_5.dedup_reduction_rate` | 0 | 0 | +0 | · |
| `stage_1_1_5.failure_modes.low_dedup_reduction` | 1 | 1 | +0 | · |
| `stage_1_1_5.failure_modes.near_duplicate_missed` | 8 | 10 | +2 | ↑ good |
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
| `stage_1_0_seed.jsonl` | `sha256:42dbc866bdb796968ee245e4fca0d480683ae7889fc81b44787e23c507f4c738` |
| `stage_1_1_synthetic.jsonl` | `sha256:81a8c7de5b0057fb67cb5f5dc6c7e2517d0661fcab09265ed6cb91e35fc1600d` |
| `stage_1_1_5_deduped.jsonl` | `sha256:81a8c7de5b0057fb67cb5f5dc6c7e2517d0661fcab09265ed6cb91e35fc1600d` |
| `stage_1_2_processed.jsonl` | `sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |