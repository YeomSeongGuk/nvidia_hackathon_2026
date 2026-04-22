# Comparison: iter_01_semdedup_intent_cosine_75 vs iter_00_baseline

- this   iter: `iter_01_semdedup_intent_cosine_75`
- parent iter: `iter_00_baseline`
- this timestamp : 2026-04-22T03:15:36+00:00
- promote flag   : False  high_variance: True

## Metric diff

| metric | parent | this | Δ | direction |
|---|---|---|---|---|
| `e2e.rows_by_stage` | <list len=5> | <list len=5> | — | · |
| `quant.e2e.rows_by_stage` | <list len=5> | <list len=5> | — | · |
| `quant.stage_2_1.attr_concrete_rate.color` | 0.738 | 0.857 | +0.119 | ↑ good |
| `quant.stage_2_1.attr_concrete_rate.fit` | 0.262 | 0.262 | +0 | · |
| `quant.stage_2_1.attr_concrete_rate.material` | 0.119 | 0.119 | +0 | · |
| `quant.stage_2_1.attr_concrete_rate.season` | 0.024 | 0.024 | +0 | · |
| `quant.stage_2_1.attr_concrete_rate.style` | 0.69 | 0.81 | +0.12 | ↑ good |
| `quant.stage_2_1.avg_keywords_per_doc` | 4.71 | 4.67 | -0.04 | ↓ bad |
| `quant.stage_2_1.general_wear_rate` | 0.262 | 0.143 | -0.119 | ↓ bad |
| `quant.stage_2_1.n` | 42 | 42 | +0 | · |
| `quant.stage_2_1_5.input_rows` | 42 | 42 | +0 | · |
| `quant.stage_2_1_5.kept_rows` | 42 | 33 | -9 | ↓ bad |
| `quant.stage_2_1_5.semdedup_avg_cosine_of_kept` | — | 0.6982 | — | · |
| `quant.stage_2_1_5.semdedup_mode` | pass_through | active | — | · |
| `quant.stage_2_1_5.semdedup_pairs_above_threshold` | 0 | 24 | +24 | ↑ good |
| `quant.stage_2_1_5.semdedup_removed_count` | 0 | 9 | +9 | ↑ good |
| `quant.stage_2_1_5.semdedup_retention_rate` | 1 | 0.786 | -0.214 | ↓ bad |
| `quant.stage_2_1_5.semdedup_selected_threshold` | 0.9 | 0.75 | -0.15 | ↓ bad |
| `quant.stage_2_1_5.semdedup_signature_builder_used` | full | full | — | · |
| `quant.stage_2_2.canonical_count` | 11 | 21 | +10 | ↑ good |
| `quant.stage_2_2.canonical_hangul_pure_rate` | 1 | 1 | +0 | · |
| `quant.stage_2_2.canonical_names` | <list len=10> | <list len=20> | — | · |
| `quant.stage_2_2.canonical_non_fashion_count` | 0 | 1 | +1 | ↑ good |
| `quant.stage_2_2.canonical_non_fashion_rate` | 0 | 0.05 | +0.05 | ↑ good |
| `quant.stage_2_2.canonical_suffix_compliance_rate` | 0.7 | 0.45 | -0.25 | ↓ bad |
| `quant.stage_2_2.evidence_one_count` | 5 | 15 | +10 | ↑ good |
| `quant.stage_2_2.n` | 11 | 21 | +10 | ↑ good |
| `quant.stage_2_2.n_real_clusters` | 10 | 20 | +10 | ↑ good |
| `quant.stage_2_3.avg_attrs_per_intent` | 4.09 | 3 | -1.09 | ↓ bad |
| `quant.stage_2_3.duplicate_value_count` | 0 | 0 | +0 | · |
| `quant.stage_2_3.n` | 11 | 21 | +10 | ↑ good |
| `quant.stage_2_3.total_attr_count` | 45 | 63 | +18 | ↑ good |
| `quant.stage_2_4.canonical_repeat_rate` | 0 | 0 | +0 | · |
| `quant.stage_2_4.garbled_count` | 0 | 0 | +0 | · |
| `quant.stage_2_4.n_intents` | 11 | 21 | +10 | ↑ good |
| `quant.stage_2_4.query_avg_length_chars` | 23.7 | 25.4 | +1.7 | ↑ good |
| `quant.stage_2_4.query_dedup_ratio` | 1 | 1 | +0 | · |
| `quant.stage_2_4.query_non_hangul_chars_count` | 0 | 1 | +1 | ↑ good |
| `quant.stage_2_4.query_non_hangul_chars_rate` | 0 | 0.01 | +0.01 | ↑ good |
| `quant.stage_2_4.query_repeat_within_intent_count` | 0 | 0 | +0 | · |
| `quant.stage_2_4.total_queries` | 55 | 105 | +50 | ↑ good |

## Output hashes

| file | sha256 |
|---|---|
| `stage_2_1_extracted.jsonl` | `sha256:b6b7baa96a6ade2d9ebf3b0c79fac14d54c5d5f13c2f972a89aa7f3a9806d12f` |
| `stage_2_1_5_deduped.jsonl` | `sha256:d05725373242e6f4d953f4d10eff7ec5b03aed5de2e607a7431f634e62c502b9` |
| `stage_2_1_5_stats.json` | `sha256:d66b127561b539e135aa5f9dfacbe38aba1510032503adf3d2110f243bd30d24` |
| `stage_2_2_clusters.jsonl` | `sha256:2da4ae1de3a90f025a6e378c11eda47692b12f84c7ac6fb14ad9fa9c2e81f0a9` |
| `stage_2_3_analyzed_intents.jsonl` | `sha256:7ea6c756dec474e1e8d728060e10fe218fbc717f0cdab49617efbaddb9970245` |
| `stage_2_4_expanded_intents.jsonl` | `sha256:7a0f4da9119590c9498e189a2a913c583148661d58b97a22632b31b05cb6aed5` |