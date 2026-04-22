"""Deterministic (no-LLM) quantitative probe for Stage 1 output.

Reads the four Stage-1 JSONLs under `--output-dir` and emits the §4e
metrics from `experiments/PLAN.md`:

  - rating_3_share          (Stage 1.1)
  - title_len_p90           (Stage 1.1)
  - title_newline_rate      (Stage 1.1)  -- catches the reasoning-leak
  - title_arrow_rate        (Stage 1.1)  -- catches '→' / '다시 조정' / '글자'
  - style_top1_share        (Stage 1.1)
  - color_top2_share        (Stage 1.1)  -- 화이트 + 블랙
  - size_suspicious_rate    (Stage 1.1)  -- sizes that are clearly not apparel
  - e2e_retention           (1.2 count / 1.0 count)
  - per-stage counts + pipeline volume

Usage:
  python scripts/quant_stage1_report.py \\
      --output-dir experiments/iter_00_baseline/output \\
      --json-out    experiments/iter_00_baseline/quant_metrics.json \\
      --md-out      experiments/iter_00_baseline/quant_report.md

If the output directory is missing any of the four JSONLs the probe
still emits whatever it can and marks the missing stages as `null`.
"""
from __future__ import annotations

import argparse
import json
import re
import statistics as stats
import sys
from collections import Counter
from pathlib import Path
from typing import Any, Dict, List, Optional


STAGE_FILENAMES = {
    "stage_1_0": "stage_1_0_seed.jsonl",
    "stage_1_1": "stage_1_1_synthetic.jsonl",
    "stage_1_1_5": "stage_1_1_5_deduped.jsonl",
    "stage_1_2": "stage_1_2_processed.jsonl",
}

# Apparel size allow-list. Anything outside this is flagged as suspicious
# (cue for H6 `size_plausibility_filter`).
APPAREL_SIZES = {
    "XS", "S", "M", "L", "XL", "XXL", "XXXL", "FREE", "ONE SIZE",
    # Korean numeric sizes for tops / dresses
    "85", "90", "95", "100", "105", "110", "115", "120",
}

# Korean apparel-size regex for "44-77 / 가슴 32" style tags
_APPAREL_NUMERIC = re.compile(r"^(2[0-9]|3[0-9]|4[0-4]|[5-9][0-9]|1[0-2][0-9])$")

# Reasoning-leak markers inside product_title
_TITLE_LEAK_RE = re.compile(r"→|글자|다시 조정|조건 미달|[\r\n]|글자 수")


def _read_jsonl(p: Path) -> List[Dict[str, Any]]:
    if not p.exists():
        return []
    out: List[Dict[str, Any]] = []
    for line in p.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            out.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return out


# ---------------------------------------------------------------------------
# Per-stage metrics
# ---------------------------------------------------------------------------

def _stage_1_0_metrics(records: List[Dict[str, Any]]) -> Dict[str, Any]:
    if not records:
        return {"n": 0}
    ratings = [
        (r.get("metadata") or {}).get("rating")
        or r.get("rating")
        or r.get("source_rating")
        for r in records
    ]
    ratings_int: List[int] = []
    for r in ratings:
        try:
            if r is None:
                continue
            ratings_int.append(int(r))
        except (TypeError, ValueError):
            continue
    rating_hist = Counter(ratings_int)
    return {
        "n": len(records),
        "rating_hist": {int(k): v for k, v in sorted(rating_hist.items())},
        "rating_3_share": (
            round(rating_hist.get(3, 0) / len(records), 3)
            if records else None
        ),
    }


def _is_size_suspicious(size: Optional[str]) -> bool:
    if size is None:
        return True
    s = str(size).strip().upper()
    if s in APPAREL_SIZES:
        return False
    if _APPAREL_NUMERIC.match(s):
        return False
    # e.g. "13개월" (baby), "250" (shoe), "4호" (? non-apparel), "15인치"
    if re.search(r"개월|인치|cm|CM|호\b|\bmm\b", s):
        return True
    # Pure number that didn't match numeric apparel → shoe / loose
    if s.isdigit():
        return True
    return True


def _stage_1_1_metrics(records: List[Dict[str, Any]]) -> Dict[str, Any]:
    if not records:
        return {"n": 0}

    titles = [(r.get("product_title") or "") for r in records]
    texts = [(r.get("raw_text") or "") for r in records]

    title_lens = [len(t) for t in titles]
    text_lens = [len(t) for t in texts]

    title_leak = sum(1 for t in titles if _TITLE_LEAK_RE.search(t))
    title_newline = sum(1 for t in titles if "\n" in t or "\r" in t)

    ratings = [
        (r.get("metadata") or {}).get("rating")
        or r.get("rating")
        or r.get("source_rating")
        for r in records
    ]
    rating_hist: Counter = Counter()
    for x in ratings:
        try:
            if x is not None:
                rating_hist[int(x)] += 1
        except (TypeError, ValueError):
            continue

    colors = []
    styles = []
    sizes = []
    for r in records:
        a = r.get("product_attributes") or {}
        colors.append((a.get("color") or "").strip())
        styles.append((a.get("style") or "").strip())
        sizes.append((a.get("size") or "").strip())

    color_hist = Counter(colors)
    style_hist = Counter(styles)
    size_hist = Counter(sizes)

    style_top1 = style_hist.most_common(1)[0][1] if style_hist else 0
    color_top2 = sum(count for _, count in color_hist.most_common(2)) if color_hist else 0

    white_black = color_hist.get("화이트", 0) + color_hist.get("블랙", 0)

    susp_sizes = sum(1 for s in sizes if _is_size_suspicious(s))

    n = len(records)

    def _pct(v: int) -> float:
        return round(v / n, 3) if n else 0.0

    def _p(values: List[int], q: float) -> int:
        if not values:
            return 0
        srt = sorted(values)
        idx = int(q * (len(srt) - 1))
        return srt[idx]

    return {
        "n": n,
        "title_len_min": min(title_lens) if title_lens else 0,
        "title_len_median": int(stats.median(title_lens)) if title_lens else 0,
        "title_len_p90": _p(title_lens, 0.9),
        "title_len_p99": _p(title_lens, 0.99),
        "title_len_max": max(title_lens) if title_lens else 0,
        "title_reasoning_leak_rate": _pct(title_leak),
        "title_newline_rate": _pct(title_newline),

        "raw_text_len_min": min(text_lens) if text_lens else 0,
        "raw_text_len_median": int(stats.median(text_lens)) if text_lens else 0,
        "raw_text_len_p90": _p(text_lens, 0.9),
        "raw_text_len_max": max(text_lens) if text_lens else 0,

        "rating_hist": {int(k): v for k, v in sorted(rating_hist.items())},
        "rating_3_share": _pct(rating_hist.get(3, 0)),

        "style_unique": len(style_hist),
        "style_top1_value": style_hist.most_common(1)[0][0] if style_hist else None,
        "style_top1_share": _pct(style_top1),

        "color_unique": len(color_hist),
        "color_top2_share": _pct(color_top2),
        "color_white_black_share": _pct(white_black),

        "size_unique": len(size_hist),
        "size_suspicious_rate": _pct(susp_sizes),
    }


def _stage_1_1_5_metrics(
    records_in: List[Dict[str, Any]],
    records_out: List[Dict[str, Any]],
) -> Dict[str, Any]:
    in_n = len(records_in)
    out_n = len(records_out)
    reduction = (in_n - out_n) / in_n if in_n else 0.0
    return {
        "dedup_in_count": in_n,
        "dedup_out_count": out_n,
        "dedup_reduction_rate": round(reduction, 3),
    }


def _stage_1_2_metrics(
    records: List[Dict[str, Any]],
    records_from_1_1_5: List[Dict[str, Any]],
) -> Dict[str, Any]:
    n = len(records)
    prev = len(records_from_1_1_5)
    retention = n / prev if prev else None
    return {
        "n": n,
        "retention_from_stage_1_1_5": round(retention, 3) if retention is not None else None,
    }


# ---------------------------------------------------------------------------
# Markdown report
# ---------------------------------------------------------------------------

def build_md_report(metrics: Dict[str, Any]) -> str:
    lines: List[str] = []
    lines.append("# Stage 1 Quantitative Probe")
    lines.append("")
    lines.append("(no-LLM deterministic metrics; LLM judges are separate)")
    lines.append("")

    # Pipeline volume
    e2e = metrics.get("e2e") or {}
    lines.append("## Pipeline volume")
    lines.append("")
    lines.append("| stage | n | retention vs prev |")
    lines.append("|---|---|---|")
    s10 = metrics.get("stage_1_0", {})
    s11 = metrics.get("stage_1_1", {})
    s115 = metrics.get("stage_1_1_5", {})
    s12 = metrics.get("stage_1_2", {})
    lines.append(f"| 1.0   seed      | {s10.get('n', 0)} | — |")
    lines.append(f"| 1.1   synthetic | {s11.get('n', 0)} | — |")
    lines.append(
        f"| 1.1.5 deduped   | {s115.get('dedup_out_count', 0)} | "
        f"reduction={s115.get('dedup_reduction_rate')} |"
    )
    lines.append(
        f"| 1.2   processed | {s12.get('n', 0)} | "
        f"retention={s12.get('retention_from_stage_1_1_5')} |"
    )
    lines.append(f"| e2e retention (1.2/1.0): **{e2e.get('e2e_retention')}** | | |")
    lines.append("")

    # Stage 1.1 hot spot
    if s11.get("n"):
        lines.append("## Stage 1.1 — synthetic review content")
        lines.append("")
        lines.append("### Title health")
        lines.append(f"- length p50 / p90 / p99 / max: "
                     f"{s11.get('title_len_median')} / "
                     f"{s11.get('title_len_p90')} / "
                     f"{s11.get('title_len_p99')} / "
                     f"{s11.get('title_len_max')}")
        lines.append(f"- reasoning-leak markers (→ / 글자 / newline / 다시 조정): "
                     f"**{s11.get('title_reasoning_leak_rate')}**")
        lines.append(f"- newline-only subset: {s11.get('title_newline_rate')}")
        lines.append("")
        lines.append("### Attribute diversity")
        lines.append(f"- color_unique: {s11.get('color_unique')} | "
                     f"top-2 share: **{s11.get('color_top2_share')}** | "
                     f"화이트+블랙 share: {s11.get('color_white_black_share')}")
        lines.append(f"- style_unique: {s11.get('style_unique')} | "
                     f"top-1 ({s11.get('style_top1_value')!r}): "
                     f"**{s11.get('style_top1_share')}**")
        lines.append(f"- size_unique: {s11.get('size_unique')} | "
                     f"suspicious (non-apparel): "
                     f"**{s11.get('size_suspicious_rate')}**")
        lines.append("")
        lines.append("### Rating distribution")
        lines.append(f"- histogram: `{s11.get('rating_hist')}`")
        lines.append(f"- rating_3_share: **{s11.get('rating_3_share')}**  "
                     f"(promote bar: > 0)")
        lines.append(f"- raw_text length p50 / p90 / max: "
                     f"{s11.get('raw_text_len_median')} / "
                     f"{s11.get('raw_text_len_p90')} / "
                     f"{s11.get('raw_text_len_max')}")
        lines.append("")

    lines.append("## Stage 1.0 — seed")
    lines.append(f"- rating_hist: `{s10.get('rating_hist')}`")
    lines.append(f"- rating_3_share: {s10.get('rating_3_share')}")
    lines.append("")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main(argv: List[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output-dir", required=True,
        help="Dir containing the four Stage-1 JSONLs (stage_1_0_seed.jsonl, ...).",
    )
    parser.add_argument(
        "--json-out", default="",
        help="Write the full metrics JSON here (default: stdout).",
    )
    parser.add_argument(
        "--md-out", default="",
        help="Write a Markdown report here (default: <output-dir>/quant_report.md).",
    )
    args = parser.parse_args(argv)

    out_dir = Path(args.output_dir)
    files = {k: out_dir / v for k, v in STAGE_FILENAMES.items()}
    s10 = _read_jsonl(files["stage_1_0"])
    s11 = _read_jsonl(files["stage_1_1"])
    s115 = _read_jsonl(files["stage_1_1_5"])
    s12 = _read_jsonl(files["stage_1_2"])

    e2e_retention = (len(s12) / len(s10)) if s10 else None

    metrics: Dict[str, Any] = {
        "stage_1_0": _stage_1_0_metrics(s10),
        "stage_1_1": _stage_1_1_metrics(s11),
        "stage_1_1_5": _stage_1_1_5_metrics(s11, s115),
        "stage_1_2": _stage_1_2_metrics(s12, s115),
        "e2e": {
            "input_rows_seed": len(s10),
            "output_rows_by_stage": [len(s10), len(s11), len(s115), len(s12)],
            "e2e_retention": round(e2e_retention, 3) if e2e_retention is not None else None,
        },
    }

    if args.json_out:
        Path(args.json_out).parent.mkdir(parents=True, exist_ok=True)
        Path(args.json_out).write_text(
            json.dumps(metrics, ensure_ascii=False, indent=2), encoding="utf-8"
        )
    else:
        json.dump(metrics, sys.stdout, ensure_ascii=False, indent=2)
        print()

    md = build_md_report(metrics)
    md_path = Path(args.md_out) if args.md_out else out_dir.parent / "quant_report.md"
    md_path.parent.mkdir(parents=True, exist_ok=True)
    md_path.write_text(md, encoding="utf-8")
    print(f"\n[quant_stage1_report] wrote {md_path}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
