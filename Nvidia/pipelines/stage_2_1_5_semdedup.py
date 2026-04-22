"""Stage 2.1.5 - embedding-based semantic dedup of extracted intents.

Sits between Stage 2.1 (per-doc extract) and Stage 2.2 (embed + cluster):

    stage_2_1_extracted.jsonl   (N rows, ExtractedIntent per doc)
          │
          │  signature-builder → short string per row
          │  BGE-M3 encode      → L2-normalised unit vectors
          │  pairwise cosine    → upper-triangle, greedy keep-first
          │  threshold filter
          ▼
    stage_2_1_5_deduped.jsonl   (M ≤ N rows, ExtractedIntent pass-through)
    stage_2_1_5_stats.json      (sidecar: kept / removed / avg_cosine / ...)

Runs on `coupang2` (embedding + CPU math) - PLAN §3c. Does NOT need vLLM.
A pass-through mode (`--threshold 1.0` or `--off`) emits a byte-identical
copy of the input so the Stage 2.2 input wiring is stable regardless of
whether the SD step is active for this iter.

Signature builders (match PLAN §5 signature-builder table):

| builder id | composition |
|---|---|
| full             | raw_intent | kw: k1,k2 | attrs: m=.|f=.|c=.|st=.|se=.           |
| signature_combo  | raw_intent | attrs: m=.|f=.|c=.|st=.|se=.                 |
| intent_only      | raw_intent                                                 |

All three lowercase and collapse internal whitespace before embedding.

CLI:
  python -m pipelines.stage_2_1_5_semdedup \\
      --input  stage_2_1_extracted.jsonl \\
      --output stage_2_1_5_deduped.jsonl \\
      --threshold 0.90 \\
      --embed-model BAAI/bge-m3 \\
      --device auto \\
      --signature-builder full
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import shutil
import sys
import time
from pathlib import Path
from typing import List, Optional

import numpy as np

from pipelines.schemas import ExtractedIntent

DEFAULT_EMBED_MODEL = "BAAI/bge-m3"
DEFAULT_FALLBACK_MODEL = (
    "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
)

_WS_RE = re.compile(r"\s+")

SIGNATURE_BUILDERS = ("full", "signature_combo", "intent_only")


# ---------------------------------------------------------------------------
# Signature builders
# ---------------------------------------------------------------------------

def _attrs_block(e: ExtractedIntent) -> str:
    a = e.attributes
    return (
        f"m={(a.material or '-').lower()}"
        f"|f={(a.fit or '-').lower()}"
        f"|c={(a.color or '-').lower()}"
        f"|st={(a.style or '-').lower()}"
        f"|se={(a.season or '-').lower()}"
    )


def _normalize(text: str) -> str:
    return _WS_RE.sub(" ", text.strip().lower())


def build_signature(e: ExtractedIntent, builder: str) -> str:
    if builder == "intent_only":
        return _normalize(e.raw_intent)
    if builder == "signature_combo":
        return _normalize(f"{e.raw_intent} | attrs: {_attrs_block(e)}")
    if builder == "full":
        kw = ",".join(e.extracted_keywords) if e.extracted_keywords else "-"
        return _normalize(
            f"{e.raw_intent} | kw: {kw} | attrs: {_attrs_block(e)}"
        )
    raise ValueError(f"unknown signature builder: {builder!r}")


# ---------------------------------------------------------------------------
# IO helpers
# ---------------------------------------------------------------------------

def _load_extracted(path: Path) -> List[ExtractedIntent]:
    out: List[ExtractedIntent] = []
    with path.open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            out.append(ExtractedIntent.model_validate_json(line))
    return out


def _write_extracted(path: Path, rows: List[ExtractedIntent]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        for r in rows:
            fh.write(r.model_dump_json() + "\n")


def _auto_device(hint: Optional[str]) -> str:
    if hint and hint != "auto":
        return hint
    try:
        import torch  # type: ignore

        if torch.cuda.is_available():
            return "cuda"
    except Exception:  # noqa: BLE001
        pass
    return "cpu"


# ---------------------------------------------------------------------------
# Core dedup
# ---------------------------------------------------------------------------

def dedup_by_cosine(
    signatures: List[str],
    embeddings: np.ndarray,
    threshold: float,
) -> tuple[List[int], List[int], int, float]:
    """Greedy near-dup removal: keep the first row of each near-dup group.

    Pairs with cosine similarity >= threshold are considered duplicates.
    Processing is left-to-right (stable), so row order in the input file
    determines which representative survives. Stage 2.1 emits rows in
    extraction order so the earliest doc_id wins.

    Returns:
      kept_idx:     list[int] of indices to keep (sorted ascending)
      removed_idx:  list[int] of dropped indices
      pairs_above:  int, number of unordered pairs at/above threshold
      avg_cos_kept: float, mean of max-cos-to-any-kept over kept rows
                    (informational: closer to 1 = less diverse kept set)
    """
    n = len(signatures)
    if n <= 1 or threshold >= 1.0:
        return list(range(n)), [], 0, 0.0

    # cosine similarity matrix (embeddings are L2-normalised by the caller)
    sim = embeddings @ embeddings.T  # (n, n)
    # count unordered pairs at/above threshold, excluding diagonal
    tri = np.triu(sim, k=1)
    pairs_above = int(np.sum(tri >= threshold))

    kept_mask = np.ones(n, dtype=bool)
    for i in range(n):
        if not kept_mask[i]:
            continue
        # mark all j > i with sim[i,j] >= threshold as duplicates of i
        for j in range(i + 1, n):
            if not kept_mask[j]:
                continue
            if sim[i, j] >= threshold:
                kept_mask[j] = False

    kept_idx = [i for i in range(n) if kept_mask[i]]
    removed_idx = [i for i in range(n) if not kept_mask[i]]

    # Informational diversity probe: for each kept row, find its max cosine
    # to any OTHER kept row. Mean of those maxes across the kept set.
    if len(kept_idx) >= 2:
        k_idx = np.array(kept_idx, dtype=int)
        k_sim = sim[np.ix_(k_idx, k_idx)]
        np.fill_diagonal(k_sim, -1.0)
        per_row_max = np.max(k_sim, axis=1)
        avg_cos_kept = float(np.mean(per_row_max))
    else:
        avg_cos_kept = 0.0

    return kept_idx, removed_idx, pairs_above, avg_cos_kept


def embed_signatures(
    signatures: List[str],
    model_name: str,
    device: str,
    batch_size: int = 64,
) -> np.ndarray:
    """Encode signatures with sentence-transformers (BGE-M3 default)."""
    from sentence_transformers import SentenceTransformer

    print(
        f"[semdedup] loading {model_name} on {device} ...",
        flush=True,
    )
    model = SentenceTransformer(model_name, device=device)
    t0 = time.time()
    vecs = model.encode(
        signatures,
        batch_size=batch_size,
        show_progress_bar=False,
        convert_to_numpy=True,
        normalize_embeddings=True,
    )
    print(
        f"[semdedup] encoded {len(signatures)} sigs in {time.time() - t0:.1f}s "
        f"shape={vecs.shape}",
        flush=True,
    )
    return vecs


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main(argv: List[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Stage 2.1.5 embedding-based semantic dedup of intents."
    )
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument(
        "--stats-out",
        default="",
        help="sidecar stats JSON (default: <output>.stats.json)",
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=0.90,
        help="cosine-similarity threshold (pairs >= this are dups)",
    )
    parser.add_argument(
        "--embed-model",
        default=DEFAULT_EMBED_MODEL,
        help=f"default {DEFAULT_EMBED_MODEL}",
    )
    parser.add_argument(
        "--device",
        default="auto",
        choices=["auto", "cpu", "cuda"],
    )
    parser.add_argument(
        "--signature-builder",
        default="full",
        choices=SIGNATURE_BUILDERS,
    )
    parser.add_argument("--embed-batch-size", type=int, default=64)
    parser.add_argument(
        "--off",
        action="store_true",
        help="pass-through mode: copy input to output, emit stats with "
        "removed=0 and kept=input count. Equivalent to --threshold 1.0.",
    )
    args = parser.parse_args(argv)

    in_path = Path(args.input)
    out_path = Path(args.output)
    stats_path = (
        Path(args.stats_out)
        if args.stats_out
        else out_path.with_name(out_path.stem + "_stats.json")
    )

    rows = _load_extracted(in_path)
    n_in = len(rows)
    print(f"[semdedup] loaded {n_in} ExtractedIntent rows from {in_path}", flush=True)

    if args.off or args.threshold >= 1.0 or n_in <= 1:
        # pass-through: copy file bytes if possible, else rewrite
        if n_in == 0:
            out_path.parent.mkdir(parents=True, exist_ok=True)
            out_path.write_text("", encoding="utf-8")
        else:
            shutil.copy2(in_path, out_path)
        stats = {
            "input_path": str(in_path),
            "output_path": str(out_path),
            "kept": n_in,
            "removed": 0,
            "pairs_checked": max(n_in * (n_in - 1) // 2, 0),
            "pairs_above_threshold": 0,
            "avg_cosine_of_kept": None,
            "selected_threshold": args.threshold,
            "signature_builder_used": args.signature_builder,
            "embed_model_used": None,
            "device_used": None,
            "mode": "pass_through",
            "timestamp": dt.datetime.now(dt.timezone.utc).isoformat(
                timespec="seconds"
            ),
        }
        stats_path.parent.mkdir(parents=True, exist_ok=True)
        stats_path.write_text(
            json.dumps(stats, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        print(
            f"[semdedup] pass-through: kept={n_in} stats={stats_path}",
            flush=True,
        )
        return 0

    signatures = [build_signature(r, args.signature_builder) for r in rows]
    device = _auto_device(args.device)

    embeddings = embed_signatures(
        signatures,
        model_name=args.embed_model,
        device=device,
        batch_size=args.embed_batch_size,
    )
    kept_idx, removed_idx, pairs_above, avg_cos = dedup_by_cosine(
        signatures, embeddings, threshold=args.threshold
    )

    kept_rows = [rows[i] for i in kept_idx]
    _write_extracted(out_path, kept_rows)

    stats = {
        "input_path": str(in_path),
        "output_path": str(out_path),
        "kept": len(kept_idx),
        "removed": len(removed_idx),
        "pairs_checked": n_in * (n_in - 1) // 2,
        "pairs_above_threshold": pairs_above,
        "avg_cosine_of_kept": round(avg_cos, 4) if avg_cos else 0.0,
        "selected_threshold": args.threshold,
        "signature_builder_used": args.signature_builder,
        "embed_model_used": args.embed_model,
        "device_used": device,
        "removed_indices": removed_idx,
        "removed_curated_ids": [rows[i].source_curated_id for i in removed_idx],
        "mode": "active",
        "timestamp": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
    }
    stats_path.parent.mkdir(parents=True, exist_ok=True)
    stats_path.write_text(
        json.dumps(stats, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    reduction = len(removed_idx) / n_in if n_in else 0.0
    print(
        f"[semdedup] DONE kept={len(kept_idx)} removed={len(removed_idx)} "
        f"reduction={reduction:.3f} pairs>=thr={pairs_above} "
        f"threshold={args.threshold} builder={args.signature_builder} "
        f"avg_cos_kept={avg_cos:.4f}",
        flush=True,
    )
    print(f"[semdedup] wrote {out_path}  stats {stats_path}", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
