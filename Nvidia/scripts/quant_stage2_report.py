"""Deterministic (no-LLM) quantitative probe for Stage 2 output.

Two modes:

1. `--mode iter` (default) — §4e metrics for a full iter's output/:
   reads stage_2_1_extracted.jsonl, stage_2_1_5_stats.json,
   stage_2_2_clusters.jsonl, stage_2_3_analyzed_intents.jsonl,
   stage_2_4_expanded_intents.jsonl and emits the deterministic probes
   defined in experiments_stage2/PLAN.md §4e (semdedup retention +
   canonical suffix / non-fashion / query dedup).

2. `--mode semdedup-probe` — PLAN §5a one-shot threshold sweep that runs
   BEFORE SD1. Takes `stage_2_1_extracted.jsonl`, embeds with BGE-M3,
   and reports per-threshold `pairs_above_threshold`, `removed_count`,
   `removed_rate`, `avg_cosine_of_kept` across a grid. Guides the
   data-driven SD1 threshold selection.

Usage:
  python scripts/quant_stage2_report.py \\
      --output-dir experiments_stage2/iter_00_baseline/output \\
      --json-out   experiments_stage2/iter_00_baseline/quant_metrics.json \\
      --md-out     experiments_stage2/iter_00_baseline/quant_report.md

  python scripts/quant_stage2_report.py \\
      --mode semdedup-probe \\
      --input  experiments_stage2/iter_00_baseline/output/stage_2_1_extracted.jsonl \\
      --thresholds 0.95,0.90,0.85,0.80,0.75,0.70 \\
      --signature full \\
      --out    experiments_stage2/iter_00a_semdedup_probe/semdedup_probe.json
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import unicodedata
from pathlib import Path
from typing import Any, Dict, List, Optional


# ---------------------------------------------------------------------------
# Stage 2 output filenames
# ---------------------------------------------------------------------------

STAGE_FILES = {
    "stage_2_1":     "stage_2_1_extracted.jsonl",
    "stage_2_1_5":   "stage_2_1_5_deduped.jsonl",
    "stage_2_1_5_stats": "stage_2_1_5_stats.json",
    "stage_2_2":     "stage_2_2_clusters.jsonl",
    "stage_2_3":     "stage_2_3_analyzed_intents.jsonl",
    "stage_2_4":     "stage_2_4_expanded_intents.jsonl",
}


# ---------------------------------------------------------------------------
# Regex heuristics (PLAN §4e)
# ---------------------------------------------------------------------------

# Hangul + optional spaces. Anything outside this + punct is non-Hangul.
_HANGUL_RE = re.compile(r"[\uAC00-\uD7A3]")

# Valid canonical suffixes per PLAN §4a/§4e. Append/prepend variants covered.
_CANONICAL_SUFFIX_PATTERNS = (
    "룩", "웨어", "복", "스타일", "캐주얼", "패션", "유형", "아이템", "감성",
)

# Non-fashion giveaways. Heuristic, not exhaustive; used as a quant probe only.
# Does not aim for precision — over-flags is fine, reviewer can inspect.
_NON_FASHION_KEYWORDS = (
    # 지명
    "서울", "부산", "제주", "경주", "강원", "인천", "대구", "광주",
    "의림지", "한강", "지리산", "설악",
    # 날씨 / 계절 명사 (단독으로 canonical 이면 이상)
    "비오는날", "눈오는날", "아침안개", "황사",
    # 사람 이름 / 관계
    "손주", "할머니", "할아버지", "사위", "며느리",
    # 음식 / 기타
    "떡볶이", "김밥", "식당", "요리",
)

# Query pathology detection
_NON_HANGUL_RE = re.compile(r"[a-zA-Z]{3,}")


# ---------------------------------------------------------------------------
# IO helpers
# ---------------------------------------------------------------------------

def _read_jsonl(path: Path) -> List[Dict[str, Any]]:
    if not path.exists():
        return []
    out: List[Dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            out.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return out


def _read_json(path: Path) -> Optional[Dict[str, Any]]:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None


def _pct(part: int, total: int) -> float:
    return round(part / total, 3) if total else 0.0


def _hangul_ratio(s: str) -> float:
    if not s:
        return 0.0
    hangul = sum(1 for c in s if _HANGUL_RE.match(c))
    return hangul / max(len(s), 1)


def _is_canonical_suffix_compliant(name: str) -> bool:
    n = name.strip()
    if not n:
        return False
    for suf in _CANONICAL_SUFFIX_PATTERNS:
        if n.endswith(suf):
            return True
    # '일반' is the fixed bucket; always compliant
    return n == "일반"


def _is_non_fashion_canonical(name: str) -> bool:
    n = name.strip()
    for kw in _NON_FASHION_KEYWORDS:
        if kw in n:
            return True
    return False


# ---------------------------------------------------------------------------
# Mode 1: iter probes (§4e)
# ---------------------------------------------------------------------------

def _stage_2_1_probe(records: List[Dict[str, Any]]) -> Dict[str, Any]:
    n = len(records)
    if n == 0:
        return {"n": 0}
    general_wear = sum(
        1 for r in records
        if (r.get("raw_intent") or "").strip().lower() == "general_wear"
    )
    # Attribute concreteness by key (non-null, non-empty ratio)
    attr_counts = {"material": 0, "fit": 0, "color": 0, "style": 0, "season": 0}
    for r in records:
        a = r.get("attributes") or {}
        for k in attr_counts:
            v = a.get(k)
            if isinstance(v, str) and v.strip():
                attr_counts[k] += 1
    # Keyword quality probe (informational)
    kw_lens = [
        len(r.get("extracted_keywords") or [])
        for r in records
    ]
    return {
        "n": n,
        "general_wear_rate": _pct(general_wear, n),
        "attr_concrete_rate": {k: _pct(v, n) for k, v in attr_counts.items()},
        "avg_keywords_per_doc": round(sum(kw_lens) / n, 2) if n else 0.0,
    }


def _stage_2_1_5_probe(
    stats: Optional[Dict[str, Any]],
    s21_n: int,
    s215_n: int,
) -> Dict[str, Any]:
    base = {
        "input_rows": s21_n,
        "kept_rows": s215_n,
        "semdedup_retention_rate": (
            round(s215_n / s21_n, 3) if s21_n else None
        ),
    }
    if stats:
        base.update({
            "semdedup_removed_count": stats.get("removed"),
            "semdedup_pairs_above_threshold": stats.get("pairs_above_threshold"),
            "semdedup_avg_cosine_of_kept": stats.get("avg_cosine_of_kept"),
            "semdedup_selected_threshold": stats.get("selected_threshold"),
            "semdedup_signature_builder_used": stats.get("signature_builder_used"),
            "semdedup_mode": stats.get("mode"),
        })
    return base


def _stage_2_2_probe(records: List[Dict[str, Any]]) -> Dict[str, Any]:
    n = len(records)
    if n == 0:
        return {"n": 0}
    # Exclude '일반' from suffix / non-fashion checks (it is the fixed bucket).
    real = [r for r in records if (r.get("canonical_name") or "") != "일반"]
    n_real = len(real)

    names = [str(r.get("canonical_name") or "") for r in real]
    hangul_pure = sum(1 for n_ in names if _hangul_ratio(n_) >= 0.95)
    suffix_ok = sum(1 for n_ in names if _is_canonical_suffix_compliant(n_))
    non_fashion = sum(1 for n_ in names if _is_non_fashion_canonical(n_))
    evidence_counts = [int(r.get("member_count") or 0) for r in real]
    ev1 = sum(1 for e in evidence_counts if e <= 1)

    return {
        "n": n,
        "n_real_clusters": n_real,
        "canonical_count": n,
        "canonical_hangul_pure_rate": _pct(hangul_pure, n_real),
        "canonical_suffix_compliance_rate": _pct(suffix_ok, n_real),
        "canonical_non_fashion_rate": _pct(non_fashion, n_real),
        "canonical_non_fashion_count": non_fashion,
        "evidence_one_count": ev1,
        "canonical_names": names,
    }


def _stage_2_3_probe(records: List[Dict[str, Any]]) -> Dict[str, Any]:
    n = len(records)
    if n == 0:
        return {"n": 0}
    total_attrs = 0
    dup_like = 0
    # light cross-lingual pair detector: (linen, 린넨), (navy, 네이비), ...
    # We count attributes per cluster and detect if two values normalize to
    # the same thing. Heuristic only.
    _BILINGUAL_PAIRS = {
        "linen": "린넨", "cotton": "코튼",
        "wool": "울", "silk": "실크",
        "denim": "데님",
        "navy": "네이비", "beige": "베이지",
        "white": "화이트", "black": "블랙",
        "grey": "그레이", "gray": "그레이",
    }
    for r in records:
        attrs = r.get("mapped_attributes") or []
        total_attrs += len(attrs)
        values_by_key: Dict[str, List[str]] = {}
        for a in attrs:
            k = str(a.get("attribute_key") or "").lower()
            v = str(a.get("attribute_value") or "").strip().lower()
            values_by_key.setdefault(k, []).append(v)
        for k, vals in values_by_key.items():
            seen_canon: set[str] = set()
            for v in vals:
                canon = _BILINGUAL_PAIRS.get(v, v)
                canon = _BILINGUAL_PAIRS_INV.get(canon, canon)
                if canon in seen_canon:
                    dup_like += 1
                else:
                    seen_canon.add(canon)
    return {
        "n": n,
        "total_attr_count": total_attrs,
        "avg_attrs_per_intent": round(total_attrs / n, 2) if n else 0.0,
        "duplicate_value_count": dup_like,
    }


# Inverse of the bilingual pair (for normalization)
_BILINGUAL_PAIRS_INV: Dict[str, str] = {
    "린넨": "linen", "코튼": "cotton",
    "울": "wool", "실크": "silk",
    "데님": "denim",
    "네이비": "navy", "베이지": "beige",
    "화이트": "white", "블랙": "black",
    "그레이": "grey",
}


def _stage_2_4_probe(records: List[Dict[str, Any]]) -> Dict[str, Any]:
    n = len(records)
    if n == 0:
        return {"n": 0}
    per_intent_unique_ratios = []
    total_queries = 0
    garbled = 0
    non_hangul_hits = 0
    canonical_names = []
    repeats_within_intent = 0
    query_lens = []
    for r in records:
        qs = list(r.get("natural_queries") or [])
        qs = [q.strip() for q in qs if isinstance(q, str)]
        total_queries += len(qs)
        canonical_names.append(str(r.get("intent_keyword") or ""))
        uniq = set(qs)
        per_intent_unique_ratios.append(
            len(uniq) / len(qs) if qs else 1.0
        )
        repeats_within_intent += len(qs) - len(uniq)
        for q in qs:
            query_lens.append(len(q))
            # crude garbled detector: empty after strip, non-UTF handling,
            # mostly non-Hangul in a Korean query context.
            if not q:
                garbled += 1
                continue
            if _NON_HANGUL_RE.search(q):
                non_hangul_hits += 1

    canonical_repeat = len(canonical_names) - len(set(canonical_names))

    return {
        "n_intents": n,
        "total_queries": total_queries,
        "query_dedup_ratio": (
            round(sum(per_intent_unique_ratios) / n, 3) if n else 0.0
        ),
        "query_repeat_within_intent_count": repeats_within_intent,
        "query_avg_length_chars": (
            round(sum(query_lens) / max(len(query_lens), 1), 1)
        ),
        "query_non_hangul_chars_count": non_hangul_hits,
        "query_non_hangul_chars_rate": _pct(non_hangul_hits, total_queries),
        "garbled_count": garbled,
        "canonical_repeat_rate": _pct(canonical_repeat, n),
    }


def run_iter_mode(
    output_dir: Path,
    json_out: Optional[Path],
    md_out: Optional[Path],
) -> int:
    s21   = _read_jsonl(output_dir / STAGE_FILES["stage_2_1"])
    s215  = _read_jsonl(output_dir / STAGE_FILES["stage_2_1_5"])
    stats = _read_json(output_dir / STAGE_FILES["stage_2_1_5_stats"])
    s22   = _read_jsonl(output_dir / STAGE_FILES["stage_2_2"])
    s23   = _read_jsonl(output_dir / STAGE_FILES["stage_2_3"])
    s24   = _read_jsonl(output_dir / STAGE_FILES["stage_2_4"])

    metrics: Dict[str, Any] = {
        "stage_2_1":   _stage_2_1_probe(s21),
        "stage_2_1_5": _stage_2_1_5_probe(stats, len(s21), len(s215)),
        "stage_2_2":   _stage_2_2_probe(s22),
        "stage_2_3":   _stage_2_3_probe(s23),
        "stage_2_4":   _stage_2_4_probe(s24),
        "e2e": {
            "rows_by_stage": [
                len(s21), len(s215), len(s22), len(s23), len(s24),
            ],
        },
    }

    if json_out:
        json_out.parent.mkdir(parents=True, exist_ok=True)
        json_out.write_text(
            json.dumps(metrics, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
    else:
        json.dump(metrics, sys.stdout, ensure_ascii=False, indent=2)
        print()

    md = _build_md_report(metrics)
    md_path = md_out if md_out else output_dir.parent / "quant_report.md"
    md_path.parent.mkdir(parents=True, exist_ok=True)
    md_path.write_text(md, encoding="utf-8")
    print(f"[quant_stage2_report] wrote {md_path}", file=sys.stderr)
    return 0


def _build_md_report(metrics: Dict[str, Any]) -> str:
    lines: List[str] = []
    lines.append("# Stage 2 Quantitative Probe")
    lines.append("")
    lines.append("(no-LLM deterministic metrics; LLM judges are separate)")
    lines.append("")

    e2e = metrics.get("e2e", {}).get("rows_by_stage") or []
    lines.append("## Pipeline volume")
    lines.append("")
    lines.append("| stage | rows |")
    lines.append("|---|---|")
    for stage_name, rows in zip(
        ("2.1 extract", "2.1.5 deduped", "2.2 clusters", "2.3 analyzed", "2.4 expanded"),
        e2e,
    ):
        lines.append(f"| {stage_name} | {rows} |")
    lines.append("")

    s215 = metrics.get("stage_2_1_5") or {}
    lines.append("## Stage 2.1.5 — semantic dedup")
    lines.append(f"- retention: **{s215.get('semdedup_retention_rate')}**")
    lines.append(f"- removed: {s215.get('semdedup_removed_count')}")
    lines.append(f"- avg cosine of kept: {s215.get('semdedup_avg_cosine_of_kept')}")
    lines.append(f"- selected threshold: {s215.get('semdedup_selected_threshold')}")
    lines.append(f"- signature builder: {s215.get('semdedup_signature_builder_used')}")
    lines.append(f"- mode: {s215.get('semdedup_mode')}")
    lines.append("")

    s22 = metrics.get("stage_2_2") or {}
    lines.append("## Stage 2.2 — canonicals")
    lines.append(f"- canonical_count: **{s22.get('canonical_count')}** (of which '일반' excluded = {s22.get('n_real_clusters')})")
    lines.append(f"- canonical_hangul_pure_rate: {s22.get('canonical_hangul_pure_rate')}")
    lines.append(f"- canonical_suffix_compliance_rate: **{s22.get('canonical_suffix_compliance_rate')}**  (promote ≥ 0.80)")
    lines.append(f"- canonical_non_fashion_rate: **{s22.get('canonical_non_fashion_rate')}**  (promote ≤ 0.05)")
    lines.append(f"- evidence_one_count: {s22.get('evidence_one_count')}")
    names = s22.get("canonical_names") or []
    if names:
        lines.append(f"- names: `{names}`")
    lines.append("")

    s23 = metrics.get("stage_2_3") or {}
    lines.append("## Stage 2.3 — aggregated attrs")
    lines.append(f"- avg_attrs_per_intent: {s23.get('avg_attrs_per_intent')}")
    lines.append(f"- duplicate_value_count: **{s23.get('duplicate_value_count')}**  (promote ≤ 2)")
    lines.append("")

    s24 = metrics.get("stage_2_4") or {}
    lines.append("## Stage 2.4 — expanded queries")
    lines.append(f"- query_dedup_ratio: **{s24.get('query_dedup_ratio')}**  (promote ≥ 0.95)")
    lines.append(f"- query_repeat_within_intent_count: {s24.get('query_repeat_within_intent_count')}")
    lines.append(f"- query_avg_length_chars: {s24.get('query_avg_length_chars')}")
    lines.append(f"- query_non_hangul_chars_rate: {s24.get('query_non_hangul_chars_rate')}  (promote ≤ 0.01)")
    lines.append(f"- garbled_count: **{s24.get('garbled_count')}**  (promote = 0)")
    lines.append(f"- canonical_repeat_rate: {s24.get('canonical_repeat_rate')}  (promote ≤ 0.10)")
    lines.append("")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Mode 2: pre-SD semdedup probe (§5a)
# ---------------------------------------------------------------------------

def run_semdedup_probe(
    input_path: Path,
    thresholds: List[float],
    signature_builder: str,
    out_path: Path,
    embed_model: str,
    device: str,
) -> int:
    """Threshold sweep on stage_2_1_extracted.jsonl. Does NOT write a
    deduped file — just reports per-threshold removal stats so the
    orchestrator can pick SD1's data-driven threshold."""
    from pipelines.schemas import ExtractedIntent
    from pipelines.stage_2_1_5_semdedup import (
        build_signature,
        embed_signatures,
        dedup_by_cosine,
        _auto_device,
    )
    import numpy as np

    rows: List[ExtractedIntent] = []
    with input_path.open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            rows.append(ExtractedIntent.model_validate_json(line))
    n = len(rows)
    if n == 0:
        print("[probe] empty input; nothing to sweep", file=sys.stderr)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(
            json.dumps({"input_rows": 0, "sweep": []}, indent=2),
            encoding="utf-8",
        )
        return 0

    signatures = [build_signature(r, signature_builder) for r in rows]
    dev = _auto_device(device)
    embeddings = embed_signatures(signatures, embed_model, device=dev)
    # Pre-compute the full similarity matrix once; re-use across thresholds.
    sim = embeddings @ embeddings.T
    tri = np.triu(sim, k=1)

    sweep: List[Dict[str, Any]] = []
    recommended: Optional[float] = None

    # PLAN §5a: pick the smallest threshold in the grid whose
    # removed_rate lies in [0.10, 0.25] as the data-driven SD1 threshold.
    for thr in sorted(thresholds, reverse=True):
        pairs_above = int(np.sum(tri >= thr))
        kept_idx, removed_idx, _, avg_cos = dedup_by_cosine(
            signatures, embeddings, threshold=thr
        )
        removed_rate = len(removed_idx) / n if n else 0.0
        sweep.append({
            "threshold": round(thr, 4),
            "pairs_above_threshold": pairs_above,
            "removed_count": len(removed_idx),
            "kept_count": len(kept_idx),
            "removed_rate": round(removed_rate, 3),
            "avg_cosine_of_kept": (
                round(avg_cos, 4) if avg_cos else 0.0
            ),
        })

    # Recommendation: smallest-threshold-in-band
    for row in sweep:  # sweep is descending by threshold
        rr = row["removed_rate"]
        if 0.10 <= rr <= 0.25:
            recommended = row["threshold"]
            # keep scanning: we want the SMALLEST threshold in band (i.e. most
            # aggressive operating point that stays within 10-25% removal)
    if recommended is None:
        # fall back to the threshold with the highest removal_rate <= 0.25
        viable = [r for r in sweep if r["removed_rate"] <= 0.25 and r["removed_rate"] > 0]
        if viable:
            recommended = min(viable, key=lambda r: r["threshold"])["threshold"]

    result = {
        "input_path": str(input_path),
        "input_rows": n,
        "embed_model": embed_model,
        "device_used": dev,
        "signature_builder": signature_builder,
        "thresholds_probed": [round(t, 4) for t in sorted(thresholds, reverse=True)],
        "sweep": sweep,
        "recommended_threshold": recommended,
        "recommendation_rule": (
            "smallest threshold in [0.10, 0.25] removed_rate; fallback = "
            "smallest threshold with any removal <= 0.25"
        ),
    }
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(
        json.dumps(result, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(
        f"[probe] wrote {out_path}  recommended threshold: {recommended}",
        file=sys.stderr,
    )
    for r in sweep:
        print(
            f"  thr={r['threshold']:.2f}  pairs={r['pairs_above_threshold']:>4}  "
            f"removed={r['removed_count']:>3}/{n}  "
            f"rate={r['removed_rate']:.3f}  avg_cos_kept={r['avg_cosine_of_kept']:.4f}",
            file=sys.stderr,
        )
    return 0


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main(argv: List[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--mode",
        choices=["iter", "semdedup-probe"],
        default="iter",
    )
    # iter mode
    parser.add_argument("--output-dir", default="")
    parser.add_argument("--json-out", default="")
    parser.add_argument("--md-out", default="")
    # semdedup-probe mode
    parser.add_argument("--input", default="")
    parser.add_argument(
        "--thresholds",
        default="0.95,0.90,0.85,0.80,0.75,0.70",
        help="CSV of thresholds to sweep",
    )
    parser.add_argument(
        "--signature",
        default="full",
        choices=("full", "signature_combo", "intent_only"),
    )
    parser.add_argument("--out", default="")
    parser.add_argument("--embed-model", default="BAAI/bge-m3")
    parser.add_argument(
        "--device", default="auto", choices=["auto", "cpu", "cuda"]
    )
    args = parser.parse_args(argv)

    if args.mode == "iter":
        if not args.output_dir:
            parser.error("--output-dir is required for --mode iter")
        return run_iter_mode(
            Path(args.output_dir),
            Path(args.json_out) if args.json_out else None,
            Path(args.md_out) if args.md_out else None,
        )

    # mode == semdedup-probe
    if not args.input or not args.out:
        parser.error("--input and --out are required for --mode semdedup-probe")
    thresholds = [float(x) for x in args.thresholds.split(",") if x.strip()]
    return run_semdedup_probe(
        input_path=Path(args.input),
        thresholds=thresholds,
        signature_builder=args.signature,
        out_path=Path(args.out),
        embed_model=args.embed_model,
        device=args.device,
    )


if __name__ == "__main__":
    sys.exit(main())
