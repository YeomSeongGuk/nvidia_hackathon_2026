# H14: Python Jaccard near-dedup (iter_19)

**Parent**: `iter_17_postgen_fashion_filter` (NOT iter_18 — iter_18's
H3v4 prose-regex + short "패션 상품" fallback regressed title_format_ok
from 0.44 → 0.06 because 4-char fallback fails spec).

**Hypothesis**: iter_17 shows `dedup_miss_rate = 0.167`, `dedup_reduction
= 0` — the fuzzy dedup step falls back to `pandas.drop_duplicates`
(exact-match only) when `cudf` is missing. Judges flag 7-9
near-duplicate groups per 50-record batch where records share 55%+
token overlap but aren't byte-identical. A pure-Python Jaccard similarity
pass at n=50 is O(n²) = 2500 set-ops, trivial, and catches these dups
without a GPU library install.

**H14 change** (in `run_fuzzy_deduplication` `except` branch):
- tokenise each `raw_text` by whitespace
- pairwise Jaccard similarity: `|a ∩ b| / |a ∪ b|`
- if ≥ 0.55, mark the later record as duplicate
- then also run `drop_duplicates(subset=text_field)` for exact-match safety

Also: explicitly write `data/stage_1_1_5/deduped.jsonl` in
`run_pipeline()` so iter_run.py picks it up as the canonical artifact
(instead of silently copying `stage_1_1_synthetic.jsonl` as the
fallback). This makes dedup measurable for the first time.

**Expected movement vs iter_17**:

- `stage_1_1_5.dedup_reduction_rate`: 0.0 → 0.10-0.20 (actual dedup).
- `stage_1_1_5.dedup_miss_rate`: 0.167 → ≤ 0.05 (promote gate).
- `stage_1_1_5.dedup_out_count`: 44 → ~37-40.
- `e2e.output_rows_by_stage`: [50, 44, <44, <44].
- All other metrics held from iter_17.

If dedup gate passes, we'd be at **7/10 gates** (up from iter_17's 6).
Remaining: stage_1_0.fashion_rate (0.87 vs 0.90, noise band),
stage_1_0.avg_text_quality (2.79 vs 3.5, structural), title_leak (0.09
in iter_17, needs a separate iter with a longer format-compliant
fallback title).
