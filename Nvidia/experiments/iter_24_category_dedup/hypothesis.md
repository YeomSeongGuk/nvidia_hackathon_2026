# H14v4: category-based signature dedup (iter_24)

**Parent**: `iter_17_postgen_fashion_filter`

**Hypothesis**: iter_23's H14v3 used `last_word_of_title + attrs` as a
signature, but that last-word was extremely noisy (titles overflow the
30-char cap and end with junk like "(면소재)", "때,", "불만입") so all
44 records had unique signatures → 0 removals → no dedup fired.

**H14v4 approach**: extract a canonical fashion category by scanning
the title for any of ~50 hand-picked category words (티셔츠, 셔츠,
원피스, 바지, 가방, 토트백, 신발, 스니커즈, …). If found, `(category,
color, style, size)` is the signature. If no category matches, the
signature falls back to `(color, style, size)` alone — which is still
the axis judges use to cluster near-dups.

**Local dry-run on iter_17 data** (predicted effect):
- 44 records → 34 distinct signatures → **10 records removed**
- top duplicate clusters:
  - `토트백|베이지|캐주얼|FREE` x5  (classic mode-collapse cluster)
  - `티셔츠|화이트|캐주얼|M` x3
  - `원피스|네이비|캐주얼|L` x2
  - `티셔츠|아이보리|캐주얼|M` x2
  - `백팩|네이비|캐주얼|FREE` x2
  - `|블랙|스포티|M` x2  (no-category fallback bucket)
- expected `dedup_reduction_rate` = **0.227** (was 0.0 in iter_17)
- expected `dedup_out_count = 34` (was 44)

**Expected movement vs iter_17**:
- `stage_1_1_5.dedup_reduction_rate`: 0.0 → 0.22
- `stage_1_1_5.dedup_miss_rate`: 0.167 → ≤ 0.05 (removes the high-
  severity clusters the tri-judge is flagging)
- `stage_1_2.n`: 44 → 34 (fewer records downstream)
- `stage_1_1.fashion_rate`, `attr_grounded`, `persona`, `rating_3_share`:
  unchanged (dedup doesn't touch Stage 1.1 output measurement)
- `stage_1_2.fashion_rate`, `retention`: should stay ≥ 0.95 / ≥ 0.85
  (dedup removes a random 10 of 44 high-quality records)

**If this works, passing gate count**: iter_17's 6/10 + dedup gate
→ **7/10 stable**. If the dice also fall lucky on title_leak
(sampling variance), could be 8/10 reproducibly.

Non-goals:
- No touch to Stage 1.1 or 1.2. Only the dedup stage changes.
- No attempt to `pip install cudf-cu12` (H10 — still the long-term
  production fix).
