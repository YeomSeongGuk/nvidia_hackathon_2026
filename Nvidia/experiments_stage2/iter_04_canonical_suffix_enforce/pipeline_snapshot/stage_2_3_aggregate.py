"""Stage 2.3 - aggregate attributes per canonical intent cluster.

For each IntentCluster from Stage 2.2, collect the extracted attribute
values across all member documents, rank them by quality-weighted
frequency, and emit the final `AnalyzedIntent` record.

Input:
  $STAGE_DATA_ROOT/stage_2_1/stage_2_1_extracted.jsonl   (ExtractedIntent per doc)
  $STAGE_DATA_ROOT/stage_2_2/stage_2_2_clusters.jsonl    (IntentCluster)

Output:
  $STAGE_DATA_ROOT/stage_2_3/analyzed_intents.jsonl      (final analyzed data)

Usage:
  python -m pipelines.stage_2_3_aggregate
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Tuple

from pipelines.config import data_root
from pipelines.schemas import (
    AnalyzedIntent,
    DataLineage,
    ExtractedIntent,
    IntentCluster,
    MappedAttribute,
)

ATTR_KEYS = ("material", "fit", "color", "style", "season")


def load_jsonl(path: Path, cls):
    out = []
    with path.open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            out.append(cls.model_validate_json(line))
    return out


def normalize_value(v: str) -> str:
    return v.strip().lower()


def aggregate_cluster(
    cluster: IntentCluster,
    doc_id_to_extracted: Dict[str, ExtractedIntent],
    top_k: int = 3,
) -> AnalyzedIntent:
    # attribute_key -> value -> (count, quality_sum)
    buckets: Dict[str, Dict[str, List[float]]] = defaultdict(lambda: defaultdict(list))
    n_evidence = 0
    source_doc_ids: List[str] = []

    for doc_id in cluster.source_curated_ids:
        extracted = doc_id_to_extracted.get(doc_id)
        if extracted is None:
            continue
        n_evidence += 1
        source_doc_ids.append(doc_id)
        attrs = extracted.attributes.model_dump()
        quality = float(extracted.source_quality_score)
        for key in ATTR_KEYS:
            val = attrs.get(key)
            if not val:
                continue
            if not isinstance(val, str):
                continue
            norm = normalize_value(val)
            if not norm or norm in ("null", "none", "n/a", "...", "…"):
                continue
            buckets[key][norm].append(quality)

    mapped: List[MappedAttribute] = []
    total = max(n_evidence, 1)
    for key in ATTR_KEYS:
        value_scores: List[Tuple[str, float, int]] = []
        for value, quals in buckets[key].items():
            freq = len(quals)
            weighted = sum(quals)  # quality-weighted frequency
            value_scores.append((value, weighted, freq))
        # rank by weighted frequency desc; cap to top_k
        value_scores.sort(key=lambda x: (-x[1], -x[2], x[0]))
        for value, weighted, freq in value_scores[:top_k]:
            weight = round(weighted / total, 3)
            mapped.append(
                MappedAttribute(
                    attribute_key=key, attribute_value=value, weight=weight
                )
            )

    now = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    return AnalyzedIntent(
        intent_keyword=cluster.canonical_name,
        mapped_attributes=mapped,
        data_lineage=DataLineage(
            total_evidence_count=n_evidence,
            source_doc_ids=sorted(set(source_doc_ids)),
        ),
        last_updated=now,
    )


def merge_clusters_by_canonical(clusters: List[IntentCluster]) -> List[IntentCluster]:
    """Post-process: merge all clusters that share the same canonical_name.

    This handles the case where the embedding step split surface forms that
    the LLM canonicalizer later maps to the same Korean name (e.g. both
    "사무실룩" (Korean) and "office casual" (English) end up with the same
    canonical "오피스룩").
    """
    grouped: Dict[str, List[IntentCluster]] = defaultdict(list)
    for c in clusters:
        grouped[c.canonical_name].append(c)

    merged: List[IntentCluster] = []
    for i, (canonical, members) in enumerate(grouped.items()):
        if len(members) == 1:
            merged.append(members[0])
            continue
        raw_intents: List[str] = []
        source_doc_ids: List[str] = []
        for m in members:
            raw_intents.extend(m.raw_intents)
            source_doc_ids.extend(m.source_curated_ids)
        merged.append(
            IntentCluster(
                cluster_id=f"merged_{i:03d}",
                canonical_name=canonical,
                raw_intents=sorted(set(raw_intents)),
                source_curated_ids=sorted(set(source_doc_ids)),
                member_count=len(set(source_doc_ids)),
            )
        )
    return merged


def main(argv: List[str] | None = None) -> int:
    root = data_root()
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--stage1",
        default=str(root / "stage_2_1" / "stage_2_1_extracted.jsonl"),
        help="Stage 2.1 extracted intents (per-doc).",
    )
    parser.add_argument(
        "--stage2",
        default=str(root / "stage_2_2" / "stage_2_2_clusters.jsonl"),
        help="Stage 2.2 canonical clusters.",
    )
    parser.add_argument(
        "--output",
        default=str(root / "stage_2_3" / "analyzed_intents.jsonl"),
    )
    parser.add_argument("--top-k", type=int, default=3)
    parser.add_argument(
        "--skip-general",
        action="store_true",
        help="drop the 'general_wear' / '일반' cluster from the final output",
    )
    args = parser.parse_args(argv)

    extracted = load_jsonl(Path(args.stage1), ExtractedIntent)
    clusters = load_jsonl(Path(args.stage2), IntentCluster)
    doc_id_to_extracted = {e.source_curated_id: e for e in extracted}

    print(
        f"[load] {len(extracted)} extracted, {len(clusters)} clusters",
        flush=True,
    )

    # Merge any clusters that landed on an identical canonical_name (e.g. two
    # "office"-like clusters both labelled "오피스룩" by the canonicalizer).
    merged = merge_clusters_by_canonical(clusters)
    if len(merged) != len(clusters):
        print(
            f"[merge] {len(clusters)} clusters -> {len(merged)} after canonical-name merge",
            flush=True,
        )

    analyzed: List[AnalyzedIntent] = []
    for cluster in merged:
        if args.skip_general and cluster.canonical_name == "일반":
            continue
        item = aggregate_cluster(cluster, doc_id_to_extracted, top_k=args.top_k)
        analyzed.append(item)
        print(
            f"[aggregate] {cluster.cluster_id} '{item.intent_keyword}': "
            f"evidence={item.data_lineage.total_evidence_count} "
            f"attrs={len(item.mapped_attributes)}",
            flush=True,
        )

    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as fh:
        for item in analyzed:
            fh.write(item.model_dump_json() + "\n")

    print(f"\n[done] wrote {len(analyzed)} analyzed intents -> {out_path}", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
