#!/usr/bin/env python3
"""
Test Summary Generator for StillMe AI Framework
===============================================

This script generates a comprehensive test summary from all test artifacts.

Author: StillMe AI Framework Team
Version: 1.0.0
Last Updated: 2025-09-26
"""

import argparse
import glob
import json
import os
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class TestResult:
    """Test result data structure"""
    test_type: str
    total_tests: int
    passed_tests: int
    failed_tests: int
    skipped_tests: int
    duration: float
    pass_rate: float
    coverage: float


@dataclass
class TestSummary:
    """Test summary data structure"""
    overall_status: str
    total_tests: int
    total_passed: int
    total_failed: int
    total_skipped: int
    overall_pass_rate: float
    overall_coverage: float
    test_duration: float
    test_results: List[TestResult]
    critical_issues: List[str]
    recommendations: List[str]


class TestSummaryGenerator:
    """Generates comprehensive test summary"""

    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root)
        self.artifacts_dir = self.project_root / "artifacts"

    def generate_summary(self, input_dir: str = "artifacts") -> TestSummary:
        """Generate comprehensive test summary"""
        print("📊 Generating test summary...")

        # Load test results from artifacts
        test_results = self._load_test_results(input_dir)

        # Calculate overall metrics
        total_tests = sum(result.total_tests for result in test_results)
        total_passed = sum(result.passed_tests for result in test_results)
        total_failed = sum(result.failed_tests for result in test_results)
        total_skipped = sum(result.skipped_tests for result in test_results)
        overall_pass_rate = (total_passed / total_tests * 100) if total_tests > 0 else 0.0
        overall_coverage = sum(result.coverage for result in test_results) / len(test_results) if test_results else 0.0
        test_duration = sum(result.duration for result in test_results)

        # Determine overall status
        overall_status = self._determine_overall_status(test_results)

        # Identify critical issues
        critical_issues = self._identify_critical_issues(test_results)

        # Generate recommendations
        recommendations = self._generate_recommendations(test_results, overall_status)

        return TestSummary(
            overall_status=overall_status,
            total_tests=total_tests,
            total_passed=total_passed,
            total_failed=total_failed,
            total_skipped=total_skipped,
            overall_pass_rate=overall_pass_rate,
            overall_coverage=overall_coverage,
            test_duration=test_duration,
            test_results=test_results,
            critical_issues=critical_issues,
            recommendations=recommendations
        )

    def _load_test_results(self, input_dir: str) -> List[TestResult]:
        """Load test results from artifact files"""
        test_results = []
        artifacts_path = self.project_root / input_dir

        if not artifacts_path.exists():
            print(f"⚠️ Artifacts directory not found: {artifacts_path}")
            return test_results

        # Load unit test results
        unit_results = self._load_test_type_results(artifacts_path, "unit")
        if unit_results:
            test_results.append(unit_results)

        # Load integration test results
        integration_results = self._load_test_type_results(artifacts_path, "integration")
        if integration_results:
            test_results.append(integration_results)

        # Load security test results
        security_results = self._load_test_type_results(artifacts_path, "security")
        if security_results:
            test_results.append(security_results)

        # Load ethics test results
        ethics_results = self._load_test_type_results(artifacts_path, "ethics")
        if ethics_results:
            test_results.append(ethics_results)

        # Load performance test results
        performance_results = self._load_test_type_results(artifacts_path, "performance")
        if performance_results:
            test_results.append(performance_results)

        return test_results

    def _load_test_type_results(self, artifacts_path: Path, test_type: str) -> Optional[TestResult]:
        """Load results for a specific test type"""
        # Look for test result files
        pattern_files = [
            f"*{test_type}*.json",
            f"junit-{test_type}.xml",
            f"coverage-{test_type}.json"
        ]

        test_files = []
        for pattern in pattern_files:
            test_files.extend(artifacts_path.glob(pattern))

        if not test_files:
            return None

        total_tests = 0
        passed_tests = 0
        failed_tests = 0
        skipped_tests = 0
        duration = 0.0
        coverage = 0.0

        # Parse JSON files
        for test_file in test_files:
            if test_file.suffix == '.json':
                try:
                    with open(test_file) as f:
                        data = json.load(f)

                    # Extract test metrics
                    if 'tests' in data:
                        total_tests += data['tests']
                    if 'passed' in data:
                        passed_tests += data['passed']
                    if 'failed' in data:
                        failed_tests += data['failed']
                    if 'skipped' in data:
                        skipped_tests += data['skipped']
                    if 'duration' in data:
                        duration += data['duration']
                    if 'coverage' in data:
                        coverage = max(coverage, data['coverage'])
                    elif 'totals' in data and 'percent_covered' in data['totals']:
                        coverage = max(coverage, data['totals']['percent_covered'])
                except Exception as e:
                    print(f"⚠️ Error reading {test_file}: {e}")

        # Parse XML files (simplified)
        for test_file in test_files:
            if test_file.suffix == '.xml':
                try:
                    # Simple XML parsing for JUnit format
                    with open(test_file) as f:
                        content = f.read()

                    # Extract basic metrics from XML
                    if 'tests=' in content:
                        import re
                        tests_match = re.search(r'tests="(\d+)"', content)
                        if tests_match:
                            total_tests = int(tests_match.group(1))

                    if 'failures=' in content:
                        failures_match = re.search(r'failures="(\d+)"', content)
                        if failures_match:
                            failed_tests = int(failures_match.group(1))

                    if 'skipped=' in content:
                        skipped_match = re.search(r'skipped="(\d+)"', content)
                        if skipped_match:
                            skipped_tests = int(skipped_match.group(1))

                    passed_tests = total_tests - failed_tests - skipped_tests
                except Exception as e:
                    print(f"⚠️ Error reading {test_file}: {e}")

        if total_tests == 0:
            return None

        pass_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0.0

        return TestResult(
            test_type=test_type,
            total_tests=total_tests,
            passed_tests=passed_tests,
            failed_tests=failed_tests,
            skipped_tests=skipped_tests,
            duration=duration,
            pass_rate=pass_rate,
            coverage=coverage
        )

    def _determine_overall_status(self, test_results: List[TestResult]) -> str:
        """Determine overall test status"""
        if not test_results:
            return "NO_TESTS"

        # Check for critical failures
        for result in test_results:
            if result.pass_rate < 70:  # Less than 70% pass rate
                return "CRITICAL"

        # Check for warnings
        for result in test_results:
            if result.pass_rate < 90:  # Less than 90% pass rate
                return "WARNING"

        return "PASS"

    def _identify_critical_issues(self, test_results: List[TestResult]) -> List[str]:
        """Identify critical issues from test results"""
        issues = []

        for result in test_results:
            if result.pass_rate < 70:
                issues.append(f"Critical: {result.test_type} tests have {result.pass_rate:.1f}% pass rate")
            elif result.pass_rate < 90:
                issues.append(f"Warning: {result.test_type} tests have {result.pass_rate:.1f}% pass rate")

            if result.coverage < 80:
                issues.append(f"Low coverage: {result.test_type} tests have {result.coverage:.1f}% coverage")

        return issues

    def _generate_recommendations(self, test_results: List[TestResult], overall_status: str) -> List[str]:
        """Generate improvement recommendations"""
        recommendations = []

        if overall_status == "CRITICAL":
            recommendations.append("🔴 CRITICAL: Fix failing tests immediately")
            recommendations.append("   - Review test failures and fix root causes")
            recommendations.append("   - Ensure all critical functionality is tested")
        elif overall_status == "WARNING":
            recommendations.append("🟡 WARNING: Address test issues to improve quality")
            recommendations.append("   - Fix failing tests")
            recommendations.append("   - Improve test coverage")
        else:
            recommendations.append("✅ Tests are passing well")
            recommendations.append("   - Continue monitoring test quality")
            recommendations.append("   - Maintain current testing standards")

        # Specific recommendations based on test results
        for result in test_results:
            if result.pass_rate < 90:
                recommendations.append(f"   - Fix {result.test_type} test failures")
            if result.coverage < 80:
                recommendations.append(f"   - Increase {result.test_type} test coverage")

        # General recommendations
        recommendations.append("📊 Implement continuous testing in CI/CD")
        recommendations.append("🔍 Add automated test result analysis")
        recommendations.append("📚 Provide testing best practices training")

        return recommendations

    def generate_report(self, summary: TestSummary) -> str:
        """Generate comprehensive test summary report"""
        report_content = f"""
# Test Summary Report
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Executive Summary
- **Overall Status**: {summary.overall_status}
- **Total Tests**: {summary.total_tests:,}
- **Passed**: {summary.total_passed:,} ({summary.overall_pass_rate:.1f}%)
- **Failed**: {summary.total_failed:,}
- **Skipped**: {summary.total_skipped:,}
- **Overall Coverage**: {summary.overall_coverage:.1f}%
- **Test Duration**: {summary.test_duration:.1f}s

## Test Results by Type
"""

        for result in summary.test_results:
            status_icon = "✅" if result.pass_rate >= 90 else "⚠️" if result.pass_rate >= 70 else "❌"
            report_content += f"### {status_icon} {result.test_type.title()} Tests\n"
            report_content += f"- **Total Tests**: {result.total_tests:,}\n"
            report_content += f"- **Passed**: {result.passed_tests:,}\n"
            report_content += f"- **Failed**: {result.failed_tests:,}\n"
            report_content += f"- **Skipped**: {result.skipped_tests:,}\n"
            report_content += f"- **Pass Rate**: {result.pass_rate:.1f}%\n"
            report_content += f"- **Coverage**: {result.coverage:.1f}%\n"
            report_content += f"- **Duration**: {result.duration:.1f}s\n\n"

        # Critical issues
        if summary.critical_issues:
            report_content += "## 🚨 Critical Issues\n\n"
            for issue in summary.critical_issues:
                report_content += f"- {issue}\n"
            report_content += "\n"

        # Recommendations
        report_content += "## 🎯 Recommendations\n\n"
        for i, rec in enumerate(summary.recommendations, 1):
            report_content += f"{i}. {rec}\n"

        # Quality metrics
        report_content += "\n## 📊 Quality Metrics\n\n"
        report_content += "### Test Coverage\n"
        report_content += "- **Target**: 90%+\n"
        report_content += f"- **Current**: {summary.overall_coverage:.1f}%\n"
        report_content += f"- **Status**: {'✅ PASS' if summary.overall_coverage >= 90 else '⚠️ WARNING' if summary.overall_coverage >= 80 else '❌ FAIL'}\n\n"

        report_content += "### Test Pass Rate\n"
        report_content += "- **Target**: 95%+\n"
        report_content += f"- **Current**: {summary.overall_pass_rate:.1f}%\n"
        report_content += f"- **Status**: {'✅ PASS' if summary.overall_pass_rate >= 95 else '⚠️ WARNING' if summary.overall_pass_rate >= 90 else '❌ FAIL'}\n\n"

        # Performance summary
        report_content += "## ⚡ Performance Summary\n\n"
        report_content += f"- **Total Test Duration**: {summary.test_duration:.1f}s\n"
        if len(summary.test_results) > 0:
            report_content += f"- **Average Test Duration**: {summary.test_duration / len(summary.test_results):.1f}s per test type\n"
        else:
            report_content += "- **Average Test Duration**: N/A (no test results)\n"
        if summary.test_duration > 0:
            report_content += f"- **Test Efficiency**: {summary.total_passed / summary.test_duration:.1f} tests/second\n\n"
        else:
            report_content += "- **Test Efficiency**: N/A (no test duration)\n\n"

        # Next steps
        report_content += "## 🚀 Next Steps\n\n"
        if summary.overall_status == "CRITICAL":
            report_content += "### Immediate Actions (Next 24 hours)\n"
            report_content += "- Fix all critical test failures\n"
            report_content += "- Ensure core functionality is working\n"
            report_content += "- Add missing test coverage\n\n"
        elif summary.overall_status == "WARNING":
            report_content += "### Short-term Actions (Next 1 week)\n"
            report_content += "- Address test failures\n"
            report_content += "- Improve test coverage\n"
            report_content += "- Optimize test performance\n\n"
        else:
            report_content += "### Maintenance Actions\n"
            report_content += "- Continue monitoring test quality\n"
            report_content += "- Maintain test coverage\n"
            report_content += "- Regular test review\n\n"

        return report_content

    def save_report(self, report_content: str, output_file: str = "artifacts/test_summary.md"):
        """Save test summary report to file"""
        output_path = self.project_root / output_file
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(report_content)

        print(f"📄 Test summary saved to: {output_path}")


def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="Generate test summary for StillMe AI Framework")
    parser.add_argument("--input", type=str, default="artifacts", help="Input directory for test artifacts")
    parser.add_argument("--output", type=str, default="artifacts/test_summary.md", help="Output report file")
    parser.add_argument("--project-root", type=str, default=".", help="Project root directory")

    args = parser.parse_args()

    print("📊 Starting test summary generation...")
    print(f"📁 Project root: {args.project_root}")
    print(f"📊 Input directory: {args.input}")

    # Initialize generator
    generator = TestSummaryGenerator(args.project_root)

    # Generate summary
    summary = generator.generate_summary(args.input)

    # Generate and save report
    report_content = generator.generate_report(summary)
    generator.save_report(report_content, args.output)

    # Print summary
    print("\n📊 Test Summary:")
    print(f"   Overall Status: {summary.overall_status}")
    print(f"   Total Tests: {summary.total_tests:,}")
    print(f"   Pass Rate: {summary.overall_pass_rate:.1f}%")
    print(f"   Coverage: {summary.overall_coverage:.1f}%")
    print(f"   Duration: {summary.test_duration:.1f}s")

    if summary.critical_issues:
        print("\n🚨 Critical Issues:")
        for issue in summary.critical_issues:
            print(f"   - {issue}")

    print(f"\n📄 Detailed report: {args.output}")


if __name__ == "__main__":
    main()
