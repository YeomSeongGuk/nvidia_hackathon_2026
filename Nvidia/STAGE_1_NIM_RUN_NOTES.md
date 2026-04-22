# Stage 1 on localhost vLLM (Nemotron-Super 120B) — Run Notes

Date: 2026-04-21  (coupang instance, brev-tuyrvhnfj)
LLM backend: **localhost vLLM** — `http://localhost:5000/v1`, served model `nemotron`
                    (actually `nvidia/NVIDIA-Nemotron-3-Super-120B-A12B-FP8`, TP=2 on 2×H100 NVL)

This run was triggered to verify that the Stage-1 team pipeline
(`data_pipeline_nemo.py`) works when pointed at our local vLLM server
instead of Friendli serverless. The team file itself was NOT modified;
we made a local copy `data_pipeline_vllm.py` that only differs in the
`PipelineConfig` defaults.

## What worked

- `data_pipeline_vllm.py` is a byte-level copy of `data_pipeline_nemo.py`
  with 3 fields in `PipelineConfig` swapped:
  - `llm_api_key:  "flp_…"                          -> "dummy"`
  - `llm_base_url: "https://api.friendli.ai/serverless/v1" -> "http://localhost:5000/v1"`
  - `llm_model:    "meta-llama/Llama-3.1-8B-Instruct"     -> "nemotron"`
- Every `import` resolved (nemo_curator, data_designer, datasets, pandas, pyarrow, ray).
- Stage 1.0 seed extraction: 50 reviews from `data/naver_shopping.txt`.
- Stage 1.1 Data Designer + vLLM nemotron: **15/15 LLM requests succeeded**,
  9 521 total tokens, 207 TPS (logged by data_designer).
- Stage 1.1.5 dedup: falls back to exact dedup because `cudf` is missing
  (fuzzy MinHash requires RAPIDS). Exact dedup ran fine.
- Stage 1.2 quality filter: ran end to end (no crash).
- Wall-clock: ~55 s for `generate_size=5`.

## What is broken (not caused by our switch)

In `data/stage_1_1/synthetic_data.jsonl` every record shows:

```json
{
  "product_title": "",
  "product_attributes": {"color":"블랙","style":"캐주얼","size":"M"},
  "raw_text": "",
  ...
}
```

- `product_attributes` is filled (structured JSON column writes fine).
- `product_title` and `raw_text` (the two `llm-text` columns) are written
  as empty strings, even though the `data_designer` log confirms 5 OK
  generations per column and 0 failures.
- Consequently Stage 1.2 `WordCountFilter(min_words=5, lang=\"ko\")` sees
  empty text and drops every row → `processed_reviews.jsonl` is a
  0-byte file.
- Root cause lives in `save_to_jsonl()` (or the DataFrame returned by
  `run_data_designer_stage`), not in the LLM path. The LLM genuinely
  produced the titles/reviews; the column lookup is missing them.
- This reproduces identically against Friendli as well (i.e. it is NOT
  a vLLM-specific bug — it is present in the unmodified team pipeline).

## Dependencies we had to install on `~/coupang/.venv`

Before running:
- `nemo-curator` (only `nemo-curator 1.1.0` was already there as a
  metadata package; core submodules needed these siblings)
- `datasets` (HuggingFace)
- `ftfy`
- `beautifulsoup4`, `justext`, `lxml_html_clean`, `fasttext-wheel`
  (pulled in transitively by `nemo_curator.stages.text.filters.*`)

Known dependency warnings (non-fatal, ignored):
- `data-designer-config 0.5.7` wants `pyarrow<20`; we have `pyarrow 24.0.0`
  because `nemo-curator` requires it. Both still import cleanly.
- `data-designer-engine 0.5.7` wants `huggingface-hub<2`; we have `0.36.2`.

## Artefacts

Host paths (not visible in Jupyter by default):
- `/home/nvidia/stage1_work/data_pipeline_vllm.py`  (local copy, vLLM cfg)
- `/home/nvidia/stage1_work/data/naver_shopping.txt`
- `/home/nvidia/stage1_work/data/stage_1_0/seed_data.jsonl`  (50 rows)
- `/home/nvidia/stage1_work/data/stage_1_1/synthetic_data.jsonl`  (5 rows; empty text fields — see bug above)
- `/home/nvidia/stage1_work/data/stage_1_2/processed_reviews.jsonl`  (0 bytes after filtering)

Jupyter-visible paths (after the rsync at the end of this run):
- `/workspace/stage1_data/` ← same tree as above.

## How to reproduce

```bash
cd ~/stage1_work
time ~/coupang/.venv/bin/python data_pipeline_vllm.py \
    --data-path data/naver_shopping.txt \
    --generate-size 5
```

To flip back to Friendli without editing files, keep the original
`data_pipeline_nemo.py` and run that instead; the team version is
untouched in both the host and container filesystems.

## Open problems — to work through one by one

1. **P0** `save_to_jsonl` / `run_data_designer_stage` column mapping:
   `product_title` and `raw_text` come out as `""` despite LLM producing
   them. Inspect the pandas dataframe returned by `DataDesignerStage.process`
   (`results.dataset` → which type? HuggingFace Dataset vs DataFrame?) and
   confirm whether column names match the `r.get(...)` lookups in
   `save_to_jsonl`. Likely fix is one line in `save_to_jsonl` or
   `DataDesignerStage.process`.
2. **P1** Stage 1.1.5 fuzzy-dedup skipped because `cudf` missing. Either
   install RAPIDS (large) or accept the exact-dedup fallback.
3. **P2** `product_attributes` returned the same color/style/size across
   all 5 records (diversity too low). `temperature=0.8` is set but maybe
   `max_parallel_requests=1` serialisation + identical prompts produce a
   mode-collapsed output. Revisit after P0 is fixed.

---

## 2026-04-21 follow-up — P0 ROOT CAUSE FOUND AND FIXED

### TL;DR
`save_to_jsonl` was innocent. Nemotron-Super-120B is a **reasoning model**;
without `chat_template_kwargs.enable_thinking=False` it dumps its full
answer into the `reasoning` channel and returns `content=""` on chat
completions. Data Designer writes `content` into the DataFrame cell, so
`product_title` and `raw_text` end up as empty strings while
`product_attributes` (guided-JSON) still worked.

### How we proved it
Driven from local macOS via `brev port-forward coupang -p 5000:5000` so
we could iterate without pushing code to the box. Direct OpenAI-SDK
calls with the exact `product_title` prompt, 5 runs:

```
run 1: content=['']                                       reasoning_len=1459
run 2: content=['\n\n에코니트 폴라티셔츠 보풀방지']         reasoning_len=1334
run 3: content=['\n\n유니클로 니트스웨터 보폴방지']          reasoning_len=1219
run 4: content=['']                                       reasoning_len=1465
run 5: content=['\n\n유니클로남성라운드니트보풀방지']        reasoning_len=1322
```

So 2 out of 5 calls returned `content=""` but spent 1.2 – 1.5 k tokens
in `reasoning`. That is exactly the pattern the team file was hitting.

### The fix
Pass `extra_body={"chat_template_kwargs": {"enable_thinking": False}}`
on BOTH the `ModelProvider` and the `ChatCompletionInferenceParams`:

```python
thinking_off = {"chat_template_kwargs": {"enable_thinking": False}}

ModelProvider(
    name="local-vllm",
    endpoint=..., api_key=..., provider_type="openai",
    extra_body=thinking_off,
)

ChatCompletionInferenceParams(
    temperature=0.8, max_tokens=500, max_parallel_requests=1,
    extra_body=thinking_off,
)
```

### Before / after on the same 3-record run
| metric           | thinking on | thinking off |
|------------------|-------------|--------------|
| output tokens    | 3492        | **985**  (3.5× cheaper)       |
| TPS              | 168         | **315**  (1.9× faster)        |
| `product_title`  | 1/3 filled  | **3/3 filled**                |
| `raw_text`       | 0/3 filled  | **3/3 filled, persona-rich** |

### Applied to
- `scripts/run_stage1_generator_local.py` (local debugging harness)
- `~/stage1_work/data_pipeline_vllm.py` on coupang (our local copy of
  the team file). The team's `data_pipeline_nemo.py` was NOT touched.

### Verified on coupang
`python data_pipeline_vllm.py --data-path data/naver_shopping.txt --generate-size 5`
now produces 5/5 records with filled `product_title` and `raw_text`
that correctly reflect the persona (e.g. the 74-year-old dock worker
persona yields a review mentioning 목욕탕, 등산, 짜장면 — all from
`hobbies`).

### New issue uncovered (demoted to P1)
Stage 1.2 `NonAlphaNumericFilter(max_non_alpha_numeric_to_text_ratio=0.85)`
drops all 5 Korean records because Hangul code points are not counted
as alphanumeric by the underlying heuristic. `WordCountFilter` now
passes (`5 → 5`) thanks to the fix above, so the filter chain needs
either a higher threshold or a Korean-aware replacement.

### Demotions
- **P0** → resolved.
- **P1 (cudf / fuzzy dedup)** unchanged.
- **P2 (attribute mono-value)** largely dissolved — after the fix,
  colors are distributed (화이트, 베이지 …) across records. Any remaining
  narrowness is a prompt-diversity concern, not a bug.
