"""Shared plumbing for Stage 2 judges.

Output layout per stage (every stage_X_Y_judge.py writes to here):

    $STAGE_DATA_ROOT/<stage>/
        eval/
            runs/
                <run_id>/
                    judge.jsonl        # per-unit judge records
                    report.md          # human report (worst-K + histograms)
                    meta.json          # run config, timings, model, git rev
            summary.jsonl              # APPEND-only: one headline row per run
            latest_report.md           # copy of most recent run's report.md

The per-run folder is the source of truth for any single evaluation; the
`summary.jsonl` lets you track metrics over time (before / after prompt
changes) without re-reading every run folder.

The helpers below enforce this layout so every judge script stays thin.
"""
from __future__ import annotations

import datetime as dt
import json
import os
import random
import shutil
import subprocess
import sys
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, List, Optional, Sequence, Tuple, TypeVar

from pipelines.config import data_root

# ---------------------------------------------------------------------------
# Run metadata
# ---------------------------------------------------------------------------

STAGES = ("stage_1_0", "stage_1_1", "stage_1_1_5", "stage_1_2", "stage_2_1", "stage_2_2", "stage_2_3", "stage_2_4")


def make_run_id(tag: Optional[str] = None) -> str:
    """UTC timestamp in filesystem-safe form, optional human tag.

    Examples:
        make_run_id()            -> '2026-04-21T18-14Z'
        make_run_id('baseline')  -> '2026-04-21T18-14Z_baseline'
    """
    stamp = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H-%MZ")
    return f"{stamp}_{tag}" if tag else stamp


def run_dir(stage: str, run_id: str, root: Optional[Path] = None) -> Path:
    """Return the directory for this run's artefacts (creates parents as needed)."""
    assert stage in STAGES, f"unknown stage {stage!r}; expected one of {STAGES}"
    base = (root or data_root()) / stage / "eval" / "runs" / run_id
    base.mkdir(parents=True, exist_ok=True)
    return base


def eval_dir(stage: str, root: Optional[Path] = None) -> Path:
    assert stage in STAGES, f"unknown stage {stage!r}; expected one of {STAGES}"
    base = (root or data_root()) / stage / "eval"
    base.mkdir(parents=True, exist_ok=True)
    return base


@dataclass
class RunMeta:
    stage: str
    run_id: str
    started_at: str
    finished_at: Optional[str] = None
    duration_sec: Optional[float] = None
    judge_model: str = ""
    provider: str = ""
    input_path: str = ""
    limit: int = 0
    n_units_total: int = 0
    n_units_sampled: int = 0
    n_ok: int = 0
    n_fail: int = 0
    tag: str = ""
    git_rev: str = ""
    extra: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def git_rev_short(cwd: Optional[Path] = None) -> str:
    """Best-effort git rev-parse --short HEAD; never raise."""
    try:
        res = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            check=False,
            capture_output=True,
            text=True,
            cwd=cwd,
            timeout=1,
        )
        return res.stdout.strip()
    except Exception:  # noqa: BLE001
        return ""


def write_meta(path: Path, meta: RunMeta) -> None:
    path.write_text(json.dumps(meta.to_dict(), ensure_ascii=False, indent=2))


# ---------------------------------------------------------------------------
# Append-only summary + latest report copy
# ---------------------------------------------------------------------------

def append_summary(stage: str, row: Dict[str, Any], root: Optional[Path] = None) -> Path:
    """Append a single JSON row to `$STAGE_DATA_ROOT/<stage>/eval/summary.jsonl`.

    The row is expected to be a small headline-metrics dict; judges should
    build it via their own Pydantic SummaryRow and pass `.model_dump()`.
    """
    path = eval_dir(stage, root=root) / "summary.jsonl"
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(row, ensure_ascii=False) + "\n")
    return path


def copy_latest_report(stage: str, run_id: str, root: Optional[Path] = None) -> Path:
    """Copy the run's report.md to `.../eval/latest_report.md`.

    We copy (not symlink) so that on shared storage / downloads the file is
    self-contained.
    """
    src = run_dir(stage, run_id, root=root) / "report.md"
    if not src.exists():
        raise FileNotFoundError(src)
    dst = eval_dir(stage, root=root) / "latest_report.md"
    shutil.copyfile(src, dst)
    return dst


# ---------------------------------------------------------------------------
# Judge call with retry (handles Nemotron-Ultra's occasional JSON truncation)
# ---------------------------------------------------------------------------

T = TypeVar("T")


def call_with_retry(
    call_fn: Callable[[int], Tuple[Optional[Dict[str, Any]], Dict[str, Any]]],
    max_tokens: int,
    retry_max_tokens: Optional[int] = None,
    sleep: float = 0.3,
) -> Tuple[Optional[Dict[str, Any]], Dict[str, Any], str]:
    """Run `call_fn(max_tokens)`; if parse fails once, retry with wider budget.

    `call_fn(mt)` must return (parsed_or_None, meta). Returns
    (parsed, meta, tag) where tag describes the outcome:
      - "primary"      : first call succeeded
      - "retry_wider"  : second call succeeded after widening tokens
      - "bad_json"     : both attempts failed to parse
      - "exception:<T>": call raised
    """
    if retry_max_tokens is None:
        retry_max_tokens = max(max_tokens * 2, 4096)
    attempts = [(max_tokens, "primary"), (retry_max_tokens, "retry_wider")]
    last_tag = "bad_json"
    meta: Dict[str, Any] = {}
    for mt, tag in attempts:
        try:
            parsed, meta = call_fn(mt)
        except Exception as exc:  # noqa: BLE001  stay alive across flaky gateways
            last_tag = f"exception:{type(exc).__name__}"
            time.sleep(sleep)
            continue
        if parsed is not None:
            return parsed, meta, tag
        last_tag = f"{tag}:bad_json"
        time.sleep(sleep)
    return None, meta, last_tag


# ---------------------------------------------------------------------------
# Sampling helpers
# ---------------------------------------------------------------------------

def cap(items: Sequence[T], limit: int) -> List[T]:
    """Return `items[:limit]` if limit>0 else list(items)."""
    return list(items[:limit] if limit else items)


def sample_random(items: Sequence[T], n: int, seed: int = 0) -> List[T]:
    """Random sample without replacement. If n >= len, return all."""
    if n <= 0 or n >= len(items):
        return list(items)
    rng = random.Random(seed)
    return rng.sample(list(items), n)


# ---------------------------------------------------------------------------
# JSONL readers
# ---------------------------------------------------------------------------

def iter_jsonl(path: Path) -> Iterable[Dict[str, Any]]:
    """Yield dicts from a .jsonl file or every .jsonl under a directory."""
    if path.is_dir():
        files = sorted(path.glob("*.jsonl"))
    else:
        files = [path]
    for f in files:
        with f.open(encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                yield json.loads(line)


# ---------------------------------------------------------------------------
# Markdown helpers
# ---------------------------------------------------------------------------

def pct(num: int, den: int) -> str:
    if den == 0:
        return "n/a"
    return f"{num}/{den} ({num / den * 100:.0f}%)"


def safe_mean(values: Sequence[float]) -> Optional[float]:
    vals = [v for v in values if v is not None]
    if not vals:
        return None
    return round(sum(vals) / len(vals), 2)


def truncate(text: str, n: int = 120) -> str:
    text = (text or "").replace("\n", " ").strip()
    return text[:n]


def safe_string_list(value: Any) -> List[str]:
    """Coerce judge-supplied `failure_modes` into a List[str].

    DeepSeek-V3.2 and other judges occasionally return an int / dict /
    string instead of the spec'd list, which crashed the judge pipeline
    with `TypeError: 'int' object is not iterable` during iter_00_baseline.
    This helper accepts:
      - list[str] (expected): keep only str items
      - list[Any]:              keep only str items
      - str:                    wrap into a one-element list
      - anything else:          fall back to [] (with the bad value
                                dropped; the judge row still validates).
    """
    if isinstance(value, list):
        return [str(x) for x in value if isinstance(x, str)]
    if isinstance(value, str) and value.strip():
        return [value.strip()]
    return []
