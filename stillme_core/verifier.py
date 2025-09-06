"""
verifier.py - Verification logic for AgentDev execution results
"""
import re
import logging
from typing import Dict, Any, Optional, Union
from pathlib import Path

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
        step: Dict[str, Any], 
        exec_result: Dict[str, Any],
        success_criteria: Optional[Dict[str, Any]] = None
    ) -> Union[bool, Dict[str, Any]]:
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
        try:
            # Basic checks
            if not isinstance(exec_result, dict):
                return {
                    "passed": False,
                    "reason": "exec_result is not a dictionary",
                    "details": {"type": type(exec_result).__name__}
                }
            
            # Check if execution was successful
            if not exec_result.get("ok", False):
                return {
                    "passed": False,
                    "reason": "execution failed",
                    "details": {
                        "stdout": exec_result.get("stdout", ""),
                        "stderr": exec_result.get("stderr", ""),
                        "error": exec_result.get("error", "")
                    }
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
                        "details": {"expected": expected_code, "actual": actual_code}
                    }
            
            # Check stdout patterns
            stdout = exec_result.get("stdout", "")
            if "stdout_patterns" in criteria:
                patterns = criteria["stdout_patterns"]
                if not self._check_patterns(stdout, patterns):
                    return {
                        "passed": False,
                        "reason": "stdout patterns not matched",
                        "details": {"patterns": patterns, "stdout": stdout[:500]}
                    }
            
            # Check stderr patterns (should be empty for success)
            stderr = exec_result.get("stderr", "")
            if "stderr_patterns" in criteria:
                patterns = criteria["stderr_patterns"]
                if not self._check_patterns(stderr, patterns):
                    return {
                        "passed": False,
                        "reason": "stderr patterns not matched",
                        "details": {"patterns": patterns, "stderr": stderr[:500]}
                    }
            
            # Default verification: check for success patterns in stdout
            if not criteria:  # No custom criteria, use defaults
                if self._check_patterns(stdout, self.default_success_patterns):
                    return {
                        "passed": True,
                        "reason": "default success patterns matched",
                        "details": {"stdout": stdout[:500]}
                    }
                elif self._check_patterns(stdout + stderr, self.default_failure_patterns):
                    return {
                        "passed": False,
                        "reason": "default failure patterns detected",
                        "details": {"stdout": stdout[:500], "stderr": stderr[:500]}
                    }
                else:
                    # If no clear success/failure patterns, consider it passed if exit code is 0
                    return {
                        "passed": True,
                        "reason": "no clear patterns, but execution succeeded",
                        "details": {"stdout": stdout[:500]}
                    }
            
            # All custom criteria passed
            return {
                "passed": True,
                "reason": "all custom criteria satisfied",
                "details": {"criteria": criteria}
            }
            
        except Exception as e:
            logger.error(f"Verification error: {e}")
            return {
                "passed": False,
                "reason": f"verification error: {str(e)}",
                "details": {"error": str(e)}
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

    def verify_test_results(self, exec_result: Dict[str, Any]) -> Dict[str, Any]:
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
            "details": {
                "stats": stats,
                "stdout": stdout[:500],
                "stderr": stderr[:500]
            }
        }

    def _extract_test_stats(self, text: str) -> Dict[str, int]:
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
            "warnings": 0
        }
        
        # Common pytest output patterns
        patterns = {
            "collected": r"collected\s+(\d+)\s+items?",
            "passed": r"(\d+)\s+passed",
            "failed": r"(\d+)\s+failed",
            "error": r"(\d+)\s+error",
            "skipped": r"(\d+)\s+skipped",
            "warnings": r"(\d+)\s+warnings?"
        }
        
        for key, pattern in patterns.items():
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    stats[key] = int(match.group(1))
                except (ValueError, IndexError):
                    continue
        
        return stats
