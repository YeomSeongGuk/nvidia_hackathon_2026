# Judge ensemble report for iter_03_title_postprocess

- run_id: `iter_03_title_postprocess`
- judges: ['zai-org/GLM-5.1', 'deepseek-ai/DeepSeek-V3.2', 'Qwen/Qwen3-235B-A22B-Instruct-2507']
- high_variance: True
- promote: False

## Promotion-bar checks

| check | passed |
|---|---|
| `stage_1_0.fashion_rate_ge_0.90` | False |
| `stage_1_0.avg_text_quality_ge_3.5` | False |
| `stage_1_1.title_leak_le_0.02` | False |
| `stage_1_1.fashion_rate_ge_0.95` | False |
| `stage_1_1.attr_grounded_ge_0.70` | False |
| `stage_1_1.persona_ge_3.5` | True |
| `quant.rating_3_share_gt_0` | False |
| `stage_1_1_5.dedup_miss_rate_le_0.05` | False |
| `stage_1_2.retention_ge_0.85` | False |
| `stage_1_2.fashion_rate_ge_0.95` | True |

## Per-stage ensemble means (selected)

| stage | metric | mean | range |
|---|---|---|---|
| stage_1_1 | `attr_grounded_rate` | 0.473 | 0.06 |
| stage_1_1 | `avg_persona_reflection` | 3.967 | 0.7 |
| stage_1_1 | `avg_raw_text_naturalness` | 4.137 | 0.82 |
| stage_1_1 | `fashion_rate` | 0.86 | 0.06 |
| stage_1_1 | `has_tpo_rate` | 0.967 | 0.02 |
| stage_1_1 | `rating_sentiment_consistent_rate` | 0.663 | 0.02 |
| stage_1_1 | `raw_text_within_spec_rate` | 0.9 | 0.1 |
| stage_1_1 | `title_format_ok_rate` | 0.35 | 0.2 |
| stage_1_1 | `title_reasoning_leak_rate` | 0.06 | 0.16 |
| stage_1_1 | `title_within_spec_rate` | 0.44 | 0.49 |
| stage_1_1_5 | `dedup_miss_rate` | 0.109 | 0.061 |
| stage_1_1_5 | `dedup_reduction_rate` | 0.0 | 0.0 |
| stage_1_2 | `avg_text_quality` | 4.0 | 0.0 |
| stage_1_2 | `fashion_rate` | 1.0 | 0.0 |
| stage_1_2 | `has_tpo_rate` | 0.667 | 1.0 |
| stage_1_2 | `pii_rate` | 0.333 | 1.0 |