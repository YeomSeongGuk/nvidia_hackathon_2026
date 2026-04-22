# Stage 1 Quantitative Probe

(no-LLM deterministic metrics; LLM judges are separate)

## Pipeline volume

| stage | n | retention vs prev |
|---|---|---|
| 1.0   seed      | 50 | — |
| 1.1   synthetic | 44 | — |
| 1.1.5 deduped   | 44 | reduction=0.0 |
| 1.2   processed | 44 | retention=1.0 |
| e2e retention (1.2/1.0): **0.88** | | |

## Stage 1.1 — synthetic review content

### Title health
- length p50 / p90 / p99 / max: 15 / 29 / 30 / 30
- reasoning-leak markers (→ / 글자 / newline / 다시 조정): **0.0**
- newline-only subset: 0.0

### Attribute diversity
- color_unique: 7 | top-2 share: **0.5** | 화이트+블랙 share: 0.409
- style_unique: 7 | top-1 ('캐주얼'): **0.477**
- size_unique: 9 | suspicious (non-apparel): **0.091**

### Rating distribution
- histogram: `{1: 6, 2: 8, 3: 11, 4: 11, 5: 8}`
- rating_3_share: **0.25**  (promote bar: > 0)
- raw_text length p50 / p90 / max: 147 / 171 / 236

## Stage 1.0 — seed
- rating_hist: `{1: 10, 2: 16, 4: 3, 5: 21}`
- rating_3_share: 0.0
