#!/usr/bin/env python3
"""
Coverage check script for NicheRadar v1.5
Ensures test coverage meets minimum requirements
"""

import json
import os
import sys
import xml.etree.ElementTree as ET
from pathlib import Path


def check_coverage_xml():
    """Check coverage from XML report"""
    coverage_file = "reports/coverage.xml"

    if not Path(coverage_file).exists():
        print(f"❌ Coverage XML report not found: {coverage_file}")
        return False

    try:
        tree = ET.parse(coverage_file)
        root = tree.getroot()

        # Get overall coverage
        line_rate = float(root.get('line-rate', 0))
        branch_rate = float(root.get('branch-rate', 0))

        print("📊 Overall Coverage:")
        print(f"   Line Coverage: {line_rate:.1%}")
        print(f"   Branch Coverage: {branch_rate:.1%}")

        # Check minimum coverage (65%)
        min_coverage = 0.65
        if line_rate >= min_coverage:
            print(f"✅ Line coverage meets minimum requirement ({min_coverage:.1%})")
        else:
            print(f"❌ Line coverage below minimum requirement ({min_coverage:.1%})")
            return False

        # Check specific modules
        modules = root.findall('.//class')
        niche_radar_coverage = {}

        for module in modules:
            filename = module.get('filename', '')
            if 'niche_radar' in filename:
                line_rate = float(module.get('line-rate', 0))
                niche_radar_coverage[filename] = line_rate

        if niche_radar_coverage:
            print("\n📊 NicheRadar Module Coverage:")
            for module, coverage in niche_radar_coverage.items():
                status = "✅" if coverage >= min_coverage else "❌"
                print(f"   {status} {module}: {coverage:.1%}")

            # Check if all modules meet minimum
            all_meet_minimum = all(coverage >= min_coverage for coverage in niche_radar_coverage.values())
            if all_meet_minimum:
                print("✅ All NicheRadar modules meet minimum coverage")
            else:
                print("❌ Some NicheRadar modules below minimum coverage")
                return False

        return True

    except ET.ParseError as e:
        print(f"❌ Error parsing coverage XML: {e}")
        return False
    except Exception as e:
        print(f"❌ Error reading coverage XML: {e}")
        return False

def check_coverage_html():
    """Check if HTML coverage report exists"""
    coverage_dir = "reports/coverage"

    if not Path(coverage_dir).exists():
        print(f"❌ Coverage HTML directory not found: {coverage_dir}")
        return False

    index_file = Path(coverage_dir) / "index.html"
    if not index_file.exists():
        print(f"❌ Coverage HTML index not found: {index_file}")
        return False

    print("✅ Coverage HTML report exists")
    return True

def check_missing_coverage():
    """Check for missing coverage in critical files"""
    critical_files = [
        "niche_radar/collectors.py",
        "niche_radar/scoring.py",
        "niche_radar/playbook.py",
        "niche_radar/feedback.py",
        "policy/tool_gate.py",
        "security/content_wrap.py",
        "cache/web_cache.py",
        "metrics/web_metrics.py"
    ]

    missing_files = []
    for file_path in critical_files:
        if not Path(file_path).exists():
            missing_files.append(file_path)

    if missing_files:
        print(f"❌ Critical files not found: {', '.join(missing_files)}")
        return False

    print("✅ All critical files exist")
    return True

def check_test_coverage_ratio():
    """Check test coverage ratio"""
    test_files = list(Path("tests").glob("test_*.py"))
    source_files = list(Path("niche_radar").glob("*.py"))

    if not test_files:
        print("❌ No test files found")
        return False

    if not source_files:
        print("❌ No source files found in niche_radar")
        return False

    test_count = len(test_files)
    source_count = len(source_files)
    ratio = test_count / source_count

    print("📊 Test Coverage Ratio:")
    print(f"   Test Files: {test_count}")
    print(f"   Source Files: {source_count}")
    print(f"   Ratio: {ratio:.2f}")

    # Minimum ratio of 0.5 (1 test file per 2 source files)
    min_ratio = 0.5
    if ratio >= min_ratio:
        print(f"✅ Test coverage ratio meets minimum requirement ({min_ratio:.2f})")
        return True
    else:
        print(f"❌ Test coverage ratio below minimum requirement ({min_ratio:.2f})")
        return False

def check_coverage_trends():
    """Check coverage trends (if previous reports exist)"""
    # This would compare with previous coverage reports
    # For now, we'll just check if the current report exists
    coverage_file = "reports/coverage.xml"

    if Path(coverage_file).exists():
        print("✅ Current coverage report exists")
        return True
    else:
        print("❌ No current coverage report found")
        return False

def generate_coverage_summary():
    """Generate coverage summary"""
    summary = {
        "timestamp": "2024-09-22T10:00:00Z",
        "coverage_files": [],
        "coverage_issues": []
    }

    # Check coverage files
    coverage_files = [
        "reports/coverage.xml",
        "reports/coverage/index.html"
    ]

    for file_path in coverage_files:
        if Path(file_path).exists():
            summary["coverage_files"].append(file_path)
        else:
            summary["coverage_issues"].append(f"Missing: {file_path}")

    # Save summary
    summary_path = "reports/coverage_summary.json"
    with open(summary_path, 'w') as f:
        json.dump(summary, f, indent=2)

    print(f"📋 Coverage summary saved to {summary_path}")
    return summary

def main():
    """Main coverage check function"""
    print("🔍 Checking test coverage...")

    checks = [
        ("Critical Files", check_missing_coverage),
        ("Test Coverage Ratio", check_test_coverage_ratio),
        ("Coverage XML Report", check_coverage_xml),
        ("Coverage HTML Report", check_coverage_html),
        ("Coverage Trends", check_coverage_trends)
    ]

    all_passed = True
    for check_name, check_func in checks:
        print(f"\n📋 {check_name}:")
        if not check_func():
            all_passed = False

    # Generate summary
    print("\n📊 Coverage Summary:")
    summary = generate_coverage_summary()

    if all_passed:
        print("\n✅ All coverage checks passed!")
        return 0
    else:
        print("\n❌ Some coverage checks failed!")
        return 1

if __name__ == "__main__":
    sys.exit(main())
