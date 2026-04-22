"""Tri-judge ensemble driver for Stage 2.

Mirror of `scripts/tri_judge_run.py` but calls Stage 2's four judge
modules (2.1 / 2.2 / 2.3 / 2.4) with their respective input flags.

  - stage_2_1 takes `--curated <Stage 1.2 file or dir>` + `--extracted <2.1 output>`
  - stage_2_2 / 2_3 / 2_4 take a single `--input`

4 stages × 3 Friendli judges = 12 subprocess calls, ThreadPoolExecutor
with `--max-workers` (default 4). Judge outputs land at

  $STAGE_DATA_ROOT/<stage>/eval/runs/<run_id>__<alias>/judge.jsonl
  $STAGE_DATA_ROOT/<stage>/eval/summary.jsonl                      (append)

After all 12 runs, `_merge_ensemble` produces an ensemble dict per stage
(mean + per-judge + range + boolean agreement_approx) and writes it as
`judge_metrics.json`.

Stage 2.1.5 is NOT judged — its quality is measured by deterministic
probes in `scripts/quant_stage2_report.py` (§4e).

Usage:
  python scripts/tri_judge_run_stage2.py \\
      --output-dir    experiments_stage2/iter_00_baseline/output \\
      --curated       experiments_stage2/stage1_pinned/stage_1_2_processed.jsonl \\
      --judge-raw-dir experiments_stage2/iter_00_baseline/judge_raw \\
      --metrics-out   experiments_stage2/iter_00_baseline/judge_metrics.json \\
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
from typing import Any, Dict, List, Optional, Tuple


JUDGES: List[Dict[str, str]] = [
    {"alias": "glm",      "model": "zai-org/GLM-5.1"},
    {"alias": "deepseek", "model": "deepseek-ai/DeepSeek-V3.2"},
    {"alias": "qwen3",    "model": "Qwen/Qwen3-235B-A22B-Instruct-2507"},
]


STAGE_INPUT_FILE = {
    "stage_2_1": "stage_2_1_extracted.jsonl",
    "stage_2_2": "stage_2_2_clusters.jsonl",
    "stage_2_3": "stage_2_3_analyzed_intents.jsonl",
    "stage_2_4": "stage_2_4_expanded_intents.jsonl",
}


# Metrics whose values are booleans-encoded-as-rates (0-1). agreement_rate
# is approximated at the aggregate level using the absolute range.
_BOOLEAN_METRICS = {
    # 2.1
    "intent_type_valid_rate", "general_wear_rate",
    "general_wear_false_negative_rate", "sentiment_rating_agreement_rate",
    # 2.2
    "coherent_rate",
    # 2.3 / 2.4
    "attr_fits_intent_rate", "per_query_natural_rate",
    "per_query_fits_intent_rate",
}

_PRINT_LOCK = threading.Lock()


def _log(msg: str) -> None:
    with _PRINT_LOCK:
        print(msg, flush=True)


def _run(argv: List[str], tag: str = "") -> int:
    """Run a subcommand, buffer output, print once (keeps parallel logs readable)."""
    _log(f"[{tag}] $ {' '.join(argv)}")
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
            for ln in lines[-80:]:
                print(ln, flush=True)
            print(f"--- [{tag}] end rc={proc.returncode} ---", flush=True)
    return proc.returncode


def _build_child_argv(
    stage: str,
    output_dir: Path,
    curated_path: Optional[Path],
    judge_alias: str,
    judge_model: str,
    provider: str,
    run_id: str,
    tag: str,
) -> List[str]:
    module = f"pipelines.eval.{stage}_judge"
    argv = [
        sys.executable, "-m", module,
        "--provider", provider,
        "--judge-model", judge_model,
        "--run-id", f"{run_id}__{judge_alias}",
        "--tag", f"{tag}__{judge_alias}",
    ]
    if stage == "stage_2_1":
        if curated_path is None:
            raise ValueError("stage_2_1 judge needs --curated")
        argv += [
            "--curated", str(curated_path),
            "--extracted", str(output_dir / STAGE_INPUT_FILE[stage]),
        ]
    else:
        argv += ["--input", str(output_dir / STAGE_INPUT_FILE[stage])]
    return argv


def _copy_judge_raw(
    stage: str, run_id: str, judge_alias: str,
    stage_data_root: Path, judge_raw_dir: Path,
) -> None:
    src = (
        stage_data_root / stage / "eval" / "runs"
        / f"{run_id}__{judge_alias}" / "judge.jsonl"
    )
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
    rows_by_alias: Dict[str, Optional[Dict[str, Any]]],
) -> Dict[str, Any]:
    """Collapse three judge summary dicts into ensemble metrics."""
    numeric_keys: set[str] = set()
    for row in rows_by_alias.values():
        if not row:
            continue
        for k, v in row.items():
            if isinstance(v, (int, float)) and k not in (
                "n_evaluated", "n_clusters", "n_intents",
                "duration_sec", "n_total", "n_sampled",
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
        rng = (
            max(values.values()) - min(values.values())
            if len(values) >= 2 else None
        )
        entry: Dict[str, Any] = {
            "mean": round(mean, 3) if mean is not None else None,
        }
        for alias in ("glm", "deepseek", "qwen3"):
            entry[alias] = (
                round(values[alias], 3) if alias in values else None
            )
        entry["range"] = round(rng, 3) if rng is not None else None
        if k in _BOOLEAN_METRICS and rng is not None:
            entry["agreement_approx"] = round(1.0 - rng, 3)
        out[k] = entry

    for k in ("n_evaluated", "n_clusters", "n_intents", "n_total", "n_sampled"):
        for _, row in rows_by_alias.items():
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


def _one_pair(
    stage: str,
    judge: Dict[str, str],
    output_dir: Path,
    curated_path: Optional[Path],
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

    argv = _build_child_argv(
        stage=stage,
        output_dir=output_dir,
        curated_path=curated_path,
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


def main(argv: List[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output-dir", required=True,
        help="Directory containing the Stage 2 JSONLs (2.1 / 2.2 / 2.3 / 2.4).",
    )
    parser.add_argument(
        "--curated", required=True,
        help=(
            "Stage 1.2 curated file or directory; passed to stage_2_1_judge "
            "as --curated. Usually experiments_stage2/stage1_pinned/"
            "stage_1_2_processed.jsonl."
        ),
    )
    parser.add_argument(
        "--stage-data-root", default="",
        help="Where per-judge runs write (<stage>/eval/runs/<run_id>). "
             "Defaults to $STAGE_DATA_ROOT or ./data_eval .",
    )
    parser.add_argument(
        "--judge-raw-dir", required=True,
        help="Where to copy per-judge judge.jsonl (12 files total).",
    )
    parser.add_argument(
        "--metrics-out", required=True,
        help="Where to write the merged ensemble judge_metrics.json .",
    )
    parser.add_argument("--provider", default="friendli")
    parser.add_argument(
        "--run-id", required=True,
        help="Shared run-id prefix across all 12 runs (we append '__<alias>').",
    )
    parser.add_argument("--tag", default="")
    parser.add_argument(
        "--stages",
        default="stage_2_1,stage_2_2,stage_2_3,stage_2_4",
        help="Comma-separated subset to run.",
    )
    parser.add_argument(
        "--max-workers", type=int, default=4,
        help="Concurrent (stage, judge) runs. Default 4.",
    )
    parser.add_argument(
        "--skip-on-error", action="store_true",
        help="Continue with remaining pairs if one fails.",
    )
    args = parser.parse_args(argv)

    stage_data_root = Path(
        args.stage_data_root
        or os.environ.get("STAGE_DATA_ROOT")
        or "./data_eval"
    )
    output_dir = Path(args.output_dir)
    curated_path = Path(args.curated)
    judge_raw_dir = Path(args.judge_raw_dir)
    metrics_out = Path(args.metrics_out)
    metrics_out.parent.mkdir(parents=True, exist_ok=True)
    judge_raw_dir.mkdir(parents=True, exist_ok=True)

    stages_to_run = [s.strip() for s in args.stages.split(",") if s.strip()]
    pairs = [(s, j) for s in stages_to_run for j in JUDGES]

    _log(
        f"[tri_judge_stage2] output_dir={output_dir}\n"
        f"                   curated={curated_path}\n"
        f"                   stage_data_root={stage_data_root}\n"
        f"                   judge_raw_dir={judge_raw_dir}\n"
        f"                   metrics_out={metrics_out}\n"
        f"                   stages={stages_to_run}  pairs={len(pairs)}  "
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
                output_dir, curated_path, args.provider, args.run_id, args.tag,
                stage_data_root, judge_raw_dir,
            ): (stage, judge["alias"])
            for stage, judge in pairs
        }
        for fut in as_completed(futures):
            stage, alias, row, err = fut.result()
            if err:
                errors.append(f"{stage}:{alias} {err}")
                rows_by_stage[stage][alias] = None
            else:
                rows_by_stage[stage][alias] = row

    ensemble: Dict[str, Dict[str, Any]] = {}
    for stage in stages_to_run:
        ensemble[stage] = _merge_ensemble(rows_by_stage[stage])

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
        f"\n[tri_judge_stage2] wrote {metrics_out}  "
        f"errors={len(errors)} duration={duration:.1f}s"
    )
    return 0 if not errors else (0 if args.skip_on_error else 1)


if __name__ == "__main__":
    sys.exit(main())
