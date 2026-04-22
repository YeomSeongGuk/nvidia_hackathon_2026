# Judge ensemble report for iter_17_postgen_fashion_filter

- run_id: `iter_17_postgen_fashion_filter`
- judges: ['zai-org/GLM-5.1', 'deepseek-ai/DeepSeek-V3.2', 'Qwen/Qwen3-235B-A22B-Instruct-2507']
- high_variance: False
- promote: False

## Promotion-bar checks

| check | passed |
|---|---|
| `stage_1_0.fashion_rate_ge_0.90` | False |
| `stage_1_0.avg_text_quality_ge_3.5` | False |
| `stage_1_1.title_leak_le_0.02` | False |
| `stage_1_1.fashion_rate_ge_0.95` | True |
| `stage_1_1.attr_grounded_ge_0.70` | True |
| `stage_1_1.persona_ge_3.5` | True |
| `quant.rating_3_share_gt_0` | True |
| `stage_1_1_5.dedup_miss_rate_le_0.05` | False |
| `stage_1_2.retention_ge_0.85` | True |
| `stage_1_2.fashion_rate_ge_0.95` | True |

## Per-stage ensemble means (selected)

| stage | metric | mean | range |
|---|---|---|---|
| stage_1_0 | `avg_text_quality` | 2.793 | 0.16 |
| stage_1_0 | `fashion_rate` | 0.873 | 0.22 |
| stage_1_0 | `has_tpo_rate` | 0.273 | 0.72 |
| stage_1_0 | `pii_rate` | 0.233 | 0.7 |
| stage_1_1 | `attr_grounded_rate` | 1.0 | 0.0 |
| stage_1_1 | `avg_persona_reflection` | 4.553 | 1.14 |
| stage_1_1 | `avg_raw_text_naturalness` | 3.86 | 1.75 |
| stage_1_1 | `fashion_rate` | 0.953 | 0.05 |
| stage_1_1 | `has_tpo_rate` | 0.967 | 0.05 |
| stage_1_1 | `rating_sentiment_consistent_rate` | 0.917 | 0.04 |
| stage_1_1 | `raw_text_within_spec_rate` | 0.977 | 0.07 |
| stage_1_1 | `title_format_ok_rate` | 0.443 | 0.16 |
| stage_1_1 | `title_reasoning_leak_rate` | 0.09 | 0.06 |
| stage_1_1 | `title_within_spec_rate` | 0.487 | 0.41 |
| stage_1_1_5 | `dedup_miss_rate` | 0.167 | 0.023 |
| stage_1_1_5 | `dedup_reduction_rate` | 0.0 | 0.0 |
| stage_1_2 | `avg_text_quality` | 3.947 | 0.46 |
| stage_1_2 | `fashion_rate` | 0.977 | 0.05 |
| stage_1_2 | `has_tpo_rate` | 0.737 | 0.77 |
| stage_1_2 | `pii_rate` | 0.437 | 0.04 |