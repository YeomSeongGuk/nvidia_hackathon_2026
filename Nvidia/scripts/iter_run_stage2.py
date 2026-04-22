"""Sealed driver for ONE Stage-2 iteration of the PLAN.md loop.

Canonical entry point for a subagent to execute a Stage 2 iteration
end-to-end. Mirrors Stage 1's `scripts/iter_run.py` but:

  - operates on the 5-script Stage 2 pipeline (2.1 / 2.1.5 / 2.2 / 2.3 / 2.4)
  - uses a per-iter `pipeline_snapshot/` directory (PLAN §7) instead of a
    single pipeline_script.py
  - supports SD on/off via `--semdedup {off,<threshold>}`
  - supports Option A (single-instance on coupang, default) or Option B
    (phase-split: coupang vLLM + coupang2 embedding) via
    `--stage22-mode {full,phase_split}` — see PLAN §3b.

iter_00_baseline uses `--semdedup off --stage22-mode full`, which
collapses the 14-step flow to a Stage 1-style single-remote recipe:

    1. prepare experiments_stage2/iter_NN_<slug>/ locally
    2. hypothesis.md (from file / inline text / default)
    3. git apply --3way <patch>  (if given)
    4. build pipeline_snapshot/  (vendored copy of pipelines/stage_2_*.py)
    5. upload pinned Stage-1 input + pipeline_snapshot/ to coupang
    6. on coupang: run Stage 2.1 → 2.1.5 (pass-through) → 2.2 → 2.3 → 2.4
    7. pull 5 outputs + stage_2_1_5_stats.json back to local output/
    8. local tri_judge_run_stage2.py          (Friendli; 12 Friendli calls)
    9. local quant_stage2_report.py --mode iter
    10. assemble metrics.json (+ promote gate checks) / judge_report.md
    11. make_comparison.py vs parent's metrics.json
    12. git commit

Usage:
  python scripts/iter_run_stage2.py \\
      --iter-id 00 --slug baseline \\
      --parent-iter "" \\
      --hypothesis-text "baseline, no changes; frozen pipeline snapshot" \\
      --semdedup off --stage22-mode full \\
      --headline "baseline"
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


REPO_ROOT = Path(__file__).resolve().parent.parent
EXPERIMENTS_DIR = REPO_ROOT / "experiments_stage2"
SCRIPTS_DIR = REPO_ROOT / "scripts"
PINNED_INPUT = (
    EXPERIMENTS_DIR / "stage1_pinned" / "stage_1_2_processed.jsonl"
)

# Remote (Brev) conventions. Override via env vars if your setup differs.
COUPANG_HOST = os.environ.get("COUPANG_HOST", "coupang")
COUPANG2_HOST = os.environ.get("COUPANG2_HOST", "coupang2")
COUPANG_ROOT = os.environ.get(
    "COUPANG_STAGE2_ROOT", "/home/nvidia/experiments_data_stage2"
)
COUPANG2_ROOT = os.environ.get(
    "COUPANG2_STAGE2_ROOT", "/home/nvidia/experiments_data_stage2"
)
COUPANG_VENV_PY = os.environ.get(
    "COUPANG_VENV_PY", "/home/nvidia/coupang/.venv/bin/python"
)
COUPANG2_VENV_PY = os.environ.get(
    "COUPANG2_VENV_PY", "/home/nvidia/coupang2/.venv/bin/python"
)
COUPANG_PIPELINES_DIR = os.environ.get(
    "COUPANG_PIPELINES_DIR", "/home/nvidia/stage2_work"
)
COUPANG2_PIPELINES_DIR = os.environ.get(
    "COUPANG2_PIPELINES_DIR", "/home/nvidia/stage2_work"
)

STAGE2_SNAPSHOT_FILES = (
    "stage_2_1_extract.py",
    "stage_2_1_5_semdedup.py",
    "stage_2_2_canonicalize.py",
    "stage_2_3_aggregate.py",
    "stage_2_4_expand.py",
)

FIVE_OUTPUT_FILES = (
    "stage_2_1_extracted.jsonl",
    "stage_2_1_5_deduped.jsonl",
    "stage_2_1_5_stats.json",
    "stage_2_2_clusters.jsonl",
    "stage_2_3_analyzed_intents.jsonl",
    "stage_2_4_expanded_intents.jsonl",
)


# ---------------------------------------------------------------------------
# utils
# ---------------------------------------------------------------------------

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


def _run(
    cmd: List[str],
    log_fh=None,
    check: bool = False,
    env: Optional[Dict[str, str]] = None,
) -> int:
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


def _run_with_retry(
    cmd: List[str],
    log_fh=None,
    *,
    attempts: int = 3,
    backoff_sec: int = 3,
    check: bool = False,
    env: Optional[Dict[str, str]] = None,
) -> int:
    """Run cmd with up to `attempts` tries on non-zero exit.

    Used for every brev copy / brev exec call in this driver: the brev
    control plane flakes intermittently ('context deadline exceeded',
    'not_found: not found') and retry-with-backoff almost always
    resolves it. Raises SystemExit only if `check=True` and all
    attempts failed.
    """
    rc = -1
    for i in range(attempts):
        rc = _run(cmd, log_fh=log_fh, env=env, check=False)
        if rc == 0:
            return 0
        if i < attempts - 1:
            msg = (
                f"  [retry] attempt {i + 1}/{attempts} failed rc={rc}; "
                f"sleeping {backoff_sec}s before retry"
            )
            print(msg, file=sys.stderr, flush=True)
            if log_fh:
                log_fh.write(msg + "\n")
                log_fh.flush()
            time.sleep(backoff_sec)
    if check and rc != 0:
        raise SystemExit(
            f"command failed rc={rc} after {attempts} attempts: {cmd}"
        )
    return rc


def _brev_exec(host: str, remote_cmd: str, log_fh=None) -> int:
    return _run_with_retry(
        ["brev", "exec", host, remote_cmd], log_fh=log_fh
    )


# ---------------------------------------------------------------------------
# steps
# ---------------------------------------------------------------------------

def _prepare_iter_dir(
    iter_id: str, slug: str, parent_iter: Optional[str]
) -> Path:
    iter_dir = EXPERIMENTS_DIR / f"iter_{iter_id}_{slug}"
    iter_dir.mkdir(parents=True, exist_ok=True)
    (iter_dir / "output").mkdir(exist_ok=True)
    (iter_dir / "judge_raw").mkdir(exist_ok=True)
    (iter_dir / "pipeline_snapshot").mkdir(exist_ok=True)
    return iter_dir


def _write_hypothesis(
    iter_dir: Path, hypothesis_path: Optional[Path], text: Optional[str]
) -> None:
    out = iter_dir / "hypothesis.md"
    if hypothesis_path and hypothesis_path.exists():
        try:
            same = hypothesis_path.resolve() == out.resolve()
        except FileNotFoundError:
            same = False
        if not same:
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
    dst = iter_dir / "patch.diff"
    shutil.copy2(patch_path, dst)
    rc = _run(
        ["git", "apply", "--3way", "--whitespace=nowarn", str(dst)],
        log_fh=log_fh,
    )
    if rc != 0:
        raise SystemExit(f"git apply failed rc={rc}")


def _build_pipeline_snapshot(iter_dir: Path) -> None:
    """Copy the five Stage 2 entry-point scripts into iter/pipeline_snapshot/
    so the exact code that produced the iter's output is checked in alongside
    the metrics. Keeps reviewers self-sufficient without pinning pipelines/*.
    """
    snap_dir = iter_dir / "pipeline_snapshot"
    snap_dir.mkdir(parents=True, exist_ok=True)
    for name in STAGE2_SNAPSHOT_FILES:
        src = REPO_ROOT / "pipelines" / name
        if not src.exists():
            raise SystemExit(f"pipelines/{name} not found; cannot snapshot")
        shutil.copy2(src, snap_dir / name)


def _upload_iter_scaffold(
    iter_full: str,
    iter_dir: Path,
    log_fh,
) -> None:
    """Upload pinned input + the five pipeline scripts + the remote-exec'd
    tri_judge driver to coupang.

    Overlays the iter's pipeline_snapshot/ (which may have been patched)
    on top of whatever is already in $COUPANG_PIPELINES_DIR/pipelines/.
    Also overlays scripts/tri_judge_run_stage2.py so the judge step
    (run remotely for Friendli-env parity with Stage 1) uses the Stage 2
    driver even if the remote checkout is stale.
    """
    _brev_exec(
        COUPANG_HOST,
        f"mkdir -p {COUPANG_ROOT}/{iter_full}/data/stage_1_2 "
        f"{COUPANG_ROOT}/{iter_full}/output "
        f"{COUPANG_ROOT}/{iter_full}/data_eval "
        f"{COUPANG_ROOT}/{iter_full}/snapshot "
        f"{COUPANG_PIPELINES_DIR}/scripts "
        f"{COUPANG_PIPELINES_DIR}/pipelines",
        log_fh=log_fh,
    )
    # pinned input
    _run_with_retry(
        [
            "brev", "copy",
            str(PINNED_INPUT),
            f"{COUPANG_HOST}:{COUPANG_ROOT}/{iter_full}/data/stage_1_2/stage_1_2_processed.jsonl",
        ],
        log_fh=log_fh,
        check=True,
    )
    # snapshot scripts (5 pipeline entry points)
    snap_dir = iter_dir / "pipeline_snapshot"
    for name in STAGE2_SNAPSHOT_FILES:
        _run_with_retry(
            [
                "brev", "copy",
                str(snap_dir / name),
                f"{COUPANG_HOST}:{COUPANG_ROOT}/{iter_full}/snapshot/{name}",
            ],
            log_fh=log_fh,
            check=True,
        )
    # Push the tri_judge Stage-2 driver AND the new stage_2_1_5_semdedup
    # module directly to the remote checkout so remote invocation works
    # even when the coupang box is behind main.
    remote_tri = f"{COUPANG_PIPELINES_DIR}/scripts/tri_judge_run_stage2.py"
    _run_with_retry(
        [
            "brev", "copy",
            str(SCRIPTS_DIR / "tri_judge_run_stage2.py"),
            f"{COUPANG_HOST}:{remote_tri}",
        ],
        log_fh=log_fh,
        check=True,
    )
    remote_semdedup = (
        f"{COUPANG_PIPELINES_DIR}/pipelines/stage_2_1_5_semdedup.py"
    )
    _run_with_retry(
        [
            "brev", "copy",
            str(REPO_ROOT / "pipelines" / "stage_2_1_5_semdedup.py"),
            f"{COUPANG_HOST}:{remote_semdedup}",
        ],
        log_fh=log_fh,
        check=True,
    )


def _remote_pipeline_cmd(
    iter_full: str,
    semdedup: str,  # "off" or a float string (as a threshold)
    stage22_mode: str,  # "full" only for now on the driver side
    provider: str,  # "vllm"
) -> str:
    """Build the coupang-side bash one-liner for Option A (single-instance).

    Executes Stage 2.1 → 2.1.5 (pass-through or active) → 2.2 (full)
    → 2.3 → 2.4 on the vLLM-backed coupang instance. Copies the five
    outputs into $COUPANG_ROOT/$iter_full/output/ at the end.
    """
    sd_cmd = (
        "--off"
        if semdedup == "off"
        else f"--threshold {float(semdedup)}"
    )
    # stage 2.2: --stage full is default; --refine --cross-merge are
    # canonical Stage 2 settings from the main branch.
    return (
        f"set -euo pipefail; "
        f"export LLM_PROVIDER={provider}; "
        f"export VLLM_BASE_URL=http://localhost:5000/v1; "
        f"export VLLM_MODEL=nemotron; "
        f"export LLM_EXTRA_BODY='{{\"chat_template_kwargs\":{{\"enable_thinking\":false}}}}'; "
        f"export STAGE_DATA_ROOT={COUPANG_ROOT}/{iter_full}/data; "
        f"cd {COUPANG_PIPELINES_DIR} && "
        # Overlay the iter's snapshot scripts on top of pipelines/ for this run.
        f"cp {COUPANG_ROOT}/{iter_full}/snapshot/stage_2_1_extract.py pipelines/stage_2_1_extract.py && "
        f"cp {COUPANG_ROOT}/{iter_full}/snapshot/stage_2_1_5_semdedup.py pipelines/stage_2_1_5_semdedup.py && "
        f"cp {COUPANG_ROOT}/{iter_full}/snapshot/stage_2_2_canonicalize.py pipelines/stage_2_2_canonicalize.py && "
        f"cp {COUPANG_ROOT}/{iter_full}/snapshot/stage_2_3_aggregate.py pipelines/stage_2_3_aggregate.py && "
        f"cp {COUPANG_ROOT}/{iter_full}/snapshot/stage_2_4_expand.py pipelines/stage_2_4_expand.py && "
        # Stage 2.1
        f"PYTHONPATH=. {COUPANG_VENV_PY} -m pipelines.stage_2_1_extract "
        f"  --input  $STAGE_DATA_ROOT/stage_1_2 "
        f"  --output $STAGE_DATA_ROOT/stage_2_1_extracted.jsonl "
        f"  --provider {provider} && "
        # Stage 2.1.5
        f"PYTHONPATH=. {COUPANG_VENV_PY} -m pipelines.stage_2_1_5_semdedup "
        f"  {sd_cmd} "
        f"  --input  $STAGE_DATA_ROOT/stage_2_1_extracted.jsonl "
        f"  --output $STAGE_DATA_ROOT/stage_2_1_5_deduped.jsonl && "
        # Stage 2.2 full
        f"PYTHONPATH=. {COUPANG_VENV_PY} -m pipelines.stage_2_2_canonicalize "
        f"  --stage full --refine --cross-merge "
        f"  --input  $STAGE_DATA_ROOT/stage_2_1_5_deduped.jsonl "
        f"  --output $STAGE_DATA_ROOT/stage_2_2_clusters.jsonl "
        f"  --provider {provider} && "
        # Stage 2.3
        f"PYTHONPATH=. {COUPANG_VENV_PY} -m pipelines.stage_2_3_aggregate "
        f"  --stage1 $STAGE_DATA_ROOT/stage_2_1_5_deduped.jsonl "
        f"  --stage2 $STAGE_DATA_ROOT/stage_2_2_clusters.jsonl "
        f"  --output $STAGE_DATA_ROOT/stage_2_3_analyzed_intents.jsonl && "
        # Stage 2.4
        f"PYTHONPATH=. {COUPANG_VENV_PY} -m pipelines.stage_2_4_expand "
        f"  --force-fallback "
        f"  --input  $STAGE_DATA_ROOT/stage_2_3_analyzed_intents.jsonl "
        f"  --output $STAGE_DATA_ROOT/stage_2_4_expanded_intents.jsonl "
        f"  --provider {provider} && "
        # Move outputs into a single folder for pulling back
        f"mkdir -p {COUPANG_ROOT}/{iter_full}/output && "
        f"cp $STAGE_DATA_ROOT/stage_2_1_extracted.jsonl       {COUPANG_ROOT}/{iter_full}/output/ && "
        f"cp $STAGE_DATA_ROOT/stage_2_1_5_deduped.jsonl       {COUPANG_ROOT}/{iter_full}/output/ && "
        f"(cp $STAGE_DATA_ROOT/stage_2_1_5_deduped_stats.json {COUPANG_ROOT}/{iter_full}/output/stage_2_1_5_stats.json 2>/dev/null || "
        f" cp $STAGE_DATA_ROOT/stage_2_1_5_stats.json         {COUPANG_ROOT}/{iter_full}/output/ 2>/dev/null || true) && "
        f"cp $STAGE_DATA_ROOT/stage_2_2_clusters.jsonl        {COUPANG_ROOT}/{iter_full}/output/ && "
        f"cp $STAGE_DATA_ROOT/stage_2_3_analyzed_intents.jsonl {COUPANG_ROOT}/{iter_full}/output/ && "
        f"cp $STAGE_DATA_ROOT/stage_2_4_expanded_intents.jsonl {COUPANG_ROOT}/{iter_full}/output/ && "
        f"wc -l {COUPANG_ROOT}/{iter_full}/output/*.jsonl"
    )


def _run_pipeline_remote(
    iter_full: str,
    semdedup: str,
    stage22_mode: str,
    provider: str,
    log_fh,
) -> int:
    remote = _remote_pipeline_cmd(
        iter_full=iter_full,
        semdedup=semdedup,
        stage22_mode=stage22_mode,
        provider=provider,
    )
    remote_full = (
        f"{remote} 2>&1 | tee {COUPANG_ROOT}/{iter_full}/run_pipeline.log"
    )
    return _brev_exec(COUPANG_HOST, remote_full, log_fh=log_fh)


def _pull_outputs(iter_dir: Path, iter_full: str, log_fh) -> None:
    dst = iter_dir / "output"
    dst.mkdir(exist_ok=True)
    for fname in FIVE_OUTPUT_FILES:
        rc = -1
        for attempt in range(3):
            rc = _run(
                [
                    "brev", "copy",
                    f"{COUPANG_HOST}:{COUPANG_ROOT}/{iter_full}/output/{fname}",
                    str(dst / fname),
                ],
                log_fh=log_fh,
            )
            if rc == 0 and (dst / fname).exists():
                break
            time.sleep(2)
        if rc != 0:
            print(
                f"  [warn] failed to pull {fname} after 3 attempts (rc={rc})",
                file=sys.stderr,
                flush=True,
            )
    # pull pipeline log for the record
    _run_with_retry(
        [
            "brev", "copy",
            f"{COUPANG_HOST}:{COUPANG_ROOT}/{iter_full}/run_pipeline.log",
            str(iter_dir / "run_pipeline_remote.log"),
        ],
        log_fh=log_fh,
    )


def _run_tri_judge_remote(
    iter_full: str, run_id: str, tag: str, log_fh
) -> int:
    """Run tri_judge_run_stage2.py on coupang (Friendli + env already there).

    We keep Friendli calls on coupang for parity with Stage 1 iter_run.py:
    the coupang box already has a Friendli key in its env; our local .env
    typically only has NVIDIA_API_KEY for smoke tests.
    """
    remote = (
        f"set -euo pipefail; "
        f"export STAGE_DATA_ROOT={COUPANG_ROOT}/{iter_full}/data_eval; "
        f"export LLM_EXTRA_BODY='{{\"chat_template_kwargs\":{{\"enable_thinking\":false}}}}'; "
        f"mkdir -p $STAGE_DATA_ROOT; "
        f"cd {COUPANG_PIPELINES_DIR} && "
        # Make sure the judge modules on coupang are the ones we intend
        # to use. (tri_judge_run_stage2.py itself + its child judges live
        # on coupang's stage2_work checkout; a snapshot copy is NOT needed
        # here since we don't touch pipelines/eval/ in iter_00.)
        f"PYTHONPATH=. {COUPANG_VENV_PY} scripts/tri_judge_run_stage2.py "
        f"  --output-dir    {COUPANG_ROOT}/{iter_full}/output "
        f"  --curated       {COUPANG_ROOT}/{iter_full}/data/stage_1_2/stage_1_2_processed.jsonl "
        f"  --stage-data-root $STAGE_DATA_ROOT "
        f"  --judge-raw-dir {COUPANG_ROOT}/{iter_full}/judge_raw "
        f"  --metrics-out   {COUPANG_ROOT}/{iter_full}/judge_metrics.json "
        f"  --provider friendli "
        f"  --run-id {run_id} --tag {tag} "
        f"  --skip-on-error 2>&1 | tee -a {COUPANG_ROOT}/{iter_full}/run_pipeline.log"
    )
    return _brev_exec(COUPANG_HOST, remote, log_fh=log_fh)


def _pull_judge_artifacts(iter_dir: Path, iter_full: str, log_fh) -> None:
    """After remote tri-judge finishes, pull judge_metrics.json + judge_raw/
    back to local experiments_stage2/iter_NN/ .

    `brev copy coupang:.../judge_raw <iter_dir>/judge_raw` when the local
    empty `judge_raw/` already exists lands files at
    `<iter_dir>/judge_raw/judge_raw/` (one level too deep) in the current
    brev CLI (0.6.x). We remove the empty dir first and pull into the
    iter_dir so the source directory name ("judge_raw") lands as the
    top-level target.
    """
    _run_with_retry(
        [
            "brev", "copy",
            f"{COUPANG_HOST}:{COUPANG_ROOT}/{iter_full}/judge_metrics.json",
            str(iter_dir / "judge_metrics.json"),
        ],
        log_fh=log_fh,
    )
    # Nuke the pre-created empty judge_raw/ so brev copy does not nest.
    shutil.rmtree(iter_dir / "judge_raw", ignore_errors=True)
    _run_with_retry(
        [
            "brev", "copy",
            f"{COUPANG_HOST}:{COUPANG_ROOT}/{iter_full}/judge_raw",
            str(iter_dir),
        ],
        log_fh=log_fh,
    )


def _run_quant_local(iter_dir: Path, log_fh) -> Dict[str, Any]:
    out_json = iter_dir / "quant_metrics.json"
    rc = _run(
        [
            sys.executable, str(SCRIPTS_DIR / "quant_stage2_report.py"),
            "--mode", "iter",
            "--output-dir", str(iter_dir / "output"),
            "--json-out",   str(out_json),
            "--md-out",     str(iter_dir / "quant_report.md"),
        ],
        log_fh=log_fh,
    )
    if rc != 0:
        print(f"  [warn] quant probe failed rc={rc}", file=sys.stderr)
        return {}
    try:
        return json.loads(out_json.read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001
        print(f"  [warn] quant JSON unreadable: {exc}", file=sys.stderr)
        return {}


def _decide_promote(j: Dict[str, Any], q: Dict[str, Any]) -> Dict[str, Any]:
    """PLAN §6 promotion bar check (tri-judge mean + quant probes)."""
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
        # 2.1
        "stage_2_1.avg_intent_groundedness_ge_4.0":
            (_mean(["stage_2_1", "avg_intent_groundedness"]) or 0) >= 4.0,
        "stage_2_1.intent_type_valid_rate_ge_0.90":
            (_mean(["stage_2_1", "intent_type_valid_rate"]) or 0) >= 0.90,
        "stage_2_1.attribute_concrete_material_ge_0.80":
            (_mean(["stage_2_1", "attribute_concrete_rate_material"]) or 0) >= 0.80,
        # 2.2
        "stage_2_2.coherent_rate_ge_0.85":
            (_mean(["stage_2_2", "coherent_rate"]) or 0) >= 0.85,
        "stage_2_2.avg_canonical_fit_ge_4.0":
            (_mean(["stage_2_2", "avg_canonical_fit"]) or 0) >= 4.0,
        "stage_2_2.non_korean_canonical_count_eq_0":
            (_mean(["stage_2_2", "non_korean_canonical_count"]) or 0) == 0,
        "stage_2_2.duplicate_pairs_found_le_1":
            (_mean(["stage_2_2", "duplicate_pairs_found"]) or 0) <= 1,
        "stage_2_2.canonical_non_fashion_rate_le_0.05":
            ((q.get("stage_2_2") or {}).get("canonical_non_fashion_rate") or 0) <= 0.05,
        # 2.3
        "stage_2_3.avg_overall_usefulness_ge_4.0":
            (_mean(["stage_2_3", "avg_overall_usefulness"]) or 0) >= 4.0,
        "stage_2_3.attr_fits_intent_rate_ge_0.85":
            (_mean(["stage_2_3", "attr_fits_intent_rate"]) or 0) >= 0.85,
        "stage_2_3.duplicate_value_count_le_2":
            ((q.get("stage_2_3") or {}).get("duplicate_value_count") or 0) <= 2,
        # 2.4
        "stage_2_4.avg_overall_usefulness_ge_4.0":
            (_mean(["stage_2_4", "avg_overall_usefulness"]) or 0) >= 4.0,
        "stage_2_4.per_query_natural_rate_ge_0.90":
            (_mean(["stage_2_4", "per_query_natural_rate"]) or 0) >= 0.90,
        "stage_2_4.avg_query_diversity_ge_3.5":
            (_mean(["stage_2_4", "avg_query_diversity"]) or 0) >= 3.5,
        "stage_2_4.canonical_repeat_rate_le_0.10":
            ((q.get("stage_2_4") or {}).get("canonical_repeat_rate") or 0) <= 0.10,
        "stage_2_4.garbled_count_eq_0":
            ((q.get("stage_2_4") or {}).get("garbled_count") or 0) == 0,
    }
    return {"promote": all(checks.values()), "checks": checks}


def _high_variance(j: Dict[str, Any]) -> bool:
    """Mark as HIGH_VARIANCE if any stage's headline range > 0.15."""
    heads = [
        ("stage_2_1", "avg_intent_groundedness"),
        ("stage_2_2", "coherent_rate"),
        ("stage_2_3", "avg_overall_usefulness"),
        ("stage_2_4", "avg_overall_usefulness"),
    ]
    for stage, metric in heads:
        node = (j.get(stage) or {}).get(metric)
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
    semdedup: str,
    stage22_mode: str,
) -> Dict[str, Any]:
    hashes = {
        f: _sha256(iter_dir / "output" / f) for f in FIVE_OUTPUT_FILES
    }
    promote = _decide_promote(
        judge_metrics.get("ensemble") or {}, quant_metrics
    )
    hi_var = _high_variance(judge_metrics.get("ensemble") or {})

    metrics = {
        "iter_id": iter_full,
        "parent_iter": parent_iter or "",
        "timestamp": _now(),
        "run_id": run_id,
        "tag": tag,
        "semdedup": semdedup,
        "stage22_mode": stage22_mode,
        "output_hashes": hashes,
        "stage_2_1":   (judge_metrics.get("ensemble") or {}).get("stage_2_1") or {},
        "stage_2_2":   (judge_metrics.get("ensemble") or {}).get("stage_2_2") or {},
        "stage_2_3":   (judge_metrics.get("ensemble") or {}).get("stage_2_3") or {},
        "stage_2_4":   (judge_metrics.get("ensemble") or {}).get("stage_2_4") or {},
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
    lines = [
        f"# Judge ensemble report for {metrics['iter_id']}",
        "",
        f"- run_id: `{metrics['run_id']}`",
        f"- semdedup: {metrics.get('semdedup')}",
        f"- stage22_mode: {metrics.get('stage22_mode')}",
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
    lines.append("## Per-stage ensemble means")
    lines.append("")
    lines.append("| stage | metric | mean | range |")
    lines.append("|---|---|---|---|")
    for stage in ("stage_2_1", "stage_2_2", "stage_2_3", "stage_2_4"):
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
        [
            "git", "commit",
            "-m", f"{iter_full}: {headline}",
        ]
    )


# ---------------------------------------------------------------------------
# top-level
# ---------------------------------------------------------------------------

def main(argv: List[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--iter-id", required=True, help="e.g. 00, 01, 02")
    parser.add_argument("--slug", required=True, help="short identifier (snake_case)")
    parser.add_argument("--parent-iter", default="", help="e.g. iter_00_baseline")
    parser.add_argument("--hypothesis-file", default="")
    parser.add_argument("--hypothesis-text", default="")
    parser.add_argument("--patch", default="")
    parser.add_argument(
        "--semdedup",
        default="off",
        help="'off' (pass-through) or a float threshold (e.g. 0.90)",
    )
    parser.add_argument(
        "--stage22-mode",
        choices=["full", "phase_split", "coupang2_direct"],
        default="full",
        help=(
            "full = Option A single-instance (default; what iter_00 uses).\n"
            "phase_split = Option B (embed on coupang2 → LLM on coupang). "
            "Not yet supported by this driver.\n"
            "coupang2_direct = Option A but on coupang2; not yet supported."
        ),
    )
    parser.add_argument("--provider", default="vllm")
    parser.add_argument("--headline", default="", help="commit msg one-liner")
    parser.add_argument("--skip-pipeline", action="store_true")
    parser.add_argument("--skip-judge", action="store_true")
    parser.add_argument("--skip-quant", action="store_true")
    parser.add_argument("--skip-commit", action="store_true")
    args = parser.parse_args(argv)

    if args.stage22_mode != "full":
        raise SystemExit(
            f"--stage22-mode {args.stage22_mode} not yet wired in the "
            f"driver. Use --stage22-mode full for iter_00_baseline."
        )

    iter_full = f"iter_{args.iter_id}_{args.slug}"
    iter_dir = _prepare_iter_dir(
        args.iter_id, args.slug, args.parent_iter or None
    )
    log_path = iter_dir / "run_log.txt"

    t0 = time.time()
    with log_path.open("a", encoding="utf-8") as log_fh:
        log_fh.write(f"\n# --- iter_run_stage2 @ {_now()} ---\n")
        log_fh.write(f"# iter={iter_full} parent={args.parent_iter}\n")
        log_fh.write(f"# semdedup={args.semdedup} stage22_mode={args.stage22_mode}\n")
        log_fh.write(f"# pinned input sha256={_sha256(PINNED_INPUT)}\n\n")

        # step 2 / 3 — hypothesis + patch
        _write_hypothesis(
            iter_dir,
            Path(args.hypothesis_file) if args.hypothesis_file else None,
            args.hypothesis_text or None,
        )
        _apply_patch(iter_dir, Path(args.patch) if args.patch else None, log_fh)

        # step 4 — build pipeline_snapshot/
        _build_pipeline_snapshot(iter_dir)

        # steps 5-7 — upload + remote pipeline + pull
        if not args.skip_pipeline:
            _upload_iter_scaffold(iter_full, iter_dir, log_fh=log_fh)
            rc = _run_pipeline_remote(
                iter_full=iter_full,
                semdedup=args.semdedup,
                stage22_mode=args.stage22_mode,
                provider=args.provider,
                log_fh=log_fh,
            )
            if rc != 0:
                raise SystemExit(f"remote pipeline failed rc={rc}")
            _pull_outputs(iter_dir, iter_full, log_fh=log_fh)

        # step 8 — tri-judge (remote on coupang; Friendli + env live there)
        run_id = iter_full
        tag = iter_full
        if not args.skip_judge:
            rc = _run_tri_judge_remote(iter_full, run_id, tag, log_fh)
            if rc != 0:
                print(
                    f"  [warn] tri_judge_run_stage2 rc={rc}; continuing",
                    file=sys.stderr,
                )
            _pull_judge_artifacts(iter_dir, iter_full, log_fh=log_fh)

        # step 9 — quant
        quant = (
            _run_quant_local(iter_dir, log_fh)
            if not args.skip_quant else {}
        )

        # step 10-11 — metrics.json + comparison + reports
        judge_metrics: Dict[str, Any] = {}
        judge_path = iter_dir / "judge_metrics.json"
        if judge_path.exists():
            try:
                judge_metrics = json.loads(judge_path.read_text(encoding="utf-8"))
            except Exception as exc:
                print(
                    f"  [warn] judge_metrics.json unreadable: {exc}",
                    file=sys.stderr,
                )

        metrics = _assemble_metrics_json(
            iter_dir=iter_dir,
            iter_full=iter_full,
            parent_iter=args.parent_iter or None,
            run_id=run_id,
            tag=tag,
            judge_metrics=judge_metrics,
            quant_metrics=quant,
            semdedup=args.semdedup,
            stage22_mode=args.stage22_mode,
        )
        _write_judge_report_stub(iter_dir, metrics)
        _run_make_comparison(
            iter_dir, args.parent_iter or None, log_fh=log_fh
        )

        # step 12 — write DONE marker BEFORE commit so it lands in the
        # commit alongside metrics.json / judge_report.md / comparison.md.
        elapsed = time.time() - t0
        log_fh.write(
            f"\n# --- iter_run_stage2 done in {elapsed:.1f}s ---\n"
        )
        log_fh.flush()

        if not args.skip_commit:
            _git_commit(
                iter_dir=iter_dir,
                iter_full=iter_full,
                headline=args.headline or f"stage2 {iter_full}",
            )

        print(
            f"\n[iter_run_stage2] DONE iter={iter_full} "
            f"promote={metrics.get('promote')} "
            f"high_variance={metrics.get('high_variance')} "
            f"duration={elapsed:.1f}s",
            flush=True,
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
