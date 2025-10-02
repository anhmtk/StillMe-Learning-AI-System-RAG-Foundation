#!/usr/bin/env python3
"""
Security Analysis Script
Analyze bandit, semgrep, and pip-audit reports
"""

import json
import sys
from pathlib import Path


def analyze_bandit_report(report_path: str):
    """Analyze bandit security report"""
    print("🔒 Bandit Security Analysis")
    print("=" * 50)

    try:
        with open(report_path) as f:
            data = json.load(f)

        # Count by severity
        severity_counts = {}
        for result in data.get('results', []):
            severity = result.get('issue_severity', 'UNKNOWN')
            severity_counts[severity] = severity_counts.get(severity, 0) + 1

        print(f"Total issues: {len(data.get('results', []))}")
        for severity, count in sorted(severity_counts.items()):
            print(f"  {severity}: {count}")

        # Show high severity issues
        high_severity = [r for r in data.get('results', []) if r.get('issue_severity') == 'HIGH']
        if high_severity:
            print(f"\n🚨 High Severity Issues ({len(high_severity)}):")
            for issue in high_severity[:10]:  # Show first 10
                print(f"  - {issue.get('filename', 'unknown')}:{issue.get('line_number', '?')}")
                print(f"    {issue.get('issue_text', 'No description')}")
                print()

        return len(high_severity)

    except Exception as e:
        print(f"Error analyzing bandit report: {e}")
        return 0


def analyze_semgrep_report(report_path: str):
    """Analyze semgrep security report"""
    print("\n🔍 Semgrep Security Analysis")
    print("=" * 50)

    try:
        with open(report_path) as f:
            data = json.load(f)

        results = data.get('results', [])
        print(f"Total findings: {len(results)}")

        # Count by severity
        severity_counts = {}
        for result in results:
            severity = result.get('extra', {}).get('severity', 'UNKNOWN')
            severity_counts[severity] = severity_counts.get(severity, 0) + 1

        for severity, count in sorted(severity_counts.items()):
            print(f"  {severity}: {count}")

        # Show high severity findings
        high_severity = [r for r in results if r.get('extra', {}).get('severity') == 'ERROR']
        if high_severity:
            print(f"\n🚨 High Severity Findings ({len(high_severity)}):")
            for finding in high_severity[:10]:  # Show first 10
                print(f"  - {finding.get('path', 'unknown')}:{finding.get('start', {}).get('line', '?')}")
                print(f"    {finding.get('extra', {}).get('message', 'No description')}")
                print()

        return len(high_severity)

    except Exception as e:
        print(f"Error analyzing semgrep report: {e}")
        return 0


def analyze_pip_audit_report(report_path: str):
    """Analyze pip-audit security report"""
    print("\n📦 Pip-Audit Security Analysis")
    print("=" * 50)

    try:
        with open(report_path) as f:
            data = json.load(f)

        vulnerabilities = data.get('vulnerabilities', [])
        print(f"Total vulnerabilities: {len(vulnerabilities)}")

        # Count by severity
        severity_counts = {}
        for vuln in vulnerabilities:
            severity = vuln.get('severity', 'UNKNOWN')
            severity_counts[severity] = severity_counts.get(severity, 0) + 1

        for severity, count in sorted(severity_counts.items()):
            print(f"  {severity}: {count}")

        # Show high severity vulnerabilities
        high_severity = [v for v in vulnerabilities if v.get('severity') in ['HIGH', 'CRITICAL']]
        if high_severity:
            print(f"\n🚨 High/Critical Vulnerabilities ({len(high_severity)}):")
            for vuln in high_severity[:10]:  # Show first 10
                print(f"  - {vuln.get('package', 'unknown')} {vuln.get('installed_version', '?')}")
                print(f"    {vuln.get('description', 'No description')}")
                print()

        return len(high_severity)

    except Exception as e:
        print(f"Error analyzing pip-audit report: {e}")
        return 0


def main():
    """Main analysis function"""
    artifacts_dir = Path("artifacts")

    total_high_severity = 0

    # Analyze bandit report
    bandit_report = artifacts_dir / "bandit-report.json"
    if bandit_report.exists():
        total_high_severity += analyze_bandit_report(str(bandit_report))
    else:
        print("⚠️  Bandit report not found")

    # Analyze semgrep report
    semgrep_report = artifacts_dir / "semgrep-report.json"
    if semgrep_report.exists():
        total_high_severity += analyze_semgrep_report(str(semgrep_report))
    else:
        print("⚠️  Semgrep report not found")

    # Analyze pip-audit report
    pip_audit_report = artifacts_dir / "pip-audit-report.json"
    if pip_audit_report.exists():
        total_high_severity += analyze_pip_audit_report(str(pip_audit_report))
    else:
        print("⚠️  Pip-audit report not found")

    print("\n📊 Summary")
    print("=" * 50)
    print(f"Total high/critical security issues: {total_high_severity}")

    if total_high_severity > 0:
        print("🚨 Security issues found - immediate action required!")
        sys.exit(1)
    else:
        print("✅ No high severity security issues found")
        sys.exit(0)


if __name__ == "__main__":
    main()
