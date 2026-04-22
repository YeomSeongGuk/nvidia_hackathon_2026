# H3v3: tighter leak regex (iter_16)

**Parent**: `iter_13_combo_plus_attr_mention` (NOT iter_15 — iter_15's
H13 Hangul floor dropped short fashion reviews and regressed
fashion_rate).

**Hypothesis**: iter_14 (H3v2) failed because widening cap 30 → 45
opened the door for reasoning leaks. The fix is NOT to widen but to
add MORE regex patterns to H3's leak-stripper while keeping the
30-char hard cap.

**Leak patterns observed in iter_13/14 synthetic titles**:
- `...선물용 29자` — bare trailing digit+자 (no parentheses)
- `...(165cm 키 추천)` — parenthetical size recommendation
- `...(키 165 기준)` — parenthetical style-spec note
- `... 28자` — same as first without parens

**H3v3 changes**:
1. Add `_LEAK_BARE_CHARCOUNT_RE = r"\s+\d+\s*자\s*$"` to catch
   trailing char counts without parentheses.
2. Add `_LEAK_PAREN_SIZE_NOTE_RE` to strip parenthetical annotations
   that contain cm / 키 / 기준 / 추천 / 권장 / size / 사이즈.
3. Add `_MARKDOWN_META_RE` (same as iter_14 H3v2) to kill trailing
   `**수정 사항:**...` blocks.
4. **KEEP** the 30-char hard cap (iter_13's H3 original — widening
   was proven wrong in iter_14).

**Expected movement vs iter_13**:

- `stage_1_1.title_reasoning_leak_rate`: 0.053 → ≤ 0.02 (clean gate pass).
- `stage_1_1.failure_modes.title_reasoning_leak`: ≤ 2.
- `stage_1_1.title_format_ok_rate`: 0.29 → 0.45.
- Other metrics inherited from iter_13 unchanged (attr_grounded,
  persona, rating_3, retention all hold).

Given iter_13's 4/10 gate pass and iter_16's likely +1 on title_leak,
we'd be at 5/10 gates. Still short of promotion, but a clear best
so far.
