"""
StillMe Secrets & PII Sweep
Comprehensive scanning for secrets, API keys, and PII in codebase.
"""

import json
import re
import subprocess
import sys
from pathlib import Path


class SecretPattern:
    """Represents a secret detection pattern."""

    def __init__(
        self,
        name: str,
        pattern: str,
        severity: str,
        description: str,
        confidence: float = 1.0,
    ):
        self.name = name
        self.pattern = re.compile(pattern, re.IGNORECASE)
        self.severity = severity  # "high", "medium", "low"
        self.description = description
        self.confidence = confidence


class SecretFinding:
    """Represents a found secret."""

    def __init__(
        self,
        file_path: str,
        line_number: int,
        pattern_name: str,
        matched_text: str,
        severity: str,
        confidence: float = 1.0,
        context: str | None = None,
    ):
        self.file_path = file_path
        self.line_number = line_number
        self.pattern_name = pattern_name
        self.matched_text = matched_text
        self.severity = severity
        self.confidence = confidence
        self.context = context

    def to_dict(self) -> dict:
        return {
            "file_path": self.file_path,
            "line_number": self.line_number,
            "pattern_name": self.pattern_name,
            "matched_text": self.matched_text,
            "severity": self.severity,
            "confidence": self.confidence,
            "context": self.context,
        }


class SecretsSweeper:
    """Scans codebase for secrets and PII."""

    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root)
        self.findings: list[SecretFinding] = []
        self.ignored_files: set[str] = set()
        self.ignored_patterns: set[str] = set()

        # Load ignore patterns
        self._load_ignore_patterns()

        # Define secret patterns
        self._define_secret_patterns()

    def _load_ignore_patterns(self):
        """Load patterns to ignore from .gitignore and custom ignore file."""
        ignore_files = [".gitignore", ".secretsignore"]

        for ignore_file in ignore_files:
            ignore_path = self.project_root / ignore_file
            if ignore_path.exists():
                with open(ignore_path) as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith("#"):
                            self.ignored_patterns.add(line)

    def _define_secret_patterns(self):
        """Define patterns for detecting secrets."""
        self.secret_patterns = [
            # API Keys
            SecretPattern(
                "OpenAI API Key",
                r"sk-[a-zA-Z0-9]{48}",
                "high",
                "OpenAI API key detected",
            ),
            SecretPattern(
                "Generic API Key",
                r"api[_-]?key\s*[:=]\s*['\"]?[a-zA-Z0-9]{20,}['\"]?",
                "high",
                "Generic API key pattern detected",
            ),
            SecretPattern(
                "AWS Access Key", r"AKIA[0-9A-Z]{16}", "high", "AWS access key detected"
            ),
            SecretPattern(
                "AWS Secret Key",
                r"['\"]?[a-zA-Z0-9/+=]{40}['\"]?",
                "high",
                "AWS secret key detected",
            ),
            # Database credentials
            SecretPattern(
                "Database Password",
                r"(?:password|pwd|pass)\s*[:=]\s*['\"]?[^'\"]{8,}['\"]?",
                "high",
                "Database password detected",
            ),
            SecretPattern(
                "MongoDB URI",
                r"mongodb://[^:]+:[^@]+@",
                "high",
                "MongoDB connection string with credentials",
            ),
            SecretPattern(
                "PostgreSQL URI",
                r"postgres://[^:]+:[^@]+@",
                "high",
                "PostgreSQL connection string with credentials",
            ),
            # JWT Tokens
            SecretPattern(
                "JWT Token",
                r"eyJ[a-zA-Z0-9_-]*\.[a-zA-Z0-9_-]*\.[a-zA-Z0-9_-]*",
                "medium",
                "JWT token detected",
            ),
            # Private Keys
            SecretPattern(
                "RSA Private Key",
                r"-----BEGIN RSA PRIVATE KEY-----",
                "high",
                "RSA private key detected",
            ),
            SecretPattern(
                "SSH Private Key",
                r"-----BEGIN OPENSSH PRIVATE KEY-----",
                "high",
                "SSH private key detected",
            ),
            SecretPattern(
                "EC Private Key",
                r"-----BEGIN EC PRIVATE KEY-----",
                "high",
                "EC private key detected",
            ),
            # Environment variables that might contain secrets
            SecretPattern(
                "Secret Environment Variable",
                r"(?:SECRET|PASSWORD|KEY|TOKEN|PRIVATE)_[A-Z_]+\s*[:=]\s*['\"]?[^'\"]{8,}['\"]?",
                "medium",
                "Environment variable that might contain secrets",
            ),
            # PII Patterns
            SecretPattern(
                "Email Address",
                r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",
                "low",
                "Email address detected",
            ),
            SecretPattern(
                "Phone Number",
                r"(\+?1[-.\s]?)?\(?[0-9]{3}\)?[-.\s]?[0-9]{3}[-.\s]?[0-9]{4}",
                "low",
                "Phone number detected",
            ),
            SecretPattern(
                "Credit Card Number",
                r"\b(?:4[0-9]{12}(?:[0-9]{3})?|5[1-5][0-9]{14}|3[47][0-9]{13}|3[0-9]{13}|6(?:011|5[0-9]{2})[0-9]{12})\b",
                "high",
                "Credit card number detected",
            ),
            SecretPattern(
                "SSN",
                r"\b\d{3}-?\d{2}-?\d{4}\b",
                "high",
                "Social Security Number detected",
            ),
            # Hardcoded secrets
            SecretPattern(
                "Hardcoded Secret",
                r"(?:secret|password|token|key)\s*[:=]\s*['\"]?[a-zA-Z0-9+/=]{16,}['\"]?",
                "medium",
                "Hardcoded secret detected",
            ),
            # Configuration files with potential secrets
            SecretPattern(
                "Config with Credentials",
                r"(?:username|user|login)\s*[:=]\s*['\"]?[^'\"]+['\"]?\s*[,;]?\s*(?:password|pass|pwd)\s*[:=]\s*['\"]?[^'\"]+['\"]?",
                "medium",
                "Configuration with username and password",
            ),
        ]

    def _should_ignore_file(self, file_path: Path) -> bool:
        """Check if file should be ignored."""
        relative_path = file_path.relative_to(self.project_root)

        # Check against ignore patterns
        for pattern in self.ignored_patterns:
            if pattern.startswith("/"):
                # Absolute path pattern
                if str(relative_path).startswith(pattern[1:]):
                    return True
            elif pattern.endswith("/"):
                # Directory pattern
                if str(relative_path).startswith(pattern[:-1]):
                    return True
            else:
                # File or pattern
                if pattern in str(relative_path) or relative_path.match(pattern):
                    return True

        # Ignore common non-source files
        ignore_extensions = {
            ".pyc",
            ".pyo",
            ".pyd",
            ".so",
            ".dll",
            ".exe",
            ".jpg",
            ".jpeg",
            ".png",
            ".gif",
            ".pdf",
            ".zip",
            ".tar",
            ".gz",
            ".bz2",
            ".7z",
            ".rar",
        }

        if file_path.suffix.lower() in ignore_extensions:
            return True

        # Ignore common directories
        ignore_dirs = {
            "__pycache__",
            ".git",
            ".pytest_cache",
            "node_modules",
            "venv",
            ".venv",
            "env",
            ".env",
            "build",
            "dist",
            "target",
        }

        for part in relative_path.parts:
            if part in ignore_dirs:
                return True

        return False

    def _scan_file(self, file_path: Path) -> list[SecretFinding]:
        """Scan a single file for secrets."""
        findings = []

        try:
            with open(file_path, encoding="utf-8", errors="ignore") as f:
                lines = f.readlines()

            for line_num, line in enumerate(lines, 1):
                for pattern in self.secret_patterns:
                    matches = pattern.pattern.finditer(line)
                    for match in matches:
                        # Get context (surrounding lines)
                        context_start = max(0, line_num - 2)
                        context_end = min(len(lines), line_num + 1)
                        context = "".join(lines[context_start:context_end])

                        finding = SecretFinding(
                            file_path=str(file_path.relative_to(self.project_root)),
                            line_number=line_num,
                            pattern_name=pattern.name,
                            matched_text=match.group(),
                            severity=pattern.severity,
                            confidence=pattern.confidence,
                            context=context.strip(),
                        )
                        findings.append(finding)

        except Exception as e:
            # Log error but continue
            print(f"Error scanning {file_path}: {e}")

        return findings

    def scan_directory(self, directory: str | None = None) -> list[SecretFinding]:
        """Scan directory for secrets."""
        if directory is None:
            directory = self.project_root
        else:
            directory = Path(directory)

        self.findings = []

        # Get all files to scan
        files_to_scan = []
        for file_path in directory.rglob("*"):
            if file_path.is_file() and not self._should_ignore_file(file_path):
                files_to_scan.append(file_path)

        print(f"Scanning {len(files_to_scan)} files for secrets...")

        # Scan each file
        for file_path in files_to_scan:
            findings = self._scan_file(file_path)
            self.findings.extend(findings)

        return self.findings

    def run_external_tools(self) -> dict:
        """Run external security tools."""
        results = {}

        # Run bandit
        try:
            result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "bandit",
                    "-r",
                    str(self.project_root),
                    "-f",
                    "json",
                ],
                capture_output=True,
                text=True,
                timeout=60,
            )

            if result.returncode == 0:
                results["bandit"] = {"status": "success", "output": result.stdout}
            else:
                results["bandit"] = {"status": "error", "output": result.stderr}
        except Exception as e:
            results["bandit"] = {"status": "error", "output": str(e)}

        # Run semgrep
        try:
            result = subprocess.run(
                ["semgrep", "--config=auto", "--json", str(self.project_root)],
                capture_output=True,
                text=True,
                timeout=120,
            )

            if result.returncode == 0:
                results["semgrep"] = {"status": "success", "output": result.stdout}
            else:
                results["semgrep"] = {"status": "error", "output": result.stderr}
        except Exception as e:
            results["semgrep"] = {"status": "error", "output": str(e)}

        # Run pip-audit
        try:
            result = subprocess.run(
                [sys.executable, "-m", "pip_audit", "--format=json"],
                capture_output=True,
                text=True,
                timeout=60,
            )

            if result.returncode == 0:
                results["pip_audit"] = {"status": "success", "output": result.stdout}
            else:
                results["pip_audit"] = {"status": "error", "output": result.stderr}
        except Exception as e:
            results["pip_audit"] = {"status": "error", "output": str(e)}

        return results

    def generate_report(
        self, output_file: str = "artifacts/security/secrets_report.json"
    ):
        """Generate comprehensive security report."""
        # Ensure output directory exists
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Count findings by severity
        high_count = sum(1 for f in self.findings if f.severity == "high")
        medium_count = sum(1 for f in self.findings if f.severity == "medium")
        low_count = sum(1 for f in self.findings if f.severity == "low")

        # Run external tools
        external_results = self.run_external_tools()

        # Generate report
        report = {
            "timestamp": datetime.now().isoformat(),
            "summary": {
                "total_findings": len(self.findings),
                "high_severity": high_count,
                "medium_severity": medium_count,
                "low_severity": low_count,
                "files_scanned": len({f.file_path for f in self.findings}),
            },
            "findings": [f.to_dict() for f in self.findings],
            "external_tools": external_results,
            "recommendations": self._generate_recommendations(),
        }

        # Save report
        with open(output_path, "w") as f:
            json.dump(report, f, indent=2)

        return report

    def _generate_recommendations(self) -> list[str]:
        """Generate security recommendations."""
        recommendations = []

        high_count = sum(1 for f in self.findings if f.severity == "high")
        medium_count = sum(1 for f in self.findings if f.severity == "medium")

        if high_count > 0:
            recommendations.append(
                f"🚨 CRITICAL: {high_count} high-severity secrets found. Remove immediately."
            )

        if medium_count > 0:
            recommendations.append(
                f"⚠️ WARNING: {medium_count} medium-severity issues found. Review and fix."
            )

        # Check for common issues
        api_keys = [f for f in self.findings if "API" in f.pattern_name]
        if api_keys:
            recommendations.append(
                "🔑 API keys found. Use environment variables or secure key management."
            )

        passwords = [f for f in self.findings if "password" in f.pattern_name.lower()]
        if passwords:
            recommendations.append(
                "🔒 Passwords found. Use secure password management."
            )

        private_keys = [
            f for f in self.findings if "private key" in f.pattern_name.lower()
        ]
        if private_keys:
            recommendations.append(
                "🗝️ Private keys found. Store in secure key management system."
            )

        pii = [
            f
            for f in self.findings
            if f.severity == "low" and "email" in f.pattern_name.lower()
        ]
        if pii:
            recommendations.append(
                "📧 PII detected. Ensure compliance with privacy regulations."
            )

        return recommendations


def main():
    """Main entry point for secrets sweep."""
    import argparse

    parser = argparse.ArgumentParser(description="StillMe Secrets & PII Sweep")
    parser.add_argument("--directory", default=".", help="Directory to scan")
    parser.add_argument(
        "--output",
        default="artifacts/security/secrets_report.json",
        help="Output report file",
    )
    parser.add_argument(
        "--fail-on-high",
        action="store_true",
        help="Exit with error code if high severity issues found",
    )

    args = parser.parse_args()

    # Run sweep
    sweeper = SecretsSweeper(args.directory)
    sweeper.scan_directory()

    # Generate report
    report = sweeper.generate_report(args.output)

    # Print summary
    summary = report["summary"]
    print("\n🔍 Secrets Sweep Complete")
    print(f"Files scanned: {summary['files_scanned']}")
    print(f"Total findings: {summary['total_findings']}")
    print(f"High severity: {summary['high_severity']} 🚨")
    print(f"Medium severity: {summary['medium_severity']} ⚠️")
    print(f"Low severity: {summary['low_severity']} ℹ️")

    # Print recommendations
    if report["recommendations"]:
        print("\n📋 Recommendations:")
        for rec in report["recommendations"]:
            print(f"  {rec}")

    # Exit with error if high severity issues found and requested
    if args.fail_on_high and summary["high_severity"] > 0:
        print("\n❌ High severity issues found. Exiting with error code.")
        sys.exit(1)

    print(f"\n✅ Report saved to: {args.output}")


if __name__ == "__main__":
    from datetime import datetime

    main()
