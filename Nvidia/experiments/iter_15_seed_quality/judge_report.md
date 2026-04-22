# Judge ensemble report for iter_15_seed_quality

- run_id: `iter_15_seed_quality`
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
| `stage_1_1.attr_grounded_ge_0.70` | True |
| `stage_1_1.persona_ge_3.5` | True |
| `quant.rating_3_share_gt_0` | True |
| `stage_1_1_5.dedup_miss_rate_le_0.05` | False |
| `stage_1_2.retention_ge_0.85` | True |
| `stage_1_2.fashion_rate_ge_0.95` | False |

## Per-stage ensemble means (selected)

| stage | metric | mean | range |
|---|---|---|---|
| stage_1_0 | `avg_text_quality` | 2.92 | 0.26 |
| stage_1_0 | `fashion_rate` | 0.86 | 0.22 |
| stage_1_0 | `has_tpo_rate` | 0.253 | 0.68 |
| stage_1_0 | `pii_rate` | 0.213 | 0.64 |
| stage_1_1 | `attr_grounded_rate` | 0.993 | 0.01 |
| stage_1_1 | `avg_persona_reflection` | 4.693 | 0.86 |
| stage_1_1 | `avg_raw_text_naturalness` | 3.753 | 1.98 |
| stage_1_1 | `fashion_rate` | 0.8 | 0.0 |
| stage_1_1 | `has_tpo_rate` | 0.953 | 0.1 |
| stage_1_1 | `rating_sentiment_consistent_rate` | 0.96 | 0.04 |
| stage_1_1 | `raw_text_within_spec_rate` | 0.993 | 0.02 |
| stage_1_1 | `title_format_ok_rate` | 0.353 | 0.2 |
| stage_1_1 | `title_reasoning_leak_rate` | 0.12 | 0.1 |
| stage_1_1 | `title_within_spec_rate` | 0.407 | 0.38 |
| stage_1_1_5 | `dedup_miss_rate` | 0.153 | 0.12 |
| stage_1_1_5 | `dedup_reduction_rate` | 0.0 | 0.0 |
| stage_1_2 | `avg_text_quality` | 3.78 | 1.06 |
| stage_1_2 | `fashion_rate` | 0.88 | 0.18 |
| stage_1_2 | `has_tpo_rate` | 0.727 | 0.7 |
| stage_1_2 | `pii_rate` | 0.493 | 0.02 |