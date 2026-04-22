# H7v2 + H13 seed quality (iter_15)

**Parent**: `iter_13_combo_plus_attr_mention` (NOT iter_14 — H3v2 regressed leak rate)

**Hypotheses**:

**H7v2** — stronger, narrower exclude list. iter_07 (H7v1) regressed
fashion_rate 0.853 → 0.787, likely because the v1 exclude list was
too broad (e.g. matched "반려견 가방" on a legitimate bag review).
v2 targets only unambiguously non-fashion items:
- storage: 정리함, 정리대, 수납함, 보관함, 신발장, 옷걸이, 행거
- cleaning: 세탁볼, 세탁망, 세제, 린스, 탈취제
- appliances: 드라이기, 고데기, 면도기
- baby: 기저귀, 13개월, 아기옷, 베이비

**H13** — minimum seed Hangul floor. Analysis of iter_13 seeds shows
several are too short ("좋아요ㅎ", "굿") to provide meaningful context
to Data Designer. Short seeds → vague titles → low `avg_text_quality`.
Floor: ≥ 30 Hangul characters per seed.

**Parent choice**: `iter_13_combo_plus_attr_mention` (not iter_14).
iter_14's H3v2 smarter postprocessor actually regressed
title_reasoning_leak_rate 0.053 → 0.093 because widening 30→45 chars
let reasoning fragments survive that used to be chopped. We revert
to iter_13's H3 (30-char hard cap).

**Changes vs iter_13**:
1. Expand `FASHION_EXCLUDE_KEYWORDS` (H7v2 careful selection).
2. Add `MIN_SEED_HANGUL_CHARS = 30` gate in `extract_seed_data`.

**Expected movement vs iter_13**:

- `stage_1_1.fashion_rate`: 0.87 → ≥ 0.92 (fewer non-fashion seeds
  propagate to synthesis).
- `stage_1_1.failure_modes.non_fashion_item`: 8+ → ≤ 3.
- `stage_1_0.avg_text_quality`: 2.79 → 3.1+ (longer, more substantive
  seeds; may still be below 3.5 gate).
- `stage_1_0.fashion_rate`: 0.87 → 0.92.
- `stage_1_2.fashion_rate`: 0.91 → 0.94.

Other metrics (persona, rating_3, attr_grounded, retention) hold
unchanged (only seed selection changes).
