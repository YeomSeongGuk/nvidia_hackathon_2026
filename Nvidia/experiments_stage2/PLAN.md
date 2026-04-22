# Stage 2 Iterative Improvement Plan

**Branch**: `experiment/stage2-iterative-improvement`  (to be created off `main`)
**Parent state**: Stage 1 best = `iter_21_dedup_v2` (commit `7387684`) — its
`stage_1_2_processed.jsonl` (42 rows) is **pinned as Stage 2 input** so
every Stage-2 iteration compares apples-to-apples.
**Time budget**: **12 hours** hard cap; no plateau stop.
**Records per iteration**: **42** (pinned — matches iter_21 output).
**Judge ensemble**: GLM-5.1 + DeepSeek-V3.2 + Qwen3-235B on Friendli (same as Stage 1).

---

## 1. Goal

Improve the four Stage-2 sub-stages — 2.1 extract / 2.2 canonicalize
/ 2.3 aggregate / 2.4 expand — until every one of them passes its
promotion bar (§6) under the tri-judge ensemble. Stage 2.2 (canonical
naming + cross-merge) is the expected bottleneck; the earlier 10K run
produced 260 canonicals with obvious noise (`의림지`, `아침안개`,
`손주`, ...) and known over-merge errors (`오피스캐주얼 + 하객룩 →
오피스캐주얼`).

The loop is the same as Stage 1:

    pinned Stage-1 input (42 rows) → run 2.1/2.2/2.3/2.4 →
    tri-judge each stage → read the worst-K → hypothesise →
    patch → regenerate → compare

Every iteration is a self-contained folder under
`experiments_stage2/iter_NN_<slug>/`.

## 2. Non-goals

- **Stage 1 changes.** The input is frozen at iter_21. Stage 1 may
  re-improve in parallel but we don't adopt those changes until a
  Stage-2 promotion is reached.
- **Big-N runs.** 42 records is deliberate — matches the iter_21
  output. If signal is unstable we might bump to 100 later (§10), not
  as a default.
- **New judge rubrics.** The four judge schemas in
  `pipelines/eval/schemas.py` (Stage 2.1/2.2/2.3/2.4) are fixed for the
  run, otherwise iterations are not comparable.
- **Cross-stage "combo" iterations before individual stage wins.**
  First we need clear per-stage wins; combos come late in the queue.

## 3. Ground rules

- All changes live on `experiment/stage2-iterative-improvement` off
  `main@<current>`. Each iteration is one commit:
  `iter_NN_<slug>: <one-liner> <headline metric Δ>`.
- `data/`, per-iter `output/`, `judge_raw/`, and `stage1_pinned/` are
  gitignored. Only distilled artefacts commit: `hypothesis.md`,
  `patch.diff`, `pipeline_script.py` (or per-iter config), `metrics.json`
  (with sha256 of outputs), `judge_report.md`, `quant_report.md`,
  `comparison.md`, `run_log.txt`.
- Each iteration uses its own `$STAGE_DATA_ROOT=$HOME/experiments_data_stage2/iter_NN`
  on coupang. Writes never clobber Stage-1 or main-pipeline data.
- `LLM_EXTRA_BODY='{"chat_template_kwargs":{"enable_thinking":false}}'`
  stays on for all vLLM calls — we're still driving Nemotron-Super 120B.
- `LLM_PROVIDER=vllm`, `VLLM_BASE_URL=http://localhost:5000/v1`,
  `VLLM_MODEL=nemotron` for pipeline-side LLM. Judge uses Friendli.

### 3a. Input pinning (critical for comparability)

The iter_21 `stage_1_2_processed.jsonl` (sha256 in its
`metrics.json.output_hashes`) is the Stage-2 input of record. Copy
procedure:

```bash
mkdir -p experiments_stage2/stage1_pinned/
cp experiments/iter_21_dedup_v2/output/stage_1_2_processed.jsonl \
   experiments_stage2/stage1_pinned/stage_1_2_processed.jsonl
```

`experiments_stage2/stage1_pinned/INPUT_SHA256` records the hash for
verification. Every iteration reads from the pin, not from the live
pipeline.

### 3b. Two-instance Brev compute topology

Stage 1's `iter_23_signature_dedup` proved that the `coupang` instance
is memory-bound: cudf-accelerated dedup OOM'd there because the vLLM
server already pins most of the GPU/host RAM. For Stage 2 we therefore
split work across **two Brev instances**.

| instance | role | typical ops |
|---|---|---|
| `coupang` (H100 NVL × 2) | vLLM Nemotron-Super 120B serving (GPU + host RAM pinned) | pipeline-side LLM calls — extract / refine / canonical naming / cross-merge / expand |
| `coupang2` *(substantial GPU + RAM; spec pending in `ENV.md`)* | heavy semantic / embedding workloads | BGE-M3 or Jina embeddings, agglomerative clustering, **embedding-based semantic dedup** (previously blocked on `coupang` OOM), any future cudf-style batch ops |

`coupang2`'s available compute changes the dedup strategy: Stage 1's
`iter_23/24/25` used rule-based signature dedup (Jaccard-bigram on
title/attrs tuples) because embedding-based semantic dedup wouldn't fit
on `coupang`. Now semantic dedup is on the table — either (a) as a new
step inside Stage 2 before clustering, or (b) as a re-pinned Stage 1
input after Stage 1's branch promotes a semantic-dedup variant. Both
paths are carried in the hypothesis queue (§5 SD-series).

Execution pattern on `coupang2` (confirmed working on Stage 1 — see
the per-iter subagent recipe in Stage 1's HANDOFF.md):

```text
local → brev copy ↑ → run script on coupang2 → brev copy ↓ → local
```

**Cross-instance LLM coordination** (TBD, pending env setup):

- Option A — `coupang2` calls `coupang:5000` vLLM over Brev internal
  network (preferred if the two instances share a private subnet).
- Option B — Phase-split Stage 2.2: embedding + clustering on
  `coupang2`, then ship the cluster file back to `coupang` and run
  refine / canonical-naming / cross-merge LLM passes there.
- Option C — local workstation acts as the broker: pulls
  clustering output from `coupang2`, pushes to `coupang` for LLM
  passes, pulls final `stage_2_2_clusters.jsonl` back.

The iter_run_stage2 driver (§11) will be written to support
**Option B by default** (simplest, no networking assumptions) and
allow Option A as a env-flag override once connectivity is confirmed.
Env setup outcome gets recorded in `experiments_stage2/ENV.md` on the
branch and the PLAN is updated in-place.

### 3c. Per-stage instance assignment (default policy)

| sub-stage | step | runs on | reason |
|---|---|---|---|
| 2.1 extract | per-doc vLLM call | `coupang` | LLM call, no heavy mem |
| **2.1.5 semdedup** (new — SD-series §5) | embedding + pairwise semantic similarity dedup of extracted intents | `coupang2` | embedding compute + N² or HNSW similarity — pure CPU/GPU on coupang2 |
| 2.2 canonicalize | 1. embed + agglomerative cluster | `coupang2` | embedding tensor + scipy linkage are RAM-heavy |
| 2.2 canonicalize | 2. refine + canonical naming + cross-merge | `coupang` | LLM call, needs vLLM |
| 2.3 aggregate | weighted aggregation | `coupang2` | pure CPU, keeps `coupang` free for LLM |
| 2.4 expand | per-intent vLLM call | `coupang` | LLM call, no heavy mem |

Quant probes (§4e) run locally. Judge calls (§4f) hit Friendli and can
fire from any instance; we run them locally to avoid extra copies.

## 4. Metric sheet

Metrics come from two sources: **LLM judge ensemble** (GLM-5.1 +
DeepSeek-V3.2 + Qwen3-235B on Friendli) and **deterministic probes**
(no LLM). Each iteration's `metrics.json` rolls all four stages up.

### 4a. Stage 2.1 — per-doc intent/attribute extraction
Input: `stage_1_2_processed.jsonl` (42 rows).
Output: `stage_2_1_extracted.jsonl` (42 rows).
Judge: `pipelines.eval.stage_2_1_judge` (Stage2_1JudgeResult).

| metric (per-judge + mean) | direction | promote-threshold |
|---|---|---|
| `avg_intent_groundedness` | ↑ | ≥ 4.0 / 5 |
| `intent_type_valid_rate` | ↑ | ≥ 0.90 |
| `general_wear_rate` | — | informational |
| `general_wear_false_negative_rate` | ↓ | ≤ 0.15 |
| `sentiment_rating_agreement_rate` | ↑ | ≥ 0.85 |
| `attribute_concrete_rate.material` | ↑ | ≥ 0.80 |
| `attribute_concrete_rate.fit` | ↑ | ≥ 0.70 |
| `attribute_concrete_rate.color` | ↑ | ≥ 0.85 |
| failure_modes: `hallucinated_intent` | ↓ | ≤ 2/42 |
| failure_modes: `subjective_attribute_value` | ↓ | ≤ 5/42 |

### 4b. Stage 2.2 — clustering + canonical naming
Input: Stage 2.1 output.
Output: `stage_2_2_clusters.jsonl` (target 5-12 clusters).
Judge: `pipelines.eval.stage_2_2_judge` (per-cluster + cross-cluster duplicate pass).

| metric (per-judge + mean) | direction | promote-threshold |
|---|---|---|
| `coherent_rate` | ↑ | ≥ 0.85 |
| `avg_canonical_fit` | ↑ | ≥ 4.0 / 5 |
| `non_korean_canonical_count` | ↓ | = 0 |
| `should_split_count` | ↓ | ≤ 10 % of clusters |
| `duplicate_pairs_found` | ↓ | ≤ 1 |
| failure_modes: `non_fashion_canonical` (quant probe, see 4e) | ↓ | ≤ 1 cluster |
| failure_modes: `wrong_canonical` | ↓ | ≤ 2 |

### 4c. Stage 2.3 — aggregated attribute quality per canonical
Input: Stage 2.2 output.
Output: `stage_2_3_analyzed_intents.jsonl`.
Judge: `pipelines.eval.stage_2_3_judge`.

| metric (per-judge + mean) | direction | promote-threshold |
|---|---|---|
| `avg_overall_usefulness` | ↑ | ≥ 4.0 / 5 |
| `attr_concrete_rate` | ↑ | ≥ 0.80 |
| `attr_fits_intent_rate` | ↑ | ≥ 0.85 |
| `duplicate_value_count` (e.g. linen vs 린넨) | ↓ | ≤ 2 |
| `evidence_reliable_rate` | ↑ | ≥ 0.80 |

### 4d. Stage 2.4 — natural-language query expansion
Input: Stage 2.3 output.
Output: `stage_2_4_expanded_intents.jsonl` (N canonicals × 5 queries).
Judge: `pipelines.eval.stage_2_4_judge`.

| metric (per-judge + mean) | direction | promote-threshold |
|---|---|---|
| `avg_overall_usefulness` | ↑ | ≥ 4.0 / 5 |
| `avg_query_diversity` | ↑ | ≥ 3.5 / 5 |
| `avg_attribute_weaving` | ↑ | ≥ 3.5 / 5 |
| `avg_canonical_coverage` | ↑ | ≥ 3.5 / 5 |
| `per_query_natural_rate` | ↑ | ≥ 0.90 |
| `per_query_fits_intent_rate` | ↑ | ≥ 0.90 |
| `canonical_repeat_rate` | ↓ | ≤ 0.10 |
| `garbled_count` | ↓ | = 0 |

### 4e. Deterministic / quantitative probes (no LLM)
`scripts/quant_stage2_report.py` (new, to be written):

| metric | stage | direction | promote-threshold |
|---|---|---|---|
| `semdedup_retention_rate` (kept / input) | 2.1.5 | — | informational (target ≈ 0.6–0.9) |
| `semdedup_removed_count` | 2.1.5 | — | informational |
| `semdedup_avg_cosine_of_kept` | 2.1.5 | ↓ | ≤ 0.85 (keeps diversity) |
| `canonical_count` | 2.2 | — | informational |
| `canonical_non_fashion_rate` (regex for 지명/날씨/사람 이름) | 2.2 | ↓ | ≤ 0.05 |
| `canonical_hangul_pure_rate` | 2.2 | ↑ | ≥ 0.95 |
| `canonical_suffix_compliance_rate` (ends in 룩/웨어/복/스타일/캐주얼/...) | 2.2 | ↑ | ≥ 0.80 |
| `query_dedup_ratio` (5 queries distinct, unique / 5) | 2.4 | ↑ | ≥ 0.95 |
| `query_avg_length_chars` | 2.4 | — | informational |
| `query_non_hangul_chars_rate` (detects "thing", "몇enaar") | 2.4 | ↓ | ≤ 0.01 |

### 4f. Judge ensemble protocol (same as Stage 1 PLAN §4f)
- Each stage × 3 judges = 12 Friendli calls per iter.
- `metrics.json` reports every metric as `{glm, deepseek, qwen3, mean, range}`.
- Promotion is decided on the mean; `range > 0.15` on the headline
  metric marks `HIGH_VARIANCE` and blocks auto-promotion.
- `agreement_rate` is computed for boolean metrics.

Cost envelope per iter:
- 2.1: 42 records × 3 judges = 126 Friendli calls
- 2.2: 8-15 clusters × 3 judges + 3 cross-cluster passes ≈ 30-45 calls
- 2.3: 5-10 intents × 3 judges = 15-30 calls
- 2.4: 5-10 intents × 3 judges = 15-30 calls (one call per intent set)
- Total ≈ **200 Friendli calls/iter × 15 iter = 3 k calls ≈ 3-4 M tokens**.
  Safely under Friendli serverless hackathon budget.

## 5. Hypothesis queue

Organised by which sub-stage the fix primarily targets. Pull one per
iteration. Failing hypotheses are still committed (important signal).

**Execution order (resolved)**: `iter_00_baseline` → `iter_00a_semdedup_probe`
(one-shot probe, no code change — see §5a) → **SD-series**
(SD1 → SD2 → SD3) to introduce Stage 2.1.5 semantic dedup and measure
its effect on downstream 2.2 quality → **C-series** (C1 → C2 → C3 →
C4 → C5 → C6 → C7 → C8) → E-series (E1-E4) → A-series (A1-A3) →
X-series (X1-X4) → combo iterations (**eager stack**: the moment a
sub-stage winner is identified it is baked into the next iter's base,
even before its combo is judged).

> SD comes before C because cleaner Stage 2.1 intents shrink the
> search space for the clustering & canonical-naming prompt fixes. If
> SD1 is already enough to satisfy several C-series bars, the later
> C iterations reshape accordingly.

**Series pruning (15-iter budget allocation)**
Total candidate count in §5 = SD 3 + C 8 + E 4 + A 3 + X 4 + combo 4 = **26**.
Budget = **15 iters**. Default allocation: SD 3 + C 3–4 + E 2 + A 2 + X 2 + combo 2–3.
Rules the orchestrator uses to prune:

- Within a series, if **two consecutive iters regress** on the series'
  headline metric (vs the series' running best), the remaining iters
  in that series are **deferred** (not dropped — can be revived post-§10).
- If a series' first iter **misses its own sub-stage promote bar by
  > 30 % relative**, the series is **frozen** until new information
  arrives (e.g. a later series gives a hint).
- C-series gets up to 4 slots (highest expected yield) before
  deferral kicks in; all other series get up to 2 slots.
- combo iters only run after *at least one winner per stacked
  series* is identified.

**5a. Pre-SD data probe (`iter_00a_semdedup_probe`)**
Before SD1 runs, a no-code-change probe is executed on the baseline's
`stage_2_1_extracted.jsonl` (42 rows from `iter_00_baseline`):

```bash
scripts/quant_stage2_report.py --mode semdedup-probe \
    --input  experiments_stage2/iter_00_baseline/output/stage_2_1_extracted.jsonl \
    --thresholds 0.95,0.90,0.85,0.80,0.75,0.70 \
    --signature full \
    --out experiments_stage2/iter_00a_semdedup_probe/semdedup_probe.json
```

It reports, per threshold, `pairs_above_threshold`, `removed_count`,
`removed_rate`, and `avg_cosine_of_kept`. This probe drives the
**data-driven SD1 threshold selection**: if `0.90` removes 0 pairs
(likely, given short intent strings), SD1's threshold falls back to
the smallest threshold in `[0.90, 0.85, 0.80, 0.75, 0.70]` where
`removed_rate ∈ [0.10, 0.25]` — i.e. SD1 always starts on an
informative operating point instead of risking a no-op first
iteration. The selected threshold is recorded in SD1's
`hypothesis.md`.

If the probe shows no threshold in `[0.70, 0.95]` produces a
meaningful removal (say, all thresholds remove either 0 or > 40 %),
the SD-series is **reclassified as a signature-engineering problem**
and SD3 (`semdedup_signature_combo`) is promoted to SD1.

**5b. Eager-stack regression guard**
A partial-win iter (e.g. SD1 improves Stage 2.1.5 stats but leaves
Stage 2.2/2.3/2.4 ≈ flat) is eagerly stacked into the next iter's
base **only if no downstream stage regresses beyond**:

| axis | tolerance |
|---|---|
| any headline gate metric, absolute | > `-0.02` |
| any failure-mode count, absolute   | > `+2` worse |
| any `avg_*` 5-point metric         | > `-0.10` |

Violations flag the iter `partial_skip` in `summary.md`; its patch
remains available as an explicit `--stack` opt-in for a later combo
iter but does not auto-propagate.

### Stage 2.1.5 — semantic dedup (SD-series, new)

`coupang2`'s spare capacity unlocks embedding-based intent dedup that
previously couldn't run on `coupang`. Introduced as a new optional
step between Stage 2.1 and Stage 2.2; `iter_00` has it disabled,
SD-series switches it on.

**Signature builders** (input to the embedder; Stage 2.1
`ExtractedIntent` schema: `raw_intent`, `extracted_keywords: List[str]`,
`attributes.{material, fit, color, style, season}`):

| builder id | composition |
|---|---|
| `full` | `f"{raw_intent} | kw: {','.join(extracted_keywords) or '-'} | attrs: m={material or '-'}|f={fit or '-'}|c={color or '-'}|st={style or '-'}|se={season or '-'}"` |
| `signature_combo` | `f"{raw_intent} | attrs: m={material or '-'}|f={fit or '-'}|c={color or '-'}|st={style or '-'}|se={season or '-'}"`  (drops `extracted_keywords`) |
| `intent_only` | `f"{raw_intent}"` (not in queue by default; smoke test only) |

All three lowercase and collapse internal whitespace before embedding.

| # | slug | hypothesis | patch target |
|---|---|---|---|
| **SD1** | `semdedup_intent_cosine_90` | After Stage 2.1, embed each row with signature builder `full` using BGE-M3 on `coupang2`, drop near-duplicates at cosine ≥ 0.90 (or the probe-selected threshold; see §5a). Expected: tighter Stage 2.2 clusters; `canonical_non_fashion_rate` falls because duplicate weak-signal intents no longer drive noise clusters. | `pipelines/stage_2_1_5_semdedup.py` (new), `pipelines/stage_2_2_canonicalize.py` (input wiring) |
| SD2 | `semdedup_strict_85` | Same builder with threshold 0.85 — more aggressive. Trade-off: retention drops, but `coherent_rate` should climb further. Falsifiable if `canonical_count` collapses below 4. | `pipelines/stage_2_1_5_semdedup.py` threshold arg |
| SD3 | `semdedup_signature_combo` | Signature builder swaps to `signature_combo` (ignore `extracted_keywords`). Tests whether noisy free-form keywords hurt SD1 signal. Threshold inherited from SD-winner. | `pipelines/stage_2_1_5_semdedup.py` (`--signature-builder signature_combo`) |

If SD-series also enables upgrading Stage 1's pinned input (i.e.
re-pin to a Stage 1 branch variant that uses semantic dedup at 1.1.5
on `coupang2`), that's a **separate re-pin decision** — not an SD
iter here. The Stage 1 `dedup_miss_rate` blocker (0.151 vs ≤ 0.05)
becomes solvable once `coupang2` is online. See §12 bullet 6.

### Stage 2.1 — extract (E-series)

| # | slug | hypothesis | patch target |
|---|---|---|---|
| **E1** | `extract_general_wear_strict` | The `general_wear` bucket is noisy in iter_00 — too many real TPOs (하객룩, 등산) get dumped there. Tighten R2-R7 rules in `EXTRACT_SYSTEM` with concrete counter-examples. | `pipelines/prompts.py::EXTRACT_SYSTEM` |
| E2 | `extract_attr_decomposition` | Single ATTRS sub-call bundles 5 attributes; model picks one and defaults the rest. Per-attribute mini-prompts force per-key reasoning. | `pipelines/stage_2_1_extract.py` |
| E3 | `extract_few_shot_expand` | Current few-shots cover 2 canonical patterns. Add 6-8 new ones covering underwear / sports / seasonal / non-fashion edge cases. | `pipelines/prompts.py` |
| E4 | `extract_keyword_rubric` | `extracted_keywords` is free-form; many rows emit products or generic adjectives. Constrain to "style cue ≤ 2 words, fashion-domain". | `pipelines/prompts.py` |

### Stage 2.2 — canonicalize (C-series) — **highest expected yield**

| # | slug | hypothesis | patch target |
|---|---|---|---|
| **C1** | `canonical_suffix_enforce` | `의림지` / `손주` canonical-fit regression because naming prompt has no suffix constraint. Force naming output to end in `룩/웨어/복/스타일/캐주얼/패션/유형` or fall back to `일반`. | `pipelines/prompts.py::CANONICAL_SYSTEM` |
| **C2** | `canonical_exclude_taxonomy` | Same prompt additionally bans: 지명, 사람 이름, 날씨, 음식, 감탄사. Paste 10-15 concrete banned examples. | `pipelines/prompts.py::CANONICAL_SYSTEM` |
| C3 | `refine_homogeneity_strict` | Refine prompt allows `["하객룩","오피스룩"]` in same cluster. Add "모든 멤버는 같은 occasion/TPO 계열이어야 함" rule with examples of valid vs invalid splits. | `pipelines/prompts.py::REFINE_SYSTEM` |
| C4 | `cluster_threshold_tight` | Agglomerative threshold 0.35 → 0.30. Produces more, smaller clusters. Expected: fewer heterogeneous clusters, more refine work, but better coherent_rate. | `pipelines/stage_2_2_canonicalize.py` CLI default |
| C5 | `crossmerge_evidence_weighted` | Cross-merge LLM call treats small clusters (evidence ≤ 2) as merge candidates and large ones (≥ 5) as anchors. Prevents `하객룩 ↗ 오피스캐주얼` over-merge. | `pipelines/prompts.py::CROSS_MERGE_SYSTEM` + pass evidence counts in prompt |
| C6 | `evidence_floor_drop_1` | `evidence=1` clusters auto-promoted to `일반` bucket before Stage 2.3. (Trade-off: loses long-tail TPOs; acceptable if they were noise.) | `pipelines/stage_2_2_canonicalize.py` post-merge |
| C7 | `embedding_model_jina` | BGE-M3 → `jinaai/jina-embeddings-v3` (stronger Korean semantic similarity, same dim). Expected: tighter cluster seeds, fewer refine iterations. | `pipelines/stage_2_2_canonicalize.py` default `--embed-model` |
| C8 | `pre_filter_general_wear` | Drop `raw_intent == "general_wear"` before clustering so they don't form noisy clusters. Attach them to `일반` bucket in Stage 2.3 aggregation. | `pipelines/stage_2_2_canonicalize.py` |

### Stage 2.3 — aggregate (A-series)

| # | slug | hypothesis | patch target |
|---|---|---|---|
| A1 | `attr_value_normalize_bilingual` | `material=linen` and `material=린넨` appear in same cluster as distinct. Post-hoc normalize via a small dict + fuzzy match. | `pipelines/stage_2_3_aggregate.py` |
| A2 | `quality_score_log_curve` | `rating=5 → 0.95` vs `rating=1 → 0.50` is linear. Log-curve (or constant) reduces 1-star-review over-weighting. | `pipelines/stage_2_3_aggregate.py::quality_score_of` |
| A3 | `topk_by_evidence` | Fixed `top_k=3` gives evidence=1 clusters the same space as evidence=100. Scale to `min(3, ceil(log2(ev)+1))`. | `pipelines/stage_2_3_aggregate.py` |

### Stage 2.4 — expand (X-series)

| # | slug | hypothesis | patch target |
|---|---|---|---|
| X1 | `query_style_diversity_rule` | Baseline 5 queries look like paraphrases. Enforce a rubric: 2 questions + 1 command + 1 descriptive + 1 situation-only. | `pipelines/prompts.py::EXPAND_SYSTEM` |
| X2 | `attr_weaving_partial` | Currently every attr ends up in every query. Instruction: "각 쿼리는 1-2 attrs만 자연스럽게." | `pipelines/prompts.py::EXPAND_SYSTEM` |
| X3 | `persona_age_mix` | Queries read homogeneous. Add 2 persona-conditioned variants per set (e.g. "20대 여성 말투로 1개, 40대 남성 말투로 1개"). | `pipelines/prompts.py::EXPAND_SYSTEM` |
| X4 | `registers_mixed_3_2` | 반말/존댓말 섞기 rule: 3 반말 + 2 존댓말 per 5-query set. | `pipelines/prompts.py::EXPAND_SYSTEM` |

### Combo iterations
Because the execution mode is **eager stacking**, the "combo" iter names
just crystallise what has already been absorbed:
- after last SD-winner: `iter_stage2_combo_sd` (baseline + SD)
- after last SD + C winner: `iter_stage2_combo_sdc`
- after last E winner: `iter_stage2_combo_sdce`
- after last A winner: `iter_stage2_combo_sdcea`
- final: `iter_stage2_combo_all` (SD+C+E+A+X stacked)

Non-monotonic cases (new combo regresses on a stage) are handled as in
Stage 1: rollback the latest patch, log `roll_back` reason in
`comparison.md`, try a smaller combo.

## 6. Promotion bar

Full Stage-2 promotion requires **all four sub-stage bars** pass
simultaneously on tri-judge mean.

**Stage 2.1**:
- `avg_intent_groundedness ≥ 4.0`
- `intent_type_valid_rate ≥ 0.90`
- `attribute_concrete_rate.material ≥ 0.80`

**Stage 2.2** (usually the hardest):
- `coherent_rate ≥ 0.85`
- `avg_canonical_fit ≥ 4.0`
- `non_korean_canonical_count = 0`
- `canonical_non_fashion_rate ≤ 0.05` (quant probe)
- `duplicate_pairs_found ≤ 1`

**Stage 2.3**:
- `avg_overall_usefulness ≥ 4.0`
- `attr_fits_intent_rate ≥ 0.85`
- `duplicate_value_count ≤ 2`

**Stage 2.4**:
- `avg_overall_usefulness ≥ 4.0`
- `per_query_natural_rate ≥ 0.90`
- `avg_query_diversity ≥ 3.5`
- `canonical_repeat_rate ≤ 0.10`
- `garbled_count = 0`

Any iteration in `HIGH_VARIANCE` on a headline gate does not
auto-promote; reviewer decides.

## 7. Iteration folder shape

```
experiments_stage2/
├── PLAN.md                          (git)
├── README.md                        (git)
├── ENV.md                           (git; coupang2 spec + routing mode)
├── summary.md                       (git; rolling leaderboard)
├── stage1_pinned/                   (gitignored)
│   ├── stage_1_2_processed.jsonl    42 rows from iter_21
│   └── INPUT_SHA256                 content hash for verification
├── iter_00_baseline/
│   ├── hypothesis.md                "baseline, no changes"
│   ├── pipeline_snapshot/           vendored copy of the 5 entry points
│   │   ├── stage_2_1_extract.py
│   │   ├── stage_2_1_5_semdedup.py  (pass-through for iter_00; live for SD*)
│   │   ├── stage_2_2_canonicalize.py
│   │   ├── stage_2_3_aggregate.py
│   │   └── stage_2_4_expand.py
│   ├── patch.diff                   (iter_00 has none; SD+ iters diff vs iter_00)
│   ├── metrics.json                 §4 + sha256 of the 5 outputs
│   ├── judge_report.md
│   ├── quant_report.md
│   ├── comparison.md                (iter_00 has none)
│   ├── run_log.txt
│   ├── output/                      (gitignored)
│   │   ├── stage_2_1_extracted.jsonl
│   │   ├── stage_2_1_5_deduped.jsonl    (pass-through == stage_2_1 for SD-off)
│   │   ├── stage_2_1_5_stats.json       (SD-off: kept=in, removed=0)
│   │   ├── stage_2_2_clusters.jsonl
│   │   ├── stage_2_3_analyzed_intents.jsonl
│   │   └── stage_2_4_expanded_intents.jsonl
│   └── judge_raw/                   (gitignored, 12 files)
├── iter_00a_semdedup_probe/         (one-shot, no pipeline run)
│   ├── semdedup_probe.json          (§5a probe output)
│   └── notes.md
├── iter_01_<slug>/
│   ├── hypothesis.md
│   ├── pipeline_snapshot/           (only files the patch touched;
│   │                                 unchanged files stay as symlinks
│   │                                 to iter_00_baseline/pipeline_snapshot/)
│   ├── patch.diff                   against iter_00 pipeline_snapshot/
│   ├── ...
└── winners/                         (gitignored)
    └── iter_NN_<slug>/              (hard-copy of promoted iter)
```

Rationale for `pipeline_snapshot/` vs Stage 1's single
`pipeline_script.py`: Stage 2 has **five** entry points (2.1 / 2.1.5
/ 2.2 / 2.3 / 2.4) so a flat `pipeline_script.py` would mix five
concerns. The per-iter `pipeline_snapshot/` directory preserves the
exact `pipelines/stage_2_*.py` versions that produced the iter's
output, while per-file symlinks keep the disk footprint small for
iters that touch only one file.

`metrics.json` schema matches Stage 1's (iter_id, parent_iter,
output_hashes, stage_2_1/2_1_5/2_2/2_3/2_4 ensemble + quant,
high_variance, promote, promote_checks).

## 8. Subagent allocation

Same pattern as Stage 1 PLAN §8. Main agent (me) is the
**orchestrator**: picks hypothesis, updates `summary.md`, enforces §6.
Each iteration is dispatched to one `subagent_general` with sealed
prompt.

Per-iter subagent responsibilities (reflects the two-instance
topology in §3b — Option B default):

1. Read `hypothesis.md` + parent iter's `metrics.json`.
2. Apply the patch to the frozen pipeline files for this iter.
3. **On `coupang` (vLLM)**: upload patched code to
   `~/experiments_data_stage2/iter_NN_<slug>/` and place the pinned
   input at `$STAGE_DATA_ROOT/stage_1_2/stage_1_2_processed.jsonl`.
4. **On `coupang` — Stage 2.1** (vLLM call, per doc):
   ```bash
   PYTHONPATH=. $VENV_PY -m pipelines.stage_2_1_extract \
       --input  $STAGE_DATA_ROOT/stage_1_2/stage_1_2_processed.jsonl \
       --output $STAGE_DATA_ROOT/stage_2_1_extracted.jsonl
   ```
5. **On `coupang2` — Stage 2.1.5 semantic dedup** (from SD1 iter
   onward; `iter_00` skips this step with a pass-through copy):
   - `brev copy` code + `stage_2_1_extracted.jsonl` to `coupang2`.
   - `brev exec coupang2`:
     ```bash
     PYTHONPATH=. $VENV_PY -m pipelines.stage_2_1_5_semdedup \
         --input     $STAGE_DATA_ROOT/stage_2_1_extracted.jsonl \
         --output    $STAGE_DATA_ROOT/stage_2_1_5_deduped.jsonl \
         --threshold 0.90 \
         --embed-model BAAI/bge-m3
     ```
   - Pull `stage_2_1_5_deduped.jsonl` back. This file becomes the
     Stage 2.2 input. If SD is disabled, symlink-copy the Stage 2.1
     output to this filename (pass-through).
6. **On `coupang2` — Stage 2.2 phase 1** (embed + agglomerative
   cluster, memory-heavy, no LLM):
   - `brev copy` the code + `stage_2_1_5_deduped.jsonl` up to
     `~/experiments_data_stage2/iter_NN_<slug>/` on `coupang2`.
   - `brev exec coupang2 "..."`:
     ```bash
     PYTHONPATH=. $VENV_PY -m pipelines.stage_2_2_canonicalize \
         --stage embed_cluster_only \
         --input  $STAGE_DATA_ROOT/stage_2_1_5_deduped.jsonl \
         --embed-device cpu \
         --output $STAGE_DATA_ROOT/stage_2_2_clusters_raw.jsonl
     ```
   - `brev copy` the clusters file back down and straight up to
     `coupang` (`stage_2_2_clusters_raw.jsonl`).
7. **On `coupang` — Stage 2.2 phase 2** (LLM refine / canonical
   naming / cross-merge against vLLM):
   ```bash
   PYTHONPATH=. $VENV_PY -m pipelines.stage_2_2_canonicalize \
       --stage llm_finalize \
       --input  $STAGE_DATA_ROOT/stage_2_2_clusters_raw.jsonl \
       --output $STAGE_DATA_ROOT/stage_2_2_clusters.jsonl \
       --refine --cross-merge
   ```
   (The existing `stage_2_2_canonicalize` script needs a light split;
   §11 Bootstrap item added.)
8. **On `coupang2` — Stage 2.3** (pure Python aggregation):
   ```bash
   PYTHONPATH=. $VENV_PY -m pipelines.stage_2_3_aggregate \
       --input  $STAGE_DATA_ROOT/stage_2_2_clusters.jsonl \
       --output $STAGE_DATA_ROOT/stage_2_3_analyzed_intents.jsonl
   ```
9. **On `coupang` — Stage 2.4** (vLLM per-intent call):
   ```bash
   PYTHONPATH=. $VENV_PY -m pipelines.stage_2_4_expand \
       --force-fallback --n-queries 5 \
       --input  $STAGE_DATA_ROOT/stage_2_3_analyzed_intents.jsonl \
       --output $STAGE_DATA_ROOT/stage_2_4_expanded_intents.jsonl
   ```
10. Pull the five outputs back to
    `experiments_stage2/iter_NN_<slug>/output/`:
    `stage_2_1_extracted.jsonl`, `stage_2_1_5_deduped.jsonl`,
    `stage_2_2_clusters.jsonl`, `stage_2_3_analyzed_intents.jsonl`,
    `stage_2_4_expanded_intents.jsonl`.
11. Run `scripts/tri_judge_run_stage2.py` **locally** (Friendli calls).
    Judge inputs are the Stage 2.1 / 2.2 / 2.3 / 2.4 outputs
    (2.1.5 is measured by deterministic probes, not judged).
12. Run `scripts/quant_stage2_report.py` locally — it reads
    both Stage 2.1 extracted and 2.1.5 deduped to compute
    `semdedup_*` metrics.
13. Assemble `metrics.json` (with sha256 per file), `judge_report.md`,
    `quant_report.md`, `comparison.md`.
14. `git commit` with the standard message format.

If coupang2 internal routing to `coupang:5000` turns out to be
available after env setup, the driver switches to Option A (§3b) —
Stage 2.2 runs on `coupang2` end-to-end and the phase split disappears
in step 5-6. `iter_run_stage2.py` exposes this as `--stage22-mode
{phase_split,coupang2_direct}`.

Context isolation is preserved: subagent only sees its hypothesis +
parent metrics, not the full history.

## 9. Safety rails

- **No Brev destructive ops** on either instance without explicit
  go-ahead.
- Each iteration's `$STAGE_DATA_ROOT=$HOME/experiments_data_stage2/iter_NN`
  on each instance keeps outputs isolated. The same `iter_NN` name is
  used on both `coupang` and `coupang2` so copy commands are symmetric.
- vLLM:5000 on `coupang` is the shared resource — iterations run
  sequentially, not parallel, to avoid starvation.
- Judge concurrency capped at **4** Friendli calls in flight
  (same as Stage 1).
- `coupang2` OOM prevention: watch `/proc/meminfo` before launching
  embed+cluster; if MemAvailable < 8 GB, abort and trim the batch.
- Source of truth for each iter's outputs is the local
  `experiments_stage2/iter_NN_<slug>/output/` folder; remote
  `$STAGE_DATA_ROOT` on either instance is considered ephemeral.
- If a pipeline sub-stage throws > 5 % failure on its 42-record input,
  abort the iter, write `run_log.txt` with the failure, commit
  nothing, requeue.

## 10. Success / stop conditions

1. **Full promotion**: any iteration passes all four sub-stage bars
   in §6 → write `promote.md`, stop the loop, flag Stage 2 output as
   production-candidate.
2. **Per-stage promotion**: if a single sub-stage clears its bar but
   others regress, tag the iter as `partial_win_<stage>` and continue
   iterating on the non-passing stages while keeping the partial win
   in the stack.
3. **Budget exhausted**: 12 h wall clock → write `budget.md`, stop
   with current best.
4. **Blocker**: vLLM dies, Friendli quota exhausted, Brev degrades →
   write `blocker.md`, stop and ping user.

Scale-up escape hatch (not a stop condition): if 42-record variance
makes gate verdicts unreliable (headline metric range > 0.2 across
three consecutive iters), jump to 100 records and re-run the top 3
candidates. One-shot decision.

## 11. Bootstrap checklist

Infrastructure:
- [x] `git checkout main && git checkout -b experiment/stage2-iterative-improvement`
- [x] `experiments_stage2/PLAN.md` + `README.md`
- [x] `experiments_stage2/stage1_pinned/stage_1_2_processed.jsonl`
      copied from iter_21; `INPUT_SHA256` written
- [x] `.gitignore` updated with `experiments_stage2/` rules

coupang2 env setup (user reports instance running; Devin to verify):
- [ ] `brev list` → record `coupang2` instance type + GPU + RAM in
      `experiments_stage2/ENV.md` (file itself is §11 deliverable).
- [ ] `brev exec coupang2 "python3 --version && nvidia-smi | head"`
      → Python ≥ 3.10, one or more GPUs visible.
- [ ] Create `~/.venv` on `coupang2` (same layout as `coupang`) and
      install `pipelines/requirements-stage2-lite.txt` — just what
      Stage 2.1.5 / 2.2 phase-1 / 2.3 need:
      `sentence-transformers, scikit-learn, scipy, numpy, pandas,
      pydantic, python-dotenv, FlagEmbedding` (NO vLLM client — that
      stays on coupang). GPU torch is OK here (speeds up BGE-M3)
      but is optional for correctness.
- [ ] Decide the LLM routing mode (§3b): run a one-shot test from
      `coupang2`:
      ```bash
      brev exec coupang2 "curl -s http://<coupang-internal-ip>:5000/v1/models"
      ```
      If 200 → Option A (simpler single-instance Stage 2.2 on coupang2).
      If blocked → Option B (phase split, default).
      Write the decision + `<coupang-internal-ip>` to `ENV.md`.
- [ ] Prove round-trip copy: `local → coupang2 → back-to-local` of a
      1 MB JSONL using `brev copy`; record wall time in `ENV.md`.
      This pins the iter-loop overhead budget (each phase-split iter
      has 4 round-trips; if one round-trip > 30s the phase-split
      becomes the main wall-clock cost).

Pipeline / scripts:
- [ ] **`pipelines/stage_2_1_5_semdedup.py`** — **new (SD-series enabler)**.
      CLI: `--input`, `--output`, `--threshold`, `--embed-model`,
      `--device`, `--signature-builder {full,signature_combo,intent_only}`
      (see §5 signature-builder table for exact composition).
      Emits the deduped JSONL plus a side-car
      `stage_2_1_5_stats.json` with `kept`, `removed`, `pairs_checked`,
      `avg_cosine_of_kept`, `selected_threshold`, `signature_builder_used`.
      Default threshold 0.90, default model `BAAI/bge-m3`,
      default builder `full`. Should run cleanly on `coupang2`.
      Stage 1 `experiment/stage1-iterative-improvement` branch's
      `scripts/run_semantic_dedup_v2.py` (iter_26 prototype;
      `raw_text` + MiniLM + cuml KMeans at doc level) is
      **not** a drop-in: Stage 2.1.5 operates at intent level with
      short strings, no KMeans pre-partitioning, and BGE-M3 for
      stronger Korean semantic signal. Use iter_26's script only as a
      shape reference.
- [ ] **`pipelines/stage_2_2_canonicalize.py`** — split into two
      invocation modes so phase-split (§8 step 6/7) works:
      `--stage embed_cluster_only` (no LLM, no vLLM dependency) vs
      `--stage llm_finalize` (takes `stage_2_2_clusters_raw.jsonl`,
      runs refine + canonical naming + cross-merge against vLLM).
      `--stage full` remains the single-machine default for Option A.
      Accept the `stage_2_1_5_deduped.jsonl` shape as input (same
      schema as `stage_2_1_extracted.jsonl`).
- [ ] **`scripts/tri_judge_run_stage2.py`** — new. Mirror of
      `tri_judge_run.py` but invokes `stage_2_1_judge` /
      `stage_2_2_judge` / `stage_2_3_judge` / `stage_2_4_judge` with
      their respective input files under `--output-dir`.
- [ ] **`scripts/quant_stage2_report.py`** — new. Two modes:
      - `--mode iter` (default): emits §4e probes, including the
        `semdedup_*` metrics read from `stage_2_1_5_stats.json`.
      - `--mode semdedup-probe`: §5a one-shot probe. Takes
        `--input stage_2_1_extracted.jsonl`, `--thresholds` CSV,
        `--signature {full,signature_combo,intent_only}`,
        `--out semdedup_probe.json`. Does not need `coupang2`
        routing; runs locally with CPU BGE-M3 for the 42-row probe.
- [ ] **`scripts/iter_run_stage2.py`** — new. Sealed driver covering
      the 14-step recipe in §8 (Option B default, Option A via
      `--stage22-mode coupang2_direct`, SD on/off via
      `--semdedup {off,threshold_value}`). Also builds the per-iter
      `pipeline_snapshot/` directory with symlinks (§7). Includes
      brev copy orchestration to / from both `coupang` and `coupang2`.
- [ ] `scripts/make_comparison.py` — **reusable as-is**; the shape of
      `metrics.json` is unchanged (SD just adds new keys).
- [ ] Verify Stage 2 judge modules all import + smoke on Friendli
      (`python -m pipelines.eval.stage_2_1_judge --help` etc.).

## 12. User decisions (resolved)

1. **Input pin** → iter_21 `stage_1_2_processed.jsonl` (42 rows). SHA256
   pinned in `experiments_stage2/stage1_pinned/INPUT_SHA256`.
2. **Execution order** → SD-series first, then C-series (§5 updated).
3. **Combo strategy** → eager stacking (§5 updated).
4. **Scope** → all four sub-stages + new Stage 2.1.5 semantic dedup.
5. **Budget** → 12 h / 42 records.
6. **Compute topology** → two-instance: `coupang` for vLLM, `coupang2`
   for semantic / embedding workloads including SD-series dedup.

### Open decisions (later, if/when applicable)

- **Stage 1 re-pin**: if a Stage 1 branch iteration delivers
  `dedup_miss_rate ≤ 0.05` via semantic dedup on `coupang2`, the
  main orchestrator may re-pin `experiments_stage2/stage1_pinned/` to
  that iter's `stage_1_2_processed.jsonl`. This invalidates prior
  Stage 2 iter metrics, so any re-pin resets Stage 2 progress to
  `iter_00_baseline` on the new pin. Not planned by default — surfaced
  as an option.

### Default policies (no user decision needed)

- **Judge failure tolerance**: if one of the three judges (Friendli
  throttle etc.) fails to return for a stage, the iter proceeds with
  the remaining two judges but is tagged `PARTIAL_JUDGE` and is **not**
  eligible for auto-promotion — reviewer decides.
- **Scale-up trigger**: if the headline gate metric's per-judge range
  exceeds 0.20 for **three consecutive** iterations, main agent jumps
  to a one-shot 100-record resample of the top-3 candidates and picks
  the new winner from that.
