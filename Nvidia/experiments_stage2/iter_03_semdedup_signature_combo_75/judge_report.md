# Judge ensemble report for iter_03_semdedup_signature_combo_75

- run_id: `iter_03_semdedup_signature_combo_75`
- semdedup: 0.75
- stage22_mode: full
- judges: ['zai-org/GLM-5.1', 'deepseek-ai/DeepSeek-V3.2', 'Qwen/Qwen3-235B-A22B-Instruct-2507']
- high_variance: True
- promote: False

## Promotion-bar checks

| check | passed |
|---|---|
| `stage_2_1.avg_intent_groundedness_ge_4.0` | False |
| `stage_2_1.intent_type_valid_rate_ge_0.90` | False |
| `stage_2_1.attribute_concrete_material_ge_0.80` | False |
| `stage_2_2.coherent_rate_ge_0.85` | True |
| `stage_2_2.avg_canonical_fit_ge_4.0` | True |
| `stage_2_2.non_korean_canonical_count_eq_0` | True |
| `stage_2_2.duplicate_pairs_found_le_1` | True |
| `stage_2_2.canonical_non_fashion_rate_le_0.05` | False |
| `stage_2_3.avg_overall_usefulness_ge_4.0` | False |
| `stage_2_3.attr_fits_intent_rate_ge_0.85` | False |
| `stage_2_3.duplicate_value_count_le_2` | True |
| `stage_2_4.avg_overall_usefulness_ge_4.0` | False |
| `stage_2_4.per_query_natural_rate_ge_0.90` | True |
| `stage_2_4.avg_query_diversity_ge_3.5` | False |
| `stage_2_4.canonical_repeat_rate_le_0.10` | True |
| `stage_2_4.garbled_count_eq_0` | True |

## Per-stage ensemble means

| stage | metric | mean | range |
|---|---|---|---|
| stage_2_1 | `avg_intent_groundedness` | 2.783 | 2.83 |
| stage_2_1 | `general_wear_false_negative_rate` | 0.667 | 1.0 |
| stage_2_1 | `general_wear_rate` | 0.19 | 0.0 |
| stage_2_1 | `intent_type_valid_rate` | 0.897 | 0.21 |
| stage_2_1 | `sentiment_rating_agreement_rate` | 0.83 | 0.0 |
| stage_2_2 | `avg_canonical_fit` | 4.643 | 0.5 |
| stage_2_2 | `coherent_rate` | 0.977 | 0.07 |
| stage_2_2 | `duplicate_pairs_found` | 0.0 | 0.0 |
| stage_2_2 | `non_korean_canonical_count` | 0.0 | 0.0 |
| stage_2_2 | `should_split_count` | 5.0 | 14.0 |
| stage_2_3 | `attr_concrete_rate` | 0.937 | 0.11 |
| stage_2_3 | `attr_fits_intent_rate` | 0.84 | 0.31 |
| stage_2_3 | `avg_overall_usefulness` | 1.76 | 1.14 |
| stage_2_3 | `duplicate_value_count` | 4.333 | 13.0 |
| stage_2_3 | `evidence_reliable_rate` | 0.38 | 1.0 |
| stage_2_4 | `avg_attribute_weaving` | 2.717 | 3.14 |
| stage_2_4 | `avg_canonical_coverage` | 3.523 | 1.78 |
| stage_2_4 | `avg_overall_usefulness` | 3.69 | 1.36 |
| stage_2_4 | `avg_query_diversity` | 3.43 | 0.93 |
| stage_2_4 | `canonical_repeat_rate` | 0.02 | 0.03 |
| stage_2_4 | `garbled_count` | 0.667 | 2.0 |
| stage_2_4 | `n_queries_total` | 70.0 | 0.0 |
| stage_2_4 | `per_query_fits_intent_rate` | 0.99 | 0.03 |
| stage_2_4 | `per_query_natural_rate` | 0.967 | 0.07 |