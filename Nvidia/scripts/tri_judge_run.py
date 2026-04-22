"""Tri-judge ensemble driver for Stage 1.

For a given iteration's `output/` directory, runs every Stage-1 judge
(stage_1_0 via `stage_1_2_judge`, stage_1_1, stage_1_1_5, stage_1_2)
once for each of the 3 Friendli models:

  - zai-org/GLM-5.1
  - deepseek-ai/DeepSeek-V3.2
  - Qwen/Qwen3-235B-A22B-Instruct-2507

Scheduling:
- The 12 `(stage, judge_model)` pairs are submitted to a thread pool
  with `--max-workers` (default 4) concurrency. Each worker spawns a
  child `python -m pipelines.eval.stage_X_judge` process; the child's
  summary row append is atomic (Linux `O_APPEND` via Python `"a"`
  mode), so parallel appends to the shared `summary.jsonl` do not
  interleave.
- Output is collected after the whole pool drains; each (stage, alias)
  judge.jsonl is copied to `--judge-raw-dir/<stage>__<alias>.jsonl`.

After all 12 runs, merges the per-judge summary rows into a single
`judge_metrics.json` with `{glm, deepseek, qwen3, mean, range}` per
metric, plus `agreement_approx` for boolean metrics.

Usage:
  python scripts/tri_judge_run.py \\
      --output-dir    experiments/iter_00_baseline/output \\
      --judge-raw-dir experiments/iter_00_baseline/judge_raw \\
      --metrics-out   experiments/iter_00_baseline/judge_metrics.json \\
      --tag iter_00_baseline \\
      --run-id iter_00_baseline \\
      --max-workers 4
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import statistics
import subprocess
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple


# Three judges. Short alias is used in filenames and in metrics keys.
JUDGES: List[Dict[str, str]] = [
    {"alias": "glm",      "model": "zai-org/GLM-5.1"},
    {"alias": "deepseek", "model": "deepseek-ai/DeepSeek-V3.2"},
    {"alias": "qwen3",    "model": "Qwen/Qwen3-235B-A22B-Instruct-2507"},
]


STAGE_INPUT_FILE = {
    # (stage, input filename inside --output-dir)
    "stage_1_0":   "stage_1_0_seed.jsonl",
    "stage_1_1":   "stage_1_1_synthetic.jsonl",
    "stage_1_2":   "stage_1_2_processed.jsonl",
}

# stage_1_1_5 needs BOTH the before (1.1) and the after (1.1.5) files.
# Handled separately below.


# Metrics whose values are booleans-encoded-as-rates (0-1). We compute
# `agreement_rate` on them: fraction of records where all three judges
# agreed on the same boolean. Approximated at the aggregate level using
# the absolute difference between judge rates.
_BOOLEAN_METRICS = {
    # Stage 1.0 / 1.2 share rubric
    "fashion_rate", "has_tpo_rate", "pii_rate",
    # Stage 1.1
    "title_within_spec_rate", "title_format_ok_rate",
    "title_reasoning_leak_rate", "raw_text_within_spec_rate",
    "has_tpo_rate", "rating_sentiment_consistent_rate",
}

_PRINT_LOCK = threading.Lock()


def _log(msg: str) -> None:
    with _PRINT_LOCK:
        print(msg, flush=True)


def _run(argv: List[str], tag: str = "") -> int:
    """Run a subcommand, buffer output, print once (so parallel pool logs
    stay readable)."""
    _log(f"[{tag}] $ {' '.join(argv)}")
    # Children use `python -m pipelines.eval.<X>`; they need the current
    # working dir (which has `pipelines/`) on PYTHONPATH. Propagate it
    # explicitly since we pass capture_output=True (default env inherits
    # os.environ but not shell-local `PYTHONPATH=.` inline assignments).
    env = os.environ.copy()
    cwd = os.getcwd()
    existing = env.get("PYTHONPATH", "")
    if cwd not in existing.split(":"):
        env["PYTHONPATH"] = (cwd + ":" + existing).rstrip(":")
    proc = subprocess.run(argv, capture_output=True, text=True, env=env)
    lines: List[str] = []
    if proc.stdout:
        lines += proc.stdout.rstrip().splitlines()
    if proc.stderr:
        lines += [f"(stderr) {ln}" for ln in proc.stderr.rstrip().splitlines()]
    if lines:
        with _PRINT_LOCK:
            print(f"--- [{tag}] begin ---", flush=True)
            for ln in lines[-80:]:     # last 80 lines is plenty
                print(ln, flush=True)
            print(f"--- [{tag}] end rc={proc.returncode} ---", flush=True)
    return proc.returncode


def _build_child_argv(
    stage: str,
    input_args: List[str],
    judge_alias: str,
    judge_model: str,
    provider: str,
    run_id: str,
    tag: str,
    extra: Optional[List[str]] = None,
) -> List[str]:
    if stage == "stage_1_0":
        module = "pipelines.eval.stage_1_2_judge"
        # stage_1_2_judge hard-codes STAGE="stage_1_2" and appends to its
        # own summary.jsonl. Pass --stage-override so Stage 1.0 output
        # lands in $STAGE_DATA_ROOT/stage_1_0/eval/ (where this driver's
        # _copy_judge_raw and _read_summary_row look for it).
        extra = [*(extra or []), "--stage-override", "stage_1_0"]
    elif stage == "stage_1_1":
        module = "pipelines.eval.stage_1_1_judge"
    elif stage == "stage_1_1_5":
        module = "pipelines.eval.stage_1_1_5_judge"
    elif stage == "stage_1_2":
        module = "pipelines.eval.stage_1_2_judge"
    else:
        raise ValueError(f"unknown stage {stage!r}")

    argv = [
        sys.executable, "-m", module,
        "--provider", provider,
        "--judge-model", judge_model,
        "--run-id", f"{run_id}__{judge_alias}",
        "--tag", f"{tag}__{judge_alias}",
    ]
    argv += input_args
    if extra:
        argv += extra
    return argv


def _copy_judge_raw(
    stage: str, run_id: str, judge_alias: str,
    stage_data_root: Path, judge_raw_dir: Path,
) -> None:
    """Copy judge.jsonl from $STAGE_DATA_ROOT/<stage>/eval/runs/<run_id>__<alias>/judge.jsonl
    to <judge_raw_dir>/<stage>__<alias>.jsonl."""
    src = stage_data_root / stage / "eval" / "runs" / f"{run_id}__{judge_alias}" / "judge.jsonl"
    dst = judge_raw_dir / f"{stage}__{judge_alias}.jsonl"
    if src.exists():
        judge_raw_dir.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(src, dst)
    else:
        _log(f"  [warn] judge raw not found: {src}")


def _read_summary_row(
    stage: str, run_id: str, judge_alias: str,
    stage_data_root: Path,
) -> Optional[Dict[str, Any]]:
    """Return the per-judge summary row with matching run_id from
    $STAGE_DATA_ROOT/<stage>/eval/summary.jsonl."""
    path = stage_data_root / stage / "eval" / "summary.jsonl"
    if not path.exists():
        return None
    wanted = f"{run_id}__{judge_alias}"
    last_match: Optional[Dict[str, Any]] = None
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            obj = json.loads(line)
        except json.JSONDecodeError:
            continue
        if obj.get("run_id") == wanted:
            last_match = obj
    return last_match


def _merge_ensemble(
    stage: str, rows_by_alias: Dict[str, Optional[Dict[str, Any]]]
) -> Dict[str, Any]:
    """Combine three judge summary dicts into ensemble metrics."""
    numeric_keys: set[str] = set()
    for row in rows_by_alias.values():
        if not row:
            continue
        for k, v in row.items():
            if isinstance(v, (int, float)) and k not in (
                "n_evaluated", "n_clusters", "n_intents",
                "dedup_in_count", "dedup_out_count", "dedup_miss_count",
                "largest_miss_cluster_size", "duration_sec",
            ):
                numeric_keys.add(k)

    out: Dict[str, Any] = {}
    for k in sorted(numeric_keys):
        values: Dict[str, float] = {}
        for alias, row in rows_by_alias.items():
            if not row or k not in row:
                continue
            v = row[k]
            if v is None:
                continue
            try:
                values[alias] = float(v)
            except (TypeError, ValueError):
                continue
        mean = statistics.mean(values.values()) if values else None
        rng = (max(values.values()) - min(values.values())) if len(values) >= 2 else None
        entry: Dict[str, Any] = {"mean": round(mean, 3) if mean is not None else None}
        for alias in ("glm", "deepseek", "qwen3"):
            entry[alias] = round(values[alias], 3) if alias in values else None
        entry["range"] = round(rng, 3) if rng is not None else None
        if k in _BOOLEAN_METRICS and rng is not None:
            entry["agreement_approx"] = round(1.0 - rng, 3)
        out[k] = entry

    for k in ("n_evaluated", "n_clusters", "n_intents",
              "dedup_in_count", "dedup_out_count",
              "dedup_miss_count", "largest_miss_cluster_size"):
        for alias, row in rows_by_alias.items():
            if row and k in row:
                out[k] = row[k]
                break

    fm_aggregate: Dict[str, int] = {}
    for row in rows_by_alias.values():
        if not row:
            continue
        fms = row.get("failure_modes") or {}
        if isinstance(fms, dict):
            for k, v in fms.items():
                try:
                    fm_aggregate[k] = max(fm_aggregate.get(k, 0), int(v))
                except (TypeError, ValueError):
                    continue
    out["failure_modes"] = fm_aggregate

    return out


# ---------------------------------------------------------------------------
# Per-(stage, judge) worker
# ---------------------------------------------------------------------------

def _one_pair(
    stage: str,
    judge: Dict[str, str],
    output_dir: Path,
    provider: str,
    run_id: str,
    tag: str,
    stage_data_root: Path,
    judge_raw_dir: Path,
) -> Tuple[str, str, Optional[Dict[str, Any]], Optional[str]]:
    alias = judge["alias"]
    model = judge["model"]
    label = f"{stage}:{alias}"
    t0 = time.time()

    if stage == "stage_1_0":
        input_args = ["--input", str(output_dir / STAGE_INPUT_FILE[stage])]
    elif stage == "stage_1_1":
        input_args = ["--input", str(output_dir / STAGE_INPUT_FILE[stage])]
    elif stage == "stage_1_1_5":
        input_args = [
            "--before", str(output_dir / "stage_1_1_synthetic.jsonl"),
            "--after",  str(output_dir / "stage_1_1_5_deduped.jsonl"),
        ]
    elif stage == "stage_1_2":
        input_args = ["--input", str(output_dir / STAGE_INPUT_FILE[stage])]
    else:
        return (stage, alias, None, f"unknown stage {stage}")

    argv = _build_child_argv(
        stage=stage,
        input_args=input_args,
        judge_alias=alias,
        judge_model=model,
        provider=provider,
        run_id=run_id,
        tag=tag,
    )

    rc = _run(argv, tag=label)
    elapsed = time.time() - t0

    if rc != 0:
        _log(f"[{label}] FAILED rc={rc} in {elapsed:.1f}s")
        return (stage, alias, None, f"rc={rc}")

    _copy_judge_raw(
        stage=stage, run_id=run_id, judge_alias=alias,
        stage_data_root=stage_data_root, judge_raw_dir=judge_raw_dir,
    )
    row = _read_summary_row(
        stage=stage, run_id=run_id, judge_alias=alias,
        stage_data_root=stage_data_root,
    )
    _log(f"[{label}] DONE in {elapsed:.1f}s")
    return (stage, alias, row, None)


# ---------------------------------------------------------------------------
# Main orchestration
# ---------------------------------------------------------------------------

def main(argv: List[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output-dir", required=True,
        help="Directory containing the 4 Stage-1 JSONLs (stage_1_0_seed.jsonl, ...).",
    )
    parser.add_argument(
        "--stage-data-root", default="",
        help="Where per-judge runs write under <stage>/eval/runs/<run_id>. "
             "Defaults to $STAGE_DATA_ROOT or ./data .",
    )
    parser.add_argument(
        "--judge-raw-dir", required=True,
        help="Directory to copy per-judge judge.jsonl into (12 files total).",
    )
    parser.add_argument(
        "--metrics-out", required=True,
        help="Where to write the merged ensemble judge_metrics.json .",
    )
    parser.add_argument(
        "--provider", default="friendli",
    )
    parser.add_argument(
        "--run-id", required=True,
        help="Shared run-id prefix across all 12 runs (we append '__<alias>').",
    )
    parser.add_argument(
        "--tag", default="",
    )
    parser.add_argument(
        "--stages", default="stage_1_0,stage_1_1,stage_1_1_5,stage_1_2",
        help="Comma-separated subset to run.",
    )
    parser.add_argument(
        "--max-workers", type=int, default=4,
        help="Concurrent (stage, judge) runs. Default 4 = ~3x speedup vs sync.",
    )
    parser.add_argument(
        "--skip-on-error", action="store_true",
        help="Continue with remaining (stage,judge) pairs if one fails.",
    )
    args = parser.parse_args(argv)

    stage_data_root = Path(
        args.stage_data_root
        or os.environ.get("STAGE_DATA_ROOT")
        or "./data"
    )
    output_dir = Path(args.output_dir)
    judge_raw_dir = Path(args.judge_raw_dir)
    metrics_out = Path(args.metrics_out)
    metrics_out.parent.mkdir(parents=True, exist_ok=True)
    judge_raw_dir.mkdir(parents=True, exist_ok=True)

    stages_to_run = [s.strip() for s in args.stages.split(",") if s.strip()]

    pairs = [(s, j) for s in stages_to_run for j in JUDGES]

    _log(
        f"[tri_judge] output_dir={output_dir}  stage_data_root={stage_data_root}\n"
        f"            judge_raw_dir={judge_raw_dir}  metrics_out={metrics_out}\n"
        f"            stages={stages_to_run}  pairs={len(pairs)}  "
        f"max_workers={args.max_workers}  run_id={args.run_id}"
    )

    errors: List[str] = []
    rows_by_stage: Dict[str, Dict[str, Optional[Dict[str, Any]]]] = {
        s: {} for s in stages_to_run
    }

    t0 = time.time()

    with ThreadPoolExecutor(max_workers=args.max_workers) as executor:
        futures = {
            executor.submit(
                _one_pair,
                stage, judge,
                output_dir, args.provider, args.run_id, args.tag,
                stage_data_root, judge_raw_dir,
            ): (stage, judge["alias"])
            for stage, judge in pairs
        }
        for fut in as_completed(futures):
            stage, alias, row, err = fut.result()
            if err:
                errors.append(f"{stage}:{alias} {err}")
                rows_by_stage[stage][alias] = None
                if not args.skip_on_error:
                    # Best effort: still continue collecting outstanding
                    # workers (they've already been submitted).
                    pass
            else:
                rows_by_stage[stage][alias] = row

    ensemble: Dict[str, Dict[str, Any]] = {}
    for stage in stages_to_run:
        ensemble[stage] = _merge_ensemble(stage, rows_by_stage[stage])

    duration = time.time() - t0
    out = {
        "run_id": args.run_id,
        "provider": args.provider,
        "judges": [j["model"] for j in JUDGES],
        "stages": stages_to_run,
        "max_workers": args.max_workers,
        "duration_sec": round(duration, 2),
        "errors": errors,
        "ensemble": ensemble,
    }
    metrics_out.write_text(
        json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    _log(
        f"\n[tri_judge] wrote {metrics_out}  "
        f"errors={len(errors)} duration={duration:.1f}s"
    )
    return 0 if not errors else (0 if args.skip_on_error else 1)


if __name__ == "__main__":
    sys.exit(main())
