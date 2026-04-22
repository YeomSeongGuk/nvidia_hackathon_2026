# Comparison: iter_02_semdedup_strict_70 vs iter_00_baseline

- this   iter: `iter_02_semdedup_strict_70`
- parent iter: `iter_00_baseline`
- this timestamp : 2026-04-22T03:32:09+00:00
- promote flag   : False  high_variance: True

## Metric diff

| metric | parent | this | Δ | direction |
|---|---|---|---|---|
| `e2e.rows_by_stage` | <list len=5> | <list len=5> | — | · |
| `quant.e2e.rows_by_stage` | <list len=5> | <list len=5> | — | · |
| `quant.stage_2_1.attr_concrete_rate.color` | 0.738 | 0.881 | +0.143 | ↑ good |
| `quant.stage_2_1.attr_concrete_rate.fit` | 0.262 | 0.262 | +0 | · |
| `quant.stage_2_1.attr_concrete_rate.material` | 0.119 | 0.119 | +0 | · |
| `quant.stage_2_1.attr_concrete_rate.season` | 0.024 | 0.024 | +0 | · |
| `quant.stage_2_1.attr_concrete_rate.style` | 0.69 | 0.738 | +0.048 | ↑ good |
| `quant.stage_2_1.avg_keywords_per_doc` | 4.71 | 4.79 | +0.08 | ↑ good |
| `quant.stage_2_1.general_wear_rate` | 0.262 | 0.119 | -0.143 | ↓ bad |
| `quant.stage_2_1.n` | 42 | 42 | +0 | · |
| `quant.stage_2_1_5.input_rows` | 42 | 42 | +0 | · |
| `quant.stage_2_1_5.kept_rows` | 42 | 26 | -16 | ↓ bad |
| `quant.stage_2_1_5.semdedup_avg_cosine_of_kept` | — | 0.6642 | — | · |
| `quant.stage_2_1_5.semdedup_mode` | pass_through | active | — | · |
| `quant.stage_2_1_5.semdedup_pairs_above_threshold` | 0 | 62 | +62 | ↑ good |
| `quant.stage_2_1_5.semdedup_removed_count` | 0 | 16 | +16 | ↑ good |
| `quant.stage_2_1_5.semdedup_retention_rate` | 1 | 0.619 | -0.381 | ↓ bad |
| `quant.stage_2_1_5.semdedup_selected_threshold` | 0.9 | 0.7 | -0.2 | ↓ bad |
| `quant.stage_2_1_5.semdedup_signature_builder_used` | full | full | — | · |
| `quant.stage_2_2.canonical_count` | 11 | 15 | +4 | ↑ good |
| `quant.stage_2_2.canonical_hangul_pure_rate` | 1 | 0.929 | -0.071 | ↓ bad |
| `quant.stage_2_2.canonical_names` | <list len=10> | <list len=14> | — | · |
| `quant.stage_2_2.canonical_non_fashion_count` | 0 | 0 | +0 | · |
| `quant.stage_2_2.canonical_non_fashion_rate` | 0 | 0 | +0 | · |
| `quant.stage_2_2.canonical_suffix_compliance_rate` | 0.7 | 0.643 | -0.057 | ↓ bad |
| `quant.stage_2_2.evidence_one_count` | 5 | 11 | +6 | ↑ good |
| `quant.stage_2_2.n` | 11 | 15 | +4 | ↑ good |
| `quant.stage_2_2.n_real_clusters` | 10 | 14 | +4 | ↑ good |
| `quant.stage_2_3.avg_attrs_per_intent` | 4.09 | 2.93 | -1.16 | ↓ bad |
| `quant.stage_2_3.duplicate_value_count` | 0 | 0 | +0 | · |
| `quant.stage_2_3.n` | 11 | 15 | +4 | ↑ good |
| `quant.stage_2_3.total_attr_count` | 45 | 44 | -1 | ↓ bad |
| `quant.stage_2_4.canonical_repeat_rate` | 0 | 0 | +0 | · |
| `quant.stage_2_4.garbled_count` | 0 | 0 | +0 | · |
| `quant.stage_2_4.n_intents` | 11 | 15 | +4 | ↑ good |
| `quant.stage_2_4.query_avg_length_chars` | 23.7 | 23.3 | -0.4 | ↓ bad |
| `quant.stage_2_4.query_dedup_ratio` | 1 | 1 | +0 | · |
| `quant.stage_2_4.query_non_hangul_chars_count` | 0 | 1 | +1 | ↑ good |
| `quant.stage_2_4.query_non_hangul_chars_rate` | 0 | 0.013 | +0.013 | ↑ good |
| `quant.stage_2_4.query_repeat_within_intent_count` | 0 | 0 | +0 | · |
| `quant.stage_2_4.total_queries` | 55 | 75 | +20 | ↑ good |

## Output hashes

| file | sha256 |
|---|---|
| `stage_2_1_extracted.jsonl` | `sha256:55496d8cf554dba9fb69d03a736d812104a3f01fa1e13902cf69a0260bc5c7b8` |
| `stage_2_1_5_deduped.jsonl` | `sha256:0412c90ff5b122a659c944f8a0598b2e300abde3e35d6491fa19461970574588` |
| `stage_2_1_5_stats.json` | `sha256:01b5b264a1b880d6ea7060c4efdb710bff68facfec772e9ccca1c3bde0a4cf87` |
| `stage_2_2_clusters.jsonl` | `sha256:c5f3bc3f3064fa826a37716d4ee98242a37531857afb2a8f19e418b535a22a60` |
| `stage_2_3_analyzed_intents.jsonl` | `sha256:cb593c413940aced3f5c10a77cbb34bf1b9fae53e02550bb9a582225c58f5394` |
| `stage_2_4_expanded_intents.jsonl` | `sha256:bbacc71fea522ecde74633df071225e1cd0303f14f0315844090b571d1ddf9ac` |