"""Index Stage 2.4 expanded intents into OpenSearch + demo hybrid search.

Stage 2.4 output (`brev_snapshot/stage2_final/stage_2_4_expanded_intents.jsonl`)
contains 260 canonical "intent" records, each with:
    - intent_keyword (e.g. "일상용")
    - natural_queries (5 user-style queries per intent)
    - mapped_attributes (weighted attribute triples)
    - data_lineage (source doc_ids, total evidence count)

We index each record with a dense_vector embedding of
`intent_keyword + all natural_queries`. At query time, user types a
natural-language request; we BM25 + kNN search for the matching intent
and show the canonical attributes + evidence counts as the result.

Usage:
    python scripts/demo_es_search_stage2.py index
    python scripts/demo_es_search_stage2.py search "편하게 입는 면 티셔츠"
    python scripts/demo_es_search_stage2.py knn    "가볍게 산책할 때 좋은 가방"
    python scripts/demo_es_search_stage2.py hybrid "30대 직장인 출근룩"
    python scripts/demo_es_search_stage2.py show "일상용"   # pick a specific intent
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

# Fix macOS Python cert path so HuggingFace model download works.
os.environ.setdefault("SSL_CERT_FILE", "/etc/ssl/cert.pem")
os.environ.setdefault("REQUESTS_CA_BUNDLE", "/etc/ssl/cert.pem")

import requests

ES = "http://localhost:9200"
INDEX = "fashion_intents"
EMB_MODEL = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
DEFAULT_INPUT = "brev_snapshot/stage2_final/stage_2_4_expanded_intents.jsonl"


def _embed(texts):
    from sentence_transformers import SentenceTransformer

    if not hasattr(_embed, "_m"):
        _embed._m = SentenceTransformer(EMB_MODEL)
    return _embed._m.encode(
        texts,
        batch_size=32,
        show_progress_bar=False,
        convert_to_numpy=True,
        normalize_embeddings=True,
    )


def _compose(rec) -> str:
    intent = str(rec.get("intent_keyword") or "")
    queries = rec.get("natural_queries") or []
    # Include top-weight attributes so "블랙" / "캐주얼" etc. also pull
    # in the intent vector direction (judges key on these too).
    top_attrs = []
    for a in (rec.get("mapped_attributes") or [])[:8]:
        top_attrs.append(str(a.get("attribute_value") or ""))
    return (
        f"[의도] {intent}. "
        f"[예시 질의] {' | '.join(queries)}. "
        f"[속성] {' '.join(top_attrs)}"
    )


def ensure_index():
    requests.delete(f"{ES}/{INDEX}")
    body = {
        "settings": {
            "index.knn": True,
            "number_of_shards": 1,
            "number_of_replicas": 0,
        },
        "mappings": {
            "properties": {
                "intent_keyword": {
                    "type": "text",
                    "analyzer": "standard",
                    "fields": {"raw": {"type": "keyword"}},
                },
                "natural_queries": {"type": "text", "analyzer": "standard"},
                "mapped_attributes": {
                    "type": "nested",
                    "properties": {
                        "attribute_key": {"type": "keyword"},
                        "attribute_value": {"type": "keyword"},
                        "weight": {"type": "float"},
                    },
                },
                "top_attr_values": {"type": "keyword"},
                "total_evidence_count": {"type": "integer"},
                "source_doc_count": {"type": "integer"},
                "last_updated": {"type": "date"},
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
    rows = []
    with open(args.input, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            rows.append(json.loads(line))
    print(f"[es] loaded {len(rows)} intent records from {args.input}", flush=True)

    print(f"[es] embedding via {EMB_MODEL} ...", flush=True)
    texts = [_compose(r) for r in rows]
    embeddings = _embed(texts)
    print(f"[es] embeddings shape={embeddings.shape}", flush=True)

    ensure_index()

    bulk_lines = []
    for rec, emb in zip(rows, embeddings):
        attrs = rec.get("mapped_attributes") or []
        top_vals = [str(a.get("attribute_value") or "") for a in attrs[:10]]
        lineage = rec.get("data_lineage") or {}
        doc = {
            "intent_keyword": rec.get("intent_keyword"),
            "natural_queries": rec.get("natural_queries") or [],
            "mapped_attributes": attrs,
            "top_attr_values": top_vals,
            "total_evidence_count": lineage.get("total_evidence_count"),
            "source_doc_count": len(lineage.get("source_doc_ids") or []),
            "last_updated": rec.get("last_updated"),
            "embedding": emb.tolist(),
        }
        bulk_lines.append(
            json.dumps({"index": {"_index": INDEX, "_id": rec.get("intent_keyword")}})
        )
        bulk_lines.append(json.dumps(doc, ensure_ascii=False))

    body = "\n".join(bulk_lines) + "\n"
    r = requests.post(
        f"{ES}/_bulk",
        data=body.encode("utf-8"),
        headers={"Content-Type": "application/x-ndjson"},
    )
    rj = r.json()
    if rj.get("errors"):
        first_err = next(
            (it["index"]["error"] for it in rj["items"] if "error" in it["index"]),
            None,
        )
        print(f"[es] bulk errors! first: {first_err}", flush=True)
    requests.post(f"{ES}/{INDEX}/_refresh")
    cnt = requests.get(f"{ES}/{INDEX}/_count").json()["count"]
    print(f"[es] indexed {cnt} documents", flush=True)


def _print_intent_hit(hit, i):
    src = hit["_source"]
    print(
        f"  #{i} score={hit['_score']:.3f}  "
        f"intent=『{src.get('intent_keyword')}』  "
        f"evidence={src.get('total_evidence_count')}  "
        f"src_docs={src.get('source_doc_count')}"
    )
    queries = src.get("natural_queries") or []
    for q in queries[:3]:
        print(f"     ▸ {q}")
    # Top-5 attrs, sorted by weight descending
    attrs = sorted(
        src.get("mapped_attributes") or [],
        key=lambda a: -float(a.get("weight") or 0),
    )[:6]
    attr_str = ", ".join(
        f"{a.get('attribute_key')}={a.get('attribute_value')}({float(a.get('weight') or 0):.3f})"
        for a in attrs
    )
    print(f"     attrs: {attr_str}")


def cmd_search(args):
    body = {
        "size": args.k,
        "query": {
            "multi_match": {
                "query": args.query,
                "fields": [
                    "intent_keyword^3",
                    "natural_queries^2",
                    "top_attr_values^1.5",
                ],
                "type": "most_fields",
            }
        },
    }
    r = requests.get(f"{ES}/{INDEX}/_search", json=body).json()
    hits = r["hits"]["hits"]
    print(f"[bm25] query={args.query!r}  total_hits={r['hits']['total']['value']}")
    for i, h in enumerate(hits):
        _print_intent_hit(h, i + 1)


def cmd_knn(args):
    emb = _embed([args.query])[0].tolist()
    body = {
        "size": args.k,
        "query": {"knn": {"embedding": {"vector": emb, "k": args.k}}},
    }
    r = requests.get(f"{ES}/{INDEX}/_search", json=body).json()
    hits = r["hits"]["hits"]
    print(f"[knn ] query={args.query!r}  total_hits={r['hits']['total']['value']}")
    for i, h in enumerate(hits):
        _print_intent_hit(h, i + 1)


def cmd_hybrid(args):
    emb = _embed([args.query])[0].tolist()
    body = {
        "size": args.k,
        "query": {
            "script_score": {
                "query": {
                    "multi_match": {
                        "query": args.query,
                        "fields": [
                            "intent_keyword^3",
                            "natural_queries^2",
                            "top_attr_values^1.5",
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
    print(f"[hybr] query={args.query!r}  total_hits={r.get('hits', {}).get('total', {}).get('value', 0)}")
    for i, h in enumerate(hits):
        _print_intent_hit(h, i + 1)


def cmd_show(args):
    """Show a specific intent by exact keyword match."""
    body = {
        "size": 1,
        "query": {"term": {"intent_keyword.raw": args.intent_keyword}},
    }
    r = requests.get(f"{ES}/{INDEX}/_search", json=body).json()
    hits = r["hits"]["hits"]
    if not hits:
        print(f"no intent match for {args.intent_keyword!r}")
        return
    src = hits[0]["_source"]
    print(f"intent: {src.get('intent_keyword')}")
    print(f"  evidence={src.get('total_evidence_count')}  "
          f"src_docs={src.get('source_doc_count')}")
    print(f"  natural_queries:")
    for q in src.get("natural_queries") or []:
        print(f"    ▸ {q}")
    print(f"  mapped_attributes (top 15):")
    attrs = sorted(
        src.get("mapped_attributes") or [],
        key=lambda a: -float(a.get("weight") or 0),
    )[:15]
    for a in attrs:
        print(
            f"    {a.get('attribute_key'):10} = {a.get('attribute_value'):10}  "
            f"(w={float(a.get('weight') or 0):.3f})"
        )


def main():
    parser = argparse.ArgumentParser()
    sp = parser.add_subparsers(dest="cmd", required=True)

    p_idx = sp.add_parser("index", help="build the intent index")
    p_idx.add_argument("--input", default=DEFAULT_INPUT)

    p_s = sp.add_parser("search", help="BM25 text search")
    p_s.add_argument("query")
    p_s.add_argument("--k", type=int, default=5)

    p_k = sp.add_parser("knn", help="k-NN vector search")
    p_k.add_argument("query")
    p_k.add_argument("--k", type=int, default=5)

    p_h = sp.add_parser("hybrid", help="hybrid BM25 + vector")
    p_h.add_argument("query")
    p_h.add_argument("--k", type=int, default=5)

    p_sh = sp.add_parser("show", help="show a specific intent")
    p_sh.add_argument("intent_keyword")

    args = parser.parse_args()
    {
        "index": cmd_index,
        "search": cmd_search,
        "knn": cmd_knn,
        "hybrid": cmd_hybrid,
        "show": cmd_show,
    }[args.cmd](args)


if __name__ == "__main__":
    sys.exit(main() or 0)
