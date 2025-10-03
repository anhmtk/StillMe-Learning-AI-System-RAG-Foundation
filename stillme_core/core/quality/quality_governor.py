# stillme_core/quality/quality_governor.py
"""
Code quality governance and management system
"""

from __future__ import annotations

import ast
import json
import logging
import time
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class QualityMetric(Enum):
    """Quality metrics to track"""

    CYCLOMATIC_COMPLEXITY = "cyclomatic_complexity"
    COGNITIVE_COMPLEXITY = "cognitive_complexity"
    CODE_DUPLICATION = "code_duplication"
    TEST_COVERAGE = "test_coverage"
    DOCUMENTATION_COVERAGE = "documentation_coverage"
    MAINTAINABILITY_INDEX = "maintainability_index"
    TECHNICAL_DEBT = "technical_debt"
    CODE_SMELLS = "code_smells"


class QualityStandard(Enum):
    """Quality standards"""

    EXCELLENT = "excellent"
    GOOD = "good"
    ACCEPTABLE = "acceptable"
    POOR = "poor"
    CRITICAL = "critical"


@dataclass
class QualityViolation:
    """Quality violation representation"""

    metric: QualityMetric
    standard: QualityStandard
    file_path: str
    line_number: int
    description: str
    current_value: float
    threshold: float
    severity: str
    recommendation: str


@dataclass
class QualityReport:
    """Comprehensive quality report"""

    overall_score: float
    metrics_summary: dict[QualityMetric, dict[str, Any]]
    violations: list[QualityViolation]
    recommendations: list[str]
    quality_trends: dict[str, float]
    report_duration: float


class QualityGovernor:
    """
    Comprehensive code quality governance system
    """

    def __init__(self, repo_root: str = "."):
        self.repo_root = Path(repo_root)
        self.quality_thresholds = self._load_quality_thresholds()
        self.coding_standards = self._load_coding_standards()
        self.quality_history = self._load_quality_history()

    def _load_quality_thresholds(self) -> dict[QualityMetric, dict[str, float]]:
        """Load quality thresholds for different metrics"""
        return {
            QualityMetric.CYCLOMATIC_COMPLEXITY: {
                "excellent": 5,
                "good": 10,
                "acceptable": 15,
                "poor": 20,
                "critical": 25,
            },
            QualityMetric.COGNITIVE_COMPLEXITY: {
                "excellent": 10,
                "good": 20,
                "acceptable": 30,
                "poor": 40,
                "critical": 50,
            },
            QualityMetric.CODE_DUPLICATION: {
                "excellent": 0.05,  # 5%
                "good": 0.10,  # 10%
                "acceptable": 0.15,  # 15%
                "poor": 0.20,  # 20%
                "critical": 0.25,  # 25%
            },
            QualityMetric.TEST_COVERAGE: {
                "excellent": 0.90,  # 90%
                "good": 0.80,  # 80%
                "acceptable": 0.70,  # 70%
                "poor": 0.60,  # 60%
                "critical": 0.50,  # 50%
            },
            QualityMetric.DOCUMENTATION_COVERAGE: {
                "excellent": 0.80,  # 80%
                "good": 0.70,  # 70%
                "acceptable": 0.60,  # 60%
                "poor": 0.50,  # 50%
                "critical": 0.40,  # 40%
            },
            QualityMetric.MAINTAINABILITY_INDEX: {
                "excellent": 80,
                "good": 70,
                "acceptable": 60,
                "poor": 50,
                "critical": 40,
            },
        }

    def _load_coding_standards(self) -> dict[str, list[dict[str, Any]]]:
        """Load coding standards and rules"""
        return {
            "naming_conventions": [
                {
                    "pattern": r"^[a-z_][a-z0-9_]*$",
                    "description": "Function and variable names should be lowercase with underscores",
                    "severity": "medium",
                },
                {
                    "pattern": r"^[A-Z][a-zA-Z0-9]*$",
                    "description": "Class names should be PascalCase",
                    "severity": "medium",
                },
                {
                    "pattern": r"^[A-Z_][A-Z0-9_]*$",
                    "description": "Constants should be UPPER_CASE",
                    "severity": "low",
                },
            ],
            "import_standards": [
                {
                    "pattern": r"^import\s+\w+$",
                    "description": "Use absolute imports",
                    "severity": "low",
                },
                {
                    "pattern": r"^from\s+\w+\s+import\s+\w+$",
                    "description": "Use specific imports instead of wildcard imports",
                    "severity": "medium",
                },
            ],
            "function_standards": [
                {
                    "pattern": r"def\s+\w+\([^)]*\):",
                    "description": "Functions should have docstrings",
                    "severity": "medium",
                },
                {
                    "pattern": r"def\s+\w+\([^)]{50,}\):",
                    "description": "Functions with too many parameters",
                    "severity": "high",
                },
            ],
            "error_handling": [
                {
                    "pattern": r"except\s*:",
                    "description": "Avoid bare except clauses",
                    "severity": "high",
                },
                {
                    "pattern": r"except\s+Exception\s*:",
                    "description": "Use specific exception types",
                    "severity": "medium",
                },
            ],
        }

    def _load_quality_history(self) -> dict[str, list[float]]:
        """Load quality history for trend analysis"""
        history_file = self.repo_root / ".quality_history.json"
        if history_file.exists():
            try:
                with open(history_file) as f:
                    return json.load(f)
            except Exception:
                pass
        return {}

    def assess_code_quality(self) -> QualityReport:
        """Perform comprehensive code quality assessment"""
        start_time = time.time()
        violations = []
        metrics_summary = {}

        # Analyze all Python files
        python_files = list(self.repo_root.rglob("*.py"))
        total_files = len(python_files)

        if total_files == 0:
            return QualityReport(
                overall_score=100.0,
                metrics_summary={},
                violations=[],
                recommendations=["No Python files found to analyze"],
                quality_trends={},
                report_duration=time.time() - start_time,
            )

        # Calculate metrics for each file
        file_metrics = []
        for py_file in python_files:
            if self._should_analyze_file(py_file):
                metrics = self._calculate_file_metrics(py_file)
                file_metrics.append(metrics)

        # Aggregate metrics
        for metric in QualityMetric:
            metric_data = self._aggregate_metric(metric, file_metrics)
            metrics_summary[metric] = metric_data

            # Check for violations
            metric_violations = self._check_metric_violations(
                metric, metric_data, file_metrics
            )
            violations.extend(metric_violations)

        # Calculate overall quality score
        overall_score = self._calculate_overall_quality_score(
            metrics_summary, violations
        )

        # Generate recommendations
        recommendations = self._generate_quality_recommendations(
            metrics_summary, violations
        )

        # Update quality trends
        self._update_quality_trends(metrics_summary, overall_score)

        report_duration = time.time() - start_time

        return QualityReport(
            overall_score=overall_score,
            metrics_summary=metrics_summary,
            violations=violations,
            recommendations=recommendations,
            quality_trends={
                k: v[-1] if v else 0.0 for k, v in self.quality_history.items()
            },
            report_duration=report_duration,
        )

    def _should_analyze_file(self, file_path: Path) -> bool:
        """Determine if file should be analyzed"""
        skip_patterns = [
            "test_",
            "_test.py",
            "tests/",
            "__pycache__/",
            ".venv/",
            "venv/",
            "env/",
            "build/",
            "dist/",
        ]

        file_str = str(file_path)
        return not any(pattern in file_str for pattern in skip_patterns)

    def _calculate_file_metrics(self, file_path: Path) -> dict[QualityMetric, float]:
        """Calculate quality metrics for a single file"""
        metrics = {}

        try:
            with open(file_path, encoding="utf-8") as f:
                content = f.read()

            # Parse AST
            try:
                tree = ast.parse(content)
            except SyntaxError:
                # File has syntax errors
                return {metric: float("inf") for metric in QualityMetric}

            # Calculate cyclomatic complexity
            metrics[QualityMetric.CYCLOMATIC_COMPLEXITY] = (
                self._calculate_cyclomatic_complexity(tree)
            )

            # Calculate cognitive complexity
            metrics[QualityMetric.COGNITIVE_COMPLEXITY] = (
                self._calculate_cognitive_complexity(tree)
            )

            # Calculate documentation coverage
            metrics[QualityMetric.DOCUMENTATION_COVERAGE] = (
                self._calculate_documentation_coverage(content)
            )

            # Calculate maintainability index
            metrics[QualityMetric.MAINTAINABILITY_INDEX] = (
                self._calculate_maintainability_index(
                    metrics[QualityMetric.CYCLOMATIC_COMPLEXITY],
                    len(content.splitlines()),
                    metrics[QualityMetric.DOCUMENTATION_COVERAGE],
                )
            )

            # Calculate code smells
            metrics[QualityMetric.CODE_SMELLS] = self._calculate_code_smells(
                tree, content
            )

        except Exception as e:
            logger.error(f"Error calculating metrics for {file_path}: {e}")
            return dict.fromkeys(QualityMetric, 0.0)

        return metrics

    def _calculate_cyclomatic_complexity(self, tree: ast.AST) -> float:
        """Calculate cyclomatic complexity"""
        complexity = 1  # Base complexity

        for node in ast.walk(tree):
            if (
                isinstance(node, ast.If | ast.While | ast.For | ast.AsyncFor)
                or isinstance(node, ast.ExceptHandler)
                or isinstance(node, ast.And | ast.Or)
            ):
                complexity += 1

        return float(complexity)

    def _calculate_cognitive_complexity(self, tree: ast.AST) -> float:
        """Calculate cognitive complexity (simplified)"""
        complexity = 0

        for node in ast.walk(tree):
            if isinstance(node, ast.If):
                complexity += 1
                # Nested conditions add more complexity
                for child in ast.walk(node):
                    if isinstance(child, ast.If) and child != node:
                        complexity += 1
            elif (
                isinstance(node, ast.While | ast.For | ast.AsyncFor)
                or isinstance(node, ast.ExceptHandler)
                or isinstance(node, ast.And | ast.Or)
            ):
                complexity += 1

        return float(complexity)

    def _calculate_documentation_coverage(self, content: str) -> float:
        """Calculate documentation coverage"""
        lines = content.splitlines()
        total_functions = 0
        documented_functions = 0

        # Simple heuristic: count functions and docstrings
        for i, line in enumerate(lines):
            stripped = line.strip()

            if stripped.startswith("def ") and ":" in stripped:
                total_functions += 1
                # Check next few lines for docstring
                for j in range(i + 1, min(i + 5, len(lines))):
                    next_line = lines[j].strip()
                    if next_line.startswith('"""') or next_line.startswith("'''"):
                        documented_functions += 1
                        break
                    elif next_line and not next_line.startswith("#"):
                        break
            elif (
                stripped
                and not stripped.startswith("#")
                and not stripped.startswith('"""')
            ):
                pass

        return documented_functions / total_functions if total_functions > 0 else 1.0

    def _calculate_maintainability_index(
        self, cyclomatic_complexity: float, lines_of_code: int, doc_coverage: float
    ) -> float:
        """Calculate maintainability index (simplified)"""
        # Simplified maintainability index calculation
        # In practice, you'd use more sophisticated algorithms

        # Penalize high complexity
        complexity_penalty = min(cyclomatic_complexity * 2, 30)

        # Penalize large files
        size_penalty = min(lines_of_code / 10, 20)

        # Reward documentation
        doc_bonus = doc_coverage * 10

        # Base score
        base_score = 100

        maintainability = base_score - complexity_penalty - size_penalty + doc_bonus
        return max(0, min(100, maintainability))

    def _calculate_code_smells(self, tree: ast.AST, content: str) -> float:
        """Calculate code smells count"""
        smells = 0

        # Long parameter lists
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                if len(node.args.args) > 5:
                    smells += 1

        # Long functions
        lines = content.splitlines()
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                if node.lineno < len(lines):
                    # Estimate function length
                    func_lines = 0
                    for i in range(node.lineno - 1, len(lines)):
                        if (
                            lines[i].strip()
                            and not lines[i].startswith(" ")
                            and not lines[i].startswith("\t")
                        ):
                            break
                        func_lines += 1

                    if func_lines > 50:
                        smells += 1

        # Duplicate code (simplified)
        # In practice, you'd use more sophisticated duplicate detection
        function_bodies = []
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                func_source = ast.get_source_segment(content, node)
                if func_source:
                    function_bodies.append(func_source)

        # Check for similar function bodies
        for i, body1 in enumerate(function_bodies):
            for body2 in function_bodies[i + 1 :]:
                if self._calculate_similarity(body1, body2) > 0.8:
                    smells += 1

        return float(smells)

    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """Calculate text similarity (simplified)"""
        # Simple character-based similarity
        if not text1 or not text2:
            return 0.0

        # Normalize whitespace
        text1 = " ".join(text1.split())
        text2 = " ".join(text2.split())

        # Simple Jaccard similarity
        set1 = set(text1.split())
        set2 = set(text2.split())

        intersection = len(set1.intersection(set2))
        union = len(set1.union(set2))

        return intersection / union if union > 0 else 0.0

    def _aggregate_metric(
        self, metric: QualityMetric, file_metrics: list[dict[QualityMetric, float]]
    ) -> dict[str, Any]:
        """Aggregate metric across all files"""
        values = [fm.get(metric, 0.0) for fm in file_metrics if metric in fm]

        if not values:
            return {"average": 0.0, "min": 0.0, "max": 0.0, "median": 0.0, "count": 0}

        values.sort()
        count = len(values)

        return {
            "average": sum(values) / count,
            "min": min(values),
            "max": max(values),
            "median": values[count // 2],
            "count": count,
        }

    def _check_metric_violations(
        self,
        metric: QualityMetric,
        metric_data: dict[str, Any],
        file_metrics: list[dict[QualityMetric, float]],
    ) -> list[QualityViolation]:
        """Check for metric violations"""
        violations = []

        if metric not in self.quality_thresholds:
            return violations

        thresholds = self.quality_thresholds[metric]
        current_value = metric_data["average"]

        # Determine current standard
        current_standard = self._determine_standard(current_value, thresholds)

        # Check if we're below acceptable threshold
        if current_standard in [QualityStandard.POOR, QualityStandard.CRITICAL]:
            violation = QualityViolation(
                metric=metric,
                standard=current_standard,
                file_path="",  # Global violation
                line_number=0,
                description=f"{metric.value} is {current_standard.value}",
                current_value=current_value,
                threshold=thresholds.get("acceptable", 0),
                severity=(
                    "high" if current_standard == QualityStandard.CRITICAL else "medium"
                ),
                recommendation=self._get_metric_recommendation(metric, current_value),
            )
            violations.append(violation)

        return violations

    def _determine_standard(
        self, value: float, thresholds: dict[str, float]
    ) -> QualityStandard:
        """Determine quality standard based on value and thresholds"""
        if value <= thresholds.get("excellent", float("inf")):
            return QualityStandard.EXCELLENT
        elif value <= thresholds.get("good", float("inf")):
            return QualityStandard.GOOD
        elif value <= thresholds.get("acceptable", float("inf")):
            return QualityStandard.ACCEPTABLE
        elif value <= thresholds.get("poor", float("inf")):
            return QualityStandard.POOR
        else:
            return QualityStandard.CRITICAL

    def _get_metric_recommendation(self, metric: QualityMetric, value: float) -> str:
        """Get recommendation for improving a metric"""
        recommendations = {
            QualityMetric.CYCLOMATIC_COMPLEXITY: "Refactor complex functions into smaller, simpler ones",
            QualityMetric.COGNITIVE_COMPLEXITY: "Simplify conditional logic and reduce nesting",
            QualityMetric.CODE_DUPLICATION: "Extract common code into reusable functions or classes",
            QualityMetric.TEST_COVERAGE: "Add more unit tests to increase coverage",
            QualityMetric.DOCUMENTATION_COVERAGE: "Add docstrings to functions and classes",
            QualityMetric.MAINTAINABILITY_INDEX: "Improve code structure and documentation",
            QualityMetric.CODE_SMELLS: "Refactor code to eliminate code smells",
        }

        return recommendations.get(metric, "Review and improve code quality")

    def _calculate_overall_quality_score(
        self,
        metrics_summary: dict[QualityMetric, dict[str, Any]],
        violations: list[QualityViolation],
    ) -> float:
        """Calculate overall quality score (0-100)"""
        if not metrics_summary:
            return 0.0

        # Weight different metrics
        weights = {
            QualityMetric.CYCLOMATIC_COMPLEXITY: 0.2,
            QualityMetric.COGNITIVE_COMPLEXITY: 0.15,
            QualityMetric.CODE_DUPLICATION: 0.15,
            QualityMetric.TEST_COVERAGE: 0.2,
            QualityMetric.DOCUMENTATION_COVERAGE: 0.1,
            QualityMetric.MAINTAINABILITY_INDEX: 0.15,
            QualityMetric.CODE_SMELLS: 0.05,
        }

        total_score = 0.0
        total_weight = 0.0

        for metric, data in metrics_summary.items():
            if metric in weights:
                # Normalize metric value to 0-100 scale
                normalized_score = self._normalize_metric_score(metric, data["average"])
                total_score += normalized_score * weights[metric]
                total_weight += weights[metric]

        # Penalize violations
        violation_penalty = min(len(violations) * 5, 30)  # Max 30 point penalty

        final_score = (
            (total_score / total_weight) - violation_penalty if total_weight > 0 else 0
        )
        return max(0.0, min(100.0, final_score))

    def _normalize_metric_score(self, metric: QualityMetric, value: float) -> float:
        """Normalize metric value to 0-100 score"""
        if metric in self.quality_thresholds:
            thresholds = self.quality_thresholds[metric]

            # For metrics where lower is better (complexity, duplication)
            if metric in [
                QualityMetric.CYCLOMATIC_COMPLEXITY,
                QualityMetric.COGNITIVE_COMPLEXITY,
                QualityMetric.CODE_DUPLICATION,
                QualityMetric.CODE_SMELLS,
            ]:
                if value <= thresholds.get("excellent", 0):
                    return 100.0
                elif value <= thresholds.get("good", 0):
                    return 80.0
                elif value <= thresholds.get("acceptable", 0):
                    return 60.0
                elif value <= thresholds.get("poor", 0):
                    return 40.0
                else:
                    return 20.0

            # For metrics where higher is better (coverage, maintainability)
            else:
                if value >= thresholds.get("excellent", 100):
                    return 100.0
                elif value >= thresholds.get("good", 80):
                    return 80.0
                elif value >= thresholds.get("acceptable", 60):
                    return 60.0
                elif value >= thresholds.get("poor", 40):
                    return 40.0
                else:
                    return 20.0

        return 50.0  # Default score

    def _generate_quality_recommendations(
        self,
        metrics_summary: dict[QualityMetric, dict[str, Any]],
        violations: list[QualityViolation],
    ) -> list[str]:
        """Generate quality improvement recommendations"""
        recommendations = []

        # Overall score recommendations
        overall_score = self._calculate_overall_quality_score(
            metrics_summary, violations
        )

        if overall_score >= 90:
            recommendations.append("🏆 Excellent code quality! Keep up the great work.")
        elif overall_score >= 80:
            recommendations.append(
                "👍 Good code quality. Address remaining issues for excellence."
            )
        elif overall_score >= 70:
            recommendations.append(
                "📋 Acceptable code quality. Focus on improving key metrics."
            )
        elif overall_score >= 60:
            recommendations.append(
                "⚠️ Code quality needs improvement. Prioritize critical issues."
            )
        else:
            recommendations.append("🚨 Poor code quality. Immediate action required.")

        # Metric-specific recommendations
        for metric, data in metrics_summary.items():
            if metric in self.quality_thresholds:
                current_value = data["average"]
                thresholds = self.quality_thresholds[metric]

                if current_value > thresholds.get("acceptable", 0):
                    recommendation = self._get_metric_recommendation(
                        metric, current_value
                    )
                    recommendations.append(f"🔧 {metric.value}: {recommendation}")

        # Violation-specific recommendations
        critical_violations = [v for v in violations if v.severity == "high"]
        if critical_violations:
            recommendations.append(
                f"🚨 {len(critical_violations)} critical quality violations need immediate attention."
            )

        return recommendations

    def _update_quality_trends(
        self, metrics_summary: dict[QualityMetric, dict[str, Any]], overall_score: float
    ):
        """Update quality trends for historical analysis"""
        time.time()

        # Update overall score trend
        if "overall_score" not in self.quality_history:
            self.quality_history["overall_score"] = []
        self.quality_history["overall_score"].append(overall_score)

        # Keep only last 30 measurements
        if len(self.quality_history["overall_score"]) > 30:
            self.quality_history["overall_score"] = self.quality_history[
                "overall_score"
            ][-30:]

        # Update metric trends
        for metric, data in metrics_summary.items():
            metric_key = f"{metric.value}_average"
            if metric_key not in self.quality_history:
                self.quality_history[metric_key] = []
            self.quality_history[metric_key].append(data["average"])

            # Keep only last 30 measurements
            if len(self.quality_history[metric_key]) > 30:
                self.quality_history[metric_key] = self.quality_history[metric_key][
                    -30:
                ]

        # Save to file
        history_file = self.repo_root / ".quality_history.json"
        try:
            with open(history_file, "w") as f:
                json.dump(self.quality_history, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving quality history: {e}")
