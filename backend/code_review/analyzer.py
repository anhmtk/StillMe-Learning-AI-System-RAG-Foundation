"""
Code Analyzer - Runs Ruff and basic security checks
"""

import json
import subprocess
import logging
from pathlib import Path
from typing import List, Optional
from dataclasses import dataclass

from .config import CodeReviewConfig

logger = logging.getLogger(__name__)


@dataclass
class CodeIssue:
    """Represents a code quality issue"""

    file_path: str
    line: int
    column: Optional[int]
    rule: str
    message: str
    severity: str  # error, warning, info
    fixable: bool = False


class CodeAnalyzer:
    """Analyzes code using Ruff and basic security checks"""

    def __init__(self, config: CodeReviewConfig):
        self.config = config
        logger.info("CodeAnalyzer initialized")

    def analyze(self, repo_path: str = ".") -> List[CodeIssue]:
        """
        Analyze codebase and return list of issues

        Args:
            repo_path: Path to repository root

        Returns:
            List of CodeIssue objects
        """
        issues: List[CodeIssue] = []

        if not self.config.enabled:
            logger.debug("Code review disabled, skipping analysis")
            return issues

        # Run Ruff checks
        if self.config.ruff_check_enabled:
            ruff_issues = self._run_ruff_check(repo_path)
            issues.extend(ruff_issues)

        # Run basic security checks
        if self.config.security_checks_enabled:
            security_issues = self._run_security_checks(repo_path)
            issues.extend(security_issues)

        # Filter by severity threshold
        filtered_issues = self._filter_by_severity(issues)

        logger.info(
            f"Found {len(filtered_issues)} code issues (filtered from {len(issues)})"
        )
        return filtered_issues

    def _run_ruff_check(self, repo_path: str) -> List[CodeIssue]:
        """Run Ruff linter and parse results"""
        issues: List[CodeIssue] = []

        try:
            # Build ruff command
            cmd = ["ruff", "check", repo_path, "--output-format", "json"]

            # Add exclude patterns
            for pattern in self.config.ruff_exclude_patterns:
                cmd.extend(["--exclude", pattern])

            logger.debug(f"Running: {' '.join(cmd)}")

            # Run ruff
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=60,
                cwd=repo_path if repo_path != "." else None,
            )

            # Parse JSON output
            if result.returncode == 0 and not result.stdout.strip():
                logger.debug("Ruff found no issues")
                return issues

            # Try to parse JSON output
            try:
                ruff_output = json.loads(result.stdout)
            except json.JSONDecodeError:
                # If not JSON, try to parse stderr or stdout as text
                logger.warning("Ruff output is not JSON, trying to parse as text")
                if result.stderr:
                    logger.warning(f"Ruff stderr: {result.stderr}")
                return issues

            # Parse ruff JSON format
            for item in ruff_output:
                if "code" in item and "message" in item:
                    # Ruff JSON format: {code, message, location, end_location, fix}
                    code = item.get("code", "")
                    message = item.get("message", "")
                    location = item.get("location", {})
                    fix = item.get("fix", None)

                    # Determine severity from rule code
                    severity = self._determine_severity(code)

                    # Determine if fixable
                    fixable = fix is not None

                    issue = CodeIssue(
                        file_path=location.get("filename", ""),
                        line=location.get("row", 0),
                        column=location.get("column", None),
                        rule=code,
                        message=message,
                        severity=severity,
                        fixable=fixable,
                    )
                    issues.append(issue)

        except subprocess.TimeoutExpired:
            logger.error("Ruff check timed out")
        except FileNotFoundError:
            logger.error("Ruff not found. Install with: pip install ruff")
        except Exception as e:
            logger.error(f"Error running Ruff: {e}")

        return issues

    def _run_security_checks(self, repo_path: str) -> List[CodeIssue]:
        """Run basic security checks"""
        issues: List[CodeIssue] = []

        # Basic security patterns to check
        security_patterns = [
            {
                "pattern": r"password\s*=\s*['\"][^'\"]+['\"]",
                "rule": "SEC001",
                "message": "Hardcoded password detected. Use environment variables instead.",
                "severity": "error",
            },
            {
                "pattern": r"api[_-]?key\s*=\s*['\"][^'\"]+['\"]",
                "rule": "SEC002",
                "message": "Hardcoded API key detected. Use environment variables instead.",
                "severity": "error",
            },
            {
                "pattern": r"eval\s*\(",
                "rule": "SEC003",
                "message": "Use of eval() is dangerous. Consider safer alternatives.",
                "severity": "error",
            },
            {
                "pattern": r"exec\s*\(",
                "rule": "SEC004",
                "message": "Use of exec() is dangerous. Consider safer alternatives.",
                "severity": "error",
            },
            {
                "pattern": r"subprocess\.call|subprocess\.Popen.*shell\s*=\s*True",
                "rule": "SEC005",
                "message": "Shell injection risk. Avoid shell=True or sanitize input.",
                "severity": "warning",
            },
        ]

        try:
            repo_path_obj = Path(repo_path)

            # Scan Python files
            for py_file in repo_path_obj.rglob("*.py"):
                # Skip excluded patterns
                if any(
                    excluded in str(py_file)
                    for excluded in self.config.ruff_exclude_patterns
                ):
                    continue

                try:
                    content = py_file.read_text(encoding="utf-8")

                    # Check each pattern
                    for pattern_info in security_patterns:
                        import re

                        matches = re.finditer(
                            pattern_info["pattern"],
                            content,
                            re.IGNORECASE | re.MULTILINE,
                        )

                        for match in matches:
                            # Calculate line number
                            line_num = content[: match.start()].count("\n") + 1

                            issue = CodeIssue(
                                file_path=str(py_file.relative_to(repo_path_obj)),
                                line=line_num,
                                column=match.start()
                                - content.rfind("\n", 0, match.start())
                                - 1,
                                rule=pattern_info["rule"],
                                message=pattern_info["message"],
                                severity=pattern_info["severity"],
                                fixable=False,
                            )
                            issues.append(issue)

                except Exception as e:
                    logger.debug(f"Error scanning {py_file}: {e}")
                    continue

        except Exception as e:
            logger.error(f"Error running security checks: {e}")

        return issues

    def _determine_severity(self, rule_code: str) -> str:
        """Determine severity from Ruff rule code"""
        # Ruff rule codes: E = error, W = warning, F = error (flake8), etc.
        if rule_code.startswith("E") or rule_code.startswith("F"):
            return "error"
        elif rule_code.startswith("W") or rule_code.startswith("I"):
            return "warning"
        else:
            return "info"

    def _filter_by_severity(self, issues: List[CodeIssue]) -> List[CodeIssue]:
        """Filter issues by minimum severity threshold"""
        severity_order = {"error": 0, "warning": 1, "info": 2}
        min_severity = severity_order.get(self.config.min_severity_to_comment, 1)

        filtered = [
            issue
            for issue in issues
            if severity_order.get(issue.severity, 2) <= min_severity
        ]

        return filtered
