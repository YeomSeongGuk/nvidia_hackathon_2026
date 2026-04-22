# Stage 1 Quantitative Probe

(no-LLM deterministic metrics; LLM judges are separate)

## Pipeline volume

| stage | n | retention vs prev |
|---|---|---|
| 1.0   seed      | 50 | — |
| 1.1   synthetic | 50 | — |
| 1.1.5 deduped   | 50 | reduction=0.0 |
| 1.2   processed | 0 | retention=0.0 |
| e2e retention (1.2/1.0): **0.0** | | |

## Stage 1.1 — synthetic review content

### Title health
- length p50 / p90 / p99 / max: 29 / 839 / 938 / 976
- reasoning-leak markers (→ / 글자 / newline / 다시 조정): **0.38**
- newline-only subset: 0.38

### Attribute diversity
- color_unique: 6 | top-2 share: **0.76** | 화이트+블랙 share: 0.0
- style_unique: 10 | top-1 ('클래식'): **0.34**
- size_unique: 8 | suspicious (non-apparel): **0.08**

### Rating distribution
- histogram: `{1: 12, 2: 17, 4: 3, 5: 18}`
- rating_3_share: **0.0**  (promote bar: > 0)
- raw_text length p50 / p90 / max: 108 / 195 / 335

## Stage 1.0 — seed
- rating_hist: `{1: 10, 2: 16, 4: 3, 5: 21}`
- rating_3_share: 0.0
