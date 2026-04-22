"""Index synthetic fashion reviews + embeddings into OpenSearch, then demo
hybrid (BM25 + k-NN vector) search.

Usage:
    python scripts/demo_es_search.py index  # build index from iter_21 output
    python scripts/demo_es_search.py search "캐주얼 베이지 토트백"
    python scripts/demo_es_search.py knn    "산책 나들이 편한 가방"
    python scripts/demo_es_search.py hybrid "분당 직장인 출근룩"

The index is `fashion_reviews` on the local OpenSearch at 9200 (docker:
`fashion-es` container).
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import requests


ES = "http://localhost:9200"
INDEX = "fashion_reviews"
EMB_MODEL = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"


def _embed_batch(texts):
    from sentence_transformers import SentenceTransformer

    if not hasattr(_embed_batch, "_m"):
        _embed_batch._m = SentenceTransformer(EMB_MODEL)
    return _embed_batch._m.encode(
        texts,
        batch_size=32,
        show_progress_bar=False,
        convert_to_numpy=True,
        normalize_embeddings=True,
    )


def _compose(row) -> str:
    title = str(row.get("product_title") or "")
    rt = str(row.get("raw_text") or "")
    attrs = row.get("product_attributes") or {}
    if isinstance(attrs, str):
        try:
            attrs = json.loads(attrs)
        except Exception:
            attrs = {}
    attr_str = (
        f"{attrs.get('color','')} {attrs.get('style','')} {attrs.get('size','')}"
        if isinstance(attrs, dict) else ""
    )
    return f"{title} | {attr_str} | {rt}".strip()


def ensure_index():
    # Wipe existing index for a clean demo.
    requests.delete(f"{ES}/{INDEX}")
    body = {
        "settings": {
            "index.knn": True,
            "number_of_shards": 1,
            "number_of_replicas": 0,
            "analysis": {
                "analyzer": {"ko": {"type": "standard"}},
            },
        },
        "mappings": {
            "properties": {
                "doc_id": {"type": "keyword"},
                "product_id": {"type": "keyword"},
                "product_title": {"type": "text", "analyzer": "ko"},
                "raw_text": {"type": "text", "analyzer": "ko"},
                "rating": {"type": "integer"},
                "color": {"type": "keyword"},
                "style": {"type": "keyword"},
                "size": {"type": "keyword"},
                "persona_age": {"type": "integer"},
                "persona_sex": {"type": "keyword"},
                "persona_occupation": {"type": "keyword"},
                "persona_province": {"type": "keyword"},
                "persona_hobbies": {"type": "text", "analyzer": "ko"},
                "timestamp": {"type": "date"},
                "embedding": {
                    "type": "knn_vector",
                    "dimension": 384,
                    "method": {
                        "name": "hnsw",
                        "space_type": "cosinesimil",
                        "engine": "lucene",
                        "parameters": {"ef_construction": 128, "m": 16},
                    },
                },
            }
        },
    }
    r = requests.put(f"{ES}/{INDEX}", json=body)
    r.raise_for_status()
    print(f"[es] index {INDEX} created", flush=True)


def cmd_index(args):
    path = Path(args.input)
    rows = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            rows.append(json.loads(line))
    print(f"[es] loaded {len(rows)} rows from {path}", flush=True)

    # Compute embeddings.
    print(f"[es] embedding via {EMB_MODEL} ...", flush=True)
    texts = [_compose(r) for r in rows]
    embeddings = _embed_batch(texts)
    print(f"[es] embeddings shape={embeddings.shape}", flush=True)

    ensure_index()

    # Bulk index.
    bulk_lines = []
    for row, emb in zip(rows, embeddings):
        attrs = row.get("product_attributes") or {}
        if isinstance(attrs, str):
            try:
                attrs = json.loads(attrs)
            except Exception:
                attrs = {}
        persona = row.get("persona_info") or {}
        doc = {
            "doc_id": row.get("doc_id"),
            "product_id": row.get("product_id"),
            "product_title": row.get("product_title"),
            "raw_text": row.get("raw_text"),
            "rating": int((row.get("metadata") or {}).get("rating", 3)),
            "color": attrs.get("color"),
            "style": attrs.get("style"),
            "size": attrs.get("size"),
            "persona_age": persona.get("age"),
            "persona_sex": persona.get("sex"),
            "persona_occupation": persona.get("occupation"),
            "persona_province": persona.get("province"),
            "persona_hobbies": persona.get("hobbies"),
            "timestamp": row.get("timestamp"),
            "embedding": emb.tolist(),
        }
        bulk_lines.append(json.dumps({"index": {"_index": INDEX, "_id": doc["doc_id"]}}))
        bulk_lines.append(json.dumps(doc, ensure_ascii=False))
    body = "\n".join(bulk_lines) + "\n"
    r = requests.post(
        f"{ES}/_bulk",
        data=body.encode("utf-8"),
        headers={"Content-Type": "application/x-ndjson"},
    )
    r.raise_for_status()
    # Refresh so searches see new docs immediately.
    requests.post(f"{ES}/{INDEX}/_refresh")
    cnt = requests.get(f"{ES}/{INDEX}/_count").json()["count"]
    print(f"[es] indexed {cnt} documents", flush=True)


def _print_hit(hit, i):
    src = hit["_source"]
    print(
        f"  #{i} score={hit['_score']:.3f}  "
        f"⭐{src.get('rating')}  "
        f"{src.get('color','')}|{src.get('style','')}|{src.get('size','')}"
    )
    print(f"     title: {src.get('product_title')}")
    rt = src.get("raw_text") or ""
    print(f"     text : {rt[:120]}...")
    persona_brief = (
        f"{src.get('persona_age','')}세 "
        f"{src.get('persona_sex','')} "
        f"{src.get('persona_occupation','')} "
        f"{src.get('persona_province','')}"
    )
    print(f"     persona: {persona_brief}")


def cmd_search(args):
    q = args.query
    body = {
        "size": args.k,
        "query": {
            "multi_match": {
                "query": q,
                "fields": [
                    "product_title^3",
                    "raw_text^1",
                    "persona_hobbies^0.5",
                    "color^2",
                    "style^2",
                ],
            }
        },
    }
    r = requests.get(f"{ES}/{INDEX}/_search", json=body).json()
    hits = r["hits"]["hits"]
    print(f"[bm25] query={q!r}  total_hits={r['hits']['total']['value']}")
    for i, h in enumerate(hits):
        _print_hit(h, i + 1)


def cmd_knn(args):
    q = args.query
    emb = _embed_batch([q])[0].tolist()
    body = {
        "size": args.k,
        "query": {
            "knn": {
                "embedding": {"vector": emb, "k": args.k},
            }
        },
    }
    r = requests.get(f"{ES}/{INDEX}/_search", json=body).json()
    hits = r["hits"]["hits"]
    print(f"[knn ] query={q!r}  total_hits={r['hits']['total']['value']}")
    for i, h in enumerate(hits):
        _print_hit(h, i + 1)


def cmd_hybrid(args):
    """Score = 0.5 * BM25 + 0.5 * cosine similarity (normalised)."""
    q = args.query
    emb = _embed_batch([q])[0].tolist()
    # OpenSearch 2.x hybrid via bool should/script_score (pragmatic approach).
    body = {
        "size": args.k,
        "query": {
            "script_score": {
                "query": {
                    "multi_match": {
                        "query": q,
                        "fields": [
                            "product_title^3",
                            "raw_text^1",
                            "color^2",
                            "style^2",
                        ],
                    }
                },
                "script": {
                    "source": (
                        "double bm = _score;"
                        "double cos = cosineSimilarity(params.v, doc['embedding']) + 1.0;"
                        "return 0.5 * bm + 3.0 * cos;"
                    ),
                    "params": {"v": emb},
                },
            }
        },
    }
    r = requests.get(f"{ES}/{INDEX}/_search", json=body).json()
    hits = r.get("hits", {}).get("hits", [])
    print(f"[hybr] query={q!r}  total_hits={r.get('hits', {}).get('total', {}).get('value', 0)}")
    for i, h in enumerate(hits):
        _print_hit(h, i + 1)


def cmd_filter_knn(args):
    """k-NN restricted by metadata filter (e.g. rating, style)."""
    q = args.query
    emb = _embed_batch([q])[0].tolist()
    filters = []
    if args.rating is not None:
        filters.append({"term": {"rating": args.rating}})
    if args.style:
        filters.append({"term": {"style": args.style}})
    if args.color:
        filters.append({"term": {"color": args.color}})
    body = {
        "size": args.k,
        "query": {
            "bool": {
                "must": [{"knn": {"embedding": {"vector": emb, "k": args.k * 3}}}],
                "filter": filters,
            }
        },
    }
    r = requests.get(f"{ES}/{INDEX}/_search", json=body).json()
    hits = r["hits"]["hits"]
    print(
        f"[knn+filter] query={q!r} filter={filters}  "
        f"total_hits={r['hits']['total']['value']}"
    )
    for i, h in enumerate(hits):
        _print_hit(h, i + 1)


def main():
    parser = argparse.ArgumentParser()
    sp = parser.add_subparsers(dest="cmd", required=True)

    p_idx = sp.add_parser("index", help="build the index from an iter JSONL")
    p_idx.add_argument(
        "--input",
        default="experiments/iter_21_dedup_v2/output/stage_1_1_synthetic.jsonl",
    )

    p_s = sp.add_parser("search", help="BM25 text search")
    p_s.add_argument("query")
    p_s.add_argument("--k", type=int, default=5)

    p_k = sp.add_parser("knn", help="k-NN vector search")
    p_k.add_argument("query")
    p_k.add_argument("--k", type=int, default=5)

    p_h = sp.add_parser("hybrid", help="hybrid BM25 + vector search")
    p_h.add_argument("query")
    p_h.add_argument("--k", type=int, default=5)

    p_f = sp.add_parser("filter_knn", help="k-NN with metadata filter")
    p_f.add_argument("query")
    p_f.add_argument("--k", type=int, default=5)
    p_f.add_argument("--rating", type=int)
    p_f.add_argument("--style")
    p_f.add_argument("--color")

    args = parser.parse_args()
    {
        "index": cmd_index,
        "search": cmd_search,
        "knn": cmd_knn,
        "hybrid": cmd_hybrid,
        "filter_knn": cmd_filter_knn,
    }[args.cmd](args)


if __name__ == "__main__":
    sys.exit(main() or 0)
