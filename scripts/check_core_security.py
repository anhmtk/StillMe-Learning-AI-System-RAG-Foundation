#!/usr/bin/env python3
"""Quick check of core security issues"""

import json
import os

def main():
    report_path = "artifacts/bandit-core-report.json"
    if not os.path.exists(report_path):
        print("❌ No bandit report found")
        return

    with open(report_path, 'r') as f:
        data = json.load(f)

    results = data.get('results', [])
    high_severity = [r for r in results if r.get('issue_severity') == 'HIGH']
    medium_severity = [r for r in results if r.get('issue_severity') == 'MEDIUM']

    print(f"🔒 Core Security Analysis")
    print(f"High severity: {len(high_severity)}")
    print(f"Medium severity: {len(medium_severity)}")

    if high_severity:
        print("\n🚨 High Severity Issues:")
        for issue in high_severity[:5]:  # Show first 5
            print(f"  - {issue['filename']}:{issue['line_number']}")
            print(f"    {issue['issue_text']}")

    if len(high_severity) == 0:
        print("✅ No high severity security issues in core code!")

if __name__ == "__main__":
    main()
