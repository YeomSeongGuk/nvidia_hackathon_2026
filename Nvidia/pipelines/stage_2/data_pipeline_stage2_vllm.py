"""Unified Stage 2 pipeline: extract → canonicalize → aggregate → expand.

Single-process orchestrator that mirrors the Stage 1 layout at
`pipelines/stage_1/data_pipeline_vllm.py`. Loads vLLM (Nemotron-Nano)
**once**, then runs all four Stage 2 sub-stages in sequence:

    Stage 2.1 extract       (curated docs -> per-doc intent + attrs)
    Stage 2.2 canonicalize  (raw intents  -> canonical clusters)
    Stage 2.3 aggregate     (clusters     -> per-intent attr profile;  pure Python)
    Stage 2.4 expand        (aggregated   -> natural-language queries)

Each stage writes its output under `$STAGE_DATA_ROOT/stage_2_N/`
exactly where the standalone `scripts/run_stage_2_N_vllm.py` drivers
would. This way iter_run_stage2.py and existing eval judges still find
the artifacts in the same place.

Typical use:

    # run the whole pipeline end-to-end
    cd ~/stage2_work
    python -m pipelines.stage_2.data_pipeline_stage2_vllm \\
        --input  /home/nvidia/data/stage_1_2 \\
        --model  nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B-BF16

    # skip the expensive 2.1 extract step and reuse its output
    python -m pipelines.stage_2.data_pipeline_stage2_vllm \\
        --skip-extract

    # only run through Stage 2.3 (skip 2.4 expansion)
    python -m pipelines.stage_2.data_pipeline_stage2_vllm \\
        --stop-after aggregate

Env / CLI knobs:

    --input         Stage 1.2 curated dir OR a single .jsonl
                    default: $STAGE_DATA_ROOT/stage_1_2
    --output-root   where stage_2_1/..stage_2_4/ land
                    default: $STAGE_DATA_ROOT
    --model         HF id for the vLLM model (used across 2.1, 2.2, 2.4)
                    default: env VLLM_OFFLINE_MODEL or Nemotron-Nano-30B-BF16
    --dtype         vLLM dtype (default env VLLM_DTYPE or "auto")
    --gpu-mem-util  0.0-1.0 fraction of VRAM vLLM may use
    --embed-model   Stage 2.2 embedding model (default BAAI/bge-m3)
    --embed-device  cuda|cpu|auto (default auto)
    --cluster-threshold   Stage 2.2 agglomerative threshold (default 0.35)
    --refine-min-size     Stage 2.2 cluster size threshold for LLM refine (default 3)
    --skip-refine         disable LLM refine
    --skip-cross-merge    disable LLM cross-cluster merge
    --skip-general        drop the 일반/general_wear cluster at Stage 2.3
    --aggregate-top-k     Stage 2.3 top-k attribute values per key (default 3)
    --n-queries           Stage 2.4 queries per canonical intent (default 5)
    --stage-limit         cap input docs for Stage 2.1 (default 0 = all)
    --skip-extract, --skip-canonicalize, --skip-aggregate, --skip-expand
    --stop-after {extract|canonicalize|aggregate|expand}

After completion the outputs land at:

    $STAGE_DATA_ROOT/stage_2_1/stage_2_1_extracted.jsonl
    $STAGE_DATA_ROOT/stage_2_2/stage_2_2_clusters.jsonl
    $STAGE_DATA_ROOT/stage_2_3/analyzed_intents.jsonl
    $STAGE_DATA_ROOT/stage_2_4/expanded_intents.jsonl

A summary line is printed at each step so a reviewer can see volumes
collapse: 50 curated → 50 extracted → 15 clusters → 15 analyzed →
15 × 5 = 75 natural_queries.
"""
from __future__ import annotations

import argparse
import os
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, List, Optional

# Make `pipelines.*` importable when this file is executed as a script
# (e.g. `python pipelines/stage_2/data_pipeline_stage2_vllm.py`).
_HERE = Path(__file__).resolve().parent
_PROJECT_ROOT = _HERE.parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from pipelines.config import data_root  # noqa: E402
from pipelines.llm_client import load_env  # noqa: E402
from pipelines.schemas import (  # noqa: E402
    AnalyzedIntent,
    CuratedDoc,
    ExtractedIntent,
    ExpandedIntent,
    IntentCluster,
)
from pipelines.vllm_adapter import (  # noqa: E402
    VLLMOfflineClient,
    expand_batch_vllm_offline,
    extract_batch_vllm_offline,
    write_jsonl,
)

# Stage 2.2 library functions.
from pipelines.stage_2_2_canonicalize import (  # noqa: E402
    canonicalize,
    cluster_intents,
    cross_cluster_merge,
    embed_intents,
    group_by_raw_intent,
    load_stage1,
    refine_cluster,
)

# Stage 2.3 library functions.
from pipelines.stage_2_3_aggregate import (  # noqa: E402
    aggregate_cluster,
    load_jsonl as s23_load_jsonl,
    merge_clusters_by_canonical,
)


# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

@dataclass
class StageConfig:
    # I/O
    input_path: Path
    output_root: Path
    # vLLM
    model_id: str = "nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B-BF16"
    dtype: str = "auto"
    gpu_mem_util: Optional[float] = None
    # Stage 2.1
    stage_limit: int = 0
    # Stage 2.2
    embed_model: str = "BAAI/bge-m3"
    embed_device: str = "auto"
    cluster_threshold: float = 0.35
    refine_min_size: int = 3
    skip_refine: bool = False
    skip_cross_merge: bool = False
    # Stage 2.3
    aggregate_top_k: int = 3
    skip_general: bool = False
    # Stage 2.4
    n_queries: int = 5
    # Orchestration
    skip_extract: bool = False
    skip_canonicalize: bool = False
    skip_aggregate: bool = False
    skip_expand: bool = False
    stop_after: Optional[str] = None  # "extract" | "canonicalize" | "aggregate" | "expand"

    # Per-stage output paths (filled in by prepare_paths)
    out_2_1: Path = field(default=Path())
    out_2_2: Path = field(default=Path())
    out_2_3: Path = field(default=Path())
    out_2_4: Path = field(default=Path())


def prepare_paths(cfg: StageConfig) -> None:
    cfg.output_root.mkdir(parents=True, exist_ok=True)
    cfg.out_2_1 = cfg.output_root / "stage_2_1" / "stage_2_1_extracted.jsonl"
    cfg.out_2_2 = cfg.output_root / "stage_2_2" / "stage_2_2_clusters.jsonl"
    cfg.out_2_3 = cfg.output_root / "stage_2_3" / "analyzed_intents.jsonl"
    cfg.out_2_4 = cfg.output_root / "stage_2_4" / "expanded_intents.jsonl"
    for p in (cfg.out_2_1, cfg.out_2_2, cfg.out_2_3, cfg.out_2_4):
        p.parent.mkdir(parents=True, exist_ok=True)


def _iter_curated(input_path: Path) -> List[CuratedDoc]:
    """Read CuratedDocs from a file or a directory of .jsonl files."""
    if input_path.is_dir():
        files = sorted(input_path.glob("*.jsonl"))
        if not files:
            raise FileNotFoundError(f"no .jsonl files under {input_path}")
    else:
        files = [input_path]
    docs: list[CuratedDoc] = []
    for f in files:
        for line in f.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            docs.append(CuratedDoc.model_validate_json(line))
    return docs


# ---------------------------------------------------------------------------
# vLLM orchestration
# ---------------------------------------------------------------------------

def _load_vllm(cfg: StageConfig):
    """Load the vLLM model once and return it. Imported lazily so this
    module is importable on a CPU-only box."""
    from vllm import LLM  # lazy import (GPU-only)

    kwargs: dict[str, Any] = {
        "model": cfg.model_id,
        "trust_remote_code": True,
        "dtype": cfg.dtype,
    }
    if cfg.gpu_mem_util is not None:
        kwargs["gpu_memory_utilization"] = float(cfg.gpu_mem_util)
    print(f"[pipeline] loading vLLM ({cfg.model_id}, dtype={cfg.dtype}) ...", flush=True)
    llm = LLM(**kwargs)
    print("[pipeline] vLLM ready", flush=True)
    return llm


# ---------------------------------------------------------------------------
# Stage 2.1 — extract
# ---------------------------------------------------------------------------

def run_stage_2_1_extract(cfg: StageConfig, llm) -> List[ExtractedIntent]:
    print("\n================================================================")
    print("STAGE 2.1 — extract (per-doc intent + attributes)")
    print("================================================================")
    docs = _iter_curated(cfg.input_path)
    if cfg.stage_limit:
        docs = docs[: cfg.stage_limit]
    print(f"[stage_2_1] loaded {len(docs)} CuratedDoc(s) from {cfg.input_path}", flush=True)

    if not docs:
        print("[stage_2_1] nothing to do", flush=True)
        write_jsonl(cfg.out_2_1, [])
        return []

    results = extract_batch_vllm_offline(llm, cfg.model_id, docs)
    print(f"[stage_2_1] extracted {len(results)}/{len(docs)}", flush=True)
    write_jsonl(cfg.out_2_1, results)
    print(f"[stage_2_1] saved -> {cfg.out_2_1}", flush=True)
    return results


def _load_extracted(cfg: StageConfig) -> List[ExtractedIntent]:
    print(f"[stage_2_1] (skipped) loading existing output {cfg.out_2_1}", flush=True)
    return load_stage1(cfg.out_2_1)


# ---------------------------------------------------------------------------
# Stage 2.2 — canonicalize
# ---------------------------------------------------------------------------

def run_stage_2_2_canonicalize(
    cfg: StageConfig, llm, extracted: List[ExtractedIntent]
) -> List[IntentCluster]:
    print("\n================================================================")
    print("STAGE 2.2 — canonicalize (embed + cluster + refine + canonical name)")
    print("================================================================")

    unique, intent_to_docs = group_by_raw_intent(extracted)
    print(f"[stage_2_2] {len(unique)} unique raw intents", flush=True)

    general_intents = [i for i in unique if i == "general_wear"]
    cluster_list = [i for i in unique if i != "general_wear"]

    if not cluster_list:
        print("[stage_2_2] no non-general intents to cluster", flush=True)
        write_jsonl(cfg.out_2_2, [])
        return []

    # 1. Embed the raw intents on GPU (BGE-M3)
    embeddings = embed_intents(
        cfg.embed_model, cluster_list, device=cfg.embed_device
    )

    # 2. Primary clustering (sklearn, CPU — small N)
    labels = cluster_intents(embeddings, distance_threshold=cfg.cluster_threshold)
    label_to_members: dict[int, list[str]] = defaultdict(list)
    for intent, lab in zip(cluster_list, labels):
        label_to_members[int(lab)].append(intent)
    primary_groups = [label_to_members[lab] for lab in sorted(label_to_members.keys())]
    print(f"[stage_2_2] {len(primary_groups)} primary clusters", flush=True)

    # 3. Wrap vLLM as a VLLMOfflineClient for the library functions
    client = VLLMOfflineClient(llm, model_name=cfg.model_id)
    llm_model = client._llm_config.model  # noqa: SLF001

    # 4. LLM refine — split heterogeneous clusters
    if cfg.skip_refine:
        final_groups = primary_groups
    else:
        refined_groups: list[list[str]] = []
        for g in primary_groups:
            subs = refine_cluster(
                client, llm_model, g, min_size_to_refine=cfg.refine_min_size
            )
            if len(subs) > 1:
                print(f"  [refine] split {g} -> {subs}", flush=True)
            refined_groups.extend(subs)
        final_groups = refined_groups
        print(
            f"[stage_2_2] refine: {len(primary_groups)} -> {len(final_groups)} clusters",
            flush=True,
        )

    # 5. LLM canonical naming
    results: list[IntentCluster] = []
    for idx, members in enumerate(final_groups):
        canonical = canonicalize(client, llm_model, members)
        source_docs: list[str] = []
        for m in members:
            source_docs.extend(intent_to_docs[m])
        cluster = IntentCluster(
            cluster_id=f"cluster_{idx:03d}",
            canonical_name=canonical,
            raw_intents=members,
            source_curated_ids=sorted(set(source_docs)),
            member_count=len(source_docs),
        )
        results.append(cluster)
        print(
            f"[stage_2_2] {cluster.cluster_id}: {canonical} <= {members}",
            flush=True,
        )

    # 6. Append the general_wear cluster as-is (no canonical naming needed)
    if general_intents:
        gw_docs: list[str] = []
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

    # 7. LLM cross-cluster merge
    if not cfg.skip_cross_merge and len(results) > 1:
        before = len(results)
        print(f"[stage_2_2] cross-merge reviewing {before} clusters ...", flush=True)
        results = cross_cluster_merge(client, llm_model, results)
        print(f"[stage_2_2] cross-merge {before} -> {len(results)}", flush=True)

    write_jsonl(cfg.out_2_2, results)
    print(f"[stage_2_2] saved -> {cfg.out_2_2}", flush=True)
    return results


def _load_clusters(cfg: StageConfig) -> List[IntentCluster]:
    print(f"[stage_2_2] (skipped) loading existing output {cfg.out_2_2}", flush=True)
    return s23_load_jsonl(cfg.out_2_2, IntentCluster)


# ---------------------------------------------------------------------------
# Stage 2.3 — aggregate (pure Python, no LLM)
# ---------------------------------------------------------------------------

def run_stage_2_3_aggregate(
    cfg: StageConfig,
    extracted: List[ExtractedIntent],
    clusters: List[IntentCluster],
) -> List[AnalyzedIntent]:
    print("\n================================================================")
    print("STAGE 2.3 — aggregate (weighted attribute profile per intent)")
    print("================================================================")

    doc_id_to_extracted = {e.source_curated_id: e for e in extracted}
    merged = merge_clusters_by_canonical(clusters)
    if len(merged) != len(clusters):
        print(
            f"[stage_2_3] {len(clusters)} clusters -> {len(merged)} after canonical-name merge",
            flush=True,
        )

    analyzed: list[AnalyzedIntent] = []
    for cluster in merged:
        if cfg.skip_general and cluster.canonical_name == "일반":
            continue
        item = aggregate_cluster(
            cluster, doc_id_to_extracted, top_k=cfg.aggregate_top_k
        )
        analyzed.append(item)
        print(
            f"[stage_2_3] {cluster.cluster_id} '{item.intent_keyword}': "
            f"evidence={item.data_lineage.total_evidence_count} "
            f"attrs={len(item.mapped_attributes)}",
            flush=True,
        )

    with cfg.out_2_3.open("w", encoding="utf-8") as fh:
        for item in analyzed:
            fh.write(item.model_dump_json() + "\n")
    print(f"[stage_2_3] saved {len(analyzed)} analyzed intents -> {cfg.out_2_3}", flush=True)
    return analyzed


def _load_analyzed(cfg: StageConfig) -> List[AnalyzedIntent]:
    print(f"[stage_2_3] (skipped) loading existing output {cfg.out_2_3}", flush=True)
    return s23_load_jsonl(cfg.out_2_3, AnalyzedIntent)


# ---------------------------------------------------------------------------
# Stage 2.4 — expand
# ---------------------------------------------------------------------------

def run_stage_2_4_expand(
    cfg: StageConfig, llm, analyzed: List[AnalyzedIntent]
) -> List[ExpandedIntent]:
    print("\n================================================================")
    print("STAGE 2.4 — expand (canonical intent -> N natural_queries)")
    print("================================================================")

    if not analyzed:
        print("[stage_2_4] nothing to expand", flush=True)
        write_jsonl(cfg.out_2_4, [])
        return []

    results = expand_batch_vllm_offline(
        llm, cfg.model_id, analyzed, n_queries=cfg.n_queries
    )
    print(f"[stage_2_4] expanded {len(results)} intents", flush=True)

    with cfg.out_2_4.open("w", encoding="utf-8") as fh:
        for r in results:
            fh.write(r.model_dump_json() + "\n")
    print(f"[stage_2_4] saved -> {cfg.out_2_4}", flush=True)
    return results


# ---------------------------------------------------------------------------
# Orchestrator
# ---------------------------------------------------------------------------

_STAGE_ORDER = ("extract", "canonicalize", "aggregate", "expand")


def _should_run(stage: str, cfg: StageConfig) -> bool:
    flag = getattr(cfg, f"skip_{stage}")
    if flag:
        return False
    if cfg.stop_after:
        idx_stop = _STAGE_ORDER.index(cfg.stop_after)
        idx_this = _STAGE_ORDER.index(stage)
        if idx_this > idx_stop:
            return False
    return True


def _needs_vllm(cfg: StageConfig) -> bool:
    """Avoid paying the vLLM load cost if ALL LLM stages are skipped."""
    return any(
        _should_run(stage, cfg) for stage in ("extract", "canonicalize", "expand")
    )


def run_pipeline(cfg: StageConfig) -> dict[str, int]:
    load_env()
    prepare_paths(cfg)
    print(
        f"[pipeline] input  : {cfg.input_path}\n"
        f"[pipeline] output : {cfg.output_root}\n"
        f"[pipeline] model  : {cfg.model_id}\n"
        f"[pipeline] skips  : "
        f"extract={cfg.skip_extract} canon={cfg.skip_canonicalize} "
        f"agg={cfg.skip_aggregate} expand={cfg.skip_expand}\n"
        f"[pipeline] stop_after: {cfg.stop_after}",
        flush=True,
    )

    llm = _load_vllm(cfg) if _needs_vllm(cfg) else None

    counts: dict[str, int] = {}

    # Stage 2.1
    if _should_run("extract", cfg):
        extracted = run_stage_2_1_extract(cfg, llm)
    else:
        extracted = _load_extracted(cfg) if cfg.out_2_1.exists() else []
    counts["extracted"] = len(extracted)
    if cfg.stop_after == "extract":
        _print_summary(counts)
        return counts

    # Stage 2.2
    if _should_run("canonicalize", cfg):
        clusters = run_stage_2_2_canonicalize(cfg, llm, extracted)
    else:
        clusters = _load_clusters(cfg) if cfg.out_2_2.exists() else []
    counts["clusters"] = len(clusters)
    if cfg.stop_after == "canonicalize":
        _print_summary(counts)
        return counts

    # Stage 2.3
    if _should_run("aggregate", cfg):
        analyzed = run_stage_2_3_aggregate(cfg, extracted, clusters)
    else:
        analyzed = _load_analyzed(cfg) if cfg.out_2_3.exists() else []
    counts["analyzed"] = len(analyzed)
    if cfg.stop_after == "aggregate":
        _print_summary(counts)
        return counts

    # Stage 2.4
    if _should_run("expand", cfg):
        expanded = run_stage_2_4_expand(cfg, llm, analyzed)
    else:
        expanded = []
    counts["expanded"] = len(expanded)
    counts["expanded_natural_queries"] = sum(
        len(e.natural_queries) for e in expanded
    )

    _print_summary(counts)
    return counts


def _print_summary(counts: dict[str, int]) -> None:
    print("\n================================================================")
    print("[pipeline] SUMMARY")
    print("================================================================")
    for k, v in counts.items():
        print(f"  {k:>30}: {v}")
    print(flush=True)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _build_argparser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="Unified Stage 2 pipeline (extract → canonicalize → aggregate → expand)",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    root = data_root()
    p.add_argument(
        "--input",
        default=os.environ.get("STAGE_INPUT") or str(root / "stage_1_2"),
        help="Stage 1.2 curated dir OR single .jsonl",
    )
    p.add_argument(
        "--output-root",
        default=os.environ.get("STAGE_DATA_ROOT") or str(root),
        help="Where stage_2_1/ .. stage_2_4/ land",
    )
    p.add_argument(
        "--model",
        default=os.environ.get(
            "VLLM_OFFLINE_MODEL", "nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B-BF16"
        ),
    )
    p.add_argument("--dtype", default=os.environ.get("VLLM_DTYPE", "auto"))
    p.add_argument(
        "--gpu-mem-util",
        type=float,
        default=float(os.environ["VLLM_GPU_MEM_UTIL"])
        if os.environ.get("VLLM_GPU_MEM_UTIL")
        else None,
    )
    p.add_argument("--embed-model", default=os.environ.get("EMBED_MODEL", "BAAI/bge-m3"))
    p.add_argument("--embed-device", default=os.environ.get("EMBED_DEVICE", "auto"))
    p.add_argument(
        "--cluster-threshold",
        type=float,
        default=float(os.environ.get("CLUSTER_THRESHOLD", "0.35")),
    )
    p.add_argument(
        "--refine-min-size",
        type=int,
        default=int(os.environ.get("REFINE_MIN_SIZE", "3")),
    )
    p.add_argument("--skip-refine", action="store_true")
    p.add_argument("--skip-cross-merge", action="store_true")
    p.add_argument("--skip-general", action="store_true")
    p.add_argument(
        "--aggregate-top-k",
        type=int,
        default=int(os.environ.get("AGGREGATE_TOP_K", "3")),
    )
    p.add_argument(
        "--n-queries",
        type=int,
        default=int(os.environ.get("STAGE_N_QUERIES", "5")),
    )
    p.add_argument(
        "--stage-limit",
        type=int,
        default=int(os.environ.get("STAGE_LIMIT", "0")),
        help="Cap # of curated docs fed into Stage 2.1 (0 = all)",
    )
    p.add_argument("--skip-extract", action="store_true")
    p.add_argument("--skip-canonicalize", action="store_true")
    p.add_argument("--skip-aggregate", action="store_true")
    p.add_argument("--skip-expand", action="store_true")
    p.add_argument(
        "--stop-after",
        choices=_STAGE_ORDER,
        default=None,
        help="Stop after this stage completes",
    )
    return p


def main(argv: list[str] | None = None) -> int:
    args = _build_argparser().parse_args(argv)
    cfg = StageConfig(
        input_path=Path(args.input),
        output_root=Path(args.output_root),
        model_id=args.model,
        dtype=args.dtype,
        gpu_mem_util=args.gpu_mem_util,
        stage_limit=args.stage_limit,
        embed_model=args.embed_model,
        embed_device=args.embed_device,
        cluster_threshold=args.cluster_threshold,
        refine_min_size=args.refine_min_size,
        skip_refine=args.skip_refine,
        skip_cross_merge=args.skip_cross_merge,
        aggregate_top_k=args.aggregate_top_k,
        skip_general=args.skip_general,
        n_queries=args.n_queries,
        skip_extract=args.skip_extract,
        skip_canonicalize=args.skip_canonicalize,
        skip_aggregate=args.skip_aggregate,
        skip_expand=args.skip_expand,
        stop_after=args.stop_after,
    )
    run_pipeline(cfg)
    return 0


if __name__ == "__main__":
    sys.exit(main())
