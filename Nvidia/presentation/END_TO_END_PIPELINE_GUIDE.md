# End-to-End Pipeline Guide (10 records)

Complete walkthrough of the personalized fashion review corpus pipeline
from 10 input records → Stage 1 synthetic reviews → Stage 2 canonical
intents + natural queries → OpenSearch index + search demo.

**Total runtime** (10 records, after all setup): ~20-30 minutes end-to-end.

---

## 0. Prerequisites

You need three machines (all but the laptop are Brev GPU instances):

| machine | role | GPU | software |
|---|---|---|---|
| `coupang` | Stage 1 generation + Stage 2 intent extraction | 2×H100 PCIe | vLLM-serving Nemotron-Super-120B + `stage2_work` Python env |
| `coupang2` | Stage 1.1.5 semantic dedup | 1×H100 NVL 96GB | `cudf-cu12` + `cuml-cu12` + sentence-transformers (see `scripts/setup_coupang2.sh`) |
| `laptop` (Apple Silicon macOS) | OpenSearch demo + analysis | none | Docker + `.venv` with `sentence-transformers` + `requests` |

Verify both GPU instances are up:
```bash
brev ls
# coupang    RUNNING  COMPLETED  READY  dmz.h100x2.pcie
# coupang2   RUNNING  COMPLETED  READY  dmz.h100x2.pcie
```

If `coupang2` is new, run the one-time setup:
```bash
brev copy scripts/setup_coupang2.sh coupang2:/tmp/
brev exec coupang2 "bash /tmp/setup_coupang2.sh"
# ~5 minutes to install cudf 25.02 + cuml + sentence-transformers
```

---

## 1. Pull latest code to both GPU instances

If coupang or coupang2 has older code:
```bash
cd /Users/sgyeom/Nvidia
tar -cf /tmp/sync.tar \
    pipelines/ scripts/ requirements.txt
brev copy /tmp/sync.tar coupang:/tmp/sync.tar
brev exec coupang "cd /home/nvidia/stage2_work && tar -xf /tmp/sync.tar"
```

(`coupang2` doesn't need the full pipeline code, only `scripts/run_semantic_dedup_v2.py`
which is already synced.)

---

## 2. Stage 1 — generate 10 synthetic reviews (on `coupang`)

**Input**: raw Naver shopping reviews at `/home/nvidia/stage1_work/data/naver_shopping.txt`
**Output**: `/home/nvidia/stage1_work/data/stage_1_2/processed_reviews.jsonl` (~10 rows)
**Duration**: ~2 minutes

```bash
brev exec coupang "cd /home/nvidia/stage1_work && \
  export LLM_EXTRA_BODY='{\"chat_template_kwargs\":{\"enable_thinking\":false}}' && \
  /home/nvidia/coupang/.venv/bin/python data_pipeline_vllm.py \
    --data-path /home/nvidia/stage1_work/data/naver_shopping.txt \
    --generate-size 10"
```

**Expected volumes** (example from a 10-record run):
```
[Volume] Stage 1.0 (Seed Data): 10
[Volume] Stage 1.1 (Synthetic Data): 10
[Volume] Stage 1.1.5 (Deduped Data): 10    ← Python fallback; exact dedup only
[Volume] Stage 1.2 (Filtered Results): 10
```

> Note: the baseline in place on coupang is **iter_21** (our 8/10-gate best).
> It has the post-gen fashion filter (H12) so a few non-fashion rows
> might be dropped — volumes of `[10, <10, <10, <10]` are normal.

**Troubleshooting**:
- vLLM not responding → `brev exec coupang "curl -sS http://localhost:5000/v1/models"` should return `nemotron`.
- Dedup warning `No module named 'cudf'` is expected; exact dedup fallback runs.

---

## 3. Stage 1.1.5 — real semantic dedup (on `coupang2`)

The Stage 1 pipeline runs exact dedup only (no `cudf` on coupang).
To do real semantic dedup we shuttle the Stage 1.1 synthetic output to
coupang2 (which has cudf + cuml), run
`scripts/run_semantic_dedup_v2.py`, and bring the deduped result back.

**Duration**: ~30 seconds (embedding + K-means + pairwise cosine on 10 rows)

```bash
# 3a. Move Stage 1.1 synth output from coupang to coupang2
brev exec coupang "cp /home/nvidia/stage1_work/data/stage_1_1/synthetic_data.jsonl /tmp/s11.jsonl"
brev copy coupang:/tmp/s11.jsonl /tmp/s11.jsonl
brev copy /tmp/s11.jsonl coupang2:/home/nvidia/dedup/data/stage_1_1_synthetic.jsonl

# 3b. Run semantic dedup on coupang2
brev exec coupang2 "source /home/nvidia/dedup/.venv/bin/activate && \
  cd /home/nvidia/dedup && \
  python run_semantic_dedup_v2.py \
    --input  data/stage_1_1_synthetic.jsonl \
    --output output/stage_1_1_5_deduped.jsonl \
    --emb-mode title_attrs \
    --n-clusters 3 \
    --eps 0.18"

# 3c. Push deduped output back to coupang
brev copy coupang2:/home/nvidia/dedup/output/stage_1_1_5_deduped.jsonl /tmp/deduped.jsonl
brev copy /tmp/deduped.jsonl coupang:/home/nvidia/stage1_work/data/stage_1_1_5/deduped.jsonl
```

**Expected**:
```
[semdedup2] loaded 10 rows
[semdedup2] embeddings shape=(10, 384)
[semdedup2] cluster sizes: {0: 4, 1: 4, 2: 2}
[semdedup2] duplicate ids identified: 2  (sim_threshold=0.820, eps=0.18)
[semdedup2] DONE. in=10 out=8 removed=2
```

For tiny n=10 batches you may see 0 duplicates (no semantic collision) —
that's fine, just skip step 3 and proceed with Stage 1.1 output as-is.

---

## 4. Re-run Stage 1.2 quality filter on the deduped output (on `coupang`)

Because we swapped the Stage 1.1.5 file, re-run only the Hangul quality
filter (pure Python, no LLM). Easiest: just re-run the whole pipeline
with `--skip-generate` is not supported, so we manually re-filter:

```bash
brev exec coupang "cd /home/nvidia/stage1_work && \
  /home/nvidia/coupang/.venv/bin/python -c '
import json, re, os
HANGUL = re.compile(r\"[\\u3131-\\u318E\\uAC00-\\uD7A3]\")
src = \"/home/nvidia/stage1_work/data/stage_1_1_5/deduped.jsonl\"
dst = \"/home/nvidia/stage1_work/data/stage_1_2/processed_reviews.jsonl\"
os.makedirs(os.path.dirname(dst), exist_ok=True)
with open(src) as f, open(dst, \"w\") as o:
    kept = 0
    for line in f:
        r = json.loads(line)
        t = r.get(\"raw_text\", \"\")
        if isinstance(t, str) and 20 <= len(HANGUL.findall(t)) and len(t.strip()) <= 500:
            o.write(json.dumps(r, ensure_ascii=False) + chr(10))
            kept += 1
    print(f\"Stage 1.2 kept {kept} records\")
'"
```

`/home/nvidia/stage1_work/data/stage_1_2/processed_reviews.jsonl` is now
the input for Stage 2.

---

## 5. Stage 2 — extract → canonicalize → aggregate → expand (on `coupang`)

Using the new unified pipeline. vLLM loads once (~3 min) and processes
all four sub-stages.

**Duration**: ~5-8 minutes for 10 records (model load dominates)

```bash
brev exec coupang "cd /home/nvidia/stage2_work && \
  /home/nvidia/coupang/.venv/bin/python scripts/run_stage_2_pipeline_vllm.py \
    --input /home/nvidia/stage1_work/data/stage_1_2 \
    --output-root /home/nvidia/data \
    --stage-limit 10"
```

**Expected summary**:
```
[pipeline] SUMMARY
                      extracted: 10      # Stage 2.1
                       clusters: 3-5     # Stage 2.2 (after LLM refine + cross-merge)
                       analyzed: 3-5     # Stage 2.3 (= clusters post-merge)
                       expanded: 3-5     # Stage 2.4
       expanded_natural_queries: 15-25   # analyzed × 5 queries
```

**Output locations on coupang** (`/home/nvidia/data/`):
- `stage_2_1/stage_2_1_extracted.jsonl`
- `stage_2_2/stage_2_2_clusters.jsonl`
- `stage_2_3/analyzed_intents.jsonl`
- `stage_2_4/expanded_intents.jsonl`   ← what we'll index

**If you want to re-run a single sub-stage** (e.g. tune Stage 2.4):
```bash
# Re-run just Stage 2.4, skip the earlier stages
brev exec coupang "cd /home/nvidia/stage2_work && \
  python scripts/run_stage_2_pipeline_vllm.py \
    --skip-extract --skip-canonicalize --skip-aggregate \
    --n-queries 5"
```

---

## 6. Pull Stage 2 outputs to laptop

```bash
cd /Users/sgyeom/Nvidia
mkdir -p data/stage_2_pipeline_run
for STAGE in stage_2_1 stage_2_2 stage_2_3 stage_2_4; do
    brev copy coupang:/home/nvidia/data/$STAGE/*.jsonl \
              data/stage_2_pipeline_run/
done
ls -la data/stage_2_pipeline_run/
#   stage_2_1_extracted.jsonl   (10 lines)
#   stage_2_2_clusters.jsonl    (3-5 lines)
#   analyzed_intents.jsonl      (3-5 lines)
#   expanded_intents.jsonl      (3-5 lines)   ← this is what ES indexes
```

---

## 7. OpenSearch index + search demo (on `laptop`)

### 7a. Start OpenSearch (if not already)
```bash
docker ps | grep fashion-es || docker run -d --name fashion-es \
    -p 9200:9200 -p 9600:9600 \
    -e "discovery.type=single-node" \
    -e "plugins.security.disabled=true" \
    -e "OPENSEARCH_INITIAL_ADMIN_PASSWORD=DemoPass_2026!" \
    -e "OPENSEARCH_JAVA_OPTS=-Xms1g -Xmx1g" \
    opensearchproject/opensearch:2.18.0
```

Wait ~20s then verify:
```bash
curl -sS http://localhost:9200 | python3 -m json.tool | head
```

### 7b. Index the NEW run's expanded intents

The demo script defaults to `brev_snapshot/stage2_final/stage_2_4_expanded_intents.jsonl`
(260 records, production). To use your fresh 10-record run, pass
`--input`:

```bash
.venv/bin/python scripts/demo_es_query_search.py index \
    --input data/stage_2_pipeline_run/expanded_intents.jsonl
```

**Expected**:
```
[es] loaded 3 intent records from data/stage_2_pipeline_run/expanded_intents.jsonl
[es] exploded into 15 per-query documents
[es] embedding via sentence-transformers/...
[es] embeddings shape=(15, 384)
[es] index fashion_queries created
[es] indexed 15 documents
```

### 7c. Run queries

```bash
# BM25
.venv/bin/python scripts/demo_es_query_search.py search "출근룩 추천해줘" --k 3

# k-NN
.venv/bin/python scripts/demo_es_query_search.py knn "편하게 입을 티셔츠" --k 3

# Hybrid (BM25 + vector)
.venv/bin/python scripts/demo_es_query_search.py hybrid "겨울에 입는 따뜻한 옷" --k 3

# Drilldown on a specific intent
.venv/bin/python scripts/demo_es_query_search.py show "출근룩"
```

Each hit shows the matched natural_query, so you can see the
retrieval path transparently.

---

## 8. End-to-end volumes (10-record example)

```
Naver raw reviews ─(FASHION keyword filter + 10 sample)─▶  10 seed rows
                                                             │
                                      Stage 1.1 Data Designer │  (persona + LLM)
                                                             ▼
                                                          10 synthetic reviews
                                                             │
                                     Stage 1.1.5 semdedup (coupang2) │  cuml K-means + cos
                                                             ▼
                                                          8 deduped reviews
                                                             │
                                     Stage 1.2 Korean quality filter │
                                                             ▼
                                                          8 processed
                                                             │
                                     Stage 2.1 per-doc extract (vLLM)│
                                                             ▼
                                                          8 extracted intents
                                                             │
                                     Stage 2.2 embed+cluster+canonical│  BGE-M3 + LLM
                                                             ▼
                                                          ~3-5 canonical clusters
                                                             │
                                     Stage 2.3 aggregate (Python)    │
                                                             ▼
                                                          ~3-5 analyzed intents
                                                             │
                                     Stage 2.4 expand (vLLM)         │  5 queries / intent
                                                             ▼
                                                          ~3-5 expanded (15-25 queries)
                                                             │
                                     indexed to OpenSearch (laptop)  │
                                                             ▼
                                                          15-25 per-query docs,
                                                          BM25 + kNN searchable
```

---

## 9. Total time budget (10 records)

| step | location | time |
|---|---|---|
| Stage 1 generation | coupang | ~2 min |
| Stage 1.1.5 semdedup | coupang2 | ~0.5 min (incl. copy) |
| Stage 1.2 refilter | coupang | ~10 sec |
| Stage 2 unified pipeline | coupang | ~5-8 min (vLLM warmup dominates) |
| Pull outputs | local | ~10 sec |
| OpenSearch index | laptop | ~15 sec |
| Demo queries | laptop | ~1-2 sec each |
| **Total** | | **~10-15 min** |

The biggest chunks are (a) vLLM model load on coupang for Stage 2 and
(b) copying between coupang ↔ coupang2 for semdedup. For a single
presentation demo you can skip semdedup entirely (step 3) if the
audience doesn't ask about it — Stage 1's pandas exact-dedup is fine
for n=10.

---

## 10. One-shot script

All the above bundled into a single script:

```bash
# TODO: scripts/run_end_to_end_demo.sh
# (not shipped yet — compose from the snippets above or run each step
#  interactively so you can show the audience each intermediate volume.)
```

For the live demo, running each stage interactively lets you show:
- "here's one raw Naver review" (`head -1 naver_shopping.txt`)
- "here's one Stage 1.1 synthetic" (`head -1 .../stage_1_1_synthetic.jsonl`)
- "here's one Stage 2.4 expanded" (`head -1 .../expanded_intents.jsonl`)
- "and here's how a user query hits it" (the OpenSearch demo)

---

## 11. Cleanup

```bash
# Laptop
docker stop fashion-es && docker rm fashion-es

# coupang (per-run data, keep the pipeline code)
brev exec coupang "rm -rf /home/nvidia/data/stage_2_{1,2,3,4}"

# coupang2 (optional, just the scratch output)
brev exec coupang2 "rm -rf /home/nvidia/dedup/output/*"
```

---

## 12. Troubleshooting

| symptom | cause | fix |
|---|---|---|
| Stage 1 pipeline exits with "Connection refused :5000" | vLLM is not up on coupang | `brev exec coupang "systemctl --user status vllm"` or restart per the team's runbook |
| Stage 2 pipeline freezes at "loading vLLM ..." | Nemotron-Nano is downloading from HF (~30GB) | Wait 3-5 min first time; subsequent runs use cache |
| `cannot open shared object file: libcudart.so` on coupang2 | Harmless `numba_cuda` warning | Ignore — cudf/cuml work regardless |
| Stage 2.4 produces 0 expanded intents | All clusters got dropped at 2.3 (e.g. `--skip-general` with only a `일반` cluster) | Re-run without `--skip-general` or inspect `analyzed_intents.jsonl` |
| OpenSearch index returns 0 hits | Wrong index name (v1 = `fashion_intents` vs v2 = `fashion_queries`) | Use `demo_es_query_search.py` (v2, denormalized); v1 `demo_es_search_stage2.py` indexes `fashion_intents` |
| Embedding download fails on laptop with SSL error | Corporate MITM proxy missing CA | `demo_es_query_search.py` sets `SSL_CERT_FILE=/etc/ssl/cert.pem` automatically — check the file exists |
