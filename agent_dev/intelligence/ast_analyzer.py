#!/usr/bin/env python3
"""
StillMe AgentDev - AST Analyzer
Enterprise-grade AST-based code analysis and semantic understanding
"""

import ast
import hashlib
import re
import time
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any


class CodeComplexity(Enum):
    """Code complexity levels"""

    SIMPLE = "simple"
    MODERATE = "moderate"
    COMPLEX = "complex"
    VERY_COMPLEX = "very_complex"


class CodeQuality(Enum):
    """Code quality levels"""

    EXCELLENT = "excellent"
    GOOD = "good"
    FAIR = "fair"
    POOR = "poor"
    CRITICAL = "critical"


class PatternType(Enum):
    """Code pattern types"""

    DESIGN_PATTERN = "design_pattern"
    ANTI_PATTERN = "anti_pattern"
    CODE_SMELL = "code_smell"
    BEST_PRACTICE = "best_practice"
    SECURITY_ISSUE = "security_issue"
    PERFORMANCE_ISSUE = "performance_issue"


@dataclass
class CodeMetric:
    """Code metric measurement"""

    metric_name: str
    value: float
    threshold: float | None
    severity: str
    description: str
    recommendations: list[str]


@dataclass
class CodePattern:
    """Code pattern detection"""

    pattern_type: PatternType
    name: str
    description: str
    severity: str
    line_number: int
    code_snippet: str
    suggestions: list[str]
    confidence: float


@dataclass
class ASTNode:
    """AST node representation"""

    node_type: str
    name: str | None
    line_number: int
    column_number: int
    children: list["ASTNode"]
    attributes: dict[str, Any]
    complexity_score: float


@dataclass
class CodeAnalysis:
    """Complete code analysis result"""

    file_path: str
    file_hash: str
    analysis_timestamp: float
    metrics: list[CodeMetric]
    patterns: list[CodePattern]
    ast_nodes: list[ASTNode]
    complexity_score: float
    quality_score: float
    maintainability_index: float
    technical_debt: float
    security_issues: list[CodePattern]
    performance_issues: list[CodePattern]
    recommendations: list[str]


class ASTAnalyzer:
    """Enterprise AST-based code analyzer"""

    def __init__(self, config_path: str | None = None):
        self.config = self._load_config(config_path)
        self.patterns = self._load_patterns()
        self.metrics_config = self._load_metrics_config()
        self.analysis_cache: dict[str, CodeAnalysis] = {}

    def _load_config(self, config_path: str | None = None) -> dict[str, Any]:
        """Load AST analyzer configuration"""
        if config_path:
            config_file = Path(config_path)
        else:
            config_file = Path("agent-dev/config/ast_analyzer.yaml")

        if config_file.exists():
            import yaml

            with open(config_file) as f:
                return yaml.safe_load(f)
        else:
            return {
                "complexity_thresholds": {
                    "cyclomatic": 10,
                    "cognitive": 15,
                    "halstead": 20,
                },
                "quality_thresholds": {
                    "maintainability_index": 70,
                    "technical_debt_ratio": 0.1,
                },
                "pattern_detection": {"enabled": True, "confidence_threshold": 0.7},
                "cache_enabled": True,
                "max_file_size": 1024 * 1024,  # 1MB
            }

    def _load_patterns(self) -> dict[str, dict[str, Any]]:
        """Load code pattern definitions"""
        return {
            "security_patterns": {
                "hardcoded_secrets": {
                    "pattern": r'(api_key|password|secret|token)\s*=\s*["\'][^"\']+["\']',
                    "severity": "high",
                    "description": "Hardcoded secrets detected",
                    "suggestions": [
                        "Use environment variables",
                        "Use secure configuration management",
                    ],
                },
                "sql_injection": {
                    "pattern": r'execute\s*\(\s*["\'].*%s.*["\']',
                    "severity": "critical",
                    "description": "Potential SQL injection vulnerability",
                    "suggestions": ["Use parameterized queries", "Validate input data"],
                },
                "eval_usage": {
                    "pattern": r"eval\s*\(",
                    "severity": "high",
                    "description": "Use of eval() function",
                    "suggestions": [
                        "Avoid eval()",
                        "Use safer alternatives like ast.literal_eval()",
                    ],
                },
            },
            "performance_patterns": {
                "inefficient_loop": {
                    "pattern": r"for\s+\w+\s+in\s+range\s*\(\s*len\s*\(",
                    "severity": "medium",
                    "description": "Inefficient loop pattern",
                    "suggestions": ["Use enumerate()", "Use direct iteration"],
                },
                "string_concatenation": {
                    "pattern": r'(\w+\s*\+=\s*["\'][^"\']*["\']|["\'][^"\']*["\']\s*\+\s*\w+)',
                    "severity": "low",
                    "description": "String concatenation in loop",
                    "suggestions": ["Use join() method", "Use f-strings"],
                },
            },
            "design_patterns": {
                "singleton": {
                    "pattern": r"class\s+\w+.*:\s*\n\s*_instance\s*=\s*None",
                    "severity": "info",
                    "description": "Singleton pattern detected",
                    "suggestions": [
                        "Consider if singleton is necessary",
                        "Use dependency injection",
                    ],
                },
                "factory": {
                    "pattern": r"def\s+create_\w+\s*\(",
                    "severity": "info",
                    "description": "Factory pattern detected",
                    "suggestions": [
                        "Good use of factory pattern",
                        "Consider abstract factory",
                    ],
                },
            },
            "anti_patterns": {
                "god_class": {
                    "pattern": r"class\s+\w+.*:\s*\n(.*\n){50,}",
                    "severity": "medium",
                    "description": "Potential God class (too many lines)",
                    "suggestions": [
                        "Split into smaller classes",
                        "Apply Single Responsibility Principle",
                    ],
                },
                "long_method": {
                    "pattern": r"def\s+\w+.*:\s*\n(.*\n){20,}",
                    "severity": "medium",
                    "description": "Long method detected",
                    "suggestions": [
                        "Break into smaller methods",
                        "Extract helper functions",
                    ],
                },
            },
        }

    def _load_metrics_config(self) -> dict[str, Any]:
        """Load metrics configuration"""
        return {
            "cyclomatic_complexity": {
                "description": "Cyclomatic complexity of the code",
                "threshold": 10,
                "calculation": "count_decision_points",
            },
            "cognitive_complexity": {
                "description": "Cognitive complexity of the code",
                "threshold": 15,
                "calculation": "count_nested_structures",
            },
            "halstead_complexity": {
                "description": "Halstead complexity measures",
                "threshold": 20,
                "calculation": "halstead_metrics",
            },
            "maintainability_index": {
                "description": "Code maintainability index",
                "threshold": 70,
                "calculation": "mi_formula",
            },
            "lines_of_code": {
                "description": "Total lines of code",
                "threshold": 1000,
                "calculation": "count_lines",
            },
            "function_length": {
                "description": "Average function length",
                "threshold": 20,
                "calculation": "avg_function_lines",
            },
        }

    def analyze_file(self, file_path: str) -> CodeAnalysis:
        """Analyze a single file"""
        file_path_obj: Path = Path(file_path)

        # Check cache
        file_hash: str = ""
        if self.config["cache_enabled"]:
            file_hash = self._calculate_file_hash(file_path_obj)
            if file_hash in self.analysis_cache:
                cached_analysis = self.analysis_cache[file_hash]
                if cached_analysis.file_path == str(file_path):
                    return cached_analysis

        # Check file size
        if file_path_obj.stat().st_size > self.config["max_file_size"]:
            raise ValueError(f"File too large: {file_path_obj}")

        try:
            with open(file_path_obj, encoding="utf-8") as f:
                source_code = f.read()
        except Exception as e:
            raise ValueError(f"Failed to read file: {e}") from e

        try:
            tree = ast.parse(source_code, filename=str(file_path_obj))
        except SyntaxError as e:
            raise ValueError(f"Syntax error in file: {e}") from e

        # Perform analysis
        analysis = self._analyze_ast(tree, str(file_path_obj), source_code)

        # Cache result
        if self.config["cache_enabled"]:
            self.analysis_cache[file_hash] = analysis

        return analysis

    def _analyze_ast(
        self, tree: ast.AST, file_path: str, source_code: str
    ) -> CodeAnalysis:
        """Analyze AST tree"""
        lines = source_code.split("\n")
        file_hash = hashlib.sha256(source_code.encode()).hexdigest()

        # Extract AST nodes
        ast_nodes = self._extract_ast_nodes(tree)

        # Calculate metrics
        metrics = self._calculate_metrics(tree, lines)

        # Detect patterns
        patterns = self._detect_patterns(source_code, lines)

        # Calculate complexity score
        complexity_score = self._calculate_complexity_score(metrics)

        # Calculate quality score
        quality_score = self._calculate_quality_score(metrics, patterns)

        # Calculate maintainability index
        maintainability_index = self._calculate_maintainability_index(metrics)

        # Calculate technical debt
        technical_debt = self._calculate_technical_debt(metrics, patterns)

        # Filter security and performance issues
        security_issues = [
            p for p in patterns if p.pattern_type == PatternType.SECURITY_ISSUE
        ]
        performance_issues = [
            p for p in patterns if p.pattern_type == PatternType.PERFORMANCE_ISSUE
        ]

        # Generate recommendations
        recommendations = self._generate_recommendations(metrics, patterns)

        return CodeAnalysis(
            file_path=file_path,
            file_hash=file_hash,
            analysis_timestamp=time.time(),
            metrics=metrics,
            patterns=patterns,
            ast_nodes=ast_nodes,
            complexity_score=complexity_score,
            quality_score=quality_score,
            maintainability_index=maintainability_index,
            technical_debt=technical_debt,
            security_issues=security_issues,
            performance_issues=performance_issues,
            recommendations=recommendations,
        )

    def _extract_ast_nodes(self, tree: ast.AST) -> list[ASTNode]:
        """Extract AST nodes with metadata"""
        nodes: list[ASTNode] = []

        for node in ast.walk(tree):
            ast_node = ASTNode(
                node_type=type(node).__name__,
                name=self._get_node_name(node),
                line_number=getattr(node, "lineno", 0),
                column_number=getattr(node, "col_offset", 0),
                children=[],
                attributes=self._get_node_attributes(node),
                complexity_score=self._calculate_node_complexity(node),
            )
            nodes.append(ast_node)

        return nodes

    def _get_node_name(self, node: ast.AST) -> str | None:
        """Get node name if applicable"""
        if isinstance(node, ast.FunctionDef | ast.ClassDef | ast.Name):
            return getattr(node, "name", None)
        elif isinstance(node, ast.Assign):
            if node.targets and isinstance(node.targets[0], ast.Name):
                return node.targets[0].id
        return None

    def _get_node_attributes(self, node: ast.AST) -> dict[str, Any]:
        """Get node attributes"""
        attributes: dict[str, Any] = {}

        if isinstance(node, ast.FunctionDef):
            attributes["args_count"] = len(node.args.args)
            attributes["decorators"] = [
                d.id if isinstance(d, ast.Name) else str(d) for d in node.decorator_list
            ]
        elif isinstance(node, ast.ClassDef):
            attributes["bases"] = [
                b.id if isinstance(b, ast.Name) else str(b) for b in node.bases
            ]
            attributes["decorators"] = [
                d.id if isinstance(d, ast.Name) else str(d) for d in node.decorator_list
            ]
        elif isinstance(node, ast.Call):
            attributes["function_name"] = self._get_call_function_name(node)
            attributes["args_count"] = len(node.args)
            attributes["keywords_count"] = len(node.keywords)

        return attributes

    def _get_call_function_name(self, node: ast.Call) -> str | None:
        """Get function name from call node"""
        if isinstance(node.func, ast.Name):
            return node.func.id
        elif isinstance(node.func, ast.Attribute):
            return node.func.attr
        return None

    def _calculate_node_complexity(self, node: ast.AST) -> float:
        """Calculate complexity score for a node"""
        complexity = 0

        # Decision points
        if isinstance(node, ast.If | ast.While | ast.For | ast.AsyncFor):
            complexity += 1
        elif isinstance(node, ast.ExceptHandler):
            complexity += 1
        elif isinstance(node, ast.And | ast.Or):
            complexity += 1

        # Nested structures
        if hasattr(node, "body"):
            body = getattr(node, "body", None)
            if body and hasattr(body, "__iter__"):
                for child in body:
                    complexity += self._calculate_node_complexity(child)

        return complexity

    def _calculate_metrics(self, tree: ast.AST, lines: list[str]) -> list[CodeMetric]:
        """Calculate code metrics"""
        metrics: list[CodeMetric] = []

        # Cyclomatic complexity
        cyclomatic = self._calculate_cyclomatic_complexity(tree)
        metrics.append(
            CodeMetric(
                metric_name="cyclomatic_complexity",
                value=cyclomatic,
                threshold=self.metrics_config["cyclomatic_complexity"]["threshold"],
                severity="high"
                if cyclomatic > 10
                else "medium"
                if cyclomatic > 5
                else "low",
                description="Cyclomatic complexity of the code",
                recommendations=[
                    "Reduce decision points",
                    "Extract methods",
                    "Use polymorphism",
                ],
            )
        )

        # Lines of code
        loc = len(
            [
                line
                for line in lines
                if line.strip() and not line.strip().startswith("#")
            ]
        )
        metrics.append(
            CodeMetric(
                metric_name="lines_of_code",
                value=loc,
                threshold=self.metrics_config["lines_of_code"]["threshold"],
                severity="high" if loc > 1000 else "medium" if loc > 500 else "low",
                description="Total lines of code",
                recommendations=["Split into smaller files", "Extract modules"],
            )
        )

        # Function count
        function_count = len(
            [node for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)]
        )
        metrics.append(
            CodeMetric(
                metric_name="function_count",
                value=function_count,
                threshold=None,
                severity="info",
                description="Number of functions",
                recommendations=[],
            )
        )

        # Class count
        class_count = len(
            [node for node in ast.walk(tree) if isinstance(node, ast.ClassDef)]
        )
        metrics.append(
            CodeMetric(
                metric_name="class_count",
                value=class_count,
                threshold=None,
                severity="info",
                description="Number of classes",
                recommendations=[],
            )
        )

        return metrics

    def _calculate_cyclomatic_complexity(self, tree: ast.AST) -> int:
        """Calculate cyclomatic complexity"""
        complexity = 1  # Base complexity

        for node in ast.walk(tree):
            if isinstance(node, ast.If | ast.While | ast.For | ast.AsyncFor):
                complexity += 1
            elif isinstance(node, ast.ExceptHandler):
                complexity += 1
            elif isinstance(node, ast.And | ast.Or):
                complexity += 1

        return complexity

    def _detect_patterns(self, source_code: str, lines: list[str]) -> list[CodePattern]:
        """Detect code patterns"""
        patterns: list[CodePattern] = []

        for category, pattern_defs in self.patterns.items():
            for pattern_name, pattern_config in pattern_defs.items():
                matches = re.finditer(
                    pattern_config["pattern"], source_code, re.MULTILINE
                )

                for match in matches:
                    line_number = source_code[: match.start()].count("\n") + 1
                    code_snippet = (
                        lines[line_number - 1] if line_number <= len(lines) else ""
                    )

                    # Determine pattern type
                    if category == "security_patterns":
                        pattern_type = PatternType.SECURITY_ISSUE
                    elif category == "performance_patterns":
                        pattern_type = PatternType.PERFORMANCE_ISSUE
                    elif category == "design_patterns":
                        pattern_type = PatternType.DESIGN_PATTERN
                    elif category == "anti_patterns":
                        pattern_type = PatternType.ANTI_PATTERN
                    else:
                        pattern_type = PatternType.CODE_SMELL

                    pattern = CodePattern(
                        pattern_type=pattern_type,
                        name=pattern_name,
                        description=pattern_config["description"],
                        severity=pattern_config["severity"],
                        line_number=line_number,
                        code_snippet=code_snippet.strip(),
                        suggestions=pattern_config["suggestions"],
                        confidence=0.8,  # Default confidence
                    )
                    patterns.append(pattern)

        return patterns

    def _calculate_complexity_score(self, metrics: list[CodeMetric]) -> float:
        """Calculate overall complexity score"""
        complexity_metrics = [m for m in metrics if "complexity" in m.metric_name]
        if not complexity_metrics:
            return 0.0

        total_complexity = sum(m.value for m in complexity_metrics)
        max_complexity = sum(m.threshold or 10 for m in complexity_metrics)

        return (
            min(total_complexity / max_complexity, 1.0) if max_complexity > 0 else 0.0
        )

    def _calculate_quality_score(
        self, metrics: list[CodeMetric], patterns: list[CodePattern]
    ) -> float:
        """Calculate code quality score"""
        score = 1.0

        # Deduct for high complexity
        for metric in metrics:
            if metric.threshold and metric.value > metric.threshold:
                score -= 0.1

        # Deduct for issues
        for pattern in patterns:
            if pattern.severity == "critical":
                score -= 0.2
            elif pattern.severity == "high":
                score -= 0.1
            elif pattern.severity == "medium":
                score -= 0.05

        return max(score, 0.0)

    def _calculate_maintainability_index(self, metrics: list[CodeMetric]) -> float:
        """Calculate maintainability index"""
        # Simplified maintainability index calculation
        loc_metric = next(
            (m for m in metrics if m.metric_name == "lines_of_code"), None
        )
        complexity_metric = next(
            (m for m in metrics if m.metric_name == "cyclomatic_complexity"), None
        )

        if not loc_metric or not complexity_metric:
            return 50.0

        # MI = 171 - 5.2 * ln(aveV) - 0.23 * aveC - 16.2 * ln(aveLOC)
        import math

        mi = (
            171
            - 5.2 * math.log(complexity_metric.value)
            - 0.23 * complexity_metric.value
            - 16.2 * math.log(loc_metric.value)
        )
        return max(mi, 0.0)

    def _calculate_technical_debt(
        self, metrics: list[CodeMetric], patterns: list[CodePattern]
    ) -> float:
        """Calculate technical debt ratio"""
        len(patterns)
        critical_issues = len([p for p in patterns if p.severity == "critical"])
        high_issues = len([p for p in patterns if p.severity == "high"])

        # Technical debt = (critical * 10 + high * 5 + medium * 2 + low * 1) / total_lines
        loc_metric = next(
            (m for m in metrics if m.metric_name == "lines_of_code"), None
        )
        if not loc_metric or loc_metric.value == 0:
            return 0.0

        debt_score = critical_issues * 10 + high_issues * 5
        return debt_score / loc_metric.value

    def _generate_recommendations(
        self, metrics: list[CodeMetric], patterns: list[CodePattern]
    ) -> list[str]:
        """Generate improvement recommendations"""
        recommendations: list[str] = []

        # Metric-based recommendations
        for metric in metrics:
            if metric.threshold and metric.value > metric.threshold:
                recommendations.extend(metric.recommendations)

        # Pattern-based recommendations
        for pattern in patterns:
            if pattern.severity in ["critical", "high"]:
                recommendations.extend(pattern.suggestions)

        # Remove duplicates
        return list(set(recommendations))

    def _calculate_file_hash(self, file_path: Path) -> str:
        """Calculate file hash for caching"""
        try:
            with open(file_path, "rb") as f:
                return hashlib.sha256(f.read()).hexdigest()
        except Exception:
            return str(file_path)

    def analyze_directory(self, directory_path: str) -> dict[str, CodeAnalysis]:
        """Analyze all Python files in directory"""
        directory: Path = Path(directory_path)
        analyses: dict[str, CodeAnalysis] = {}

        for py_file in directory.rglob("*.py"):
            try:
                analysis = self.analyze_file(str(py_file))
                analyses[str(py_file)] = analysis
            except Exception as e:
                print(f"⚠️ Failed to analyze {py_file}: {e}")

        return analyses

    def get_analysis_summary(self, analyses: dict[str, CodeAnalysis]) -> dict[str, Any]:
        """Get summary of multiple analyses"""
        total_files: int = len(analyses)
        total_lines: float = sum(
            a.metrics[1].value for a in analyses.values() if len(a.metrics) > 1
        )
        avg_complexity: float = (
            sum(a.complexity_score for a in analyses.values()) / total_files
            if total_files > 0
            else 0
        )
        avg_quality: float = (
            sum(a.quality_score for a in analyses.values()) / total_files
            if total_files > 0
            else 0
        )

        # Count issues by severity
        issue_counts: dict[str, int] = {"critical": 0, "high": 0, "medium": 0, "low": 0}
        for analysis in analyses.values():
            for pattern in analysis.patterns:
                issue_counts[pattern.severity] += 1

        return {
            "total_files": total_files,
            "total_lines": total_lines,
            "average_complexity": avg_complexity,
            "average_quality": avg_quality,
            "issue_counts": issue_counts,
            "files_with_issues": len([a for a in analyses.values() if a.patterns]),
            "recommendations_count": sum(
                len(a.recommendations) for a in analyses.values()
            ),
        }


# Global AST analyzer instance
ast_analyzer = ASTAnalyzer()


# Convenience functions
def analyze_code_file(file_path: str) -> CodeAnalysis:
    """Analyze a single code file"""
    return ast_analyzer.analyze_file(file_path)


def analyze_code_directory(directory_path: str) -> dict[str, CodeAnalysis]:
    """Analyze all Python files in directory"""
    return ast_analyzer.analyze_directory(directory_path)


def get_code_quality_summary(analyses: dict[str, CodeAnalysis]) -> dict[str, Any]:
    """Get code quality summary"""
    return ast_analyzer.get_analysis_summary(analyses)


if __name__ == "__main__":
    # Example usage
    analyzer = ASTAnalyzer()

    # Analyze a single file
    try:
        analysis = analyzer.analyze_file("agent-dev/cli/agentdev_cli.py")
        print(f"File: {analysis.file_path}")
        print(f"Complexity Score: {analysis.complexity_score:.2f}")
        print(f"Quality Score: {analysis.quality_score:.2f}")
        print(f"Maintainability Index: {analysis.maintainability_index:.2f}")
        print(f"Technical Debt: {analysis.technical_debt:.2f}")
        print(f"Issues Found: {len(analysis.patterns)}")
        print(f"Recommendations: {len(analysis.recommendations)}")
    except Exception as e:
        print(f"Analysis failed: {e}")

    # Analyze directory
    try:
        analyses = analyzer.analyze_directory("agent-dev")
        summary = analyzer.get_analysis_summary(analyses)
        print("\nDirectory Analysis Summary:")
        print(f"Total Files: {summary['total_files']}")
        print(f"Total Lines: {summary['total_lines']}")
        print(f"Average Complexity: {summary['average_complexity']:.2f}")
        print(f"Average Quality: {summary['average_quality']:.2f}")
        print(f"Issues: {summary['issue_counts']}")
    except Exception as e:
        print(f"Directory analysis failed: {e}")
