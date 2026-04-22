"""Stage 2.4 judge: natural-query expansion quality.

Evaluates `ExpandedIntent` records produced by
`pipelines.stage_2_4_expand`. For each canonical the judge verifies its
set of natural_queries along four axes:

  - per-query checks (natural_korean, repeats_canonical, fits_intent,
    language_ok, garbled, style)
  - query_diversity        (1-5)
  - attribute_weaving       (1-5)  -- are mapped_attributes woven naturally?
  - canonical_coverage      (1-5)
  - overall_usefulness      (1-5)
  - failure_modes

Output layout mirrors the other stages:
  $STAGE_DATA_ROOT/stage_2_4/eval/runs/<run_id>/judge.jsonl
  $STAGE_DATA_ROOT/stage_2_4/eval/runs/<run_id>/report.md
  $STAGE_DATA_ROOT/stage_2_4/eval/runs/<run_id>/meta.json
  $STAGE_DATA_ROOT/stage_2_4/eval/summary.jsonl (append)
  $STAGE_DATA_ROOT/stage_2_4/eval/latest_report.md

Usage:
  LLM_VERIFY_SSL=0 python -m pipelines.eval.stage_2_4_judge

  # Friendli GLM-5.1 judge (multilingual, strong on Korean)
  python -m pipelines.eval.stage_2_4_judge \\
      --provider friendli --judge-model zai-org/GLM-5.1

  # Local vLLM Nemotron-Super
  LLM_EXTRA_BODY='{"chat_template_kwargs":{"enable_thinking":false}}' \\
      python -m pipelines.eval.stage_2_4_judge \\
      --provider vllm --judge-model nemotron
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
    STAGE_2_4_JUDGE_SYSTEM,
    STAGE_2_4_JUDGE_USER_TEMPLATE,
)
from pipelines.eval.schemas import (
    STAGE_2_4_FAILURE_MODES,
    QueryJudge,
    Stage2_4JudgeRecord,
    Stage2_4JudgeResult,
    Stage2_4SummaryRow,
)
from pipelines.llm_client import get_client, load_env
from pipelines.schemas import ExpandedIntent

STAGE = "stage_2_4"
DEFAULT_JUDGE_MODEL = "nvidia/llama-3.1-nemotron-ultra-253b-v1"

_VALID_STYLES = ("question", "command", "descriptive", "mixed", "unknown")


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


def _coerce_queries(
    raw: object, input_queries: List[str]
) -> List[QueryJudge]:
    """Best-effort align LLM `queries[]` with the input list by index.

    If the LLM returned fewer / more items we fall back to per-input defaults
    so counts stay consistent across records.
    """
    items: List[Dict[str, Any]] = raw if isinstance(raw, list) else []
    out: List[QueryJudge] = []
    for i, q_str in enumerate(input_queries):
        row = items[i] if i < len(items) and isinstance(items[i], dict) else {}
        style = str(row.get("style") or "unknown").lower()
        if style not in _VALID_STYLES:
            style = "unknown"
        try:
            out.append(
                QueryJudge(
                    query=str(row.get("query") or q_str),
                    natural_korean=_to_bool(
                        row.get("natural_korean"), default=False
                    ),
                    repeats_canonical=_to_bool(
                        row.get("repeats_canonical"), default=False
                    ),
                    fits_intent=_to_bool(
                        row.get("fits_intent"), default=True
                    ),
                    language_ok=_to_bool(
                        row.get("language_ok"), default=True
                    ),
                    garbled=_to_bool(row.get("garbled"), default=False),
                    style=style,
                )
            )
        except ValidationError:
            out.append(
                QueryJudge(
                    query=q_str,
                    natural_korean=False,
                    repeats_canonical=False,
                    fits_intent=True,
                    language_ok=True,
                    garbled=False,
                    style="unknown",
                )
            )
    return out


def parse_judge_result(
    raw: Optional[Dict], input_queries: List[str]
) -> Optional[Stage2_4JudgeResult]:
    if not raw:
        return None
    try:
        return Stage2_4JudgeResult(
            queries=_coerce_queries(raw.get("queries"), input_queries),
            query_diversity=_to_int(raw.get("query_diversity"), 1, 5),
            attribute_weaving=_to_int(raw.get("attribute_weaving"), 1, 5),
            canonical_coverage=_to_int(raw.get("canonical_coverage"), 1, 5),
            overall_usefulness=_to_int(raw.get("overall_usefulness"), 1, 5),
            failure_modes=common.safe_string_list(raw.get("failure_modes")),
            reasoning=str(raw.get("reasoning") or "").strip()[:600],
        )
    except ValidationError as exc:
        print(f"  [warn] schema error: {exc}", flush=True)
        return None


# ---------------------------------------------------------------------------
# Prompt
# ---------------------------------------------------------------------------

def _fmt_attrs(mapped_attributes: List[Dict[str, Any]]) -> str:
    if not mapped_attributes:
        return "  (none)"
    lines = []
    for a in mapped_attributes[:6]:
        lines.append(
            f"  - {a.get('attribute_key')}: {a.get('attribute_value')} "
            f"(weight={a.get('weight')})"
        )
    return "\n".join(lines)


def _fmt_queries(queries: List[str]) -> str:
    if not queries:
        return "  (no queries)"
    return "\n".join(f"  {i + 1}. {q}" for i, q in enumerate(queries))


def build_judge_user(intent: ExpandedIntent) -> str:
    attrs_raw = [a.model_dump() for a in intent.mapped_attributes]
    return STAGE_2_4_JUDGE_USER_TEMPLATE.format(
        intent_keyword=intent.intent_keyword,
        evidence=intent.data_lineage.total_evidence_count,
        attributes=_fmt_attrs(attrs_raw),
        queries=_fmt_queries(intent.natural_queries),
    )


# ---------------------------------------------------------------------------
# Report + summary
# ---------------------------------------------------------------------------

def build_report(records: List[Stage2_4JudgeRecord], meta: common.RunMeta) -> str:
    if not records:
        return "# Stage 2.4 Judge Report\n\n(no records)\n"

    n_intents = len(records)
    n_queries = sum(len(r.natural_queries) for r in records)
    div = [r.judge.query_diversity for r in records]
    weave = [r.judge.attribute_weaving for r in records]
    cov = [r.judge.canonical_coverage for r in records]
    use = [r.judge.overall_usefulness for r in records]

    q_total = 0
    q_natural = q_fits = q_lang = 0
    canonical_repeat = 0
    garbled = 0
    for r in records:
        for qj in r.judge.queries:
            q_total += 1
            if qj.natural_korean:
                q_natural += 1
            if qj.fits_intent:
                q_fits += 1
            if qj.language_ok:
                q_lang += 1
            if qj.repeats_canonical:
                canonical_repeat += 1
            if qj.garbled:
                garbled += 1

    fm_counter: Counter = Counter()
    for r in records:
        for fm in r.judge.failure_modes:
            fm_counter[fm] += 1
    for fm in STAGE_2_4_FAILURE_MODES:
        fm_counter.setdefault(fm, 0)

    worst_use = sorted(records, key=lambda r: r.judge.overall_usefulness)[:5]
    worst_div = sorted(records, key=lambda r: r.judge.query_diversity)[:5]
    repeat_heavy = [
        r for r in records
        if sum(1 for qj in r.judge.queries if qj.repeats_canonical) >= 2
    ][:5]
    garbled_heavy = [
        r for r in records
        if any(qj.garbled for qj in r.judge.queries)
    ][:5]

    lines: List[str] = []
    lines.append("# Stage 2.4 Judge Report")
    lines.append("")
    lines.append(f"- run_id: `{meta.run_id}`")
    lines.append(f"- canonical intents: **{n_intents}**  natural queries: **{n_queries}**")
    lines.append(f"- judge model: `{meta.judge_model}` (provider={meta.provider})")
    if meta.duration_sec:
        lines.append(f"- duration: {meta.duration_sec:.1f}s")
    lines.append("")

    lines.append("## Expansion quality")
    lines.append(f"- avg query_diversity    : **{common.safe_mean(div)}**")
    lines.append(f"- avg attribute_weaving  : **{common.safe_mean(weave)}**")
    lines.append(f"- avg canonical_coverage : **{common.safe_mean(cov)}**")
    lines.append(f"- avg overall_usefulness : **{common.safe_mean(use)}**")
    lines.append("")

    lines.append("## Per-query checks")
    lines.append(f"- natural Korean              : **{common.pct(q_natural, q_total)}**")
    lines.append(f"- fits_intent                 : **{common.pct(q_fits, q_total)}**")
    lines.append(f"- language_ok (no mixing)     : **{common.pct(q_lang, q_total)}**")
    lines.append(
        f"- canonical-name parroting    : {common.pct(canonical_repeat, q_total)}"
    )
    lines.append(
        f"- garbled output              : {common.pct(garbled, q_total)}  ← reasoning-leak / tokenizer bug"
    )
    lines.append("")

    lines.append("## Failure-mode histogram")
    lines.append("")
    lines.append("| failure_mode | count |")
    lines.append("|---|---|")
    for fm, cnt in sorted(fm_counter.items(), key=lambda x: (-x[1], x[0])):
        lines.append(f"| `{fm}` | {cnt} |")
    lines.append("")

    def _render(rows: List[Stage2_4JudgeRecord], title: str) -> None:
        lines.append(f"### {title}")
        if not rows:
            lines.append("(none)")
            lines.append("")
            return
        for r in rows:
            lines.append(
                f"- **{r.intent_keyword}** evidence={r.total_evidence_count} "
                f"use={r.judge.overall_usefulness} div={r.judge.query_diversity} "
                f"weave={r.judge.attribute_weaving}"
            )
            for qj in r.judge.queries:
                flags = []
                if qj.repeats_canonical:
                    flags.append("repeat")
                if not qj.natural_korean:
                    flags.append("!natural")
                if qj.garbled:
                    flags.append("garbled")
                if not qj.language_ok:
                    flags.append("lang")
                tag = f" [{','.join(flags)}]" if flags else ""
                lines.append(f"    - {common.truncate(qj.query, 140)}{tag}")
            lines.append(f"  - fm: `{r.judge.failure_modes}`")
            lines.append(f"  - judge: {common.truncate(r.judge.reasoning, 180)}")
        lines.append("")

    lines.append("## Worst cases")
    lines.append("")
    _render(worst_use,     "Lowest overall_usefulness (top 5)")
    _render(worst_div,     "Lowest query_diversity (top 5)")
    _render(repeat_heavy,  "Heavy canonical-name parroting (>=2 queries, top 5)")
    _render(garbled_heavy, "Records with garbled queries (top 5)")

    return "\n".join(line for line in lines if line != "")


def build_summary_row(
    records: List[Stage2_4JudgeRecord], meta: common.RunMeta
) -> Stage2_4SummaryRow:
    n_intents = len(records)
    n_queries_total = 0
    q_natural = q_fits = 0
    canonical_repeat = 0
    garbled = 0
    for r in records:
        for qj in r.judge.queries:
            n_queries_total += 1
            if qj.natural_korean:
                q_natural += 1
            if qj.fits_intent:
                q_fits += 1
            if qj.repeats_canonical:
                canonical_repeat += 1
            if qj.garbled:
                garbled += 1

    fm_counter: Counter = Counter()
    for r in records:
        for fm in r.judge.failure_modes:
            fm_counter[fm] += 1
    for fm in STAGE_2_4_FAILURE_MODES:
        fm_counter.setdefault(fm, 0)

    return Stage2_4SummaryRow(
        run_id=meta.run_id,
        judge_model=meta.judge_model,
        provider=meta.provider,
        n_intents=n_intents,
        n_queries_total=n_queries_total,
        avg_query_diversity=common.safe_mean(
            [r.judge.query_diversity for r in records]
        ),
        avg_attribute_weaving=common.safe_mean(
            [r.judge.attribute_weaving for r in records]
        ),
        avg_canonical_coverage=common.safe_mean(
            [r.judge.canonical_coverage for r in records]
        ),
        avg_overall_usefulness=common.safe_mean(
            [r.judge.overall_usefulness for r in records]
        ),
        per_query_natural_rate=(
            round(q_natural / n_queries_total, 2) if n_queries_total else 0.0
        ),
        per_query_fits_intent_rate=(
            round(q_fits / n_queries_total, 2) if n_queries_total else 0.0
        ),
        canonical_repeat_rate=(
            round(canonical_repeat / n_queries_total, 2)
            if n_queries_total
            else 0.0
        ),
        garbled_count=garbled,
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
        default=str(root / "stage_2_4" / "expanded_intents.jsonl"),
        help="Stage 2.4 expanded_intents.jsonl (file or directory).",
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
        help="LLM provider for the judge (default = $LLM_PROVIDER)",
    )
    parser.add_argument("--limit", type=int, default=0, help="0 = all")
    parser.add_argument(
        "--sample", type=int, default=0,
        help="random-sample N records (0 = use --limit or all)",
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

    intents = [
        ExpandedIntent.model_validate(o)
        for o in common.iter_jsonl(Path(args.input))
    ]
    n_total = len(intents)
    if args.sample > 0:
        subset = common.sample_random(intents, args.sample, seed=args.seed)
    else:
        subset = common.cap(intents, args.limit)

    print(
        f"[stage_2_4 judge] run_id={run_id} {cfg.describe()}\n"
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
    records: List[Stage2_4JudgeRecord] = []

    with judge_path.open("w", encoding="utf-8") as out_fh:
        for i, intent in enumerate(subset):
            user_prompt = build_judge_user(intent)

            def _call(mt: int):
                return call_json_judge(
                    client,
                    cfg.model,
                    STAGE_2_4_JUDGE_SYSTEM,
                    user_prompt,
                    temperature=0.1,
                    max_tokens=mt,
                )

            parsed, call_meta, tag = common.call_with_retry(
                _call, max_tokens=args.max_tokens, sleep=args.sleep
            )

            judge = parse_judge_result(parsed, intent.natural_queries)
            if judge is None:
                fail += 1
                print(
                    f"[{i + 1:04d}] ERR {intent.intent_keyword}: {tag} "
                    f"raw={(call_meta.get('raw_content') or '')[:120]!r}",
                    flush=True,
                )
                time.sleep(args.sleep)
                continue

            record = Stage2_4JudgeRecord(
                intent_keyword=intent.intent_keyword,
                mapped_attributes=[a.model_dump() for a in intent.mapped_attributes],
                natural_queries=intent.natural_queries,
                total_evidence_count=intent.data_lineage.total_evidence_count,
                judge=judge,
                judge_model=call_meta["model"],
                judge_tokens=call_meta.get("tokens"),
            )
            out_fh.write(record.model_dump_json() + "\n")
            out_fh.flush()
            records.append(record)
            ok += 1
            print(
                f"[{i + 1:04d}] OK  {intent.intent_keyword} "
                f"use={judge.overall_usefulness} div={judge.query_diversity} "
                f"weave={judge.attribute_weaving} "
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
        f"\n[stage_2_4 judge] ok={ok} fail={fail} "
        f"duration={duration:.1f}s -> {report_path}",
        flush=True,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
