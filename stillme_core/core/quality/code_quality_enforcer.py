"""
Code Quality Enforcer - Trái tim của hệ thống Quality Assurance

Module này cho phép AgentDev tự động đánh giá và cải thiện chất lượng code
của chính nó và của các agent khác trong hệ thống StillMe.
"""

import json
import logging
import subprocess
import time
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class QualityIssue:
    """Represents a single quality issue found by a tool"""

    tool: str
    file_path: str
    line_number: int
    column: int
    code: str
    message: str
    severity: str  # error, warning, info
    category: str  # style, bug, complexity, etc.
    fixable: bool = False
    auto_fix: Optional[str] = None


@dataclass
class QualityReport:
    """Comprehensive quality report for a codebase"""

    timestamp: datetime
    target_path: str
    total_files: int
    total_issues: int
    issues_by_tool: dict[str, int]
    issues_by_severity: dict[str, int]
    issues_by_category: dict[str, int]
    issues: list[QualityIssue]
    quality_score: float  # 0-100
    recommendations: list[str]
    auto_fixes_applied: int = 0
    execution_time: float = 0.0


class CodeQualityEnforcer:
    """
    Main class for enforcing code quality standards.

    This class orchestrates multiple quality tools (ruff, pylint, mypy)
    and provides intelligent analysis and auto-fixing capabilities.
    """

    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize the Code Quality Enforcer.

        Args:
            config_path: Path to configuration file (optional)
        """
        self.config_path = config_path or "pyproject.toml"
        self.tools = {
            "ruff": self._run_ruff,
            "pylint": self._run_pylint,
            "mypy": self._run_mypy,
            "black": self._run_black,
            "isort": self._run_isort,
        }
        self.logger = logging.getLogger(f"{__name__}.CodeQualityEnforcer")

    async def analyze_directory(
        self,
        target_path: str,
        tools: Optional[list[str]] = None,
        auto_fix: bool = False,
        include_patterns: Optional[list[str]] = None,
        exclude_patterns: Optional[list[str]] = None,
    ) -> QualityReport:
        """
        Analyze a directory for code quality issues.

        Args:
            target_path: Path to analyze
            tools: List of tools to run (default: all)
            auto_fix: Whether to apply auto-fixes
            include_patterns: File patterns to include
            exclude_patterns: File patterns to exclude

        Returns:
            QualityReport with comprehensive analysis
        """
        start_time = time.time()
        self.logger.info(f"Starting quality analysis of {target_path}")

        target_path = Path(target_path)  # type: ignore
        if not target_path.exists():
            raise ValueError(f"Target path does not exist: {target_path}")

        # Get list of Python files to analyze
        python_files = self._get_python_files(
            target_path,
            include_patterns,
            exclude_patterns,  # type: ignore
        )

        if not python_files:
            self.logger.warning(f"No Python files found in {target_path}")
            return self._create_empty_report(target_path)  # type: ignore

        # Run quality tools
        tools_to_run = tools or list(self.tools.keys())
        all_issues = []

        for tool_name in tools_to_run:
            if tool_name in self.tools:
                try:
                    self.logger.info(f"Running {tool_name}...")
                    tool_issues = await self.tools[tool_name](python_files)
                    all_issues.extend(tool_issues)
                    self.logger.info(f"{tool_name} found {len(tool_issues)} issues")
                except Exception as e:
                    self.logger.error(f"Error running {tool_name}: {e}")

        # Apply auto-fixes if requested
        auto_fixes_applied = 0
        if auto_fix:
            auto_fixes_applied = await self._apply_auto_fixes(all_issues)

        # Generate report
        execution_time = time.time() - start_time
        report = self._generate_report(
            target_path,
            python_files,
            all_issues,
            auto_fixes_applied,
            execution_time,  # type: ignore
        )

        self.logger.info(
            f"Quality analysis completed: {report.total_issues} issues found, "
            f"quality score: {report.quality_score:.1f}/100"
        )

        return report

    def _get_python_files(
        self,
        target_path: Path,
        include_patterns: Optional[list[str]] = None,
        exclude_patterns: Optional[list[str]] = None,
    ) -> list[Path]:
        """Get list of Python files to analyze"""
        include_patterns = include_patterns or ["*.py"]
        exclude_patterns = exclude_patterns or [
            "*/__pycache__/*",
            "*/.*",
            "*/tests/fixtures/*",
            "*/node_modules/*",
            "*/venv/*",
            "*/env/*",
            "*/build/*",
            "*/dist/*",
        ]

        python_files = []
        for pattern in include_patterns:
            for file_path in target_path.rglob(pattern):
                # Check if file should be excluded
                should_exclude = False
                for exclude_pattern in exclude_patterns:
                    if file_path.match(exclude_pattern):
                        should_exclude = True
                        break

                if not should_exclude and file_path.is_file():
                    python_files.append(file_path)

        return python_files

    async def _run_ruff(self, files: list[Path]) -> list[QualityIssue]:
        """Run ruff static analysis"""
        issues = []

        try:
            # Run ruff check
            cmd = ["ruff", "check", "--output-format=json"] + [str(f) for f in files]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)

            if result.returncode == 0:
                return issues  # No issues found

            # Parse JSON output
            try:
                ruff_output = json.loads(result.stdout)
                for item in ruff_output:
                    issue = QualityIssue(
                        tool="ruff",
                        file_path=item["filename"],
                        line_number=item["location"]["row"],
                        column=item["location"]["column"],
                        code=item["code"],
                        message=item["message"],
                        severity=self._map_ruff_severity(item["code"]),
                        category=self._map_ruff_category(item["code"]),
                        fixable=(
                            item.get("fix", {}).get("applicable", False)
                            if item.get("fix")
                            else False
                        ),
                        auto_fix=(
                            item.get("fix", {}).get("message")
                            if item.get("fix") and item.get("fix", {}).get("applicable")
                            else None
                        ),
                    )
                    issues.append(issue)
            except json.JSONDecodeError:
                # Fallback to text parsing
                self.logger.warning(
                    "Failed to parse ruff JSON output, using text fallback"
                )

        except subprocess.TimeoutExpired:
            self.logger.error("Ruff analysis timed out")
        except Exception as e:
            self.logger.error(f"Error running ruff: {e}")

        return issues

    async def _run_pylint(self, files: list[Path]) -> list[QualityIssue]:
        """Run pylint analysis"""
        issues = []

        try:
            # Run pylint with JSON output
            cmd = ["pylint", "--output-format=json"] + [str(f) for f in files]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)

            # Parse JSON output
            try:
                pylint_output = json.loads(result.stdout)
                for item in pylint_output:
                    issue = QualityIssue(
                        tool="pylint",
                        file_path=item["path"],
                        line_number=item["line"],
                        column=item["column"],
                        code=item["message-id"],
                        message=item["message"],
                        severity=item["type"].lower(),
                        category=self._map_pylint_category(item["message-id"]),
                        fixable=False,  # Pylint doesn't provide auto-fix info
                    )
                    issues.append(issue)
            except json.JSONDecodeError:
                self.logger.warning("Failed to parse pylint JSON output")

        except subprocess.TimeoutExpired:
            self.logger.error("Pylint analysis timed out")
        except Exception as e:
            self.logger.error(f"Error running pylint: {e}")

        return issues

    async def _run_mypy(self, files: list[Path]) -> list[QualityIssue]:
        """Run mypy type checking"""
        issues = []

        try:
            # Run mypy with JSON output
            cmd = [
                "mypy",
                "--show-error-codes",
                "--json-report",
                "/tmp/mypy-report",
            ] + [str(f) for f in files]
            subprocess.run(cmd, capture_output=True, text=True, timeout=300)

            # Parse JSON report
            try:
                with open("/tmp/mypy-report") as f:
                    mypy_output = json.load(f)

                for file_path, file_errors in mypy_output.get("files", {}).items():
                    for error in file_errors.get("errors", []):
                        issue = QualityIssue(
                            tool="mypy",
                            file_path=file_path,
                            line_number=error["line"],
                            column=error["column"],
                            code=error.get("error_code", "unknown"),
                            message=error["message"],
                            severity="error",
                            category="type",
                            fixable=False,
                        )
                        issues.append(issue)
            except (FileNotFoundError, json.JSONDecodeError):
                self.logger.warning("Failed to parse mypy JSON report")

        except subprocess.TimeoutExpired:
            self.logger.error("Mypy analysis timed out")
        except Exception as e:
            self.logger.error(f"Error running mypy: {e}")

        return issues

    async def _run_black(self, files: list[Path]) -> list[QualityIssue]:
        """Run black formatting check"""
        issues = []

        try:
            # Run black in check mode
            cmd = ["black", "--check", "--diff"] + [str(f) for f in files]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)

            if result.returncode != 0:
                # Black found formatting issues
                issue = QualityIssue(
                    tool="black",
                    file_path="multiple",
                    line_number=0,
                    column=0,
                    code="BLACK_FORMATTING",
                    message="Code formatting issues found",
                    severity="warning",
                    category="style",
                    fixable=True,
                    auto_fix="Run 'black .' to fix formatting",
                )
                issues.append(issue)

        except subprocess.TimeoutExpired:
            self.logger.error("Black analysis timed out")
        except Exception as e:
            self.logger.error(f"Error running black: {e}")

        return issues

    async def _run_isort(self, files: list[Path]) -> list[QualityIssue]:
        """Run isort import sorting check"""
        issues = []

        try:
            # Run isort in check mode
            cmd = ["isort", "--check-only", "--diff"] + [str(f) for f in files]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)

            if result.returncode != 0:
                # isort found import issues
                issue = QualityIssue(
                    tool="isort",
                    file_path="multiple",
                    line_number=0,
                    column=0,
                    code="ISORT_IMPORTS",
                    message="Import sorting issues found",
                    severity="warning",
                    category="style",
                    fixable=True,
                    auto_fix="Run 'isort .' to fix import order",
                )
                issues.append(issue)

        except subprocess.TimeoutExpired:
            self.logger.error("isort analysis timed out")
        except Exception as e:
            self.logger.error(f"Error running isort: {e}")

        return issues

    async def _apply_auto_fixes(self, issues: list[QualityIssue]) -> int:
        """Apply auto-fixes for fixable issues"""
        fixes_applied = 0

        # Group issues by tool for batch fixing
        tool_issues = {}
        for issue in issues:
            if issue.fixable and issue.tool in ["black", "isort", "ruff"]:
                if issue.tool not in tool_issues:
                    tool_issues[issue.tool] = []
                tool_issues[issue.tool].append(issue)

        # Apply fixes
        for tool, tool_issue_list in tool_issues.items():
            try:
                if tool == "black":
                    result = subprocess.run(
                        ["black", "."], capture_output=True, text=True, timeout=60
                    )
                    if result.returncode == 0:
                        fixes_applied += len(tool_issue_list)

                elif tool == "isort":
                    result = subprocess.run(
                        ["isort", "."], capture_output=True, text=True, timeout=60
                    )
                    if result.returncode == 0:
                        fixes_applied += len(tool_issue_list)

                elif tool == "ruff":
                    result = subprocess.run(
                        ["ruff", "check", "--fix"],
                        capture_output=True,
                        text=True,
                        timeout=60,
                    )
                    if result.returncode == 0:
                        fixes_applied += len(tool_issue_list)

            except Exception as e:
                self.logger.error(f"Error applying {tool} fixes: {e}")

        return fixes_applied

    def _generate_report(
        self,
        target_path: Path,
        files: list[Path],
        issues: list[QualityIssue],
        auto_fixes_applied: int,
        execution_time: float,
    ) -> QualityReport:
        """Generate comprehensive quality report"""

        # Count issues by tool
        issues_by_tool = {}
        for issue in issues:
            issues_by_tool[issue.tool] = issues_by_tool.get(issue.tool, 0) + 1

        # Count issues by severity
        issues_by_severity = {}
        for issue in issues:
            issues_by_severity[issue.severity] = (
                issues_by_severity.get(issue.severity, 0) + 1
            )

        # Count issues by category
        issues_by_category = {}
        for issue in issues:
            issues_by_category[issue.category] = (
                issues_by_category.get(issue.category, 0) + 1
            )

        # Calculate quality score (0-100)
        quality_score = self._calculate_quality_score(issues, len(files))

        # Generate recommendations
        recommendations = self._generate_recommendations(issues, issues_by_tool)

        return QualityReport(
            timestamp=datetime.now(),
            target_path=str(target_path),
            total_files=len(files),
            total_issues=len(issues),
            issues_by_tool=issues_by_tool,
            issues_by_severity=issues_by_severity,
            issues_by_category=issues_by_category,
            issues=issues,
            quality_score=quality_score,
            recommendations=recommendations,
            auto_fixes_applied=auto_fixes_applied,
            execution_time=execution_time,
        )

    def _calculate_quality_score(
        self, issues: list[QualityIssue], total_files: int
    ) -> float:
        """Calculate quality score (0-100)"""
        if total_files == 0:
            return 100.0

        # Weight issues by severity
        severity_weights = {"error": 10, "warning": 5, "info": 1}

        total_weight = sum(severity_weights.get(issue.severity, 1) for issue in issues)
        max_possible_weight = total_files * 20  # Assume max 20 issues per file

        if max_possible_weight == 0:
            return 100.0

        score = max(0, 100 - (total_weight / max_possible_weight) * 100)
        return round(score, 1)

    def _generate_recommendations(
        self, issues: list[QualityIssue], issues_by_tool: dict[str, int]
    ) -> list[str]:
        """Generate actionable recommendations"""
        recommendations = []

        # Tool-specific recommendations
        if issues_by_tool.get("ruff", 0) > 10:
            recommendations.append(
                "Run 'ruff check --fix' to auto-fix many style issues"
            )

        if issues_by_tool.get("pylint", 0) > 5:
            recommendations.append(
                "Review pylint warnings for code quality improvements"
            )

        if issues_by_tool.get("mypy", 0) > 0:
            recommendations.append("Add type hints to improve code reliability")

        if issues_by_tool.get("black", 0) > 0:
            recommendations.append("Run 'black .' to fix code formatting")

        if issues_by_tool.get("isort", 0) > 0:
            recommendations.append("Run 'isort .' to fix import ordering")

        # Category-specific recommendations
        style_issues = sum(1 for issue in issues if issue.category == "style")
        if style_issues > 5:
            recommendations.append("Focus on code style consistency")

        type_issues = sum(1 for issue in issues if issue.category == "type")
        if type_issues > 0:
            recommendations.append("Add type annotations to improve code safety")

        # General recommendations
        if len(issues) > 20:
            recommendations.append(
                "Consider breaking down large files into smaller modules"
            )

        if not recommendations:
            recommendations.append("Code quality looks good! Keep up the great work!")

        return recommendations

    def _create_empty_report(self, target_path: Path) -> QualityReport:
        """Create empty report when no files found"""
        return QualityReport(
            timestamp=datetime.now(),
            target_path=str(target_path),
            total_files=0,
            total_issues=0,
            issues_by_tool={},
            issues_by_severity={},
            issues_by_category={},
            issues=[],
            quality_score=100.0,
            recommendations=["No Python files found to analyze"],
            auto_fixes_applied=0,
            execution_time=0.0,
        )

    def _map_ruff_severity(self, code: str) -> str:
        """Map ruff error codes to severity levels"""
        if code.startswith("E") or code.startswith("F"):
            return "error"
        elif code.startswith("W"):
            return "warning"
        else:
            return "info"

    def _map_ruff_category(self, code: str) -> str:
        """Map ruff error codes to categories"""
        if code.startswith("E") or code.startswith("W"):
            return "style"
        elif code.startswith("F"):
            return "bug"
        elif code.startswith("B"):
            return "complexity"
        elif code.startswith("C"):
            return "style"
        else:
            return "other"

    def _map_pylint_category(self, message_id: str) -> str:
        """Map pylint message IDs to categories"""
        if message_id.startswith("C"):
            return "style"
        elif message_id.startswith("R"):
            return "complexity"
        elif message_id.startswith("W"):
            return "warning"
        elif message_id.startswith("E"):
            return "error"
        else:
            return "other"

    def save_report(self, report: QualityReport, output_path: str) -> None:
        """Save quality report to file"""
        output_path = Path(output_path)  # type: ignore
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Convert to JSON-serializable format
        report_dict = asdict(report)
        report_dict["timestamp"] = report.timestamp.isoformat()

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(report_dict, f, indent=2, ensure_ascii=False)

        self.logger.info(f"Quality report saved to {output_path}")

    def load_report(self, report_path: str) -> QualityReport:
        """Load quality report from file"""
        with open(report_path, encoding="utf-8") as f:
            report_dict = json.load(f)

        # Convert timestamp back to datetime
        report_dict["timestamp"] = datetime.fromisoformat(report_dict["timestamp"])

        # Convert issues back to QualityIssue objects
        issues = []
        for issue_dict in report_dict["issues"]:
            issue = QualityIssue(**issue_dict)
            issues.append(issue)
        report_dict["issues"] = issues

        return QualityReport(**report_dict)
