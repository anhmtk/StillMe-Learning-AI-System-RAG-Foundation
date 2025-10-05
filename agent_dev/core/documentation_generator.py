#!/usr/bin/env python3
"""
Documentation Generator - Auto Documentation System
Tự động tạo documentation cho AgentDev Unified

Tính năng:
1. Auto Documentation - Tự động tạo docstrings
2. Module-level Documentation - Tài liệu module
3. API Documentation - Tài liệu API endpoints
4. Code Comments Generator - Tạo comments cho code
5. Knowledge Base Management - Quản lý knowledge base
6. Best Practices Library - Thư viện best practices
"""

import ast
import json
import re
import time
from dataclasses import asdict, dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path


class DocType(Enum):
    """Loại documentation"""

    MODULE = "module"
    FUNCTION = "function"
    CLASS = "class"
    API = "api"
    KNOWLEDGE = "knowledge"
    BEST_PRACTICE = "best_practice"


class DocQuality(Enum):
    """Chất lượng documentation"""

    EXCELLENT = "excellent"
    GOOD = "good"
    FAIR = "fair"
    POOR = "poor"
    MISSING = "missing"


@dataclass
class DocMetadata:
    """Metadata của documentation"""

    doc_type: DocType
    file_path: str
    line_number: int
    name: str
    description: str
    parameters: list[dict[str, str]]
    return_type: str
    examples: list[str]
    quality_score: float
    last_updated: datetime


@dataclass
class DocumentationReport:
    """Báo cáo documentation"""

    total_files: int
    documented_files: int
    documentation_coverage: float
    quality_scores: dict[str, float]
    missing_docs: list[str]
    recommendations: list[str]
    generated_docs: list[DocMetadata]
    analysis_time: float


class DocumentationGenerator:
    """Documentation Generator - Tự động tạo documentation"""

    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.docs_dir = self.project_root / "docs"
        self.knowledge_base_dir = self.docs_dir / "knowledge_base"
        self.troubleshooting_dir = self.docs_dir / "troubleshooting"
        self.best_practices_dir = self.docs_dir / "best_practices"

        # Tạo thư mục docs nếu chưa có
        self._ensure_docs_directories()

        # Load templates
        self.doc_templates = self._load_doc_templates()
        self.best_practices = self._load_best_practices()

    def _ensure_docs_directories(self):
        """Đảm bảo thư mục docs tồn tại"""
        for dir_path in [
            self.docs_dir,
            self.knowledge_base_dir,
            self.troubleshooting_dir,
            self.best_practices_dir,
        ]:
            dir_path.mkdir(parents=True, exist_ok=True)

    def _load_doc_templates(self) -> dict[str, str]:
        """Load documentation templates"""
        return {
            "module": '''"""
{module_name} - {description}

{detailed_description}

Tính năng:
{features}

Sử dụng:
{usage_examples}

Author: AgentDev Unified
Generated: {timestamp}
"""

''',
            "function": '''def {function_name}({parameters}):
    """
    {description}

    Args:
{args_doc}

    Returns:
        {return_type}: {return_description}

    Raises:
        {raises_doc}

    Examples:
{examples_doc}
    """
''',
            "class": '''class {class_name}:
    """
    {description}

    Attributes:
{attributes_doc}

    Methods:
{methods_doc}

    Examples:
{examples_doc}
    """
''',
            "api": '''"""
API Endpoint: {endpoint}

Method: {method}
Description: {description}

Parameters:
{parameters_doc}

Response:
{response_doc}

Examples:
{examples_doc}

Status Codes:
{status_codes_doc}
"""
''',
        }

    def _load_best_practices(self) -> dict[str, list[str]]:
        """Load best practices library"""
        return {
            "python": [
                "Use type hints for all function parameters and return values",
                "Follow PEP 8 style guide",
                "Use meaningful variable and function names",
                "Keep functions small and focused (max 20 lines)",
                "Use docstrings for all public functions and classes",
                "Handle exceptions gracefully with specific exception types",
                "Use list/dict comprehensions for simple transformations",
                "Prefer f-strings over .format() or % formatting",
                "Use context managers (with statements) for resource management",
                "Write unit tests for all public functions",
            ],
            "security": [
                "Never hardcode secrets or API keys in code",
                "Use environment variables for configuration",
                "Validate all user inputs",
                "Use parameterized queries to prevent SQL injection",
                "Implement proper authentication and authorization",
                "Use HTTPS for all external communications",
                "Sanitize user input before displaying",
                "Keep dependencies updated",
                "Use secure random number generators",
                "Implement proper logging without sensitive data",
            ],
            "performance": [
                "Use appropriate data structures for the use case",
                "Avoid premature optimization",
                "Profile code before optimizing",
                "Use caching for expensive operations",
                "Minimize database queries",
                "Use async/await for I/O operations",
                "Avoid deep recursion",
                "Use generators for large datasets",
                "Implement connection pooling",
                "Monitor memory usage",
            ],
            "testing": [
                "Write tests before writing code (TDD)",
                "Use descriptive test names",
                "Test edge cases and error conditions",
                "Mock external dependencies",
                "Keep tests independent and isolated",
                "Use fixtures for test data setup",
                "Test both success and failure scenarios",
                "Maintain high test coverage (aim for 80%+)",
                "Use property-based testing for complex logic",
                "Automate test execution in CI/CD",
            ],
        }

    def generate_module_documentation(self, file_path: str) -> DocMetadata:
        """Tạo documentation cho module"""
        try:
            with open(file_path, encoding="utf-8") as f:
                content = f.read()

            # Parse AST
            tree = ast.parse(content)

            # Extract module info
            module_name = Path(file_path).stem
            docstring = ast.get_docstring(tree)

            # Analyze functions and classes
            functions = [
                node for node in tree.body if isinstance(node, ast.FunctionDef)
            ]
            classes = [node for node in tree.body if isinstance(node, ast.ClassDef)]

            # Generate description
            if docstring:
                description = docstring.split("\n")[0]
            else:
                description = f"Module {module_name} - Auto-generated documentation"

            # Generate features list
            features: list[str] = []
            for func in functions:
                if not func.name.startswith("_"):
                    features.append(
                        f"- {func.name}(): {ast.get_docstring(func) or 'Function'}"
                    )

            for cls in classes:
                if not cls.name.startswith("_"):
                    features.append(
                        f"- {cls.name}: {ast.get_docstring(cls) or 'Class'}"
                    )

            # Generate usage examples
            usage_examples = [
                f"from {module_name} import {', '.join([f.name for f in functions[:3] if not f.name.startswith('_')])}",
                "# Example usage:",
                f"# result = {functions[0].name if functions else 'function_name'}()",
            ]

            # Calculate quality score
            quality_score = self._calculate_doc_quality(
                docstring, len(functions), len(classes)
            )

            return DocMetadata(
                doc_type=DocType.MODULE,
                file_path=file_path,
                line_number=1,
                name=module_name,
                description=description,
                parameters=[],
                return_type="",
                examples=usage_examples,
                quality_score=quality_score,
                last_updated=datetime.now(),
            )

        except Exception as e:
            return DocMetadata(
                doc_type=DocType.MODULE,
                file_path=file_path,
                line_number=1,
                name=Path(file_path).stem,
                description=f"Error generating docs: {e}",
                parameters=[],
                return_type="",
                examples=[],
                quality_score=0.0,
                last_updated=datetime.now(),
            )

    def generate_function_documentation(
        self, file_path: str, function_node: ast.FunctionDef
    ) -> DocMetadata:
        """Tạo documentation cho function"""
        try:
            # Extract function info
            func_name = function_node.name
            docstring = ast.get_docstring(function_node)

            # Extract parameters
            parameters: list[dict[str, str]] = []
            for arg in function_node.args.args:
                param_info = {
                    "name": arg.arg,
                    "type": "Any",  # Could be enhanced with type hints
                    "description": f"Parameter {arg.arg}",
                }
                parameters.append(param_info)

            # Generate description
            if docstring:
                description = docstring.split("\n")[0]
            else:
                description = f"Function {func_name}"

            # Generate examples
            examples: list[str] = [
                "# Example usage:",
                f"# result = {func_name}({', '.join([p['name'] for p in parameters[:3]])})",
            ]

            # Calculate quality score
            quality_score = self._calculate_doc_quality(docstring, 1, 0)

            return DocMetadata(
                doc_type=DocType.FUNCTION,
                file_path=file_path,
                line_number=function_node.lineno,
                name=func_name,
                description=description,
                parameters=parameters,
                return_type="Any",
                examples=examples,
                quality_score=quality_score,
                last_updated=datetime.now(),
            )

        except Exception as e:
            return DocMetadata(
                doc_type=DocType.FUNCTION,
                file_path=file_path,
                line_number=function_node.lineno,
                name=function_node.name,
                description=f"Error generating docs: {e}",
                parameters=[],
                return_type="",
                examples=[],
                quality_score=0.0,
                last_updated=datetime.now(),
            )

    def _calculate_doc_quality(
        self, docstring: str | None, func_count: int, class_count: int
    ) -> float:
        """Tính điểm chất lượng documentation"""
        score = 0.0

        if docstring:
            score += 0.4  # Has docstring
            if len(docstring) > 50:
                score += 0.2  # Detailed docstring
            if "Args:" in docstring or "Parameters:" in docstring:
                score += 0.2  # Has parameter documentation
            if "Returns:" in docstring or "Return:" in docstring:
                score += 0.2  # Has return documentation
        else:
            score = 0.0  # No docstring

        return min(score, 1.0)

    def generate_code_comments(self, file_path: str) -> str:
        """Tạo comments cho code"""
        content = ""
        try:
            with open(file_path, encoding="utf-8") as f:
                content = f.read()

            # Parse AST
            ast.parse(content)

            # Add comments to functions without docstrings
            lines = content.split("\n")
            new_lines: list[str] = []

            for i, line in enumerate(lines):
                new_lines.append(line)

                # Check if this is a function definition without docstring
                if re.match(r"^\s*def\s+\w+", line):
                    # Look ahead to see if there's a docstring
                    has_docstring = False
                    for j in range(i + 1, min(i + 5, len(lines))):
                        if '"""' in lines[j] or "'''" in lines[j]:
                            has_docstring = True
                            break
                        if lines[j].strip() and not lines[j].startswith(" "):
                            break

                    if not has_docstring:
                        # Add a comment
                        match = re.search(r"def\s+(\w+)", line)
                        if match:
                            func_name = match.group(1)
                        else:
                            continue
                        indent = len(line) - len(line.lstrip())
                        comment = (
                            " " * (indent + 4)
                            + f"# TODO: Add docstring for {func_name}()"
                        )
                        new_lines.append(comment)

            return "\n".join(new_lines)

        except Exception as e:
            return f"# Error generating comments: {e}\n{content}"

    def create_knowledge_base_entry(
        self, topic: str, content: str, category: str = "general"
    ) -> str:
        """Tạo entry trong knowledge base"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        entry_content = f"""# {topic}

**Category**: {category}
**Created**: {timestamp}
**Source**: AgentDev Unified Documentation Generator

## Overview

{content}

## Related Topics

- [Best Practices](../best_practices/)
- [Troubleshooting](../troubleshooting/)

## References

- Generated by AgentDev Unified
- Last updated: {timestamp}
"""

        # Save to knowledge base
        filename = f"{topic.lower().replace(' ', '_')}.md"
        file_path = self.knowledge_base_dir / filename

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(entry_content)

        return str(file_path)

    def create_best_practices_guide(self, language: str) -> str:
        """Tạo best practices guide"""
        if language not in self.best_practices:
            return ""

        practices = self.best_practices[language]
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        content = f"""# {language.title()} Best Practices

**Generated**: {timestamp}
**Source**: AgentDev Unified Documentation Generator

## Overview

This guide contains best practices for {language} development, automatically generated and maintained by AgentDev Unified.

## Best Practices

"""

        for i, practice in enumerate(practices, 1):
            content += f"{i}. {practice}\n"

        content += f"""
## Implementation Checklist

- [ ] Review all practices
- [ ] Implement in current project
- [ ] Add to team guidelines
- [ ] Update CI/CD checks

## Notes

- This guide is automatically maintained
- Last updated: {timestamp}
- For questions, refer to AgentDev Unified documentation
"""

        # Save to best practices directory
        filename = f"{language}_best_practices.md"
        file_path = self.best_practices_dir / filename

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)

        return str(file_path)

    def generate_documentation_report(self) -> DocumentationReport:
        """Tạo báo cáo documentation"""
        start_time = time.time()

        # Scan project files
        python_files = list(self.project_root.rglob("*.py"))
        total_files = len(python_files)
        documented_files = 0
        generated_docs: list[DocMetadata] = []
        missing_docs: list[str] = []
        quality_scores: dict[str, list[float]] = {
            "modules": [],
            "functions": [],
            "classes": [],
        }

        for file_path in python_files:
            try:
                # Skip test files and __pycache__
                if "test" in str(file_path) or "__pycache__" in str(file_path):
                    continue

                # Generate module documentation
                module_doc = self.generate_module_documentation(str(file_path))
                generated_docs.append(module_doc)

                if module_doc.quality_score > 0.5:
                    documented_files += 1
                else:
                    missing_docs.append(str(file_path))

                quality_scores["modules"].append(module_doc.quality_score)

                # Parse file for functions and classes
                with open(file_path, encoding="utf-8") as f:
                    content = f.read()

                tree = ast.parse(content)

                # Generate function documentation
                for node in tree.body:
                    if isinstance(node, ast.FunctionDef) and not node.name.startswith(
                        "_"
                    ):
                        func_doc = self.generate_function_documentation(
                            str(file_path), node
                        )
                        generated_docs.append(func_doc)
                        quality_scores["functions"].append(func_doc.quality_score)

                # Generate class documentation
                for node in tree.body:
                    if isinstance(node, ast.ClassDef) and not node.name.startswith("_"):
                        class_doc = self.generate_module_documentation(
                            str(file_path)
                        )  # Simplified
                        generated_docs.append(class_doc)
                        quality_scores["classes"].append(class_doc.quality_score)

            except Exception as e:
                missing_docs.append(f"{file_path}: {e}")

        # Calculate coverage
        documentation_coverage = (
            (documented_files / total_files * 100) if total_files > 0 else 0
        )

        # Calculate average quality scores
        avg_quality_scores: dict[str, float] = {}
        for category, scores in quality_scores.items():
            avg_quality_scores[category] = sum(scores) / len(scores) if scores else 0.0

        # Generate recommendations
        recommendations: list[str] = []
        if documentation_coverage < 50:
            recommendations.append("Increase documentation coverage to at least 50%")
        if avg_quality_scores.get("modules", 0) < 0.7:
            recommendations.append("Improve module documentation quality")
        if avg_quality_scores.get("functions", 0) < 0.6:
            recommendations.append("Add docstrings to more functions")

        analysis_time = time.time() - start_time

        return DocumentationReport(
            total_files=total_files,
            documented_files=documented_files,
            documentation_coverage=documentation_coverage,
            quality_scores=avg_quality_scores,
            missing_docs=missing_docs,
            recommendations=recommendations,
            generated_docs=generated_docs,
            analysis_time=analysis_time,
        )

    def save_documentation_report(self, report: DocumentationReport) -> str:
        """Lưu báo cáo documentation"""
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

        # Save JSON report
        json_path = (
            self.project_root / "artifacts" / f"documentation_report_{timestamp}.json"
        )
        json_path.parent.mkdir(exist_ok=True)

        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(asdict(report), f, indent=2, default=str)

        # Save HTML report
        html_path = (
            self.project_root / "artifacts" / f"documentation_report_{timestamp}.html"
        )

        html_content = f"""<!DOCTYPE html>
<html>
<head>
    <title>Documentation Report - {timestamp}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        .header {{ background: #f0f0f0; padding: 20px; border-radius: 5px; }}
        .metric {{ display: inline-block; margin: 10px; padding: 10px; background: #e0e0e0; border-radius: 3px; }}
        .good {{ background: #d4edda; }}
        .warning {{ background: #fff3cd; }}
        .error {{ background: #f8d7da; }}
        .recommendations {{ background: #cce5ff; padding: 15px; border-radius: 5px; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>Documentation Report</h1>
        <p>Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>
    </div>

    <h2>Summary</h2>
    <div class="metric {'good' if report.documentation_coverage >= 70 else 'warning' if report.documentation_coverage >= 50 else 'error'}">
        <strong>Coverage:</strong> {report.documentation_coverage:.1f}%
    </div>
    <div class="metric {'good' if report.documented_files >= report.total_files * 0.7 else 'warning' if report.documented_files >= report.total_files * 0.5 else 'error'}">
        <strong>Documented Files:</strong> {report.documented_files}/{report.total_files}
    </div>
    <div class="metric">
        <strong>Analysis Time:</strong> {report.analysis_time:.2f}s
    </div>

    <h2>Quality Scores</h2>
    <div class="metric {'good' if report.quality_scores.get('modules', 0) >= 0.7 else 'warning' if report.quality_scores.get('modules', 0) >= 0.5 else 'error'}">
        <strong>Modules:</strong> {report.quality_scores.get('modules', 0):.2f}
    </div>
    <div class="metric {'good' if report.quality_scores.get('functions', 0) >= 0.6 else 'warning' if report.quality_scores.get('functions', 0) >= 0.4 else 'error'}">
        <strong>Functions:</strong> {report.quality_scores.get('functions', 0):.2f}
    </div>
    <div class="metric {'good' if report.quality_scores.get('classes', 0) >= 0.7 else 'warning' if report.quality_scores.get('classes', 0) >= 0.5 else 'error'}">
        <strong>Classes:</strong> {report.quality_scores.get('classes', 0):.2f}
    </div>

    <h2>Recommendations</h2>
    <div class="recommendations">
        <ul>
            {''.join([f'<li>{rec}</li>' for rec in report.recommendations])}
        </ul>
    </div>

    <h2>Missing Documentation</h2>
    <ul>
        {''.join([f'<li>{doc}</li>' for doc in report.missing_docs[:10]])}
        {f'<li>... and {len(report.missing_docs) - 10} more</li>' if len(report.missing_docs) > 10 else ''}
    </ul>
</body>
</html>"""

        with open(html_path, "w", encoding="utf-8") as f:
            f.write(html_content)

        return str(html_path)


def main():
    """Main function for testing"""
    generator = DocumentationGenerator(".")

    # Generate documentation report
    report = generator.generate_documentation_report()

    # Save report
    html_path = generator.save_documentation_report(report)

    print(f"Documentation report generated: {html_path}")
    print(f"Coverage: {report.documentation_coverage:.1f}%")
    print(f"Documented files: {report.documented_files}/{report.total_files}")


if __name__ == "__main__":
    main()
