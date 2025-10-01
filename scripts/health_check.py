#!/usr/bin/env python3
"""
StillMe Health Check Script
Validates system health across multiple dimensions:
- Unit/Integration tests (short)
- Security scanning (bandit/semgrep)
- Ethics smoke tests
- Open ports check
- Library versions
- Core functionality smoke tests
"""

import json
import os
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

class HealthChecker:
    def __init__(self):
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "overall_status": "UNKNOWN",
            "checks": {},
            "artifacts": {},
            "summary": {}
        }
        self.artifacts_dir = project_root / "artifacts"
        self.reports_dir = project_root / "reports"
        self.logs_dir = project_root / "logs"

        # Ensure directories exist
        for dir_path in [self.artifacts_dir, self.reports_dir, self.logs_dir]:
            dir_path.mkdir(exist_ok=True)

    def run_command(self, cmd: List[str], timeout: int = 30) -> Tuple[bool, str, str]:
        """Run command with timeout and capture output."""
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=project_root
            )
            return result.returncode == 0, result.stdout, result.stderr
        except subprocess.TimeoutExpired:
            return False, "", f"Command timed out after {timeout}s"
        except Exception as e:
            return False, "", str(e)

    def check_unit_tests(self) -> Dict:
        """Run unit tests with coverage."""
        print("🔍 Running unit tests...")

        # Install test dependencies if needed
        self.run_command([sys.executable, "-m", "pip", "install", "pytest", "pytest-cov"])

        # Run tests
        success, stdout, stderr = self.run_command([
            sys.executable, "-m", "pytest",
            "tests/",
            "-v",
            "--tb=short",
            "--maxfail=5",
            "--cov=stillme_core",
            "--cov-report=html:artifacts/coverage",
            "--cov-report=json:artifacts/coverage.json"
        ], timeout=60)

        # Parse results
        test_count = 0
        passed = 0
        failed = 0

        for line in stdout.split('\n'):
            if " passed" in line and " failed" in line:
                # Extract numbers from pytest output
                parts = line.split()
                for i, part in enumerate(parts):
                    if part == "passed":
                        passed = int(parts[i-1])
                    elif part == "failed":
                        failed = int(parts[i-1])
                test_count = passed + failed
                break

        coverage = 0.0
        if os.path.exists("artifacts/coverage.json"):
            try:
                with open("artifacts/coverage.json") as f:
                    cov_data = json.load(f)
                    coverage = cov_data.get("totals", {}).get("percent_covered", 0.0)
            except:
                pass

        result = {
            "status": "PASS" if success and failed == 0 else "FAIL",
            "test_count": test_count,
            "passed": passed,
            "failed": failed,
            "coverage_percent": coverage,
            "output": stdout[-500:],  # Last 500 chars
            "error": stderr[-500:] if stderr else None
        }

        self.results["checks"]["unit_tests"] = result
        return result

    def check_security_scan(self) -> Dict:
        """Run security scanning tools."""
        print("🔒 Running security scans...")

        # Install security tools
        self.run_command([sys.executable, "-m", "pip", "install", "bandit", "semgrep"])

        # Bandit scan
        bandit_success, bandit_stdout, bandit_stderr = self.run_command([
            sys.executable, "-m", "bandit",
            "-r", "stillme_core/",
            "-f", "json",
            "-o", "artifacts/bandit-report.json"
        ], timeout=30)

        # Semgrep scan
        semgrep_success, semgrep_stdout, semgrep_stderr = self.run_command([
            "semgrep",
            "--config=auto",
            "--json",
            "--output=artifacts/semgrep-report.json",
            "stillme_core/"
        ], timeout=60)

        # Parse bandit results
        bandit_high = 0
        bandit_medium = 0
        bandit_low = 0

        if os.path.exists("artifacts/bandit-report.json"):
            try:
                with open("artifacts/bandit-report.json") as f:
                    bandit_data = json.load(f)
                    for issue in bandit_data.get("results", []):
                        severity = issue.get("issue_severity", "").lower()
                        if severity == "high":
                            bandit_high += 1
                        elif severity == "medium":
                            bandit_medium += 1
                        elif severity == "low":
                            bandit_low += 1
            except:
                pass

        # Parse semgrep results
        semgrep_high = 0
        semgrep_medium = 0
        semgrep_low = 0

        if os.path.exists("artifacts/semgrep-report.json"):
            try:
                with open("artifacts/semgrep-report.json") as f:
                    semgrep_data = json.load(f)
                    for result in semgrep_data.get("results", []):
                        severity = result.get("extra", {}).get("severity", "").lower()
                        if severity == "error":
                            semgrep_high += 1
                        elif severity == "warning":
                            semgrep_medium += 1
                        elif severity == "info":
                            semgrep_low += 1
            except:
                pass

        total_high = bandit_high + semgrep_high

        result = {
            "status": "PASS" if total_high == 0 else "FAIL",
            "bandit": {
                "high": bandit_high,
                "medium": bandit_medium,
                "low": bandit_low,
                "success": bandit_success
            },
            "semgrep": {
                "high": semgrep_high,
                "medium": semgrep_medium,
                "low": semgrep_low,
                "success": semgrep_success
            },
            "total_high_severity": total_high,
            "bandit_output": bandit_stdout[-300:] if bandit_stdout else None,
            "semgrep_output": semgrep_stdout[-300:] if semgrep_stdout else None
        }

        self.results["checks"]["security_scan"] = result
        return result

    def check_ethics_tests(self) -> Dict:
        """Run ethics smoke tests."""
        print("⚖️ Running ethics tests...")

        # Check if ethics tests exist
        ethics_test_dir = project_root / "tests" / "ethics"
        if not ethics_test_dir.exists():
            result = {
                "status": "SKIP",
                "reason": "No ethics tests found",
                "test_count": 0,
                "passed": 0,
                "failed": 0
            }
            self.results["checks"]["ethics_tests"] = result
            return result

        # Run ethics tests
        success, stdout, stderr = self.run_command([
            sys.executable, "-m", "pytest",
            "tests/ethics/",
            "-v",
            "--tb=short"
        ], timeout=30)

        # Parse results
        test_count = 0
        passed = 0
        failed = 0

        for line in stdout.split('\n'):
            if " passed" in line and " failed" in line:
                parts = line.split()
                for i, part in enumerate(parts):
                    if part == "passed":
                        passed = int(parts[i-1])
                    elif part == "failed":
                        failed = int(parts[i-1])
                test_count = passed + failed
                break

        result = {
            "status": "PASS" if success and failed == 0 else "FAIL",
            "test_count": test_count,
            "passed": passed,
            "failed": failed,
            "output": stdout[-300:],
            "error": stderr[-300:] if stderr else None
        }

        self.results["checks"]["ethics_tests"] = result
        return result

    def check_open_ports(self) -> Dict:
        """Check for open ports (security concern)."""
        print("🔌 Checking open ports...")

        try:
            import socket

            # Check common ports that shouldn't be open
            dangerous_ports = [22, 23, 80, 443, 3306, 5432, 6379, 27017]
            open_ports = []

            for port in dangerous_ports:
                try:
                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    sock.settimeout(1)
                    result = sock.connect_ex(('localhost', port))
                    if result == 0:
                        open_ports.append(port)
                    sock.close()
                except:
                    pass

            result = {
                "status": "PASS" if len(open_ports) == 0 else "WARN",
                "open_ports": open_ports,
                "checked_ports": dangerous_ports
            }

        except Exception as e:
            result = {
                "status": "ERROR",
                "error": str(e)
            }

        self.results["checks"]["open_ports"] = result
        return result

    def check_library_versions(self) -> Dict:
        """Check critical library versions."""
        print("📦 Checking library versions...")

        critical_libs = [
            "fastapi", "pydantic", "numpy", "pandas",
            "scikit-learn", "transformers", "torch"
        ]

        versions = {}
        missing = []

        for lib in critical_libs:
            try:
                result = subprocess.run([
                    sys.executable, "-c", f"import {lib}; print({lib}.__version__)"
                ], capture_output=True, text=True, timeout=5)

                if result.returncode == 0:
                    versions[lib] = result.stdout.strip()
                else:
                    missing.append(lib)
            except:
                missing.append(lib)

        result = {
            "status": "PASS" if len(missing) == 0 else "WARN",
            "versions": versions,
            "missing": missing
        }

        self.results["checks"]["library_versions"] = result
        return result

    def check_core_functionality(self) -> Dict:
        """Smoke test core functionality."""
        print("🧪 Testing core functionality...")

        try:
            # Test router loading
            from stillme_core.router_loader import load_router
            router = load_router()
            model = router.choose_model("test prompt")

            # Test basic imports
            import stillme_core

            result = {
                "status": "PASS",
                "router_loaded": True,
                "model_selected": model,
                "core_imports": True
            }

        except Exception as e:
            result = {
                "status": "FAIL",
                "error": str(e),
                "router_loaded": False,
                "core_imports": False
            }

        self.results["checks"]["core_functionality"] = result
        return result

    def generate_summary(self):
        """Generate overall summary."""
        checks = self.results["checks"]

        total_checks = len(checks)
        passed = sum(1 for check in checks.values() if check["status"] == "PASS")
        failed = sum(1 for check in checks.values() if check["status"] == "FAIL")
        warnings = sum(1 for check in checks.values() if check["status"] == "WARN")

        # Critical checks that must pass
        critical_checks = ["unit_tests", "security_scan", "core_functionality"]
        critical_passed = all(
            checks.get(check, {}).get("status") == "PASS"
            for check in critical_checks
        )

        # Security gate: no high severity issues
        security_high = checks.get("security_scan", {}).get("total_high_severity", 0)
        security_pass = security_high == 0

        # Coverage gate: >= 85%
        coverage = checks.get("unit_tests", {}).get("coverage_percent", 0.0)
        coverage_pass = coverage >= 85.0

        overall_status = "PASS" if (
            critical_passed and security_pass and coverage_pass
        ) else "FAIL"

        self.results["overall_status"] = overall_status
        self.results["summary"] = {
            "total_checks": total_checks,
            "passed": passed,
            "failed": failed,
            "warnings": warnings,
            "critical_passed": critical_passed,
            "security_pass": security_pass,
            "coverage_pass": coverage_pass,
            "coverage_percent": coverage,
            "security_high_severity": security_high
        }

    def save_artifacts(self):
        """Save all artifacts and reports."""
        # Save detailed results
        with open("reports/health_check.json", "w") as f:
            json.dump(self.results, f, indent=2)

        # Generate markdown report
        self.generate_markdown_report()

    def generate_markdown_report(self):
        """Generate SYSTEM_HEALTH.md report."""
        summary = self.results["summary"]
        checks = self.results["checks"]

        report = f"""# System Health Report

**Generated:** {self.results['timestamp']}  
**Overall Status:** {self.results['overall_status']}

## Summary

- **Total Checks:** {summary['total_checks']}
- **Passed:** {summary['passed']} ✅
- **Failed:** {summary['failed']} ❌
- **Warnings:** {summary['warnings']} ⚠️

### Critical Gates

- **Critical Checks:** {'✅ PASS' if summary['critical_passed'] else '❌ FAIL'}
- **Security (High=0):** {'✅ PASS' if summary['security_pass'] else '❌ FAIL'} ({summary['security_high_severity']} high severity)
- **Coverage (≥85%):** {'✅ PASS' if summary['coverage_pass'] else '❌ FAIL'} ({summary['coverage_percent']:.1f}%)

## Detailed Results

"""

        for check_name, check_result in checks.items():
            status_emoji = {
                "PASS": "✅",
                "FAIL": "❌",
                "WARN": "⚠️",
                "SKIP": "⏭️",
                "ERROR": "💥"
            }.get(check_result["status"], "❓")

            report += f"### {check_name.replace('_', ' ').title()} {status_emoji}\n\n"
            report += f"**Status:** {check_result['status']}\n\n"

            # Add specific details based on check type
            if check_name == "unit_tests":
                report += f"- Tests: {check_result.get('test_count', 0)}\n"
                report += f"- Passed: {check_result.get('passed', 0)}\n"
                report += f"- Failed: {check_result.get('failed', 0)}\n"
                report += f"- Coverage: {check_result.get('coverage_percent', 0):.1f}%\n"
            elif check_name == "security_scan":
                bandit = check_result.get('bandit', {})
                semgrep = check_result.get('semgrep', {})
                report += f"- Bandit: {bandit.get('high', 0)}H/{bandit.get('medium', 0)}M/{bandit.get('low', 0)}L\n"
                report += f"- Semgrep: {semgrep.get('high', 0)}H/{semgrep.get('medium', 0)}M/{semgrep.get('low', 0)}L\n"
                report += f"- Total High Severity: {check_result.get('total_high_severity', 0)}\n"
            elif check_name == "ethics_tests":
                report += f"- Tests: {check_result.get('test_count', 0)}\n"
                report += f"- Passed: {check_result.get('passed', 0)}\n"
                report += f"- Failed: {check_result.get('failed', 0)}\n"
            elif check_name == "open_ports":
                open_ports = check_result.get('open_ports', [])
                if open_ports:
                    report += f"- Open Ports: {', '.join(map(str, open_ports))}\n"
                else:
                    report += "- No dangerous ports open\n"
            elif check_name == "library_versions":
                missing = check_result.get('missing', [])
                if missing:
                    report += f"- Missing Libraries: {', '.join(missing)}\n"
                else:
                    report += "- All critical libraries available\n"
            elif check_name == "core_functionality":
                report += f"- Router Loaded: {check_result.get('router_loaded', False)}\n"
                report += f"- Core Imports: {check_result.get('core_imports', False)}\n"
                if check_result.get('model_selected'):
                    report += f"- Model Selected: {check_result['model_selected']}\n"

            if check_result.get('error'):
                report += f"\n**Error:** {check_result['error']}\n"

            report += "\n"

        report += """## Artifacts

- **Detailed Results:** `reports/health_check.json`
- **Coverage Report:** `artifacts/coverage/index.html`
- **Security Reports:** `artifacts/bandit-report.json`, `artifacts/semgrep-report.json`

## Next Steps

"""

        if self.results["overall_status"] == "FAIL":
            report += "- ❌ **System health check failed** - address critical issues before proceeding\n"
            if not summary['critical_passed']:
                report += "- Fix critical check failures\n"
            if not summary['security_pass']:
                report += f"- Resolve {summary['security_high_severity']} high severity security issues\n"
            if not summary['coverage_pass']:
                report += f"- Increase test coverage to ≥85% (currently {summary['coverage_percent']:.1f}%)\n"
        else:
            report += "- ✅ **System health check passed** - ready for deployment\n"

        with open("docs/SYSTEM_HEALTH.md", "w", encoding="utf-8") as f:
            f.write(report)

    def run_all_checks(self):
        """Run all health checks."""
        print("🏥 Starting StillMe Health Check...")
        print("=" * 50)

        start_time = time.time()

        # Run all checks
        self.check_unit_tests()
        self.check_security_scan()
        self.check_ethics_tests()
        self.check_open_ports()
        self.check_library_versions()
        self.check_core_functionality()

        # Generate summary and save artifacts
        self.generate_summary()
        self.save_artifacts()

        elapsed = time.time() - start_time

        print("=" * 50)
        print(f"🏥 Health Check Complete ({elapsed:.1f}s)")
        print(f"Overall Status: {self.results['overall_status']}")

        summary = self.results["summary"]
        print(f"Checks: {summary['passed']}✅ {summary['failed']}❌ {summary['warnings']}⚠️")
        print(f"Coverage: {summary['coverage_percent']:.1f}%")
        print(f"Security High: {summary['security_high_severity']}")

        print(f"\n📊 Reports generated:")
        print(f"- docs/SYSTEM_HEALTH.md")
        print(f"- reports/health_check.json")
        print(f"- artifacts/coverage/")
        print(f"- artifacts/bandit-report.json")
        print(f"- artifacts/semgrep-report.json")

        return self.results["overall_status"] == "PASS"

def main():
    """Main entry point."""
    checker = HealthChecker()
    success = checker.run_all_checks()

    # Exit with appropriate code
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
