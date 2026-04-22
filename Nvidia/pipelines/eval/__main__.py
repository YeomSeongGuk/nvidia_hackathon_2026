"""Unified multi-stage judge runner.

Lets you evaluate one or more pipeline stages in a single invocation,
with one consistent set of provider / judge-model / sampling flags.

Examples
========

  # smoke: 5 records of Stage 1.1 on the default NIM judge
  python -m pipelines.eval --stages stage_1_1 --limit 5

  # all Stage 2 stages via Friendli GLM-5.1
  python -m pipelines.eval \\
      --stages stage_2_1,stage_2_2,stage_2_3,stage_2_4 \\
      --provider friendli --judge-model zai-org/GLM-5.1

  # Stage 1.1 + 2.4 against local vLLM Nemotron-Super
  LLM_EXTRA_BODY='{"chat_template_kwargs":{"enable_thinking":false}}' \\
      python -m pipelines.eval \\
      --stages stage_1_1,stage_2_4 \\
      --provider vllm --judge-model nemotron \\
      --sample 50 --tag vllm_120b

  # EVERY stage (stage_1_1, 1_2, 2_1, 2_2, 2_3, 2_4)
  python -m pipelines.eval --stages all \\
      --provider friendli --judge-model Qwen/Qwen3-235B-A22B-Instruct-2507

Supported `--provider` values:  `nim` / `friendli` / `vllm`.
Friendli offers a wide menu of multilingual judges with no local GPU:
  - `zai-org/GLM-5.1`
  - `zai-org/GLM-5`
  - `Qwen/Qwen3-235B-A22B-Instruct-2507`
  - `deepseek-ai/DeepSeek-V3.2`
  - `LGAI-EXAONE/K-EXAONE-236B-A23B`
  - `meta-llama-3.1-8b-instruct`   (lightweight, non-reasoning)

The wrapper simply builds a `sys.argv` for each selected stage's judge CLI
and calls its `main()`. Any flag that the per-stage judges all understand
(provider, judge-model, limit, sample, seed, sleep, max-tokens, tag, run-id)
is forwarded; stage-specific defaults (e.g. Stage 2.1's `--curated` and
`--extracted`) keep working via the child CLI defaults.
"""
from __future__ import annotations

import argparse
import sys
import time
from typing import Callable, List

from pipelines.eval import common


# Each stage -> its module's main(argv) entry point.
# Imports are lazy so that a user evaluating only Stage 2.4 is not forced to
# import Stage 2.2's clustering / Pydantic graph.

def _run_stage_1_1(argv: List[str]) -> int:
    from pipelines.eval.stage_1_1_judge import main
    return main(argv)


def _run_stage_1_1_5(argv: List[str]) -> int:
    from pipelines.eval.stage_1_1_5_judge import main
    return main(argv)


def _run_stage_1_2(argv: List[str]) -> int:
    from pipelines.eval.stage_1_2_judge import main
    return main(argv)


def _run_stage_2_1(argv: List[str]) -> int:
    from pipelines.eval.stage_2_1_judge import main
    return main(argv)


def _run_stage_2_2(argv: List[str]) -> int:
    from pipelines.eval.stage_2_2_judge import main
    return main(argv)


def _run_stage_2_3(argv: List[str]) -> int:
    from pipelines.eval.stage_2_3_judge import main
    return main(argv)


def _run_stage_2_4(argv: List[str]) -> int:
    from pipelines.eval.stage_2_4_judge import main
    return main(argv)


STAGE_RUNNERS: dict[str, Callable[[List[str]], int]] = {
    "stage_1_1": _run_stage_1_1,
    "stage_1_1_5": _run_stage_1_1_5,
    "stage_1_2": _run_stage_1_2,
    "stage_2_1": _run_stage_2_1,
    "stage_2_2": _run_stage_2_2,
    "stage_2_3": _run_stage_2_3,
    "stage_2_4": _run_stage_2_4,
}


def _parse_stage_list(raw: str) -> List[str]:
    if raw.strip().lower() in ("all", "*"):
        return list(common.STAGES)
    stages: List[str] = []
    for part in raw.split(","):
        s = part.strip()
        if not s:
            continue
        if s not in STAGE_RUNNERS:
            raise SystemExit(
                f"unknown stage {s!r}. Valid: {', '.join(STAGE_RUNNERS)}"
            )
        stages.append(s)
    return stages or list(common.STAGES)


def _build_child_argv(args: argparse.Namespace) -> List[str]:
    """Translate the shared flags into the child stages' CLI."""
    out: List[str] = []
    if args.provider:
        out += ["--provider", args.provider]
    if args.judge_model:
        out += ["--judge-model", args.judge_model]
    if args.limit:
        out += ["--limit", str(args.limit)]
    if args.sample:
        out += ["--sample", str(args.sample), "--seed", str(args.seed)]
    if args.sleep is not None:
        out += ["--sleep", str(args.sleep)]
    if args.max_tokens is not None:
        out += ["--max-tokens", str(args.max_tokens)]
    if args.tag:
        out += ["--tag", args.tag]
    if args.run_id:
        out += ["--run-id", args.run_id]
    return out


def main(argv: List[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="pipelines.eval",
        description="Run one or more stage judges with a shared config.",
    )
    parser.add_argument(
        "--stages",
        required=True,
        help="Comma-separated list, or 'all'. "
             f"Valid names: {','.join(common.STAGES)}.",
    )
    parser.add_argument(
        "--provider", choices=["nim", "friendli", "vllm"], default=None,
        help="LLM provider for the judge (default = $LLM_PROVIDER).",
    )
    parser.add_argument(
        "--judge-model", default=None,
        help="Judge model id. Omit to use each stage's DEFAULT_JUDGE_MODEL.",
    )
    parser.add_argument("--limit", type=int, default=0, help="0 = no limit.")
    parser.add_argument("--sample", type=int, default=0, help="random sample N.")
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--sleep", type=float, default=0.15)
    parser.add_argument("--max-tokens", type=int, default=1536)
    parser.add_argument("--tag", default="")
    parser.add_argument(
        "--run-id", default="",
        help="Shared run-id across all selected stages. "
             "If empty, each stage generates its own timestamped run-id.",
    )
    parser.add_argument(
        "--continue-on-error", action="store_true",
        help="If a stage fails, log and continue with the next one.",
    )
    args = parser.parse_args(argv)

    stages = _parse_stage_list(args.stages)
    child_argv = _build_child_argv(args)
    print(
        f"[pipelines.eval] running {len(stages)} stage(s): "
        f"{','.join(stages)}  shared_argv={child_argv}",
        flush=True,
    )

    exit_code = 0
    for s in stages:
        print(
            f"\n========================================\n"
            f"== {s}\n"
            f"========================================",
            flush=True,
        )
        t0 = time.time()
        try:
            rc = STAGE_RUNNERS[s](child_argv)
        except SystemExit as exc:
            rc = int(exc.code or 0)
        except Exception as exc:  # noqa: BLE001
            print(f"[{s}] crashed: {type(exc).__name__}: {exc}", flush=True)
            rc = 1
        dur = time.time() - t0
        print(f"== {s} done: rc={rc} dur={dur:.1f}s ==", flush=True)
        if rc != 0:
            exit_code = rc
            if not args.continue_on_error:
                break
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
