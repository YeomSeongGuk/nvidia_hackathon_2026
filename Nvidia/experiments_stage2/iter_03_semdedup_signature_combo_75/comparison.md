# Comparison: iter_03_semdedup_signature_combo_75 vs iter_00_baseline

- this   iter: `iter_03_semdedup_signature_combo_75`
- parent iter: `iter_00_baseline`
- this timestamp : 2026-04-22T03:58:15+00:00
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
| `quant.stage_2_1_5.kept_rows` | 42 | 16 | -26 | ↓ bad |
| `quant.stage_2_1_5.semdedup_avg_cosine_of_kept` | — | 0.7174 | — | · |
| `quant.stage_2_1_5.semdedup_mode` | pass_through | active | — | · |
| `quant.stage_2_1_5.semdedup_pairs_above_threshold` | 0 | 227 | +227 | ↑ good |
| `quant.stage_2_1_5.semdedup_removed_count` | 0 | 26 | +26 | ↑ good |
| `quant.stage_2_1_5.semdedup_retention_rate` | 1 | 0.381 | -0.619 | ↓ bad |
| `quant.stage_2_1_5.semdedup_selected_threshold` | 0.9 | 0.75 | -0.15 | ↓ bad |
| `quant.stage_2_1_5.semdedup_signature_builder_used` | full | signature_combo | — | · |
| `quant.stage_2_2.canonical_count` | 11 | 15 | +4 | ↑ good |
| `quant.stage_2_2.canonical_hangul_pure_rate` | 1 | 0.929 | -0.071 | ↓ bad |
| `quant.stage_2_2.canonical_names` | <list len=10> | <list len=14> | — | · |
| `quant.stage_2_2.canonical_non_fashion_count` | 0 | 1 | +1 | ↑ good |
| `quant.stage_2_2.canonical_non_fashion_rate` | 0 | 0.071 | +0.071 | ↑ good |
| `quant.stage_2_2.canonical_suffix_compliance_rate` | 0.7 | 0.571 | -0.129 | ↓ bad |
| `quant.stage_2_2.evidence_one_count` | 5 | 13 | +8 | ↑ good |
| `quant.stage_2_2.n` | 11 | 15 | +4 | ↑ good |
| `quant.stage_2_2.n_real_clusters` | 10 | 14 | +4 | ↑ good |
| `quant.stage_2_3.avg_attrs_per_intent` | 4.09 | 2.57 | -1.52 | ↓ bad |
| `quant.stage_2_3.duplicate_value_count` | 0 | 0 | +0 | · |
| `quant.stage_2_3.n` | 11 | 14 | +3 | ↑ good |
| `quant.stage_2_3.total_attr_count` | 45 | 36 | -9 | ↓ bad |
| `quant.stage_2_4.canonical_repeat_rate` | 0 | 0 | +0 | · |
| `quant.stage_2_4.garbled_count` | 0 | 0 | +0 | · |
| `quant.stage_2_4.n_intents` | 11 | 14 | +3 | ↑ good |
| `quant.stage_2_4.query_avg_length_chars` | 23.7 | 24.2 | +0.5 | ↑ good |
| `quant.stage_2_4.query_dedup_ratio` | 1 | 1 | +0 | · |
| `quant.stage_2_4.query_non_hangul_chars_count` | 0 | 0 | +0 | · |
| `quant.stage_2_4.query_non_hangul_chars_rate` | 0 | 0 | +0 | · |
| `quant.stage_2_4.query_repeat_within_intent_count` | 0 | 0 | +0 | · |
| `quant.stage_2_4.total_queries` | 55 | 70 | +15 | ↑ good |

## Output hashes

| file | sha256 |
|---|---|
| `stage_2_1_extracted.jsonl` | `sha256:8ba4606ba1c9c452510b859f73fe38c257d118fe2fc547f3aa2df56037c7254b` |
| `stage_2_1_5_deduped.jsonl` | `sha256:f734d9ebf1c2aa438d0d407cc522c00f26af73ee52e503d0438db14c6f0ab2b8` |
| `stage_2_1_5_stats.json` | `sha256:d637d9a836d9e77ae833f5c89a66eef17a698d9d032ddc842dd02f9fc3d2ca5e` |
| `stage_2_2_clusters.jsonl` | `sha256:f3aabf56d6ae2d5135fd67a33895abc20c5468d9a8faef952f1e7287ad77a17d` |
| `stage_2_3_analyzed_intents.jsonl` | `sha256:7d92b75aa72008984d3ef6f1e93cd78ccc94a040bcfe048e23b5cf9f9ac320c4` |
| `stage_2_4_expanded_intents.jsonl` | `sha256:8650b16dbb728f75eeffda7c0e018f3d6b0420de319620321259ded3d1755735` |