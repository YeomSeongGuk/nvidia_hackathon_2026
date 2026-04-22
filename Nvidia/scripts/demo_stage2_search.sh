#!/bin/bash
# End-to-end demo: index Stage 2.4 expanded intents into OpenSearch,
# then compare BM25 vs k-NN vs hybrid retrieval on 4 natural-language queries.
#
# Prereq:
#   1. docker run ... opensearchproject/opensearch:2.18.0 on :9200
#   2. stage_2_4_expanded_intents.jsonl present
#
# Run:  bash scripts/demo_stage2_search.sh  (from any directory)

set -euo pipefail

# Resolve repo root from this script's own location so the demo works
# regardless of where it is invoked from.
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$REPO_ROOT"

PY="$REPO_ROOT/.venv/bin/python"
SCRIPT="$REPO_ROOT/scripts/demo_es_search_stage2.py"

if [ ! -x "$PY" ]; then
    echo "! Python venv not found at $PY"
    exit 1
fi

echo "================================================================"
echo "DEMO: Stage 2.4 → OpenSearch (dense_vector + BM25 + hybrid)"
echo "================================================================"
echo

# Guard: ES up?
if ! curl -sS http://localhost:9200/_cluster/health >/dev/null; then
    echo "! OpenSearch not reachable on localhost:9200."
    echo "  docker run -d --name fashion-es -p 9200:9200 -p 9600:9600 \\"
    echo "    -e discovery.type=single-node -e plugins.security.disabled=true \\"
    echo "    opensearchproject/opensearch:2.18.0"
    exit 1
fi

# Index (idempotent — script recreates the index).
echo "--- STEP 1: indexing 260 intents ---"
$PY $SCRIPT index 2>&1 | grep -E '^\[es\]' || true
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
    echo "QUERY: $Q"
    echo "================================================================"

    echo
    echo "--- [BM25 text] ---"
    $PY $SCRIPT search "$Q" --k 3 2>&1 | \
        grep -vE 'Loading weights|Warning:|BertModel|LOAD REPORT|Key |^---|embeddings.position_ids|^Notes:|can be ignored'

    echo
    echo "--- [kNN  vector] ---"
    $PY $SCRIPT knn "$Q" --k 3 2>&1 | \
        grep -vE 'Loading weights|Warning:|BertModel|LOAD REPORT|Key |^---|embeddings.position_ids|^Notes:|can be ignored'

    echo
    echo "--- [hybrid] ---"
    $PY $SCRIPT hybrid "$Q" --k 3 2>&1 | \
        grep -vE 'Loading weights|Warning:|BertModel|LOAD REPORT|Key |^---|embeddings.position_ids|^Notes:|can be ignored'

    echo
done

echo "================================================================"
echo "Example: show one specific intent end-to-end"
echo "================================================================"
$PY $SCRIPT show "출근룩" 2>&1 | \
    grep -vE 'Loading weights|Warning:|BertModel|LOAD REPORT|Key |^---|embeddings.position_ids|^Notes:|can be ignored'

echo
echo "Done."
