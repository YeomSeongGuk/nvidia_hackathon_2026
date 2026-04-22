#!/bin/bash
# End-to-end demo: index Stage 2.4 natural_queries into OpenSearch, then
# compare BM25 vs k-NN vs hybrid retrieval on 5 natural-language queries.
#
# CORRECT retrieval semantics: user's query is matched against the STORED
# natural_queries (the queries each intent represents), NOT against the
# intent_keyword or a blob. Each intent's 5 natural_queries become 5
# separate documents, and results are collapsed by intent at read time.
#
# Prereq:
#   1. docker run ... opensearchproject/opensearch:2.18.0 on :9200
#   2. brev_snapshot/stage2_final/stage_2_4_expanded_intents.jsonl
#
# Run:  bash scripts/demo_stage2_query_search.sh  (from any directory)

set -euo pipefail

# Resolve repo root from this script's own location so the demo works
# regardless of where it is invoked from (repo root, scripts/, etc.).
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$REPO_ROOT"

PY="$REPO_ROOT/.venv/bin/python"
SCRIPT="$REPO_ROOT/scripts/demo_es_query_search.py"

if [ ! -x "$PY" ]; then
    echo "! Python venv not found at $PY"
    echo "  Create one: python3 -m venv $REPO_ROOT/.venv"
    echo "  Then install deps: $PY -m pip install sentence-transformers requests"
    exit 1
fi

echo "================================================================"
echo "DEMO: Stage 2.4 natural_queries → OpenSearch (BM25 + kNN + hybrid)"
echo "================================================================"
echo "repo_root = $REPO_ROOT"
echo

if ! curl -sS http://localhost:9200/_cluster/health >/dev/null; then
    echo "! OpenSearch not reachable on localhost:9200."
    echo "  docker run -d --name fashion-es -p 9200:9200 -p 9600:9600 \\"
    echo "    -e discovery.type=single-node -e plugins.security.disabled=true \\"
    echo "    opensearchproject/opensearch:2.18.0"
    exit 1
fi

echo "--- STEP 1: indexing 260 intents × 5 queries = 1300 docs ---"
"$PY" "$SCRIPT" index 2>&1 | grep -vE 'Loading weights|Warning:|BertModel|LOAD REPORT|^Key |embeddings.position_ids|^Notes:|can be ignored|^$'
echo

QUERIES=(
    "편하게 입는 면 티셔츠"
    "30대 직장인 출근룩"
    "운동할 때 좋은 옷"
    "나들이 가방 추천"
    "겨울 등산 갈 때 따뜻한 옷"
)

for Q in "${QUERIES[@]}"; do
    echo "================================================================"
    echo "USER QUERY: $Q"
    echo "================================================================"

    for MODE in search knn hybrid; do
        echo
        echo "--- [$MODE] ---"
        "$PY" "$SCRIPT" "$MODE" "$Q" --k 3 2>&1 | \
            grep -vE 'Loading weights|Warning:|BertModel|LOAD REPORT|^Key |embeddings.position_ids|^Notes:|can be ignored|^---|^$'
    done

    echo
done

echo "================================================================"
echo "DRILLDOWN: show all natural_queries for intent 『출근룩』"
echo "================================================================"
"$PY" "$SCRIPT" show "출근룩" 2>&1 | \
    grep -vE 'Loading weights|Warning:|BertModel|LOAD REPORT|^Key |embeddings.position_ids|^Notes:|can be ignored|^---|^$'

echo
echo "Done."
