# H9: `korean_quality_filter` (iter_02)

**Parent**: `iter_00_baseline` (`stage_1_2.n_evaluated = 0`, `e2e_retention = 0`)

**Hypothesis**: The baseline Stage 1.2 uses two nemo-curator filters:
```python
WordCountFilter(min_words=5, lang="ko")
NonAlphaNumericFilter(max_non_alpha_numeric_to_text_ratio=0.85)
```
`NonAlphaNumericFilter` treats Hangul (U+AC00–U+D7A3) as
*non-alphanumeric*, so a normal Korean review (which is >85% Hangul) is
always above the 0.85 ratio → dropped. iter_00 observed exactly this:
50 → 0 survivors.

**Change**: Replace `run_quality_filtering()` with a Korean-aware
pandas filter:

- drop rows where `raw_text` is non-string, empty, or >500 chars
  (500 doubles as a reasoning-leak guardrail)
- require ≥ 20 Hangul characters (`[\u3131-\u318E\uAC00-\uD7A3]`)
- remove `WordCountFilter` — Korean has no space-separated words.

Expected movement:

- `stage_1_2.n_evaluated`: 0 → ~45.
- `quant.stage_1_2.retention_from_stage_1_1_5`: 0 → ≥ 0.85 target.
- `stage_1_2.fashion_rate`, `has_tpo_rate`, etc. become non-zero for
  the first time (they propagate from Stage 1.1 since no real content
  filter now runs).
- `e2e.e2e_retention`: 0 → ≥ 0.80.

Non-goals:
- Stage 1.1 metrics are unaffected (pipeline_script.py only changes
  Stage 1.2 logic). `title_reasoning_leak_rate` stays ≈ 0.47.
- This is an infra fix, not a quality fix.
