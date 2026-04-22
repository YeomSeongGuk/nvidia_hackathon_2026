# Stage 2 Quantitative Probe

(no-LLM deterministic metrics; LLM judges are separate)

## Pipeline volume

| stage | rows |
|---|---|
| 2.1 extract | 42 |
| 2.1.5 deduped | 16 |
| 2.2 clusters | 15 |
| 2.3 analyzed | 14 |
| 2.4 expanded | 14 |

## Stage 2.1.5 — semantic dedup
- retention: **0.381**
- removed: 26
- avg cosine of kept: 0.7174
- selected threshold: 0.75
- signature builder: signature_combo
- mode: active

## Stage 2.2 — canonicals
- canonical_count: **15** (of which '일반' excluded = 14)
- canonical_hangul_pure_rate: 0.929
- canonical_suffix_compliance_rate: **0.571**  (promote ≥ 0.80)
- canonical_non_fashion_rate: **0.071**  (promote ≤ 0.05)
- evidence_one_count: 13
- names: `['주말룩', '출근복', '해질녘', '주점', '중식당룩', '풍경사진', '산책룩', '수락산 드라이브', '등산복', '주짓수', '주말나들이', '운전복', '민요룩', '등산복']`

## Stage 2.3 — aggregated attrs
- avg_attrs_per_intent: 2.57
- duplicate_value_count: **0**  (promote ≤ 2)

## Stage 2.4 — expanded queries
- query_dedup_ratio: **1.0**  (promote ≥ 0.95)
- query_repeat_within_intent_count: 0
- query_avg_length_chars: 24.2
- query_non_hangul_chars_rate: 0.0  (promote ≤ 0.01)
- garbled_count: **0**  (promote = 0)
- canonical_repeat_rate: 0.0  (promote ≤ 0.10)
