"""Run Stage 2.2 canonicalize with in-process vLLM offline + BGE-M3 GPU embed.

This is the GPU-node equivalent of
`python -m pipelines.stage_2_2_canonicalize --refine --cross-merge`,
using a locally-loaded `vllm.LLM` object instead of an OpenAI-compatible
endpoint.

Typical use:

    cd ~/stage2_work
    python scripts/run_stage_2_2_vllm.py

Env knobs:
    STAGE_INPUT              default $STAGE_DATA_ROOT/stage_2_1/stage_2_1_extracted.jsonl
    STAGE_OUTPUT             default $STAGE_DATA_ROOT/stage_2_2/stage_2_2_clusters.jsonl
    EMBED_MODEL              default BAAI/bge-m3
    EMBED_DEVICE             default auto (cuda|cpu|auto)
    CLUSTER_THRESHOLD        default 0.35
    REFINE_MIN_SIZE          default 3
    SKIP_REFINE=1            disable LLM refine
    SKIP_CROSS_MERGE=1       disable cross-cluster merge
    VLLM_OFFLINE_MODEL       default nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B-BF16
    VLLM_DTYPE               default "auto"
    VLLM_GPU_MEM_UTIL        0.0-1.0 (default let vLLM pick)
"""
from __future__ import annotations

import os
import sys
from collections import defaultdict
from pathlib import Path

# Make `pipelines.*` importable when run as `python scripts/run_stage_2_2_vllm.py`
HERE = Path(__file__).resolve().parent
PROJECT_ROOT = HERE.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from pipelines.config import data_root  # noqa: E402
from pipelines.llm_client import load_env  # noqa: E402
from pipelines.schemas import IntentCluster  # noqa: E402
from pipelines.stage_2_2_canonicalize import (  # noqa: E402
    canonicalize,
    cluster_intents,
    cross_cluster_merge,
    embed_intents,
    group_by_raw_intent,
    load_stage1,
    refine_cluster,
)
from pipelines.vllm_adapter import VLLMOfflineClient  # noqa: E402


def _env_flag(name: str) -> bool:
    return os.environ.get(name, "0") not in ("0", "false", "False", "")


def main() -> int:
    load_env()
    root = data_root()

    input_path = Path(
        os.environ.get("STAGE_INPUT")
        or (root / "stage_2_1" / "stage_2_1_extracted.jsonl")
    )
    output_path = Path(
        os.environ.get("STAGE_OUTPUT")
        or (root / "stage_2_2" / "stage_2_2_clusters.jsonl")
    )

    embed_model = os.environ.get("EMBED_MODEL", "BAAI/bge-m3")
    embed_device = os.environ.get("EMBED_DEVICE", "auto")
    threshold = float(os.environ.get("CLUSTER_THRESHOLD", "0.35"))
    refine_min = int(os.environ.get("REFINE_MIN_SIZE", "3"))
    do_refine = not _env_flag("SKIP_REFINE")
    do_cross_merge = not _env_flag("SKIP_CROSS_MERGE")

    model_id = os.environ.get(
        "VLLM_OFFLINE_MODEL",
        "nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B-BF16",
    )
    dtype = os.environ.get("VLLM_DTYPE", "auto")
    gpu_util = os.environ.get("VLLM_GPU_MEM_UTIL")

    print(f"[stage_2_2] input  : {input_path}", flush=True)
    print(f"[stage_2_2] output : {output_path}", flush=True)
    print(f"[stage_2_2] embed  : {embed_model} device={embed_device}", flush=True)
    print(f"[stage_2_2] llm    : vllm-offline {model_id}", flush=True)

    extracted = load_stage1(input_path)
    print(f"[load] {len(extracted)} extracted intents", flush=True)

    unique, intent_to_docs = group_by_raw_intent(extracted)
    print(f"[group] {len(unique)} unique intents", flush=True)

    general_intents = [i for i in unique if i == "general_wear"]
    cluster_list = [i for i in unique if i != "general_wear"]

    if not cluster_list:
        print("[warn] no non-general intents to cluster", flush=True)
        return 0

    # 1) Embed on GPU
    embeddings = embed_intents(embed_model, cluster_list, device=embed_device)

    # 2) Primary clustering (sklearn, CPU - small N)
    labels = cluster_intents(embeddings, distance_threshold=threshold)
    label_to_members = defaultdict(list)
    for intent, lab in zip(cluster_list, labels):
        label_to_members[int(lab)].append(intent)
    primary_groups = [label_to_members[lab] for lab in sorted(label_to_members.keys())]
    print(f"[cluster] {len(primary_groups)} primary clusters", flush=True)
    for i, g in enumerate(primary_groups):
        print(f"  primary {i}: {g}", flush=True)

    # 3) Load vLLM for the three LLM steps
    from vllm import LLM  # lazy import

    kwargs: dict = {"model": model_id, "trust_remote_code": True, "dtype": dtype}
    if gpu_util:
        kwargs["gpu_memory_utilization"] = float(gpu_util)
    print("[stage_2_2] loading vLLM ...", flush=True)
    llm = LLM(**kwargs)
    client = VLLMOfflineClient(llm, model_name=model_id)
    llm_model = client._llm_config.model
    print("[stage_2_2] vLLM ready", flush=True)

    # 4) (optional) LLM refine - split heterogeneous clusters
    if do_refine:
        refined_groups: list[list[str]] = []
        for g in primary_groups:
            subs = refine_cluster(client, llm_model, g, min_size_to_refine=refine_min)
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

    # 5) LLM canonical naming per final group
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
        print(f"[canonical] {cluster.cluster_id}: {canonical}  <= {members}", flush=True)

    # 6) Append general_wear as its own cluster
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

    # 7) (optional) LLM cross-cluster merge
    if do_cross_merge:
        before = len(results)
        print(f"\n[cross-merge] reviewing {before} clusters ...", flush=True)
        results = cross_cluster_merge(client, llm_model, results)
        print(f"[cross-merge] {before} -> {len(results)} clusters", flush=True)

    # 8) Save
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as fh:
        for c in results:
            fh.write(c.model_dump_json() + "\n")
    print(f"\n[stage_2_2] saved {len(results)} clusters -> {output_path}", flush=True)
    for c in results:
        print(
            f"  {c.cluster_id}  '{c.canonical_name}'  "
            f"members={c.raw_intents}  evidence={c.member_count}",
            flush=True,
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
