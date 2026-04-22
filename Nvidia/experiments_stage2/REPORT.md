# Stage 2 Iteration Report

**Branch**: `main` (Stage 2 work merged from
`experiment/stage2-iterative-improvement` at `43ea760`)
**Iterations completed**: 6 — `iter_00_baseline`, `iter_00a_semdedup_probe`,
`iter_01..04` (see §3)
**Best iteration**: **`iter_04_canonical_suffix_enforce`** — 12/16 §6
gates passing (baseline was 9/16)
**Date**: 2026-04-22
**Stop reason**: time budget exhausted; C2/C3/E/A/X/combo series not
attempted.

---

## 1. Executive summary

Starting from `iter_00_baseline` (9/16 §6 gates), we explored the
PLAN.md §5 hypothesis queue — **SD-series then pruned, skipped C2/C3,
stopped before E/A/X**. The single commit that moved the needle was
`iter_04 C1 canonical_suffix_enforce` which **crossed all three Stage
2.2 gates** (`coherent_rate`, `avg_canonical_fit`, `duplicate_pairs_found`)
by patching `CANONICAL_SYSTEM` to require a fashion-suffix ending.

Concretely, between iter_00 and iter_04:

| metric | base | iter_04 | Δ | gate |
|---|---|---|---|---|
| stage_2_2.coherent_rate | 0.80 | **0.96** | +0.16 | fail → **PASS** |
| stage_2_2.avg_canonical_fit | 3.633 | **4.623** | +0.99 | fail → **PASS** |
| stage_2_2.duplicate_pairs_found | 1.33 | **0.33** | -1.00 | fail → **PASS** |

Five §6 gates still fail at stop:

1. `stage_2_1.avg_intent_groundedness ≥ 4.0` — iter_04 is 2.84,
   largest remaining gap. Unaddressed; E-series (`extract_general_wear_strict`
   / `extract_attr_decomposition`) was queued but not run.
2. `stage_2_3.avg_overall_usefulness ≥ 4.0` — iter_04 is 2.19 (worse
   than baseline's 2.955 after C1 shrank `canonical_count` 11→9).
   Would be fixed by A2 (`quality_score_log_curve`) or A3 (`topk_by_evidence`).
3. `stage_2_4.avg_overall_usefulness ≥ 4.0` — iter_04 is 3.89, one
   click from passing. X1–X2 prompt patches expected to close.
4. `stage_2_1.attribute_concrete_material ≥ 0.80` (quant probe) —
   iter_04 is 0.12. E4 (`extract_keyword_rubric`) targets this.
5. `stage_2_2.canonical_suffix_compliance_rate ≥ 0.80` (quant) —
   iter_04 is 0.625. **C1's own headline metric actually regressed**
   (0.70 → 0.625) despite the prompt patch; the LLM introduced new
   failures (`여름원피스`, `루즈핏티`, `일하며 등산`) treating product-
   type nouns as acceptable endings. C2 (banned-example list) was
   the intended follow-up but was pruned.

Three-judge variance flagged `HIGH_VARIANCE=true` on every iter
(driven by DeepSeek-V3.2 rating `stage_2_1.groundedness=1.0` vs
GLM-5.1 / Qwen3-235B rating 3.4–3.7) — this is a judge-behavior
artifact, not a pipeline bug.

---

## 2. Methodology

Loop per `scripts/iter_run_stage2.py` (Option A single-instance mode):

```
experiments_stage2/stage1_pinned/stage_1_2_processed.jsonl   (42 rows, sha256 5e513bc7…)
  → [coupang vLLM]  Stage 2.1 extract            stage_2_1_extracted.jsonl
  → [coupang CPU]   Stage 2.1.5 semdedup         stage_2_1_5_deduped.jsonl (+ stats.json)
  → [coupang vLLM]  Stage 2.2 canonicalize full  stage_2_2_clusters.jsonl
  → [coupang CPU]   Stage 2.3 aggregate          stage_2_3_analyzed_intents.jsonl
  → [coupang vLLM]  Stage 2.4 expand             stage_2_4_expanded_intents.jsonl
  → [coupang]       tri_judge_run_stage2 (Friendli × 3 judges × 4 stages = 12 runs)
  → [local]         quant_stage2_report (§4e probes)
  → git commit      iter_NN_<slug>: <headline>
```

Each iter's `pipeline_snapshot/` captures the six files (5 pipeline
entry scripts + `prompts.py`) that produced its outputs. Prompt
patches modify `pipelines/prompts.py` locally, get snapshotted, get
overlaid on coupang at run time, and then `git checkout HEAD --
pipelines/` reverts the working tree so the next iter starts clean.

§6 promote-bar is 16 checks (Stage 2.1 × 3, Stage 2.2 × 6, Stage 2.3
× 3, Stage 2.4 × 5). §5b eager-stack regression guard blocks a
partial winner from propagating if any downstream headline gate
regresses > -0.02 absolute, any 5-point avg_* regresses > -0.10, or
any failure-mode count increases > +2.

---

## 3. Iteration-by-iteration results

| iter | gates | 2.1.grnd | 2.2.coh | 2.2.fit | 2.2.dup | 2.3.use | 2.4.use | suffix | canonical_count | §5b | commit |
|---|---|---|---|---|---|---|---|---|---|---|---|
| iter_00_baseline | **9/16** | 2.70 | 0.80 | 3.63 | 1.33 | 2.96 | 3.97 | 0.70 | 11 | — | `3647336` |
| iter_00a_probe (no pipeline) | — | — | — | — | — | — | — | — | — | — | `b672422` |
| iter_01 SD1 (full @ 0.75) | 10/16 | 2.88 | **0.95** | **4.53** | 3.00 | 2.01 | 3.82 | 0.45 | 21 | SKIP | `3004f3d` |
| iter_02 SD2 (full @ 0.70) | 9/16 | 3.07 | 0.95 | 4.45 | 2.67 | 2.63 | 3.76 | 0.64 | 15 | SKIP | `4af9df6` |
| iter_03 SD3 (signature_combo @ 0.75) | 8/16 | 2.78 | 0.98 | 4.64 | 0.00 | 1.76 | 3.69 | 0.57 | 15 | SKIP (falsified) | `cc0d404` |
| **iter_04 C1** (suffix enforce) | **12/16** | 2.84 | **0.96** | **4.62** | **0.33** | 2.19 | 3.89 | 0.625 | 9 | SKIP | `e40d677` |

Metric key: `grnd` = avg_intent_groundedness, `coh` = coherent_rate,
`fit` = avg_canonical_fit, `dup` = duplicate_pairs_found, `use` =
avg_overall_usefulness, `suffix` = canonical_suffix_compliance_rate
(quant). **Bold** cells cross a §6 gate for the first time.

All 6 iters have `HIGH_VARIANCE=true` and `Promote=false`.

### 3.1 iter_00a probe (PLAN §5a, data-driven SD threshold)

Probe showed PLAN's default θ=0.90 is a no-op (0/42 removed) on the
baseline. Per PLAN §5a fallback rule (`smallest θ in [0.70, 0.95]
where removed_rate ∈ [0.10, 0.25]`), SD1 adopted **θ=0.75** (5/42
removed predicted; 9/42 actual on coupang due to GPU-side cosine
nondeterminism). SD2 used θ=0.70 (16/42 removed), SD3 reused
θ=0.75 with the `signature_combo` builder.

### 3.2 SD-series pattern (SD1 → SD2 → SD3, all PARTIAL_SKIP)

- **SD winner by gate count**: SD1 (10/16), beating SD2 (9) and SD3 (8).
- **Why all SD iters blocked downstream**: removing rows by intent
  signature INCREASES the count of unique surface intents that
  survive to Stage 2.2 (the remaining rows are more heterogeneous),
  so agglomerative clustering produces MORE, SMALLER clusters
  (baseline 11 → SD1 21 → SD2 15 → SD3 15). Each cluster gets
  `evidence=1` more often → Stage 2.3 flags
  `low_evidence_high_weight` on nearly every intent → usefulness
  collapses (-0.94 on SD1, -0.33 on SD2, -1.20 on SD3).
- **SD3 falsification**: dropping `extracted_keywords` from the
  signature made signatures much more similar; retention dropped to
  38% (16/42 kept) and the output even produced a *duplicate*
  `등산복` canonical in two separate clusters. Keywords were a
  distinguishing signal, not noise.

### 3.3 iter_04 C1 (the winner)

Patch adds two blocks to `CANONICAL_SYSTEM`:

1. "Canonical name must end in 룩/웨어/복/스타일/캐주얼/패션/유형."
2. "If the group is not fashion-related (place/person/weather/food
   /activity/brand), output `일반`."

Outcome: `canonical_count` collapsed 11→9 (LLM merged aggressively
when suffix constraint was tight). All three Stage 2.2 gates
crossed, but:

- Four of the 9 canonicals still violate the suffix rule:
  `일하며 등산`, `여름원피스`, `루즈핏티`, `일식집데이트룩` (only
  the last is actually OK). Product-type words (`피스`, `티`) got
  treated as acceptable endings by the LLM.
- Stage 2.3 usefulness regressed 2.96 → 2.19 because Stage 2.2 over-
  merged — some clusters now contain heterogeneous members whose
  aggregated attributes don't support the chosen canonical.

---

## 4. Infrastructure delivered (main branch)

Commits outside the iter-commits:

| commit | scope |
|---|---|
| `7439444` | PLAN §11 bootstrap: 5 Stage 2 entry points + tri-judge/quant/driver/ENV |
| `d321d87` | iter_run_stage2: tri_judge on coupang (Stage 1 parity) + auto-deploy |
| `9432b14` | fix 3 issues from iter_00 run: DeepSeek judge crash on int failure_modes, judge_raw/judge_raw/ nesting, DONE marker after commit |
| `db48360` | retry wrapper (3 attempts, 3s backoff) on every `brev copy/exec` call |
| `f089092`, `627586d` | `--signature-builder` CLI plumbing for SD3 |
| `3e82afc`, `5435bc1` | prompts.py in `STAGE2_SNAPSHOT_FILES` + `_revert_pipelines_to_head` for C/E/X patches |

Pipeline module changes:

- **new** `pipelines/stage_2_1_5_semdedup.py` — SD-series enabler, 3
  signature builders, BGE-M3 greedy dedup with pass-through mode
- **refactor** `pipelines/stage_2_2_canonicalize.py` — added
  `--stage {full, embed_cluster_only, llm_finalize}` for Option B
  phase-split (unused by this session's iters, all ran in `full`)
- **new** `scripts/quant_stage2_report.py` — §4e probes + §5a probe
  mode
- **new** `scripts/tri_judge_run_stage2.py` — 4-stage × 3-judge
  orchestrator
- **new** `scripts/iter_run_stage2.py` — sealed 14-step driver
- **new** `experiments_stage2/ENV.md` — coupang2 topology worksheet
- `pipelines/eval/common.py` + 6 judges — `safe_string_list` helper
  to defend against judges returning non-list `failure_modes`

---

## 5. Open items / next steps

### 5.1 Not attempted this session (unblocked, queued in PLAN §5)

| series | iter | hypothesis | expected gain | blocker |
|---|---|---|---|---|
| C | C2 | taxonomy-exclude (banned-example list) | headline suffix_compliance 0.625 → ~0.85 | none; patch trivial |
| C | C3 | refine_homogeneity_strict | stage_2_2 marginal | C1 already saturated 2.2 |
| E | E1 | extract_general_wear_strict | stage_2_1.groundedness +0.5? | none |
| E | E2 | extract_attr_decomposition | attr_concrete.material 0.12 → 0.5+ | none |
| E | E3 | extract_few_shot_expand | stage_2_1 coverage | none |
| E | E4 | extract_keyword_rubric | attr_concrete + keyword quality | none |
| A | A1 | attr_value_normalize_bilingual | stage_2_3.duplicate_value_count | none |
| A | A2 | quality_score_log_curve | stage_2_3.usefulness (target +1.0) | none |
| A | A3 | topk_by_evidence | stage_2_3.usefulness | none |
| X | X1 | query_style_diversity_rule | stage_2_4.avg_query_diversity | none |
| X | X2 | attr_weaving_partial | stage_2_4 attribute_weaving | none |
| combo | combo_c1_e1 | stack C1 on top of E winner | multi-stage lift | need E winner first |

Rough ordering if work resumes: **E1 first** (largest single gap,
Stage 2.1 groundedness), then **A2 or A3** (Stage 2.3 usefulness),
then **X1/X2** (Stage 2.4 to cross 4.0), then **C2** only if the
suffix headline still blocks promotion.

### 5.2 Structural items / known issues

- `HIGH_VARIANCE=true` on every iter: DeepSeek-V3.2 consistently
  scores `stage_2_1.avg_intent_groundedness` around 1.0 while GLM
  + Qwen3 score 3.4–3.7, range ≈ 2.7 on every iter. This is a
  judge-behavior issue, not pipeline. Mitigation candidate: tighten
  the Stage 2.1 judge rubric (not in PLAN §5; requires separate
  decision).
- `experiments_stage2/summary.md` still uses Stage-1 column headings
  and shows `None` for every metric — `scripts/make_comparison.py`
  writes the leaderboard with a Stage 1 schema that does not map to
  Stage 2 metric keys. Low priority cosmetic fix.
- `iter_01` has two commits (`c529780` and `3004f3d`) because the
  first run was interrupted after the pipeline succeeded but the
  tri-judge stopped mid-way (6/12 judges); the re-run via
  `--skip-pipeline` completed the remaining judges and wrote the
  final metrics. History is slightly messy but the latest commit
  is canonical.
- iter_03 surfaced a **duplicate canonical** bug (`등산복` in two
  separate clusters) when surface intents collapse onto identical
  canonicals even after the `merge_clusters_by_canonical` pass in
  `stage_2_3_aggregate.py`. Not investigated; likely prompt-driven
  (signature_combo made the two source clusters superficially
  different but the LLM canonicalized them to the same name).

### 5.3 Resume checklist (for a future session)

1. `git log --oneline -25` should show `e40d677` as iter_04 C1 and
   `5435bc1` as the last driver fix.
2. `experiments_stage2/stage1_pinned/stage_1_2_processed.jsonl` is
   gitignored; re-create from
   `experiments/iter_21_dedup_v2/output/stage_1_2_processed.jsonl`
   if missing (sha256 `5e513bc7…fb640b6`).
3. coupang + coupang2 are both running per the last `brev list`.
4. Friendli key lives on coupang's env, not local `.env` (local has
   `NVIDIA_API_KEY` only). tri_judge runs remotely for this reason.
5. For E1 (recommended first continuation):
   - patch lives in `pipelines/prompts.py::EXTRACT_SYSTEM` R2–R7
     (lines 20–50 of prompts.py)
   - invoke: `scripts/iter_run_stage2.py --iter-id 05 --slug
     extract_general_wear_strict --parent-iter iter_00_baseline
     --patch /tmp/E1.diff --semdedup off --headline "iter_05 E1: …"`
   - parent is `iter_00_baseline`, NOT iter_04, because C1 is
     `PARTIAL_SKIP` per §5b; combo lifting C1 + E1 comes later.

---

## 6. Appendix: commit index

Iter commits on main (descending):

```
e40d677 iter_04_canonical_suffix_enforce: CANONICAL_SYSTEM enforces 룩/웨어/복/... suffix
cc0d404 iter_03_semdedup_signature_combo_75: signature_combo @ θ=0.75 (FALSIFIED)
4af9df6 iter_02_semdedup_strict_70: full @ θ=0.70 (aggressive)
3004f3d iter_01_semdedup_intent_cosine_75: full @ θ=0.75 (probe-recommended, 9/42 @ remote)
c529780 iter_01_semdedup_intent_cosine_75: (partial; 6 of 12 judges then cancelled)
b672422 iter_00a_semdedup_probe: §5a threshold sweep (recommended θ=0.75, 5/42)
3647336 iter_00_baseline: SD off, full Option A, 42 pinned input rows
```

Full log: `git log --oneline main` from `43ea760` forward.
