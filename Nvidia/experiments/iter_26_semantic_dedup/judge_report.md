# Judge ensemble report for iter_26_semantic_dedup

- run_id: `iter_26_semantic_dedup`
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
| stage_1_0 | `avg_text_quality` | 2.847 | 0.18 |
| stage_1_0 | `fashion_rate` | 0.88 | 0.2 |
| stage_1_0 | `has_tpo_rate` | 0.333 | 0.84 |
| stage_1_0 | `pii_rate` | 0.273 | 0.82 |
| stage_1_1 | `attr_grounded_rate` | 0.99 | 0.0 |
| stage_1_1 | `avg_persona_reflection` | 4.7 | 0.88 |
| stage_1_1 | `avg_raw_text_naturalness` | 3.883 | 1.81 |
| stage_1_1 | `fashion_rate` | 0.97 | 0.03 |
| stage_1_1 | `has_tpo_rate` | 0.993 | 0.02 |
| stage_1_1 | `rating_sentiment_consistent_rate` | 0.97 | 0.03 |
| stage_1_1 | `raw_text_within_spec_rate` | 0.993 | 0.02 |
| stage_1_1 | `title_format_ok_rate` | 0.393 | 0.19 |
| stage_1_1 | `title_reasoning_leak_rate` | 0.03 | 0.03 |
| stage_1_1 | `title_within_spec_rate` | 0.563 | 0.54 |
| stage_1_1_5 | `dedup_miss_rate` | 0.182 | 0.121 |
| stage_1_1_5 | `dedup_reduction_rate` | 0.214 | 0.0 |
| stage_1_2 | `avg_text_quality` | 4.03 | 0.45 |
| stage_1_2 | `fashion_rate` | 0.97 | 0.0 |
| stage_1_2 | `has_tpo_rate` | 0.707 | 0.79 |
| stage_1_2 | `pii_rate` | 0.453 | 0.16 |