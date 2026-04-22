# Stage 2.4 → OpenSearch Demo

End-to-end query demo using the final `stage_2_4_expanded_intents.jsonl`
(260 canonical fashion-intent records, each with 5 natural-language
queries + weighted mapped attributes + source doc lineage).

## Setup (one-time)

```bash
# 1. Start OpenSearch 2.18 single-node (ES 8.x equivalent, Apache 2 license).
#    docker.elastic.co is blocked by corporate proxy so we use OpenSearch
#    from Docker Hub.
docker run -d --name fashion-es \
    -p 9200:9200 -p 9600:9600 \
    -e "discovery.type=single-node" \
    -e "plugins.security.disabled=true" \
    -e "OPENSEARCH_INITIAL_ADMIN_PASSWORD=DemoPass_2026!" \
    -e "OPENSEARCH_JAVA_OPTS=-Xms1g -Xmx1g" \
    opensearchproject/opensearch:2.18.0

# 2. Wait ~30s then verify
curl http://localhost:9200
```

## Run the demo

```bash
bash scripts/demo_stage2_search.sh
```

This will:
1. Build the `fashion_intents` index (260 docs, 384-d dense vectors +
   BM25 text fields + nested mapped_attributes).
2. For each of 5 example queries, run **BM25**, **k-NN vector**, and
   **hybrid** retrieval; print top-3 hits with evidence counts +
   top-5 weighted attributes.

## Index schema

| field | type | notes |
|---|---|---|
| `intent_keyword` | `text + keyword` | canonical Korean intent keyword (e.g. "출근룩") |
| `natural_queries` | `text[]` | 5 user-style queries per intent |
| `mapped_attributes` | `nested` | `{attribute_key, attribute_value, weight}` |
| `top_attr_values` | `keyword[]` | top-10 attr values denormalised for BM25 |
| `total_evidence_count` | `integer` | number of Stage 2.1 extracted entries backing this intent |
| `source_doc_count` | `integer` | number of unique synthetic review docs (evidence) |
| `last_updated` | `date` | Stage 2.4 generation timestamp |
| **`embedding`** | **`knn_vector`** (384-d, HNSW cosine) | sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2 on `intent_keyword + natural_queries + top attrs` |

## Example queries

All queries below are natural Korean; see `demo_stage2_search_output.txt`
for the full demo log.

| query | BM25 top-1 | k-NN top-1 | why they differ |
|---|---|---|---|
| 편하게 입는 면 티셔츠 | 당구장 티셔츠 (score 19) | **사우나룩** (cos 0.87) | kNN finds semantic neighbours (sauna has many cotton-tee reviews) |
| 30대 직장인 출근룩 | **출근룩** (score 16, 581 evidence) | 퇴근후 (cos 0.70) | BM25 exact keyword wins; kNN picks adjacent "off-work" concept |
| 운동할 때 좋은 옷 | 헬스복 (score 11) | 홈트 (cos 0.88) | Both valid; kNN more abstract |
| 나들이 가방 추천 | **나들이** (score 24) | 면접가방 (cos 0.85) | BM25 exact; kNN finds "occasion bag" cluster |
| 겨울 등산 갈 때 따뜻한 옷 | **등산** (score 28) | **등산** (cos 0.84) | Both converge on the strongest intent |

Hybrid (BM25 + kNN, weight 0.5:3.0) pulls best of both — e.g. for
"겨울 등산 갈 때 따뜻한 옷" it surfaces `스노보드 / 보문산 / 등산 후 외출`,
all strong seasonal winter matches.

## Per-intent drilldown

`demo_es_search_stage2.py show <intent_keyword>` prints the full
intent record:

```
intent: 출근룩
  evidence=581  src_docs=581
  natural_queries:
    ▸ 오늘 출근할 때 입을 옷 추천해줘
    ▸ 슬림핏 니트 원피스 찾고 있어
    ▸ 면 소재 오버핏 셔츠 어디에 팔지?
    ▸ 코튼 루즈핏 바지 추천해줘
    ▸ 출근룩으로 편하면서도 단정하게 입는 거 뭐가 좋을까?
  mapped_attributes (top 15):
    color      = 블랙   (w=0.169)
    color      = 화이트  (w=0.134)
    style      = 캐주얼  (w=0.110)
    color      = 베이지  (w=0.083)
    fit        = 슬림핏  (w=0.057)
    material   = 니트   (w=0.026)
    material   = 면    (w=0.020)
    ...
```

## Cleanup

```bash
docker stop fashion-es && docker rm fashion-es
```

## Notes

- **Embedding model**: `paraphrase-multilingual-MiniLM-L12-v2` (384-d,
  HuggingFace). Same model we use on coupang2 for Stage 1.1.5 semantic
  dedup, so we share the index vector space.
- **Corporate proxy + macOS**: `openai.co` & `docker.elastic.co` are
  blocked; we use OpenSearch from Docker Hub. Python's sentence-
  transformers needs `SSL_CERT_FILE=/etc/ssl/cert.pem` to bypass the
  corporate MITM cert issue. This is set automatically by
  `demo_es_search_stage2.py`.
- **Why k-NN returns different top-1s than BM25**: the embedding is
  computed over `intent_keyword + 5 natural_queries + top attrs`,
  which captures semantic intent. BM25 keys on exact token overlap.
  Both are useful; the hybrid query combines them.
