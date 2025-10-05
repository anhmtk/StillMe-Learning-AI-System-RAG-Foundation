#!/usr/bin/env python3
"""
AgentDev Monitoring System
=========================

Monitoring and metrics collection for self-improvement loop.
"""

import json
import subprocess
import sys
import time
from datetime import datetime, UTC
from pathlib import Path
from typing import Any, Dict, List

from agent_dev.persistence.repo import AgentDevRepo


class MonitoringSystem:
    """Monitoring system for AgentDev self-improvement"""

    def __init__(self, repo: AgentDevRepo):
        self.repo = repo
        self.logs_dir = Path("logs")
        self.logs_dir.mkdir(exist_ok=True)

    def run_tests(self) -> Dict[str, Any]:
        """Run pytest and collect results"""
        try:
            start_time = time.time()

            # Run pytest with coverage
            result = subprocess.run(
                [sys.executable, "-m", "pytest", "-q", "--tb=short", "--maxfail=1"],
                capture_output=True,
                text=True,
                timeout=300,
            )

            duration = time.time() - start_time

            # Parse results
            output = result.stdout + result.stderr
            pass_count = output.count("PASSED")
            fail_count = output.count("FAILED")
            error_count = output.count("ERROR")

            total_tests = pass_count + fail_count + error_count
            pass_rate = (pass_count / total_tests * 100) if total_tests > 0 else 0

            return {
                "pass_count": pass_count,
                "fail_count": fail_count,
                "error_count": error_count,
                "total_tests": total_tests,
                "pass_rate": pass_rate,
                "duration": duration,
                "output": output,
                "return_code": result.returncode,
            }
        except subprocess.TimeoutExpired:
            return {
                "pass_count": 0,
                "fail_count": 0,
                "error_count": 0,
                "total_tests": 0,
                "pass_rate": 0,
                "duration": 300,
                "output": "Test timeout after 5 minutes",
                "return_code": -1,
            }
        except Exception as e:
            return {
                "pass_count": 0,
                "fail_count": 0,
                "error_count": 0,
                "total_tests": 0,
                "pass_rate": 0,
                "duration": 0,
                "output": f"Test error: {e}",
                "return_code": -1,
            }

    def run_coverage(self) -> Dict[str, float]:
        """Run coverage analysis"""
        try:
            # Run coverage
            result = subprocess.run(
                [sys.executable, "-m", "coverage", "run", "-m", "pytest", "-q"],
                capture_output=True,
                text=True,
                timeout=300,
            )

            if result.returncode != 0:
                return {"overall": 0.0, "touched": 0.0}

            # Get coverage report
            report_result = subprocess.run(
                [sys.executable, "-m", "coverage", "report", "--show-missing"],
                capture_output=True,
                text=True,
                timeout=60,
            )

            if report_result.returncode != 0:
                return {"overall": 0.0, "touched": 0.0}

            # Parse coverage from output
            output = report_result.stdout
            lines = output.split("\n")

            overall = 0.0
            for line in lines:
                if "TOTAL" in line:
                    # Extract percentage from "TOTAL" line
                    parts = line.split()
                    for part in parts:
                        if part.endswith("%"):
                            overall = float(part[:-1])
                            break
                    break

            return {"overall": overall, "touched": overall}  # Simplified for now

        except Exception:
            return {"overall": 0.0, "touched": 0.0}

    def run_linting(self) -> Dict[str, int]:
        """Run linting tools"""
        try:
            # Run ruff
            ruff_result = subprocess.run(
                [sys.executable, "-m", "ruff", "check", ".", "--force-exclude"],
                capture_output=True,
                text=True,
                timeout=60,
            )

            ruff_errors = 0
            if ruff_result.returncode != 0:
                ruff_errors = len(ruff_result.stdout.split("\n")) - 1

            # Run pyright
            pyright_result = subprocess.run(
                [sys.executable, "-m", "pyright", "--stats"],
                capture_output=True,
                text=True,
                timeout=60,
            )

            pyright_errors = 0
            if pyright_result.returncode != 0:
                pyright_errors = pyright_result.stdout.count("error")

            return {
                "ruff_errors": ruff_errors,
                "pyright_errors": pyright_errors,
            }
        except Exception:
            return {"ruff_errors": 0, "pyright_errors": 0}

    def collect_metrics(self) -> Dict[str, Any]:
        """Collect all metrics"""
        print("🔍 Collecting test metrics...")
        test_results = self.run_tests()

        print("📊 Collecting coverage metrics...")
        coverage_results = self.run_coverage()

        print("🔧 Collecting linting metrics...")
        linting_results = self.run_linting()

        metrics = {
            "timestamp": datetime.now(UTC),
            "pass_rate": test_results["pass_rate"],
            "fail_rate": 100 - test_results["pass_rate"],
            "coverage_overall": coverage_results["overall"],
            "coverage_touched": coverage_results["touched"],
            "lint_errors": linting_results["ruff_errors"],
            "pyright_errors": linting_results["pyright_errors"],
            "duration": test_results["duration"],
            "total_tests": test_results["total_tests"],
        }

        return metrics

    def log_run(self, metrics: Dict[str, Any]) -> None:
        """Log run to JSONL file"""
        log_file = self.logs_dir / "agentdev_run.jsonl"

        with open(log_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(metrics, default=str) + "\n")

    def record_metrics(self, metrics: Dict[str, Any]) -> int:
        """Record metrics to database"""
        return self.repo.record_metrics(
            date=metrics["timestamp"],
            pass_rate=metrics["pass_rate"],
            fail_rate=metrics["fail_rate"],
            coverage_overall=metrics["coverage_overall"],
            coverage_touched=metrics["coverage_touched"],
            mttr_min=metrics.get("duration", 0) / 60,  # Convert to minutes
            lint_errors=metrics["lint_errors"],
            pyright_errors=metrics["pyright_errors"],
        )

    def get_recent_metrics(self, days: int = 7) -> List[Dict[str, Any]]:
        """Get recent metrics for analysis"""
        recent = self.repo.get_recent_metrics(days)
        return [
            {
                "date": m.date,
                "pass_rate": m.pass_rate,
                "fail_rate": m.fail_rate,
                "coverage_overall": m.coverage_overall,
                "coverage_touched": m.coverage_touched,
                "lint_errors": m.lint_errors,
                "pyright_errors": m.pyright_errors,
            }
            for m in recent
        ]
