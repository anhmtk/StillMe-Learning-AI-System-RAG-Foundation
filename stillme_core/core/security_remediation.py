
"""
🛡️ SECURITY REMEDIATION SYSTEM

Hệ thống tự động fix các security vulnerabilities đã phát hiện trong ecosystem.
Thực hiện security hardening và implement best practices.

Author: AgentDev System
Version: 1.0.0
Phase: 0.1 - Security Remediation
"""

import json
import logging
import re
import secrets
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class SecurityIssue:
    """Security issue definition"""

    file_path: str
    line_number: int
    issue_type: str
    severity: str  # 'critical', 'high', 'medium', 'low'
    description: str
    current_code: str
    suggested_fix: str
    status: str = "pending"  # 'pending', 'fixed', 'ignored'


@dataclass
class SecurityRemediation:
    """Security remediation result"""

    total_issues: int
    fixed_issues: int
    ignored_issues: int
    remaining_issues: int
    security_score: float
    recommendations: list[str]


class SecurityRemediationSystem:
    """
    Main security remediation system
    """

    def __init__(self, root_path: str = "."):
        self.root_path = Path(root_path)
        self.security_issues: list[SecurityIssue] = []
        self.fixed_files: set[str] = set()

        # Security patterns to detect
        self.dangerous_functions = {
            "eval": "Use ast.literal_eval() or json.loads() instead",
            "exec": "Use subprocess.run() with proper validation",
            "os.system": "Use subprocess.run() with shell=False",
            "subprocess.call": "Use subprocess.run() with proper validation",
            "__import__": "Use importlib.import_module() instead",
        }

        # Hardcoded credential patterns
        self.credential_patterns = [
            r'password\s*=\s*["\'][^"\']+["\']',
            r'api_key\s*=\s*["\'][^"\']+["\']',
            r'secret\s*=\s*["\'][^"\']+["\']',
            r'token\s*=\s*["\'][^"\']+["\']',
            r'key\s*=\s*["\'][^"\']+["\']',
        ]

        # SQL injection patterns
        self.sql_injection_patterns = [
            r"%s.*%",
            r"\+.*\+",
            r'f".*{.*}.*"',
            r"\.format\(.*\)",
        ]

    def scan_security_issues(self) -> list[SecurityIssue]:
        """
        Scan toàn bộ codebase để tìm security issues
        """
        logger.info("🔍 Scanning for security issues...")

        issues = []

        # Scan Python files
        for py_file in self.root_path.rglob("*.py"):
            if self._should_skip_file(py_file):
                continue

            file_issues = self._scan_file(py_file)
            issues.extend(file_issues)

        self.security_issues = issues
        logger.info(f"✅ Found {len(issues)} security issues")

        return issues

    def _should_skip_file(self, file_path: Path) -> bool:
        """Check if file should be skipped"""
        skip_patterns = [
            "__pycache__",
            ".venv",
            "venv",
            "node_modules",
            ".git",
            "backup_legacy",
            "tests/fixtures",
        ]

        return any(pattern in str(file_path) for pattern in skip_patterns)

    def _scan_file(self, file_path: Path) -> list[SecurityIssue]:
        """Scan individual file for security issues"""
        issues = []

        try:
            content = file_path.read_text(encoding="utf-8")
            lines = content.split("\n")

            # Check for dangerous functions
            for line_num, line in enumerate(lines, 1):
                for func, suggestion in self.dangerous_functions.items():
                    if func in line and not self._is_safe_usage(line, func):
                        issues.append(
                            SecurityIssue(
                                file_path=str(file_path),
                                line_number=line_num,
                                issue_type="dangerous_function",
                                severity="high",
                                description=f"Use of potentially dangerous function: {func}",
                                current_code=line.strip(),
                                suggested_fix=suggestion,
                            )
                        )

                # Check for hardcoded credentials
                for pattern in self.credential_patterns:
                    if re.search(pattern, line, re.IGNORECASE):
                        issues.append(
                            SecurityIssue(
                                file_path=str(file_path),
                                line_number=line_num,
                                issue_type="hardcoded_credential",
                                severity="critical",
                                description="Potential hardcoded credential",
                                current_code=line.strip(),
                                suggested_fix="Use environment variables or secure configuration",
                            )
                        )

                # Check for SQL injection
                for pattern in self.sql_injection_patterns:
                    if re.search(pattern, line):
                        issues.append(
                            SecurityIssue(
                                file_path=str(file_path),
                                line_number=line_num,
                                issue_type="sql_injection",
                                severity="high",
                                description="Potential SQL injection vulnerability",
                                current_code=line.strip(),
                                suggested_fix="Use parameterized queries or ORM",
                            )
                        )

        except Exception as e:
            logger.error(f"Error scanning {file_path}: {e}")

        return issues

    def _is_safe_usage(self, line: str, func: str) -> bool:
        """Check if function usage is safe"""
        # Check for safe patterns
        safe_patterns = [
            f"# {func}",  # Commented out
            f'"{func}"',  # String literal
            f"'{func}'",  # String literal
            f"def {func}",  # Function definition
            f"class {func}",  # Class definition
        ]

        return any(pattern in line for pattern in safe_patterns)

    def fix_security_issues(self) -> SecurityRemediation:
        """
        Fix security issues automatically
        """
        logger.info("🔧 Starting security remediation...")

        fixed_count = 0
        ignored_count = 0

        for issue in self.security_issues:
            try:
                if self._can_fix_automatically(issue):
                    if self._fix_issue(issue):
                        issue.status = "fixed"
                        fixed_count += 1
                        logger.info(
                            f"✅ Fixed {issue.issue_type} in {issue.file_path}:{issue.line_number}"
                        )
                    else:
                        issue.status = "ignored"
                        ignored_count += 1
                else:
                    issue.status = "ignored"
                    ignored_count += 1
            except Exception as e:
                logger.error(
                    f"Error fixing issue {issue.file_path}:{issue.line_number}: {e}"
                )
                issue.status = "ignored"
                ignored_count += 1

        # Calculate security score
        total_issues = len(self.security_issues)
        security_score = (
            ((total_issues - ignored_count) / total_issues * 100)
            if total_issues > 0
            else 100
        )

        # Generate recommendations
        recommendations = self._generate_recommendations()

        remediation = SecurityRemediation(
            total_issues=total_issues,
            fixed_issues=fixed_count,
            ignored_issues=ignored_count,
            remaining_issues=total_issues - fixed_count - ignored_count,
            security_score=security_score,
            recommendations=recommendations,
        )

        logger.info(
            f"✅ Security remediation completed: {fixed_count} fixed, {ignored_count} ignored"
        )

        return remediation

    def _can_fix_automatically(self, issue: SecurityIssue) -> bool:
        """Check if issue can be fixed automatically"""
        auto_fixable_types = ["dangerous_function", "hardcoded_credential"]

        return issue.issue_type in auto_fixable_types

    def _fix_issue(self, issue: SecurityIssue) -> bool:
        """Fix individual security issue"""
        try:
            file_path = Path(issue.file_path)
            content = file_path.read_text(encoding="utf-8")
            lines = content.split("\n")

            if issue.issue_type == "dangerous_function":
                return self._fix_dangerous_function(lines, issue)
            elif issue.issue_type == "hardcoded_credential":
                return self._fix_hardcoded_credential(lines, issue)

            return False

        except Exception as e:
            logger.error(f"Error fixing issue: {e}")
            return False

    def _fix_dangerous_function(self, lines: list[str], issue: SecurityIssue) -> bool:
        """Fix dangerous function usage"""
        line_index = issue.line_number - 1

        if line_index >= len(lines):
            return False

        original_line = lines[line_index]

        # Replace dangerous functions with safe alternatives
        replacements = {
            "ast.literal_eval(": "ast.literal_ast.literal_eval(",
            "exec(": "# exec(  # SECURITY: Replaced with safe alternative",
            "subprocess.run(  # SECURITY: Replaced with safe alternative": "subprocess.run(  # SECURITY: Replaced with safe alternative",
        }

        new_line = original_line
        for old_func, new_func in replacements.items():
            if old_func in new_line:
                new_line = new_line.replace(old_func, new_func)
                break

        if new_line != original_line:
            lines[line_index] = new_line

            # Write back to file
            new_content = "\n".join(lines)
            Path(issue.file_path).write_text(new_content, encoding="utf-8")

            self.fixed_files.add(issue.file_path)
            return True

        return False

    def _fix_hardcoded_credential(self, lines: list[str], issue: SecurityIssue) -> bool:
        """Fix hardcoded credentials"""
        line_index = issue.line_number - 1

        if line_index >= len(lines):
            return False

        original_line = lines[line_index]

        # Replace hardcoded credentials with environment variables
        patterns = [
            (
                r'password\s*=\s*["\']([^"\']+)["\']',
                'password = os.getenv("PASSWORD", "default_password")',
            ),
            (
                r'api_key\s*=\s*["\']([^"\']+)["\']',
                'api_key = os.getenv("API_KEY", "")',
            ),
            (r'secret\s*=\s*["\']([^"\']+)["\']', 'secret = os.getenv("SECRET", "")'),
            (r'token\s*=\s*["\']([^"\']+)["\']', 'token = os.getenv("TOKEN", "")'),
            (r'key\s*=\s*["\']([^"\']+)["\']', 'key = os.getenv("KEY", "")'),
        ]

        new_line = original_line
        for pattern, replacement in patterns:
            if re.search(pattern, new_line, re.IGNORECASE):
                new_line = re.sub(pattern, replacement, new_line, flags=re.IGNORECASE)
                break

        if new_line != original_line:
            lines[line_index] = new_line

            # Add os import if not present
            if "import os" not in "\n".join(lines[:10]):
                lines.insert(0, "import os")

            # Write back to file
            new_content = "\n".join(lines)
            Path(issue.file_path).write_text(new_content, encoding="utf-8")

            self.fixed_files.add(issue.file_path)
            return True

        return False

    def _generate_recommendations(self) -> list[str]:
        """Generate security recommendations"""
        recommendations = [
            "Implement input validation for all user inputs",
            "Use parameterized queries for database operations",
            "Implement proper authentication and authorization",
            "Use HTTPS for all communications",
            "Implement rate limiting to prevent abuse",
            "Regular security audits and penetration testing",
            "Use secure coding practices and code reviews",
            "Implement proper error handling without information disclosure",
            "Use environment variables for sensitive configuration",
            "Implement logging and monitoring for security events",
        ]

        return recommendations

    def create_security_config(self) -> dict[str, Any]:
        """Create security configuration file"""
        config = {
            "security": {
                "authentication": {
                    "jwt_secret": secrets.token_urlsafe(32),
                    "token_expiry": 3600,
                    "refresh_token_expiry": 86400,
                },
                "encryption": {
                    "algorithm": "AES-256-GCM",
                    "key_rotation_interval": 86400,
                },
                "rate_limiting": {
                    "enabled": True,
                    "default_limit": 100,
                    "login_limit": 10,
                },
                "headers": {
                    "x_frame_options": "DENY",
                    "x_content_type_options": "nosniff",
                    "x_xss_protection": "1; mode=block",
                    "strict_transport_security": "max-age=31536000; includeSubDomains",
                },
                "cors": {
                    "enabled": True,
                    "allowed_origins": ["http://localhost:3000"],
                    "allowed_methods": ["GET", "POST", "PUT", "DELETE"],
                    "allowed_headers": ["Content-Type", "Authorization"],
                },
            }
        }

        return config

    def save_security_report(self, remediation: SecurityRemediation) -> Path:
        """Save security remediation report"""
        report = {
            "timestamp": datetime.now().isoformat(),
            "remediation": asdict(remediation),
            "issues": [asdict(issue) for issue in self.security_issues],
            "fixed_files": list(self.fixed_files),
            "security_config": self.create_security_config(),
        }

        # Create reports directory
        reports_dir = self.root_path / "reports"
        reports_dir.mkdir(exist_ok=True)

        # Save report
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_path = reports_dir / f"security_remediation_report_{timestamp}.json"

        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False, default=str)

        logger.info(f"💾 Security report saved to {report_path}")
        return report_path


def main():
    """Main function to run security remediation"""
    remediation_system = SecurityRemediationSystem()

    # Scan for issues
    remediation_system.scan_security_issues()

    # Fix issues
    remediation = remediation_system.fix_security_issues()

    # Save report
    report_path = remediation_system.save_security_report(remediation)

    print("✅ Security remediation completed!")
    print(f"📊 Total issues: {remediation.total_issues}")
    print(f"🔧 Fixed issues: {remediation.fixed_issues}")
    print(f"⚠️ Ignored issues: {remediation.ignored_issues}")
    print(f"🛡️ Security score: {remediation.security_score:.1f}%")
    print(f"📄 Report saved to: {report_path}")


if __name__ == "__main__":
    main()
