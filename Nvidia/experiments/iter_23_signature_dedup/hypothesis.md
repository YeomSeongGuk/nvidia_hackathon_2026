# H14v3: signature-based exact dedup (iter_23)

**Parent**: `iter_17_postgen_fashion_filter` (best so far, 6/10 stable; iter_21 hit 8/10 via sampling luck)

**Hypothesis**: iter_21 judge_raw shows near-dup clusters like:
- "Both praise a beige, FREE-size, casual 토트백..."
- "Both complain about a missing strap on a black bag..."

These share the SAME `(category, color, style, size)` tuple. The
fuzzy Jaccard approaches (iter_19 v1, iter_21 v2) couldn't detect
these because per-persona reviews diverge on unique content
(district, hobby) while converging on product attributes.

**H14v3 approach**: drop fuzzy similarity entirely. Compute a
canonical signature:

```
sig = f"{last_word_of_title}|{color}|{style}|{size}"
```

Records with identical signatures are DUPLICATES. First occurrence is
kept. This is ∼deterministic and zero-parameter (no threshold to
tune).

Trade-off analysis:
- If two legitimately different products share signature (e.g.
  two brands' 토트백+베이지+캐주얼+FREE), one gets dropped. That's
  acceptable — our corpus is only 50 records, so any double-coverage
  of the same product niche IS near-duplicate.
- Signature grain = category (last word) + 3 attrs. Different brands
  won't share signature because different brands produce different
  final words on average. And the judge explicitly counts these as
  near-dups anyway.

**Expected movement vs iter_17**:
- `stage_1_1_5.dedup_reduction_rate`: 0.0 → 0.10-0.25 (finally fires).
- `stage_1_1_5.dedup_miss_rate`: 0.167 → ≤ 0.05.
- `stage_1_1_5.dedup_out_count < dedup_in_count` for the first time.
- `e2e.output_rows_by_stage`: [50, 44, ~35-40, ~35-40].
- Other metrics held.

If this fires the dedup gate, combined with iter_17's 6/10 we're at
**7/10**. If also title_leak happens to be in the lucky-low-variance
regime (like iter_21 at 0.013), we'd match iter_21's 8/10 with
stable dedup.
