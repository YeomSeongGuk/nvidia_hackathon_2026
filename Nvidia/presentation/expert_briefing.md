# Expert Briefing — 10 min 1:1 Before Demo

**Format**: conversational, paper-in-hand or on-laptop reference.
**Audience**: NVIDIA or hackathon technical expert.
**Goal**: technical depth behind the 5-min pitch, invite substantive questions.

Six sections, ~90 s each. If the expert latches onto one, stay there
and drop a later section — pitch has already covered the story arc.

---

## 1 · The Problem We Solve  `(~60 s)`

A Korean fashion shopper searches with intent — *"wedding guest outfit
for tomorrow"*, *"office look for first-day-of-work"*, *"daily screen-golf
wear"*. Catalog metadata only knows **material, fit, color**. That's a
**two-language gap**, not a ranking problem.

Two patterns dominate existing solutions and both fail here:

1. **Keyword/BM25** — the TPO tokens don't exist in product text.
2. **End-to-end semantic search (BGE/E5 over titles + descriptions)** —
   titles are marketing copy, not customer language; similarity scores
   collapse to attribute repetition, not intent matching.

Our bet: the bridge already exists in **review text**. Reviews are the
one corpus where shoppers use TPO language alongside attribute
language, in the same sentence. We just need to **curate** that bridge
explicitly — extract canonical TPO intents, aggregate their attribute
signatures, make it queryable.

> **Key framing**: this is a data curation problem solved with LLMs,
> not a retrieval-model fine-tuning problem.

---

## 2 · Architecture at a Glance  `(~2 min)`

Two stages, five sub-stages, one iteration loop.

```
[Korean review corpus]   10 000 docs (Musinsa + Naver + YouTube)
        │
        ▼
Stage 1  ▌ NeMo Curator pipeline on Brev H100
  1.0    ▌ seed quality gate          ← judge
  1.1    ▌ synth (NeMo Data Designer  + Korean Persona)
  1.1.5  ▌ dedup                      ← probe
  1.2    ▌ filter + format             ← judge
        │                               5 497 curated rows
        ▼
Stage 2  ▌ still Curator-flavored, LLM calls via vLLM
  2.1    ▌ per-doc intent + attr extract    ← judge
  2.2    ▌ embed (BGE-M3) + agglomerative   ← judge
         ▌ cluster + LLM refine + canonical
         ▌ naming + cross-merge
  2.3    ▌ weighted attribute aggregation   ← judge
  2.4    ▌ natural-language query expansion ← judge
        │                               260 canonical TPO intents ×
        │                               ~5 queries each = 1 300 queries
        ▼
[Semantic Bridge output, ready to serve catalog matching]
```

Three infrastructure boxes to know:

- **coupang** (Brev H100 NVL × 2): vLLM serves Nemotron-Super 120B FP8.
- **Friendli serverless**: hosts the three foreign judges for every
  stage that has a `judge` arrow in the diagram above.
- **Local dev box**: orchestrates iter_run.py, pulls outputs, assembles
  metrics.json + judge_report.md per iteration.

Every iteration is a **folder**, every folder is a **commit**,
every commit has a **judge report** inside.

---

## 3 · Three Critical Technical Choices  `(~3 min)`

If the expert only remembers three things, I want these.

### 3.1 `enable_thinking=False` on Nemotron-Super  `(~45 s)`

Nemotron-Super/Nano is a reasoning model — by default the `content`
field comes back empty and the full answer lives in a separate
`reasoning` field. Every first-time integrator hits this. In our
hackathon run it initially caused:

- 14.6 % failure rate on structured JSON extraction (parser couldn't
  find the answer).
- 3.5× wasted output tokens on reasoning we didn't need.

Fix is a single line on the client:

```python
extra_body = {"chat_template_kwargs": {"enable_thinking": False}}
```

Applied to both the ModelProvider and the per-request params. Result:
**3.5× fewer output tokens, 1.9× faster, 0 % extraction failures.**
Worth knowing for anyone else using Nemotron-Super for structured tasks.

### 3.2 Korean Personalized Persona over "generic user"  `(~60 s)`

The Data Designer synthetic step conditions on a **seven-field Korean
persona** per synthesized review:

| field | example |
|---|---|
| age | 28 |
| sex | female |
| occupation | office worker |
| province | 부산광역시 |
| district | 해운대구 |
| character | pragmatic, budget-conscious |
| hobbies | hiking, screen golf, baking |

Not cosmetic. Two concrete effects:

1. **Long-tail coverage**: screen golf and Pilates layering showed up
   because personas with those hobbies were seeded. Without the hobby
   axis the LLM stayed around the 5–10 most common TPOs.
2. **Persona reflection score**: tri-judge `persona_reflection` went
   from 3.62 → 4.66 on a 1-5 scale once the persona was **structurally
   bound in the prompt**, not passively mentioned (H8 win). This is
   the single largest persona-faithfulness jump in the 23 iters.

### 3.3 Wisdom of the Crowd with three foreign judges  `(~75 s)`

LLM-as-Judge is the default hackathon approach. We deliberately did
*not* let Nemotron judge its own output. Three independent models on
Friendli serverless:

| judge | vendor | why in the panel |
|---|---|---|
| GLM-5.1 | Z.AI | strong Korean, distinct training data |
| DeepSeek-V3.2 | DeepSeek | excellent long-context reasoning |
| Qwen3-235B-A22B | Alibaba | fast, high-agreement scoring |

Every judged metric reported as `{glm, deepseek, qwen3, mean, range}`.
The promotion decision is **only on the mean**, but we block auto-promote
if `range > 0.15` on a headline metric — that's `HIGH_VARIANCE`, and
the reviewer has to decide manually.

Concrete payoff: three times during the 23-iter run, one judge would
have approved an iter that the other two caught as regressed. Because
promote required majority + variance check, we didn't commit those
regressions.

> **This is the core insight I'd want to leave with the expert.**
> "LLM as judge" is not a single decision — it's a *panel*. The
> panel's disagreement carries signal, not just its agreement.

---

## 4 · Iteration Loop — Mechanics, Not Just Slogans  `(~2 min)`

13 minutes per iteration, end-to-end. That number isn't a goal — it's
what the critical path (vLLM + Friendli) costs for 42–50 docs. The
point is we **ran 23 of them**.

### 4.1 Per-iter folder

```
experiments/iter_NN_<slug>/
├── hypothesis.md         ← what we're testing, 1 paragraph
├── patch.diff            ← minimal code delta vs parent iter
├── pipeline_script.py    ← frozen snapshot so it reruns verbatim
├── metrics.json          ← tri-judge ensemble + quant probes + sha256
├── judge_report.md       ← human-readable judge summary
├── quant_report.md       ← deterministic probes
├── comparison.md         ← delta vs parent iter
└── output/               ← (gitignored) raw JSONL artifacts
```

### 4.2 Promotion protocol

- **Eager stacking**: once an iter clears its promote bar on judge mean,
  the next iter's base includes it automatically.
- **Rollback**: an iter that regresses a previously-passing gate is
  rolled back even if it wins on its target metric. This protocol
  caught H3v2, H3v4, H3v5, H4, H7 — five otherwise-looking-good iters.
- **Negative signal is committed**: falsified hypotheses stay in git.
  If someone re-proposes the same idea six months from now, the
  comparison.md is already there.

### 4.3 The real payoff

What the 23 iters bought us wasn't just the final number. It was:

- 9 **ruled-in** hypotheses we can confidently re-use in new domains.
- 11 **ruled-out** hypotheses with written-down reasons.
- An infrastructure that can keep iterating for free — Stage 2 is
  running on the same driver right now.

---

## 5 · Results + Honest Blockers  `(~90 s)`

### 5.1 Headline numbers (Stage 1, best = iter_21_dedup_v2)

- **8 / 10 promote gates** (from 1 / 10 at baseline).
- `attribute_grounded_rate`: 0.467 → 0.99 (H11 win — biggest single
  delta in the run).
- `title_reasoning_leak`: 0.473 → 0.013 (H3 + H3v3).
- `persona_reflection`: 3.62 → 4.66 (H8).
- `fashion_rate`: 0.853 → 0.977 (H12 post-gen filter).
- `stage_1_2.retention`: 0.0 → 1.0 (H9 structural — the original
  `NonAlphaNumericFilter` dropped every Korean row).

### 5.2 Two blockers we didn't solve (and why)

**`stage_1_0.avg_text_quality ≥ 3.5`** — seed corpus is structurally
low quality. All three judges score raw Naver reviews in the 2.7–2.9
range regardless of sampling. Clearing this gate requires a different
seed corpus (e.g. Musinsa only + curated 무신사 매거진), which was
out of scope for a hackathon.

**`stage_1_1_5.dedup_miss_rate ≤ 0.05`** — pure-Python Jaccard didn't
fire a single removal at any threshold, because the synthetic reviews
have enough textual variety that character bigrams stay <0.40 similar
even for semantic near-dupes. **This is exactly the case for semantic
dedup**, which is queued now in Stage 2.1.5 (SD-series). The honest
answer if asked: we deferred the cudf+SemDedup install because it
would compete with vLLM for GPU memory.

### 5.3 Stage 2 is running

Stage 2 iteration loop started tonight. Uses the same driver shape,
adds SD-series (semantic dedup) as iter_01. Results will land in the
deck before demo.

---

## 6 · Where This Goes Next  `(~45 s)`

**Production path**:

1. Re-pin Stage 1 input to a bigger seed corpus (100 K → 1 M reviews).
2. Replace the pure-Python dedup with real semantic dedup on SemDedup
   (the cudf install we deferred).
3. Serve the 260 canonicals as an **index** the ranking layer can join
   against — either via direct attribute filter, or as features into
   an existing retrieval model.
4. Keep the iteration loop alive — every quarter, rerun on new review
   cohorts, diff the canonical set.

**Hackathon honest reflection**:

- If I had another week, first move is **more personas**, specifically
  covering shopper archetypes absent from Naver (e.g. 시니어, 10대,
  플러스사이즈 쇼퍼).
- Second move is the **Option A networking** between coupang and
  coupang2 so Stage 2.2 doesn't need the phase-split (this is a
  plumbing task, not a research one).
- Third move is **learned dedup thresholds** per cluster-density
  regime — fixed cosine 0.9 is a starting point, not an answer.

---

## Likely Expert Questions — Quick Cheat Sheet

| Q | Short answer | Slide reference |
|---|---|---|
| "How did you validate the 260 canonicals?" | tri-judge on `coherent_rate`, `avg_canonical_fit`, `non_korean_canonical_count` — see §4b of Stage 2 PLAN | Slide 6 / §3.3 here |
| "Why not fine-tune Nemotron?" | Persona + prompt + enable_thinking fix got us to 8/10 gates without any weight updates. FT would add ops cost without clearing the remaining two structural blockers | §3 here |
| "Why three judges, why those three?" | Independence from Nemotron (no self-eval), distinct training lineages, all three handle Korean well. Diversity > strongest-single-judge. | §3.3 |
| "What's the iter cycle time and cost?" | ~13 min wall-clock; ~200 Friendli calls per Stage 2 iter (~3-4 M tokens) — well within hackathon quota | §4 |
| "How do you stop the iter loop?" | Three stop conditions: all gates pass / budget (12 h or 15 iters) / blocker detected. `HIGH_VARIANCE` blocks auto-promote but not continuation | §4.2 |
| "Did judges ever disagree meaningfully?" | Yes, 3× in the run — caught by the `range > 0.15` rule. Each time we pulled the raw judge outputs and two out of three had caught a regression the third missed | §3.3 |
| "What's the single most reusable piece of this work?" | The **iteration loop + eval report structure**. The rest is domain-specific, the loop transfers to any LLM curation task | §4 |

---

## Delivery notes

- **Carry the deck open alongside this document.** Refer to slide
  numbers when an expert asks for visuals.
- **Don't read sequentially.** Use the section headers as jumping-off
  points. If the expert asks about judges, go to §3.3 directly.
- **Stop at 9 minutes wall-clock.** Leave 60 s for "any last questions
  before the demo?" — that's when the real dialogue happens.
