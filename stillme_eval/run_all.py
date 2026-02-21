"""
Run full StillMe Lite evaluation pipeline end-to-end.

This script orchestrates:
1) before run
2) after run
3) report generation
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RUN_EVAL = ROOT / "stillme_eval" / "run_eval.py"
GEN_REPORT = ROOT / "stillme_eval" / "generate_report.py"


def _run(cmd: list[str]) -> None:
    print(f"\n$ {' '.join(cmd)}")
    subprocess.run(cmd, check=True)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run full before/after evaluation and report generation")
    parser.add_argument("--dataset", default="stillme_eval/prompts_v2.jsonl")
    parser.add_argument("--before-url", default="http://localhost:8000")
    parser.add_argument("--after-url", default="http://localhost:8000")
    parser.add_argument("--before-output", default="stillme_eval/results_before.jsonl")
    parser.add_argument("--after-output", default="stillme_eval/results_after.jsonl")
    parser.add_argument("--report", default="reports/case_study_sample.md")
    parser.add_argument("--metrics-json", default="stillme_eval/metrics_summary.json")
    parser.add_argument("--timeout", type=int, default=90)
    parser.add_argument("--context-limit", type=int, default=3)
    parser.add_argument("--sleep-seconds", type=float, default=0.25)
    parser.add_argument("--max-retries-429", type=int, default=4)
    parser.add_argument("--retry-base-seconds", type=float, default=1.0)
    parser.add_argument("--skip-validator-mode-check", action="store_true")
    args = parser.parse_args()

    python = sys.executable

    before_cmd = [
        python,
        str(RUN_EVAL),
        "--mode",
        "before",
        "--dataset",
        args.dataset,
        "--output",
        args.before_output,
        "--api-base-url",
        args.before_url,
        "--timeout",
        str(args.timeout),
        "--context-limit",
        str(args.context_limit),
        "--sleep-seconds",
        str(args.sleep_seconds),
        "--max-retries-429",
        str(args.max_retries_429),
        "--retry-base-seconds",
        str(args.retry_base_seconds),
    ]
    if args.skip_validator_mode_check:
        before_cmd.append("--skip-validator-mode-check")

    after_cmd = [
        python,
        str(RUN_EVAL),
        "--mode",
        "after",
        "--dataset",
        args.dataset,
        "--output",
        args.after_output,
        "--api-base-url",
        args.after_url,
        "--timeout",
        str(args.timeout),
        "--context-limit",
        str(args.context_limit),
        "--sleep-seconds",
        str(args.sleep_seconds),
        "--max-retries-429",
        str(args.max_retries_429),
        "--retry-base-seconds",
        str(args.retry_base_seconds),
    ]
    if args.skip_validator_mode_check:
        after_cmd.append("--skip-validator-mode-check")

    report_cmd = [
        python,
        str(GEN_REPORT),
        "--before",
        args.before_output,
        "--after",
        args.after_output,
        "--report",
        args.report,
        "--metrics-json",
        args.metrics_json,
    ]

    _run(before_cmd)
    _run(after_cmd)
    _run(report_cmd)

    print("\nPipeline complete.")


if __name__ == "__main__":
    main()

