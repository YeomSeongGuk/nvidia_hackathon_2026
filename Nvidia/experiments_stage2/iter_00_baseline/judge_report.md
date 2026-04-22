# Judge ensemble report for iter_00_baseline

- run_id: `iter_00_baseline`
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
| `stage_2_2.coherent_rate_ge_0.85` | False |
| `stage_2_2.avg_canonical_fit_ge_4.0` | False |
| `stage_2_2.non_korean_canonical_count_eq_0` | True |
| `stage_2_2.duplicate_pairs_found_le_1` | False |
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
| stage_2_1 | `avg_intent_groundedness` | 2.703 | 2.71 |
| stage_2_1 | `general_wear_false_negative_rate` | 0.637 | 1.0 |
| stage_2_1 | `general_wear_rate` | 0.26 | 0.0 |
| stage_2_1 | `intent_type_valid_rate` | 0.907 | 0.14 |
| stage_2_1 | `sentiment_rating_agreement_rate` | 0.86 | 0.0 |
| stage_2_2 | `avg_canonical_fit` | 3.633 | 0.4 |
| stage_2_2 | `coherent_rate` | 0.8 | 0.3 |
| stage_2_2 | `duplicate_pairs_found` | 1.333 | 3.0 |
| stage_2_2 | `non_korean_canonical_count` | 0.0 | 0.0 |
| stage_2_2 | `should_split_count` | 5.333 | 7.0 |
| stage_2_3 | `attr_concrete_rate` | 0.9 | 0.02 |
| stage_2_3 | `attr_fits_intent_rate` | 0.875 | 0.07 |
| stage_2_3 | `avg_overall_usefulness` | 2.955 | 0.09 |
| stage_2_3 | `duplicate_value_count` | 0.5 | 1.0 |
| stage_2_3 | `evidence_reliable_rate` | 0.365 | 0.37 |
| stage_2_4 | `avg_attribute_weaving` | 2.967 | 3.27 |
| stage_2_4 | `avg_canonical_coverage` | 3.817 | 1.46 |
| stage_2_4 | `avg_overall_usefulness` | 3.97 | 1.37 |
| stage_2_4 | `avg_query_diversity` | 3.697 | 0.55 |
| stage_2_4 | `canonical_repeat_rate` | 0.053 | 0.03 |
| stage_2_4 | `garbled_count` | 0.0 | 0.0 |
| stage_2_4 | `n_queries_total` | 55.0 | 0.0 |
| stage_2_4 | `per_query_fits_intent_rate` | 0.987 | 0.04 |
| stage_2_4 | `per_query_natural_rate` | 0.993 | 0.02 |