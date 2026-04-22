"""Stage 2.2 judge: cluster coherence + canonical naming quality.

Evaluates `IntentCluster` records produced by
`pipelines.stage_2_2_canonicalize`. Two independent passes:

  (a) per-cluster rubric -- for each cluster, the judge rates coherence,
      canonical-name fit, Korean-output compliance, and whether it should be
      split. Members of split clusters get carried into `split_suggestion`.

  (b) cross-cluster duplicate pass -- ONE additional call that sees the whole
      canonical list and proposes pairs that should actually be merged
      (e.g. "운동복" ≈ "운동룩", "데일리룩" ≈ "캐주얼"). These land as
      DuplicateCanonicalPair records at the top of judge.jsonl.

Output:
  $STAGE_DATA_ROOT/stage_2_2/eval/runs/<run_id>/judge.jsonl
  $STAGE_DATA_ROOT/stage_2_2/eval/runs/<run_id>/report.md
  $STAGE_DATA_ROOT/stage_2_2/eval/runs/<run_id>/meta.json
  $STAGE_DATA_ROOT/stage_2_2/eval/summary.jsonl      (append)
  $STAGE_DATA_ROOT/stage_2_2/eval/latest_report.md

Usage:
  LLM_VERIFY_SSL=0 python -m pipelines.eval.stage_2_2_judge
  python -m pipelines.eval.stage_2_2_judge --input ./data/stage_2_2_clusters.jsonl
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import sys
import time
from collections import Counter
from pathlib import Path
from typing import Any, Dict, List, Optional

from pydantic import ValidationError

from pipelines.config import data_root
from pipelines.eval import common
from pipelines.eval.judge_client import call_json_judge
from pipelines.eval.prompts import (
    STAGE_2_2_DUPLICATE_SYSTEM,
    STAGE_2_2_DUPLICATE_USER_TEMPLATE,
    STAGE_2_2_JUDGE_SYSTEM,
    STAGE_2_2_JUDGE_USER_TEMPLATE,
)
from pipelines.eval.schemas import (
    STAGE_2_2_FAILURE_MODES,
    DuplicateCanonicalPair,
    Stage2_2JudgeRecord,
    Stage2_2JudgeResult,
    Stage2_2SummaryRow,
)
from pipelines.llm_client import get_client, load_env
from pipelines.schemas import IntentCluster

STAGE = "stage_2_2"
DEFAULT_JUDGE_MODEL = "nvidia/llama-3.1-nemotron-ultra-253b-v1"

_HANGUL = re.compile(r"[\uac00-\ud7a3]")


# ---------------------------------------------------------------------------
# Parsing
# ---------------------------------------------------------------------------

def _to_int(v: object, lo: int, hi: int) -> int:
    try:
        iv = int(v)
    except (TypeError, ValueError):
        return lo
    return max(lo, min(hi, iv))


def parse_cluster_judge(raw: Optional[Dict]) -> Optional[Stage2_2JudgeResult]:
    if not raw:
        return None
    split_suggestion: List[List[str]] = []
    rs = raw.get("split_suggestion") or []
    if isinstance(rs, list):
        for sg in rs:
            if isinstance(sg, list):
                split_suggestion.append(
                    [str(m) for m in sg if isinstance(m, str)]
                )
    try:
        return Stage2_2JudgeResult(
            cluster_coherent=bool(raw.get("cluster_coherent", False)),
            canonical_fit=_to_int(raw.get("canonical_fit"), 1, 5),
            canonical_language_ok=bool(raw.get("canonical_language_ok", False)),
            should_split=bool(raw.get("should_split", False)),
            split_suggestion=split_suggestion,
            failure_modes=common.safe_string_list(raw.get("failure_modes")),
            reasoning=str(raw.get("reasoning") or "").strip()[:500],
        )
    except ValidationError as exc:
        print(f"  [warn] schema error: {exc}", flush=True)
        return None


def parse_duplicate_pairs(raw: Optional[Dict]) -> List[DuplicateCanonicalPair]:
    if not raw:
        return []
    pairs: List[DuplicateCanonicalPair] = []
    seen = set()
    for entry in raw.get("duplicate_pairs") or []:
        if not isinstance(entry, dict):
            continue
        a = str(entry.get("canonical_a") or "").strip()
        b = str(entry.get("canonical_b") or "").strip()
        if not a or not b or a == b:
            continue
        key = tuple(sorted([a, b]))
        if key in seen:
            continue
        seen.add(key)
        try:
            pairs.append(
                DuplicateCanonicalPair(
                    canonical_a=a,
                    canonical_b=b,
                    confidence=_to_int(entry.get("confidence"), 1, 5),
                    reason=str(entry.get("reason") or "").strip()[:200],
                )
            )
        except ValidationError:
            continue
    return pairs


def build_cluster_user(cluster: IntentCluster) -> str:
    members = "\n".join(f"    - {m}" for m in cluster.raw_intents)
    return STAGE_2_2_JUDGE_USER_TEMPLATE.format(
        cluster_id=cluster.cluster_id,
        canonical_name=cluster.canonical_name,
        member_count=cluster.member_count,
        members=members,
    )


def build_duplicate_user(clusters: List[IntentCluster]) -> str:
    lines = []
    for c in clusters:
        if c.canonical_name == "일반":
            continue
        members_str = ", ".join(f'"{m}"' for m in c.raw_intents)
        lines.append(
            f"- {c.canonical_name} (evidence={c.member_count}): [{members_str}]"
        )
    return STAGE_2_2_DUPLICATE_USER_TEMPLATE.format(intent_list="\n".join(lines))


# ---------------------------------------------------------------------------
# Report
# ---------------------------------------------------------------------------

def build_report(
    records: List[Stage2_2JudgeRecord],
    dup_pairs: List[DuplicateCanonicalPair],
    meta: common.RunMeta,
) -> str:
    n = len(records)
    if n == 0:
        return "# Stage 2.2 Judge Report\n\n(no records)\n"

    coherent = sum(1 for r in records if r.judge.cluster_coherent)
    canonical_fit_scores = [r.judge.canonical_fit for r in records]
    non_korean = sum(1 for r in records if not r.judge.canonical_language_ok)
    should_split = [r for r in records if r.judge.should_split]

    fm_counter: Counter = Counter()
    for r in records:
        for fm in r.judge.failure_modes:
            fm_counter[fm] += 1
    for fm in STAGE_2_2_FAILURE_MODES:
        fm_counter.setdefault(fm, 0)

    low_fit = sorted(records, key=lambda r: (r.judge.canonical_fit, r.cluster_id))[:5]
    heterogeneous = [r for r in records if not r.judge.cluster_coherent][:5]
    non_korean_examples = [r for r in records if not r.judge.canonical_language_ok][:5]

    lines: List[str] = []
    lines.append("# Stage 2.2 Judge Report")
    lines.append("")
    lines.append(f"- run_id: `{meta.run_id}`")
    lines.append(f"- clusters evaluated: **{n}**")
    lines.append(f"- judge model: `{meta.judge_model}` (provider={meta.provider})")
    if meta.duration_sec:
        lines.append(f"- duration: {meta.duration_sec}s")
    lines.append("")

    lines.append("## Cluster quality")
    lines.append(f"- coherent clusters: **{common.pct(coherent, n)}**")
    lines.append(f"- avg canonical_fit: **{common.safe_mean(canonical_fit_scores)}** / 5")
    lines.append(f"- non-Korean canonical: **{common.pct(non_korean, n)}**")
    lines.append(f"- clusters judge wants to split: **{common.pct(len(should_split), n)}**")
    lines.append("")

    lines.append("## Cross-cluster duplicates (one-shot LLM pass)")
    if not dup_pairs:
        lines.append("- no duplicate pairs detected")
    else:
        lines.append("")
        lines.append("| canonical_a | canonical_b | confidence | reason |")
        lines.append("|---|---|---|---|")
        for p in sorted(dup_pairs, key=lambda x: -x.confidence):
            lines.append(
                f"| `{p.canonical_a}` | `{p.canonical_b}` | {p.confidence} | "
                f"{common.truncate(p.reason, 80)} |"
            )
    lines.append("")

    lines.append("## Failure-mode histogram")
    lines.append("")
    lines.append("| failure_mode | count |")
    lines.append("|---|---|")
    for fm, cnt in sorted(fm_counter.items(), key=lambda x: (-x[1], x[0])):
        lines.append(f"| `{fm}` | {cnt} |")
    lines.append("")

    def _render(rows: List[Stage2_2JudgeRecord], title: str) -> None:
        lines.append(f"### {title}")
        if not rows:
            lines.append("(none)")
            lines.append("")
            return
        for r in rows:
            lines.append(
                f"- **{r.cluster_id}** `{r.canonical_name}` "
                f"(members={r.member_count}) "
                f"fit={r.judge.canonical_fit} "
                f"coherent={r.judge.cluster_coherent} "
                f"lang_ok={r.judge.canonical_language_ok} "
                f"should_split={r.judge.should_split}"
            )
            lines.append(f"  - members: `{r.raw_intents}`")
            if r.judge.split_suggestion:
                lines.append(f"  - split_suggestion: `{r.judge.split_suggestion}`")
            lines.append(f"  - fm: `{r.judge.failure_modes}`")
            lines.append(f"  - judge: {common.truncate(r.judge.reasoning, 160)}")
        lines.append("")

    lines.append("## Worst clusters")
    lines.append("")
    _render(low_fit, "Lowest canonical_fit (top 5)")
    _render(heterogeneous, "Heterogeneous (cluster_coherent=false, top 5)")
    _render(should_split[:5], "should_split=true (top 5)")
    _render(non_korean_examples, "Non-Korean canonical (top 5)")

    return "\n".join(line for line in lines if line != "")


def build_summary_row(
    records: List[Stage2_2JudgeRecord],
    dup_pairs: List[DuplicateCanonicalPair],
    meta: common.RunMeta,
) -> Stage2_2SummaryRow:
    n = len(records)
    coherent = sum(1 for r in records if r.judge.cluster_coherent)
    non_korean = sum(1 for r in records if not r.judge.canonical_language_ok)
    should_split = sum(1 for r in records if r.judge.should_split)

    fm_counter: Counter = Counter()
    for r in records:
        for fm in r.judge.failure_modes:
            fm_counter[fm] += 1
    for fm in STAGE_2_2_FAILURE_MODES:
        fm_counter.setdefault(fm, 0)

    return Stage2_2SummaryRow(
        run_id=meta.run_id,
        judge_model=meta.judge_model,
        provider=meta.provider,
        n_clusters=n,
        coherent_rate=round(coherent / n, 2) if n else 0.0,
        avg_canonical_fit=common.safe_mean([r.judge.canonical_fit for r in records]),
        non_korean_canonical_count=non_korean,
        should_split_count=should_split,
        duplicate_pairs_found=len(dup_pairs),
        failure_modes=dict(fm_counter),
        duration_sec=meta.duration_sec or 0.0,
        tag=meta.tag,
    )


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main(argv: List[str] | None = None) -> int:
    root = data_root()
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--input",
        default=str(root / "stage_2_2" / "stage_2_2_clusters.jsonl"),
    )
    parser.add_argument("--judge-model", default=DEFAULT_JUDGE_MODEL)
    parser.add_argument(
        "--provider", choices=["nim", "friendli", "vllm"], default="nim"
    )
    parser.add_argument("--limit", type=int, default=0, help="0 = all clusters")
    parser.add_argument("--sleep", type=float, default=0.2)
    parser.add_argument("--max-tokens", type=int, default=1024)
    parser.add_argument(
        "--skip-duplicates", action="store_true",
        help="skip the cross-cluster duplicate detection pass",
    )
    parser.add_argument("--duplicate-max-tokens", type=int, default=2048)
    parser.add_argument("--tag", default="")
    parser.add_argument("--run-id", default="")
    args = parser.parse_args(argv)

    load_env()
    client, _ = get_client(
        provider=args.provider, model_override=args.judge_model
    )
    cfg = client._llm_config  # type: ignore[attr-defined]

    run_id = args.run_id or common.make_run_id(args.tag or None)
    out_dir = common.run_dir(STAGE, run_id)
    judge_path = out_dir / "judge.jsonl"
    report_path = out_dir / "report.md"
    meta_path = out_dir / "meta.json"

    clusters: List[IntentCluster] = [
        IntentCluster.model_validate(obj) for obj in common.iter_jsonl(Path(args.input))
    ]
    # Drop "일반" from eval: it's a fixed fallback bucket, not a real cluster.
    real_clusters = [c for c in clusters if c.canonical_name != "일반"]
    n_total = len(real_clusters)
    subset = common.cap(real_clusters, args.limit)

    print(
        f"[stage_2_2 judge] run_id={run_id} {cfg.describe()}\n"
        f"  clusters_total={n_total} sampled={len(subset)} (dropped '일반')\n"
        f"  -> {out_dir}",
        flush=True,
    )

    meta = common.RunMeta(
        stage=STAGE,
        run_id=run_id,
        started_at=dt.datetime.now(dt.timezone.utc).isoformat(),
        judge_model=cfg.model,
        provider=cfg.provider,
        input_path=str(args.input),
        limit=args.limit,
        n_units_total=n_total,
        n_units_sampled=len(subset),
        tag=args.tag,
        git_rev=common.git_rev_short(),
        extra={"skip_duplicates": args.skip_duplicates},
    )

    ok = fail = 0
    t0 = time.time()
    records: List[Stage2_2JudgeRecord] = []
    dup_pairs: List[DuplicateCanonicalPair] = []

    # -- Pass 1: per-cluster judge -------------------------------------------
    with judge_path.open("w", encoding="utf-8") as out_fh:
        for i, cluster in enumerate(subset):
            user_prompt = build_cluster_user(cluster)

            def _call(mt: int):
                return call_json_judge(
                    client,
                    cfg.model,
                    STAGE_2_2_JUDGE_SYSTEM,
                    user_prompt,
                    temperature=0.1,
                    max_tokens=mt,
                )

            parsed, call_meta, tag = common.call_with_retry(
                _call, max_tokens=args.max_tokens, sleep=args.sleep
            )
            judge = parse_cluster_judge(parsed)
            if judge is None:
                fail += 1
                print(
                    f"[{i + 1:04d}] ERR {cluster.cluster_id}: {tag} "
                    f"tokens={call_meta.get('tokens')} "
                    f"raw={(call_meta.get('raw_content') or '')[:120]!r}",
                    flush=True,
                )
                time.sleep(args.sleep)
                continue

            # Post-hoc: if canonical has no Hangul character and judge said OK,
            # override to false (judge occasionally misreads "general_wear").
            if not _HANGUL.search(cluster.canonical_name) and judge.canonical_language_ok:
                judge.canonical_language_ok = False
                if "non_korean_canonical" not in judge.failure_modes:
                    judge.failure_modes.append("non_korean_canonical")

            record = Stage2_2JudgeRecord(
                cluster_id=cluster.cluster_id,
                canonical_name=cluster.canonical_name,
                raw_intents=cluster.raw_intents,
                member_count=cluster.member_count,
                judge=judge,
                judge_model=call_meta["model"],
                judge_tokens=call_meta.get("tokens"),
            )
            out_fh.write(record.model_dump_json() + "\n")
            out_fh.flush()
            records.append(record)
            ok += 1

            print(
                f"[{i + 1:04d}] OK  {cluster.cluster_id} '{cluster.canonical_name}' "
                f"coh={judge.cluster_coherent} fit={judge.canonical_fit} "
                f"ko={judge.canonical_language_ok} split={judge.should_split} "
                f"fm={judge.failure_modes or '[]'}",
                flush=True,
            )
            time.sleep(args.sleep)

        # -- Pass 2: cross-cluster duplicate detection (one extra call) -----
        if not args.skip_duplicates and real_clusters:
            print("\n[stage_2_2 judge] cross-cluster duplicate pass ...", flush=True)
            user_prompt = build_duplicate_user(real_clusters)

            def _dup_call(mt: int):
                return call_json_judge(
                    client,
                    cfg.model,
                    STAGE_2_2_DUPLICATE_SYSTEM,
                    user_prompt,
                    temperature=0.1,
                    max_tokens=mt,
                )

            parsed_dup, dup_meta, dup_tag = common.call_with_retry(
                _dup_call, max_tokens=args.duplicate_max_tokens, sleep=args.sleep
            )
            dup_pairs = parse_duplicate_pairs(parsed_dup)
            if parsed_dup is None:
                print(
                    f"  [warn] duplicate pass failed ({dup_tag}); "
                    f"raw={(dup_meta.get('raw_content') or '')[:160]!r}",
                    flush=True,
                )

            # Persist duplicate pairs as one trailing JSON line per pair.
            for p in dup_pairs:
                # Mark with a marker key so downstream readers can tell apart
                # from Stage2_2JudgeRecord.
                line = p.model_dump()
                line["_record_type"] = "duplicate_pair"
                out_fh.write(json.dumps(line, ensure_ascii=False) + "\n")
            out_fh.flush()
            print(
                f"  duplicate_pairs={len(dup_pairs)}",
                flush=True,
            )

    meta.finished_at = dt.datetime.now(dt.timezone.utc).isoformat()
    meta.duration_sec = round(time.time() - t0, 1)
    meta.n_ok = ok
    meta.n_fail = fail
    common.write_meta(meta_path, meta)

    report_md = build_report(records, dup_pairs, meta)
    report_path.write_text(report_md, encoding="utf-8")

    summary_row = build_summary_row(records, dup_pairs, meta)
    common.append_summary(STAGE, summary_row.model_dump())
    common.copy_latest_report(STAGE, run_id)

    print(
        f"\n[done] clusters ok={ok} fail={fail} dup_pairs={len(dup_pairs)} "
        f"time={meta.duration_sec}s\n"
        f"  judge.jsonl: {judge_path}\n"
        f"  report.md  : {report_path}\n"
        f"  meta.json  : {meta_path}\n"
        f"  summary row appended at eval/summary.jsonl",
        flush=True,
    )
    return 0 if fail == 0 else 2


if __name__ == "__main__":
    sys.exit(main())
