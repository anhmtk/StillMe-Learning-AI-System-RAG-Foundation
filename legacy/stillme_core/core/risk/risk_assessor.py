# stillme_core/risk/risk_assessor.py
"""
Technical risk assessment and management system
"""

from __future__ import annotations

import ast
import logging
import time
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class RiskLevel(Enum):
    """Risk severity levels"""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class RiskCategory(Enum):
    """Risk categories"""

    SECURITY = "security"
    PERFORMANCE = "performance"
    MAINTAINABILITY = "maintainability"
    RELIABILITY = "reliability"
    SCALABILITY = "scalability"
    COMPLIANCE = "compliance"


@dataclass
class RiskFactor:
    """Individual risk factor"""

    category: RiskCategory
    level: RiskLevel
    description: str
    file_path: str
    line_number: int
    code_snippet: str
    impact: str
    probability: float
    mitigation: str
    cost_estimate: str | None = None


@dataclass
class RiskAssessment:
    """Comprehensive risk assessment"""

    total_risks: int
    risks_by_level: dict[RiskLevel, int]
    risks_by_category: dict[RiskCategory, int]
    risk_factors: list[RiskFactor]
    overall_risk_score: float
    recommendations: list[str]
    assessment_duration: float


class RiskAssessor:
    """
    Comprehensive technical risk assessment system
    """

    def __init__(self, repo_root: str = "."):
        self.repo_root = Path(repo_root)
        self.risk_patterns = self._load_risk_patterns()
        self.complexity_thresholds = self._load_complexity_thresholds()

    def _load_risk_patterns(self) -> dict[RiskCategory, list[dict[str, Any]]]:
        """Load risk detection patterns"""
        return {
            RiskCategory.SECURITY: [
                {
                    "pattern": r"(?i)(password|secret|key|token)\s*[=:]\s*['\"][^'\"]+['\"]",
                    "level": RiskLevel.HIGH,
                    "description": "Hardcoded credentials",
                    "impact": "Security breach risk",
                    "probability": 0.8,
                    "mitigation": "Use environment variables or secure secret management",
                },
                {
                    "pattern": r"(?i)(eval|exec|compile)\s*\(",
                    "level": RiskLevel.CRITICAL,
                    "description": "Code execution vulnerability",
                    "impact": "Remote code execution",
                    "probability": 0.9,
                    "mitigation": "Avoid dynamic code execution",
                },
                {
                    "pattern": r"(?i)(sql|query)\s*[=:]\s*['\"].*\+.*['\"]",
                    "level": RiskLevel.HIGH,
                    "description": "Potential SQL injection",
                    "impact": "Data breach",
                    "probability": 0.7,
                    "mitigation": "Use parameterized queries",
                },
            ],
            RiskCategory.PERFORMANCE: [
                {
                    "pattern": r"(?i)(for|while)\s+.*:\s*.*\.append\(",
                    "level": RiskLevel.MEDIUM,
                    "description": "Inefficient list operations",
                    "impact": "Performance degradation",
                    "probability": 0.6,
                    "mitigation": "Use list comprehensions or generators",
                },
                {
                    "pattern": r"(?i)(time\.sleep|time\.wait)\s*\(",
                    "level": RiskLevel.MEDIUM,
                    "description": "Blocking operations",
                    "impact": "Poor user experience",
                    "probability": 0.5,
                    "mitigation": "Use async/await or threading",
                },
                {
                    "pattern": r"(?i)(select\s+\*|SELECT\s+\*)",
                    "level": RiskLevel.MEDIUM,
                    "description": "Inefficient database queries",
                    "impact": "Database performance issues",
                    "probability": 0.6,
                    "mitigation": "Select only required columns",
                },
            ],
            RiskCategory.MAINTAINABILITY: [
                {
                    "pattern": r"(?i)(TODO|FIXME|HACK|XXX)",
                    "level": RiskLevel.LOW,
                    "description": "Technical debt markers",
                    "impact": "Code maintenance issues",
                    "probability": 0.3,
                    "mitigation": "Address technical debt items",
                },
                {
                    "pattern": r"(?i)(import\s+\*|from\s+.*\s+import\s+\*)",
                    "level": RiskLevel.MEDIUM,
                    "description": "Wildcard imports",
                    "impact": "Namespace pollution",
                    "probability": 0.4,
                    "mitigation": "Use specific imports",
                },
                {
                    "pattern": r"(?i)(global\s+\w+)",
                    "level": RiskLevel.MEDIUM,
                    "description": "Global variables",
                    "impact": "Code coupling and testing issues",
                    "probability": 0.5,
                    "mitigation": "Use dependency injection",
                },
            ],
            RiskCategory.RELIABILITY: [
                {
                    "pattern": r"(?i)(except\s*:|\s+except\s+Exception\s*:)",
                    "level": RiskLevel.MEDIUM,
                    "description": "Broad exception handling",
                    "impact": "Hidden errors and debugging issues",
                    "probability": 0.6,
                    "mitigation": "Use specific exception types",
                },
                {
                    "pattern": r"(?i)(assert\s+\w+)",
                    "level": RiskLevel.LOW,
                    "description": "Production assertions",
                    "impact": "Application crashes in production",
                    "probability": 0.3,
                    "mitigation": "Use proper error handling",
                },
                {
                    "pattern": r"(?i)(None\s*==|\s*==\s*None)",
                    "level": RiskLevel.LOW,
                    "description": "Incorrect None comparison",
                    "impact": "Potential runtime errors",
                    "probability": 0.2,
                    "mitigation": "Use 'is None' or 'is not None'",
                },
            ],
            RiskCategory.SCALABILITY: [
                {
                    "pattern": r"(?i)(\.append\s*\(.*\)\s*for\s+.*\s+in\s+.*)",
                    "level": RiskLevel.MEDIUM,
                    "description": "Memory-intensive operations",
                    "impact": "Memory usage issues at scale",
                    "probability": 0.5,
                    "mitigation": "Use generators or streaming",
                },
                {
                    "pattern": r"(?i)(synchronous\s+requests|requests\.get|requests\.post)",
                    "level": RiskLevel.MEDIUM,
                    "description": "Synchronous I/O operations",
                    "impact": "Poor scalability",
                    "probability": 0.6,
                    "mitigation": "Use async I/O operations",
                },
            ],
            RiskCategory.COMPLIANCE: [
                {
                    "pattern": r"(?i)(print\s*\(.*\)|console\.log)",
                    "level": RiskLevel.LOW,
                    "description": "Debug statements in production code",
                    "impact": "Information disclosure",
                    "probability": 0.2,
                    "mitigation": "Use proper logging framework",
                },
                {
                    "pattern": r"(?i)(localhost|127\.0\.0\.1|0\.0\.0\.0)",
                    "level": RiskLevel.MEDIUM,
                    "description": "Hardcoded local addresses",
                    "impact": "Deployment and security issues",
                    "probability": 0.4,
                    "mitigation": "Use configuration management",
                },
            ],
        }

    def _load_complexity_thresholds(self) -> dict[str, int]:
        """Load complexity thresholds for risk assessment"""
        return {
            "cyclomatic_complexity": 10,
            "cognitive_complexity": 15,
            "function_length": 50,
            "class_length": 200,
            "parameter_count": 5,
            "nesting_depth": 4,
        }

    def assess_repository_risks(self) -> RiskAssessment:
        """Perform comprehensive risk assessment"""
        start_time = time.time()
        risk_factors = []

        # Analyze all Python files
        for py_file in self.repo_root.rglob("*.py"):
            if self._should_analyze_file(py_file):
                file_risks = self._analyze_file_risks(py_file)
                risk_factors.extend(file_risks)

        # Analyze dependencies
        dependency_risks = self._analyze_dependency_risks()
        risk_factors.extend(dependency_risks)

        # Analyze architecture risks
        architecture_risks = self._analyze_architecture_risks()
        risk_factors.extend(architecture_risks)

        assessment_duration = time.time() - start_time

        return self._generate_risk_report(risk_factors, assessment_duration)

    def _should_analyze_file(self, file_path: Path) -> bool:
        """Determine if file should be analyzed"""
        # Skip test files, virtual environments, and build directories
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

    def _analyze_file_risks(self, file_path: Path) -> list[RiskFactor]:
        """Analyze risks in a single file"""
        risk_factors = []

        try:
            with open(file_path, encoding="utf-8") as f:
                content = f.read()

            lines = content.splitlines()

            # Pattern-based analysis
            for category, patterns in self.risk_patterns.items():
                for pattern_info in patterns:
                    import re

                    matches = re.finditer(pattern_info["pattern"], content)

                    for match in matches:
                        line_number = content[: match.start()].count("\n") + 1
                        code_snippet = (
                            lines[line_number - 1] if line_number <= len(lines) else ""
                        )

                        risk_factor = RiskFactor(
                            category=category,
                            level=pattern_info["level"],
                            description=pattern_info["description"],
                            file_path=str(file_path),
                            line_number=line_number,
                            code_snippet=code_snippet.strip(),
                            impact=pattern_info["impact"],
                            probability=pattern_info["probability"],
                            mitigation=pattern_info["mitigation"],
                        )
                        risk_factors.append(risk_factor)

            # AST-based analysis
            try:
                tree = ast.parse(content)
                ast_risks = self._analyze_ast_risks(tree, file_path)
                risk_factors.extend(ast_risks)
            except SyntaxError:
                # File has syntax errors - this is a risk itself
                risk_factor = RiskFactor(
                    category=RiskCategory.RELIABILITY,
                    level=RiskLevel.HIGH,
                    description="Syntax errors in code",
                    file_path=str(file_path),
                    line_number=0,
                    code_snippet="",
                    impact="Code cannot be executed",
                    probability=1.0,
                    mitigation="Fix syntax errors",
                )
                risk_factors.append(risk_factor)

        except Exception as e:
            logger.error(f"Error analyzing file {file_path}: {e}")

        return risk_factors

    def _analyze_ast_risks(self, tree: ast.AST, file_path: Path) -> list[RiskFactor]:
        """Analyze risks using AST"""

        class RiskVisitor(ast.NodeVisitor):
            def __init__(self, file_path: Path, complexity_thresholds: dict[str, int]):
                self.file_path = file_path
                self.risks = []
                self.complexity_thresholds = complexity_thresholds

            def visit_FunctionDef(self, node: ast.FunctionDef):
                # Check function complexity
                complexity = self._calculate_cyclomatic_complexity(node)
                if complexity > self.complexity_thresholds["cyclomatic_complexity"]:
                    risk = RiskFactor(
                        category=RiskCategory.MAINTAINABILITY,
                        level=RiskLevel.MEDIUM,
                        description=f"High cyclomatic complexity ({complexity})",
                        file_path=str(self.file_path),
                        line_number=node.lineno,
                        code_snippet=node.name,
                        impact="Difficult to test and maintain",
                        probability=0.7,
                        mitigation="Refactor into smaller functions",
                    )
                    self.risks.append(risk)

                # Check parameter count
                if len(node.args.args) > self.complexity_thresholds["parameter_count"]:
                    risk = RiskFactor(
                        category=RiskCategory.MAINTAINABILITY,
                        level=RiskLevel.LOW,
                        description=f"Too many parameters ({len(node.args.args)})",
                        file_path=str(self.file_path),
                        line_number=node.lineno,
                        code_snippet=node.name,
                        impact="Function is hard to use and maintain",
                        probability=0.5,
                        mitigation="Use data classes or configuration objects",
                    )
                    self.risks.append(risk)

                self.generic_visit(node)

            def visit_ClassDef(self, node: ast.ClassDef):
                # Check class length
                if len(node.body) > self.complexity_thresholds["class_length"]:
                    risk = RiskFactor(
                        category=RiskCategory.MAINTAINABILITY,
                        level=RiskLevel.MEDIUM,
                        description=f"Large class ({len(node.body)} methods/properties)",
                        file_path=str(self.file_path),
                        line_number=node.lineno,
                        code_snippet=node.name,
                        impact="Violates Single Responsibility Principle",
                        probability=0.6,
                        mitigation="Split into smaller classes",
                    )
                    self.risks.append(risk)

                self.generic_visit(node)

            def visit_ExceptHandler(self, node: ast.ExceptHandler):
                # Check for bare except
                if node.type is None:
                    risk = RiskFactor(
                        category=RiskCategory.RELIABILITY,
                        level=RiskLevel.MEDIUM,
                        description="Bare except clause",
                        file_path=str(self.file_path),
                        line_number=node.lineno,
                        code_snippet="except:",
                        impact="Catches all exceptions, including system exits",
                        probability=0.8,
                        mitigation="Use specific exception types",
                    )
                    self.risks.append(risk)

                self.generic_visit(node)

            def _calculate_cyclomatic_complexity(self, node: ast.AST) -> int:
                """Calculate cyclomatic complexity"""
                complexity = 1  # Base complexity

                for child in ast.walk(node):
                    if (
                        isinstance(child, ast.If | ast.While | ast.For | ast.AsyncFor)
                        or isinstance(child, ast.ExceptHandler)
                        or isinstance(child, ast.And | ast.Or)
                    ):
                        complexity += 1

                return complexity

        visitor = RiskVisitor(file_path, self.complexity_thresholds)
        visitor.visit(tree)
        return visitor.risks

    def _analyze_dependency_risks(self) -> list[RiskFactor]:
        """Analyze dependency-related risks"""
        risk_factors = []

        # Check requirements.txt
        requirements_file = self.repo_root / "requirements.txt"
        if requirements_file.exists():
            try:
                with open(requirements_file) as f:
                    requirements = f.read()

                # Check for pinned versions
                if "==" not in requirements and "~=" not in requirements:
                    risk = RiskFactor(
                        category=RiskCategory.RELIABILITY,
                        level=RiskLevel.MEDIUM,
                        description="Unpinned dependencies",
                        file_path=str(requirements_file),
                        line_number=0,
                        code_snippet="",
                        impact="Non-deterministic builds",
                        probability=0.6,
                        mitigation="Pin dependency versions",
                    )
                    risk_factors.append(risk)

                # Check for outdated packages
                outdated_packages = self._check_outdated_packages(requirements)
                for package in outdated_packages:
                    risk = RiskFactor(
                        category=RiskCategory.SECURITY,
                        level=RiskLevel.MEDIUM,
                        description=f"Outdated package: {package}",
                        file_path=str(requirements_file),
                        line_number=0,
                        code_snippet=package,
                        impact="Security vulnerabilities",
                        probability=0.5,
                        mitigation="Update to latest version",
                    )
                    risk_factors.append(risk)

            except Exception as e:
                logger.error(f"Error analyzing dependencies: {e}")

        return risk_factors

    def _check_outdated_packages(self, requirements: str) -> list[str]:
        """Check for outdated packages (simplified)"""
        # This is a simplified check - in practice, you'd use pip-tools or similar
        outdated_indicators = ["django<3.0", "flask<2.0", "requests<2.25", "numpy<1.20"]

        outdated = []
        for indicator in outdated_indicators:
            if indicator in requirements:
                outdated.append(indicator)

        return outdated

    def _analyze_architecture_risks(self) -> list[RiskFactor]:
        """Analyze architecture-related risks"""
        risk_factors = []

        # Check for circular imports
        circular_imports = self._detect_circular_imports()
        for import_cycle in circular_imports:
            risk = RiskFactor(
                category=RiskCategory.MAINTAINABILITY,
                level=RiskLevel.HIGH,
                description=f"Circular import: {' -> '.join(import_cycle)}",
                file_path="",
                line_number=0,
                code_snippet="",
                impact="Code coupling and import issues",
                probability=0.8,
                mitigation="Refactor to remove circular dependencies",
            )
            risk_factors.append(risk)

        # Check for large files
        large_files = self._find_large_files()
        for file_path, line_count in large_files:
            risk = RiskFactor(
                category=RiskCategory.MAINTAINABILITY,
                level=RiskLevel.MEDIUM,
                description=f"Large file ({line_count} lines)",
                file_path=file_path,
                line_number=0,
                code_snippet="",
                impact="Difficult to maintain and understand",
                probability=0.6,
                mitigation="Split into smaller modules",
            )
            risk_factors.append(risk)

        return risk_factors

    def _detect_circular_imports(self) -> list[list[str]]:
        """Detect circular imports (simplified)"""
        # This is a simplified implementation
        # In practice, you'd use more sophisticated analysis
        return []

    def _find_large_files(self) -> list[tuple[str, int]]:
        """Find files with excessive line counts"""
        large_files = []
        max_lines = 500  # Threshold for large files

        for py_file in self.repo_root.rglob("*.py"):
            if self._should_analyze_file(py_file):
                try:
                    with open(py_file, encoding="utf-8") as f:
                        lines = f.readlines()

                    if len(lines) > max_lines:
                        large_files.append((str(py_file), len(lines)))

                except Exception:
                    continue

        return large_files

    def _generate_risk_report(
        self, risk_factors: list[RiskFactor], duration: float
    ) -> RiskAssessment:
        """Generate comprehensive risk report"""
        # Count risks by level
        risks_by_level = dict.fromkeys(RiskLevel, 0)
        for risk in risk_factors:
            risks_by_level[risk.level] += 1

        # Count risks by category
        risks_by_category = dict.fromkeys(RiskCategory, 0)
        for risk in risk_factors:
            risks_by_category[risk.category] += 1

        # Calculate overall risk score
        risk_score = self._calculate_overall_risk_score(risk_factors)

        # Generate recommendations
        recommendations = self._generate_risk_recommendations(
            risk_factors, risks_by_level
        )

        return RiskAssessment(
            total_risks=len(risk_factors),
            risks_by_level=risks_by_level,
            risks_by_category=risks_by_category,
            risk_factors=risk_factors,
            overall_risk_score=risk_score,
            recommendations=recommendations,
            assessment_duration=duration,
        )

    def _calculate_overall_risk_score(self, risk_factors: list[RiskFactor]) -> float:
        """Calculate overall risk score (0-100)"""
        if not risk_factors:
            return 0.0

        # Weight by severity and probability
        weights = {
            RiskLevel.CRITICAL: 10,
            RiskLevel.HIGH: 7,
            RiskLevel.MEDIUM: 4,
            RiskLevel.LOW: 2,
            RiskLevel.INFO: 1,
        }

        total_weighted_score = 0
        for risk in risk_factors:
            weight = weights[risk.level]
            total_weighted_score += weight * risk.probability

        max_possible_score = (
            len(risk_factors) * 10
        )  # All critical with 100% probability

        return min(100.0, (total_weighted_score / max_possible_score) * 100)

    def _generate_risk_recommendations(
        self, risk_factors: list[RiskFactor], risks_by_level: dict[RiskLevel, int]
    ) -> list[str]:
        """Generate risk mitigation recommendations"""
        recommendations = []

        # Critical risks
        if risks_by_level[RiskLevel.CRITICAL] > 0:
            recommendations.append(
                f"🚨 CRITICAL: {risks_by_level[RiskLevel.CRITICAL]} critical risks found. "
                "Address immediately."
            )

        # High risks
        if risks_by_level[RiskLevel.HIGH] > 0:
            recommendations.append(
                f"⚠️ HIGH: {risks_by_level[RiskLevel.HIGH]} high-risk issues found. "
                "Prioritize for next sprint."
            )

        # Category-specific recommendations
        category_counts = {}
        for risk in risk_factors:
            category_counts[risk.category] = category_counts.get(risk.category, 0) + 1

        for category, count in category_counts.items():
            if count > 0:
                if category == RiskCategory.SECURITY:
                    recommendations.append(
                        f"🔐 SECURITY: {count} security risks found. "
                        "Implement security best practices."
                    )
                elif category == RiskCategory.PERFORMANCE:
                    recommendations.append(
                        f"⚡ PERFORMANCE: {count} performance risks found. "
                        "Consider performance optimization."
                    )
                elif category == RiskCategory.MAINTAINABILITY:
                    recommendations.append(
                        f"🔧 MAINTAINABILITY: {count} maintainability issues found. "
                        "Focus on code quality improvements."
                    )
                elif category == RiskCategory.RELIABILITY:
                    recommendations.append(
                        f"🛡️ RELIABILITY: {count} reliability risks found. "
                        "Improve error handling and testing."
                    )

        # General recommendations
        if len(risk_factors) == 0:
            recommendations.append(
                "✅ No significant risks detected. Keep up the good work!"
            )
        elif len(risk_factors) < 10:
            recommendations.append("👍 Good risk profile. Address remaining issues.")
        else:
            recommendations.append(
                "📈 Consider implementing risk management practices."
            )

        return recommendations
