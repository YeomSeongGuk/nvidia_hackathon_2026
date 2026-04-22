"""Stage 2.2 - cluster extracted intents and assign canonical names.

Pipeline (full mode):
  1. Load ExtractedIntent[] from Stage 2.1 (or 2.1.5) output
  2. Group surface intents (excluding 'general_wear')
  3. Embed with sentence-transformers, GPU when available (default BGE-M3)
  4. Agglomerative clustering by cosine distance      [end of phase 1]
  5. (optional) LLM refine - split heterogeneous clusters into subgroups
  6. LLM canonicalizes each cluster to a Korean name
  7. (optional) LLM cross-merges canonicals that mean the same thing
  8. Write IntentCluster[] JSONL                     [end of phase 2]

Stage 2 PLAN §8 Option B phase-split support:
  --stage embed_cluster_only  -- phase 1 only (no LLM, no vLLM).
                                 Runs on coupang2. Writes raw clusters
                                 (canonical_name = "(unresolved)") to
                                 <output>.
  --stage llm_finalize         -- phase 2 only. Reads the raw clusters
                                 jsonl and runs refine + canonical +
                                 cross-merge against vLLM on coupang.
  --stage full (default)       -- both phases, single machine.

Input:   $STAGE_DATA_ROOT/stage_2_1/stage_2_1_extracted.jsonl
         (or a 2.1.5 deduped file with the same ExtractedIntent shape)
Output:  $STAGE_DATA_ROOT/stage_2_2/stage_2_2_clusters.jsonl
         (full / llm_finalize) OR stage_2_2_clusters_raw.jsonl
         (embed_cluster_only)

Usage:
  python -m pipelines.stage_2_2_canonicalize --refine --cross-merge
  python -m pipelines.stage_2_2_canonicalize --provider friendli --embed-device cuda

  # phase split:
  python -m pipelines.stage_2_2_canonicalize --stage embed_cluster_only \\
      --input stage_2_1_5_deduped.jsonl --output stage_2_2_clusters_raw.jsonl
  python -m pipelines.stage_2_2_canonicalize --stage llm_finalize --refine --cross-merge \\
      --input stage_2_2_clusters_raw.jsonl --output stage_2_2_clusters.jsonl
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np
from sklearn.cluster import AgglomerativeClustering
from sklearn.metrics.pairwise import cosine_similarity

from pipelines.config import Provider, data_root
from pipelines.llm_client import call_json, get_client, load_env
from pipelines.prompts import (
    CANONICAL_SYSTEM,
    CANONICAL_USER_TEMPLATE,
    CROSS_MERGE_SYSTEM,
    CROSS_MERGE_USER_TEMPLATE,
    REFINE_SYSTEM,
    REFINE_USER_TEMPLATE,
)
from pipelines.schemas import ExtractedIntent, IntentCluster

# Default embedding model - multilingual, strong Korean, GPU-friendly.
# On CPU we fall back to MiniLM (set via --embed-model).
DEFAULT_EMBED_MODEL = "BAAI/bge-m3"
DEFAULT_FALLBACK_EMBED_MODEL = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"


def load_stage1(path: Path) -> List[ExtractedIntent]:
    out = []
    with path.open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            out.append(ExtractedIntent.model_validate_json(line))
    return out


def group_by_raw_intent(
    extracted: List[ExtractedIntent],
) -> Tuple[List[str], Dict[str, List[str]]]:
    """Returns (unique_intents, intent_to_source_doc_ids)."""
    intent_to_docs: Dict[str, List[str]] = defaultdict(list)
    for e in extracted:
        intent_to_docs[e.raw_intent].append(e.source_curated_id)
    unique = sorted(intent_to_docs.keys())
    return unique, intent_to_docs


def _auto_device(hint: Optional[str] = None) -> str:
    """Return 'cuda' when available (unless caller forces one)."""
    if hint and hint != "auto":
        return hint
    try:
        import torch  # type: ignore

        if torch.cuda.is_available():
            return "cuda"
    except Exception:  # noqa: BLE001
        pass
    return "cpu"


def embed_intents(
    model_name: str,
    intents: List[str],
    device: Optional[str] = None,
    batch_size: int = 64,
) -> np.ndarray:
    """Embed surface intents to a shared vector space.

    # [NEMO-CURATOR] GPU swap: replace with
    #   from nemo_curator.modules.semantic_dedup import EmbeddingCreator
    #   EmbeddingCreator(embedding_model_name_or_path="BAAI/bge-m3",
    #                    cache_dir=..., embedding_batch_size=128)(dataset)
    # NeMo Curator runs embedding via Dask-cudf on multi-GPU. This path
    # uses sentence-transformers, which runs on CUDA when available.
    """
    from sentence_transformers import SentenceTransformer

    dev = _auto_device(device)
    print(f"[embed] loading {model_name} on {dev} ...", flush=True)
    model = SentenceTransformer(model_name, device=dev)

    # E5 family expects a 'query: ' / 'passage: ' prefix. For short surface-form
    # intent comparison, treat both sides as queries. BGE-M3 does not require
    # the prefix but is happy without one.
    is_e5 = "/multilingual-e5" in model_name or "intfloat/e5" in model_name
    texts = [f"query: {x}" for x in intents] if is_e5 else list(intents)
    print(
        f"[embed] encoding {len(texts)} intents "
        f"(e5_prefix={is_e5}, batch_size={batch_size}) ...",
        flush=True,
    )
    t0 = time.time()
    vecs = model.encode(
        texts,
        normalize_embeddings=True,
        show_progress_bar=False,
        batch_size=batch_size,
    )
    print(f"[embed] done in {time.time() - t0:.1f}s, shape={vecs.shape}", flush=True)
    return vecs


def cluster_intents(
    embeddings: np.ndarray, distance_threshold: float = 0.35
) -> np.ndarray:
    """Cluster intents so that near-duplicates in embedding space are grouped.

    # [NEMO-CURATOR] GPU swap: replace with
    #   from nemo_curator.modules.semantic_dedup import ClusteringModel
    #   ClusteringModel(id_column=..., max_iter=100, n_clusters=K,
    #                   clustering_output_dir=...)(embeddings_dataset)
    # NeMo Curator uses mini-batch K-means on GPU, then
    # SemanticClusterLevelDedup handles within-cluster similarity
    # thresholding. For ~20 surface intents this is overkill; hierarchical
    # clustering with a distance threshold produces the equivalent grouping.
    """
    sim = cosine_similarity(embeddings)
    dist = 1.0 - sim
    np.fill_diagonal(dist, 0.0)
    dist = np.clip(dist, 0.0, None)  # numerical safety

    model = AgglomerativeClustering(
        n_clusters=None,
        distance_threshold=distance_threshold,
        metric="precomputed",
        linkage="average",
    )
    labels = model.fit_predict(dist)
    return labels


def canonicalize(
    client, llm_model: str, members: List[str]
) -> str:
    user = CANONICAL_USER_TEMPLATE.format(
        members="\n".join(f"- {m}" for m in members)
    )
    parsed, _meta = call_json(client, llm_model, CANONICAL_SYSTEM, user, temperature=0.0)
    if parsed is None or not parsed.get("canonical_name"):
        # fallback: pick the shortest member as canonical
        return min(members, key=len)
    name = str(parsed["canonical_name"]).strip().strip("\"'`")
    return name or min(members, key=len)


def refine_cluster(
    client, llm_model: str, members: List[str], min_size_to_refine: int = 3
) -> List[List[str]]:
    """Ask LLM to split a heterogeneous cluster into semantically clean subgroups.

    - Clusters with < min_size_to_refine members are passed through untouched.
    - If the LLM output is malformed or does not cover all members exactly,
      we fall back to the original single group.
    """
    if len(members) < min_size_to_refine:
        return [members]

    user = REFINE_USER_TEMPLATE.format(members="\n".join(f"- {m}" for m in members))
    parsed, _meta = call_json(client, llm_model, REFINE_SYSTEM, user, temperature=0.0)
    if not parsed or "subgroups" not in parsed:
        return [members]

    raw = parsed["subgroups"]
    if not isinstance(raw, list):
        return [members]

    # Keep only members that actually appear in the input, dedupe.
    members_set = set(members)
    subgroups: List[List[str]] = []
    seen: set[str] = set()
    for sg in raw:
        if not isinstance(sg, list):
            continue
        cleaned = []
        for m in sg:
            if not isinstance(m, str):
                continue
            m = m.strip().strip("\"'`")
            if m in members_set and m not in seen:
                cleaned.append(m)
                seen.add(m)
        if cleaned:
            subgroups.append(cleaned)

    # Attach any missing members to their own subgroup so nothing is dropped.
    missing = [m for m in members if m not in seen]
    if missing:
        subgroups.append(missing)

    # If refinement collapsed into a single identical subgroup, return as-is.
    if not subgroups:
        return [members]
    return subgroups


def cross_cluster_merge(
    client,
    llm_model: str,
    clusters: List[IntentCluster],
) -> List[IntentCluster]:
    """LLM-driven cross-cluster merge.

    After primary embed+cluster+refine, independent clusters may still share
    semantics (e.g. "jogging-look" vs "workout-wear",
    "daily-look" vs "casual"). We feed the full list of canonical names plus
    their raw members to the LLM and ask it to propose merge groups.

    Merges are applied by picking the cluster with the highest evidence count
    in each group as the survivor and folding the others into it.
    """
    # Skip when there is nothing to compare. "일반" is the fixed bucket for
    # reviews with no concrete TPO and should never be merged into fashion
    # clusters.
    mergeable = [c for c in clusters if c.canonical_name != "일반"]
    if len(mergeable) < 2:
        return clusters

    lines = []
    for c in mergeable:
        members_str = ", ".join(f'"{m}"' for m in c.raw_intents)
        lines.append(
            f"- {c.canonical_name} (evidence={c.member_count}): [{members_str}]"
        )
    intent_list = "\n".join(lines)

    user = CROSS_MERGE_USER_TEMPLATE.format(intent_list=intent_list)
    parsed, _meta = call_json(client, llm_model, CROSS_MERGE_SYSTEM, user, temperature=0.0)
    if not parsed or "merge_groups" not in parsed:
        return clusters

    raw_groups = parsed.get("merge_groups") or []
    if not isinstance(raw_groups, list) or not raw_groups:
        return clusters

    # Map canonical name -> cluster (unique by canonical after earlier merge).
    name_to_cluster: Dict[str, IntentCluster] = {c.canonical_name: c for c in clusters}
    survivors: Dict[str, IntentCluster] = dict(name_to_cluster)

    for group in raw_groups:
        if not isinstance(group, list):
            continue
        names_in_group = [n for n in group if isinstance(n, str) and n in survivors]
        if len(names_in_group) < 2:
            continue

        # Pick survivor: highest evidence, ties broken by first appearance order
        survivor = max(
            names_in_group,
            key=lambda n: (survivors[n].member_count, -names_in_group.index(n)),
        )
        survivor_cluster = survivors[survivor]
        new_raw_intents = list(survivor_cluster.raw_intents)
        new_source_doc_ids = list(survivor_cluster.source_curated_ids)

        for n in names_in_group:
            if n == survivor:
                continue
            victim = survivors.pop(n, None)
            if victim is None:
                continue
            new_raw_intents.extend(victim.raw_intents)
            new_source_doc_ids.extend(victim.source_curated_ids)

        merged_cluster = IntentCluster(
            cluster_id=survivor_cluster.cluster_id,
            canonical_name=survivor,
            raw_intents=sorted(set(new_raw_intents)),
            source_curated_ids=sorted(set(new_source_doc_ids)),
            member_count=len(set(new_source_doc_ids)),
        )
        survivors[survivor] = merged_cluster
        print(
            f"  [cross-merge] {names_in_group} -> '{survivor}' "
            f"(evidence now {merged_cluster.member_count})",
            flush=True,
        )

    # Preserve original order by canonical_name
    seen = set()
    result: List[IntentCluster] = []
    for c in clusters:
        if c.canonical_name in seen:
            continue
        if c.canonical_name in survivors:
            result.append(survivors[c.canonical_name])
            seen.add(c.canonical_name)
    return result


# ---------------------------------------------------------------------------
# Phase split helpers (PLAN §8 Option B)
# ---------------------------------------------------------------------------

RAW_CLUSTER_PLACEHOLDER = "(unresolved)"


def _write_clusters(clusters: List[IntentCluster], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        for c in clusters:
            fh.write(c.model_dump_json() + "\n")


def load_clusters(path: Path) -> List[IntentCluster]:
    out: List[IntentCluster] = []
    with path.open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            out.append(IntentCluster.model_validate_json(line))
    return out


def _resolve_extracted_path(raw_clusters_path: Path, override: str) -> Path:
    """Find the ExtractedIntent jsonl that phase-1 clustered.

    Precedence:
      1. --extracted CLI override (if non-empty and exists).
      2. Same directory as raw clusters: stage_2_1_5_deduped.jsonl,
         then stage_2_1_extracted.jsonl.
      3. Parent directory fallback (for $STAGE_DATA_ROOT/stage_2_2 layout).
    """
    if override:
        p = Path(override)
        if p.exists():
            return p
        raise SystemExit(f"--extracted path not found: {p}")

    sibling = raw_clusters_path.parent
    for name in ("stage_2_1_5_deduped.jsonl", "stage_2_1_extracted.jsonl"):
        candidate = sibling / name
        if candidate.exists():
            return candidate

    # look one level up (e.g. when raw is under stage_2_2/ and extracted under stage_2_1/)
    up = raw_clusters_path.parent.parent
    for sub in ("stage_2_1_5", "stage_2_1"):
        for name in ("stage_2_1_5_deduped.jsonl", "stage_2_1_extracted.jsonl"):
            candidate = up / sub / name
            if candidate.exists():
                return candidate

    raise SystemExit(
        f"Could not auto-locate the extracted jsonl near {raw_clusters_path}. "
        f"Pass --extracted <path>."
    )


def phase1_embed_cluster(
    extracted: List[ExtractedIntent],
    *,
    embed_model: str,
    embed_device: str,
    embed_batch_size: int,
    threshold: float,
) -> List[IntentCluster]:
    """Phase 1: embed surface intents and agglomerative-cluster them.

    Returns a list of IntentCluster:
      - 'real' clusters with canonical_name="(unresolved)" placeholder;
        phase 2 replaces these via canonicalize(members).
      - a single '일반' cluster for general_wear intents (passes through
        phase 2 untouched).
    """
    unique, intent_to_docs = group_by_raw_intent(extracted)
    print(f"[group] {len(unique)} unique intents", flush=True)

    general_intents = [i for i in unique if i == "general_wear"]
    cluster_intents_list = [i for i in unique if i != "general_wear"]

    results: List[IntentCluster] = []

    if cluster_intents_list:
        embeddings = embed_intents(
            embed_model,
            cluster_intents_list,
            device=embed_device,
            batch_size=embed_batch_size,
        )
        labels = cluster_intents(embeddings, distance_threshold=threshold)

        label_to_members: Dict[int, List[str]] = defaultdict(list)
        for intent, lab in zip(cluster_intents_list, labels):
            label_to_members[int(lab)].append(intent)

        primary_groups = [
            label_to_members[lab] for lab in sorted(label_to_members.keys())
        ]
        print(
            f"[cluster] {len(primary_groups)} primary clusters found",
            flush=True,
        )
        for i, g in enumerate(primary_groups):
            print(f"  primary {i}: {g}", flush=True)

        for idx, members in enumerate(primary_groups):
            source_docs: List[str] = []
            for m in members:
                source_docs.extend(intent_to_docs[m])
            results.append(
                IntentCluster(
                    cluster_id=f"cluster_{idx:03d}",
                    canonical_name=RAW_CLUSTER_PLACEHOLDER,
                    raw_intents=members,
                    source_curated_ids=sorted(set(source_docs)),
                    member_count=len(source_docs),
                )
            )
    else:
        print("[warn] no non-general intents to cluster", flush=True)

    if general_intents:
        gw_docs: List[str] = []
        for m in general_intents:
            gw_docs.extend(intent_to_docs[m])
        results.append(
            IntentCluster(
                cluster_id=f"cluster_{len(results):03d}",
                canonical_name="일반",
                raw_intents=general_intents,
                source_curated_ids=sorted(set(gw_docs)),
                member_count=len(gw_docs),
            )
        )

    return results


def phase2_llm_finalize(
    raw_clusters: List[IntentCluster],
    intent_to_docs: Dict[str, List[str]],
    *,
    client,
    llm_model: Optional[str],
    skip_canonical: bool,
    refine: bool,
    refine_min_size: int,
    cross_merge: bool,
) -> List[IntentCluster]:
    """Phase 2: refine (optional) + canonical naming + cross-merge (optional).

    '일반' clusters pass through untouched. Unresolved clusters are
    re-expanded to their surface-intent lists and pushed through
    refine → canonicalize. source_curated_ids are rebuilt from
    intent_to_docs after each refine split.
    """
    fixed = [c for c in raw_clusters if c.canonical_name == "일반"]
    unresolved = [c for c in raw_clusters if c.canonical_name == RAW_CLUSTER_PLACEHOLDER]
    primary_groups = [c.raw_intents for c in unresolved]

    # Optional LLM refine - split heterogeneous clusters
    if refine:
        if client is None:
            raise SystemExit("refine=True requires an LLM client")
        refined_groups: List[List[str]] = []
        for g in primary_groups:
            subs = refine_cluster(
                client, llm_model, g, min_size_to_refine=refine_min_size
            )
            if len(subs) > 1:
                print(f"  [refine] split {g} -> {subs}", flush=True)
            refined_groups.extend(subs)
        final_groups = refined_groups
        print(
            f"[refine] {len(primary_groups)} -> {len(final_groups)} clusters",
            flush=True,
        )
    else:
        final_groups = primary_groups

    # Canonical naming per final group
    results: List[IntentCluster] = []
    for idx, members in enumerate(final_groups):
        if skip_canonical:
            canonical = min(members, key=len)
        elif client is None:
            raise SystemExit("canonicalize requires an LLM client")
        else:
            canonical = canonicalize(client, llm_model, members)
        source_docs: List[str] = []
        for m in members:
            source_docs.extend(intent_to_docs.get(m, []))
        cluster = IntentCluster(
            cluster_id=f"cluster_{idx:03d}",
            canonical_name=canonical,
            raw_intents=members,
            source_curated_ids=sorted(set(source_docs)),
            member_count=len(source_docs),
        )
        results.append(cluster)
        print(
            f"[canonical] {cluster.cluster_id}: {canonical}  <= {members}",
            flush=True,
        )

    # Append '일반' clusters (untouched)
    for c in fixed:
        results.append(
            IntentCluster(
                cluster_id=f"cluster_{len(results):03d}",
                canonical_name=c.canonical_name,
                raw_intents=c.raw_intents,
                source_curated_ids=c.source_curated_ids,
                member_count=c.member_count,
            )
        )

    # Optional cross-cluster merge
    if cross_merge:
        if client is None:
            raise SystemExit("cross-merge requires an LLM client")
        before = len(results)
        print(f"\n[cross-merge] reviewing {before} clusters ...", flush=True)
        results = cross_cluster_merge(client, llm_model, results)
        print(
            f"[cross-merge] {before} -> {len(results)} clusters",
            flush=True,
        )

    return results


def main(argv: List[str] | None = None) -> int:
    root = data_root()
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--input",
        default=str(root / "stage_2_1" / "stage_2_1_extracted.jsonl"),
        help=(
            "full / embed_cluster_only: ExtractedIntent jsonl (same shape as "
            "stage_2_1_extracted.jsonl; Stage 2.1.5 output also works).\n"
            "llm_finalize: IntentCluster jsonl produced by "
            "--stage embed_cluster_only."
        ),
    )
    parser.add_argument(
        "--output",
        default=str(root / "stage_2_2" / "stage_2_2_clusters.jsonl"),
    )
    parser.add_argument(
        "--stage",
        choices=["full", "embed_cluster_only", "llm_finalize"],
        default="full",
        help=(
            "full = embed + cluster + LLM finalize (single machine; default).\n"
            "embed_cluster_only = phase 1 only; writes raw clusters with "
            "canonical_name placeholder (no LLM, no vLLM).\n"
            "llm_finalize = phase 2 only; reads raw clusters from --input and "
            "runs refine + canonical + cross-merge against vLLM."
        ),
    )
    parser.add_argument(
        "--extracted",
        default="",
        help=(
            "(llm_finalize only) path to the ExtractedIntent jsonl that "
            "phase-1 clustered. Needed to rebuild the surface-intent "
            "→ source_curated_ids map for refine / aggregation. "
            "Defaults to <raw-clusters dir>/../stage_2_1_5_deduped.jsonl or "
            "stage_2_1_extracted.jsonl, whichever exists."
        ),
    )
    parser.add_argument(
        "--provider",
        choices=["nim", "friendli", "vllm"],
        default=None,
        help="LLM provider; falls back to $LLM_PROVIDER or nim",
    )
    parser.add_argument(
        "--llm-model",
        default=None,
        help="override the LLM model for this run (optional)",
    )
    parser.add_argument("--embed-model", default=DEFAULT_EMBED_MODEL)
    parser.add_argument(
        "--embed-device",
        default="auto",
        help="cuda | cpu | auto (default auto)",
    )
    parser.add_argument(
        "--embed-batch-size",
        type=int,
        default=64,
        help="sentence-transformers encode batch size",
    )
    parser.add_argument("--threshold", type=float, default=0.35)
    parser.add_argument("--skip-canonical", action="store_true",
                        help="skip LLM canonicalization; use shortest member")
    parser.add_argument("--refine", action="store_true",
                        help="use LLM to split over-merged clusters into subgroups")
    parser.add_argument("--refine-min-size", type=int, default=3,
                        help="only refine clusters with >= this many members")
    parser.add_argument("--cross-merge", action="store_true",
                        help="after canonical naming, let the LLM merge semantically duplicate clusters across different canonicals")
    args = parser.parse_args(argv)

    in_path = Path(args.input)
    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    # ------- phase 1 only (no LLM) -------------------------------------
    if args.stage == "embed_cluster_only":
        extracted = load_stage1(in_path)
        print(
            f"[load] {len(extracted)} extracted intents from {in_path}",
            flush=True,
        )
        raw_clusters = phase1_embed_cluster(
            extracted,
            embed_model=args.embed_model,
            embed_device=args.embed_device,
            embed_batch_size=args.embed_batch_size,
            threshold=args.threshold,
        )
        _write_clusters(raw_clusters, out_path)
        print(
            f"\n[done] wrote {len(raw_clusters)} raw clusters -> {out_path}",
            flush=True,
        )
        return 0

    # ------- phase 2 only (vLLM on coupang) -----------------------------
    if args.stage == "llm_finalize":
        load_env()
        raw_clusters = load_clusters(in_path)
        print(
            f"[load] {len(raw_clusters)} raw clusters from {in_path}",
            flush=True,
        )
        extracted_path = _resolve_extracted_path(in_path, args.extracted)
        extracted = load_stage1(extracted_path)
        _, intent_to_docs = group_by_raw_intent(extracted)
        print(
            f"[load] {len(extracted)} extracted intents from {extracted_path}  "
            f"({len(intent_to_docs)} unique surfaces)",
            flush=True,
        )
        client, llm_model = get_client(
            provider=args.provider,
            model_override=args.llm_model,
        )
        cfg = client._llm_config  # type: ignore[attr-defined]
        print(f"[stage_2_2] {cfg.describe()}", flush=True)

        results = phase2_llm_finalize(
            raw_clusters,
            intent_to_docs,
            client=client,
            llm_model=llm_model,
            skip_canonical=args.skip_canonical,
            refine=args.refine,
            refine_min_size=args.refine_min_size,
            cross_merge=args.cross_merge,
        )
        _write_clusters(results, out_path)
        print(
            f"\n[done] wrote {len(results)} clusters -> {out_path}",
            flush=True,
        )
        return 0

    # ------- full (default; both phases, single machine) ----------------
    load_env()
    extracted = load_stage1(in_path)
    print(
        f"[load] {len(extracted)} extracted intents from {in_path}",
        flush=True,
    )
    _, intent_to_docs = group_by_raw_intent(extracted)

    raw_clusters = phase1_embed_cluster(
        extracted,
        embed_model=args.embed_model,
        embed_device=args.embed_device,
        embed_batch_size=args.embed_batch_size,
        threshold=args.threshold,
    )

    need_llm = (
        (not args.skip_canonical) or args.refine or args.cross_merge
    )
    if need_llm:
        client, llm_model = get_client(
            provider=args.provider,
            model_override=args.llm_model,
        )
        cfg = client._llm_config  # type: ignore[attr-defined]
        print(f"[stage_2_2] {cfg.describe()}", flush=True)
    else:
        client, llm_model = None, None

    results = phase2_llm_finalize(
        raw_clusters,
        intent_to_docs,
        client=client,
        llm_model=llm_model,
        skip_canonical=args.skip_canonical,
        refine=args.refine,
        refine_min_size=args.refine_min_size,
        cross_merge=args.cross_merge,
    )
    _write_clusters(results, out_path)
    print(
        f"\n[done] wrote {len(results)} clusters -> {out_path}",
        flush=True,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
