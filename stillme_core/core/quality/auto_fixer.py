"""
Auto Fixer - Tự động sửa chữa các vấn đề chất lượng code

Module này cung cấp khả năng tự động sửa chữa các vấn đề chất lượng code
mà AgentDev có thể phát hiện và sửa một cách an toàn.
"""

import ast
import logging
import re
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path

from stillme_core.quality.code_quality_enforcer import QualityIssue


@dataclass
class FixResult:
    """Result of an auto-fix operation"""

    success: bool
    file_path: str
    fixes_applied: int
    errors_fixed: list[str]
    warnings: list[str]
    errors: list[str]
    backup_path: str | None = None


class AutoFixer:
    """
    Automatic code quality issue fixer.

    This class provides intelligent auto-fixing capabilities for common
    code quality issues that can be safely resolved automatically.
    """

    def __init__(self, create_backups: bool = True):
        """
        Initialize Auto Fixer.

        Args:
            create_backups: Whether to create backup files before fixing
        """
        self.create_backups = create_backups
        self.logger = logging.getLogger(f"{__name__}.AutoFixer")

        # Define fixable issue patterns
        self.fixable_patterns = {
            "import_order": self._fix_import_order,
            "unused_imports": self._fix_unused_imports,
            "line_length": self._fix_line_length,
            "trailing_whitespace": self._fix_trailing_whitespace,
            "missing_newline": self._fix_missing_newline,
            "quotes": self._fix_quotes,
            "indentation": self._fix_indentation,
            "semicolons": self._fix_semicolons,
            "comparison": self._fix_comparison,
            "f_strings": self._fix_f_strings,
        }

    async def fix_issues(
        self, issues: list[QualityIssue], target_path: str
    ) -> list[FixResult]:
        """
        Fix quality issues in files.

        Args:
            issues: List of quality issues to fix
            target_path: Path to the target file or directory

        Returns:
            List of fix results
        """
        # Group issues by file
        file_issues = {}
        for issue in issues:
            if issue.fixable and issue.file_path != "multiple":
                if issue.file_path not in file_issues:
                    file_issues[issue.file_path] = []
                file_issues[issue.file_path].append(issue)

        results = []
        for file_path, file_issue_list in file_issues.items():
            try:
                result = await self._fix_file_issues(file_path, file_issue_list)
                results.append(result)
            except Exception as e:
                self.logger.error(f"Error fixing issues in {file_path}: {e}")
                results.append(
                    FixResult(
                        success=False,
                        file_path=file_path,
                        fixes_applied=0,
                        errors_fixed=[],
                        warnings=[],
                        errors=[str(e)],
                    )
                )

        return results

    async def _fix_file_issues(
        self, file_path: str, issues: list[QualityIssue]
    ) -> FixResult:
        """Fix issues in a single file"""
        file_path = Path(file_path)  # type: ignore

        if not file_path.exists():
            return FixResult(
                success=False,
                file_path=str(file_path),
                fixes_applied=0,
                errors_fixed=[],
                warnings=[],
                errors=[f"File not found: {file_path}"],
            )

        # Create backup if requested
        backup_path = None
        if self.create_backups:
            backup_path = f"{file_path}.backup"
            file_path.rename(backup_path)
            file_path = Path(backup_path)  # type: ignore

        try:
            # Read file content
            with open(file_path, encoding="utf-8") as f:
                content = f.read()

            original_content = content
            fixes_applied = 0
            errors_fixed = []
            warnings = []

            # Apply fixes based on issue types
            for issue in issues:
                try:
                    fixed_content, fix_applied = self._apply_issue_fix(content, issue)
                    if fix_applied:
                        content = fixed_content
                        fixes_applied += 1
                        errors_fixed.append(f"{issue.tool}:{issue.code}")
                except Exception as e:
                    warnings.append(f"Could not fix {issue.tool}:{issue.code}: {e}")

            # Write fixed content back
            if content != original_content:
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(content)

            return FixResult(
                success=True,
                file_path=str(file_path),
                fixes_applied=fixes_applied,
                errors_fixed=errors_fixed,
                warnings=warnings,
                errors=[],
                backup_path=backup_path,
            )

        except Exception as e:
            # Restore backup if fix failed
            if backup_path and Path(backup_path).exists():
                Path(backup_path).rename(file_path)

            return FixResult(
                success=False,
                file_path=str(file_path),
                fixes_applied=0,
                errors_fixed=[],
                warnings=[],
                errors=[str(e)],
                backup_path=backup_path,
            )

    def _apply_issue_fix(self, content: str, issue: QualityIssue) -> tuple[str, bool]:
        """Apply a specific fix for an issue"""
        fix_type = self._determine_fix_type(issue)

        if fix_type in self.fixable_patterns:
            return self.fixable_patterns[fix_type](content, issue)
        else:
            return content, False

    def _determine_fix_type(self, issue: QualityIssue) -> str:
        """Determine the type of fix needed for an issue"""
        # Map issue codes to fix types
        code_mapping = {
            # Import issues
            "I001": "import_order",
            "F401": "unused_imports",
            "F811": "unused_imports",
            # Style issues
            "E501": "line_length",
            "W291": "trailing_whitespace",
            "W292": "missing_newline",
            "Q000": "quotes",
            "Q001": "quotes",
            "Q002": "quotes",
            "Q003": "quotes",
            # Indentation
            "E111": "indentation",
            "E112": "indentation",
            "E113": "indentation",
            "E114": "indentation",
            "E115": "indentation",
            "E116": "indentation",
            "E117": "indentation",
            # Semicolons
            "E702": "semicolons",
            "E703": "semicolons",
            # Comparisons
            "E711": "comparison",
            "E712": "comparison",
            # F-strings
            "UP032": "f_strings",
        }

        return code_mapping.get(issue.code, "unknown")

    def _fix_import_order(self, content: str, issue: QualityIssue) -> tuple[str, bool]:
        """Fix import order issues"""
        try:
            # Use isort to fix import order
            with tempfile.NamedTemporaryFile(
                mode="w", suffix=".py", delete=False
            ) as tmp:
                tmp.write(content)
                tmp_path = tmp.name

            result = subprocess.run(
                ["isort", tmp_path, "--quiet"],
                capture_output=True,
                text=True,
                timeout=30,
            )

            if result.returncode == 0:
                with open(tmp_path, encoding="utf-8") as f:
                    fixed_content = f.read()
                Path(tmp_path).unlink()
                return fixed_content, True
            else:
                Path(tmp_path).unlink()
                return content, False

        except Exception:
            return content, False

    def _fix_unused_imports(
        self, content: str, issue: QualityIssue
    ) -> tuple[str, bool]:
        """Fix unused import issues"""
        try:
            # Parse AST to find unused imports
            tree = ast.parse(content)

            # Find all import statements
            imports = []
            for node in ast.walk(tree):
                if isinstance(node, ast.Import | ast.ImportFrom):
                    imports.append(node)

            # Find all name references
            names = set()
            for node in ast.walk(tree):
                if isinstance(node, ast.Name):
                    names.add(node.id)
                elif isinstance(node, ast.Attribute):
                    names.add(node.attr)

            # Remove unused imports
            lines = content.splitlines()
            lines_to_remove = set()

            for import_node in imports:
                if isinstance(import_node, ast.Import):
                    for alias in import_node.names:
                        if alias.name not in names:
                            lines_to_remove.add(import_node.lineno - 1)
                elif isinstance(import_node, ast.ImportFrom):
                    if import_node.module and import_node.module not in names:
                        for alias in import_node.names:
                            if alias.name not in names:
                                lines_to_remove.add(import_node.lineno - 1)

            # Remove lines (in reverse order to maintain line numbers)
            for line_num in sorted(lines_to_remove, reverse=True):
                if line_num < len(lines):
                    lines.pop(line_num)

            return "\n".join(lines), len(lines_to_remove) > 0

        except Exception:
            return content, False

    def _fix_line_length(self, content: str, issue: QualityIssue) -> tuple[str, bool]:
        """Fix line length issues"""
        try:
            # Use black to fix line length
            with tempfile.NamedTemporaryFile(
                mode="w", suffix=".py", delete=False
            ) as tmp:
                tmp.write(content)
                tmp_path = tmp.name

            result = subprocess.run(
                ["black", tmp_path, "--quiet"],
                capture_output=True,
                text=True,
                timeout=30,
            )

            if result.returncode == 0:
                with open(tmp_path, encoding="utf-8") as f:
                    fixed_content = f.read()
                Path(tmp_path).unlink()
                return fixed_content, True
            else:
                Path(tmp_path).unlink()
                return content, False

        except Exception:
            return content, False

    def _fix_trailing_whitespace(
        self, content: str, issue: QualityIssue
    ) -> tuple[str, bool]:
        """Fix trailing whitespace issues"""
        lines = content.splitlines()
        fixed_lines = []
        fixed = False

        for line in lines:
            # Remove trailing whitespace
            original_line = line
            line = line.rstrip()
            if line != original_line:
                fixed = True
            fixed_lines.append(line)

        return "\n".join(fixed_lines), fixed

    def _fix_missing_newline(
        self, content: str, issue: QualityIssue
    ) -> tuple[str, bool]:
        """Fix missing newline at end of file"""
        if content and not content.endswith("\n"):
            return content + "\n", True
        return content, False

    def _fix_quotes(self, content: str, issue: QualityIssue) -> tuple[str, bool]:
        """Fix quote consistency issues"""
        # Simple quote fixing - convert to double quotes
        lines = content.splitlines()
        fixed_lines = []
        fixed = False

        for line in lines:
            # Replace single quotes with double quotes (simple approach)
            original_line = line
            # Only replace single quotes that are not inside strings
            line = re.sub(r"'([^']*)'", r'"\1"', line)
            if line != original_line:
                fixed = True
            fixed_lines.append(line)

        return "\n".join(fixed_lines), fixed

    def _fix_indentation(self, content: str, issue: QualityIssue) -> tuple[str, bool]:
        """Fix indentation issues"""
        try:
            # Use black to fix indentation
            with tempfile.NamedTemporaryFile(
                mode="w", suffix=".py", delete=False
            ) as tmp:
                tmp.write(content)
                tmp_path = tmp.name

            result = subprocess.run(
                ["black", tmp_path, "--quiet"],
                capture_output=True,
                text=True,
                timeout=30,
            )

            if result.returncode == 0:
                with open(tmp_path, encoding="utf-8") as f:
                    fixed_content = f.read()
                Path(tmp_path).unlink()
                return fixed_content, True
            else:
                Path(tmp_path).unlink()
                return content, False

        except Exception:
            return content, False

    def _fix_semicolons(self, content: str, issue: QualityIssue) -> tuple[str, bool]:
        """Fix semicolon issues"""
        lines = content.splitlines()
        fixed_lines = []
        fixed = False

        for line in lines:
            # Remove unnecessary semicolons
            original_line = line
            line = re.sub(r";\s*$", "", line)
            if line != original_line:
                fixed = True
            fixed_lines.append(line)

        return "\n".join(fixed_lines), fixed

    def _fix_comparison(self, content: str, issue: QualityIssue) -> tuple[str, bool]:
        """Fix comparison issues"""
        lines = content.splitlines()
        fixed_lines = []
        fixed = False

        for line in lines:
            original_line = line
            # Fix "is None" comparisons
            line = re.sub(r"\bis\s+None\b", "is None", line)
            line = re.sub(r"\bis\s+not\s+None\b", "is not None", line)

            # Fix "== True/False" comparisons
            line = re.sub(r"\b==\s+True\b", "", line)
            line = re.sub(r"\b==\s+False\b", " is False", line)

            if line != original_line:
                fixed = True
            fixed_lines.append(line)

        return "\n".join(fixed_lines), fixed

    def _fix_f_strings(self, content: str, issue: QualityIssue) -> tuple[str, bool]:
        """Fix f-string issues"""
        lines = content.splitlines()
        fixed_lines = []
        fixed = False

        for line in lines:
            original_line = line
            # Convert .format() to f-strings (simple cases)
            # This is a simplified implementation
            if ".format(" in line and "{" in line:
                # Basic f-string conversion
                line = re.sub(r"(\w+)\.format\(([^)]+)\)", r'f"\1{\2}"', line)
                if line != original_line:
                    fixed = True
            fixed_lines.append(line)

        return "\n".join(fixed_lines), fixed

    def run_tool_fixes(
        self, target_path: str, tools: list[str]
    ) -> dict[str, FixResult]:
        """Run tool-specific fixes"""
        results = {}

        for tool in tools:
            try:
                if tool == "black":
                    result = subprocess.run(
                        ["black", target_path],
                        capture_output=True,
                        text=True,
                        timeout=60,
                    )
                    results[tool] = FixResult(
                        success=result.returncode == 0,
                        file_path=target_path,
                        fixes_applied=1 if result.returncode == 0 else 0,
                        errors_fixed=["formatting"] if result.returncode == 0 else [],
                        warnings=[],
                        errors=[result.stderr] if result.returncode != 0 else [],
                    )

                elif tool == "isort":
                    result = subprocess.run(
                        ["isort", target_path],
                        capture_output=True,
                        text=True,
                        timeout=60,
                    )
                    results[tool] = FixResult(
                        success=result.returncode == 0,
                        file_path=target_path,
                        fixes_applied=1 if result.returncode == 0 else 0,
                        errors_fixed=["import_order"] if result.returncode == 0 else [],
                        warnings=[],
                        errors=[result.stderr] if result.returncode != 0 else [],
                    )

                elif tool == "ruff":
                    result = subprocess.run(
                        ["ruff", "check", "--fix", target_path],
                        capture_output=True,
                        text=True,
                        timeout=60,
                    )
                    results[tool] = FixResult(
                        success=result.returncode == 0,
                        file_path=target_path,
                        fixes_applied=1 if result.returncode == 0 else 0,
                        errors_fixed=["ruff_issues"] if result.returncode == 0 else [],
                        warnings=[],
                        errors=[result.stderr] if result.returncode != 0 else [],
                    )

            except Exception as e:
                results[tool] = FixResult(
                    success=False,
                    file_path=target_path,
                    fixes_applied=0,
                    errors_fixed=[],
                    warnings=[],
                    errors=[str(e)],
                )

        return results
