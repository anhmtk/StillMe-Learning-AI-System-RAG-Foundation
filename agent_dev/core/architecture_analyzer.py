#!/usr/bin/env python3
"""
Architecture Analyzer - Architecture Analysis & Design Pattern Recognition
Phân tích kiến trúc và nhận dạng design patterns cho AgentDev Unified

Tính năng:
1. Architecture Analysis - Phân tích kiến trúc (dependency graph, coupling metrics)
2. Design Pattern Recognition - Nhận dạng design patterns (factory, singleton, observer)
3. Refactoring Suggestions - Đề xuất refactoring (report trong docs/refactor/)
4. Code Structure Analysis - Phân tích cấu trúc code
5. Technical Debt Assessment - Đánh giá technical debt
"""

import ast
import json
import re
import time
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

import networkx as nx


class DesignPattern(Enum):
    """Design Patterns"""

    SINGLETON = "singleton"
    FACTORY = "factory"
    OBSERVER = "observer"
    STRATEGY = "strategy"
    DECORATOR = "decorator"
    ADAPTER = "adapter"
    FACADE = "facade"
    PROXY = "proxy"
    COMMAND = "command"
    STATE = "state"


class CouplingLevel(Enum):
    """Coupling Levels"""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    VERY_HIGH = "very_high"


class ComplexityLevel(Enum):
    """Complexity Levels"""

    SIMPLE = "simple"
    MODERATE = "moderate"
    COMPLEX = "complex"
    VERY_COMPLEX = "very_complex"


@dataclass
class DependencyInfo:
    """Dependency Information"""

    source: str
    target: str
    dependency_type: str  # "import", "inheritance", "composition"
    line_number: int
    strength: float  # 0.0 to 1.0


@dataclass
class DesignPatternMatch:
    """Design Pattern Match"""

    pattern: DesignPattern
    file_path: str
    line_number: int
    confidence: float
    description: str
    code_snippet: str


@dataclass
class RefactoringSuggestion:
    """Refactoring Suggestion"""

    suggestion_id: str
    file_path: str
    line_number: int
    suggestion_type: str
    description: str
    priority: str  # "low", "medium", "high", "critical"
    impact: str  # "low", "medium", "high"
    effort: str  # "low", "medium", "high"
    code_before: str
    code_after: str
    benefits: list[str]


@dataclass
class TechnicalDebtItem:
    """Technical Debt Item"""

    debt_id: str
    file_path: str
    line_number: int
    debt_type: str
    description: str
    severity: str  # "low", "medium", "high", "critical"
    estimated_cost: float
    impact: str
    suggested_fix: str


@dataclass
class ArchitectureMetrics:
    """Architecture Metrics"""

    total_files: int
    total_classes: int
    total_functions: int
    total_lines: int
    cyclomatic_complexity: float
    coupling_metrics: dict[str, float]
    cohesion_metrics: dict[str, float]
    design_patterns_found: list[DesignPatternMatch]
    refactoring_suggestions: list[RefactoringSuggestion]
    technical_debt: list[TechnicalDebtItem]


@dataclass
class ArchitectureReport:
    """Architecture Report"""

    analysis_timestamp: datetime
    metrics: ArchitectureMetrics
    dependency_graph: dict[str, dict[str, dict[str, Any]]]
    coupling_analysis: dict[str, CouplingLevel]
    complexity_analysis: dict[str, ComplexityLevel]
    recommendations: list[str]
    analysis_time: float


class ArchitectureAnalyzer:
    """Architecture Analyzer - Phân tích kiến trúc toàn diện"""

    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.refactor_dir = self.project_root / "docs" / "refactor"
        self.analysis_dir = self.project_root / "analysis"

        # Tạo thư mục cần thiết
        self._ensure_directories()

        # Analysis data
        self.dependency_graph: nx.DiGraph[str] = nx.DiGraph()
        self.dependencies: list[DependencyInfo] = []
        self.design_patterns: list[DesignPatternMatch] = []
        self.refactoring_suggestions: list[RefactoringSuggestion] = []
        self.technical_debt: list[TechnicalDebtItem] = []

        # Pattern recognition rules
        self.pattern_rules = self._load_pattern_rules()

    def _ensure_directories(self):
        """Đảm bảo thư mục cần thiết tồn tại"""
        for dir_path in [self.refactor_dir, self.analysis_dir]:
            dir_path.mkdir(parents=True, exist_ok=True)

    def _load_pattern_rules(self) -> dict[DesignPattern, dict[str, Any]]:
        """Load design pattern recognition rules"""
        return {
            DesignPattern.SINGLETON: {
                "patterns": [
                    r"class\s+\w+.*:\s*\n.*__instance\s*=.*None",
                    r"def\s+__new__\s*\(.*cls.*\):",
                    r"if\s+.*__instance\s+is\s+None:",
                    r"__instance\s*=\s*.*\(\)",
                ],
                "confidence_threshold": 0.7,
            },
            DesignPattern.FACTORY: {
                "patterns": [
                    r"class\s+\w*Factory\w*.*:",
                    r"def\s+create_\w+\s*\(",
                    r"def\s+get_\w+\s*\(",
                    r"return\s+\w+\(.*\)",
                ],
                "confidence_threshold": 0.6,
            },
            DesignPattern.OBSERVER: {
                "patterns": [
                    r"def\s+attach\s*\(",
                    r"def\s+detach\s*\(",
                    r"def\s+notify\s*\(",
                    r"observers\s*=\s*\[\]",
                    r"for\s+observer\s+in\s+.*observers",
                ],
                "confidence_threshold": 0.6,
            },
            DesignPattern.STRATEGY: {
                "patterns": [
                    r"class\s+\w*Strategy\w*.*:",
                    r"def\s+execute\s*\(",
                    r"def\s+algorithm\s*\(",
                    r"strategy\s*=\s*\w+",
                ],
                "confidence_threshold": 0.6,
            },
            DesignPattern.DECORATOR: {
                "patterns": [
                    r"def\s+\w*decorator\w*\s*\(",
                    r"@\w+",
                    r"def\s+wrapper\s*\(",
                    r"return\s+wrapper",
                ],
                "confidence_threshold": 0.7,
            },
        }

    def analyze_architecture(self) -> ArchitectureReport:
        """Analyze project architecture"""
        start_time = time.time()

        # Scan all Python files
        python_files = list(self.project_root.rglob("*.py"))

        # Filter out test files and __pycache__ (but allow test files in temp projects)
        python_files = [
            f
            for f in python_files
            if "__pycache__" not in str(f)
            and not (str(f).endswith("test_") and "temp" not in str(f))
        ]

        # Analyze each file
        for file_path in python_files:
            self._analyze_file(file_path)

        # Build dependency graph
        self._build_dependency_graph()

        # Calculate metrics
        metrics = self._calculate_metrics(python_files)

        # Analyze coupling and complexity
        coupling_analysis = self._analyze_coupling()
        complexity_analysis = self._analyze_complexity()

        # Generate recommendations
        recommendations = self._generate_recommendations(
            metrics, coupling_analysis, complexity_analysis
        )

        analysis_time = time.time() - start_time

        return ArchitectureReport(
            analysis_timestamp=datetime.now(),
            metrics=metrics,
            dependency_graph=dict(self.dependency_graph.adjacency()),
            coupling_analysis=coupling_analysis,
            complexity_analysis=complexity_analysis,
            recommendations=recommendations,
            analysis_time=analysis_time,
        )

    def _analyze_file(self, file_path: Path):
        """Analyze individual file"""
        try:
            with open(file_path, encoding="utf-8") as f:
                content = f.read()

            # Parse AST
            tree = ast.parse(content)

            # Extract dependencies
            self._extract_dependencies(file_path, tree)

            # Detect design patterns
            self._detect_design_patterns(file_path, content)

            # Identify refactoring opportunities
            self._identify_refactoring_opportunities(file_path, tree, content)

            # Identify technical debt
            self._identify_technical_debt(file_path, tree, content)

        except Exception as e:
            print(f"Error analyzing {file_path}: {e}")

    def _extract_dependencies(self, file_path: Path, tree: ast.AST):
        """Extract dependencies from AST"""
        file_name = str(file_path.relative_to(self.project_root))

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    dep = DependencyInfo(
                        source=file_name,
                        target=alias.name,
                        dependency_type="import",
                        line_number=node.lineno,
                        strength=1.0,
                    )
                    self.dependencies.append(dep)
                    self.dependency_graph.add_edge(file_name, alias.name)

            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    dep = DependencyInfo(
                        source=file_name,
                        target=node.module,
                        dependency_type="import",
                        line_number=node.lineno,
                        strength=1.0,
                    )
                    self.dependencies.append(dep)
                    self.dependency_graph.add_edge(file_name, node.module)

            elif isinstance(node, ast.ClassDef):
                # Check for inheritance
                for base in node.bases:
                    if isinstance(base, ast.Name):
                        dep = DependencyInfo(
                            source=file_name,
                            target=base.id,
                            dependency_type="inheritance",
                            line_number=node.lineno,
                            strength=0.8,
                        )
                        self.dependencies.append(dep)
                        self.dependency_graph.add_edge(file_name, base.id)

    def _detect_design_patterns(self, file_path: Path, content: str):
        """Detect design patterns in code"""
        lines = content.split("\n")

        for pattern_type, rules in self.pattern_rules.items():
            matches = 0
            total_patterns = len(rules["patterns"])

            for pattern in rules["patterns"]:
                if re.search(pattern, content, re.MULTILINE | re.DOTALL):
                    matches += 1

            confidence = matches / total_patterns if total_patterns > 0 else 0

            if confidence >= rules["confidence_threshold"]:
                # Find line number for the pattern
                line_number = 1
                for i, line in enumerate(lines):
                    if re.search(rules["patterns"][0], line):
                        line_number = i + 1
                        break

                pattern_match = DesignPatternMatch(
                    pattern=pattern_type,
                    file_path=str(file_path.relative_to(self.project_root)),
                    line_number=line_number,
                    confidence=confidence,
                    description=f"{pattern_type.value.title()} pattern detected",
                    code_snippet=lines[line_number - 1]
                    if line_number <= len(lines)
                    else "",
                )

                self.design_patterns.append(pattern_match)

    def _identify_refactoring_opportunities(
        self, file_path: Path, tree: ast.AST, content: str
    ):
        """Identify refactoring opportunities"""
        lines = content.split("\n")

        # Check for long functions
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                if len(node.body) > 20:  # Long function
                    suggestion = RefactoringSuggestion(
                        suggestion_id=f"long_function_{file_path.stem}_{node.lineno}",
                        file_path=str(file_path.relative_to(self.project_root)),
                        line_number=node.lineno,
                        suggestion_type="extract_method",
                        description=f"Function '{node.name}' is too long ({len(node.body)} lines)",
                        priority="medium",
                        impact="medium",
                        effort="medium",
                        code_before=lines[node.lineno - 1]
                        if node.lineno <= len(lines)
                        else "",
                        code_after="# Extract smaller methods from this function",
                        benefits=[
                            "Improved readability",
                            "Better testability",
                            "Reduced complexity",
                        ],
                    )
                    self.refactoring_suggestions.append(suggestion)

                # Check for complex conditions
                if self._has_complex_conditions(node):
                    suggestion = RefactoringSuggestion(
                        suggestion_id=f"complex_condition_{file_path.stem}_{node.lineno}",
                        file_path=str(file_path.relative_to(self.project_root)),
                        line_number=node.lineno,
                        suggestion_type="simplify_condition",
                        description=f"Function '{node.name}' has complex conditions",
                        priority="low",
                        impact="low",
                        effort="low",
                        code_before=lines[node.lineno - 1]
                        if node.lineno <= len(lines)
                        else "",
                        code_after="# Simplify complex conditions",
                        benefits=["Improved readability", "Easier maintenance"],
                    )
                    self.refactoring_suggestions.append(suggestion)

        # Check for duplicate code
        self._detect_duplicate_code(file_path, content)

    def _has_complex_conditions(self, node: ast.FunctionDef) -> bool:
        """Check if function has complex conditions"""
        for child in ast.walk(node):
            if isinstance(child, ast.If):
                # Count boolean operators in condition
                condition_complexity = 0
                for condition_node in ast.walk(child.test):
                    if isinstance(condition_node, ast.And | ast.Or):
                        condition_complexity += 1

                if condition_complexity > 2:
                    return True

        return False

    def _detect_duplicate_code(self, file_path: Path, content: str):
        """Detect duplicate code patterns"""
        lines = content.split("\n")

        # Simple duplicate detection (can be enhanced)
        line_counts = Counter(lines)
        duplicates = [
            (line, count)
            for line, count in line_counts.items()
            if count > 3 and line.strip() and not line.strip().startswith("#")
        ]

        for line, count in duplicates:
            line_number = lines.index(line) + 1
            suggestion = RefactoringSuggestion(
                suggestion_id=f"duplicate_code_{file_path.stem}_{line_number}",
                file_path=str(file_path.relative_to(self.project_root)),
                line_number=line_number,
                suggestion_type="extract_common_code",
                description=f"Duplicate code detected (appears {count} times)",
                priority="low",
                impact="low",
                effort="low",
                code_before=line,
                code_after="# Extract to common function or constant",
                benefits=["Reduced duplication", "Easier maintenance"],
            )
            self.refactoring_suggestions.append(suggestion)

    def _identify_technical_debt(self, file_path: Path, tree: ast.AST, content: str):
        """Identify technical debt"""
        lines = content.split("\n")

        # Check for TODO comments
        for i, line in enumerate(lines):
            if "TODO" in line.upper() or "FIXME" in line.upper():
                debt = TechnicalDebtItem(
                    debt_id=f"todo_{file_path.stem}_{i+1}",
                    file_path=str(file_path.relative_to(self.project_root)),
                    line_number=i + 1,
                    debt_type="todo_comment",
                    description=f"TODO/FIXME comment: {line.strip()}",
                    severity="low",
                    estimated_cost=1.0,
                    impact="low",
                    suggested_fix="Implement the TODO item or remove if obsolete",
                )
                self.technical_debt.append(debt)

        # Check for long parameter lists
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                if len(node.args.args) > 5:  # Too many parameters
                    debt = TechnicalDebtItem(
                        debt_id=f"long_params_{file_path.stem}_{node.lineno}",
                        file_path=str(file_path.relative_to(self.project_root)),
                        line_number=node.lineno,
                        debt_type="long_parameter_list",
                        description=f"Function '{node.name}' has too many parameters ({len(node.args.args)})",
                        severity="medium",
                        estimated_cost=2.0,
                        impact="medium",
                        suggested_fix="Use data classes or configuration objects",
                    )
                    self.technical_debt.append(debt)

        # Check for deep nesting
        max_depth = self._calculate_nesting_depth(tree)
        if max_depth > 4:
            debt = TechnicalDebtItem(
                debt_id=f"deep_nesting_{file_path.stem}",
                file_path=str(file_path.relative_to(self.project_root)),
                line_number=1,
                debt_type="deep_nesting",
                description=f"Code has deep nesting (depth: {max_depth})",
                severity="medium",
                estimated_cost=3.0,
                impact="medium",
                suggested_fix="Extract methods to reduce nesting",
            )
            self.technical_debt.append(debt)

    def _calculate_nesting_depth(self, tree: ast.AST) -> int:
        """Calculate maximum nesting depth"""
        max_depth = 0

        def visit_node(node: ast.AST, depth: int) -> None:
            nonlocal max_depth
            max_depth = max(max_depth, depth)

            for child in ast.iter_child_nodes(node):
                if isinstance(child, ast.If | ast.For | ast.While | ast.With | ast.Try):
                    visit_node(child, depth + 1)
                else:
                    visit_node(child, depth)

        visit_node(tree, 0)
        return max_depth

    def _build_dependency_graph(self):
        """Build dependency graph"""
        for dep in self.dependencies:
            self.dependency_graph.add_edge(dep.source, dep.target, weight=dep.strength)

    def _calculate_metrics(self, python_files: list[Path]) -> ArchitectureMetrics:
        """Calculate architecture metrics"""
        total_files = len(python_files)
        total_classes = 0
        total_functions = 0
        total_lines = 0

        for file_path in python_files:
            try:
                with open(file_path, encoding="utf-8") as f:
                    content = f.read()

                tree = ast.parse(content)
                total_lines += len(content.split("\n"))

                for node in ast.walk(tree):
                    if isinstance(node, ast.ClassDef):
                        total_classes += 1
                    elif isinstance(node, ast.FunctionDef):
                        total_functions += 1

            except Exception:
                continue

        # Calculate cyclomatic complexity (simplified)
        cyclomatic_complexity = self._calculate_cyclomatic_complexity(python_files)

        # Calculate coupling metrics
        coupling_metrics = self._calculate_coupling_metrics()

        # Calculate cohesion metrics
        cohesion_metrics = self._calculate_cohesion_metrics()

        return ArchitectureMetrics(
            total_files=total_files,
            total_classes=total_classes,
            total_functions=total_functions,
            total_lines=total_lines,
            cyclomatic_complexity=cyclomatic_complexity,
            coupling_metrics=coupling_metrics,
            cohesion_metrics=cohesion_metrics,
            design_patterns_found=self.design_patterns,
            refactoring_suggestions=self.refactoring_suggestions,
            technical_debt=self.technical_debt,
        )

    def _calculate_cyclomatic_complexity(self, python_files: list[Path]) -> float:
        """Calculate cyclomatic complexity"""
        total_complexity = 0
        total_functions = 0

        for file_path in python_files:
            try:
                with open(file_path, encoding="utf-8") as f:
                    content = f.read()

                tree = ast.parse(content)

                for node in ast.walk(tree):
                    if isinstance(node, ast.FunctionDef):
                        complexity = 1  # Base complexity

                        for child in ast.walk(node):
                            if isinstance(
                                child, ast.If | ast.While | ast.For | ast.ExceptHandler
                            ):
                                complexity += 1
                            elif isinstance(child, ast.BoolOp):
                                complexity += len(child.values) - 1

                        total_complexity += complexity
                        total_functions += 1

            except Exception:
                continue

        return total_complexity / total_functions if total_functions > 0 else 0

    def _calculate_coupling_metrics(self) -> dict[str, float]:
        """Calculate coupling metrics"""
        if not self.dependency_graph.nodes():
            return {}

        # Calculate various coupling metrics
        metrics = {}

        # Average degree
        degrees = [
            int(self.dependency_graph.degree(node)) for node in self.dependency_graph.nodes()
        ]
        metrics["average_degree"] = sum(degrees) / len(degrees) if degrees else 0

        # In-degree and out-degree
        in_degrees = [
            int(self.dependency_graph.in_degree(node))
            for node in self.dependency_graph.nodes()
        ]
        out_degrees = [
            int(self.dependency_graph.out_degree(node))
            for node in self.dependency_graph.nodes()
        ]

        metrics["average_in_degree"] = (
            sum(in_degrees) / len(in_degrees) if in_degrees else 0
        )
        metrics["average_out_degree"] = (
            sum(out_degrees) / len(out_degrees) if out_degrees else 0
        )

        # Coupling ratio
        total_edges = self.dependency_graph.number_of_edges()
        total_nodes = self.dependency_graph.number_of_nodes()
        metrics["coupling_ratio"] = (
            total_edges / (total_nodes * (total_nodes - 1)) if total_nodes > 1 else 0
        )

        return metrics

    def _calculate_cohesion_metrics(self) -> dict[str, float]:
        """Calculate cohesion metrics"""
        # Simplified cohesion calculation
        metrics = {}

        # LCOM (Lack of Cohesion of Methods) - simplified
        total_classes = len(
            [p for p in self.design_patterns if p.pattern == DesignPattern.SINGLETON]
        )
        metrics["lcom"] = (
            1.0 - (total_classes / len(self.design_patterns))
            if self.design_patterns
            else 0
        )

        return metrics

    def _analyze_coupling(self) -> dict[str, CouplingLevel]:
        """Analyze coupling levels"""
        coupling_analysis = {}

        for node in self.dependency_graph.nodes():
            degree = int(self.dependency_graph.degree(node))

            if degree <= 2:
                coupling_analysis[node] = CouplingLevel.LOW
            elif degree <= 5:
                coupling_analysis[node] = CouplingLevel.MEDIUM
            elif degree <= 10:
                coupling_analysis[node] = CouplingLevel.HIGH
            else:
                coupling_analysis[node] = CouplingLevel.VERY_HIGH

        return coupling_analysis

    def _analyze_complexity(self) -> dict[str, ComplexityLevel]:
        """Analyze complexity levels"""
        complexity_analysis = {}

        # Analyze based on cyclomatic complexity and other factors
        for file_path in self.project_root.rglob("*.py"):
            if "__pycache__" not in str(file_path):
                try:
                    with open(file_path, encoding="utf-8") as f:
                        content = f.read()

                    tree = ast.parse(content)
                    complexity = self._calculate_file_complexity(tree)

                    if complexity <= 5:
                        complexity_analysis[
                            str(file_path.relative_to(self.project_root))
                        ] = ComplexityLevel.SIMPLE
                    elif complexity <= 15:
                        complexity_analysis[
                            str(file_path.relative_to(self.project_root))
                        ] = ComplexityLevel.MODERATE
                    elif complexity <= 30:
                        complexity_analysis[
                            str(file_path.relative_to(self.project_root))
                        ] = ComplexityLevel.COMPLEX
                    else:
                        complexity_analysis[
                            str(file_path.relative_to(self.project_root))
                        ] = ComplexityLevel.VERY_COMPLEX

                except Exception:
                    continue

        return complexity_analysis

    def _calculate_file_complexity(self, tree: ast.AST) -> int:
        """Calculate complexity for a single file"""
        complexity = 0

        for node in ast.walk(tree):
            if isinstance(node, ast.If | ast.While | ast.For | ast.ExceptHandler):
                complexity += 1
            elif isinstance(node, ast.BoolOp):
                complexity += len(node.values) - 1

        return complexity

    def _generate_recommendations(
        self,
        metrics: ArchitectureMetrics,
        coupling_analysis: dict[str, CouplingLevel],
        complexity_analysis: dict[str, ComplexityLevel],
    ) -> list[str]:
        """Generate architecture recommendations"""
        recommendations = []

        # Complexity recommendations
        if metrics.cyclomatic_complexity > 10:
            recommendations.append(
                "Reduce cyclomatic complexity by breaking down complex functions"
            )

        # Coupling recommendations
        high_coupling_files = [
            f
            for f, level in coupling_analysis.items()
            if level in [CouplingLevel.HIGH, CouplingLevel.VERY_HIGH]
        ]
        if high_coupling_files:
            recommendations.append(
                f"Reduce coupling in {len(high_coupling_files)} files"
            )

        # Complexity recommendations
        complex_files = [
            f
            for f, level in complexity_analysis.items()
            if level in [ComplexityLevel.COMPLEX, ComplexityLevel.VERY_COMPLEX]
        ]
        if complex_files:
            recommendations.append(f"Simplify {len(complex_files)} complex files")

        # Design pattern recommendations
        if len(metrics.design_patterns_found) < 3:
            recommendations.append(
                "Consider implementing more design patterns for better code organization"
            )

        # Refactoring recommendations
        high_priority_refactoring = [
            r
            for r in metrics.refactoring_suggestions
            if r.priority in ["high", "critical"]
        ]
        if high_priority_refactoring:
            recommendations.append(
                f"Address {len(high_priority_refactoring)} high-priority refactoring items"
            )

        # Technical debt recommendations
        critical_debt = [d for d in metrics.technical_debt if d.severity == "critical"]
        if critical_debt:
            recommendations.append(
                f"Address {len(critical_debt)} critical technical debt items"
            )

        return recommendations

    def save_refactoring_report(self, report: ArchitectureReport) -> str:
        """Save refactoring report"""
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

        # Save detailed refactoring suggestions
        refactor_file = self.refactor_dir / f"refactoring_suggestions_{timestamp}.md"

        with open(refactor_file, "w", encoding="utf-8") as f:
            f.write("# Refactoring Suggestions Report\n\n")
            f.write(f"**Generated**: {timestamp}\n\n")

            # Group by priority
            by_priority = defaultdict(list)
            for suggestion in report.metrics.refactoring_suggestions:
                by_priority[suggestion.priority].append(suggestion)

            for priority in ["critical", "high", "medium", "low"]:
                if priority in by_priority:
                    f.write(f"## {priority.title()} Priority\n\n")

                    for suggestion in by_priority[priority]:
                        f.write(f"### {suggestion.description}\n")
                        f.write(
                            f"**File**: {suggestion.file_path}:{suggestion.line_number}\n"
                        )
                        f.write(f"**Type**: {suggestion.suggestion_type}\n")
                        f.write(f"**Impact**: {suggestion.impact}\n")
                        f.write(f"**Effort**: {suggestion.effort}\n\n")
                        f.write("**Benefits**:\n")
                        for benefit in suggestion.benefits:
                            f.write(f"- {benefit}\n")
                        f.write("\n")

        return str(refactor_file)

    def save_architecture_report(self, report: ArchitectureReport) -> str:
        """Save architecture report"""
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

        # Save JSON report
        json_path = (
            self.project_root / "artifacts" / f"architecture_report_{timestamp}.json"
        )
        json_path.parent.mkdir(exist_ok=True)

        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(asdict(report), f, indent=2, default=str)

        return str(json_path)


def main():
    """Main function for testing"""
    analyzer = ArchitectureAnalyzer(".")

    # Analyze architecture
    report = analyzer.analyze_architecture()

    # Save reports
    json_path = analyzer.save_architecture_report(report)
    refactor_path = analyzer.save_refactoring_report(report)

    print(f"Architecture report saved: {json_path}")
    print(f"Refactoring report saved: {refactor_path}")
    print(f"Total files analyzed: {report.metrics.total_files}")
    print(f"Design patterns found: {len(report.metrics.design_patterns_found)}")
    print(f"Refactoring suggestions: {len(report.metrics.refactoring_suggestions)}")


if __name__ == "__main__":
    main()
