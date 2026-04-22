"""Sweep distance thresholds to find the best cluster count/cohesion tradeoff."""
from __future__ import annotations

import os
import sys
from pathlib import Path

import numpy as np
from sklearn.cluster import AgglomerativeClustering
from sklearn.metrics.pairwise import cosine_similarity

from pipelines.llm_client import load_env
from pipelines.stage_2_2_canonicalize import (
    DEFAULT_EMBED_MODEL,
    embed_intents,
    group_by_raw_intent,
    load_stage1,
)


def main() -> None:
    load_env()
    extracted = load_stage1(Path("data/stage_2_1_extracted.jsonl"))
    unique, _ = group_by_raw_intent(extracted)
    intents = [i for i in unique if i != "general_wear"]

    model = os.environ.get("EMBED_MODEL", DEFAULT_EMBED_MODEL)
    emb = embed_intents(model, intents)
    sim = cosine_similarity(emb)
    dist = 1.0 - sim
    np.fill_diagonal(dist, 0.0)
    dist = np.clip(dist, 0.0, None)

    for threshold in [0.15, 0.20, 0.25, 0.30, 0.35, 0.40, 0.45]:
        mdl = AgglomerativeClustering(
            n_clusters=None,
            distance_threshold=threshold,
            metric="precomputed",
            linkage="average",
        )
        labels = mdl.fit_predict(dist)
        groups: dict[int, list[str]] = {}
        for intent, lab in zip(intents, labels):
            groups.setdefault(int(lab), []).append(intent)

        print(f"\n=== threshold={threshold} -> {len(groups)} clusters ===")
        for lab in sorted(groups):
            members = groups[lab]
            if len(members) == 1:
                continue
            print(f"  {lab}: {members}")
        singletons = [m[0] for m in groups.values() if len(m) == 1]
        print(f"  singletons ({len(singletons)}): {singletons}")


if __name__ == "__main__":
    sys.exit(main())
