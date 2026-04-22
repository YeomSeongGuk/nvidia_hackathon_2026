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
- length p50 / p90 / p99 / max: 29 / 869 / 928 / 1015
- reasoning-leak markers (→ / 글자 / newline / 다시 조정): **0.3**
- newline-only subset: 0.3

### Attribute diversity
- color_unique: 7 | top-2 share: **0.74** | 화이트+블랙 share: 0.74
- style_unique: 6 | top-1 ('캐주얼'): **0.9**
- size_unique: 3 | suspicious (non-apparel): **0.0**

### Rating distribution
- histogram: `{1: 9, 2: 12, 4: 3, 5: 26}`
- rating_3_share: **0.0**  (promote bar: > 0)
- raw_text length p50 / p90 / max: 100 / 203 / 347

## Stage 1.0 — seed
- rating_hist: `{1: 9, 2: 15, 4: 3, 5: 23}`
- rating_3_share: 0.0
