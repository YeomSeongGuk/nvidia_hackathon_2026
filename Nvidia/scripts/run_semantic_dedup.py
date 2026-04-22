"""Semantic dedup runner for Stage 1.1 → 1.1.5.

Runs independently from the main pipeline. Takes a Stage 1.1 synthetic
JSONL file, creates sentence-transformer embeddings, clusters them with
cudf K-means, identifies near-duplicates via pairwise cosine similarity,
and writes a deduplicated JSONL.

Designed to run on a GPU instance that has cudf + RAPIDS installed but
does NOT need vLLM (unlike the main pipeline which uses vLLM on a
separate host).

Usage:
    python run_semantic_dedup.py \\
        --input  stage_1_1_synthetic.jsonl \\
        --output stage_1_1_5_deduped.jsonl \\
        --text-field raw_text \\
        --model-identifier sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2 \\
        --n-clusters 4 \\
        --eps 0.1
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
import tempfile
from pathlib import Path

import pandas as pd


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, help="Path to Stage 1.1 synthetic JSONL")
    parser.add_argument("--output", required=True, help="Path to Stage 1.1.5 deduped JSONL")
    parser.add_argument("--text-field", default="raw_text")
    parser.add_argument("--id-field", default="doc_id")
    parser.add_argument(
        "--model-identifier",
        default="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
        help="HuggingFace sentence-transformer model for embeddings.",
    )
    parser.add_argument(
        "--n-clusters", type=int, default=4,
        help="Number of K-means clusters. For n=50 records keep this small (3-8).",
    )
    parser.add_argument(
        "--eps", type=float, default=0.1,
        help="Epsilon for near-duplicate threshold. cosine-distance ≤ eps → dup. "
             "Typical: 0.05-0.15.",
    )
    parser.add_argument(
        "--embedding-dim", type=int, default=384,
        help="paraphrase-multilingual-MiniLM-L12-v2 = 384.",
    )
    parser.add_argument(
        "--cache-dir", default="/tmp/semdedup_cache",
        help="Scratch dir for K-means + pairwise intermediate outputs.",
    )
    args = parser.parse_args()

    print(f"[semdedup] loading {args.input}", flush=True)
    rows = []
    with open(args.input, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            rows.append(json.loads(line))
    n_in = len(rows)
    print(f"[semdedup] loaded {n_in} rows", flush=True)

    if n_in == 0:
        Path(args.output).write_text("", encoding="utf-8")
        print("[semdedup] empty input; wrote empty output", flush=True)
        return 0

    # Prepare a DataFrame with the ID and text fields
    df = pd.DataFrame(rows)
    if args.id_field not in df.columns:
        df[args.id_field] = [f"r_{i:05d}" for i in range(n_in)]

    # --- Step 1: create embeddings using sentence-transformers ---
    # We intentionally bypass NeMo Curator's EmbeddingCreatorStage and
    # use sentence-transformers directly for simplicity. It's tiny
    # (paraphrase-multilingual-MiniLM-L12-v2 ≈ 120MB) and doesn't need
    # Ray orchestration for n=50.
    print(f"[semdedup] loading model {args.model_identifier}", flush=True)
    from sentence_transformers import SentenceTransformer

    model = SentenceTransformer(args.model_identifier, device="cuda")
    print("[semdedup] encoding...", flush=True)
    texts = df[args.text_field].fillna("").astype(str).tolist()
    embeddings = model.encode(
        texts,
        batch_size=32,
        show_progress_bar=False,
        convert_to_numpy=True,
        normalize_embeddings=True,
    )
    print(f"[semdedup] embeddings shape={embeddings.shape}", flush=True)

    # Prepare a parquet with id + embeddings for SemanticDeduplicationWorkflow
    emb_dir = Path(args.cache_dir) / "embeddings"
    emb_dir.mkdir(parents=True, exist_ok=True)
    emb_parquet_path = emb_dir / "part-0.parquet"
    df_emb = pd.DataFrame({
        args.id_field: df[args.id_field].values,
        "embeddings": embeddings.tolist(),
    })
    df_emb.to_parquet(emb_parquet_path, index=False)
    print(f"[semdedup] wrote embeddings parquet to {emb_parquet_path}", flush=True)

    # --- Step 2: semantic dedup via cudf + SemanticDeduplicationWorkflow ---
    output_dir = Path(args.cache_dir) / "semdedup_output"
    cache_dir = Path(args.cache_dir) / "semdedup_cache"
    for d in (output_dir, cache_dir):
        if d.exists():
            shutil.rmtree(d)
        d.mkdir(parents=True, exist_ok=True)

    from nemo_curator.stages.deduplication.semantic.workflow import (
        SemanticDeduplicationWorkflow,
    )
    from nemo_curator.backends.experimental.ray_actor_pool.executor import (
        RayActorPoolExecutor,
    )

    workflow = SemanticDeduplicationWorkflow(
        input_path=str(emb_dir),
        output_path=str(output_dir),
        cache_path=str(cache_dir),
        n_clusters=max(2, min(args.n_clusters, n_in // 2)),
        eps=args.eps,
        id_field=args.id_field,
        embedding_field="embeddings",
        embedding_dim=args.embedding_dim,
        input_filetype="parquet",
        random_state=42,
    )

    import ray
    if not ray.is_initialized():
        ray.init(ignore_reinit_error=True, log_to_driver=False)

    print("[semdedup] running SemanticDeduplicationWorkflow...", flush=True)
    executor = RayActorPoolExecutor()
    workflow_stats = workflow.run(
        kmeans_executor=executor,
        pairwise_executor=executor,
    )
    print(f"[semdedup] workflow stats: {workflow_stats}", flush=True)

    # --- Step 3: load duplicate IDs and filter ---
    dup_dir = output_dir / "duplicates"
    dup_ids: set[str] = set()
    if dup_dir.exists():
        for pq in dup_dir.glob("*.parquet"):
            d = pd.read_parquet(pq)
            if args.id_field in d.columns:
                dup_ids.update(d[args.id_field].astype(str).tolist())

    print(f"[semdedup] duplicate ids identified: {len(dup_ids)}", flush=True)
    mask = ~df[args.id_field].astype(str).isin(dup_ids)
    deduped_df = df[mask].reset_index(drop=True)
    n_out = len(deduped_df)

    # Write deduped JSONL in the same shape as the input (preserving all fields)
    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        for _, row in deduped_df.iterrows():
            record = {k: row[k] for k in df.columns}
            # Convert numpy types to python-native for json
            for k, v in list(record.items()):
                if isinstance(v, (pd.Timestamp,)):
                    record[k] = v.isoformat()
                try:
                    json.dumps(v)
                except TypeError:
                    record[k] = str(v)
            f.write(json.dumps(record, ensure_ascii=False) + "\n")

    print(
        f"[semdedup] DONE. in={n_in} out={n_out} removed={n_in - n_out}  "
        f"(reduction={((n_in - n_out) / n_in):.3f}, eps={args.eps}, "
        f"k={workflow.n_clusters})", flush=True,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
