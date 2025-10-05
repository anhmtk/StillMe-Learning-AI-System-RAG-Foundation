# stillme_core/security/security_scanner.py
"""
Security scanner with Bandit and Semgrep integration
"""

from __future__ import annotations

import json
import logging
import re
import subprocess
import time
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class VulnerabilityLevel(Enum):
    """Vulnerability severity levels"""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


@dataclass
class SecurityIssue:
    """Security issue representation"""

    tool: str
    level: VulnerabilityLevel
    rule_id: str
    description: str
    file_path: str
    line_number: int
    code_snippet: str
    confidence: str
    cwe_id: str | None = None
    owasp_category: str | None = None
    remediation: str | None = None


@dataclass
class SecurityReport:
    """Comprehensive security report"""

    total_issues: int
    issues_by_level: dict[VulnerabilityLevel, int]
    issues_by_tool: dict[str, int]
    issues: list[SecurityIssue]
    recommendations: list[str]
    risk_score: float
    scan_duration: float


class SecurityScanner:
    """
    Comprehensive security scanner with multiple tools integration
    """

    def __init__(self, repo_root: str = "."):
        self.repo_root = Path(repo_root)
        self.tools_available = self._check_available_tools()
        self.secret_patterns = self._load_secret_patterns()

    def _check_available_tools(self) -> dict[str, bool]:
        """Check which security tools are available"""
        tools = {}

        # Check Bandit
        try:
            result = subprocess.run(
                ["bandit", "--version"], capture_output=True, text=True, timeout=5
            )
            tools["bandit"] = result.returncode == 0
        except Exception:
            tools["bandit"] = False

        # Check Semgrep
        try:
            result = subprocess.run(
                ["semgrep", "--version"], capture_output=True, text=True, timeout=5
            )
            tools["semgrep"] = result.returncode == 0
        except Exception:
            tools["semgrep"] = False

        # Check Safety (for dependency vulnerabilities)
        try:
            result = subprocess.run(
                ["safety", "--version"], capture_output=True, text=True, timeout=5
            )
            tools["safety"] = result.returncode == 0
        except Exception:
            tools["safety"] = False

        return tools

    def _load_secret_patterns(self) -> list[dict[str, Any]]:
        """Load patterns for detecting secrets"""
        return [
            {
                "name": "API Key",
                "pattern": r"(?i)(api[_-]?key|apikey)\s*[=:]\s*['\"]?([a-zA-Z0-9]{20,})['\"]?",
                "level": VulnerabilityLevel.HIGH,
            },
            {
                "name": "Secret Key",
                "pattern": r"(?i)(secret[_-]?key|secretkey)\s*[=:]\s*['\"]?([a-zA-Z0-9]{20,})['\"]?",
                "level": VulnerabilityLevel.HIGH,
            },
            {
                "name": "Password",
                "pattern": r"(?i)(password|passwd|pwd)\s*[=:]\s*['\"]?([^\s'\"\n]{8,})['\"]?",
                "level": VulnerabilityLevel.MEDIUM,
            },
            {
                "name": "Database URL",
                "pattern": r"(?i)(database[_-]?url|db[_-]?url)\s*[=:]\s*['\"]?(postgresql|mysql|mongodb)://[^\s'\"]+['\"]?",
                "level": VulnerabilityLevel.MEDIUM,
            },
            {
                "name": "JWT Token",
                "pattern": r"eyJ[A-Za-z0-9_-]*\.[A-Za-z0-9_-]*\.[A-Za-z0-9_-]*",
                "level": VulnerabilityLevel.MEDIUM,
            },
            {
                "name": "AWS Access Key",
                "pattern": r"AKIA[0-9A-Z]{16}",
                "level": VulnerabilityLevel.HIGH,
            },
            {
                "name": "Private Key",
                "pattern": r"-----BEGIN (RSA )?PRIVATE KEY-----",
                "level": VulnerabilityLevel.CRITICAL,
            },
        ]

    def scan_repository(self, include_tests: bool = False) -> SecurityReport:
        """Perform comprehensive security scan"""
        start_time = time.time()
        all_issues = []

        # Run Bandit scan
        if self.tools_available.get("bandit"):
            bandit_issues = self._run_bandit_scan(include_tests)
            all_issues.extend(bandit_issues)

        # Run Semgrep scan
        if self.tools_available.get("semgrep"):
            semgrep_issues = self._run_semgrep_scan(include_tests)
            all_issues.extend(semgrep_issues)

        # Run Safety scan for dependencies
        if self.tools_available.get("safety"):
            safety_issues = self._run_safety_scan()
            all_issues.extend(safety_issues)

        # Run custom secret detection
        secret_issues = self._run_secret_detection()
        all_issues.extend(secret_issues)

        # Run custom vulnerability patterns
        custom_issues = self._run_custom_patterns()
        all_issues.extend(custom_issues)

        scan_duration = time.time() - start_time

        # Generate report
        return self._generate_security_report(all_issues, scan_duration)

    def _run_bandit_scan(self, include_tests: bool) -> list[SecurityIssue]:
        """Run Bandit security scan"""
        issues = []

        try:
            args = ["bandit", "-r", "-f", "json"]
            if not include_tests:
                args.extend(["-x", "tests/", "-x", "test_*.py"])

            result = subprocess.run(
                args, cwd=self.repo_root, capture_output=True, text=True, timeout=60
            )

            if result.returncode in [0, 1]:  # 0 = no issues, 1 = issues found
                data = json.loads(result.stdout)

                for issue in data.get("results", []):
                    security_issue = SecurityIssue(
                        tool="bandit",
                        level=VulnerabilityLevel(
                            issue.get("issue_severity", "low").lower()
                        ),
                        rule_id=issue.get("test_id", "unknown"),
                        description=issue.get("issue_text", ""),
                        file_path=issue.get("filename", ""),
                        line_number=issue.get("line_number", 0),
                        code_snippet=issue.get("code", ""),
                        confidence=issue.get("issue_confidence", "medium"),
                        cwe_id=(
                            issue.get("issue_cwe", {}).get("id")
                            if issue.get("issue_cwe")
                            else None
                        ),
                    )
                    issues.append(security_issue)

        except Exception as e:
            logger.error(f"Bandit scan failed: {e}")

        return issues

    def _run_semgrep_scan(self, include_tests: bool) -> list[SecurityIssue]:
        """Run Semgrep security scan"""
        issues = []

        try:
            args = ["semgrep", "--config=auto", "--json", "--no-git-ignore"]
            if not include_tests:
                args.extend(["--exclude", "tests/", "--exclude", "test_*.py"])

            result = subprocess.run(
                args, cwd=self.repo_root, capture_output=True, text=True, timeout=120
            )

            if result.returncode in [0, 1]:  # 0 = no issues, 1 = issues found
                data = json.loads(result.stdout)

                for result_item in data.get("results", []):
                    # Map Semgrep severity to our levels
                    severity_map = {
                        "ERROR": VulnerabilityLevel.CRITICAL,
                        "WARNING": VulnerabilityLevel.HIGH,
                        "INFO": VulnerabilityLevel.MEDIUM,
                    }

                    security_issue = SecurityIssue(
                        tool="semgrep",
                        level=severity_map.get(
                            result_item.get("extra", {}).get("severity", "INFO"),
                            VulnerabilityLevel.MEDIUM,
                        ),
                        rule_id=result_item.get("check_id", "unknown"),
                        description=result_item.get("extra", {}).get("message", ""),
                        file_path=result_item.get("path", ""),
                        line_number=result_item.get("start", {}).get("line", 0),
                        code_snippet=result_item.get("extra", {}).get("lines", ""),
                        confidence="high",  # Semgrep is generally high confidence
                    )
                    issues.append(security_issue)

        except Exception as e:
            logger.error(f"Semgrep scan failed: {e}")

        return issues

    def _run_safety_scan(self) -> list[SecurityIssue]:
        """Run Safety scan for dependency vulnerabilities"""
        issues = []

        try:
            result = subprocess.run(
                ["safety", "check", "--json"],
                cwd=self.repo_root,
                capture_output=True,
                text=True,
                timeout=60,
            )

            if result.returncode == 1:  # Vulnerabilities found
                data = json.loads(result.stdout)

                for vuln in data:
                    security_issue = SecurityIssue(
                        tool="safety",
                        level=VulnerabilityLevel.HIGH,  # Dependency vulns are usually high
                        rule_id=vuln.get("id", "unknown"),
                        description=f"Vulnerable dependency: {vuln.get('package', 'unknown')} {vuln.get('installed_version', 'unknown')}",
                        file_path="requirements.txt",
                        line_number=0,
                        code_snippet=f"{vuln.get('package', 'unknown')}=={vuln.get('installed_version', 'unknown')}",
                        confidence="high",
                        remediation=f"Update to version {vuln.get('specs', 'latest')}",
                    )
                    issues.append(security_issue)

        except Exception as e:
            logger.error(f"Safety scan failed: {e}")

        return issues

    def _run_secret_detection(self) -> list[SecurityIssue]:
        """Run custom secret detection"""
        issues = []

        try:
            for py_file in self.repo_root.rglob("*.py"):
                if "test" in str(py_file).lower():
                    continue

                with open(py_file, encoding="utf-8") as f:
                    content = f.read()

                for pattern_info in self.secret_patterns:
                    matches = re.finditer(pattern_info["pattern"], content)

                    for match in matches:
                        security_issue = SecurityIssue(
                            tool="secret_detection",
                            level=VulnerabilityLevel(pattern_info["level"]),
                            rule_id=f"secret_{pattern_info['name'].lower().replace(' ', '_')}",
                            description=f"Potential {pattern_info['name']} detected",
                            file_path=str(py_file),
                            line_number=content[: match.start()].count("\n") + 1,
                            code_snippet=match.group(0),
                            confidence="medium",
                            remediation="Remove or properly secure the secret",
                        )
                        issues.append(security_issue)

        except Exception as e:
            logger.error(f"Secret detection failed: {e}")

        return issues

    def _run_custom_patterns(self) -> list[SecurityIssue]:
        """Run custom vulnerability patterns"""
        issues = []

        custom_patterns = [
            {
                "name": "SQL Injection",
                "pattern": r"(?i)(execute|query|fetchall|fetchone)\s*\(\s*['\"].*%s.*['\"]",
                "level": VulnerabilityLevel.HIGH,
                "description": "Potential SQL injection vulnerability",
            },
            {
                "name": "Command Injection",
                "pattern": r"(?i)(os\.system|subprocess\.call|subprocess\.run)\s*\(\s*['\"].*\+.*['\"]",
                "level": VulnerabilityLevel.HIGH,
                "description": "Potential command injection vulnerability",
            },
            {
                "name": "Path Traversal",
                "pattern": r"(?i)(open|file)\s*\(\s*['\"].*\.\./.*['\"]",
                "level": VulnerabilityLevel.MEDIUM,
                "description": "Potential path traversal vulnerability",
            },
            {
                "name": "Hardcoded Credentials",
                "pattern": r"(?i)(username|password|user|pass)\s*[=:]\s*['\"][^'\"]{3,}['\"]",
                "level": VulnerabilityLevel.MEDIUM,
                "description": "Hardcoded credentials detected",
            },
        ]

        try:
            for py_file in self.repo_root.rglob("*.py"):
                if "test" in str(py_file).lower():
                    continue

                with open(py_file, encoding="utf-8") as f:
                    content = f.read()

                for pattern_info in custom_patterns:
                    matches = re.finditer(pattern_info["pattern"], content)

                    for match in matches:
                        security_issue = SecurityIssue(
                            tool="custom_patterns",
                            level=VulnerabilityLevel(pattern_info["level"]),
                            rule_id=f"custom_{pattern_info['name'].lower().replace(' ', '_')}",
                            description=pattern_info["description"],
                            file_path=str(py_file),
                            line_number=content[: match.start()].count("\n") + 1,
                            code_snippet=match.group(0),
                            confidence="medium",
                        )
                        issues.append(security_issue)

        except Exception as e:
            logger.error(f"Custom pattern scan failed: {e}")

        return issues

    def _generate_security_report(
        self, issues: list[SecurityIssue], duration: float
    ) -> SecurityReport:
        """Generate comprehensive security report"""
        # Count issues by level
        issues_by_level = dict.fromkeys(VulnerabilityLevel, 0)
        for issue in issues:
            issues_by_level[issue.level] += 1

        # Count issues by tool
        issues_by_tool = {}
        for issue in issues:
            tool = issue.tool
            issues_by_tool[tool] = issues_by_tool.get(tool, 0) + 1

        # Calculate risk score (0-100)
        risk_score = self._calculate_risk_score(issues)

        # Generate recommendations
        recommendations = self._generate_recommendations(issues, issues_by_level)

        return SecurityReport(
            total_issues=len(issues),
            issues_by_level=issues_by_level,
            issues_by_tool=issues_by_tool,
            issues=issues,
            recommendations=recommendations,
            risk_score=risk_score,
            scan_duration=duration,
        )

    def _calculate_risk_score(self, issues: list[SecurityIssue]) -> float:
        """Calculate overall risk score (0-100)"""
        if not issues:
            return 0.0

        # Weight by severity
        weights = {
            VulnerabilityLevel.CRITICAL: 10,
            VulnerabilityLevel.HIGH: 7,
            VulnerabilityLevel.MEDIUM: 4,
            VulnerabilityLevel.LOW: 2,
            VulnerabilityLevel.INFO: 1,
        }

        total_weight = sum(weights[issue.level] for issue in issues)
        max_possible_weight = len(issues) * 10  # All critical

        return min(100.0, (total_weight / max_possible_weight) * 100)

    def _generate_recommendations(
        self,
        issues: list[SecurityIssue],
        issues_by_level: dict[VulnerabilityLevel, int],
    ) -> list[str]:
        """Generate security recommendations"""
        recommendations = []

        # Critical issues
        if issues_by_level[VulnerabilityLevel.CRITICAL] > 0:
            recommendations.append(
                f"🚨 CRITICAL: {issues_by_level[VulnerabilityLevel.CRITICAL]} critical vulnerabilities found. "
                "Address immediately before deployment."
            )

        # High issues
        if issues_by_level[VulnerabilityLevel.HIGH] > 0:
            recommendations.append(
                f"⚠️ HIGH: {issues_by_level[VulnerabilityLevel.HIGH]} high-severity vulnerabilities found. "
                "Review and fix before production deployment."
            )

        # Medium issues
        if issues_by_level[VulnerabilityLevel.MEDIUM] > 0:
            recommendations.append(
                f"📋 MEDIUM: {issues_by_level[VulnerabilityLevel.MEDIUM]} medium-severity issues found. "
                "Consider addressing in next security review."
            )

        # Tool-specific recommendations
        tools_used = {issue.tool for issue in issues}

        if "secret_detection" in tools_used:
            recommendations.append(
                "🔐 SECRETS: Hardcoded secrets detected. Use environment variables or secure secret management."
            )

        if "safety" in tools_used:
            recommendations.append(
                "📦 DEPENDENCIES: Vulnerable dependencies found. Update to latest secure versions."
            )

        if "bandit" in tools_used:
            recommendations.append(
                "🛡️ BANDIT: Security issues detected by Bandit. Review and implement secure coding practices."
            )

        if "semgrep" in tools_used:
            recommendations.append(
                "🔍 SEMGREP: Code patterns with security implications found. Review and refactor."
            )

        # General recommendations
        if len(issues) == 0:
            recommendations.append(
                "✅ No security issues detected. Keep up the good work!"
            )
        elif len(issues) < 5:
            recommendations.append(
                "👍 Good security posture. Address remaining issues for better security."
            )
        else:
            recommendations.append(
                "📈 Consider implementing a security-first development approach."
            )

        return recommendations
