#!/usr/bin/env python3
"""
Security Hardening Script for StillMe AI Framework
==================================================

This script performs comprehensive security hardening checks and fixes.

Author: StillMe AI Framework Team
Version: 1.0.0
Last Updated: 2025-09-26
"""

import argparse
import json
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path


@dataclass
class SecurityIssue:
    """Security issue data structure"""

    severity: str  # CRITICAL, HIGH, MEDIUM, LOW
    category: str  # VULNERABILITY, MISCONFIGURATION, BEST_PRACTICE
    file_path: str
    line_number: int
    description: str
    recommendation: str
    fix_available: bool = False
    fix_code: str = ""


@dataclass
class SecurityReport:
    """Security report data structure"""

    total_issues: int
    critical_issues: int
    high_issues: int
    medium_issues: int
    low_issues: int
    security_score: int  # 0-100
    issues: list[SecurityIssue]
    recommendations: list[str]


class SecurityHardener:
    """Performs security hardening checks and fixes"""

    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root)
        self.security_patterns = self._load_security_patterns()
        self.best_practices = self._load_best_practices()

    def _load_security_patterns(self) -> dict[str, list[str]]:
        """Load security vulnerability patterns"""
        return {
            "sql_injection": [
                r"execute\s*\(\s*['\"].*%s.*['\"]",
                r"cursor\.execute\s*\(\s*['\"].*%s.*['\"]",
                r"query\s*=\s*['\"].*\+.*['\"]",
                r"f['\"].*SELECT.*{.*}.*['\"]",
            ],
            "xss": [
                r"innerHTML\s*=",
                r"document\.write\s*\(",
                r"eval\s*\(",
                r"setTimeout\s*\(\s*['\"].*['\"]",
                r"setInterval\s*\(\s*['\"].*['\"]",
            ],
            "command_injection": [
                r"os\.system\s*\(",
                r"subprocess\.run\s*\(\s*['\"].*['\"]",
                r"subprocess\.call\s*\(\s*['\"].*['\"]",
                r"subprocess\.Popen\s*\(\s*['\"].*['\"]",
                r"shell\s*=\s*True",
            ],
            "path_traversal": [
                r"open\s*\(\s*.*\.\./",
                r"Path\s*\(\s*.*\.\./",
                r"os\.path\.join\s*\(\s*.*\.\./",
                r"\.\./.*\.\./",
                r"\.\.\\\.\.\\",
            ],
            "hardcoded_secrets": [
                r"password\s*=\s*['\"][^'\"]+['\"]",
                r"api_key\s*=\s*['\"][^'\"]+['\"]",
                r"secret\s*=\s*['\"][^'\"]+['\"]",
                r"token\s*=\s*['\"][^'\"]+['\"]",
                r"key\s*=\s*['\"][^'\"]+['\"]",
            ],
            "insecure_random": [
                r"random\.random\s*\(",
                r"random\.randint\s*\(",
                r"random\.choice\s*\(",
                r"random\.sample\s*\(",
            ],
            "weak_crypto": [
                r"hashlib\.md5\s*\(",
                r"hashlib\.sha1\s*\(",
                r"DES\s*\(",
                r"RC4\s*\(",
                r"MD5\s*\(",
            ],
        }

    def _load_best_practices(self) -> dict[str, list[str]]:
        """Load security best practices"""
        return {
            "input_validation": [
                "Validate all user inputs",
                "Use parameterized queries",
                "Sanitize HTML output",
                "Validate file uploads",
            ],
            "authentication": [
                "Use strong passwords",
                "Implement MFA",
                "Use secure session management",
                "Implement account lockout",
            ],
            "authorization": [
                "Implement RBAC",
                "Use principle of least privilege",
                "Validate permissions on every request",
                "Implement proper session management",
            ],
            "encryption": [
                "Use strong encryption algorithms",
                "Store keys securely",
                "Use HTTPS everywhere",
                "Encrypt sensitive data at rest",
            ],
            "logging": [
                "Log security events",
                "Don't log sensitive data",
                "Use secure logging",
                "Implement log rotation",
            ],
        }

    def scan_security_issues(self) -> SecurityReport:
        """Scan for security issues"""
        print("🔍 Scanning for security issues...")

        issues = []

        # Scan Python files
        python_files = list(self.project_root.rglob("*.py"))
        for file_path in python_files:
            if self._should_skip_file(file_path):
                continue

            file_issues = self._scan_file(file_path)
            issues.extend(file_issues)

        # Run external security tools
        external_issues = self._run_external_security_tools()
        issues.extend(external_issues)

        # Categorize issues
        critical_issues = [i for i in issues if i.severity == "CRITICAL"]
        high_issues = [i for i in issues if i.severity == "HIGH"]
        medium_issues = [i for i in issues if i.severity == "MEDIUM"]
        low_issues = [i for i in issues if i.severity == "LOW"]

        # Calculate security score
        security_score = self._calculate_security_score(issues)

        # Generate recommendations
        recommendations = self._generate_recommendations(issues)

        return SecurityReport(
            total_issues=len(issues),
            critical_issues=len(critical_issues),
            high_issues=len(high_issues),
            medium_issues=len(medium_issues),
            low_issues=len(low_issues),
            security_score=security_score,
            issues=issues,
            recommendations=recommendations,
        )

    def _should_skip_file(self, file_path: Path) -> bool:
        """Check if file should be skipped"""
        skip_patterns = [
            "__pycache__",
            ".git",
            "node_modules",
            ".venv",
            "venv",
            "env",
            "site-packages",
            "dist-packages",
            "build",
            "dist",
        ]

        return any(pattern in str(file_path) for pattern in skip_patterns)

    def _scan_file(self, file_path: Path) -> list[SecurityIssue]:
        """Scan a single file for security issues"""
        issues = []

        try:
            with open(file_path, encoding="utf-8") as f:
                content = f.read()
                lines = content.split("\n")

            for pattern_name, patterns in self.security_patterns.items():
                for pattern in patterns:
                    for line_num, line in enumerate(lines, 1):
                        if re.search(pattern, line, re.IGNORECASE):
                            issue = self._create_security_issue(
                                pattern_name, file_path, line_num, line
                            )
                            issues.append(issue)

            # Check for missing security practices
            missing_practices = self._check_missing_practices(file_path, content)
            issues.extend(missing_practices)

        except Exception as e:
            print(f"⚠️ Error scanning {file_path}: {e}")

        return issues

    def _create_security_issue(
        self, pattern_name: str, file_path: Path, line_num: int, line: str
    ) -> SecurityIssue:
        """Create security issue from pattern match"""
        severity_map = {
            "sql_injection": "CRITICAL",
            "command_injection": "CRITICAL",
            "xss": "HIGH",
            "path_traversal": "HIGH",
            "hardcoded_secrets": "HIGH",
            "insecure_random": "MEDIUM",
            "weak_crypto": "MEDIUM",
        }

        severity = severity_map.get(pattern_name, "LOW")

        description_map = {
            "sql_injection": "Potential SQL injection vulnerability",
            "command_injection": "Potential command injection vulnerability",
            "xss": "Potential XSS vulnerability",
            "path_traversal": "Potential path traversal vulnerability",
            "hardcoded_secrets": "Hardcoded secret detected",
            "insecure_random": "Insecure random number generation",
            "weak_crypto": "Weak cryptographic algorithm",
        }

        recommendation_map = {
            "sql_injection": "Use parameterized queries or ORM",
            "command_injection": "Use subprocess with shell=False and validate inputs",
            "xss": "Sanitize HTML output and use CSP headers",
            "path_traversal": "Validate and sanitize file paths",
            "hardcoded_secrets": "Use environment variables or secure key management",
            "insecure_random": "Use secrets module for cryptographic randomness",
            "weak_crypto": "Use strong cryptographic algorithms (AES-256, SHA-256)",
        }

        return SecurityIssue(
            severity=severity,
            category="VULNERABILITY",
            file_path=str(file_path),
            line_number=line_num,
            description=description_map.get(pattern_name, "Security issue detected"),
            recommendation=recommendation_map.get(
                pattern_name, "Review and fix security issue"
            ),
            fix_available=True,
            fix_code=self._generate_fix_code(pattern_name, line),
        )

    def _generate_fix_code(self, pattern_name: str, line: str) -> str:
        """Generate fix code for security issue"""
        fixes = {
            "sql_injection": '# Use parameterized queries\n# OLD: cursor.execute(f"SELECT * FROM users WHERE id = {user_id}")\n# NEW: cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))',
            "command_injection": '# Use subprocess with shell=False\n# OLD: os.system(f"echo {user_input}")\n# NEW: subprocess.run(["echo", user_input], shell=False)',
            "xss": "# Sanitize HTML output\n# OLD: innerHTML = user_input\n# NEW: textContent = user_input or use DOMPurify",
            "path_traversal": "# Validate file paths\n# OLD: open(user_path)\n# NEW: if os.path.commonpath([base_path, user_path]) == base_path:",
            "hardcoded_secrets": '# Use environment variables\n# OLD: api_key = "sk-1234567890"\n# NEW: api_key = os.getenv("API_KEY")',
            "insecure_random": "# Use secrets module\n# OLD: secrets.randbelow(1, 100)\n# NEW: secrets.randbelow(100) + 1",
            "weak_crypto": "# Use strong algorithms\n# OLD: hashlib.sha256(data)\n# NEW: hashlib.sha256(data)",
        }

        return fixes.get(pattern_name, "# Review and implement secure alternative")

    def _check_missing_practices(
        self, file_path: Path, content: str
    ) -> list[SecurityIssue]:
        """Check for missing security practices"""
        issues = []

        # Check for missing input validation
        if "def " in content and "validate" not in content.lower():
            issues.append(
                SecurityIssue(
                    severity="MEDIUM",
                    category="BEST_PRACTICE",
                    file_path=str(file_path),
                    line_number=1,
                    description="Missing input validation",
                    recommendation="Add input validation for all user inputs",
                )
            )

        # Check for missing error handling
        if "try:" not in content and "except" not in content:
            issues.append(
                SecurityIssue(
                    severity="LOW",
                    category="BEST_PRACTICE",
                    file_path=str(file_path),
                    line_number=1,
                    description="Missing error handling",
                    recommendation="Add proper error handling and logging",
                )
            )

        # Check for missing logging
        if "import logging" not in content and "logger" not in content:
            issues.append(
                SecurityIssue(
                    severity="LOW",
                    category="BEST_PRACTICE",
                    file_path=str(file_path),
                    line_number=1,
                    description="Missing security logging",
                    recommendation="Add security event logging",
                )
            )

        return issues

    def _run_external_security_tools(self) -> list[SecurityIssue]:
        """Run external security tools"""
        issues = []

        # Run bandit
        try:
            result = subprocess.run(
                ["bandit", "-r", str(self.project_root), "-f", "json"],
                capture_output=True,
                text=True,
                cwd=self.project_root,
            )
            if result.returncode == 0:
                bandit_results = json.loads(result.stdout)
                for result_item in bandit_results.get("results", []):
                    issues.append(
                        SecurityIssue(
                            severity=result_item.get("issue_severity", "LOW").upper(),
                            category="VULNERABILITY",
                            file_path=result_item.get("filename", ""),
                            line_number=result_item.get("line_number", 0),
                            description=result_item.get("issue_text", ""),
                            recommendation=result_item.get("issue_confidence", ""),
                            fix_available=False,
                        )
                    )
        except Exception as e:
            print(f"⚠️ Error running bandit: {e}")

        # Run safety
        try:
            result = subprocess.run(
                ["safety", "check", "--json"],
                capture_output=True,
                text=True,
                cwd=self.project_root,
            )
            if result.returncode != 0:
                safety_results = json.loads(result.stdout)
                for vuln in safety_results:
                    issues.append(
                        SecurityIssue(
                            severity="HIGH",
                            category="VULNERABILITY",
                            file_path="requirements.txt",
                            line_number=0,
                            description=f"Vulnerable dependency: {vuln.get('package', '')}",
                            recommendation=f"Update to version {vuln.get('secure_version', 'latest')}",
                            fix_available=True,
                        )
                    )
        except Exception as e:
            print(f"⚠️ Error running safety: {e}")

        return issues

    def _calculate_security_score(self, issues: list[SecurityIssue]) -> int:
        """Calculate security score (0-100)"""
        if not issues:
            return 100

        critical_count = len([i for i in issues if i.severity == "CRITICAL"])
        high_count = len([i for i in issues if i.severity == "HIGH"])
        medium_count = len([i for i in issues if i.severity == "MEDIUM"])
        low_count = len([i for i in issues if i.severity == "LOW"])

        # Calculate score based on severity weights
        score = 100
        score -= critical_count * 20  # -20 points per critical
        score -= high_count * 10  # -10 points per high
        score -= medium_count * 5  # -5 points per medium
        score -= low_count * 1  # -1 point per low

        return max(0, score)

    def _generate_recommendations(self, issues: list[SecurityIssue]) -> list[str]:
        """Generate security recommendations"""
        recommendations = []

        critical_issues = [i for i in issues if i.severity == "CRITICAL"]
        high_issues = [i for i in issues if i.severity == "HIGH"]

        if critical_issues:
            recommendations.append(
                "🔴 CRITICAL: Fix all critical security vulnerabilities immediately"
            )

        if high_issues:
            recommendations.append(
                "🟠 HIGH: Address high-severity security issues within 1 week"
            )

        if any(i.category == "VULNERABILITY" for i in issues):
            recommendations.append(
                "🛡️ Implement comprehensive input validation and sanitization"
            )

        if any("hardcoded" in i.description.lower() for i in issues):
            recommendations.append(
                "🔐 Replace hardcoded secrets with secure key management"
            )

        if any("injection" in i.description.lower() for i in issues):
            recommendations.append("💉 Use parameterized queries and input validation")

        if any("xss" in i.description.lower() for i in issues):
            recommendations.append("🌐 Implement XSS protection with CSP headers")

        recommendations.append("📊 Implement continuous security monitoring")
        recommendations.append("🔍 Add automated security testing to CI/CD")
        recommendations.append("📚 Provide security training for development team")

        return recommendations

    def generate_security_report(self, report: SecurityReport) -> str:
        """Generate comprehensive security report"""
        report_content = f"""
# Security Hardening Report
Generated: {self._get_current_timestamp()}

## Executive Summary
- **Total Issues**: {report.total_issues}
- **Critical Issues**: {report.critical_issues}
- **High Issues**: {report.high_issues}
- **Medium Issues**: {report.medium_issues}
- **Low Issues**: {report.low_issues}
- **Security Score**: {report.security_score}/100

## Security Status
"""

        if report.security_score >= 90:
            report_content += "✅ **EXCELLENT** - Security posture is strong\n\n"
        elif report.security_score >= 75:
            report_content += "🟡 **GOOD** - Some improvements needed\n\n"
        elif report.security_score >= 50:
            report_content += "🟠 **FAIR** - Significant improvements required\n\n"
        else:
            report_content += "🔴 **POOR** - Immediate security attention required\n\n"

        # Critical issues
        if report.critical_issues > 0:
            report_content += "## 🔴 Critical Issues (Immediate Action Required)\n\n"
            critical_issues = [i for i in report.issues if i.severity == "CRITICAL"]
            for issue in critical_issues[:5]:  # Top 5
                report_content += f"### {issue.file_path}:{issue.line_number}\n"
                report_content += f"- **Description**: {issue.description}\n"
                report_content += f"- **Recommendation**: {issue.recommendation}\n"
                if issue.fix_available:
                    report_content += f"- **Fix**: {issue.fix_code}\n"
                report_content += "\n"

        # High issues
        if report.high_issues > 0:
            report_content += "## 🟠 High Priority Issues (Address within 1 week)\n\n"
            high_issues = [i for i in report.issues if i.severity == "HIGH"]
            for issue in high_issues[:5]:  # Top 5
                report_content += f"### {issue.file_path}:{issue.line_number}\n"
                report_content += f"- **Description**: {issue.description}\n"
                report_content += f"- **Recommendation**: {issue.recommendation}\n\n"

        # Recommendations
        report_content += "## 🎯 Security Recommendations\n\n"
        for i, rec in enumerate(report.recommendations, 1):
            report_content += f"{i}. {rec}\n"

        # Best practices
        report_content += "\n## 📚 Security Best Practices\n\n"
        for category, practices in self.best_practices.items():
            report_content += f"### {category.title()}\n"
            for practice in practices:
                report_content += f"- {practice}\n"
            report_content += "\n"

        # Action plan
        report_content += "## 📋 Action Plan\n\n"
        if report.critical_issues > 0:
            report_content += "### Immediate (Next 24 hours)\n"
            report_content += "- Fix all critical security vulnerabilities\n"
            report_content += "- Implement emergency security measures\n"
            report_content += "- Notify security team\n\n"

        if report.high_issues > 0:
            report_content += "### Short-term (Next 1 week)\n"
            report_content += "- Address all high-severity issues\n"
            report_content += "- Implement input validation\n"
            report_content += "- Add security logging\n\n"

        report_content += "### Medium-term (Next 1 month)\n"
        report_content += "- Implement comprehensive security testing\n"
        report_content += "- Add automated security scanning\n"
        report_content += "- Conduct security training\n\n"

        report_content += "### Long-term (Ongoing)\n"
        report_content += "- Regular security audits\n"
        report_content += "- Continuous monitoring\n"
        report_content += "- Security culture development\n\n"

        return report_content

    def _get_current_timestamp(self) -> str:
        """Get current timestamp"""
        from datetime import datetime

        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def save_report(
        self,
        report_content: str,
        output_file: str = "artifacts/security_hardening_report.md",
    ):
        """Save security report to file"""
        output_path = self.project_root / output_file
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(report_content)

        print(f"📄 Security report saved to: {output_path}")


def main():
    """Main function"""
    parser = argparse.ArgumentParser(
        description="Security hardening for StillMe AI Framework"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="artifacts/security_hardening_report.md",
        help="Output file path",
    )
    parser.add_argument(
        "--project-root", type=str, default=".", help="Project root directory"
    )

    args = parser.parse_args()

    print("🔒 Starting security hardening analysis...")
    print(f"📁 Project root: {args.project_root}")

    # Initialize hardener
    hardener = SecurityHardener(args.project_root)

    # Run security scan
    report = hardener.scan_security_issues()

    # Generate report
    report_content = hardener.generate_security_report(report)
    hardener.save_report(report_content, args.output)

    # Print summary
    print("\n🔒 Security Summary:")
    print(f"   Total Issues: {report.total_issues}")
    print(f"   Critical: {report.critical_issues}")
    print(f"   High: {report.high_issues}")
    print(f"   Medium: {report.medium_issues}")
    print(f"   Low: {report.low_issues}")
    print(f"   Security Score: {report.security_score}/100")

    if report.security_score >= 90:
        print("🎉 Excellent security posture!")
    elif report.security_score >= 75:
        print("🟡 Good security, some improvements needed")
    elif report.security_score >= 50:
        print("🟠 Fair security, significant improvements required")
    else:
        print("🔴 Poor security, immediate attention required")

    print(f"\n📄 Detailed report: {args.output}")


if __name__ == "__main__":
    main()
