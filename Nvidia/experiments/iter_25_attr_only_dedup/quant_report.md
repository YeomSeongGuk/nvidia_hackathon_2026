# Stage 1 Quantitative Probe

(no-LLM deterministic metrics; LLM judges are separate)

## Pipeline volume

| stage | n | retention vs prev |
|---|---|---|
| 1.0   seed      | 50 | — |
| 1.1   synthetic | 43 | — |
| 1.1.5 deduped   | 31 | reduction=0.279 |
| 1.2   processed | 31 | retention=1.0 |
| e2e retention (1.2/1.0): **0.62** | | |

## Stage 1.1 — synthetic review content

### Title health
- length p50 / p90 / p99 / max: 22 / 30 / 30 / 30
- reasoning-leak markers (→ / 글자 / newline / 다시 조정): **0.0**
- newline-only subset: 0.0

### Attribute diversity
- color_unique: 8 | top-2 share: **0.512** | 화이트+블랙 share: 0.349
- style_unique: 8 | top-1 ('캐주얼'): **0.512**
- size_unique: 8 | suspicious (non-apparel): **0.116**

### Rating distribution
- histogram: `{1: 6, 2: 12, 3: 10, 4: 6, 5: 9}`
- rating_3_share: **0.233**  (promote bar: > 0)
- raw_text length p50 / p90 / max: 160 / 201 / 260

## Stage 1.0 — seed
- rating_hist: `{1: 10, 2: 16, 4: 3, 5: 21}`
- rating_3_share: 0.0
