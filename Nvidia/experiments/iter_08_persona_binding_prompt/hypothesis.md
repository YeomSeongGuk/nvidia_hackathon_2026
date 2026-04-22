# H8: `persona_binding_prompt` (iter_08)

**Parent**: `iter_00_baseline`
(`stage_1_1.avg_persona_reflection = 3.62`,
 `persona_drift` fires on 19/50 records,
 `rating_sentiment_consistent_rate = 0.78`)

**Hypothesis**: Baseline review prompt asks for "페르소나의 성격, 취미,
직업을 반영한 어투" abstractly. Nemotron interprets loosely — often
references ONE persona field ("산책길에") but not multiple, and many
reviews could plausibly be written by any persona. The 19 records
flagged `persona_drift` are these generic reviews. Forcing **2+
specific persona field citations** and showing two good examples
should push persona_reflection up and persona_drift down.

**Change**: Rewrite `review_prompt` in `run_data_designer_stage()`:

- make the instruction explicit: "반드시 다음 중 2개 이상을 구체적으로
  언급하라: 취미 / 직업 / 거주지 / 연령대 감성"
- show 2 good examples (one 40대 분당, one 70대 영주) that cite both
  hobby AND occupation/province
- widen review length 20-80 → 50-150 to allow room for the citations
- keep rating-sentiment rule explicit (1-2점 부정, 4-5점 긍정) so
  `rating_sentiment_consistent_rate` doesn't regress

Expected movement:

- `stage_1_1.avg_persona_reflection`: 3.62 → ≥ 4.0.
- `stage_1_1.failure_modes.persona_drift`: 19/50 → ≤ 8/50.
- `stage_1_1.rating_sentiment_consistent_rate`: 0.78 → ≥ 0.85.
- Side effect `stage_1_1.failure_modes.length_violation` may rise
  (widened length envelope), but judges evaluate against the prompt,
  so they should adapt.

Non-goals:
- No title change (H1/H2/H3).
- No attr change (H5).
- Stage 1.2 still broken (H9).
