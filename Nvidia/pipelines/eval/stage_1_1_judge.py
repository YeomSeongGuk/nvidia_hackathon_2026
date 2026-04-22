"""Stage 1.1 judge: synthetic fashion review quality.

Evaluates the synthetic output of Stage 1.1 (Data Designer + LLM) — i.e.
`~/stage1_work/data/stage_1_1/synthetic_data.jsonl`. For each record we
verify the generator actually followed the spec:

  - title within 15-30 chars, format `브랜드 + 상품종류 + 특징`
  - no reasoning-leak in product_title (the Nemotron-Super bug)
  - raw_text 80-200 chars, natural Korean
  - persona reflected in the review
  - TPO signal present
  - product_attributes grounded in raw_text
  - sentiment vs star rating consistency

Output:
  $STAGE_DATA_ROOT/stage_1_1/eval/runs/<run_id>/
      judge.jsonl       per-record Stage1_1JudgeRecord
      report.md         summary + worst-K
      meta.json         RunMeta
  $STAGE_DATA_ROOT/stage_1_1/eval/summary.jsonl    (append)
  $STAGE_DATA_ROOT/stage_1_1/eval/latest_report.md (copy)

Usage:
  # smoke
  LLM_VERIFY_SSL=0 python -m pipelines.eval.stage_1_1_judge --limit 5

  # full run on coupang via Friendli GLM-5.1 judge
  python -m pipelines.eval.stage_1_1_judge \\
      --input /home/nvidia/stage1_work/data/stage_1_1/synthetic_data.jsonl \\
      --provider friendli --judge-model zai-org/GLM-5.1 --sample 200

  # against local vLLM Nemotron-Super
  LLM_EXTRA_BODY='{"chat_template_kwargs":{"enable_thinking":false}}' \\
      python -m pipelines.eval.stage_1_1_judge \\
      --provider vllm --judge-model nemotron --sample 100
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
    STAGE_1_1_JUDGE_SYSTEM,
    STAGE_1_1_JUDGE_USER_TEMPLATE,
)
from pipelines.eval.schemas import (
    STAGE_1_1_FAILURE_MODES,
    AttrGrounded,
    Stage1_1JudgeRecord,
    Stage1_1JudgeResult,
    Stage1_1SummaryRow,
)
from pipelines.llm_client import get_client, load_env


STAGE = "stage_1_1"
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


def _to_bool(v: object, default: bool = False) -> bool:
    if isinstance(v, bool):
        return v
    if isinstance(v, str):
        s = v.strip().lower()
        if s in ("true", "yes", "1"):
            return True
        if s in ("false", "no", "0"):
            return False
    return default


def _coerce_attrs_grounded(raw: object) -> List[AttrGrounded]:
    out: List[AttrGrounded] = []
    if not isinstance(raw, list):
        return out
    for item in raw:
        if not isinstance(item, dict):
            continue
        try:
            out.append(
                AttrGrounded(
                    key=str(item.get("key") or ""),
                    value=str(item.get("value") or ""),
                    mentioned_in_text=_to_bool(item.get("mentioned_in_text")),
                    plausible_for_product=_to_bool(
                        item.get("plausible_for_product"), default=True
                    ),
                )
            )
        except ValidationError:
            continue
    return out


def parse_judge_result(raw: Optional[Dict]) -> Optional[Stage1_1JudgeResult]:
    if not raw:
        return None
    try:
        return Stage1_1JudgeResult(
            is_fashion=_to_bool(raw.get("is_fashion")),
            title_within_spec=_to_bool(raw.get("title_within_spec")),
            title_format_ok=_to_bool(raw.get("title_format_ok")),
            title_has_reasoning_leak=_to_bool(
                raw.get("title_has_reasoning_leak")
            ),
            raw_text_within_spec=_to_bool(raw.get("raw_text_within_spec")),
            raw_text_naturalness=_to_int(raw.get("raw_text_naturalness"), 1, 5),
            persona_reflection=_to_int(raw.get("persona_reflection"), 1, 5),
            has_tpo_signal=_to_bool(raw.get("has_tpo_signal")),
            attributes_grounded=_coerce_attrs_grounded(
                raw.get("attributes_grounded")
            ),
            rating_sentiment_consistent=_to_bool(
                raw.get("rating_sentiment_consistent"), default=True
            ),
            failure_modes=common.safe_string_list(raw.get("failure_modes")),
            reasoning=str(raw.get("reasoning") or "").strip()[:600],
        )
    except ValidationError as exc:
        print(f"  [warn] schema error: {exc}", flush=True)
        return None


# ---------------------------------------------------------------------------
# Prompt
# ---------------------------------------------------------------------------

def build_judge_user(rec: Dict[str, Any]) -> str:
    p = rec.get("persona_info") or {}
    attrs = rec.get("product_attributes") or {}
    return STAGE_1_1_JUDGE_USER_TEMPLATE.format(
        age=p.get("age"),
        sex=p.get("sex"),
        occupation=p.get("occupation"),
        province=p.get("province"),
        district=p.get("district"),
        character=p.get("character"),
        hobbies=p.get("hobbies"),
        product_title=rec.get("product_title", ""),
        color=attrs.get("color"),
        style=attrs.get("style"),
        size=attrs.get("size"),
        raw_text=rec.get("raw_text", ""),
        rating=(rec.get("metadata") or {}).get("rating"),
    )


# ---------------------------------------------------------------------------
# Report + summary
# ---------------------------------------------------------------------------

def build_report(records: List[Stage1_1JudgeRecord], meta: common.RunMeta) -> str:
    if not records:
        return "# Stage 1.1 Judge Report\n\n(no records)\n"

    n = len(records)
    fashion = sum(1 for r in records if r.judge.is_fashion)
    title_spec = sum(1 for r in records if r.judge.title_within_spec)
    title_fmt = sum(1 for r in records if r.judge.title_format_ok)
    title_leak = sum(1 for r in records if r.judge.title_has_reasoning_leak)
    text_spec = sum(1 for r in records if r.judge.raw_text_within_spec)
    has_tpo = sum(1 for r in records if r.judge.has_tpo_signal)
    rs_consistent = sum(1 for r in records if r.judge.rating_sentiment_consistent)

    naturalness = [r.judge.raw_text_naturalness for r in records]
    persona = [r.judge.persona_reflection for r in records]

    # Attribute grounding: fraction of (record, attr) pairs where mentioned_in_text
    total_attr_checks = 0
    total_grounded = 0
    total_plausible = 0
    for r in records:
        for ag in r.judge.attributes_grounded:
            total_attr_checks += 1
            if ag.mentioned_in_text:
                total_grounded += 1
            if ag.plausible_for_product:
                total_plausible += 1

    # Failure-mode histogram
    fm_counter: Counter = Counter()
    for r in records:
        for fm in r.judge.failure_modes:
            fm_counter[fm] += 1
    for fm in STAGE_1_1_FAILURE_MODES:
        fm_counter.setdefault(fm, 0)

    # Worst cases
    leak_cases = [r for r in records if r.judge.title_has_reasoning_leak][:5]
    non_fashion = [r for r in records if not r.judge.is_fashion][:5]
    low_persona = sorted(records, key=lambda r: r.judge.persona_reflection)[:5]
    low_nat = sorted(records, key=lambda r: r.judge.raw_text_naturalness)[:5]
    sentiment_mismatch = [r for r in records if not r.judge.rating_sentiment_consistent][:5]

    lines: List[str] = []
    lines.append("# Stage 1.1 Judge Report")
    lines.append("")
    lines.append(f"- run_id: `{meta.run_id}`")
    lines.append(f"- records evaluated: **{n}**")
    lines.append(f"- judge model: `{meta.judge_model}` (provider={meta.provider})")
    if meta.duration_sec:
        lines.append(f"- duration: {meta.duration_sec:.1f}s")
    lines.append("")

    lines.append("## Spec compliance")
    lines.append(f"- is_fashion:               **{common.pct(fashion, n)}**")
    lines.append(f"- title_within_spec:        **{common.pct(title_spec, n)}**")
    lines.append(f"- title_format_ok:          **{common.pct(title_fmt, n)}**")
    lines.append(f"- title_has_reasoning_leak: **{common.pct(title_leak, n)}**  ← key bug metric")
    lines.append(f"- raw_text_within_spec:     **{common.pct(text_spec, n)}**")
    lines.append(f"- has_tpo_signal:           **{common.pct(has_tpo, n)}**")
    lines.append(
        f"- rating_sentiment_consistent: **{common.pct(rs_consistent, n)}**"
    )
    lines.append("")

    lines.append("## Quality scores (1-5)")
    lines.append(
        f"- avg raw_text naturalness : **{common.safe_mean(naturalness)}**"
    )
    lines.append(
        f"- avg persona_reflection   : **{common.safe_mean(persona)}**"
    )
    lines.append("")

    lines.append("## Attribute grounding")
    lines.append(
        f"- mentioned_in_text rate: **{common.pct(total_grounded, total_attr_checks)}**"
    )
    lines.append(
        f"- plausible_for_product : **{common.pct(total_plausible, total_attr_checks)}**"
    )
    lines.append("")

    lines.append("## Failure-mode histogram")
    lines.append("")
    lines.append("| failure_mode | count |")
    lines.append("|---|---|")
    for fm, cnt in sorted(fm_counter.items(), key=lambda x: (-x[1], x[0])):
        lines.append(f"| `{fm}` | {cnt} |")
    lines.append("")

    def _render(rows: List[Stage1_1JudgeRecord], title: str) -> None:
        lines.append(f"### {title}")
        if not rows:
            lines.append("(none)")
            lines.append("")
            return
        for r in rows:
            lines.append(
                f"- **{r.doc_id}** rating={r.rating} "
                f"natural={r.judge.raw_text_naturalness} "
                f"persona={r.judge.persona_reflection}"
            )
            lines.append(f"  - title: `{common.truncate(r.product_title, 80)}`")
            lines.append(f"  - text : {common.truncate(r.raw_text, 160)}")
            lines.append(f"  - fm   : `{r.judge.failure_modes}`")
            lines.append(f"  - judge: {common.truncate(r.judge.reasoning, 180)}")
        lines.append("")

    lines.append("## Worst cases")
    lines.append("")
    _render(leak_cases,       "Reasoning-leak in product_title (top 5)")
    _render(non_fashion,      "is_fashion = false (top 5)")
    _render(low_persona,      "Lowest persona_reflection (top 5)")
    _render(low_nat,          "Lowest raw_text naturalness (top 5)")
    _render(sentiment_mismatch, "Rating vs sentiment mismatch (top 5)")

    return "\n".join(line for line in lines if line != "")


def build_summary_row(
    records: List[Stage1_1JudgeRecord], meta: common.RunMeta
) -> Stage1_1SummaryRow:
    n = len(records)
    if n == 0:
        return Stage1_1SummaryRow(
            run_id=meta.run_id,
            judge_model=meta.judge_model,
            provider=meta.provider,
            n_evaluated=0,
            fashion_rate=0.0,
            title_within_spec_rate=0.0,
            title_format_ok_rate=0.0,
            title_reasoning_leak_rate=0.0,
            raw_text_within_spec_rate=0.0,
            avg_raw_text_naturalness=None,
            avg_persona_reflection=None,
            has_tpo_rate=0.0,
            attr_grounded_rate=None,
            rating_sentiment_consistent_rate=0.0,
            failure_modes={},
            duration_sec=meta.duration_sec or 0.0,
            tag=meta.tag,
        )

    fashion = sum(1 for r in records if r.judge.is_fashion)
    title_spec = sum(1 for r in records if r.judge.title_within_spec)
    title_fmt = sum(1 for r in records if r.judge.title_format_ok)
    title_leak = sum(1 for r in records if r.judge.title_has_reasoning_leak)
    text_spec = sum(1 for r in records if r.judge.raw_text_within_spec)
    has_tpo = sum(1 for r in records if r.judge.has_tpo_signal)
    rs_consistent = sum(1 for r in records if r.judge.rating_sentiment_consistent)

    total_attr_checks = 0
    grounded = 0
    for r in records:
        for ag in r.judge.attributes_grounded:
            total_attr_checks += 1
            if ag.mentioned_in_text:
                grounded += 1

    fm_counter: Counter = Counter()
    for r in records:
        for fm in r.judge.failure_modes:
            fm_counter[fm] += 1
    for fm in STAGE_1_1_FAILURE_MODES:
        fm_counter.setdefault(fm, 0)

    return Stage1_1SummaryRow(
        run_id=meta.run_id,
        judge_model=meta.judge_model,
        provider=meta.provider,
        n_evaluated=n,
        fashion_rate=round(fashion / n, 2),
        title_within_spec_rate=round(title_spec / n, 2),
        title_format_ok_rate=round(title_fmt / n, 2),
        title_reasoning_leak_rate=round(title_leak / n, 2),
        raw_text_within_spec_rate=round(text_spec / n, 2),
        avg_raw_text_naturalness=common.safe_mean(
            [r.judge.raw_text_naturalness for r in records]
        ),
        avg_persona_reflection=common.safe_mean(
            [r.judge.persona_reflection for r in records]
        ),
        has_tpo_rate=round(has_tpo / n, 2),
        attr_grounded_rate=(
            round(grounded / total_attr_checks, 2)
            if total_attr_checks
            else None
        ),
        rating_sentiment_consistent_rate=round(rs_consistent / n, 2),
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
        default=str(root / "stage_1_1" / "synthetic_data.jsonl"),
        help="Stage 1.1 synthetic_data.jsonl (file or directory).",
    )
    parser.add_argument(
        "--judge-model",
        default=DEFAULT_JUDGE_MODEL,
        help="judge LLM model id (must be on the selected provider)",
    )
    parser.add_argument(
        "--provider",
        choices=["nim", "friendli", "vllm"],
        default=None,
        help="LLM provider for the judge (default = $LLM_PROVIDER).",
    )
    parser.add_argument("--limit", type=int, default=0, help="0 = all")
    parser.add_argument(
        "--sample", type=int, default=0,
        help="random-sample N records (0 = use --limit or all).",
    )
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--sleep", type=float, default=0.15)
    parser.add_argument("--max-tokens", type=int, default=1536)
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

    all_records = list(common.iter_jsonl(Path(args.input)))
    n_total = len(all_records)
    if args.sample > 0:
        subset = common.sample_random(all_records, args.sample, seed=args.seed)
    else:
        subset = common.cap(all_records, args.limit)

    print(
        f"[stage_1_1 judge] run_id={run_id} {cfg.describe()}\n"
        f"  input={args.input} total={n_total} sampled={len(subset)}\n"
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
    )

    ok = fail = 0
    t0 = time.time()
    records: List[Stage1_1JudgeRecord] = []

    with judge_path.open("w", encoding="utf-8") as out_fh:
        for i, rec in enumerate(subset):
            doc_id = rec.get("doc_id") or f"rec_{i:06d}"
            user_prompt = build_judge_user(rec)

            def _call(mt: int):
                return call_json_judge(
                    client,
                    cfg.model,
                    STAGE_1_1_JUDGE_SYSTEM,
                    user_prompt,
                    temperature=0.1,
                    max_tokens=mt,
                )

            parsed, call_meta, tag = common.call_with_retry(
                _call, max_tokens=args.max_tokens, sleep=args.sleep
            )

            judge = parse_judge_result(parsed)
            if judge is None:
                fail += 1
                print(
                    f"[{i + 1:04d}] ERR {doc_id}: {tag} "
                    f"raw={(call_meta.get('raw_content') or '')[:120]!r}",
                    flush=True,
                )
                time.sleep(args.sleep)
                continue

            rating = (rec.get("metadata") or {}).get("rating")
            try:
                rating = int(rating) if rating is not None else None
            except (TypeError, ValueError):
                rating = None

            record = Stage1_1JudgeRecord(
                doc_id=doc_id,
                product_title=rec.get("product_title", ""),
                product_attributes=rec.get("product_attributes") or {},
                raw_text=rec.get("raw_text", ""),
                persona_info=rec.get("persona_info") or {},
                rating=rating,
                judge=judge,
                judge_model=call_meta["model"],
                judge_tokens=call_meta.get("tokens"),
            )
            out_fh.write(record.model_dump_json() + "\n")
            out_fh.flush()
            records.append(record)
            ok += 1
            print(
                f"[{i + 1:04d}] OK  {doc_id} "
                f"fash={judge.is_fashion} "
                f"tspec={judge.title_within_spec} "
                f"tleak={judge.title_has_reasoning_leak} "
                f"nat={judge.raw_text_naturalness} "
                f"persona={judge.persona_reflection} "
                f"fm={judge.failure_modes or '[]'}",
                flush=True,
            )
            time.sleep(args.sleep)

    duration = time.time() - t0
    meta.finished_at = dt.datetime.now(dt.timezone.utc).isoformat()
    meta.duration_sec = round(duration, 2)
    meta.n_ok = ok
    meta.n_fail = fail
    common.write_meta(meta_path, meta)

    report = build_report(records, meta)
    report_path.write_text(report, encoding="utf-8")

    row = build_summary_row(records, meta)
    common.append_summary(STAGE, row.model_dump())
    common.copy_latest_report(STAGE, run_id)

    print(
        f"\n[stage_1_1 judge] ok={ok} fail={fail} "
        f"duration={duration:.1f}s -> {report_path}",
        flush=True,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
