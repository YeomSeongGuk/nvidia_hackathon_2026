"""Semantic dedup runner v2 — bypass NeMo Curator, use cuml directly.

iter_26-wave: NeMo Curator's SemanticDeduplicationWorkflow expects a
pylibcudf API (`Column.from_cuda_array_interface`) that was renamed to
`from_cuda_array_interface_obj` in newer cudf versions. Rather than
monkey-patch, compute K-means + pairwise cosine similarity ourselves
using cuml + cudf directly. Much simpler for n=50 and avoids version
skew entirely.

Algorithm:
1. Encode raw_text via sentence-transformers (GPU).
2. K-means (cuml) on embeddings → cluster assignments.
3. Within each cluster, find pairs with cosine distance ≤ eps.
4. For each dup cluster, keep the ONE record with the median norm;
   mark the rest for removal.
5. Write deduped JSONL preserving the original schema.

Usage:
    python run_semantic_dedup_v2.py \\
        --input  stage_1_1_synthetic.jsonl \\
        --output stage_1_1_5_deduped.jsonl \\
        --eps 0.1
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--text-field", default="raw_text")
    parser.add_argument("--id-field", default="doc_id")
    parser.add_argument(
        "--model-identifier",
        default="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
    )
    parser.add_argument("--n-clusters", type=int, default=4)
    parser.add_argument(
        "--eps", type=float, default=0.1,
        help="cosine-distance threshold; pairs with dist ≤ eps → dup cluster",
    )
    parser.add_argument(
        "--emb-mode",
        choices=["text", "title_attrs", "title_attrs_text"],
        default="title_attrs_text",
        help="What to embed: raw_text only / title+attrs only / title+attrs+text",
    )
    args = parser.parse_args()

    print(f"[semdedup2] loading {args.input}", flush=True)
    rows = []
    with open(args.input, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            rows.append(json.loads(line))
    n_in = len(rows)
    print(f"[semdedup2] loaded {n_in} rows", flush=True)

    if n_in == 0:
        Path(args.output).write_text("", encoding="utf-8")
        print("[semdedup2] empty input; wrote empty output", flush=True)
        return 0

    df = pd.DataFrame(rows)
    if args.id_field not in df.columns:
        df[args.id_field] = [f"r_{i:05d}" for i in range(n_in)]

    # --- 1. Embeddings ---
    print(f"[semdedup2] loading {args.model_identifier}", flush=True)
    from sentence_transformers import SentenceTransformer

    model = SentenceTransformer(args.model_identifier, device="cuda")

    def _compose(row) -> str:
        title = str(row.get("product_title") or "")
        rt = str(row.get(args.text_field) or "")
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
        if args.emb_mode == "text":
            return rt
        if args.emb_mode == "title_attrs":
            return f"{title} | {attr_str}".strip()
        # title_attrs_text (default)
        return f"{title} | {attr_str} | {rt}".strip()

    texts = [_compose(r) for r in rows]
    emb = model.encode(
        texts,
        batch_size=32,
        show_progress_bar=False,
        convert_to_numpy=True,
        normalize_embeddings=True,
    )
    print(
        f"[semdedup2] embeddings shape={emb.shape} "
        f"(mode={args.emb_mode})", flush=True,
    )

    # --- 2. K-means via cuml ---
    import cudf
    import cupy as cp
    from cuml.cluster import KMeans as cuKMeans

    emb_gpu = cp.asarray(emb, dtype=cp.float32)
    n_clusters = max(2, min(args.n_clusters, n_in // 2))
    print(f"[semdedup2] running cuml KMeans with k={n_clusters}", flush=True)
    km = cuKMeans(n_clusters=n_clusters, random_state=42, max_iter=300, n_init=4)
    km.fit(emb_gpu)
    labels = km.labels_
    if hasattr(labels, "to_numpy"):
        labels_np = labels.to_numpy()
    else:
        labels_np = cp.asnumpy(labels)
    print(
        f"[semdedup2] cluster sizes: "
        f"{pd.Series(labels_np).value_counts().sort_index().to_dict()}",
        flush=True,
    )

    # --- 3. Within-cluster pairwise cosine, mark dups ---
    # For each cluster, build pairwise similarity matrix. Since embeddings
    # are L2-normalised, cosine similarity = dot product. Distance =
    # 1 - similarity. Pairs with distance ≤ eps are near-dups.
    dup_ids: set[str] = set()
    doc_ids = df[args.id_field].astype(str).to_numpy()

    sim_threshold = 1.0 - args.eps  # cosine sim ≥ (1-eps) → dup
    for c in range(n_clusters):
        idx = np.where(labels_np == c)[0]
        if len(idx) < 2:
            continue
        sub = emb[idx]  # (k, d)
        sim = sub @ sub.T  # (k, k) cosine similarity (unit vectors)
        # Find pairs above threshold (excluding diagonal)
        for i in range(len(idx)):
            if doc_ids[idx[i]] in dup_ids:
                continue
            for j in range(i + 1, len(idx)):
                if sim[i, j] >= sim_threshold:
                    # mark j as duplicate of i
                    dup_ids.add(doc_ids[idx[j]])

    print(
        f"[semdedup2] duplicate ids identified: {len(dup_ids)} "
        f"(sim_threshold={sim_threshold:.3f}, eps={args.eps})",
        flush=True,
    )

    # --- 4. Filter & write ---
    mask = ~df[args.id_field].astype(str).isin(dup_ids)
    deduped_df = df[mask].reset_index(drop=True)
    n_out = len(deduped_df)

    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        for _, row in deduped_df.iterrows():
            record = {k: row[k] for k in df.columns}
            for k, v in list(record.items()):
                try:
                    json.dumps(v, ensure_ascii=False)
                except TypeError:
                    record[k] = str(v)
            f.write(json.dumps(record, ensure_ascii=False) + "\n")

    print(
        f"[semdedup2] DONE. in={n_in} out={n_out} removed={n_in - n_out}  "
        f"(reduction={((n_in - n_out) / n_in):.3f}, k={n_clusters}, eps={args.eps})",
        flush=True,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
