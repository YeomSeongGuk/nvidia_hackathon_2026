"""Sealed driver for ONE Stage-1 iteration of the PLAN.md loop.

This is the canonical entry point for a subagent to execute an
iteration end-to-end. It assumes:

  - the user is already on branch `experiment/stage1-iterative-improvement`
  - a coupang Brev instance is reachable via `brev exec coupang`
  - Friendli key is in `.env`
  - the "baseline" source pipeline to patch lives at
    `code/stage1_work/data_pipeline_vllm.py` inside
    `brev_snapshot/` OR at `scripts/patches/baseline_pipeline_script.py`
    (falls back to pulling from coupang on demand).

Flow
====

  1. Prepare `experiments/iter_NN_<slug>/` locally.
     Copy the parent iter's `pipeline_script.py` in as the starting
     point (or the baseline on disk if `--parent-iter` is empty).
  2. Write `hypothesis.md`.
  3. If `--patch <file>` is given, `git apply --3way` it against the
     iteration folder.
  4. Upload `pipeline_script.py` to coupang:
       ~/experiments_data/iter_NN_<slug>/data_pipeline_vllm.py
  5. Kick off pipeline on coupang with
       STAGE_DATA_ROOT=~/experiments_data/iter_NN_<slug>/data
     and generate-size=50.  Writes four JSONLs into
     ~/experiments_data/iter_NN_<slug>/output/.
  6. `brev copy` those four jsonl back to
     experiments/iter_NN_<slug>/output/.
  7. Run scripts/tri_judge_run.py (on LOCAL with --stage-data-root
     pointing at coupang's $STAGE_DATA_ROOT via rsync first, OR on
     coupang and copy judge_raw back). For simplicity we run the
     tri-judge on COUPANG too (closer to Friendli, data already there),
     then pull back judge_raw/.
  8. Run scripts/quant_stage1_report.py locally on the pulled output.
  9. Assemble metrics.json (with sha256 of each output jsonl +
     judge ensemble from step 7 + quant from step 8 + promote flag).
  10. Run scripts/make_comparison.py  vs the parent iter's metrics.json.
  11. Write run_log.txt.
  12. `git add experiments/iter_NN_<slug>/  experiments/summary.md`
      then `git commit`.

The subagent is expected to call this driver ONCE per iteration; all
failures should leave `run_log.txt` on disk so the orchestrator can
read it without re-opening the subagent.

Usage:
  python scripts/iter_run.py \\
      --iter-id 02 \\
      --slug title_max_tokens_short \\
      --parent-iter iter_01_title_prompt_strict \\
      --hypothesis-file hyps/iter_02.md \\
      --patch patches/iter_02.patch \\
      --n-records 50
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import shlex
import shutil
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional


# -- Paths --------------------------------------------------------------------

REPO_ROOT = Path(__file__).resolve().parent.parent
EXPERIMENTS_DIR = REPO_ROOT / "experiments"
SCRIPTS_DIR = REPO_ROOT / "scripts"
BASELINE_PIPELINE = (
    REPO_ROOT / "brev_snapshot" / "code" / "stage1_work" / "data_pipeline_vllm.py"
)
COUPANG_ROOT = "/home/nvidia/experiments_data"
COUPANG_VENV_PY = "/home/nvidia/coupang/.venv/bin/python"
COUPANG_PIPELINES_DIR = "/home/nvidia/stage2_work"  # has pipelines/ eval/ etc.
VLLM_URL = "http://localhost:5000/v1"
VLLM_MODEL = "nemotron"


FOUR_OUTPUT_FILES = [
    "stage_1_0_seed.jsonl",
    "stage_1_1_synthetic.jsonl",
    "stage_1_1_5_deduped.jsonl",
    "stage_1_2_processed.jsonl",
]


# -- tiny utils ---------------------------------------------------------------

def _now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")


def _sha256(path: Path) -> str:
    if not path.exists():
        return ""
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return f"sha256:{h.hexdigest()}"


def _run(cmd: List[str], log_fh=None, check: bool = False, env: Optional[Dict[str, str]] = None) -> int:
    line = "$ " + " ".join(shlex.quote(c) for c in cmd)
    print(line, flush=True)
    if log_fh:
        log_fh.write(line + "\n")
        log_fh.flush()
    proc = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        env=env,
        text=True,
    )
    assert proc.stdout is not None
    for line in proc.stdout:
        print(line, end="", flush=True)
        if log_fh:
            log_fh.write(line)
            log_fh.flush()
    rc = proc.wait()
    if check and rc != 0:
        raise SystemExit(f"command failed rc={rc}: {cmd}")
    return rc


def _brev_exec(remote_cmd: str, log_fh=None) -> int:
    """Run a shell one-liner on coupang via `brev exec coupang`."""
    return _run(["brev", "exec", "coupang", remote_cmd], log_fh=log_fh)


# -- steps --------------------------------------------------------------------

def _prepare_iter_dir(
    iter_id: str, slug: str, parent_iter: Optional[str]
) -> Path:
    iter_dir = EXPERIMENTS_DIR / f"iter_{iter_id}_{slug}"
    iter_dir.mkdir(parents=True, exist_ok=True)
    (iter_dir / "output").mkdir(exist_ok=True)
    (iter_dir / "judge_raw").mkdir(exist_ok=True)

    # Seed pipeline_script.py from the parent if given, else from baseline.
    target = iter_dir / "pipeline_script.py"
    if not target.exists():
        if parent_iter:
            src = EXPERIMENTS_DIR / parent_iter / "pipeline_script.py"
            if not src.exists():
                raise SystemExit(
                    f"parent iter {parent_iter} has no pipeline_script.py at {src}"
                )
            shutil.copy2(src, target)
        elif BASELINE_PIPELINE.exists():
            shutil.copy2(BASELINE_PIPELINE, target)
        else:
            raise SystemExit(
                f"No parent and no baseline at {BASELINE_PIPELINE}. "
                f"Either set --parent-iter or populate the baseline first."
            )
    return iter_dir


def _write_hypothesis(iter_dir: Path, hypothesis_path: Optional[Path], text: Optional[str]) -> None:
    out = iter_dir / "hypothesis.md"
    if hypothesis_path and hypothesis_path.exists():
        # If caller pointed at the already-staged file, nothing to do.
        try:
            same_file = hypothesis_path.resolve() == out.resolve()
        except FileNotFoundError:
            same_file = False
        if not same_file:
            shutil.copy2(hypothesis_path, out)
    elif text:
        out.write_text(text, encoding="utf-8")
    elif not out.exists():
        out.write_text(
            f"# Hypothesis for {iter_dir.name}\n\n(TBD by orchestrator)\n",
            encoding="utf-8",
        )


def _apply_patch(iter_dir: Path, patch_path: Optional[Path], log_fh) -> None:
    if patch_path is None:
        return
    if not patch_path.exists():
        raise SystemExit(f"patch not found: {patch_path}")
    # Copy the patch into the iter dir for reproducibility.
    dst = iter_dir / "patch.diff"
    shutil.copy2(patch_path, dst)
    # Apply to pipeline_script.py in-place. The patch is expected to
    # target `a/experiments/iter_NN_<slug>/pipeline_script.py`.
    rc = _run(
        ["git", "apply", "--3way", "--whitespace=nowarn", str(dst)],
        log_fh=log_fh,
    )
    if rc != 0:
        raise SystemExit(f"git apply failed rc={rc}")


def _upload_pipeline_script(iter_dir: Path, iter_full: str, log_fh) -> None:
    _brev_exec(f"mkdir -p {COUPANG_ROOT}/{iter_full}/data /home/nvidia/experiments_data/{iter_full}/output", log_fh=log_fh)
    rc = _run(
        [
            "brev", "copy",
            str(iter_dir / "pipeline_script.py"),
            f"coupang:{COUPANG_ROOT}/{iter_full}/data_pipeline_vllm.py",
        ],
        log_fh=log_fh,
    )
    if rc != 0:
        raise SystemExit(f"brev copy (upload) failed rc={rc}")


def _run_pipeline_remote(
    iter_full: str, n_records: int, log_fh
) -> int:
    """Kick off the 4-stage Stage 1 pipeline on coupang."""
    # The pipeline script writes into data/stage_1_0, data/stage_1_1, etc.
    # relative to its own cwd. We cd into the per-iter dir first.
    remote = (
        f"export LLM_EXTRA_BODY='{{\"chat_template_kwargs\":{{\"enable_thinking\":false}}}}'; "
        f"cd {COUPANG_ROOT}/{iter_full} && "
        f"{COUPANG_VENV_PY} data_pipeline_vllm.py "
        f"--data-path /home/nvidia/stage1_work/data/naver_shopping.txt "
        f"--generate-size {n_records} 2>&1 | tee {COUPANG_ROOT}/{iter_full}/run_pipeline.log ; "
        # Rename outputs into the canonical names expected by the judges.
        f"mkdir -p {COUPANG_ROOT}/{iter_full}/output; "
        f"cp {COUPANG_ROOT}/{iter_full}/data/stage_1_0/seed_data.jsonl             {COUPANG_ROOT}/{iter_full}/output/stage_1_0_seed.jsonl 2>/dev/null || true; "
        f"cp {COUPANG_ROOT}/{iter_full}/data/stage_1_1/synthetic_data.jsonl        {COUPANG_ROOT}/{iter_full}/output/stage_1_1_synthetic.jsonl 2>/dev/null || true; "
        # No explicit 1.1.5 output from team pipeline; fall back to 1.1 copy if missing
        f"[ -f {COUPANG_ROOT}/{iter_full}/data/stage_1_1_5/deduped.jsonl ] && cp {COUPANG_ROOT}/{iter_full}/data/stage_1_1_5/deduped.jsonl {COUPANG_ROOT}/{iter_full}/output/stage_1_1_5_deduped.jsonl || cp {COUPANG_ROOT}/{iter_full}/output/stage_1_1_synthetic.jsonl {COUPANG_ROOT}/{iter_full}/output/stage_1_1_5_deduped.jsonl; "
        f"cp {COUPANG_ROOT}/{iter_full}/data/stage_1_2/processed_reviews.jsonl     {COUPANG_ROOT}/{iter_full}/output/stage_1_2_processed.jsonl 2>/dev/null || true; "
        f"wc -l {COUPANG_ROOT}/{iter_full}/output/*.jsonl"
    )
    return _brev_exec(remote, log_fh=log_fh)


def _pull_outputs(iter_dir: Path, iter_full: str, log_fh) -> None:
    dst = iter_dir / "output"
    dst.mkdir(exist_ok=True)
    for f in FOUR_OUTPUT_FILES:
        rc = -1
        for attempt in range(3):
            rc = _run(
                [
                    "brev", "copy",
                    f"coupang:{COUPANG_ROOT}/{iter_full}/output/{f}",
                    str(dst / f),
                ],
                log_fh=log_fh,
            )
            if rc == 0 and (dst / f).exists():
                break
            time.sleep(2)
        if rc != 0:
            print(f"  [warn] failed to pull {f} after 3 attempts (rc={rc})", file=sys.stderr, flush=True)


def _run_tri_judge_remote(
    iter_full: str, run_id: str, tag: str, log_fh
) -> int:
    """Run tri_judge_run.py on coupang, leaving judge_metrics.json + judge_raw/ there."""
    remote = (
        f"export STAGE_DATA_ROOT={COUPANG_ROOT}/{iter_full}/data_eval; "
        f"export LLM_EXTRA_BODY='{{\"chat_template_kwargs\":{{\"enable_thinking\":false}}}}'; "
        f"mkdir -p $STAGE_DATA_ROOT; "
        f"cd {COUPANG_PIPELINES_DIR} && "
        f"PYTHONPATH=. {COUPANG_VENV_PY} scripts/tri_judge_run.py "
        f"--output-dir    {COUPANG_ROOT}/{iter_full}/output "
        f"--stage-data-root $STAGE_DATA_ROOT "
        f"--judge-raw-dir {COUPANG_ROOT}/{iter_full}/judge_raw "
        f"--metrics-out   {COUPANG_ROOT}/{iter_full}/judge_metrics.json "
        f"--provider friendli "
        f"--run-id {run_id} --tag {tag} "
        f"--skip-on-error 2>&1 | tee -a {COUPANG_ROOT}/{iter_full}/run_pipeline.log"
    )
    return _brev_exec(remote, log_fh=log_fh)


def _pull_judge_artifacts(iter_dir: Path, iter_full: str, log_fh) -> None:
    # judge_metrics.json
    _run(
        [
            "brev", "copy",
            f"coupang:{COUPANG_ROOT}/{iter_full}/judge_metrics.json",
            str(iter_dir / "judge_metrics.json"),
        ],
        log_fh=log_fh,
    )
    # judge_raw/*.jsonl — pull each of the 12 files (7 if some stages skipped).
    # Use rsync-style via brev copy directory.
    jr_src = f"coupang:{COUPANG_ROOT}/{iter_full}/judge_raw"
    _run(["brev", "copy", jr_src, str(iter_dir / "judge_raw")], log_fh=log_fh)
    # pipeline_run log
    _run(
        [
            "brev", "copy",
            f"coupang:{COUPANG_ROOT}/{iter_full}/run_pipeline.log",
            str(iter_dir / "run_pipeline_remote.log"),
        ],
        log_fh=log_fh,
    )


def _run_quant_local(iter_dir: Path, log_fh) -> Dict[str, Any]:
    out_json = iter_dir / "quant_metrics.json"
    rc = _run(
        [
            sys.executable, str(SCRIPTS_DIR / "quant_stage1_report.py"),
            "--output-dir", str(iter_dir / "output"),
            "--json-out",   str(out_json),
            "--md-out",     str(iter_dir / "quant_report.md"),
        ],
        log_fh=log_fh,
    )
    if rc != 0:
        print(f"  [warn] quant probe failed rc={rc}", file=sys.stderr, flush=True)
        return {}
    try:
        return json.loads(out_json.read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001
        print(f"  [warn] quant JSON unreadable: {exc}", file=sys.stderr)
        return {}


def _decide_promote(j: Dict[str, Any], q: Dict[str, Any]) -> Dict[str, Any]:
    """PLAN §6 promotion bar check."""
    def _mean(path: List[str]) -> Optional[float]:
        node: Any = j
        for p in path:
            if not isinstance(node, dict):
                return None
            node = node.get(p)
            if node is None:
                return None
        if isinstance(node, dict) and "mean" in node:
            return node.get("mean")
        return node if isinstance(node, (int, float)) else None

    checks = {
        "stage_1_0.fashion_rate_ge_0.90":     (_mean(["stage_1_0", "fashion_rate"]) or 0) >= 0.90,
        "stage_1_0.avg_text_quality_ge_3.5":  (_mean(["stage_1_0", "avg_text_quality"]) or 0) >= 3.5,
        "stage_1_1.title_leak_le_0.02":       (_mean(["stage_1_1", "title_reasoning_leak_rate"]) or 1.0) <= 0.02,
        "stage_1_1.fashion_rate_ge_0.95":     (_mean(["stage_1_1", "fashion_rate"]) or 0) >= 0.95,
        "stage_1_1.attr_grounded_ge_0.70":    (_mean(["stage_1_1", "attr_grounded_rate"]) or 0) >= 0.70,
        "stage_1_1.persona_ge_3.5":           (_mean(["stage_1_1", "avg_persona_reflection"]) or 0) >= 3.5,
        "quant.rating_3_share_gt_0":          ((q.get("stage_1_1") or {}).get("rating_3_share") or 0) > 0,
        "stage_1_1_5.dedup_miss_rate_le_0.05":(_mean(["stage_1_1_5", "dedup_miss_rate"]) or 1.0) <= 0.05,
        "stage_1_2.retention_ge_0.85":        ((q.get("stage_1_2") or {}).get("retention_from_stage_1_1_5") or 0) >= 0.85,
        "stage_1_2.fashion_rate_ge_0.95":     (_mean(["stage_1_2", "fashion_rate"]) or 0) >= 0.95,
    }
    promote = all(checks.values())
    return {"promote": promote, "checks": checks}


def _high_variance(j: Dict[str, Any]) -> bool:
    """Mark as HIGH_VARIANCE if judge range > 0.15 on the headline leak-rate."""
    node: Any = j
    for p in ("stage_1_1", "title_reasoning_leak_rate"):
        if not isinstance(node, dict):
            return False
        node = node.get(p)
        if node is None:
            return False
    if isinstance(node, dict):
        rng = node.get("range")
        if isinstance(rng, (int, float)) and rng > 0.15:
            return True
    return False


def _assemble_metrics_json(
    iter_dir: Path,
    iter_full: str,
    parent_iter: Optional[str],
    run_id: str,
    tag: str,
    judge_metrics: Dict[str, Any],
    quant_metrics: Dict[str, Any],
) -> Dict[str, Any]:
    hashes = {
        f: _sha256(iter_dir / "output" / f) for f in FOUR_OUTPUT_FILES
    }
    promote = _decide_promote(judge_metrics.get("ensemble") or {}, quant_metrics)
    hi_var = _high_variance(judge_metrics.get("ensemble") or {})

    metrics = {
        "iter_id": iter_full,
        "parent_iter": parent_iter or "",
        "timestamp": _now(),
        "run_id": run_id,
        "tag": tag,
        "output_hashes": hashes,
        "stage_1_0":   (judge_metrics.get("ensemble") or {}).get("stage_1_0") or {},
        "stage_1_1":   (judge_metrics.get("ensemble") or {}).get("stage_1_1") or {},
        "stage_1_1_5": (judge_metrics.get("ensemble") or {}).get("stage_1_1_5") or {},
        "stage_1_2":   (judge_metrics.get("ensemble") or {}).get("stage_1_2") or {},
        "quant": quant_metrics,
        "e2e": (quant_metrics.get("e2e") or {}),
        "judges": judge_metrics.get("judges"),
        "judge_duration_sec": judge_metrics.get("duration_sec"),
        "judge_errors": judge_metrics.get("errors"),
        "high_variance": hi_var,
        "promote": promote["promote"],
        "promote_checks": promote["checks"],
    }
    (iter_dir / "metrics.json").write_text(
        json.dumps(metrics, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return metrics


def _run_make_comparison(
    iter_dir: Path, parent_iter: Optional[str], log_fh
) -> None:
    cmd = [
        sys.executable, str(SCRIPTS_DIR / "make_comparison.py"),
        "--this", str(iter_dir / "metrics.json"),
        "--out",  str(iter_dir / "comparison.md"),
        "--summary", str(EXPERIMENTS_DIR / "summary.md"),
    ]
    if parent_iter:
        parent_metrics = EXPERIMENTS_DIR / parent_iter / "metrics.json"
        if parent_metrics.exists():
            cmd += ["--parent", str(parent_metrics)]
    _run(cmd, log_fh=log_fh)


def _write_judge_report_stub(iter_dir: Path, metrics: Dict[str, Any]) -> None:
    """Dump a human-readable summary (the real per-judge reports are in
    judge_raw/ and $STAGE_DATA_ROOT on coupang, but we surface a compact
    overview here for reviewers)."""
    lines = [
        f"# Judge ensemble report for {metrics['iter_id']}",
        "",
        f"- run_id: `{metrics['run_id']}`",
        f"- judges: {metrics.get('judges')}",
        f"- high_variance: {metrics.get('high_variance')}",
        f"- promote: {metrics.get('promote')}",
        "",
        "## Promotion-bar checks",
        "",
        "| check | passed |",
        "|---|---|",
    ]
    for k, v in (metrics.get("promote_checks") or {}).items():
        lines.append(f"| `{k}` | {v} |")
    lines.append("")
    lines.append("## Per-stage ensemble means (selected)")
    lines.append("")
    lines.append("| stage | metric | mean | range |")
    lines.append("|---|---|---|---|")
    for stage in ("stage_1_0", "stage_1_1", "stage_1_1_5", "stage_1_2"):
        for k, v in (metrics.get(stage) or {}).items():
            if isinstance(v, dict) and "mean" in v:
                lines.append(
                    f"| {stage} | `{k}` | {v.get('mean')} | {v.get('range')} |"
                )
    (iter_dir / "judge_report.md").write_text(
        "\n".join(lines), encoding="utf-8"
    )


def _git_commit(iter_dir: Path, iter_full: str, headline: str) -> None:
    _run(
        [
            "git", "add",
            str(iter_dir),
            str(EXPERIMENTS_DIR / "summary.md"),
        ]
    )
    _run(
        ["git", "commit", "-m", f"{iter_full}: {headline}"]
    )


# -- top-level ----------------------------------------------------------------

def main(argv: List[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--iter-id", required=True, help="e.g. 00, 01, 02")
    parser.add_argument("--slug", required=True, help="short identifier (snake_case)")
    parser.add_argument("--parent-iter", default="", help="e.g. iter_01_title_prompt_strict")
    parser.add_argument("--hypothesis-file", default="")
    parser.add_argument("--hypothesis-text", default="")
    parser.add_argument("--patch", default="")
    parser.add_argument("--n-records", type=int, default=50)
    parser.add_argument("--headline", default="", help="commit msg one-liner")
    parser.add_argument("--skip-pipeline", action="store_true", help="(debug) reuse existing output/")
    parser.add_argument("--skip-judge",    action="store_true", help="(debug) reuse existing judge_metrics.json")
    parser.add_argument("--skip-commit",   action="store_true")
    args = parser.parse_args(argv)

    iter_full = f"iter_{args.iter_id}_{args.slug}"
    iter_dir = _prepare_iter_dir(args.iter_id, args.slug, args.parent_iter or None)
    log_path = iter_dir / "run_log.txt"

    t0 = time.time()
    with log_path.open("a", encoding="utf-8") as log_fh:
        log_fh.write(f"\n\n=== iter_run.py {iter_full} @ {_now()} ===\n")

        _write_hypothesis(
            iter_dir,
            Path(args.hypothesis_file) if args.hypothesis_file else None,
            args.hypothesis_text or None,
        )
        if args.patch:
            _apply_patch(iter_dir, Path(args.patch), log_fh)

        if not args.skip_pipeline:
            _upload_pipeline_script(iter_dir, iter_full, log_fh)
            rc = _run_pipeline_remote(iter_full, args.n_records, log_fh)
            if rc != 0:
                log_fh.write(f"[abort] pipeline remote failed rc={rc}\n")
                return rc
            _pull_outputs(iter_dir, iter_full, log_fh)

        judge_metrics: Dict[str, Any] = {}
        if not args.skip_judge:
            rc = _run_tri_judge_remote(
                iter_full,
                run_id=iter_full,
                tag=iter_full,
                log_fh=log_fh,
            )
            if rc != 0:
                log_fh.write(f"[warn] tri_judge rc={rc} (continuing)\n")
            _pull_judge_artifacts(iter_dir, iter_full, log_fh)
            jm_path = iter_dir / "judge_metrics.json"
            if jm_path.exists():
                try:
                    judge_metrics = json.loads(jm_path.read_text(encoding="utf-8"))
                except Exception as exc:  # noqa: BLE001
                    log_fh.write(f"[warn] judge_metrics.json unreadable: {exc}\n")
        else:
            jm_path = iter_dir / "judge_metrics.json"
            if jm_path.exists():
                judge_metrics = json.loads(jm_path.read_text(encoding="utf-8"))

        quant_metrics = _run_quant_local(iter_dir, log_fh)

        metrics = _assemble_metrics_json(
            iter_dir=iter_dir,
            iter_full=iter_full,
            parent_iter=args.parent_iter or None,
            run_id=iter_full,
            tag=iter_full,
            judge_metrics=judge_metrics,
            quant_metrics=quant_metrics,
        )
        _write_judge_report_stub(iter_dir, metrics)
        _run_make_comparison(iter_dir, args.parent_iter or None, log_fh)

        duration = time.time() - t0
        log_fh.write(f"\n[iter_run] total duration: {duration:.1f}s\n")
        log_fh.write(f"[iter_run] promote={metrics['promote']}  "
                     f"high_variance={metrics['high_variance']}\n")

    if not args.skip_commit:
        headline = args.headline or (
            f"promote={metrics['promote']} leak={((metrics.get('stage_1_1') or {}).get('title_reasoning_leak_rate') or {}).get('mean')}"
        )
        try:
            _git_commit(iter_dir, iter_full, headline)
        except SystemExit:
            pass

    print(
        f"\n[iter_run] {iter_full} DONE. "
        f"promote={metrics['promote']} high_variance={metrics['high_variance']} "
        f"duration={time.time() - t0:.1f}s"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
