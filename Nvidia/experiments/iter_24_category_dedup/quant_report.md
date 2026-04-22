# Stage 1 Quantitative Probe

(no-LLM deterministic metrics; LLM judges are separate)

## Pipeline volume

| stage | n | retention vs prev |
|---|---|---|
| 1.0   seed      | 50 | — |
| 1.1   synthetic | 43 | — |
| 1.1.5 deduped   | 38 | reduction=0.116 |
| 1.2   processed | 38 | retention=1.0 |
| e2e retention (1.2/1.0): **0.76** | | |

## Stage 1.1 — synthetic review content

### Title health
- length p50 / p90 / p99 / max: 23 / 29 / 30 / 30
- reasoning-leak markers (→ / 글자 / newline / 다시 조정): **0.0**
- newline-only subset: 0.0

### Attribute diversity
- color_unique: 6 | top-2 share: **0.488** | 화이트+블랙 share: 0.442
- style_unique: 7 | top-1 ('캐주얼'): **0.442**
- size_unique: 10 | suspicious (non-apparel): **0.116**

### Rating distribution
- histogram: `{1: 8, 2: 10, 3: 8, 4: 8, 5: 9}`
- rating_3_share: **0.186**  (promote bar: > 0)
- raw_text length p50 / p90 / max: 154 / 211 / 294

## Stage 1.0 — seed
- rating_hist: `{1: 10, 2: 16, 4: 3, 5: 21}`
- rating_3_share: 0.0
