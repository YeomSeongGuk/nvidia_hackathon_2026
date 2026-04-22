# Comparison: iter_00_baseline vs (none)

- this   iter: `iter_00_baseline`
- parent iter: ``
- this timestamp : 2026-04-22T02:28:40+00:00
- promote flag   : False  high_variance: True

(no parent metrics.json provided — showing current values only)

## Metric diff

| metric | parent | this | Δ | direction |
|---|---|---|---|---|
| `e2e.rows_by_stage` | — | <list len=5> | — | · |
| `quant.e2e.rows_by_stage` | — | <list len=5> | — | · |
| `quant.stage_2_1.attr_concrete_rate.color` | — | 0.738 | — | · |
| `quant.stage_2_1.attr_concrete_rate.fit` | — | 0.262 | — | · |
| `quant.stage_2_1.attr_concrete_rate.material` | — | 0.119 | — | · |
| `quant.stage_2_1.attr_concrete_rate.season` | — | 0.024 | — | · |
| `quant.stage_2_1.attr_concrete_rate.style` | — | 0.69 | — | · |
| `quant.stage_2_1.avg_keywords_per_doc` | — | 4.71 | — | · |
| `quant.stage_2_1.general_wear_rate` | — | 0.262 | — | · |
| `quant.stage_2_1.n` | — | 42 | — | · |
| `quant.stage_2_1_5.input_rows` | — | 42 | — | · |
| `quant.stage_2_1_5.kept_rows` | — | 42 | — | · |
| `quant.stage_2_1_5.semdedup_avg_cosine_of_kept` | — | — | — | · |
| `quant.stage_2_1_5.semdedup_mode` | — | pass_through | — | · |
| `quant.stage_2_1_5.semdedup_pairs_above_threshold` | — | 0 | — | · |
| `quant.stage_2_1_5.semdedup_removed_count` | — | 0 | — | · |
| `quant.stage_2_1_5.semdedup_retention_rate` | — | 1 | — | · |
| `quant.stage_2_1_5.semdedup_selected_threshold` | — | 0.9 | — | · |
| `quant.stage_2_1_5.semdedup_signature_builder_used` | — | full | — | · |
| `quant.stage_2_2.canonical_count` | — | 11 | — | · |
| `quant.stage_2_2.canonical_hangul_pure_rate` | — | 1 | — | · |
| `quant.stage_2_2.canonical_names` | — | <list len=10> | — | · |
| `quant.stage_2_2.canonical_non_fashion_count` | — | 0 | — | · |
| `quant.stage_2_2.canonical_non_fashion_rate` | — | 0 | — | · |
| `quant.stage_2_2.canonical_suffix_compliance_rate` | — | 0.7 | — | · |
| `quant.stage_2_2.evidence_one_count` | — | 5 | — | · |
| `quant.stage_2_2.n` | — | 11 | — | · |
| `quant.stage_2_2.n_real_clusters` | — | 10 | — | · |
| `quant.stage_2_3.avg_attrs_per_intent` | — | 4.09 | — | · |
| `quant.stage_2_3.duplicate_value_count` | — | 0 | — | · |
| `quant.stage_2_3.n` | — | 11 | — | · |
| `quant.stage_2_3.total_attr_count` | — | 45 | — | · |
| `quant.stage_2_4.canonical_repeat_rate` | — | 0 | — | · |
| `quant.stage_2_4.garbled_count` | — | 0 | — | · |
| `quant.stage_2_4.n_intents` | — | 11 | — | · |
| `quant.stage_2_4.query_avg_length_chars` | — | 23.7 | — | · |
| `quant.stage_2_4.query_dedup_ratio` | — | 1 | — | · |
| `quant.stage_2_4.query_non_hangul_chars_count` | — | 0 | — | · |
| `quant.stage_2_4.query_non_hangul_chars_rate` | — | 0 | — | · |
| `quant.stage_2_4.query_repeat_within_intent_count` | — | 0 | — | · |
| `quant.stage_2_4.total_queries` | — | 55 | — | · |

## Output hashes

| file | sha256 |
|---|---|
| `stage_2_1_extracted.jsonl` | `sha256:d941a0b6a3adb074e71d32904266bd507428d8139a51d439acace2f4b770cd21` |
| `stage_2_1_5_deduped.jsonl` | `sha256:d941a0b6a3adb074e71d32904266bd507428d8139a51d439acace2f4b770cd21` |
| `stage_2_1_5_stats.json` | `sha256:0ebfa6a376d24c1fb709cbbead8e121a72cba4af152c5900b433d6b4cde2e6e8` |
| `stage_2_2_clusters.jsonl` | `sha256:f16a18278b31d04a31ab911295899a7b9b09cea8bbf19ad72c7330ae7a75b112` |
| `stage_2_3_analyzed_intents.jsonl` | `sha256:9b755aaab8531554d285db6888e66b29eca596ac5a0675fcf54fd96ec63a31f1` |
| `stage_2_4_expanded_intents.jsonl` | `sha256:039370a767b6c2eea4a3f3f301cec43c5d376ae8b4f319c46a60d889b2250b7d` |