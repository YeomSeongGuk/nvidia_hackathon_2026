# Judge ensemble report for iter_11_combo_h3_h9_h5_h8

- run_id: `iter_11_combo_h3_h9_h5_h8`
- judges: ['zai-org/GLM-5.1', 'deepseek-ai/DeepSeek-V3.2', 'Qwen/Qwen3-235B-A22B-Instruct-2507']
- high_variance: False
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
| `stage_1_2.retention_ge_0.85` | True |
| `stage_1_2.fashion_rate_ge_0.95` | False |

## Per-stage ensemble means (selected)

| stage | metric | mean | range |
|---|---|---|---|
| stage_1_0 | `avg_text_quality` | 2.8 | 0.12 |
| stage_1_0 | `fashion_rate` | 0.893 | 0.16 |
| stage_1_0 | `has_tpo_rate` | 0.3 | 0.76 |
| stage_1_0 | `pii_rate` | 0.247 | 0.74 |
| stage_1_1 | `attr_grounded_rate` | 0.353 | 0.06 |
| stage_1_1 | `avg_persona_reflection` | 4.633 | 0.78 |
| stage_1_1 | `avg_raw_text_naturalness` | 3.94 | 1.48 |
| stage_1_1 | `fashion_rate` | 0.853 | 0.04 |
| stage_1_1 | `has_tpo_rate` | 0.94 | 0.12 |
| stage_1_1 | `rating_sentiment_consistent_rate` | 0.967 | 0.02 |
| stage_1_1 | `raw_text_within_spec_rate` | 0.993 | 0.02 |
| stage_1_1 | `title_format_ok_rate` | 0.327 | 0.26 |
| stage_1_1 | `title_reasoning_leak_rate` | 0.073 | 0.06 |
| stage_1_1 | `title_within_spec_rate` | 0.447 | 0.46 |
| stage_1_1_5 | `dedup_miss_rate` | 0.2 | 0.06 |
| stage_1_1_5 | `dedup_reduction_rate` | 0.0 | 0.0 |
| stage_1_2 | `avg_text_quality` | 3.58 | 1.02 |
| stage_1_2 | `fashion_rate` | 0.893 | 0.24 |
| stage_1_2 | `has_tpo_rate` | 0.66 | 0.86 |
| stage_1_2 | `pii_rate` | 0.507 | 0.14 |