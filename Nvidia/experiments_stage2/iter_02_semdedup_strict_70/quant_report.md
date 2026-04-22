# Stage 2 Quantitative Probe

(no-LLM deterministic metrics; LLM judges are separate)

## Pipeline volume

| stage | rows |
|---|---|
| 2.1 extract | 42 |
| 2.1.5 deduped | 26 |
| 2.2 clusters | 15 |
| 2.3 analyzed | 15 |
| 2.4 expanded | 15 |

## Stage 2.1.5 — semantic dedup
- retention: **0.619**
- removed: 16
- avg cosine of kept: 0.6642
- selected threshold: 0.7
- signature builder: full
- mode: active

## Stage 2.2 — canonicals
- canonical_count: **15** (of which '일반' excluded = 14)
- canonical_hangul_pure_rate: 0.929
- canonical_suffix_compliance_rate: **0.643**  (promote ≥ 0.80)
- canonical_non_fashion_rate: **0.0**  (promote ≤ 0.05)
- evidence_one_count: 11
- names: `['주말룩', '외출복', '산책룩', '풍경사진', '출근복', '홈웨어', '데이트룩', '잠옷', '수락산 드라이브', '등산복', '주짓수', '배드민턴', '민요룩', '스포티룩']`

## Stage 2.3 — aggregated attrs
- avg_attrs_per_intent: 2.93
- duplicate_value_count: **0**  (promote ≤ 2)

## Stage 2.4 — expanded queries
- query_dedup_ratio: **1.0**  (promote ≥ 0.95)
- query_repeat_within_intent_count: 0
- query_avg_length_chars: 23.3
- query_non_hangul_chars_rate: 0.013  (promote ≤ 0.01)
- garbled_count: **0**  (promote = 0)
- canonical_repeat_rate: 0.0  (promote ≤ 0.10)
