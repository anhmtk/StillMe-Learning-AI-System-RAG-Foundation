"""AgentDev Quality Integration for StillMe Framework"""

import logging
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class IntegrationStatus(Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    ERROR = "error"
    PENDING = "pending"


class QualityGate(Enum):
    COVERAGE = "coverage"
    SECURITY = "security"
    PERFORMANCE = "performance"
    MAINTAINABILITY = "maintainability"
    ETHICS = "ethics"


@dataclass
class QualityGateResult:
    """Quality gate result"""

    gate_id: str
    gate_type: QualityGate
    status: str
    score: float
    threshold: float
    passed: bool
    timestamp: datetime
    details: dict[str, Any] | None = None

    def __post_init__(self):
        if self.details is None:
            self.details = {}


class AgentDevQualityIntegration:
    """AgentDev quality integration for StillMe Framework"""

    def __init__(self):
        self.logger = logger
        self.integration_status = IntegrationStatus.ACTIVE
        self.quality_gates: list[QualityGateResult] = []
        self.gate_thresholds = self._initialize_gate_thresholds()
        self.logger.info("✅ AgentDevQualityIntegration initialized")

    def _initialize_gate_thresholds(self) -> dict[QualityGate, float]:
        """Initialize quality gate thresholds"""
        return {
            QualityGate.COVERAGE: 80.0,  # 80% coverage
            QualityGate.SECURITY: 9.0,  # Security rating 1-10
            QualityGate.PERFORMANCE: 8.0,  # Performance rating 1-10
            QualityGate.MAINTAINABILITY: 7.0,  # Maintainability rating 1-10
            QualityGate.ETHICS: 9.0,  # Ethics rating 1-10
        }

    def run_quality_gates(
        self,
        code_content: str,
        test_results: dict[str, Any] = None,
        security_scan: dict[str, Any] = None,
        performance_metrics: dict[str, Any] = None,
    ) -> list[QualityGateResult]:
        """Run quality gates"""
        try:
            results = []

            # Coverage gate
            coverage_result = self._run_coverage_gate(test_results)
            if coverage_result:
                results.append(coverage_result)

            # Security gate
            security_result = self._run_security_gate(security_scan)
            if security_result:
                results.append(security_result)

            # Performance gate
            performance_result = self._run_performance_gate(performance_metrics)
            if performance_result:
                results.append(performance_result)

            # Maintainability gate
            maintainability_result = self._run_maintainability_gate(code_content)
            if maintainability_result:
                results.append(maintainability_result)

            # Ethics gate
            ethics_result = self._run_ethics_gate(code_content)
            if ethics_result:
                results.append(ethics_result)

            # Record results
            for result in results:
                self.quality_gates.append(result)
                status_icon = "✅" if result.passed else "❌"
                self.logger.info(
                    f"{status_icon} Quality gate: {result.gate_type.value} = {result.score} ({result.status})"
                )

            return results

        except Exception as e:
            self.logger.error(f"❌ Failed to run quality gates: {e}")
            return []

    def _run_coverage_gate(
        self, test_results: dict[str, Any] = None
    ) -> QualityGateResult | None:
        """Run coverage quality gate"""
        try:
            if not test_results:
                return None

            coverage = test_results.get("coverage", 0.0)
            threshold = self.gate_thresholds[QualityGate.COVERAGE]

            passed = coverage >= threshold
            status = "PASS" if passed else "FAIL"

            result = QualityGateResult(
                gate_id=f"coverage_{len(self.quality_gates) + 1}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                gate_type=QualityGate.COVERAGE,
                status=status,
                score=coverage,
                threshold=threshold,
                passed=passed,
                timestamp=datetime.now(),
                details={
                    "coverage_percentage": coverage,
                    "threshold_percentage": threshold,
                    "test_results": test_results,
                },
            )

            return result

        except Exception as e:
            self.logger.error(f"❌ Failed to run coverage gate: {e}")
            return None

    def _run_security_gate(
        self, security_scan: dict[str, Any] = None
    ) -> QualityGateResult | None:
        """Run security quality gate"""
        try:
            if not security_scan:
                return None

            # Calculate security score based on scan results
            high_severity = security_scan.get("high_severity", 0)
            medium_severity = security_scan.get("medium_severity", 0)
            total_issues = security_scan.get("total_issues", 0)

            # Simple scoring: 10 - (high * 2 + medium * 1) / 10
            security_score = max(0, 10 - (high_severity * 2 + medium_severity * 1) / 10)
            threshold = self.gate_thresholds[QualityGate.SECURITY]

            passed = security_score >= threshold
            status = "PASS" if passed else "FAIL"

            result = QualityGateResult(
                gate_id=f"security_{len(self.quality_gates) + 1}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                gate_type=QualityGate.SECURITY,
                status=status,
                score=security_score,
                threshold=threshold,
                passed=passed,
                timestamp=datetime.now(),
                details={
                    "high_severity_issues": high_severity,
                    "medium_severity_issues": medium_severity,
                    "total_issues": total_issues,
                    "security_scan": security_scan,
                },
            )

            return result

        except Exception as e:
            self.logger.error(f"❌ Failed to run security gate: {e}")
            return None

    def _run_performance_gate(
        self, performance_metrics: dict[str, Any] = None
    ) -> QualityGateResult | None:
        """Run performance quality gate"""
        try:
            if not performance_metrics:
                return None

            # Calculate performance score based on metrics
            response_time = performance_metrics.get("response_time", 1000)  # ms
            memory_usage = performance_metrics.get("memory_usage", 100)  # MB
            cpu_usage = performance_metrics.get("cpu_usage", 80)  # %

            # Simple scoring: 10 - (response_time/1000 + memory_usage/100 + cpu_usage/100)
            performance_score = max(
                0, 10 - (response_time / 1000 + memory_usage / 100 + cpu_usage / 100)
            )
            threshold = self.gate_thresholds[QualityGate.PERFORMANCE]

            passed = performance_score >= threshold
            status = "PASS" if passed else "FAIL"

            result = QualityGateResult(
                gate_id=f"performance_{len(self.quality_gates) + 1}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                gate_type=QualityGate.PERFORMANCE,
                status=status,
                score=performance_score,
                threshold=threshold,
                passed=passed,
                timestamp=datetime.now(),
                details={
                    "response_time_ms": response_time,
                    "memory_usage_mb": memory_usage,
                    "cpu_usage_percent": cpu_usage,
                    "performance_metrics": performance_metrics,
                },
            )

            return result

        except Exception as e:
            self.logger.error(f"❌ Failed to run performance gate: {e}")
            return None

    def _run_maintainability_gate(self, code_content: str) -> QualityGateResult | None:
        """Run maintainability quality gate"""
        try:
            if not code_content:
                return None

            # Simple maintainability scoring based on code characteristics
            lines = code_content.split("\n")
            total_lines = len(lines)

            # Count various maintainability indicators
            docstring_lines = sum(1 for line in lines if '"""' in line or "'''" in line)
            comment_lines = sum(1 for line in lines if line.strip().startswith("#"))
            function_definitions = sum(
                1 for line in lines if line.strip().startswith("def ")
            )
            class_definitions = sum(
                1 for line in lines if line.strip().startswith("class ")
            )

            # Calculate maintainability score
            docstring_ratio = docstring_lines / max(
                1, function_definitions + class_definitions
            )
            comment_ratio = comment_lines / max(1, total_lines)

            maintainability_score = (docstring_ratio * 5 + comment_ratio * 5) * 10
            maintainability_score = min(10, maintainability_score)

            threshold = self.gate_thresholds[QualityGate.MAINTAINABILITY]

            passed = maintainability_score >= threshold
            status = "PASS" if passed else "FAIL"

            result = QualityGateResult(
                gate_id=f"maintainability_{len(self.quality_gates) + 1}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                gate_type=QualityGate.MAINTAINABILITY,
                status=status,
                score=maintainability_score,
                threshold=threshold,
                passed=passed,
                timestamp=datetime.now(),
                details={
                    "total_lines": total_lines,
                    "docstring_lines": docstring_lines,
                    "comment_lines": comment_lines,
                    "function_definitions": function_definitions,
                    "class_definitions": class_definitions,
                    "docstring_ratio": docstring_ratio,
                    "comment_ratio": comment_ratio,
                },
            )

            return result

        except Exception as e:
            self.logger.error(f"❌ Failed to run maintainability gate: {e}")
            return None

    def _run_ethics_gate(self, code_content: str) -> QualityGateResult | None:
        """Run ethics quality gate"""
        try:
            if not code_content:
                return None

            # Simple ethics scoring based on content analysis
            content_lower = code_content.lower()

            # Check for ethical concerns
            harmful_keywords = ["violence", "harm", "danger", "threat", "attack"]
            bias_keywords = ["always", "never", "all", "none", "typical", "normal"]
            privacy_keywords = ["password", "secret", "key", "token", "personal"]

            harmful_count = sum(
                1 for keyword in harmful_keywords if keyword in content_lower
            )
            bias_count = sum(1 for keyword in bias_keywords if keyword in content_lower)
            privacy_count = sum(
                1 for keyword in privacy_keywords if keyword in content_lower
            )

            # Calculate ethics score (10 - violations)
            ethics_score = max(
                0, 10 - (harmful_count * 2 + bias_count * 1 + privacy_count * 2)
            )
            threshold = self.gate_thresholds[QualityGate.ETHICS]

            passed = ethics_score >= threshold
            status = "PASS" if passed else "FAIL"

            result = QualityGateResult(
                gate_id=f"ethics_{len(self.quality_gates) + 1}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                gate_type=QualityGate.ETHICS,
                status=status,
                score=ethics_score,
                threshold=threshold,
                passed=passed,
                timestamp=datetime.now(),
                details={
                    "harmful_keywords_found": harmful_count,
                    "bias_keywords_found": bias_count,
                    "privacy_keywords_found": privacy_count,
                    "total_violations": harmful_count + bias_count + privacy_count,
                },
            )

            return result

        except Exception as e:
            self.logger.error(f"❌ Failed to run ethics gate: {e}")
            return None

    def get_quality_gate_summary(self) -> dict[str, Any]:
        """Get quality gate summary"""
        try:
            total_gates = len(self.quality_gates)

            gates_by_type = {}
            gates_by_status = {}
            passed_gates = 0

            for gate in self.quality_gates:
                # By type
                type_key = gate.gate_type.value
                gates_by_type[type_key] = gates_by_type.get(type_key, 0) + 1

                # By status
                status_key = gate.status
                gates_by_status[status_key] = gates_by_status.get(status_key, 0) + 1

                # Count passed gates
                if gate.passed:
                    passed_gates += 1

            # Calculate overall quality score
            overall_score = (passed_gates / max(1, total_gates)) * 100

            return {
                "total_gates": total_gates,
                "passed_gates": passed_gates,
                "failed_gates": total_gates - passed_gates,
                "overall_quality_score": overall_score,
                "gates_by_type": gates_by_type,
                "gates_by_status": gates_by_status,
                "integration_status": self.integration_status.value,
                "timestamp": datetime.now().isoformat(),
            }

        except Exception as e:
            self.logger.error(f"❌ Failed to get quality gate summary: {e}")
            return {"error": str(e)}

    def update_gate_threshold(self, gate_type: QualityGate, threshold: float):
        """Update quality gate threshold"""
        try:
            self.gate_thresholds[gate_type] = threshold
            self.logger.info(
                f"📝 Gate threshold updated: {gate_type.value} = {threshold}"
            )

        except Exception as e:
            self.logger.error(f"❌ Failed to update gate threshold: {e}")
            raise

    def clear_quality_gates(self):
        """Clear all quality gates"""
        self.quality_gates.clear()
        self.logger.info("🧹 All quality gates cleared")
