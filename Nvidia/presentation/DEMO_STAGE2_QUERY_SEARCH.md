# Stage 2.4 → OpenSearch Demo (v2: query-denormalized)

End-to-end query demo using the final `stage_2_4_expanded_intents.jsonl`
(260 canonical fashion-intent records). **Correct retrieval semantics**:
the user's natural-language query is matched against the STORED
natural_queries that each intent represents — not against the
intent_keyword alone or a concatenated blob.

## Why denormalize?

Stage 2.4 schema:
```json
{
  "intent_keyword": "출근룩",
  "natural_queries": [
    "오늘 출근할 때 입을 옷 추천해줘",
    "슬림핏 니트 원피스 찾고 있어",
    "면 소재 오버핏 셔츠 어디에 팔지?",
    "코튼 루즈핏 바지 추천해줘",
    "출근룩으로 편하면서도 단정하게 입는 거 뭐가 좋을까?"
  ],
  "mapped_attributes": [{"attribute_key":"color","attribute_value":"블랙","weight":0.169}, ...],
  "data_lineage": {"total_evidence_count": 581, "source_doc_ids": [...]}
}
```

`natural_queries` ARE the queries users type. So:
1. **Explode** each intent into N separate per-query docs (260 × 5 = 1300).
2. **Embed** each `query_text` individually — embedding space matches
   user-query distribution.
3. **Attach** intent metadata (keyword, attrs, evidence) to each doc.
4. **Collapse** top-k hits by `intent_keyword` at read time (keep
   highest-scoring per intent).

An earlier v1 demo embedded `intent_keyword + joined queries + attrs`
into a single per-intent vector. That matched user queries against a
blob, not against user-side text → weaker retrieval.

## Setup

```bash
# Once:
docker run -d --name fashion-es \
    -p 9200:9200 -p 9600:9600 \
    -e "discovery.type=single-node" \
    -e "plugins.security.disabled=true" \
    -e "OPENSEARCH_INITIAL_ADMIN_PASSWORD=DemoPass_2026!" \
    -e "OPENSEARCH_JAVA_OPTS=-Xms1g -Xmx1g" \
    opensearchproject/opensearch:2.18.0
```

## Run

```bash
bash scripts/demo_stage2_query_search.sh
```

## Example outputs

### Query: "편하게 입는 면 티셔츠"

```
[bm25] total_hits=283  (collapsed to 3 intents)
  #1 intent=『사우나룩』  evidence=43
     matched_query: 사우나 갈 때 입기 좋은 면 티셔츠 추천해줘
  #2 intent=『집콕룩』     evidence=8
     matched_query: 집에서 편하게 입을 면 티셔츠 추천해줘
  #3 intent=『당구장 티셔츠』
     matched_query: 당구장에서 편하게 입을 루즈핏 티셔츠 추천해줘

[knn ] total_hits=15  (collapsed to 3 intents)
  #1 intent=『집콕룩』     evidence=8   (cos 0.89)
     matched_query: 집에서 편하게 입을 면 티셔츠 추천해줘
  #2 intent=『홈웨어』     evidence=X   (cos 0.87)
  #3 intent=『사우나룩』   evidence=43  (cos 0.85)
```

Note the `matched_query` field — it shows WHICH stored query surfaced
this intent, making the retrieval path transparent.

### Query: "30대 직장인 출근룩"

```
[bm25] #1 intent=『출근룩』  evidence=581
       matched_query: 출근룩으로 편하면서도 단정하게 입는 거 뭐가 좋을까?
[knn ] #1 intent=『직장룩』  evidence=4
       matched_query: 캐주얼한 직장룩 코디 알려줘
```

### Query: "겨울 등산 갈 때 따뜻한 옷"

```
[bm25] #1 intent=『스노보드』  (matched "스노보드 타러 갈 때 편하고 따뜻한 회색 옷 있어?")
[knn ] #1 intent=『등산후복』  (matched "등산 다녀와서 입기 좋은 캐주얼한 옷 뭐 있어?")
[hybr] #1 intent=『스노보드』
```

## Index schema

| field | type | role |
|---|---|---|
| `query_text` | text | **the retrievable unit** — one of the natural_queries |
| `intent_keyword` | keyword | parent intent (what BM25 + kNN return after collapse) |
| `intent_position` | integer | 0..4, which of the 5 queries this is |
| `mapped_attributes` | nested | weighted attribute triples (metadata) |
| `top_attr_values` | keyword[] | top-10 attr values denormalised for BM25 |
| `total_evidence_count` | integer | # of Stage 2.1 extractions backing this intent |
| `source_doc_count` | integer | # of unique Stage 1 review doc_ids |
| **`embedding`** | **knn_vector** (384-d HNSW cosine) | embed(`query_text`) — user-query distribution |

## Retrieval modes

| mode | scoring | best for |
|---|---|---|
| `search` (BM25) | `multi_match` on `query_text^3 + intent_keyword_text^2 + top_attr_values^1.5`, most-fields | exact keyword / attr matches ("나들이", "30대") |
| `knn` | HNSW cosine on `embedding` | paraphrases, semantic neighbours |
| `hybrid` | `script_score`: `0.5 * bm25 + 3.0 * (cos + 1)` | production-ready default |

After scoring, `_collapse_by_intent(hits, k)` keeps the single
highest-scoring hit per `intent_keyword`.

## Example: show one intent

```
.venv/bin/python scripts/demo_es_query_search.py show "출근룩"
```

prints all 5 natural_queries for that intent plus its top-10 weighted
mapped_attributes (the metadata a downstream recommender would use).

## Cleanup

```bash
docker stop fashion-es && docker rm fashion-es
```

## Notes

- **Embedding model**: `sentence-transformers/paraphrase-multilingual-
  MiniLM-L12-v2` (384-d). Same model as our Stage 1.1.5 semantic
  dedup on coupang2 — shared vector space.
- **Corporate proxy on macOS**: SSL handshake to HuggingFace Hub fails
  without `SSL_CERT_FILE=/etc/ssl/cert.pem`. The script sets this
  automatically. After the first run the model is cached under
  `~/.cache/huggingface/hub/` and subsequent runs use
  `HF_HUB_OFFLINE=1` to avoid the (flaky) proxy round-trip.
- **Why k-NN returns different intents than BM25 for the same query**:
  BM25 is token-exact, kNN captures semantic neighbours. For "편하게
  입는 면 티셔츠", BM25 surfaces `당구장 티셔츠` (literal "편하게 입을
  루즈핏 티셔츠" keyword match) while kNN surfaces `집콕룩` (semantic
  "집에서 편하게 입을 면 티셔츠"). The hybrid query fuses both
  signals.
