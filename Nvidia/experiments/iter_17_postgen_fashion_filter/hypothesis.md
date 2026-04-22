# H12: post-gen fashion filter (iter_17)

**Parent**: `iter_16_tighter_leak_regex`

**Hypothesis**: Even with a tighter seed filter (H7v2) and a
structured title postprocessor (H3v3), ~5-10% of synthetic records
end up with product_titles like "신발 정리함 2단 수납함" because:
1. The seed review mentioned 신발 (covered by include keyword) and
   also 정리함 (exclusion). Our exclude list isn't perfect.
2. Data Designer's LLM sometimes invents non-fashion titles from a
   fashion seed (surprisingly).

**H12 change**: after the title postprocessor runs, drop any synthetic
record whose `product_title` contains a non-fashion keyword OR equals
the "패션 상품" fallback. This reduces the output batch size below 50
but keeps only genuine fashion records.

**Exclude list** (post-gen): 정리함, 정리대, 수납함, 보관함, 신발장,
옷걸이, 행거, 선반, 세탁볼, 세탁망, 세제, 린스, 탈취제, 향수, 드라이기,
고데기, 면도기, 기저귀, 13개월, 아기옷, 베이비.

**Expected movement vs iter_16**:

- `stage_1_1.fashion_rate`: 0.867 → ≥ 0.95 (removed the tail of
  non-fashion).
- `stage_1_1.failure_modes.non_fashion_item`: ≤ 3.
- `stage_1_2.fashion_rate`: 0.927 → ≥ 0.95 (propagates).
- `stage_1_1.n_evaluated`: 50 → ~45 (drop ~5 records).
- `e2e.output_rows_by_stage`: [50, ~45, ~45, ~45].

This iter may show passes on `stage_1_1.fashion_rate_ge_0.95` and
`stage_1_2.fashion_rate_ge_0.95` — two more gates. Combined with the
existing 4/10 that iter_16 held, that would be **6/10 gates** —
closer than we've been.

Remaining blockers: title_leak (0.04), avg_text_quality (2.8), and
dedup_miss_rate (0.147 — H10 territory).
