# Judge ensemble report for iter_04_canonical_suffix_enforce

- run_id: `iter_04_canonical_suffix_enforce`
- semdedup: off
- stage22_mode: full
- judges: ['zai-org/GLM-5.1', 'deepseek-ai/DeepSeek-V3.2', 'Qwen/Qwen3-235B-A22B-Instruct-2507']
- high_variance: True
- promote: False

## Promotion-bar checks

| check | passed |
|---|---|
| `stage_2_1.avg_intent_groundedness_ge_4.0` | False |
| `stage_2_1.intent_type_valid_rate_ge_0.90` | True |
| `stage_2_1.attribute_concrete_material_ge_0.80` | False |
| `stage_2_2.coherent_rate_ge_0.85` | True |
| `stage_2_2.avg_canonical_fit_ge_4.0` | True |
| `stage_2_2.non_korean_canonical_count_eq_0` | True |
| `stage_2_2.duplicate_pairs_found_le_1` | True |
| `stage_2_2.canonical_non_fashion_rate_le_0.05` | True |
| `stage_2_3.avg_overall_usefulness_ge_4.0` | False |
| `stage_2_3.attr_fits_intent_rate_ge_0.85` | True |
| `stage_2_3.duplicate_value_count_le_2` | True |
| `stage_2_4.avg_overall_usefulness_ge_4.0` | False |
| `stage_2_4.per_query_natural_rate_ge_0.90` | True |
| `stage_2_4.avg_query_diversity_ge_3.5` | True |
| `stage_2_4.canonical_repeat_rate_le_0.10` | True |
| `stage_2_4.garbled_count_eq_0` | True |

## Per-stage ensemble means

| stage | metric | mean | range |
|---|---|---|---|
| stage_2_1 | `avg_intent_groundedness` | 2.84 | 2.76 |
| stage_2_1 | `general_wear_false_negative_rate` | 0.667 | 1.0 |
| stage_2_1 | `general_wear_rate` | 0.19 | 0.0 |
| stage_2_1 | `intent_type_valid_rate` | 0.913 | 0.14 |
| stage_2_1 | `sentiment_rating_agreement_rate` | 0.86 | 0.0 |
| stage_2_2 | `avg_canonical_fit` | 4.623 | 0.25 |
| stage_2_2 | `coherent_rate` | 0.96 | 0.12 |
| stage_2_2 | `duplicate_pairs_found` | 0.333 | 1.0 |
| stage_2_2 | `non_korean_canonical_count` | 0.0 | 0.0 |
| stage_2_2 | `should_split_count` | 2.667 | 7.0 |
| stage_2_3 | `attr_concrete_rate` | 0.973 | 0.04 |
| stage_2_3 | `attr_fits_intent_rate` | 0.94 | 0.11 |
| stage_2_3 | `avg_overall_usefulness` | 2.187 | 2.0 |
| stage_2_3 | `duplicate_value_count` | 5.0 | 15.0 |
| stage_2_3 | `evidence_reliable_rate` | 0.553 | 0.78 |
| stage_2_4 | `avg_attribute_weaving` | 2.63 | 3.22 |
| stage_2_4 | `avg_canonical_coverage` | 3.593 | 1.56 |
| stage_2_4 | `avg_overall_usefulness` | 3.89 | 1.67 |
| stage_2_4 | `avg_query_diversity` | 3.557 | 0.78 |
| stage_2_4 | `canonical_repeat_rate` | 0.02 | 0.04 |
| stage_2_4 | `garbled_count` | 0.0 | 0.0 |
| stage_2_4 | `n_queries_total` | 45.0 | 0.0 |
| stage_2_4 | `per_query_fits_intent_rate` | 1.0 | 0.0 |
| stage_2_4 | `per_query_natural_rate` | 1.0 | 0.0 |