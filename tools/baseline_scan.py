#!/usr/bin/env python3
"""
Baseline Scanner - Truth Mode
=============================

Windows-friendly baseline scanner that runs real tools and captures evidence.
No shell=True, proper encoding handling, timeout protection.
"""

import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List


class BaselineScanner:
    """Baseline scanner with truth mode enforcement"""

    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root)
        self.artifacts_dir = self.project_root / "artifacts"
        self.artifacts_dir.mkdir(exist_ok=True)

        # Results storage
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "ruff": {"ok": False, "count": 0, "raw_path": None},
            "pytest": {"ok": False, "failures": 0},
            "mypy": {"ok": False, "reason": "not configured"},
            "bandit": {"ok": False, "count": 0, "raw_path": None},
        }

    def run_command(self, cmd: List[str], timeout: int = 120) -> Dict[str, Any]:
        """Run command with proper Windows handling"""
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                cwd=self.project_root,
                timeout=timeout,
            )

            return {
                "ok": result.returncode == 0,
                "returncode": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "timeout": False,
            }
        except subprocess.TimeoutExpired:
            return {
                "ok": False,
                "returncode": -1,
                "stdout": "",
                "stderr": f"Command timed out after {timeout}s",
                "timeout": True,
            }
        except Exception as e:
            return {
                "ok": False,
                "returncode": -1,
                "stdout": "",
                "stderr": str(e),
                "timeout": False,
            }

    def scan_ruff(self) -> Dict[str, Any]:
        """Scan with ruff and capture JSON output"""
        print("Running ruff check...")

        cmd = ["ruff", "check", ".", "--output-format", "json"]
        result = self.run_command(cmd)

        if result["timeout"]:
            return {"ok": False, "count": 0, "raw_path": None, "error": "timeout"}

        if not result["ok"]:
            print(f"Ruff failed with return code {result['returncode']}")
            print(f"Stderr: {result['stderr']}")
            return {
                "ok": False,
                "count": 0,
                "raw_path": None,
                "error": "command_failed",
            }

        try:
            # Parse JSON output
            ruff_data = json.loads(result["stdout"])
            if not isinstance(ruff_data, list):
                ruff_data = []

            # Save raw output
            raw_path = self.artifacts_dir / "ruff.json"
            with open(raw_path, "w", encoding="utf-8") as f:
                json.dump(ruff_data, f, indent=2, ensure_ascii=False)

            count = len(ruff_data)
            print(f"Ruff found {count} issues")

            return {
                "ok": True,
                "count": count,
                "raw_path": str(raw_path.relative_to(self.project_root)),
            }

        except json.JSONDecodeError as e:
            print(f"Failed to parse ruff JSON: {e}")
            return {
                "ok": False,
                "count": 0,
                "raw_path": None,
                "error": "json_parse_failed",
            }

    def scan_pytest(self) -> Dict[str, Any]:
        """Scan with pytest and count failures"""
        print("Running pytest...")

        cmd = ["pytest", "-q", "--tb=no"]
        result = self.run_command(cmd, timeout=300)  # Longer timeout for tests

        if result["timeout"]:
            return {"ok": False, "failures": 0, "error": "timeout"}

        # Parse pytest output to count failures
        failures = 0
        if "failed" in result["stdout"]:
            # Look for "X failed" pattern
            import re

            match = re.search(r"(\d+) failed", result["stdout"])
            if match:
                failures = int(match.group(1))

        # Pytest returns non-zero if there are failures
        ok = result["returncode"] == 0

        print(f"Pytest: {failures} failures, return code: {result['returncode']}")

        return {"ok": ok, "failures": failures, "returncode": result["returncode"]}

    def scan_mypy(self) -> Dict[str, Any]:
        """Check if mypy is configured and run it"""
        print("Checking mypy...")

        # Check if mypy config exists
        mypy_configs = ["mypy.ini", "pyproject.toml", ".mypy.ini", "setup.cfg"]

        has_config = any(
            (self.project_root / config).exists() for config in mypy_configs
        )

        if not has_config:
            print("No mypy configuration found")
            return {"ok": False, "reason": "not configured"}

        # Try to run mypy
        cmd = ["mypy", "."]
        result = self.run_command(cmd)

        if result["timeout"]:
            return {"ok": False, "reason": "timeout"}

        if not result["ok"]:
            print(f"Mypy failed with return code {result['returncode']}")
            return {"ok": False, "reason": "command_failed"}

        print("Mypy completed successfully")
        return {"ok": True, "reason": "success"}

    def scan_bandit(self) -> Dict[str, Any]:
        """Scan with bandit for security issues"""
        print("Running bandit...")

        cmd = ["bandit", "-q", "-r", ".", "-f", "json"]
        result = self.run_command(cmd)

        if result["timeout"]:
            return {"ok": False, "count": 0, "raw_path": None, "error": "timeout"}

        if not result["ok"]:
            print(f"Bandit failed with return code {result['returncode']}")
            print(f"Stderr: {result['stderr']}")
            return {
                "ok": False,
                "count": 0,
                "raw_path": None,
                "error": "command_failed",
            }

        try:
            # Parse JSON output
            bandit_data = json.loads(result["stdout"])
            if not isinstance(bandit_data, dict) or "results" not in bandit_data:
                bandit_data = {"results": []}

            # Save raw output
            raw_path = self.artifacts_dir / "bandit.json"
            with open(raw_path, "w", encoding="utf-8") as f:
                json.dump(bandit_data, f, indent=2, ensure_ascii=False)

            count = len(bandit_data.get("results", []))
            print(f"Bandit found {count} security issues")

            return {
                "ok": True,
                "count": count,
                "raw_path": str(raw_path.relative_to(self.project_root)),
            }

        except json.JSONDecodeError as e:
            print(f"Failed to parse bandit JSON: {e}")
            return {
                "ok": False,
                "count": 0,
                "raw_path": None,
                "error": "json_parse_failed",
            }

    def run_baseline_scan(self) -> Dict[str, Any]:
        """Run complete baseline scan"""
        print("Starting baseline scan in TRUTH MODE...")
        print(f"Project root: {self.project_root}")
        print(f"Artifacts dir: {self.artifacts_dir}")

        # Run all scans
        self.results["ruff"] = self.scan_ruff()
        self.results["pytest"] = self.scan_pytest()
        self.results["mypy"] = self.scan_mypy()
        self.results["bandit"] = self.scan_bandit()

        # Save results
        baseline_path = self.artifacts_dir / "baseline_scan.json"
        with open(baseline_path, "w", encoding="utf-8") as f:
            json.dump(self.results, f, indent=2, ensure_ascii=False)

        print(f"Baseline results saved to: {baseline_path}")

        # Print summary
        print("\nBASELINE SUMMARY:")
        print(f"  Ruff: {self.results['ruff']['count']} issues")
        print(f"  Pytest: {self.results['pytest']['failures']} failures")
        print(f"  Mypy: {self.results['mypy']['reason']}")
        print(f"  Bandit: {self.results['bandit']['count']} security issues")

        return self.results


def main():
    """Main entry point"""
    scanner = BaselineScanner()
    results = scanner.run_baseline_scan()

    # Check for incomplete sources
    incomplete_sources = []
    for source, data in results.items():
        if source == "timestamp":
            continue
        if not data.get("ok", False):
            incomplete_sources.append(source)

    if incomplete_sources:
        print(f"\nINCOMPLETE sources: {', '.join(incomplete_sources)}")
        sys.exit(2)
    else:
        print("\nAll sources completed successfully")
        sys.exit(0)


if __name__ == "__main__":
    main()
