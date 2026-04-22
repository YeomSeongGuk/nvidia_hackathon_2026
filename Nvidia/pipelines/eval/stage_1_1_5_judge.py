"""Stage 1.1.5 judge: dedup-miss finder.

Audits the deduplication stage of the Stage-1 pipeline. For each judge
model we make **one** chat-completion call that contains:

  - the full BEFORE set  (Stage 1.1 synthetic output, compact form)
  - the full AFTER set   (Stage 1.1.5 deduped survivors, compact form)

The judge returns a list of near-duplicate groups it thinks the dedup
step should have collapsed but didn't. See
`pipelines/eval/prompts.py::STAGE_1_1_5_JUDGE_SYSTEM` for the rubric
and `schemas.py::Stage1_1_5JudgeResult`.

Output layout (same shape as other judges):
  $STAGE_DATA_ROOT/stage_1_1_5/eval/runs/<run_id>/
      judge.jsonl   one Stage1_1_5JudgeRecord per judge model
      report.md     ensemble / mean summary + miss-clusters
      meta.json     RunMeta
  $STAGE_DATA_ROOT/stage_1_1_5/eval/summary.jsonl    (append)
  $STAGE_DATA_ROOT/stage_1_1_5/eval/latest_report.md (copy)

Usage:
  # Friendli tri-judge ensemble (one judge at a time, call this script 3x
  # with --judge-model different each time, or let scripts/tri_judge_run.py
  # drive it):
  python -m pipelines.eval.stage_1_1_5_judge \\
      --before ./output/stage_1_1_synthetic.jsonl \\
      --after  ./output/stage_1_1_5_deduped.jsonl \\
      --provider friendli --judge-model zai-org/GLM-5.1
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
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
    STAGE_1_1_5_JUDGE_SYSTEM,
    STAGE_1_1_5_JUDGE_USER_TEMPLATE,
)
from pipelines.eval.schemas import (
    STAGE_1_1_5_FAILURE_MODES,
    NearDuplicateGroup,
    Stage1_1_5JudgeRecord,
    Stage1_1_5JudgeResult,
    Stage1_1_5SummaryRow,
)
from pipelines.llm_client import get_client, load_env


STAGE = "stage_1_1_5"
DEFAULT_JUDGE_MODEL = "zai-org/GLM-5.1"


# ---------------------------------------------------------------------------
# Compact record rendering — the judge prompt has to fit in context
# ---------------------------------------------------------------------------

def _doc_id_of(rec: Dict[str, Any], fallback_idx: int) -> str:
    """Return a stable short id we can quote back to the judge."""
    return (
        rec.get("doc_id")
        or rec.get("curated_id")
        or rec.get("id")
        or f"rec_{fallback_idx:05d}"
    )


def _render_record(rec: Dict[str, Any], idx: int, max_text_chars: int = 220) -> str:
    did = _doc_id_of(rec, idx)
    title = (rec.get("product_title") or "").replace("\n", " ").strip()
    if len(title) > 60:
        title = title[:57] + "..."
    text = (rec.get("raw_text") or rec.get("clean_text") or "").replace("\n", " ").strip()
    if len(text) > max_text_chars:
        text = text[: max_text_chars - 3] + "..."
    attrs = rec.get("product_attributes") or {}
    attr_str = " / ".join(
        f"{k}={v}" for k, v in attrs.items() if v not in (None, "")
    )
    rating = (rec.get("metadata") or {}).get("rating")
    return (
        f"- {did} | rating={rating} | attrs: {attr_str or '(none)'}\n"
        f"  title: {title}\n"
        f"  text : {text}"
    )


def _render_set(records: List[Dict[str, Any]], max_text_chars: int = 220) -> str:
    return "\n".join(
        _render_record(r, i, max_text_chars=max_text_chars)
        for i, r in enumerate(records)
    )


# ---------------------------------------------------------------------------
# Judge result parsing
# ---------------------------------------------------------------------------

def _to_int(v: object, default: int = 0) -> int:
    try:
        return int(v)
    except (TypeError, ValueError):
        return default


def _coerce_groups(raw: object) -> List[NearDuplicateGroup]:
    out: List[NearDuplicateGroup] = []
    if not isinstance(raw, list):
        return out
    for item in raw:
        if not isinstance(item, dict):
            continue
        doc_ids = item.get("doc_ids")
        if not isinstance(doc_ids, list) or len(doc_ids) < 2:
            continue
        try:
            out.append(
                NearDuplicateGroup(
                    doc_ids=[str(x) for x in doc_ids if x],
                    reason=str(item.get("reason") or "").strip()[:300],
                    severity=str(item.get("severity") or "medium").strip().lower(),
                )
            )
        except ValidationError:
            continue
    return out


def parse_judge_result(
    raw: Optional[Dict], before_count: int, after_count: int
) -> Optional[Stage1_1_5JudgeResult]:
    if not raw:
        return None
    groups = _coerce_groups(raw.get("near_duplicate_groups"))
    # Recompute miss_count from the authoritative groups list (models love
    # to hallucinate the number).
    miss_count = sum(max(0, len(g.doc_ids) - 1) for g in groups)
    try:
        return Stage1_1_5JudgeResult(
            near_duplicate_groups=groups,
            dedup_in_count=_to_int(raw.get("dedup_in_count"), before_count),
            dedup_out_count=_to_int(raw.get("dedup_out_count"), after_count),
            dedup_miss_count=miss_count,
            reasoning=str(raw.get("reasoning") or "").strip()[:600],
        )
    except ValidationError as exc:
        print(f"  [warn] schema error: {exc}", flush=True)
        return None


# ---------------------------------------------------------------------------
# Report + summary
# ---------------------------------------------------------------------------

def build_report(record: Stage1_1_5JudgeRecord, meta: common.RunMeta) -> str:
    n_groups = len(record.judge.near_duplicate_groups)
    out_n = record.dedup_out_count
    miss = record.judge.dedup_miss_count
    sev_counter: Counter = Counter(
        g.severity for g in record.judge.near_duplicate_groups
    )

    lines: List[str] = []
    lines.append("# Stage 1.1.5 Judge Report (dedup-miss finder)")
    lines.append("")
    lines.append(f"- run_id: `{meta.run_id}`")
    lines.append(f"- judge model: `{meta.judge_model}` (provider={meta.provider})")
    if meta.duration_sec:
        lines.append(f"- duration: {meta.duration_sec:.1f}s")
    lines.append("")
    lines.append(f"- dedup_in_count  (Stage 1.1 rows): **{record.dedup_in_count}**")
    lines.append(f"- dedup_out_count (Stage 1.1.5 survivors): **{record.dedup_out_count}**")
    reduction = (
        (record.dedup_in_count - record.dedup_out_count) / record.dedup_in_count
        if record.dedup_in_count
        else 0.0
    )
    lines.append(f"- dedup_reduction_rate: **{reduction:.3f}**")
    lines.append(
        f"- near-duplicate groups found in AFTER-SET: **{n_groups}** "
        f"(severity: {dict(sev_counter)})"
    )
    lines.append(
        f"- dedup_miss_count (extra removals the judge would have made): **{miss}**"
    )
    if out_n:
        lines.append(f"- dedup_miss_rate: **{miss / out_n:.3f}**")
    lines.append("")
    lines.append("## Judge reasoning")
    lines.append(record.judge.reasoning or "(no reasoning)")
    lines.append("")
    if n_groups:
        lines.append("## Missed near-duplicate groups")
        lines.append("")
        lines.append("| severity | size | doc_ids | reason |")
        lines.append("|---|---|---|---|")
        for g in sorted(
            record.judge.near_duplicate_groups,
            key=lambda g: (-len(g.doc_ids), g.severity),
        ):
            lines.append(
                f"| {g.severity} | {len(g.doc_ids)} | "
                f"`{', '.join(g.doc_ids)}` | {common.truncate(g.reason, 200)} |"
            )
        lines.append("")
    return "\n".join(lines)


def build_summary_row(
    record: Stage1_1_5JudgeRecord, meta: common.RunMeta
) -> Stage1_1_5SummaryRow:
    out_n = record.dedup_out_count
    in_n = record.dedup_in_count
    miss = record.judge.dedup_miss_count
    reduction = ((in_n - out_n) / in_n) if in_n else 0.0
    largest = max(
        (len(g.doc_ids) for g in record.judge.near_duplicate_groups),
        default=0,
    )

    fm_counter: Counter = Counter()
    if record.judge.near_duplicate_groups:
        fm_counter["near_duplicate_missed"] = len(record.judge.near_duplicate_groups)
    if reduction < 0.01 and len(record.judge.near_duplicate_groups) > 0:
        fm_counter["low_dedup_reduction"] = 1
    for fm in STAGE_1_1_5_FAILURE_MODES:
        fm_counter.setdefault(fm, 0)

    return Stage1_1_5SummaryRow(
        run_id=meta.run_id,
        judge_model=meta.judge_model,
        provider=meta.provider,
        dedup_in_count=in_n,
        dedup_out_count=out_n,
        dedup_reduction_rate=round(reduction, 3),
        dedup_miss_count=miss,
        dedup_miss_rate=round(miss / out_n, 3) if out_n else 0.0,
        largest_miss_cluster_size=largest,
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
        "--before",
        default=str(root / "stage_1_1" / "synthetic_data.jsonl"),
        help="Stage 1.1 synthetic output (before dedup).",
    )
    parser.add_argument(
        "--after",
        default=str(root / "stage_1_1_5" / "deduped.jsonl"),
        help="Stage 1.1.5 deduped output (after dedup).",
    )
    parser.add_argument(
        "--judge-model",
        default=DEFAULT_JUDGE_MODEL,
        help="Judge LLM id (defaults to GLM-5.1 on Friendli)",
    )
    parser.add_argument(
        "--provider",
        choices=["nim", "friendli", "vllm"],
        default="friendli",
    )
    parser.add_argument(
        "--max-text-chars", type=int, default=220,
        help="Truncate each record's text to this many chars in the prompt.",
    )
    parser.add_argument(
        "--max-records", type=int, default=80,
        help="Hard cap on rows we include in the prompt to avoid context blow-up.",
    )
    parser.add_argument("--max-tokens", type=int, default=4096)
    parser.add_argument("--tag", default="")
    parser.add_argument("--run-id", default="")
    args = parser.parse_args(argv)

    load_env()
    client, _ = get_client(
        provider=args.provider, model_override=args.judge_model
    )
    cfg = client._llm_config  # type: ignore[attr-defined]

    before = list(common.iter_jsonl(Path(args.before)))
    after = list(common.iter_jsonl(Path(args.after)))

    before_shown = before[: args.max_records]
    after_shown = after[: args.max_records]

    run_id = args.run_id or common.make_run_id(args.tag or None)
    out_dir = common.run_dir(STAGE, run_id)
    judge_path = out_dir / "judge.jsonl"
    report_path = out_dir / "report.md"
    meta_path = out_dir / "meta.json"

    print(
        f"[stage_1_1_5 judge] run_id={run_id} {cfg.describe()}\n"
        f"  before={len(before)} after={len(after)} "
        f"(prompt will show {len(before_shown)} / {len(after_shown)})",
        flush=True,
    )

    meta = common.RunMeta(
        stage=STAGE,
        run_id=run_id,
        started_at=dt.datetime.now(dt.timezone.utc).isoformat(),
        judge_model=cfg.model,
        provider=cfg.provider,
        input_path=f"{args.before} | {args.after}",
        n_units_total=len(after),
        n_units_sampled=len(after_shown),
        tag=args.tag,
        git_rev=common.git_rev_short(),
    )

    user_prompt = STAGE_1_1_5_JUDGE_USER_TEMPLATE.format(
        before_count=len(before_shown),
        before_block=_render_set(before_shown, max_text_chars=args.max_text_chars),
        after_count=len(after_shown),
        after_block=_render_set(after_shown, max_text_chars=args.max_text_chars),
    )

    t0 = time.time()

    def _call(mt: int):
        return call_json_judge(
            client,
            cfg.model,
            STAGE_1_1_5_JUDGE_SYSTEM,
            user_prompt,
            temperature=0.1,
            max_tokens=mt,
        )

    parsed, call_meta, tag = common.call_with_retry(
        _call, max_tokens=args.max_tokens, sleep=0.2
    )

    judge = parse_judge_result(parsed, len(before_shown), len(after_shown))
    if judge is None:
        print(
            f"[stage_1_1_5 judge] ERR parse failed ({tag}) "
            f"raw={(call_meta.get('raw_content') or '')[:200]!r}",
            flush=True,
        )
        meta.finished_at = dt.datetime.now(dt.timezone.utc).isoformat()
        meta.duration_sec = round(time.time() - t0, 2)
        meta.n_ok = 0
        meta.n_fail = 1
        common.write_meta(meta_path, meta)
        return 1

    record = Stage1_1_5JudgeRecord(
        dedup_in_count=len(before_shown),
        dedup_out_count=len(after_shown),
        judge=judge,
        judge_model=call_meta["model"],
        judge_tokens=call_meta.get("tokens"),
    )

    with judge_path.open("w", encoding="utf-8") as fh:
        fh.write(record.model_dump_json() + "\n")

    duration = time.time() - t0
    meta.finished_at = dt.datetime.now(dt.timezone.utc).isoformat()
    meta.duration_sec = round(duration, 2)
    meta.n_ok = 1
    meta.n_fail = 0
    common.write_meta(meta_path, meta)

    report = build_report(record, meta)
    report_path.write_text(report, encoding="utf-8")

    row = build_summary_row(record, meta)
    common.append_summary(STAGE, row.model_dump())
    common.copy_latest_report(STAGE, run_id)

    print(
        f"\n[stage_1_1_5 judge] reduction={row.dedup_reduction_rate} "
        f"miss={row.dedup_miss_count} ({row.dedup_miss_rate}) "
        f"groups={len(judge.near_duplicate_groups)} "
        f"largest={row.largest_miss_cluster_size} "
        f"-> {report_path}",
        flush=True,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
