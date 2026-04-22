# Stage 2 Quantitative Probe

(no-LLM deterministic metrics; LLM judges are separate)

## Pipeline volume

| stage | rows |
|---|---|
| 2.1 extract | 42 |
| 2.1.5 deduped | 33 |
| 2.2 clusters | 21 |
| 2.3 analyzed | 21 |
| 2.4 expanded | 21 |

## Stage 2.1.5 — semantic dedup
- retention: **0.786**
- removed: 9
- avg cosine of kept: 0.6982
- selected threshold: 0.75
- signature builder: full
- mode: active

## Stage 2.2 — canonicals
- canonical_count: **21** (of which '일반' excluded = 20)
- canonical_hangul_pure_rate: 1.0
- canonical_suffix_compliance_rate: **0.45**  (promote ≥ 0.80)
- canonical_non_fashion_rate: **0.05**  (promote ≤ 0.05)
- evidence_one_count: 15
- names: `['주말룩', '주말데이트', '풍경사진', '등산복', '산책', '중식당룩', '출근복', '목욕복', '데일리룩', '해질녘산책', '주점', '배드민턴', '잠옷', '주말나들이', '홈캠', '드라이브룩', '주짓수', '민요룩', '운전복', '여름원피스']`

## Stage 2.3 — aggregated attrs
- avg_attrs_per_intent: 3.0
- duplicate_value_count: **0**  (promote ≤ 2)

## Stage 2.4 — expanded queries
- query_dedup_ratio: **1.0**  (promote ≥ 0.95)
- query_repeat_within_intent_count: 0
- query_avg_length_chars: 25.4
- query_non_hangul_chars_rate: 0.01  (promote ≤ 0.01)
- garbled_count: **0**  (promote = 0)
- canonical_repeat_rate: 0.0  (promote ≤ 0.10)
