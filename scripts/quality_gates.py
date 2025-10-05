#!/usr/bin/env python3
"""
Quality Gates for StillMe AI Framework
======================================

This script implements quality gates to ensure code quality, security, and performance
standards are met before deployment.

Author: StillMe AI Framework Team
Version: 1.0.0
Last Updated: 2025-09-26
"""

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path


@dataclass
class QualityGate:
    """Quality gate definition"""

    name: str
    description: str
    threshold: float
    current_value: float
    status: str  # PASS, FAIL, WARNING
    weight: float  # Importance weight (0-1)


@dataclass
class QualityReport:
    """Quality report data structure"""

    overall_status: str
    total_gates: int
    passed_gates: int
    failed_gates: int
    warning_gates: int
    quality_score: float
    gates: list[QualityGate]
    recommendations: list[str]


class QualityGates:
    """Quality gates implementation for StillMe AI Framework"""

    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root)
        self.artifacts_dir = self.project_root / "artifacts"
        self.gates = self._initialize_gates()

    def _initialize_gates(self) -> list[QualityGate]:
        """Initialize quality gates with default thresholds"""
        return [
            QualityGate(
                name="test_coverage",
                description="Test coverage percentage",
                threshold=85.0,
                current_value=0.0,
                status="UNKNOWN",
                weight=0.2,
            ),
            QualityGate(
                name="test_pass_rate",
                description="Test pass rate percentage",
                threshold=90.0,
                current_value=0.0,
                status="UNKNOWN",
                weight=0.15,
            ),
            QualityGate(
                name="security_score",
                description="Security score (0-100)",
                threshold=75.0,
                current_value=0.0,
                status="UNKNOWN",
                weight=0.25,
            ),
            QualityGate(
                name="performance_p95",
                description="P95 response time (ms)",
                threshold=1000.0,
                current_value=0.0,
                status="UNKNOWN",
                weight=0.15,
            ),
            QualityGate(
                name="error_rate",
                description="Error rate percentage",
                threshold=5.0,
                current_value=0.0,
                status="UNKNOWN",
                weight=0.1,
            ),
            QualityGate(
                name="ethics_compliance",
                description="Ethics test pass rate",
                threshold=95.0,
                current_value=0.0,
                status="UNKNOWN",
                weight=0.15,
            ),
        ]

    def evaluate_gates(self, input_dir: str = "artifacts") -> QualityReport:
        """Evaluate all quality gates"""
        print("🚪 Evaluating quality gates...")

        # Load metrics from artifacts
        metrics = self._load_metrics_from_artifacts(input_dir)

        # Update gate values
        for gate in self.gates:
            gate.current_value = metrics.get(gate.name, 0.0)
            gate.status = self._evaluate_gate_status(gate)

        # Calculate overall status
        overall_status = self._calculate_overall_status()
        quality_score = self._calculate_quality_score()

        # Generate recommendations
        recommendations = self._generate_recommendations()

        return QualityReport(
            overall_status=overall_status,
            total_gates=len(self.gates),
            passed_gates=len([g for g in self.gates if g.status == "PASS"]),
            failed_gates=len([g for g in self.gates if g.status == "FAIL"]),
            warning_gates=len([g for g in self.gates if g.status == "WARNING"]),
            quality_score=quality_score,
            gates=self.gates,
            recommendations=recommendations,
        )

    def _load_metrics_from_artifacts(self, input_dir: str) -> dict[str, float]:
        """Load metrics from artifact files"""
        metrics = {}
        artifacts_path = self.project_root / input_dir

        if not artifacts_path.exists():
            print(f"⚠️ Artifacts directory not found: {artifacts_path}")
            return metrics

        # Load test coverage
        coverage_files = list(artifacts_path.glob("*coverage*.json"))
        for coverage_file in coverage_files:
            try:
                with open(coverage_file) as f:
                    data = json.load(f)
                if "totals" in data:
                    metrics["test_coverage"] = data["totals"].get(
                        "percent_covered", 0.0
                    )
                break
            except Exception as e:
                print(f"⚠️ Error reading coverage file {coverage_file}: {e}")

        # Load test results
        test_files = list(artifacts_path.glob("*test*.json"))
        for test_file in test_files:
            try:
                with open(test_file) as f:
                    data = json.load(f)
                if "tests" in data and "passed" in data:
                    total_tests = data["tests"]
                    passed_tests = data["passed"]
                    if total_tests > 0:
                        metrics["test_pass_rate"] = (passed_tests / total_tests) * 100
                break
            except Exception as e:
                print(f"⚠️ Error reading test file {test_file}: {e}")

        # Load security metrics
        security_files = list(artifacts_path.glob("*security*.json"))
        for security_file in security_files:
            try:
                with open(security_file) as f:
                    data = json.load(f)
                if "security_score" in data:
                    metrics["security_score"] = data["security_score"]
                elif "vulnerabilities" in data:
                    # Calculate security score from vulnerabilities
                    vulns = data["vulnerabilities"]
                    critical = vulns.get("critical", 0)
                    high = vulns.get("high", 0)
                    medium = vulns.get("medium", 0)
                    low = vulns.get("low", 0)

                    # Simple scoring: start at 100, subtract based on severity
                    score = (
                        100 - (critical * 20) - (high * 10) - (medium * 5) - (low * 1)
                    )
                    metrics["security_score"] = max(0, score)
                break
            except Exception as e:
                print(f"⚠️ Error reading security file {security_file}: {e}")

        # Load performance metrics
        perf_files = list(artifacts_path.glob("*performance*.json"))
        for perf_file in perf_files:
            try:
                with open(perf_file) as f:
                    data = json.load(f)
                if "metrics" in data:
                    metrics_data = data["metrics"]
                    metrics["performance_p95"] = metrics_data.get(
                        "p95_response_time", 0.0
                    )
                    metrics["error_rate"] = metrics_data.get("error_rate", 0.0)
                break
            except Exception as e:
                print(f"⚠️ Error reading performance file {perf_file}: {e}")

        # Load ethics metrics
        ethics_files = list(artifacts_path.glob("*ethics*.json"))
        for ethics_file in ethics_files:
            try:
                with open(ethics_file) as f:
                    data = json.load(f)
                if "pass_rate" in data:
                    metrics["ethics_compliance"] = data["pass_rate"]
                elif "passed" in data and "total" in data:
                    if data["total"] > 0:
                        metrics["ethics_compliance"] = (
                            data["passed"] / data["total"]
                        ) * 100
                break
            except Exception as e:
                print(f"⚠️ Error reading ethics file {ethics_file}: {e}")

        return metrics

    def _evaluate_gate_status(self, gate: QualityGate) -> str:
        """Evaluate individual gate status"""
        if gate.name in ["performance_p95", "error_rate"]:
            # Lower is better for these metrics
            if gate.current_value <= gate.threshold:
                return "PASS"
            elif gate.current_value <= gate.threshold * 1.2:
                return "WARNING"
            else:
                return "FAIL"
        else:
            # Higher is better for these metrics
            if gate.current_value >= gate.threshold:
                return "PASS"
            elif gate.current_value >= gate.threshold * 0.8:
                return "WARNING"
            else:
                return "FAIL"

    def _calculate_overall_status(self) -> str:
        """Calculate overall quality status"""
        failed_gates = [g for g in self.gates if g.status == "FAIL"]
        warning_gates = [g for g in self.gates if g.status == "WARNING"]

        if failed_gates:
            return "FAIL"
        elif warning_gates:
            return "WARNING"
        else:
            return "PASS"

    def _calculate_quality_score(self) -> float:
        """Calculate weighted quality score"""
        total_weight = sum(gate.weight for gate in self.gates)
        weighted_score = 0.0

        for gate in self.gates:
            if gate.status == "PASS":
                gate_score = 100.0
            elif gate.status == "WARNING":
                gate_score = 70.0
            else:
                gate_score = 0.0

            weighted_score += gate_score * gate.weight

        return weighted_score / total_weight if total_weight > 0 else 0.0

    def _generate_recommendations(self) -> list[str]:
        """Generate improvement recommendations"""
        recommendations = []

        failed_gates = [g for g in self.gates if g.status == "FAIL"]
        warning_gates = [g for g in self.gates if g.status == "WARNING"]

        # Critical issues (failed gates)
        if failed_gates:
            recommendations.append(
                "🔴 CRITICAL: Address failed quality gates immediately"
            )
            for gate in failed_gates:
                if gate.name == "test_coverage":
                    recommendations.append(
                        f"   - Increase test coverage from {gate.current_value:.1f}% to {gate.threshold}%"
                    )
                elif gate.name == "test_pass_rate":
                    recommendations.append(
                        f"   - Fix failing tests to achieve {gate.threshold}% pass rate"
                    )
                elif gate.name == "security_score":
                    recommendations.append(
                        f"   - Address security vulnerabilities (current: {gate.current_value:.1f}/100)"
                    )
                elif gate.name == "performance_p95":
                    recommendations.append(
                        f"   - Optimize performance (P95: {gate.current_value:.0f}ms > {gate.threshold}ms)"
                    )
                elif gate.name == "error_rate":
                    recommendations.append(
                        f"   - Reduce error rate from {gate.current_value:.1f}% to {gate.threshold}%"
                    )
                elif gate.name == "ethics_compliance":
                    recommendations.append(
                        f"   - Fix ethics test failures (current: {gate.current_value:.1f}%)"
                    )

        # Warning issues
        if warning_gates:
            recommendations.append(
                "🟡 WARNING: Monitor and improve warning quality gates"
            )
            for gate in warning_gates:
                recommendations.append(
                    f"   - {gate.description}: {gate.current_value:.1f} (target: {gate.threshold})"
                )

        # General recommendations
        if not failed_gates and not warning_gates:
            recommendations.append(
                "✅ All quality gates passed! Maintain current standards."
            )
        else:
            recommendations.append(
                "📊 Implement continuous monitoring to prevent regression"
            )
            recommendations.append("🔄 Add automated quality checks to CI/CD pipeline")
            recommendations.append("📚 Provide team training on quality standards")

        return recommendations

    def generate_report(self, report: QualityReport) -> str:
        """Generate quality gates report"""
        report_content = f"""
# Quality Gates Report
Generated: {self._get_current_timestamp()}

## Executive Summary
- **Overall Status**: {report.overall_status}
- **Quality Score**: {report.quality_score:.1f}/100
- **Total Gates**: {report.total_gates}
- **Passed**: {report.passed_gates} ✅
- **Failed**: {report.failed_gates} ❌
- **Warning**: {report.warning_gates} ⚠️

## Quality Gates Status
"""

        for gate in report.gates:
            status_icon = (
                "✅"
                if gate.status == "PASS"
                else "⚠️"
                if gate.status == "WARNING"
                else "❌"
            )
            report_content += (
                f"### {status_icon} {gate.name.replace('_', ' ').title()}\n"
            )
            report_content += f"- **Description**: {gate.description}\n"
            report_content += f"- **Current Value**: {gate.current_value:.1f}\n"
            report_content += f"- **Threshold**: {gate.threshold:.1f}\n"
            report_content += f"- **Status**: {gate.status}\n"
            report_content += f"- **Weight**: {gate.weight:.1f}\n\n"

        # Recommendations
        report_content += "## Recommendations\n\n"
        for i, rec in enumerate(report.recommendations, 1):
            report_content += f"{i}. {rec}\n"

        # Action plan
        report_content += "\n## Action Plan\n\n"
        if report.overall_status == "FAIL":
            report_content += "### Immediate Actions (Next 24 hours)\n"
            report_content += "- Fix all failed quality gates\n"
            report_content += "- Address critical security vulnerabilities\n"
            report_content += "- Fix failing tests\n"
            report_content += "- Optimize performance bottlenecks\n\n"
        elif report.overall_status == "WARNING":
            report_content += "### Short-term Actions (Next 1 week)\n"
            report_content += "- Address warning quality gates\n"
            report_content += "- Improve test coverage\n"
            report_content += "- Enhance security posture\n"
            report_content += "- Optimize performance\n\n"
        else:
            report_content += "### Maintenance Actions\n"
            report_content += "- Continue monitoring quality metrics\n"
            report_content += "- Maintain current quality standards\n"
            report_content += "- Implement preventive measures\n\n"

        # Quality trends
        report_content += "## Quality Trends\n\n"
        report_content += "### Improvement Areas\n"
        for gate in sorted(report.gates, key=lambda x: x.weight, reverse=True):
            if gate.status != "PASS":
                report_content += f"- **{gate.name.replace('_', ' ').title()}**: {gate.current_value:.1f} → {gate.threshold:.1f}\n"

        report_content += "\n### Success Metrics\n"
        for gate in report.gates:
            if gate.status == "PASS":
                report_content += f"- **{gate.name.replace('_', ' ').title()}**: {gate.current_value:.1f} ✅\n"

        return report_content

    def _get_current_timestamp(self) -> str:
        """Get current timestamp"""
        from datetime import datetime

        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def save_report(
        self,
        report_content: str,
        output_file: str = "artifacts/quality_gates_report.md",
    ):
        """Save quality gates report to file"""
        output_path = self.project_root / output_file
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(report_content)

        print(f"📄 Quality gates report saved to: {output_path}")

    def run_quality_checks(self) -> bool:
        """Run quality checks and return pass/fail status"""
        print("🚪 Running quality gates...")

        # Evaluate gates
        report = self.evaluate_gates()

        # Generate and save report
        report_content = self.generate_report(report)
        self.save_report(report_content)

        # Print summary
        print("\n🚪 Quality Gates Summary:")
        print(f"   Overall Status: {report.overall_status}")
        print(f"   Quality Score: {report.quality_score:.1f}/100")
        print(f"   Passed: {report.passed_gates}/{report.total_gates}")

        if report.failed_gates > 0:
            print(f"   Failed Gates: {report.failed_gates}")
            for gate in report.gates:
                if gate.status == "FAIL":
                    print(
                        f"     - {gate.name}: {gate.current_value:.1f} (target: {gate.threshold:.1f})"
                    )

        if report.warning_gates > 0:
            print(f"   Warning Gates: {report.warning_gates}")
            for gate in report.gates:
                if gate.status == "WARNING":
                    print(
                        f"     - {gate.name}: {gate.current_value:.1f} (target: {gate.threshold:.1f})"
                    )

        # Return pass/fail status
        return report.overall_status == "PASS"


def main():
    """Main function"""
    parser = argparse.ArgumentParser(
        description="Quality Gates for StillMe AI Framework"
    )
    parser.add_argument(
        "--coverage-threshold", type=float, default=85.0, help="Test coverage threshold"
    )
    parser.add_argument(
        "--security-threshold",
        type=float,
        default=75.0,
        help="Security score threshold",
    )
    parser.add_argument(
        "--performance-threshold",
        type=float,
        default=1000.0,
        help="Performance P95 threshold",
    )
    parser.add_argument(
        "--ethics-threshold",
        type=float,
        default=95.0,
        help="Ethics compliance threshold",
    )
    parser.add_argument(
        "--input", type=str, default="artifacts", help="Input directory for metrics"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="artifacts/quality_gates_report.md",
        help="Output report file",
    )
    parser.add_argument(
        "--project-root", type=str, default=".", help="Project root directory"
    )

    args = parser.parse_args()

    print("🚪 Starting quality gates evaluation...")
    print(f"📁 Project root: {args.project_root}")
    print(f"📊 Input directory: {args.input}")

    # Initialize quality gates
    quality_gates = QualityGates(args.project_root)

    # Update thresholds
    for gate in quality_gates.gates:
        if gate.name == "test_coverage":
            gate.threshold = args.coverage_threshold
        elif gate.name == "security_score":
            gate.threshold = args.security_threshold
        elif gate.name == "performance_p95":
            gate.threshold = args.performance_threshold
        elif gate.name == "ethics_compliance":
            gate.threshold = args.ethics_threshold

    # Run quality checks
    passed = quality_gates.run_quality_checks()

    if passed:
        print("✅ Quality gates PASSED!")
        sys.exit(0)
    else:
        print("❌ Quality gates FAILED!")
        sys.exit(1)


if __name__ == "__main__":
    main()
