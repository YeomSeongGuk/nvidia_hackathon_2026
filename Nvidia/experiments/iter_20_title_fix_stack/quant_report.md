# Stage 1 Quantitative Probe

(no-LLM deterministic metrics; LLM judges are separate)

## Pipeline volume

| stage | n | retention vs prev |
|---|---|---|
| 1.0   seed      | 50 | — |
| 1.1   synthetic | 34 | — |
| 1.1.5 deduped   | 34 | reduction=0.0 |
| 1.2   processed | 34 | retention=1.0 |
| e2e retention (1.2/1.0): **0.68** | | |

## Stage 1.1 — synthetic review content

### Title health
- length p50 / p90 / p99 / max: 16 / 23 / 30 / 30
- reasoning-leak markers (→ / 글자 / newline / 다시 조정): **0.0**
- newline-only subset: 0.0

### Attribute diversity
- color_unique: 9 | top-2 share: **0.559** | 화이트+블랙 share: 0.206
- style_unique: 6 | top-1 ('캐주얼'): **0.559**
- size_unique: 6 | suspicious (non-apparel): **0.029**

### Rating distribution
- histogram: `{1: 8, 2: 7, 3: 7, 4: 6, 5: 6}`
- rating_3_share: **0.206**  (promote bar: > 0)
- raw_text length p50 / p90 / max: 143 / 167 / 227

## Stage 1.0 — seed
- rating_hist: `{1: 10, 2: 16, 4: 3, 5: 21}`
- rating_3_share: 0.0
