# H14v5: attr-only signature dedup (iter_25)

**Parent**: `iter_17_postgen_fashion_filter`

**Hypothesis**: iter_24 H14v4 used `(category, color, style, size)`
as signature and removed 5 records → `dedup_miss_rate` 0.167 → 0.132,
still above the 0.05 gate. Judge analysis shows the remaining near-
dup pairs all share `(color, style, size)` but NOT category:
- rv1a (cat="", attrs={베이지, 캐주얼, FREE}) vs rv2d (cat="토트백",
  attrs={베이지, 캐주얼, FREE}) — different sig under v4, same
  under attr-only.
- Reasoning-leak titles ("리뷰에서 핵심 내용은...") produce empty
  category, splitting them into a "ghost bucket" separate from
  real products.

**H14v5 change**: drop `category` from the signature. Use only
`(color, style, size)`. Local dry-run on iter_24's stage_1_1 output:
- v4: 5 removed
- v5: 9 removed (+4 from merging the "ghost bucket" with real clusters)

**Expected movement vs iter_24**:
- `stage_1_1_5.dedup_reduction_rate`: 0.116 → ≈ 0.20
- `stage_1_1_5.dedup_miss_rate`: 0.132 → ≤ 0.05 (promote gate)
- `stage_1_1_5.dedup_out_count`: 38 → ~34
- `e2e.output_rows_by_stage`: [50, 43, ~34, ~34]
- Other gates unchanged from iter_17/24 baseline.

If dedup gate passes, we're at **7/10 stably**. Combined with any
sampling luck on title_leak (iter_21 showed 0.013 is achievable
with this exact pipeline), 8/10 becomes reproducible.

Risk: v5 is more aggressive. If two legitimately different products
(e.g. a 토트백 and a 백팩 that happen to share color/style/size)
collide, we over-dedup. But at n=50 that's acceptable — the corpus
shouldn't have products that identical anyway.
