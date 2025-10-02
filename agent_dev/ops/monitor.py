"""
Patrol Monitoring System for AgentDev Operations
===============================================

Handles periodic monitoring and health checks.
"""

import logging
import os
import subprocess
import time
from datetime import datetime
from typing import Any

logger = logging.getLogger(__name__)


class PatrolRunner:
    """Runs periodic patrols and health checks"""

    def __init__(self, project_root: str = "."):
        self.project_root = project_root
        self.last_quick_patrol = 0
        self.last_deep_patrol = 0
        self.quick_interval = 15 * 60  # 15 minutes
        self.deep_interval = 6 * 60 * 60  # 6 hours

    def run_quick_patrol(self) -> dict[str, Any]:
        """Run quick patrol (ruff + pytest smoke)"""
        logger.info("Starting quick patrol...")
        start_time = time.time()

        results = {
            "timestamp": datetime.now().isoformat(),
            "type": "quick",
            "ruff_issues": [],
            "pytest_status": "unknown",
            "duration_seconds": 0,
            "success": False,
        }

        try:
            # Run ruff check
            ruff_result = self._run_ruff_check()
            results["ruff_issues"] = ruff_result.get("issues", [])

            # Run pytest smoke test
            pytest_result = self._run_pytest_smoke()
            results["pytest_status"] = pytest_result.get("status", "unknown")

            results["success"] = (
                len(results["ruff_issues"]) == 0
                and results["pytest_status"] == "passed"
            )
            results["duration_seconds"] = time.time() - start_time

            self.last_quick_patrol = time.time()
            logger.info(f"Quick patrol completed in {results['duration_seconds']:.2f}s")

        except Exception as e:
            logger.error(f"Quick patrol failed: {e}")
            results["error"] = str(e)
            results["duration_seconds"] = time.time() - start_time

        return results

    def run_deep_patrol(self) -> dict[str, Any]:
        """Run deep patrol (includes red-team if available)"""
        logger.info("Starting deep patrol...")
        start_time = time.time()

        results = {
            "timestamp": datetime.now().isoformat(),
            "type": "deep",
            "ruff_issues": [],
            "pytest_status": "unknown",
            "red_team_status": "not_available",
            "duration_seconds": 0,
            "success": False,
        }

        try:
            # Run quick patrol first
            quick_results = self.run_quick_patrol()
            results.update(quick_results)

            # Run red-team check if available
            red_team_result = self._run_red_team_check()
            results["red_team_status"] = red_team_result.get("status", "not_available")
            if "risk_score" in red_team_result:
                results["red_team_risk_score"] = red_team_result["risk_score"]

            results["success"] = (
                len(results["ruff_issues"]) == 0
                and results["pytest_status"] == "passed"
                and results["red_team_status"] != "high_risk"
            )
            results["duration_seconds"] = time.time() - start_time

            self.last_deep_patrol = time.time()
            logger.info(f"Deep patrol completed in {results['duration_seconds']:.2f}s")

        except Exception as e:
            logger.error(f"Deep patrol failed: {e}")
            results["error"] = str(e)
            results["duration_seconds"] = time.time() - start_time

        return results

    def should_run_quick_patrol(self) -> bool:
        """Check if quick patrol should run"""
        return time.time() - self.last_quick_patrol >= self.quick_interval

    def should_run_deep_patrol(self) -> bool:
        """Check if deep patrol should run"""
        return time.time() - self.last_deep_patrol >= self.deep_interval

    def _run_ruff_check(self) -> dict[str, Any]:
        """Run ruff check and return results"""
        try:
            cmd = [
                "ruff",
                "check",
                "stillme_ai",
                "tests",
                "--output-format=json",
                "--select",
                "F821,W293,W291,E302,I001,F401",
            ]

            result = subprocess.run(
                cmd,
                cwd=self.project_root,
                capture_output=True,
                text=False,  # Capture raw bytes
                timeout=60,
            )

            if result.returncode == 0:
                return {"issues": []}

            # Parse JSON output with Unicode safety
            try:
                import json

                from stillme_core.utils.io_safe import safe_decode

                # Use safe decoding for stdout
                stdout_text = safe_decode(result.stdout) if result.stdout else ""

                if stdout_text:
                    issues = json.loads(stdout_text)
                else:
                    issues = []
                return {"issues": issues}
            except (json.JSONDecodeError, UnicodeDecodeError):
                # Fallback to parsing stderr with Unicode safety
                issues = []
                try:
                    from stillme_core.utils.io_safe import safe_decode

                    stderr_bytes = (
                        result.stderr.encode()
                        if isinstance(result.stderr, str)
                        else result.stderr
                    )
                    stderr_text = safe_decode(stderr_bytes) if stderr_bytes else ""

                    for line in stderr_text.split("\n"):
                        if ":" in line and any(
                            rule in line
                            for rule in ["F821", "W293", "W291", "E302", "I001", "F401"]
                        ):
                            parts = line.split(":")
                            if len(parts) >= 4:
                                issues.append(
                                    {
                                        "file": parts[0],
                                        "line": int(parts[1])
                                        if parts[1].isdigit()
                                        else 0,
                                        "rule": parts[3].strip().split()[0]
                                        if parts[3].strip()
                                        else "UNKNOWN",
                                        "message": ":".join(parts[3:]).strip(),
                                    }
                                )
                except UnicodeDecodeError:
                    # If stderr also has Unicode issues, return empty
                    pass
                return {"issues": issues}

        except subprocess.TimeoutExpired:
            logger.warning("Ruff check timed out")
            return {"issues": [], "timeout": True}
        except Exception as e:
            logger.error(f"Ruff check failed: {e}")
            return {"issues": [], "error": str(e)}

    def _run_pytest_smoke(self) -> dict[str, Any]:
        """Run pytest smoke test"""
        try:
            cmd = [
                "pytest",
                "-q",
                "-k",
                "not slow",
                "--maxfail=1",
                "--disable-warnings",
                "--tb=no",
            ]

            result = subprocess.run(
                cmd,
                cwd=self.project_root,
                capture_output=True,
                text=False,  # Capture raw bytes
                timeout=120,
            )

            if result.returncode == 0:
                return {"status": "passed"}
            else:
                # Use safe decoding for output
                from stillme_core.utils.io_safe import safe_decode

                stdout_text = safe_decode(result.stdout) if result.stdout else ""
                stderr_text = safe_decode(result.stderr) if result.stderr else ""
                return {"status": "failed", "output": stdout_text + stderr_text}

        except subprocess.TimeoutExpired:
            logger.warning("Pytest smoke test timed out")
            return {"status": "timeout"}
        except Exception as e:
            logger.error(f"Pytest smoke test failed: {e}")
            return {"status": "error", "error": str(e)}

    def _run_red_team_check(self) -> dict[str, Any]:
        """Run red-team security check if available"""
        try:
            # Check if red-team engine is available
            red_team_path = os.path.join(
                self.project_root,
                "stillme_core",
                "core",
                "advanced_security",
                "red_team_engine.py",
            )
            if not os.path.exists(red_team_path):
                return {"status": "not_available"}

            # Import and run light security check
            import sys

            sys.path.insert(0, os.path.join(self.project_root, "stillme_core"))

            from core.advanced_security.red_team_engine import RedTeamEngine

            # Run light scenario
            engine = RedTeamEngine()
            result = engine.run_light_security_check(self.project_root)

            return {
                "status": "completed",
                "risk_score": result.get("risk_score", 0.0),
                "findings": result.get("findings", []),
            }

        except ImportError:
            logger.warning("Red-team engine not available")
            return {"status": "not_available"}
        except Exception as e:
            logger.error(f"Red-team check failed: {e}")
            return {"status": "error", "error": str(e)}
