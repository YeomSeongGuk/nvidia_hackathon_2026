"""Stage 2.3 judge: final analyzed-intent + aggregated attribute quality.

For each `AnalyzedIntent` from `pipelines.stage_2_3_aggregate`, the judge
reviews every top-K (key, value, weight) row and decides:

  - concrete: is the value a real product-grade attribute or an adjective?
  - fits_intent: does the value plausibly belong to this intent?
  - duplicate_suspect: does this value duplicate another (린넨 vs linen)?

Plus overall_usefulness (1-5) and evidence_reliable (bool) for the intent.

Output layout mirrors the other stages:
  $STAGE_DATA_ROOT/stage_2_3/eval/runs/<run_id>/judge.jsonl
  $STAGE_DATA_ROOT/stage_2_3/eval/runs/<run_id>/report.md
  $STAGE_DATA_ROOT/stage_2_3/eval/runs/<run_id>/meta.json
  $STAGE_DATA_ROOT/stage_2_3/eval/summary.jsonl (append)
  $STAGE_DATA_ROOT/stage_2_3/eval/latest_report.md
"""
from __future__ import annotations

import argparse
import datetime as dt
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
    STAGE_2_3_JUDGE_SYSTEM,
    STAGE_2_3_JUDGE_USER_TEMPLATE,
)
from pipelines.eval.schemas import (
    STAGE_2_3_FAILURE_MODES,
    MappedAttrJudge,
    Stage2_3JudgeRecord,
    Stage2_3JudgeResult,
    Stage2_3SummaryRow,
)
from pipelines.llm_client import get_client, load_env
from pipelines.schemas import AnalyzedIntent

STAGE = "stage_2_3"
DEFAULT_JUDGE_MODEL = "nvidia/llama-3.1-nemotron-ultra-253b-v1"


# ---------------------------------------------------------------------------
# Parsing
# ---------------------------------------------------------------------------

def _to_int(v: object, lo: int, hi: int) -> int:
    try:
        iv = int(v)
    except (TypeError, ValueError):
        return lo
    return max(lo, min(hi, iv))


def _to_float(v: object) -> float:
    try:
        return float(v)
    except (TypeError, ValueError):
        return 0.0


def parse_judge_result(
    raw: Optional[Dict], input_attrs: List[Dict[str, Any]]
) -> Optional[Stage2_3JudgeResult]:
    if not raw:
        return None

    attrs_out: List[MappedAttrJudge] = []
    raw_attrs = raw.get("attributes") or []
    if isinstance(raw_attrs, list):
        # Align by index with input: if the LLM lost an item, we fall back to
        # the input row with concrete=False, fits_intent=False so it shows up
        # as a worst-case rather than silently vanishing.
        for i, in_attr in enumerate(input_attrs):
            j = raw_attrs[i] if i < len(raw_attrs) and isinstance(raw_attrs[i], dict) else {}
            dup = j.get("duplicate_suspect")
            if dup is None or (isinstance(dup, str) and dup.strip() in ("", "null", "None")):
                dup_clean = None
            else:
                dup_clean = str(dup).strip()
            try:
                attrs_out.append(
                    MappedAttrJudge(
                        key=str(j.get("key") or in_attr.get("attribute_key") or ""),
                        value=str(j.get("value") or in_attr.get("attribute_value") or ""),
                        weight=_to_float(
                            j.get("weight")
                            if j.get("weight") is not None
                            else in_attr.get("weight")
                        ),
                        concrete=bool(j.get("concrete", False)),
                        fits_intent=bool(j.get("fits_intent", False)),
                        duplicate_suspect=dup_clean,
                    )
                )
            except ValidationError:
                continue

    try:
        return Stage2_3JudgeResult(
            overall_usefulness=_to_int(raw.get("overall_usefulness"), 1, 5),
            attributes=attrs_out,
            evidence_reliable=bool(raw.get("evidence_reliable", True)),
            failure_modes=common.safe_string_list(raw.get("failure_modes")),
            reasoning=str(raw.get("reasoning") or "").strip()[:500],
        )
    except ValidationError as exc:
        print(f"  [warn] schema error: {exc}", flush=True)
        return None


def build_judge_user(intent: AnalyzedIntent) -> str:
    if intent.mapped_attributes:
        attr_lines = []
        for a in intent.mapped_attributes:
            attr_lines.append(
                f'    - {{"key": "{a.attribute_key}", '
                f'"value": "{a.attribute_value}", "weight": {a.weight}}}'
            )
        attrs_block = "\n".join(attr_lines)
    else:
        attrs_block = "    (no attributes)"
    return STAGE_2_3_JUDGE_USER_TEMPLATE.format(
        intent_keyword=intent.intent_keyword,
        evidence=intent.data_lineage.total_evidence_count,
        attributes=attrs_block,
    )


# ---------------------------------------------------------------------------
# Report
# ---------------------------------------------------------------------------

def _flat_attr_stats(records: List[Stage2_3JudgeRecord]) -> Dict[str, Any]:
    total = 0
    concrete = 0
    fits = 0
    duplicates = 0
    for r in records:
        for a in r.judge.attributes:
            total += 1
            if a.concrete:
                concrete += 1
            if a.fits_intent:
                fits += 1
            if a.duplicate_suspect:
                duplicates += 1
    return {
        "total": total, "concrete": concrete, "fits": fits, "duplicates": duplicates
    }


def build_report(records: List[Stage2_3JudgeRecord], meta: common.RunMeta) -> str:
    n = len(records)
    if n == 0:
        return "# Stage 2.3 Judge Report\n\n(no records)\n"

    usefulness = [r.judge.overall_usefulness for r in records]
    reliable = sum(1 for r in records if r.judge.evidence_reliable)

    stats = _flat_attr_stats(records)
    concrete_rate = stats["concrete"] / max(stats["total"], 1)
    fits_rate = stats["fits"] / max(stats["total"], 1)

    fm_counter: Counter = Counter()
    for r in records:
        for fm in r.judge.failure_modes:
            fm_counter[fm] += 1
    for fm in STAGE_2_3_FAILURE_MODES:
        fm_counter.setdefault(fm, 0)

    low_use = sorted(records, key=lambda r: (r.judge.overall_usefulness, r.intent_keyword))[:5]
    low_reliable = [r for r in records if not r.judge.evidence_reliable][:5]
    dup_intents = [
        r for r in records if any(a.duplicate_suspect for a in r.judge.attributes)
    ][:5]
    subj_intents = [
        r for r in records if any(not a.concrete for a in r.judge.attributes)
    ][:5]
    wrong_attr = [
        r for r in records
        if any(not a.fits_intent for a in r.judge.attributes)
    ][:5]

    lines: List[str] = []
    lines.append("# Stage 2.3 Judge Report")
    lines.append("")
    lines.append(f"- run_id: `{meta.run_id}`")
    lines.append(f"- analyzed intents: **{n}**")
    lines.append(f"- judge model: `{meta.judge_model}` (provider={meta.provider})")
    if meta.duration_sec:
        lines.append(f"- duration: {meta.duration_sec}s")
    lines.append("")

    lines.append("## Overall quality")
    lines.append(f"- avg overall_usefulness: **{common.safe_mean(usefulness)}** / 5")
    lines.append(f"- evidence_reliable: **{common.pct(reliable, n)}**")
    lines.append(f"- attribute concrete rate: **{stats['concrete']}/{stats['total']} "
                 f"({concrete_rate * 100:.0f}%)**")
    lines.append(f"- attribute fits_intent rate: **{stats['fits']}/{stats['total']} "
                 f"({fits_rate * 100:.0f}%)**")
    lines.append(f"- duplicate-value flags: **{stats['duplicates']}**")
    lines.append("")

    lines.append("## Failure-mode histogram")
    lines.append("")
    lines.append("| failure_mode | count |")
    lines.append("|---|---|")
    for fm, cnt in sorted(fm_counter.items(), key=lambda x: (-x[1], x[0])):
        lines.append(f"| `{fm}` | {cnt} |")
    lines.append("")

    def _render(rows: List[Stage2_3JudgeRecord], title: str) -> None:
        lines.append(f"### {title}")
        if not rows:
            lines.append("(none)")
            lines.append("")
            return
        for r in rows:
            lines.append(
                f"- **{r.intent_keyword}** (evidence={r.total_evidence_count}) "
                f"usefulness={r.judge.overall_usefulness} "
                f"reliable={r.judge.evidence_reliable}"
            )
            for a in r.judge.attributes:
                flags = []
                if not a.concrete:
                    flags.append("subjective")
                if not a.fits_intent:
                    flags.append("wrong_for_intent")
                if a.duplicate_suspect:
                    flags.append(f"dup={a.duplicate_suspect}")
                flag_s = f" [{', '.join(flags)}]" if flags else ""
                lines.append(
                    f"  - {a.key}={a.value!r} w={a.weight:.3f}{flag_s}"
                )
            lines.append(f"  - fm: `{r.judge.failure_modes}`")
            lines.append(f"  - judge: {common.truncate(r.judge.reasoning, 160)}")
        lines.append("")

    lines.append("## Worst cases")
    lines.append("")
    _render(low_use, "Lowest overall_usefulness (top 5)")
    _render(low_reliable, "evidence_reliable=false (top 5)")
    _render(subj_intents, "Has subjective attribute value (top 5)")
    _render(wrong_attr, "Attribute doesn't fit intent (top 5)")
    _render(dup_intents, "Has duplicate_suspect attribute (top 5)")

    return "\n".join(line for line in lines if line != "")


def build_summary_row(
    records: List[Stage2_3JudgeRecord], meta: common.RunMeta
) -> Stage2_3SummaryRow:
    n = len(records)
    usefulness = [r.judge.overall_usefulness for r in records]
    reliable = sum(1 for r in records if r.judge.evidence_reliable)
    stats = _flat_attr_stats(records)

    fm_counter: Counter = Counter()
    for r in records:
        for fm in r.judge.failure_modes:
            fm_counter[fm] += 1
    for fm in STAGE_2_3_FAILURE_MODES:
        fm_counter.setdefault(fm, 0)

    return Stage2_3SummaryRow(
        run_id=meta.run_id,
        judge_model=meta.judge_model,
        provider=meta.provider,
        n_intents=n,
        avg_overall_usefulness=common.safe_mean(usefulness),
        attr_concrete_rate=round(stats["concrete"] / max(stats["total"], 1), 2),
        attr_fits_intent_rate=round(stats["fits"] / max(stats["total"], 1), 2),
        duplicate_value_count=stats["duplicates"],
        evidence_reliable_rate=round(reliable / n, 2) if n else 0.0,
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
        default=str(root / "stage_2_3" / "analyzed_intents.jsonl"),
    )
    parser.add_argument("--judge-model", default=DEFAULT_JUDGE_MODEL)
    parser.add_argument(
        "--provider", choices=["nim", "friendli", "vllm"], default="nim"
    )
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--sleep", type=float, default=0.2)
    parser.add_argument("--max-tokens", type=int, default=1536)
    parser.add_argument(
        "--skip-general", action="store_true",
        help="skip the '일반' intent (always low quality by design)",
    )
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

    intents: List[AnalyzedIntent] = [
        AnalyzedIntent.model_validate(obj) for obj in common.iter_jsonl(Path(args.input))
    ]
    if args.skip_general:
        intents = [i for i in intents if i.intent_keyword != "일반"]

    n_total = len(intents)
    subset = common.cap(intents, args.limit)

    print(
        f"[stage_2_3 judge] run_id={run_id} {cfg.describe()}\n"
        f"  intents_total={n_total} sampled={len(subset)}"
        f"{' (skipped 일반)' if args.skip_general else ''}\n"
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
        extra={"skip_general": args.skip_general},
    )

    ok = fail = 0
    t0 = time.time()
    records: List[Stage2_3JudgeRecord] = []

    with judge_path.open("w", encoding="utf-8") as out_fh:
        for i, intent in enumerate(subset):
            user_prompt = build_judge_user(intent)
            input_attrs = [a.model_dump() for a in intent.mapped_attributes]

            def _call(mt: int):
                return call_json_judge(
                    client,
                    cfg.model,
                    STAGE_2_3_JUDGE_SYSTEM,
                    user_prompt,
                    temperature=0.1,
                    max_tokens=mt,
                )

            parsed, call_meta, tag = common.call_with_retry(
                _call, max_tokens=args.max_tokens, sleep=args.sleep
            )
            judge = parse_judge_result(parsed, input_attrs)
            if judge is None:
                fail += 1
                print(
                    f"[{i + 1:04d}] ERR {intent.intent_keyword}: {tag} "
                    f"tokens={call_meta.get('tokens')} "
                    f"raw={(call_meta.get('raw_content') or '')[:120]!r}",
                    flush=True,
                )
                time.sleep(args.sleep)
                continue

            record = Stage2_3JudgeRecord(
                intent_keyword=intent.intent_keyword,
                total_evidence_count=intent.data_lineage.total_evidence_count,
                mapped_attributes=input_attrs,
                judge=judge,
                judge_model=call_meta["model"],
                judge_tokens=call_meta.get("tokens"),
            )
            out_fh.write(record.model_dump_json() + "\n")
            out_fh.flush()
            records.append(record)
            ok += 1

            n_subj = sum(1 for a in judge.attributes if not a.concrete)
            n_wrong = sum(1 for a in judge.attributes if not a.fits_intent)
            n_dup = sum(1 for a in judge.attributes if a.duplicate_suspect)
            print(
                f"[{i + 1:04d}] OK  {intent.intent_keyword} "
                f"use={judge.overall_usefulness} "
                f"reliable={judge.evidence_reliable} "
                f"subj={n_subj} wrong={n_wrong} dup={n_dup} "
                f"fm={judge.failure_modes or '[]'}",
                flush=True,
            )
            time.sleep(args.sleep)

    meta.finished_at = dt.datetime.now(dt.timezone.utc).isoformat()
    meta.duration_sec = round(time.time() - t0, 1)
    meta.n_ok = ok
    meta.n_fail = fail
    common.write_meta(meta_path, meta)

    report_md = build_report(records, meta)
    report_path.write_text(report_md, encoding="utf-8")

    summary_row = build_summary_row(records, meta)
    common.append_summary(STAGE, summary_row.model_dump())
    common.copy_latest_report(STAGE, run_id)

    print(
        f"\n[done] ok={ok} fail={fail} time={meta.duration_sec}s\n"
        f"  judge.jsonl: {judge_path}\n"
        f"  report.md  : {report_path}\n"
        f"  meta.json  : {meta_path}\n"
        f"  summary row appended at eval/summary.jsonl",
        flush=True,
    )
    return 0 if fail == 0 else 2


if __name__ == "__main__":
    sys.exit(main())
