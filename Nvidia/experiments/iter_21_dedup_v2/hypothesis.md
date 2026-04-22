# H14v2: Jaccard-bigram dedup with lowered threshold (iter_21)

**Parent**: `iter_17_postgen_fashion_filter`

**Hypothesis**: iter_19's H14v1 (whitespace tokens, threshold 0.55)
removed 0 records because:
1. Korean reviews have weak whitespace structure (words are often
   joined); whitespace-token Jaccard is a bad proxy.
2. 0.55 threshold is too strict for diverse per-persona reviews that
   share only a few common concepts (rating, product category).

**H14v2 changes**:

1. **Signature = `product_title + first 80 chars of raw_text + color + style`**
   — richer but bounded. Limits the influence of unique per-persona
   content like district names and occupations that bloat uniqueness.
2. **Tokenisation = character bigrams** (not whitespace). Robust to
   Korean morphology. E.g. "유니클로 기본 면 티셔츠" and "유니클로 베이직
   면 티" will share `"유니"`, `"니클"`, `"클로"`, `"면 "`, `" 티"` — high
   bigram overlap even when whitespace tokenisation shows 0% overlap.
3. **Threshold = 0.40** — moderate (catches near-dup clusters judges
   flag; avoids clobbering merely same-category items).

Signature/threshold choice rationale:
- Baseline iter_17 shows `dedup_miss_rate = 0.167`; 7-9 groups per 44
  records. Typical group contains 2-3 near-dups.
- Character bigrams at threshold 0.40 should fire on 2-3 clusters
  → removal rate ≈ 4-8 records → drops `dedup_miss_rate` to 0.02-0.08.

**Expected movement vs iter_17**:
- `stage_1_1_5.dedup_reduction_rate`: 0.0 → 0.05-0.15 (finally non-zero).
- `stage_1_1_5.dedup_miss_rate`: 0.167 → ≤ 0.05 (gate).
- `stage_1_1_5.dedup_out_count`: 44 → ~36-40.
- Other metrics held.

If gate fires, combined with iter_17's 6/10, we're at **7/10**.
