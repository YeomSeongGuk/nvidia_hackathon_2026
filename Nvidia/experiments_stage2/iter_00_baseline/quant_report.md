# Stage 2 Quantitative Probe

(no-LLM deterministic metrics; LLM judges are separate)

## Pipeline volume

| stage | rows |
|---|---|
| 2.1 extract | 42 |
| 2.1.5 deduped | 42 |
| 2.2 clusters | 11 |
| 2.3 analyzed | 11 |
| 2.4 expanded | 11 |

## Stage 2.1.5 — semantic dedup
- retention: **1.0**
- removed: 0
- avg cosine of kept: None
- selected threshold: 0.9
- signature builder: full
- mode: pass_through

## Stage 2.2 — canonicals
- canonical_count: **11** (of which '일반' excluded = 10)
- canonical_hangul_pure_rate: 1.0
- canonical_suffix_compliance_rate: **0.7**  (promote ≥ 0.80)
- canonical_non_fashion_rate: **0.0**  (promote ≤ 0.05)
- evidence_one_count: 5
- names: `['일상', '홈웨어', '외출복', '산책룩', '등산복', '주점', '출근복', '여름원피스', '민요룩', '주짓수복']`

## Stage 2.3 — aggregated attrs
- avg_attrs_per_intent: 4.09
- duplicate_value_count: **0**  (promote ≤ 2)

## Stage 2.4 — expanded queries
- query_dedup_ratio: **1.0**  (promote ≥ 0.95)
- query_repeat_within_intent_count: 0
- query_avg_length_chars: 23.7
- query_non_hangul_chars_rate: 0.0  (promote ≤ 0.01)
- garbled_count: **0**  (promote = 0)
- canonical_repeat_rate: 0.0  (promote ≤ 0.10)
