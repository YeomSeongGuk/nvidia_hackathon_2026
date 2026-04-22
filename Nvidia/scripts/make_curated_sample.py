"""Build a curated_sample.jsonl from clothing_reviews.jsonl + a few English seeds.

Input:  data/clothing_reviews.jsonl   (rating, text, id)
Output: data/curated_sample.jsonl     (curated_id, clean_text, pipeline_metadata)

Quality score is a simple proxy:
  - rating 5 -> 0.95
  - rating 4 -> 0.85
  - rating 3 -> 0.70
  - rating 2 -> 0.60
  - rating 1 -> 0.50
"""
from __future__ import annotations

import argparse
import json
import random
from pathlib import Path

RATING_TO_QUALITY = {5: 0.95, 4: 0.85, 3: 0.70, 2: 0.60, 1: 0.50}

# A few English seeds so we can later verify cross-lingual intent merging in Stage 2.
ENGLISH_SEEDS = [
    {
        "curated_id": "curated_blog_en_001",
        "clean_text": "Wedding guest look recommendation. Neat fit, premium tweed material, generous length covering the belly well.",
        "pipeline_metadata": {"quality_score": 0.92, "is_delta_update": True, "source_type": "blog"},
    },
    {
        "curated_id": "curated_blog_en_002",
        "clean_text": "Perfect office casual for a summer day. Linen blend with a relaxed fit, in a light beige color.",
        "pipeline_metadata": {"quality_score": 0.88, "is_delta_update": True, "source_type": "blog"},
    },
    {
        "curated_id": "curated_rv_en_003",
        "clean_text": "Bought this for a wedding. The tweed fabric looks premium and the fit is tailored. Length hits just below the knee.",
        "pipeline_metadata": {"quality_score": 0.90, "is_delta_update": True, "source_type": "review"},
    },
    {
        "curated_id": "curated_rv_en_004",
        "clean_text": "Great everyday casual tee. Soft cotton, loose fit, and the black color has not faded after many washes.",
        "pipeline_metadata": {"quality_score": 0.80, "is_delta_update": True, "source_type": "review"},
    },
    {
        "curated_id": "curated_blog_en_005",
        "clean_text": "Effortless date night outfit. Silky slip dress in deep navy, slim fit, midi length, perfect for dinner.",
        "pipeline_metadata": {"quality_score": 0.93, "is_delta_update": True, "source_type": "blog"},
    },
]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default="data/clothing_reviews.jsonl")
    parser.add_argument("--output", default="data/curated_sample.jsonl")
    parser.add_argument("--n-korean", type=int, default=45)
    parser.add_argument("--min-length", type=int, default=30)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    rng = random.Random(args.seed)

    in_path = Path(args.input)
    out_path = Path(args.output)
    assert in_path.exists(), f"input not found: {in_path}"
    out_path.parent.mkdir(parents=True, exist_ok=True)

    rows = []
    with in_path.open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            obj = json.loads(line)
            if len(obj.get("text", "")) < args.min_length:
                continue
            rows.append(obj)

    rng.shuffle(rows)
    rows = rows[: args.n_korean]

    with out_path.open("w", encoding="utf-8") as fh:
        rows_out = []
        for row in rows:
            rating = int(row.get("rating", 3))
            rows_out.append(
                {
                    "curated_id": f"curated_{row['id']}",
                    "clean_text": row["text"],
                    "pipeline_metadata": {
                        "quality_score": RATING_TO_QUALITY.get(rating, 0.70),
                        "is_delta_update": True,
                        "source_type": "review",
                        "source_rating": rating,
                    },
                }
            )
        rows_out.extend(ENGLISH_SEEDS)
        rng.shuffle(rows_out)
        for row in rows_out:
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")

    total = args.n_korean + len(ENGLISH_SEEDS)
    print(f"wrote {total} curated docs -> {out_path}")


if __name__ == "__main__":
    main()
