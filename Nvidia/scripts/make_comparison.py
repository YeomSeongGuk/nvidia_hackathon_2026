"""Produce `comparison.md` + update `summary.md` from two `metrics.json`s.

`metrics.json` shape (written by scripts/iter_run.py):

    {
      "iter_id": "iter_03_attr_diversity_prompt",
      "parent_iter": "iter_02_title_max_tokens_short",
      "output_hashes": {...},
      "stage_1_0":   {"fashion_rate": {"glm":..., "deepseek":..., "qwen3":..., "mean":..., "range":...}, ...},
      "stage_1_1":   {...},
      "stage_1_1_5": {...},
      "stage_1_2":   {...},
      "quant": {...},
      "e2e":   {...},
      "promote": false,
      ...
    }

This script flattens both metrics files into a single sorted diff table
and writes `comparison.md` into the *this* iteration's folder.

It also appends/updates a row in `experiments/summary.md`
(rolling leaderboard). Idempotent — re-running overwrites the row.

Usage:
  python scripts/make_comparison.py \\
      --this   experiments/iter_03_.../metrics.json \\
      --parent experiments/iter_02_.../metrics.json \\
      --out    experiments/iter_03_.../comparison.md \\
      --summary experiments/summary.md
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


# Metrics where a lower number is better. Everything else: higher = better.
_LOWER_IS_BETTER = {
    "title_reasoning_leak_rate",
    "title_newline_rate",
    "title_len_p90",
    "title_len_p99",
    "title_len_max",
    "style_top1_share",
    "color_top2_share",
    "color_white_black_share",
    "size_suspicious_rate",
    "pii_rate",
    "dedup_miss_count",
    "dedup_miss_rate",
    "largest_miss_cluster_size",
    "noise_level_hist.high_rate",
}


# ---------------------------------------------------------------------------
# Flattening helpers
# ---------------------------------------------------------------------------

def _flatten(
    prefix: str, obj: Any, out: Dict[str, Any],
) -> None:
    """Recursively flatten a nested metric dict.

    For ensemble dicts of shape {glm,deepseek,qwen3,mean,range} we flatten
    ONLY the `mean` field as `<prefix>.mean` for the comparison table,
    because the range/individual judges can still be found in metrics.json.
    """
    if isinstance(obj, dict):
        ensemble_keys = {"glm", "deepseek", "qwen3", "mean", "range"}
        if "mean" in obj and ensemble_keys.issuperset(set(obj.keys()) - {"agreement_approx"}):
            out[prefix] = obj.get("mean")
            return
        for k, v in obj.items():
            key = f"{prefix}.{k}" if prefix else k
            _flatten(key, v, out)
    elif isinstance(obj, list):
        # Skip large lists.
        out[prefix] = f"<list len={len(obj)}>"
    else:
        out[prefix] = obj


def _sig_delta(a: Optional[float], b: Optional[float]) -> Optional[float]:
    if a is None or b is None:
        return None
    try:
        return round(float(b) - float(a), 3)
    except (TypeError, ValueError):
        return None


def _direction_mark(metric: str, delta: Optional[float]) -> str:
    if delta is None or delta == 0:
        return "·"
    is_lower_better = any(tag in metric for tag in _LOWER_IS_BETTER)
    if is_lower_better:
        return "↓ good" if delta < 0 else "↑ bad"
    return "↑ good" if delta > 0 else "↓ bad"


# ---------------------------------------------------------------------------
# Report + summary
# ---------------------------------------------------------------------------

def build_comparison_md(
    this: Dict[str, Any], parent: Optional[Dict[str, Any]]
) -> str:
    lines: List[str] = []
    lines.append(f"# Comparison: {this.get('iter_id')} vs {this.get('parent_iter') or '(none)'}")
    lines.append("")
    lines.append(f"- this   iter: `{this.get('iter_id')}`")
    lines.append(f"- parent iter: `{this.get('parent_iter')}`")
    lines.append(f"- this timestamp : {this.get('timestamp')}")
    lines.append(f"- promote flag   : {this.get('promote')}  high_variance: {this.get('high_variance')}")
    lines.append("")

    if parent is None:
        lines.append("(no parent metrics.json provided — showing current values only)")
        lines.append("")

    this_flat: Dict[str, Any] = {}
    parent_flat: Dict[str, Any] = {}
    for group in ("stage_1_0", "stage_1_1", "stage_1_1_5", "stage_1_2", "quant", "e2e"):
        _flatten(group, this.get(group) or {}, this_flat)
        if parent is not None:
            _flatten(group, (parent or {}).get(group) or {}, parent_flat)

    keys = sorted(set(this_flat.keys()) | set(parent_flat.keys()))

    lines.append("## Metric diff")
    lines.append("")
    lines.append("| metric | parent | this | Δ | direction |")
    lines.append("|---|---|---|---|---|")
    for k in keys:
        pv = parent_flat.get(k)
        tv = this_flat.get(k)
        if isinstance(pv, float):
            pv_str = f"{pv:g}"
        else:
            pv_str = "—" if pv is None else str(pv)
        if isinstance(tv, float):
            tv_str = f"{tv:g}"
        else:
            tv_str = "—" if tv is None else str(tv)

        delta = _sig_delta(pv, tv) if isinstance(pv, (int, float)) and isinstance(tv, (int, float)) else None
        delta_str = "—" if delta is None else f"{delta:+g}"
        lines.append(f"| `{k}` | {pv_str} | {tv_str} | {delta_str} | {_direction_mark(k, delta)} |")

    lines.append("")
    lines.append("## Output hashes")
    lines.append("")
    lines.append("| file | sha256 |")
    lines.append("|---|---|")
    for fname, h in (this.get("output_hashes") or {}).items():
        lines.append(f"| `{fname}` | `{h}` |")
    return "\n".join(lines)


def update_summary_md(
    summary_path: Path, this: Dict[str, Any]
) -> None:
    """Append/replace a row for this iter in experiments/summary.md.

    Idempotent: if a row with `iter_id` already exists, replace it.
    """
    summary_path.parent.mkdir(parents=True, exist_ok=True)

    iter_id = this.get("iter_id") or "?"
    # Pull the headline numbers. `_flatten` above, simpler inline here.
    def _ensemble_mean(path: List[str]) -> Optional[float]:
        node: Any = this
        for p in path:
            if not isinstance(node, dict):
                return None
            node = node.get(p)
            if node is None:
                return None
        if isinstance(node, dict) and "mean" in node:
            return node.get("mean")
        if isinstance(node, (int, float)):
            return node
        return None

    title_leak = _ensemble_mean(["stage_1_1", "title_reasoning_leak_rate"])
    fashion_1_1 = _ensemble_mean(["stage_1_1", "fashion_rate"])
    persona = _ensemble_mean(["stage_1_1", "avg_persona_reflection"])
    attr_grnd = _ensemble_mean(["stage_1_1", "attr_grounded_rate"])
    rating_3 = ((this.get("quant") or {}).get("stage_1_1") or {}).get("rating_3_share")
    dedup_red = ((this.get("quant") or {}).get("stage_1_1_5") or {}).get("dedup_reduction_rate")
    e2e_ret = ((this.get("e2e") or {}).get("e2e_retention"))
    promote = this.get("promote")

    row = (
        f"| `{iter_id}` | {title_leak} | {fashion_1_1} | {persona} | "
        f"{attr_grnd} | {rating_3} | {dedup_red} | {e2e_ret} | {promote} |"
    )

    header_lines = [
        "# Stage 1 iteration leaderboard",
        "",
        "| iter_id | 1.1 leak ↓ | 1.1 fashion ↑ | 1.1 persona ↑ | "
        "1.1 attr_grnd ↑ | rating_3 > 0 | dedup_reduction ↑ | e2e_ret ↑ | promote |",
        "|---|---|---|---|---|---|---|---|---|",
    ]
    existing: List[str] = []
    if summary_path.exists():
        existing = summary_path.read_text(encoding="utf-8").splitlines()

    # Strip the header lines + any previous row for this iter_id.
    body_rows = [
        line for line in existing
        if line.startswith("|")
        and not line.startswith("| iter_id ")
        and not line.startswith("|---")
        and f"| `{iter_id}` " not in line
    ]
    body_rows.append(row)
    out = header_lines + body_rows + [""]
    summary_path.write_text("\n".join(out) + "\n", encoding="utf-8")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main(argv: List[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--this", required=True, help="this iter's metrics.json")
    parser.add_argument("--parent", default="", help="parent iter's metrics.json (optional for iter_00)")
    parser.add_argument("--out", required=True, help="output comparison.md path")
    parser.add_argument(
        "--summary", default="experiments/summary.md",
        help="rolling leaderboard to upsert.",
    )
    args = parser.parse_args(argv)

    this = json.loads(Path(args.this).read_text(encoding="utf-8"))
    parent = (
        json.loads(Path(args.parent).read_text(encoding="utf-8"))
        if args.parent
        else None
    )

    md = build_comparison_md(this, parent)
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_text(md, encoding="utf-8")
    print(f"[make_comparison] wrote {args.out}", file=sys.stderr)

    update_summary_md(Path(args.summary), this)
    print(f"[make_comparison] updated leaderboard: {args.summary}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
