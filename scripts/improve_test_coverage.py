#!/usr/bin/env python3
"""
Test Coverage Improvement Script for StillMe AI Framework
========================================================

This script analyzes test coverage and suggests improvements to reach target coverage levels.

Author: StillMe AI Framework Team
Version: 1.0.0
Last Updated: 2025-09-26
"""

import argparse
import json
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass
class CoverageReport:
    """Coverage report data structure"""
    total_lines: int
    covered_lines: int
    missing_lines: int
    coverage_percentage: float
    files: list[dict[str, Any]]


@dataclass
class CoverageImprovement:
    """Coverage improvement suggestion"""
    file_path: str
    missing_lines: list[int]
    priority: str
    effort: str
    suggestion: str


class CoverageAnalyzer:
    """Analyzes test coverage and suggests improvements"""

    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root)
        self.target_coverage = 90.0
        self.critical_modules = [
            "stillme_core/security",
            "stillme_core/privacy",
            "stillme_core/learning",
            "stillme_core/control",
            "stillme_core/transparency"
        ]

    def run_coverage_analysis(self) -> CoverageReport:
        """Run coverage analysis and return results"""
        print("🔍 Running coverage analysis...")

        # Run pytest with coverage
        cmd = [
            "python", "-m", "pytest",
            "--cov=stillme_core",
            "--cov-report=json:artifacts/coverage.json",
            "--cov-report=html:artifacts/coverage.html",
            "--cov-report=term-missing",
            "tests/"
        ]

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, cwd=self.project_root)
            if result.returncode != 0:
                print(f"⚠️ Coverage analysis completed with warnings: {result.stderr}")
        except Exception as e:
            print(f"❌ Error running coverage analysis: {e}")
            return self._create_empty_report()

        # Parse coverage results
        coverage_file = self.project_root / "artifacts" / "coverage.json"
        if coverage_file.exists():
            return self._parse_coverage_json(coverage_file)
        else:
            return self._create_empty_report()

    def _parse_coverage_json(self, coverage_file: Path) -> CoverageReport:
        """Parse coverage JSON file"""
        try:
            with open(coverage_file) as f:
                data = json.load(f)

            total_lines = data.get('totals', {}).get('num_statements', 0)
            covered_lines = data.get('totals', {}).get('covered_lines', 0)
            missing_lines = total_lines - covered_lines
            coverage_percentage = data.get('totals', {}).get('percent_covered', 0.0)

            files = []
            for file_path, file_data in data.get('files', {}).items():
                files.append({
                    'path': file_path,
                    'total_lines': file_data.get('num_statements', 0),
                    'covered_lines': file_data.get('covered_lines', 0),
                    'missing_lines': file_data.get('missing_lines', []),
                    'coverage_percentage': file_data.get('percent_covered', 0.0)
                })

            return CoverageReport(
                total_lines=total_lines,
                covered_lines=covered_lines,
                missing_lines=missing_lines,
                coverage_percentage=coverage_percentage,
                files=files
            )
        except Exception as e:
            print(f"❌ Error parsing coverage file: {e}")
            return self._create_empty_report()

    def _create_empty_report(self) -> CoverageReport:
        """Create empty coverage report"""
        return CoverageReport(
            total_lines=0,
            covered_lines=0,
            missing_lines=0,
            coverage_percentage=0.0,
            files=[]
        )

    def analyze_coverage_gaps(self, report: CoverageReport) -> list[CoverageImprovement]:
        """Analyze coverage gaps and suggest improvements"""
        improvements = []

        for file_info in report.files:
            if file_info['coverage_percentage'] < self.target_coverage:
                improvement = self._create_improvement_suggestion(file_info)
                improvements.append(improvement)

        # Sort by priority and effort
        improvements.sort(key=lambda x: (x.priority, x.effort))
        return improvements

    def _create_improvement_suggestion(self, file_info: dict[str, Any]) -> CoverageImprovement:
        """Create improvement suggestion for a file"""
        file_path = file_info['path']
        coverage_percentage = file_info['coverage_percentage']
        missing_lines = file_info['missing_lines']

        # Determine priority
        if any(module in file_path for module in self.critical_modules):
            priority = "HIGH"
        elif coverage_percentage < 50:
            priority = "HIGH"
        elif coverage_percentage < 75:
            priority = "MEDIUM"
        else:
            priority = "LOW"

        # Determine effort
        if len(missing_lines) > 50:
            effort = "HIGH"
        elif len(missing_lines) > 20:
            effort = "MEDIUM"
        else:
            effort = "LOW"

        # Create suggestion
        suggestion = self._generate_suggestion(file_path, missing_lines, coverage_percentage)

        return CoverageImprovement(
            file_path=file_path,
            missing_lines=missing_lines,
            priority=priority,
            effort=effort,
            suggestion=suggestion
        )

    def _generate_suggestion(self, file_path: str, missing_lines: list[int], coverage_percentage: float) -> str:
        """Generate improvement suggestion"""
        suggestions = []

        if coverage_percentage < 50:
            suggestions.append("Add comprehensive unit tests for all functions")
            suggestions.append("Add integration tests for main workflows")
        elif coverage_percentage < 75:
            suggestions.append("Add tests for edge cases and error conditions")
            suggestions.append("Add tests for boundary conditions")
        else:
            suggestions.append("Add tests for remaining uncovered lines")
            suggestions.append("Add tests for error handling paths")

        if len(missing_lines) > 0:
            suggestions.append(f"Focus on lines: {missing_lines[:10]}{'...' if len(missing_lines) > 10 else ''}")

        return "; ".join(suggestions)

    def generate_coverage_report(self, report: CoverageReport, improvements: list[CoverageImprovement]) -> str:
        """Generate comprehensive coverage report"""
        report_content = f"""
# Test Coverage Analysis Report
Generated: {self._get_current_timestamp()}

## Overall Coverage Summary
- **Total Lines**: {report.total_lines:,}
- **Covered Lines**: {report.covered_lines:,}
- **Missing Lines**: {report.missing_lines:,}
- **Coverage Percentage**: {report.coverage_percentage:.1f}%
- **Target Coverage**: {self.target_coverage}%

## Coverage Status
"""

        if report.coverage_percentage >= self.target_coverage:
            report_content += "✅ **TARGET ACHIEVED** - Coverage meets target requirements\n\n"
        else:
            report_content += f"⚠️ **BELOW TARGET** - Need {self.target_coverage - report.coverage_percentage:.1f}% more coverage\n\n"

        # Critical modules analysis
        report_content += "## Critical Modules Analysis\n\n"
        critical_coverage = self._analyze_critical_modules(report)
        for module, coverage in critical_coverage.items():
            status = "✅" if coverage >= self.target_coverage else "⚠️"
            report_content += f"- {status} **{module}**: {coverage:.1f}%\n"

        # Improvement suggestions
        report_content += "\n## Improvement Suggestions\n\n"
        if improvements:
            high_priority = [imp for imp in improvements if imp.priority == "HIGH"]
            medium_priority = [imp for imp in improvements if imp.priority == "MEDIUM"]
            low_priority = [imp for imp in improvements if imp.priority == "LOW"]

            if high_priority:
                report_content += "### 🔴 High Priority (Immediate Action Required)\n\n"
                for imp in high_priority[:5]:  # Top 5
                    report_content += f"- **{imp.file_path}** ({imp.effort} effort)\n"
                    report_content += f"  - {imp.suggestion}\n\n"

            if medium_priority:
                report_content += "### 🟡 Medium Priority (Next Sprint)\n\n"
                for imp in medium_priority[:5]:  # Top 5
                    report_content += f"- **{imp.file_path}** ({imp.effort} effort)\n"
                    report_content += f"  - {imp.suggestion}\n\n"

            if low_priority:
                report_content += "### 🟢 Low Priority (Future Improvements)\n\n"
                for imp in low_priority[:3]:  # Top 3
                    report_content += f"- **{imp.file_path}** ({imp.effort} effort)\n"
                    report_content += f"  - {imp.suggestion}\n\n"
        else:
            report_content += "🎉 **No improvements needed** - All modules meet coverage targets!\n\n"

        # Recommendations
        report_content += "## Recommendations\n\n"
        if report.coverage_percentage < self.target_coverage:
            report_content += "1. **Focus on critical modules** - Ensure security, privacy, and learning modules have 95%+ coverage\n"
            report_content += "2. **Add integration tests** - Test cross-module interactions and workflows\n"
            report_content += "3. **Add error handling tests** - Test exception paths and edge cases\n"
            report_content += "4. **Add performance tests** - Test under load and stress conditions\n"
            report_content += "5. **Automate coverage checks** - Add coverage gates to CI/CD pipeline\n\n"
        else:
            report_content += "1. **Maintain coverage** - Ensure new code includes tests\n"
            report_content += "2. **Improve test quality** - Focus on meaningful test cases\n"
            report_content += "3. **Add mutation testing** - Test test quality with mutation testing\n"
            report_content += "4. **Regular coverage reviews** - Monthly coverage analysis\n\n"

        return report_content

    def _analyze_critical_modules(self, report: CoverageReport) -> dict[str, float]:
        """Analyze coverage for critical modules"""
        critical_coverage = {}

        for module in self.critical_modules:
            module_files = [f for f in report.files if module in f['path']]
            if module_files:
                total_lines = sum(f['total_lines'] for f in module_files)
                covered_lines = sum(f['covered_lines'] for f in module_files)
                coverage = (covered_lines / total_lines * 100) if total_lines > 0 else 0.0
                critical_coverage[module] = coverage

        return critical_coverage

    def _get_current_timestamp(self) -> str:
        """Get current timestamp"""
        from datetime import datetime
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def save_report(self, report_content: str, output_file: str = "artifacts/coverage_improvement_report.md"):
        """Save coverage report to file"""
        output_path = self.project_root / output_file
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(report_content)

        print(f"📄 Coverage report saved to: {output_path}")


def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="Improve test coverage for StillMe AI Framework")
    parser.add_argument("--target", type=float, default=90.0, help="Target coverage percentage")
    parser.add_argument("--output", type=str, default="artifacts/coverage_improvement_report.md", help="Output file path")
    parser.add_argument("--project-root", type=str, default=".", help="Project root directory")

    args = parser.parse_args()

    print("🚀 Starting coverage improvement analysis...")
    print(f"📊 Target coverage: {args.target}%")
    print(f"📁 Project root: {args.project_root}")

    # Initialize analyzer
    analyzer = CoverageAnalyzer(args.project_root)
    analyzer.target_coverage = args.target

    # Run analysis
    report = analyzer.run_coverage_analysis()
    improvements = analyzer.analyze_coverage_gaps(report)

    # Generate report
    report_content = analyzer.generate_coverage_report(report, improvements)
    analyzer.save_report(report_content, args.output)

    # Print summary
    print("\n📈 Coverage Summary:")
    print(f"   Current: {report.coverage_percentage:.1f}%")
    print(f"   Target: {args.target}%")
    print(f"   Gap: {args.target - report.coverage_percentage:.1f}%")
    print(f"   Improvements needed: {len(improvements)}")

    if report.coverage_percentage >= args.target:
        print("🎉 Target coverage achieved!")
    else:
        print(f"⚠️ Need to improve coverage by {args.target - report.coverage_percentage:.1f}%")

    print(f"\n📄 Detailed report: {args.output}")


if __name__ == "__main__":
    main()
