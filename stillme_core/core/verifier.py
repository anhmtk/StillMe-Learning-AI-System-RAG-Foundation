"""
verifier.py - Verification logic for AgentDev execution results
"""

import logging
import re
from typing import Any, Optional, Union

logger = logging.getLogger("AgentDev-Verifier")


class Verifier:
    """
    Verifies execution results against success criteria.
    """

    def __init__(self):
        self.default_success_patterns = [
            r"(\d+)\s+passed",
            r"(\d+)\s+failed.*0\s+error",
            r"test\s+passed",
            r"ok\s*$",
            r"success",
        ]
        self.default_failure_patterns = [
            r"(\d+)\s+failed",
            r"error:",
            r"exception:",
            r"traceback",
            r"assertion\s+error",
            r"failed\s+test",
        ]

    def verify(
        self,
        step: dict[str, Any],
        exec_result: dict[str, Any],
        success_criteria: Optional[dict[str, Any]] = None,
    ) -> Union[bool, dict[str, Any]]:
        """
        Verify execution result against success criteria.

        Args:
            step: Step information from plan
            exec_result: Execution result from executor
            success_criteria: Optional custom success criteria

        Returns:
            bool: True if verification passes
            dict: Detailed verification result with reasons
        """
        # Improved terminal output parsing
        stdout = exec_result.get("stdout", "")
        stderr = exec_result.get("stderr", "")
        combined_output = f"{stdout}\n{stderr}".strip()

        logger.debug(f"Verifying step: {step.get('step_id', 'unknown')}")
        logger.debug(f"Combined output: {combined_output[:200]}...")

        # Check for basic execution success
        if not exec_result.get("ok", False):
            return {
                "success": False,
                "reason": "Execution failed",
                "details": {
                    "stdout": stdout,
                    "stderr": stderr,
                    "error": exec_result.get("error", "Unknown error"),
                },
            }
        # Enhanced pytest output parsing
        pytest_patterns = {
            "passed": r"(\d+)\s+passed",
            "failed": r"(\d+)\s+failed",
            "xfailed": r"(\d+)\s+xfailed",
            "warnings": r"(\d+)\s+warnings",
            "no_tests": r"no tests ran",
            "collected": r"collected\s+(\d+)\s+items",
            "session_starts": r"test session starts",
            "session_ends": r"test session ends",
        }

        parsed_results = {}
        for key, pattern in pytest_patterns.items():
            match = re.search(pattern, combined_output, re.IGNORECASE)
            if match:
                parsed_results[key] = int(match.group(1)) if match.groups() else True

        logger.debug(f"Parsed pytest results: {parsed_results}")

        # Determine success based on parsed results
        if "no_tests" in parsed_results:
            return {
                "success": False,
                "reason": "No tests were executed",
                "details": {
                    "stdout": stdout,
                    "stderr": stderr,
                    "parsed_results": parsed_results,
                },
            }

        # If we have session info but no test results, it might be a different type of command
        if "session_starts" in parsed_results and not any(
            k in parsed_results for k in ["passed", "failed", "xfailed"]
        ):
            # This might be a non-test command, check for general success patterns
            if (
                "error" not in combined_output.lower()
                and "exception" not in combined_output.lower()
            ):
                return {
                    "success": True,
                    "reason": "Command executed without errors",
                    "details": {
                        "stdout": stdout,
                        "stderr": stderr,
                        "parsed_results": parsed_results,
                    },
                }

        # Check for test failures
        failed_count = parsed_results.get("failed", 0)
        passed_count = parsed_results.get("passed", 0)

        if failed_count > 0:
            return {
                "success": False,
                "reason": f"{failed_count} tests failed",
                "details": {
                    "stdout": stdout,
                    "stderr": stderr,
                    "parsed_results": parsed_results,
                },
            }

        # Success if tests passed
        if passed_count > 0:
            return {
                "success": True,
                "passed": True,
                "reason": f"{passed_count} tests passed",
                "details": {
                    "stdout": stdout,
                    "stderr": stderr,
                    "parsed_results": parsed_results,
                },
            }

        # Check for general command success (no errors, no exceptions)
        if (
            "error" not in combined_output.lower()
            and "exception" not in combined_output.lower()
            and "traceback" not in combined_output.lower()
        ):
            # If we have some output and no errors, consider it successful
            if len(combined_output.strip()) > 0:
                return {
                    "success": True,
                    "passed": True,
                    "reason": "Command executed without errors",
                    "details": {
                        "stdout": stdout,
                        "stderr": stderr,
                        "parsed_results": parsed_results,
                    },
                }

        # Fallback to pattern matching
        try:
            # Basic checks
            if not isinstance(exec_result, dict):
                return {
                    "success": False,
                    "reason": "exec_result is not a dictionary",
                    "details": {"type": type(exec_result).__name__},
                }

            # Check if execution was successful
            if not exec_result.get("ok", False):
                return {
                    "passed": False,
                    "reason": "execution failed",
                    "details": {
                        "stdout": exec_result.get("stdout", ""),
                        "stderr": exec_result.get("stderr", ""),
                        "error": exec_result.get("error", ""),
                    },
                }

            # Get success criteria
            criteria = success_criteria or step.get("success_criteria", {})

            # Check exit code if specified
            if "exit_code" in criteria:
                expected_code = criteria["exit_code"]
                actual_code = exec_result.get("exit_code", 0)
                if actual_code != expected_code:
                    return {
                        "passed": False,
                        "reason": f"exit code mismatch: expected {expected_code}, got {actual_code}",
                        "details": {"expected": expected_code, "actual": actual_code},
                    }

            # Check stdout patterns
            stdout = exec_result.get("stdout", "")
            if "stdout_patterns" in criteria:
                patterns = criteria["stdout_patterns"]
                if not self._check_patterns(stdout, patterns):
                    return {
                        "passed": False,
                        "reason": "stdout patterns not matched",
                        "details": {"patterns": patterns, "stdout": stdout[:500]},
                    }

            # Check stderr patterns (should be empty for success)
            stderr = exec_result.get("stderr", "")
            if "stderr_patterns" in criteria:
                patterns = criteria["stderr_patterns"]
                if not self._check_patterns(stderr, patterns):
                    return {
                        "passed": False,
                        "reason": "stderr patterns not matched",
                        "details": {"patterns": patterns, "stderr": stderr[:500]},
                    }

            # Default verification: check for success patterns in stdout
            if not criteria:  # No custom criteria, use defaults
                if self._check_patterns(stdout, self.default_success_patterns):
                    return {
                        "passed": True,
                        "reason": "default success patterns matched",
                        "details": {"stdout": stdout[:500]},
                    }
                elif self._check_patterns(
                    stdout + stderr, self.default_failure_patterns
                ):
                    return {
                        "passed": False,
                        "reason": "default failure patterns detected",
                        "details": {"stdout": stdout[:500], "stderr": stderr[:500]},
                    }
                else:
                    # If no clear success/failure patterns, consider it passed if exit code is 0
                    return {
                        "passed": True,
                        "reason": "no clear patterns, but execution succeeded",
                        "details": {"stdout": stdout[:500]},
                    }

            # All custom criteria passed
            return {
                "passed": True,
                "reason": "all custom criteria satisfied",
                "details": {"criteria": criteria},
            }

        except Exception as e:
            logger.error(f"Verification error: {e}")
            return {
                "passed": False,
                "reason": f"verification error: {e!s}",
                "details": {"error": str(e)},
            }

    def _check_patterns(self, text: str, patterns: list) -> bool:
        """
        Check if any pattern matches in the text.

        Args:
            text: Text to search in
            patterns: List of regex patterns

        Returns:
            bool: True if any pattern matches
        """
        if not patterns:
            return True

        for pattern in patterns:
            try:
                if re.search(pattern, text, re.IGNORECASE):
                    return True
            except re.error as e:
                logger.warning(f"Invalid regex pattern '{pattern}': {e}")
                continue

        return False

    def verify_test_results(self, exec_result: dict[str, Any]) -> dict[str, Any]:
        """
        Specialized verification for test results.

        Args:
            exec_result: Execution result from pytest

        Returns:
            dict: Verification result with test statistics
        """
        stdout = exec_result.get("stdout", "")
        stderr = exec_result.get("stderr", "")

        # Extract test statistics
        stats = self._extract_test_stats(stdout + stderr)

        # Determine if tests passed
        passed = stats.get("failed", 0) == 0 and stats.get("error", 0) == 0

        return {
            "passed": passed,
            "reason": "test results verification",
            "details": {"stats": stats, "stdout": stdout[:500], "stderr": stderr[:500]},
        }

    def _extract_test_stats(self, text: str) -> dict[str, int]:
        """
        Extract test statistics from pytest output.

        Args:
            text: Pytest output text

        Returns:
            dict: Test statistics
        """
        stats = {
            "collected": 0,
            "passed": 0,
            "failed": 0,
            "error": 0,
            "skipped": 0,
            "warnings": 0,
        }

        # Common pytest output patterns
        patterns = {
            "collected": r"collected\s+(\d+)\s+items?",
            "passed": r"(\d+)\s+passed",
            "failed": r"(\d+)\s+failed",
            "error": r"(\d+)\s+error",
            "skipped": r"(\d+)\s+skipped",
            "warnings": r"(\d+)\s+warnings?",
        }

        for key, pattern in patterns.items():
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    stats[key] = int(match.group(1))
                except (ValueError, IndexError):
                    continue

        return stats
