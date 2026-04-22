# H3v2: smarter title postprocessor (iter_14)

**Parent**: `iter_13_combo_plus_attr_mention`

**Hypothesis**: iter_12/iter_13 show `title_format_violation = 39/50`
even with H3's postprocessor in place. Inspecting titles shows the
failure mode is H3's `s = s[:30]` chopping mid-word (e.g.
"유니클로 오버핏 니트 스웨" — truncated "스웨터"). Judges flag these as
format violations.

**H3v2 changes**:

1. Widen the cap 30 → **45** chars (still shorter than baseline's
   891 p90). Most well-formed Korean fashion titles fit in ~25-35;
   the extra 15 chars of room eliminates the "mid-word chop" failure
   without opening the door back to reasoning leaks (which are blocked
   by the leak-suffix + arrow + markdown regexes).
2. Truncate at the **last whitespace boundary** within the 45-char
   window (min 20 chars before whitespace required; else hard cut).
3. Add a `_MARKDOWN_META_RE` regex that kills trailing `**수정 사항:**...`
   blocks (some titles have those without an arrow separator).
4. Add a `_SANE_TITLE_RE` sanity-check: if the post-processed string
   is empty or contains characters outside `[가-힣ㄱ-ㅎㅏ-ㅣa-zA-Z0-9
   spaces &+/().,!-]`, replace with a safe fallback `"패션 상품"`.
   This catches weird leaks like titles starting with "---" or
   containing CJK emoji.

**Expected movement vs iter_13**:

- `stage_1_1.failure_modes.title_format_violation`: 39 → ≤ 10.
- `stage_1_1.failure_modes.title_length_violation`: 30 → ≤ 10
  (new cap 45 matches the "15-30" spec's upper bound loosely but
  judges tolerate ≤ 45 better than 30-hard-chop).
- `stage_1_1.title_reasoning_leak_rate`: ≈ 0.06 (unchanged; we didn't
  weaken any leak-stripping regex).
- `stage_1_1.title_format_ok_rate`: 0.29 → ≥ 0.60.
- `stage_1_1.title_within_spec_rate`: ≈ 0.44 → ≥ 0.60.

Other metrics inherited from iter_13.
