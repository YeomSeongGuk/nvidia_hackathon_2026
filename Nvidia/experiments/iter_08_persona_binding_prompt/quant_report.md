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
- length p50 / p90 / p99 / max: 26 / 866 / 891 / 892
- reasoning-leak markers (→ / 글자 / newline / 다시 조정): **0.28**
- newline-only subset: 0.28

### Attribute diversity
- color_unique: 8 | top-2 share: **0.72** | 화이트+블랙 share: 0.72
- style_unique: 6 | top-1 ('캐주얼'): **0.88**
- size_unique: 4 | suspicious (non-apparel): **0.0**

### Rating distribution
- histogram: `{1: 12, 2: 17, 4: 3, 5: 18}`
- rating_3_share: **0.0**  (promote bar: > 0)
- raw_text length p50 / p90 / max: 137 / 210 / 277

## Stage 1.0 — seed
- rating_hist: `{1: 10, 2: 16, 4: 3, 5: 21}`
- rating_3_share: 0.0
