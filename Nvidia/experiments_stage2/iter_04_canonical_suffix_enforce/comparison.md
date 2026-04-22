# Comparison: iter_04_canonical_suffix_enforce vs iter_00_baseline

- this   iter: `iter_04_canonical_suffix_enforce`
- parent iter: `iter_00_baseline`
- this timestamp : 2026-04-22T04:36:44+00:00
- promote flag   : False  high_variance: True

## Metric diff

| metric | parent | this | Δ | direction |
|---|---|---|---|---|
| `e2e.rows_by_stage` | <list len=5> | <list len=5> | — | · |
| `quant.e2e.rows_by_stage` | <list len=5> | <list len=5> | — | · |
| `quant.stage_2_1.attr_concrete_rate.color` | 0.738 | 0.81 | +0.072 | ↑ good |
| `quant.stage_2_1.attr_concrete_rate.fit` | 0.262 | 0.262 | +0 | · |
| `quant.stage_2_1.attr_concrete_rate.material` | 0.119 | 0.119 | +0 | · |
| `quant.stage_2_1.attr_concrete_rate.season` | 0.024 | 0.024 | +0 | · |
| `quant.stage_2_1.attr_concrete_rate.style` | 0.69 | 0.738 | +0.048 | ↑ good |
| `quant.stage_2_1.avg_keywords_per_doc` | 4.71 | 4.74 | +0.03 | ↑ good |
| `quant.stage_2_1.general_wear_rate` | 0.262 | 0.19 | -0.072 | ↓ bad |
| `quant.stage_2_1.n` | 42 | 42 | +0 | · |
| `quant.stage_2_1_5.input_rows` | 42 | 42 | +0 | · |
| `quant.stage_2_1_5.kept_rows` | 42 | 42 | +0 | · |
| `quant.stage_2_1_5.semdedup_avg_cosine_of_kept` | — | — | — | · |
| `quant.stage_2_1_5.semdedup_mode` | pass_through | pass_through | — | · |
| `quant.stage_2_1_5.semdedup_pairs_above_threshold` | 0 | 0 | +0 | · |
| `quant.stage_2_1_5.semdedup_removed_count` | 0 | 0 | +0 | · |
| `quant.stage_2_1_5.semdedup_retention_rate` | 1 | 1 | +0 | · |
| `quant.stage_2_1_5.semdedup_selected_threshold` | 0.9 | 0.9 | +0 | · |
| `quant.stage_2_1_5.semdedup_signature_builder_used` | full | full | — | · |
| `quant.stage_2_2.canonical_count` | 11 | 9 | -2 | ↓ bad |
| `quant.stage_2_2.canonical_hangul_pure_rate` | 1 | 0.875 | -0.125 | ↓ bad |
| `quant.stage_2_2.canonical_names` | <list len=10> | <list len=8> | — | · |
| `quant.stage_2_2.canonical_non_fashion_count` | 0 | 0 | +0 | · |
| `quant.stage_2_2.canonical_non_fashion_rate` | 0 | 0 | +0 | · |
| `quant.stage_2_2.canonical_suffix_compliance_rate` | 0.7 | 0.625 | -0.075 | ↓ bad |
| `quant.stage_2_2.evidence_one_count` | 5 | 7 | +2 | ↑ good |
| `quant.stage_2_2.n` | 11 | 9 | -2 | ↓ bad |
| `quant.stage_2_2.n_real_clusters` | 10 | 8 | -2 | ↓ bad |
| `quant.stage_2_3.avg_attrs_per_intent` | 4.09 | 3 | -1.09 | ↓ bad |
| `quant.stage_2_3.duplicate_value_count` | 0 | 0 | +0 | · |
| `quant.stage_2_3.n` | 11 | 9 | -2 | ↓ bad |
| `quant.stage_2_3.total_attr_count` | 45 | 27 | -18 | ↓ bad |
| `quant.stage_2_4.canonical_repeat_rate` | 0 | 0 | +0 | · |
| `quant.stage_2_4.garbled_count` | 0 | 0 | +0 | · |
| `quant.stage_2_4.n_intents` | 11 | 9 | -2 | ↓ bad |
| `quant.stage_2_4.query_avg_length_chars` | 23.7 | 24.1 | +0.4 | ↑ good |
| `quant.stage_2_4.query_dedup_ratio` | 1 | 1 | +0 | · |
| `quant.stage_2_4.query_non_hangul_chars_count` | 0 | 0 | +0 | · |
| `quant.stage_2_4.query_non_hangul_chars_rate` | 0 | 0 | +0 | · |
| `quant.stage_2_4.query_repeat_within_intent_count` | 0 | 0 | +0 | · |
| `quant.stage_2_4.total_queries` | 55 | 45 | -10 | ↓ bad |

## Output hashes

| file | sha256 |
|---|---|
| `stage_2_1_extracted.jsonl` | `sha256:6729726f83268ece3e531f48e2c9e78a723b116d461f34ea80b0a7c50e7dc5b1` |
| `stage_2_1_5_deduped.jsonl` | `sha256:6729726f83268ece3e531f48e2c9e78a723b116d461f34ea80b0a7c50e7dc5b1` |
| `stage_2_1_5_stats.json` | `sha256:c128faa624b23536983204231bdea137caaf09b6ce30a878304572d38bef20e3` |
| `stage_2_2_clusters.jsonl` | `sha256:18abe339299faff32df98d758ee384c36f498e84fa5b92bf9ee25c4319ee5c0b` |
| `stage_2_3_analyzed_intents.jsonl` | `sha256:6728ed8b69b6148871a73be8c56339b94409c5421dd84f2d282d3a6c4fcea4ba` |
| `stage_2_4_expanded_intents.jsonl` | `sha256:d84787706132c54960e30b02eb25b51bf4e7377121ed598f55bc643eb678d356` |