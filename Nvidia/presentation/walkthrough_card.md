# Walk-through Check Card — NVIDIA Skill × Problem Map

**Context**: 10 teams in 15 min → **~1.5 min per team**, rapid check-in
format. This card is one page — reviewer points, you answer.

**Keep on table, face-up. Do not page through.**

---

## Elevator  `(10 s · ~30 words)`

> Korean fashion shoppers search in **situations** — *"wedding guest
> outfit", "screen-golf wear"*. The catalog metadata only knows
> **material, fit, color**. Two-language gap. We mine the bridge from
> review data using the NeMo stack.

---

## NVIDIA Skill × Problem Map  `(60–80 s · skim & point)`

| NVIDIA Skill | Problem it solves | How we applied it |
|---|---|---|
| **NeMo Data Designer** | Korean fashion review corpus is small & noisy — not enough signal for direct mining | Synthetic expansion via per-row LLM prompts; **5 497 synth reviews** generated from 10 K real seeds |
| **Korean Personalized Persona**  *(Data Designer feature)* | Generic "user" prompts produce homogeneous TPO coverage — only the head-5 intents surface | **7-field Korean persona** (age · sex · occupation · province · district · character · hobbies) anchors every synth row. Unlocked long-tail TPOs like **스크린골프, 필라테스 레이어, 분식룩** |
| **NeMo Curator** | 7-substage curation pipeline (synth → dedup → filter → extract → cluster → aggregate → expand) needs clean boundaries so each stage can iterate independently | Stage 1 (synth / dedup / filter) + Stage 2 (extract / cluster / aggregate / expand) both follow Curator idioms; enabled our 23-iter improvement loop |
| **Nemotron-Super 120B FP8** | Korean TPO nuance (존댓말 · 반말 · 은어) needs strong reasoning without fine-tuning budget | vLLM serving on Brev H100 NVL × 2. Critical gotcha: `enable_thinking=False` extra_body for structured JSON — **14.6 % extraction failures → 0 %**, 3.5× throughput |
| **Brev H100 NVL × 2** | FP8 inference throughput at hackathon scale | 10 K docs → 260 canonical intents in minutes. Made our **13-minute-per-iter loop** tractable |

---

## Headline Result  `(10 s · ~25 words)`

> **260 canonical TPO intents · 1 300 natural-language queries ·
> 8 / 10 promote gates passed. Stage 2 iteration loop running now.**

---

## If the reviewer pauses on a row  `(~30 s backup answers)`

- **"Single most NVIDIA-dependent piece?"** → Persona-conditioned Data
  Designer. Without it we'd be stuck with the top-5 head TPOs; long
  tail wouldn't surface.
- **"Why Nemotron-Super?"** → Korean reasoning + FP8 throughput on a
  hackathon clock. Reasoning-mode fix is a one-liner; happy to share.
- **"Show me it running?"** → Demo is next — Stage 2 pipeline
  end-to-end on sample queries.

---

## Physical delivery tips

- Carry this card face-up on the demo laptop or printed half-sheet.
- **Point to the row the reviewer is looking at** rather than
  summarizing the whole table. Table is visual load; you are voice.
- **Result line is non-negotiable** — always deliver the "260 · 1 300 ·
  8/10" trio, even if time is tight.
- If the reviewer leaves at 1:00, that's a win — card did its job.
