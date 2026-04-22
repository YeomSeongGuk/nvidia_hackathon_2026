# Stage 1 Quantitative Probe

(no-LLM deterministic metrics; LLM judges are separate)

## Pipeline volume

| stage | n | retention vs prev |
|---|---|---|
| 1.0   seed      | 0 | — |
| 1.1   synthetic | 50 | — |
| 1.1.5 deduped   | 50 | reduction=0.0 |
| 1.2   processed | 1 | retention=0.02 |
| e2e retention (1.2/1.0): **None** | | |

## Stage 1.1 — synthetic review content

### Title health
- length p50 / p90 / p99 / max: 30 / 828 / 866 / 888
- reasoning-leak markers (→ / 글자 / newline / 다시 조정): **0.34**
- newline-only subset: 0.34

### Attribute diversity
- color_unique: 9 | top-2 share: **0.68** | 화이트+블랙 share: 0.68
- style_unique: 4 | top-1 ('캐주얼'): **0.88**
- size_unique: 8 | suspicious (non-apparel): **0.08**

### Rating distribution
- histogram: `{1: 8, 2: 14, 4: 10, 5: 18}`
- rating_3_share: **0.0**  (promote bar: > 0)
- raw_text length p50 / p90 / max: 106 / 185 / 265

## Stage 1.0 — seed
- rating_hist: `None`
- rating_3_share: None
