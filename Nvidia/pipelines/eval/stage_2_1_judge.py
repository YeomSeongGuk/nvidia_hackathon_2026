"""Stage 2.1 judge: per-doc intent/attribute extraction quality.

Evaluates the output of `pipelines.stage_2_1_extract` against the upstream
curated docs (Stage 1.2). For each (curated_doc, extraction) pair it asks a
judge LLM to rate:

  - intent_groundedness (1-5)
  - intent_type_valid (bool)
  - general_wear_false_negative (bool | null) - only when raw_intent=general_wear
  - per-attribute present/groundedness/concrete
  - failure_modes tags

It also computes `sentiment_rating_agreement` deterministically (no LLM)
from the star rating.

Output:
  $STAGE_DATA_ROOT/stage_2_1/eval/runs/<run_id>/
      judge.jsonl      per-doc Stage2_1JudgeRecord
      report.md        summary + worst-K
      meta.json        RunMeta
  $STAGE_DATA_ROOT/stage_2_1/eval/summary.jsonl    (append)
  $STAGE_DATA_ROOT/stage_2_1/eval/latest_report.md (copy)

Usage:
  # smoke
  LLM_VERIFY_SSL=0 python -m pipelines.eval.stage_2_1_judge --limit 5

  # full with Nemotron-Ultra (default)
  python -m pipelines.eval.stage_2_1_judge

  # Llama-3.3-70B judge
  python -m pipelines.eval.stage_2_1_judge \\
      --judge-model meta/llama-3.3-70b-instruct

  # Friendli multilingual judges (serverless, no local GPU needed):
  python -m pipelines.eval.stage_2_1_judge --provider friendli \\
      --judge-model zai-org/GLM-5.1
  python -m pipelines.eval.stage_2_1_judge --provider friendli \\
      --judge-model Qwen/Qwen3-235B-A22B-Instruct-2507
  python -m pipelines.eval.stage_2_1_judge --provider friendli \\
      --judge-model deepseek-ai/DeepSeek-V3.2
  python -m pipelines.eval.stage_2_1_judge --provider friendli \\
      --judge-model LGAI-EXAONE/K-EXAONE-236B-A23B

  # Local vLLM Nemotron-Super (served as "nemotron")
  LLM_EXTRA_BODY='{"chat_template_kwargs":{"enable_thinking":false}}' \\
      python -m pipelines.eval.stage_2_1_judge \\
      --provider vllm --judge-model nemotron
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
import time
from collections import Counter
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from pydantic import ValidationError

from pipelines.config import data_root
from pipelines.eval import common
from pipelines.eval.judge_client import call_json_judge
from pipelines.eval.prompts import (
    STAGE_2_1_JUDGE_SYSTEM,
    STAGE_2_1_JUDGE_USER_TEMPLATE,
)
from pipelines.eval.schemas import (
    ATTR_KEYS,
    STAGE_2_1_FAILURE_MODES,
    AttrJudge,
    Stage2_1JudgeRecord,
    Stage2_1JudgeResult,
    Stage2_1SummaryRow,
)
from pipelines.llm_client import get_client, load_env
from pipelines.schemas import CuratedDoc, ExtractedIntent

STAGE = "stage_2_1"
DEFAULT_JUDGE_MODEL = "nvidia/llama-3.1-nemotron-ultra-253b-v1"


# ---------------------------------------------------------------------------
# Loading + joining
# ---------------------------------------------------------------------------

def load_curated(path: Path) -> Dict[str, CuratedDoc]:
    out: Dict[str, CuratedDoc] = {}
    for obj in common.iter_jsonl(path):
        d = CuratedDoc.model_validate(obj)
        out[d.curated_id] = d
    return out


def load_extracted(path: Path) -> List[ExtractedIntent]:
    return [ExtractedIntent.model_validate(o) for o in common.iter_jsonl(path)]


def _rating_of(doc: Optional[CuratedDoc]) -> Optional[int]:
    if doc is None:
        return None
    # pipeline_metadata may hold the rating under either old or new key.
    meta = doc.pipeline_metadata
    r = meta.get("source_rating")
    if r is None:
        r = meta.get("rating")
    try:
        return int(r) if r is not None else None
    except (TypeError, ValueError):
        return None


def sentiment_rating_check(
    sentiment: str, rating: Optional[int]
) -> Tuple[Optional[bool], str]:
    """rating 4-5+positive, 1-2+negative, 3+neutral => agree."""
    if rating is None:
        return None, "no rating"
    s = (sentiment or "").strip().lower()
    if rating >= 4:
        expected = "positive"
    elif rating <= 2:
        expected = "negative"
    else:
        expected = "neutral"
    return s == expected, f"rating={rating} sentiment={s!r} expected={expected!r}"


# ---------------------------------------------------------------------------
# Judge result coercion (tolerate slightly-off LLM outputs)
# ---------------------------------------------------------------------------

def _to_int_or_none(v: object) -> Optional[int]:
    if v is None:
        return None
    try:
        iv = int(v)
    except (TypeError, ValueError):
        return None
    return max(1, min(5, iv))


def _to_bool_or_none(v: object) -> Optional[bool]:
    if v is None:
        return None
    if isinstance(v, bool):
        return v
    if isinstance(v, str):
        s = v.strip().lower()
        if s in ("true", "yes", "1"):
            return True
        if s in ("false", "no", "0"):
            return False
    return None


def _coerce_attributes(raw: object) -> Dict[str, AttrJudge]:
    out: Dict[str, AttrJudge] = {}
    data = raw if isinstance(raw, dict) else {}
    for key in ATTR_KEYS:
        sub = data.get(key) or {}
        if not isinstance(sub, dict):
            sub = {}
        try:
            out[key] = AttrJudge(
                present_in_text=bool(sub.get("present_in_text", False)),
                groundedness=_to_int_or_none(sub.get("groundedness")),
                concrete=_to_bool_or_none(sub.get("concrete")),
            )
        except ValidationError:
            out[key] = AttrJudge(present_in_text=False)
    return out


def parse_judge_result(raw: Optional[Dict]) -> Optional[Stage2_1JudgeResult]:
    if not raw:
        return None
    try:
        return Stage2_1JudgeResult(
            intent_groundedness=_to_int_or_none(raw.get("intent_groundedness")) or 1,
            intent_type_valid=bool(raw.get("intent_type_valid", False)),
            general_wear_false_negative=_to_bool_or_none(
                raw.get("general_wear_false_negative")
            ),
            attributes=_coerce_attributes(raw.get("attributes")),
            failure_modes=common.safe_string_list(raw.get("failure_modes")),
            reasoning=str(raw.get("reasoning") or "").strip()[:500],
        )
    except ValidationError as exc:
        print(f"  [warn] schema error: {exc}", flush=True)
        return None


# ---------------------------------------------------------------------------
# Judge prompt + runner
# ---------------------------------------------------------------------------

def build_judge_user(doc: CuratedDoc, ext: ExtractedIntent) -> str:
    attrs = ext.attributes.model_dump()
    return STAGE_2_1_JUDGE_USER_TEMPLATE.format(
        text=doc.clean_text,
        rating=_rating_of(doc),
        raw_intent=ext.raw_intent,
        material=attrs.get("material"),
        fit=attrs.get("fit"),
        color=attrs.get("color"),
        style=attrs.get("style"),
        season=attrs.get("season"),
        sentiment=ext.sentiment,
        keywords=json.dumps(ext.extracted_keywords, ensure_ascii=False),
    )


# ---------------------------------------------------------------------------
# Report
# ---------------------------------------------------------------------------

def build_report(records: List[Stage2_1JudgeRecord], meta: common.RunMeta) -> str:
    if not records:
        return "# Stage 2.1 Judge Report\n\n(no records)\n"

    n = len(records)
    ground_scores = [r.judge.intent_groundedness for r in records]
    type_valid = sum(1 for r in records if r.judge.intent_type_valid)
    gw_records = [r for r in records if r.raw_intent == "general_wear"]
    gw_fn = sum(
        1 for r in gw_records if r.judge.general_wear_false_negative is True
    )

    # attribute stats
    attr_stats: Dict[str, Dict[str, int]] = {
        k: {"present": 0, "extracted": 0, "grounded_sum": 0, "grounded_n": 0, "concrete": 0}
        for k in ATTR_KEYS
    }
    for r in records:
        for key in ATTR_KEYS:
            aj = r.judge.attributes.get(key)
            if aj is None:
                continue
            if aj.present_in_text:
                attr_stats[key]["present"] += 1
            extracted_val = r.extracted_attributes.get(key)
            if extracted_val not in (None, "", "null", "None"):
                attr_stats[key]["extracted"] += 1
                if aj.groundedness is not None:
                    attr_stats[key]["grounded_sum"] += aj.groundedness
                    attr_stats[key]["grounded_n"] += 1
                if aj.concrete is True:
                    attr_stats[key]["concrete"] += 1

    # sentiment/rating
    sr_total = sum(1 for r in records if r.sentiment_rating_agreement is not None)
    sr_ok = sum(1 for r in records if r.sentiment_rating_agreement is True)

    # failure modes (pre-fill canonical set with 0)
    fm_counter: Counter = Counter()
    for r in records:
        for fm in r.judge.failure_modes:
            fm_counter[fm] += 1
    for fm in STAGE_2_1_FAILURE_MODES:
        fm_counter.setdefault(fm, 0)

    # worst cases
    low_ground = sorted(records, key=lambda r: (r.judge.intent_groundedness, r.source_curated_id))[:5]
    invalid_type = [r for r in records if not r.judge.intent_type_valid][:5]
    missed_tpo = [r for r in records if r.judge.general_wear_false_negative is True][:5]
    noise_attr = [
        r for r in records
        if any(aj.concrete is False for aj in r.judge.attributes.values())
    ][:5]
    sr_mismatch = [r for r in records if r.sentiment_rating_agreement is False][:5]

    lines: List[str] = []
    lines.append("# Stage 2.1 Judge Report")
    lines.append("")
    lines.append(f"- run_id: `{meta.run_id}`")
    lines.append(f"- records: **{n}**")
    lines.append(f"- judge model: `{meta.judge_model}` (provider={meta.provider})")
    lines.append(f"- duration: {meta.duration_sec:.1f}s" if meta.duration_sec else "")
    lines.append("")

    lines.append("## Intent quality")
    lines.append(f"- avg intent_groundedness: **{common.safe_mean(ground_scores)}** / 5")
    lines.append(f"- intent_type_valid: **{common.pct(type_valid, n)}**")
    lines.append(
        f"- general_wear usage: {common.pct(len(gw_records), n)} — "
        f"false-negative (TPO missed): **{common.pct(gw_fn, len(gw_records))}**"
    )
    lines.append("")

    lines.append("## Attribute quality (per key)")
    lines.append("")
    lines.append("| key | mentioned in text | extracted | avg groundedness (when extracted) | concrete rate |")
    lines.append("|---|---|---|---|---|")
    for key in ATTR_KEYS:
        s = attr_stats[key]
        avg_ground = (
            round(s["grounded_sum"] / s["grounded_n"], 2) if s["grounded_n"] else None
        )
        concrete_rate = common.pct(s["concrete"], s["extracted"]) if s["extracted"] else "n/a"
        lines.append(
            f"| {key} | {common.pct(s['present'], n)} | {common.pct(s['extracted'], n)} | "
            f"{avg_ground if avg_ground is not None else 'n/a'} | {concrete_rate} |"
        )
    lines.append("")

    lines.append("## Sentiment vs star rating (deterministic)")
    lines.append(f"- agreement: **{common.pct(sr_ok, sr_total)}** (skipped when rating absent)")
    lines.append("")

    lines.append("## Failure-mode histogram")
    lines.append("")
    lines.append("| failure_mode | count |")
    lines.append("|---|---|")
    for fm, cnt in sorted(fm_counter.items(), key=lambda x: (-x[1], x[0])):
        lines.append(f"| `{fm}` | {cnt} |")
    lines.append("")

    def _render(rows: List[Stage2_1JudgeRecord], title: str) -> None:
        lines.append(f"### {title}")
        if not rows:
            lines.append("(none)")
            lines.append("")
            return
        for r in rows:
            attrs_preview = {
                k: v for k, v in r.extracted_attributes.items() if v not in (None, "")
            }
            lines.append(
                f"- **{r.source_curated_id}** (rating={r.rating}) "
                f"intent=`{r.raw_intent}` "
                f"intent_ground={r.judge.intent_groundedness} "
                f"type_valid={r.judge.intent_type_valid}"
            )
            lines.append(f"  - text: {common.truncate(r.review_text)}")
            if attrs_preview:
                lines.append(f"  - attrs: `{attrs_preview}`")
            lines.append(f"  - fm: `{r.judge.failure_modes}`")
            lines.append(f"  - judge: {common.truncate(r.judge.reasoning, 160)}")
        lines.append("")

    lines.append("## Worst cases")
    lines.append("")
    _render(low_ground, "Lowest intent_groundedness (top 5)")
    _render(invalid_type, "intent_type_valid = false (top 5)")
    _render(missed_tpo, "general_wear false-negative — missed TPO (top 5)")
    _render(noise_attr, "Non-concrete / subjective attribute values (top 5)")
    _render(sr_mismatch, "Sentiment vs rating mismatch (top 5)")

    return "\n".join(line for line in lines if line != "")


def build_summary_row(
    records: List[Stage2_1JudgeRecord], meta: common.RunMeta
) -> Stage2_1SummaryRow:
    n = len(records)
    ground_scores = [r.judge.intent_groundedness for r in records]
    gw_records = [r for r in records if r.raw_intent == "general_wear"]
    gw_fn = sum(1 for r in gw_records if r.judge.general_wear_false_negative is True)
    gw_fn_rate = round(gw_fn / len(gw_records), 2) if gw_records else None

    type_valid = sum(1 for r in records if r.judge.intent_type_valid)
    sr_total = sum(1 for r in records if r.sentiment_rating_agreement is not None)
    sr_ok = sum(1 for r in records if r.sentiment_rating_agreement is True)
    sr_rate = round(sr_ok / sr_total, 2) if sr_total else None

    attr_concrete: Dict[str, Optional[float]] = {}
    attr_ground_avg: Dict[str, Optional[float]] = {}
    for key in ATTR_KEYS:
        extracted = 0
        concrete = 0
        ground: List[int] = []
        for r in records:
            aj = r.judge.attributes.get(key)
            if aj is None:
                continue
            val = r.extracted_attributes.get(key)
            if val in (None, "", "null", "None"):
                continue
            extracted += 1
            if aj.concrete is True:
                concrete += 1
            if aj.groundedness is not None:
                ground.append(aj.groundedness)
        attr_concrete[key] = round(concrete / extracted, 2) if extracted else None
        attr_ground_avg[key] = common.safe_mean(ground)

    fm_counter: Counter = Counter()
    for r in records:
        for fm in r.judge.failure_modes:
            fm_counter[fm] += 1
    for fm in STAGE_2_1_FAILURE_MODES:
        fm_counter.setdefault(fm, 0)

    return Stage2_1SummaryRow(
        run_id=meta.run_id,
        judge_model=meta.judge_model,
        provider=meta.provider,
        n_evaluated=n,
        avg_intent_groundedness=common.safe_mean(ground_scores),
        intent_type_valid_rate=round(type_valid / n, 2) if n else 0.0,
        general_wear_rate=round(len(gw_records) / n, 2) if n else 0.0,
        general_wear_false_negative_rate=gw_fn_rate,
        sentiment_rating_agreement_rate=sr_rate,
        attribute_concrete_rate=attr_concrete,
        attribute_groundedness_avg=attr_ground_avg,
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
        "--curated",
        default=str(root / "stage_1_2"),
        help="Stage 1.2 output path (file or directory of .jsonl).",
    )
    parser.add_argument(
        "--extracted",
        default=str(root / "stage_2_1" / "stage_2_1_extracted.jsonl"),
        help="Stage 2.1 extracted intents JSONL.",
    )
    parser.add_argument(
        "--judge-model", default=DEFAULT_JUDGE_MODEL,
        help="judge LLM model id (must be on the selected provider)",
    )
    parser.add_argument(
        "--provider", choices=["nim", "friendli", "vllm"], default="nim",
        help="LLM provider for the judge (default nim for Nemotron-Ultra).",
    )
    parser.add_argument("--limit", type=int, default=0, help="0 = all")
    parser.add_argument("--sleep", type=float, default=0.2)
    parser.add_argument("--max-tokens", type=int, default=1536)
    parser.add_argument("--tag", default="", help="free-form tag for this run")
    parser.add_argument(
        "--run-id", default="",
        help="override run-id (default: UTC timestamp)",
    )
    args = parser.parse_args(argv)

    load_env()
    client, default_model = get_client(
        provider=args.provider, model_override=args.judge_model
    )
    cfg = client._llm_config  # type: ignore[attr-defined]

    run_id = args.run_id or common.make_run_id(args.tag or None)
    out_dir = common.run_dir(STAGE, run_id)
    judge_path = out_dir / "judge.jsonl"
    report_path = out_dir / "report.md"
    meta_path = out_dir / "meta.json"

    curated = load_curated(Path(args.curated))
    extracted = load_extracted(Path(args.extracted))
    n_total = len(extracted)
    subset = common.cap(extracted, args.limit)

    print(
        f"[stage_2_1 judge] run_id={run_id} {cfg.describe()}\n"
        f"  curated={len(curated)} extracted={n_total} sampled={len(subset)}\n"
        f"  -> {out_dir}",
        flush=True,
    )

    meta = common.RunMeta(
        stage=STAGE,
        run_id=run_id,
        started_at=dt.datetime.now(dt.timezone.utc).isoformat(),
        judge_model=cfg.model,
        provider=cfg.provider,
        input_path=str(args.extracted),
        limit=args.limit,
        n_units_total=n_total,
        n_units_sampled=len(subset),
        tag=args.tag,
        git_rev=common.git_rev_short(),
    )

    ok = fail = 0
    t0 = time.time()
    records: List[Stage2_1JudgeRecord] = []

    with judge_path.open("w", encoding="utf-8") as out_fh:
        for i, ext in enumerate(subset):
            doc = curated.get(ext.source_curated_id)
            if doc is None:
                print(
                    f"[{i + 1:04d}] SKIP {ext.source_curated_id}: not in curated",
                    flush=True,
                )
                continue

            user_prompt = build_judge_user(doc, ext)

            def _call(mt: int):
                return call_json_judge(
                    client,
                    cfg.model,
                    STAGE_2_1_JUDGE_SYSTEM,
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
                    f"[{i + 1:04d}] ERR {ext.source_curated_id}: {tag} "
                    f"tokens={call_meta.get('tokens')} "
                    f"raw={(call_meta.get('raw_content') or '')[:120]!r}",
                    flush=True,
                )
                time.sleep(args.sleep)
                continue

            rating = _rating_of(doc)
            sr_agree, sr_reason = sentiment_rating_check(ext.sentiment, rating)

            record = Stage2_1JudgeRecord(
                source_curated_id=ext.source_curated_id,
                review_text=doc.clean_text,
                rating=rating,
                raw_intent=ext.raw_intent,
                extracted_attributes=ext.attributes.model_dump(),
                extracted_sentiment=ext.sentiment,
                judge=judge,
                sentiment_rating_agreement=sr_agree,
                sentiment_rating_reason=sr_reason,
                judge_model=call_meta["model"],
                judge_tokens=call_meta.get("tokens"),
            )
            out_fh.write(record.model_dump_json() + "\n")
            out_fh.flush()
            records.append(record)
            ok += 1

            gw_fn = judge.general_wear_false_negative
            gw_fn_s = "" if gw_fn is None else f" gw_fn={gw_fn}"
            print(
                f"[{i + 1:04d}] OK  {ext.source_curated_id} "
                f"ig={judge.intent_groundedness} "
                f"tv={judge.intent_type_valid}"
                f"{gw_fn_s} "
                f"fm={judge.failure_modes or '[]'} "
                f"sr={sr_agree}",
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
