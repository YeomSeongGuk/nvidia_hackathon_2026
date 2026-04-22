# Stage 1 iteration leaderboard

| iter_id | 1.1 leak ↓ | 1.1 fashion ↑ | 1.1 persona ↑ | 1.1 attr_grnd ↑ | rating_3 > 0 | dedup_reduction ↑ | e2e_ret ↑ | promote |
|---|---|---|---|---|---|---|---|---|
| `iter_00_baseline` | 0.473 | 0.853 | 3.62 | 0.467 | 0.0 | 0.0 | 0.0 | False |
| `iter_01_title_prompt_strict` | 0.12 | 0.827 | 4.0 | 0.43 | 0.0 | 0.0 | 0.02 | False |
| `iter_02_korean_quality_filter` | 0.393 | 0.86 | 3.807 | 0.43 | 0.0 | 0.0 | 1.0 | False |
| `iter_03_title_postprocess` | 0.06 | 0.86 | 3.967 | 0.473 | 0.0 | 0.0 | 0.02 | False |
| `iter_04_attr_diversity_prompt` | 0.42 | 0.88 | 3.973 | 0.593 | 0.0 | 0.0 | 0.0 | False |
| `iter_05_title_max_tokens_short` | 0.267 | 0.853 | 3.92 | 0.43 | 0.0 | 0.0 | 0.0 | False |
| `iter_06_seed_rating_3_injection` | 0.413 | 0.92 | 4.107 | 0.51 | 0.0 | 0.0 | None | False |
| `iter_07_non_fashion_seed_filter` | 0.393 | 0.787 | 4.067 | 0.47 | 0.0 | 0.0 | 0.0 | False |
| `iter_08_persona_binding_prompt` | 0.427 | 0.84 | 4.507 | 0.417 | 0.0 | 0.0 | 0.0 | False |
| `iter_09_combo_h3_h9` | 0.16 | 0.82 | 3.82 | 0.357 | 0.0 | 0.0 | 1.0 | False |
| `iter_10_combo_h3_h9_h5` | 0.067 | 0.867 | 3.827 | 0.51 | 0.0 | 0.0 | 1.0 | False |
| `iter_11_combo_h3_h9_h5_h8` | 0.073 | 0.853 | 4.633 | 0.353 | 0.0 | 0.0 | 1.0 | False |
| `iter_12_combo_all_plus_rating_sampler` | 0.127 | 0.9 | 4.693 | 0.467 | 0.3 | 0.0 | 1.0 | False |
| `iter_13_combo_plus_attr_mention` | 0.053 | 0.873 | 4.553 | 0.99 | 0.3 | 0.0 | 1.0 | False |
| `iter_14_smarter_title_postprocess` | 0.093 | 0.847 | 4.46 | 0.99 | 0.26 | 0.0 | 1.0 | False |
| `iter_15_seed_quality` | 0.12 | 0.8 | 4.693 | 0.993 | 0.22 | 0.0 | 1.0 | False |
| `iter_16_tighter_leak_regex` | 0.04 | 0.867 | 4.493 | 0.983 | 0.26 | 0.0 | 1.0 | False |
| `iter_17_postgen_fashion_filter` | 0.09 | 0.953 | 4.553 | 1.0 | 0.273 | 0.0 | 0.88 | False |
| `iter_18_h1_title_prompt_stack` | 0.057 | 0.943 | 4.633 | 0.997 | 0.146 | 0.0 | 0.82 | False |
| `iter_19_python_near_dedup` | 0.09 | 0.963 | 4.453 | 1.0 | 0.186 | 0.0 | 0.86 | False |
| `iter_20_title_fix_stack` | 0.01 | 0.94 | 4.41 | 0.997 | 0.206 | 0.0 | 0.68 | False |
| `iter_21_dedup_v2` | 0.013 | 0.97 | 4.66 | 0.99 | 0.262 | 0.0 | 0.84 | False |
| `iter_22_h1_prompt_only` | 0.047 | 0.9 | 4.463 | 0.983 | 0.25 | 0.0 | 0.88 | False |
| `iter_24_category_dedup` | 0.1 | 0.953 | 4.6 | 1.0 | 0.186 | 0.116 | 0.76 | False |
| `iter_25_attr_only_dedup` | 0.133 | 0.967 | 4.45 | 0.99 | 0.233 | 0.279 | 0.62 | False |
| `iter_26_semantic_dedup` | 0.03 | 0.97 | 4.7 | 0.99 | 0.262 | 0.214 | 0.66 | False |
| `iter_27_semdedup_aggressive` | 0.02 | 0.97 | 4.58 | 0.99 | 0.262 | 0.429 | 0.48 | False |

