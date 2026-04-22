# Stage 1 Quantitative Probe

(no-LLM deterministic metrics; LLM judges are separate)

## Pipeline volume

| stage | n | retention vs prev |
|---|---|---|
| 1.0   seed      | 50 | — |
| 1.1   synthetic | 50 | — |
| 1.1.5 deduped   | 50 | reduction=0.0 |
| 1.2   processed | 50 | retention=1.0 |
| e2e retention (1.2/1.0): **1.0** | | |

## Stage 1.1 — synthetic review content

### Title health
- length p50 / p90 / p99 / max: 27 / 30 / 30 / 30
- reasoning-leak markers (→ / 글자 / newline / 다시 조정): **0.0**
- newline-only subset: 0.0

### Attribute diversity
- color_unique: 11 | top-2 share: **0.52** | 화이트+블랙 share: 0.4
- style_unique: 9 | top-1 ('캐주얼'): **0.4**
- size_unique: 9 | suspicious (non-apparel): **0.16**

### Rating distribution
- histogram: `{1: 8, 2: 11, 3: 11, 4: 8, 5: 12}`
- rating_3_share: **0.22**  (promote bar: > 0)
- raw_text length p50 / p90 / max: 174 / 227 / 313

## Stage 1.0 — seed
- rating_hist: `{1: 12, 2: 17, 4: 4, 5: 17}`
- rating_3_share: 0.0
