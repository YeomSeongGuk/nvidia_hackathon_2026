"""Stage 1.2 judge: upstream curation quality.

Evaluates the CuratedDoc output of Stage 1.2 (which in this repo we only
consume - the actual curation lives in a different session/repo). The goal
is to detect non-fashion leakage, PII, noise, and low-quality text so you
can tighten the upstream curator before spending more compute downstream.

Output layout (accumulating across runs):
  $STAGE_DATA_ROOT/stage_1_2/eval/runs/<run_id>/judge.jsonl
  $STAGE_DATA_ROOT/stage_1_2/eval/runs/<run_id>/report.md
  $STAGE_DATA_ROOT/stage_1_2/eval/runs/<run_id>/meta.json
  $STAGE_DATA_ROOT/stage_1_2/eval/summary.jsonl         (append)
  $STAGE_DATA_ROOT/stage_1_2/eval/latest_report.md      (copy)

Usage:
  # smoke test 5 docs
  LLM_VERIFY_SSL=0 python -m pipelines.eval.stage_1_2_judge --limit 5

  # sample 100 out of N
  python -m pipelines.eval.stage_1_2_judge --sample 100 --seed 1

  # explicit input path (for legacy flat data layout)
  python -m pipelines.eval.stage_1_2_judge \\
      --input ./data/curated_sample.jsonl
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
    STAGE_1_2_JUDGE_SYSTEM,
    STAGE_1_2_JUDGE_USER_TEMPLATE,
)
from pipelines.eval.schemas import (
    STAGE_1_2_FAILURE_MODES,
    Stage1_2JudgeRecord,
    Stage1_2JudgeResult,
    Stage1_2SummaryRow,
)
from pipelines.llm_client import get_client, load_env
from pipelines.schemas import CuratedDoc

STAGE = "stage_1_2"
DEFAULT_JUDGE_MODEL = "nvidia/llama-3.1-nemotron-ultra-253b-v1"

_NOISE_LEVELS = ("none", "low", "medium", "high")
_LANGS = ("ko", "en", "mixed", "other")


# ---------------------------------------------------------------------------
# Parsing
# ---------------------------------------------------------------------------

def _coerce_enum(v: object, allowed: tuple, default: str) -> str:
    if isinstance(v, str):
        s = v.strip().lower()
        if s in allowed:
            return s
    return default


def _to_int(v: object, lo: int, hi: int) -> int:
    try:
        iv = int(v)
    except (TypeError, ValueError):
        return lo
    return max(lo, min(hi, iv))


def parse_judge_result(raw: Optional[Dict]) -> Optional[Stage1_2JudgeResult]:
    if not raw:
        return None
    try:
        return Stage1_2JudgeResult(
            is_fashion=bool(raw.get("is_fashion", False)),
            has_tpo_signal=bool(raw.get("has_tpo_signal", False)),
            text_quality=_to_int(raw.get("text_quality"), 1, 5),
            language=_coerce_enum(raw.get("language"), _LANGS, "other"),
            noise_level=_coerce_enum(raw.get("noise_level"), _NOISE_LEVELS, "none"),
            pii_leak=bool(raw.get("pii_leak", False)),
            failure_modes=common.safe_string_list(raw.get("failure_modes")),
            reasoning=str(raw.get("reasoning") or "").strip()[:500],
        )
    except ValidationError as exc:
        print(f"  [warn] schema error: {exc}", flush=True)
        return None


def build_judge_user(doc: CuratedDoc) -> str:
    meta = doc.pipeline_metadata or {}
    rating = meta.get("rating") or meta.get("source_rating")
    source_type = meta.get("source_type")
    return STAGE_1_2_JUDGE_USER_TEMPLATE.format(
        doc_id=doc.curated_id,
        rating=rating,
        source_type=source_type,
        text=doc.clean_text,
    )


# ---------------------------------------------------------------------------
# Report
# ---------------------------------------------------------------------------

def build_report(records: List[Stage1_2JudgeRecord], meta: common.RunMeta) -> str:
    if not records:
        return "# Stage 1.2 Judge Report\n\n(no records)\n"

    n = len(records)
    fashion = sum(1 for r in records if r.judge.is_fashion)
    tpo = sum(1 for r in records if r.judge.has_tpo_signal)
    pii = sum(1 for r in records if r.judge.pii_leak)
    quality_scores = [r.judge.text_quality for r in records]

    noise_hist: Counter = Counter()
    lang_hist: Counter = Counter()
    for r in records:
        noise_hist[r.judge.noise_level] += 1
        lang_hist[r.judge.language] += 1
    for lv in _NOISE_LEVELS:
        noise_hist.setdefault(lv, 0)
    for lv in _LANGS:
        lang_hist.setdefault(lv, 0)

    fm_counter: Counter = Counter()
    for r in records:
        for fm in r.judge.failure_modes:
            fm_counter[fm] += 1
    for fm in STAGE_1_2_FAILURE_MODES:
        fm_counter.setdefault(fm, 0)

    non_fashion = [r for r in records if not r.judge.is_fashion][:5]
    low_quality = sorted(records, key=lambda r: (r.judge.text_quality, r.curated_id))[:5]
    pii_cases = [r for r in records if r.judge.pii_leak][:5]
    noisy = [r for r in records if r.judge.noise_level in ("medium", "high")][:5]

    lines: List[str] = []
    lines.append("# Stage 1.2 Judge Report")
    lines.append("")
    lines.append(f"- run_id: `{meta.run_id}`")
    lines.append(f"- records: **{n}** (of {meta.n_units_total})")
    lines.append(f"- judge model: `{meta.judge_model}` (provider={meta.provider})")
    if meta.duration_sec:
        lines.append(f"- duration: {meta.duration_sec}s")
    lines.append("")

    lines.append("## Curation health")
    lines.append(f"- is_fashion: **{common.pct(fashion, n)}**")
    lines.append(f"- has_tpo_signal: **{common.pct(tpo, n)}**")
    lines.append(f"- avg text_quality: **{common.safe_mean(quality_scores)}** / 5")
    lines.append(f"- pii_leak: **{common.pct(pii, n)}**")
    lines.append("")

    lines.append("## Noise & language histograms")
    lines.append("")
    lines.append("| noise_level | count |")
    lines.append("|---|---|")
    for lv in _NOISE_LEVELS:
        lines.append(f"| `{lv}` | {noise_hist[lv]} |")
    lines.append("")
    lines.append("| language | count |")
    lines.append("|---|---|")
    for lv in _LANGS:
        lines.append(f"| `{lv}` | {lang_hist[lv]} |")
    lines.append("")

    lines.append("## Failure-mode histogram")
    lines.append("")
    lines.append("| failure_mode | count |")
    lines.append("|---|---|")
    for fm, cnt in sorted(fm_counter.items(), key=lambda x: (-x[1], x[0])):
        lines.append(f"| `{fm}` | {cnt} |")
    lines.append("")

    def _render(rows: List[Stage1_2JudgeRecord], title: str) -> None:
        lines.append(f"### {title}")
        if not rows:
            lines.append("(none)")
            lines.append("")
            return
        for r in rows:
            lines.append(
                f"- **{r.curated_id}** (rating={r.rating}) "
                f"quality={r.judge.text_quality} "
                f"fashion={r.judge.is_fashion} "
                f"tpo={r.judge.has_tpo_signal} "
                f"lang={r.judge.language} "
                f"noise={r.judge.noise_level}"
            )
            lines.append(f"  - text: {common.truncate(r.clean_text)}")
            lines.append(f"  - fm: `{r.judge.failure_modes}`")
            lines.append(f"  - judge: {common.truncate(r.judge.reasoning, 160)}")
        lines.append("")

    lines.append("## Worst cases")
    lines.append("")
    _render(non_fashion, "is_fashion = false (top 5)")
    _render(low_quality, "Lowest text_quality (top 5)")
    _render(pii_cases, "PII leak (top 5)")
    _render(noisy, "Noisy text (medium/high) (top 5)")

    return "\n".join(line for line in lines if line != "")


def build_summary_row(
    records: List[Stage1_2JudgeRecord], meta: common.RunMeta
) -> Stage1_2SummaryRow:
    n = len(records)
    fashion = sum(1 for r in records if r.judge.is_fashion)
    tpo = sum(1 for r in records if r.judge.has_tpo_signal)
    pii = sum(1 for r in records if r.judge.pii_leak)
    quality_scores = [r.judge.text_quality for r in records]

    noise_hist: Dict[str, int] = {lv: 0 for lv in _NOISE_LEVELS}
    for r in records:
        noise_hist[r.judge.noise_level] = noise_hist.get(r.judge.noise_level, 0) + 1

    fm_counter: Counter = Counter()
    for r in records:
        for fm in r.judge.failure_modes:
            fm_counter[fm] += 1
    for fm in STAGE_1_2_FAILURE_MODES:
        fm_counter.setdefault(fm, 0)

    return Stage1_2SummaryRow(
        run_id=meta.run_id,
        judge_model=meta.judge_model,
        provider=meta.provider,
        n_evaluated=n,
        fashion_rate=round(fashion / n, 2) if n else 0.0,
        has_tpo_rate=round(tpo / n, 2) if n else 0.0,
        avg_text_quality=common.safe_mean(quality_scores),
        pii_rate=round(pii / n, 2) if n else 0.0,
        noise_hist=noise_hist,
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
        default=str(root / "stage_1_2"),
        help="Stage 1.2 output: .jsonl file OR directory of .jsonl.",
    )
    parser.add_argument("--judge-model", default=DEFAULT_JUDGE_MODEL)
    parser.add_argument(
        "--provider", choices=["nim", "friendli", "vllm"], default="nim"
    )
    parser.add_argument("--limit", type=int, default=0, help="0 = all")
    parser.add_argument(
        "--sample", type=int, default=0,
        help="random sample N docs (uses --seed); 0 disables sampling.",
    )
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--sleep", type=float, default=0.2)
    parser.add_argument("--max-tokens", type=int, default=1024)
    parser.add_argument("--tag", default="")
    parser.add_argument("--run-id", default="")
    parser.add_argument(
        "--stage-override", default="",
        help="Override STAGE dir name (used when tri_judge reuses this "
             "judge for Stage 1.0 seed data — output lands under "
             "$STAGE_DATA_ROOT/stage_1_0/eval/ instead of stage_1_2/).",
    )
    args = parser.parse_args(argv)

    load_env()
    client, _ = get_client(
        provider=args.provider, model_override=args.judge_model
    )
    cfg = client._llm_config  # type: ignore[attr-defined]

    stage = args.stage_override or STAGE
    run_id = args.run_id or common.make_run_id(args.tag or None)
    out_dir = common.run_dir(stage, run_id)
    judge_path = out_dir / "judge.jsonl"
    report_path = out_dir / "report.md"
    meta_path = out_dir / "meta.json"

    # Load curated docs (file or dir of .jsonl).
    # Be lenient: Stage 1.0 seed output is shaped like {"rating":..., "text":...}
    # (raw naver rows filtered by FASHION_KEYWORDS). Synthesize a minimal
    # CuratedDoc for those so the same rubric can score seed quality.
    def _coerce_to_curateddoc(obj: Dict[str, Any], idx: int) -> Dict[str, Any]:
        has_id = "curated_id" in obj or "doc_id" in obj
        has_text = (
            "clean_text" in obj or "raw_text" in obj
        )
        if has_id and has_text:
            return obj
        out = dict(obj)
        if not has_id:
            out["curated_id"] = f"seed_{idx:05d}"
        if not has_text and isinstance(obj.get("text"), str):
            out["clean_text"] = obj["text"]
        if "pipeline_metadata" not in out and "metadata" not in out:
            if "rating" in obj:
                out["pipeline_metadata"] = {
                    "rating": obj["rating"], "source_type": "seed"
                }
        return out

    docs: List[CuratedDoc] = [
        CuratedDoc.model_validate(_coerce_to_curateddoc(obj, i))
        for i, obj in enumerate(common.iter_jsonl(Path(args.input)))
    ]
    n_total = len(docs)

    if args.sample:
        subset = common.sample_random(docs, args.sample, seed=args.seed)
    else:
        subset = common.cap(docs, args.limit)

    print(
        f"[stage_1_2 judge] run_id={run_id} {cfg.describe()}\n"
        f"  total={n_total} sampled={len(subset)}\n"
        f"  -> {out_dir}",
        flush=True,
    )

    meta = common.RunMeta(
        stage=stage,
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
        extra={"sample": args.sample, "seed": args.seed},
    )

    ok = fail = 0
    t0 = time.time()
    records: List[Stage1_2JudgeRecord] = []

    with judge_path.open("w", encoding="utf-8") as out_fh:
        for i, doc in enumerate(subset):
            user_prompt = build_judge_user(doc)

            def _call(mt: int):
                return call_json_judge(
                    client,
                    cfg.model,
                    STAGE_1_2_JUDGE_SYSTEM,
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
                    f"[{i + 1:04d}] ERR {doc.curated_id}: {tag} "
                    f"tokens={call_meta.get('tokens')} "
                    f"raw={(call_meta.get('raw_content') or '')[:120]!r}",
                    flush=True,
                )
                time.sleep(args.sleep)
                continue

            rating = doc.pipeline_metadata.get("rating") or doc.pipeline_metadata.get(
                "source_rating"
            )
            try:
                rating_int = int(rating) if rating is not None else None
            except (TypeError, ValueError):
                rating_int = None

            record = Stage1_2JudgeRecord(
                curated_id=doc.curated_id,
                clean_text=doc.clean_text,
                rating=rating_int,
                source_type=doc.pipeline_metadata.get("source_type"),
                judge=judge,
                judge_model=call_meta["model"],
                judge_tokens=call_meta.get("tokens"),
            )
            out_fh.write(record.model_dump_json() + "\n")
            out_fh.flush()
            records.append(record)
            ok += 1

            print(
                f"[{i + 1:04d}] OK  {doc.curated_id} "
                f"fashion={judge.is_fashion} tpo={judge.has_tpo_signal} "
                f"q={judge.text_quality} lang={judge.language} noise={judge.noise_level} "
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
    common.append_summary(stage, summary_row.model_dump())
    common.copy_latest_report(stage, run_id)

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
