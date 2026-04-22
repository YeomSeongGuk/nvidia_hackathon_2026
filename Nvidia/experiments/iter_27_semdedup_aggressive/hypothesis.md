# iter_27: aggressive semantic dedup (title+attrs embedding, eps=0.18)

**Parent**: `iter_21_dedup_v2` (reuses its stage_1_0 + stage_1_1 outputs)

**Hypothesis**: iter_26 removed 9 records semantically but
`dedup_miss_rate` stayed at 0.18 — judges still saw 7 near-dup pairs
in the 33 remaining. Root cause: our embedding mixes per-persona
review prose (high variance) with product signal (low variance),
diluting similarity. iter_27 fixes this:

1. **Embedding mode = `title_attrs` only** (no review text). The
   signal is `product_title + color + style + size`, which is exactly
   what the tri-judge near-dup rubric keys on.
2. **Aggressive eps = 0.18** (similarity ≥ 0.82). Tight threshold
   keeps only records that are clearly distinct on attrs.

**Local dry-run**: 42 → 24 (18 removed, reduction 0.429). More
aggressive than iter_26's 9 but should push `dedup_miss_rate` under
0.05.

**Trade-off**: e2e_retention drops to 0.48 (24/50). We lose ~40% of
records, but they're the redundant ones. If the gate passes, this
validates semantic dedup as the promote mechanism.

**Alternative considered**: multi-level or LSH-based. Not attempted;
cuml K-means + raw cosine at n=50 is plenty fast and the signature
choice (title_attrs only) is where the leverage is.
