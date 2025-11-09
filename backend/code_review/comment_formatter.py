"""
Comment Formatter - Formats code issues into readable PR comments
"""

import logging
from typing import List
from collections import defaultdict

from .analyzer import CodeIssue

logger = logging.getLogger(__name__)


class CommentFormatter:
    """Formats code issues into GitHub PR comments"""

    def __init__(self):
        logger.info("CommentFormatter initialized")

    def format_issues(self, issues: List[CodeIssue]) -> List[str]:
        """
        Format issues into PR comments

        Args:
            issues: List of CodeIssue objects

        Returns:
            List of formatted comment strings
        """
        if not issues:
            return []

        # Group issues by file
        issues_by_file = defaultdict(list)
        for issue in issues:
            issues_by_file[issue.file_path].append(issue)

        comments: List[str] = []

        # Create one comment per file (or group small files)
        for file_path, file_issues in issues_by_file.items():
            comment = self._format_file_issues(file_path, file_issues)
            if comment:
                comments.append(comment)

        return comments

    def _format_file_issues(self, file_path: str, issues: List[CodeIssue]) -> str:
        """Format issues for a single file"""
        if not issues:
            return ""

        # Header
        lines = [
            f"## 📝 Code Review: `{file_path}`",
            "",
            f"Found **{len(issues)}** issue(s):",
            "",
        ]

        # Group by severity
        errors = [i for i in issues if i.severity == "error"]
        warnings = [i for i in issues if i.severity == "warning"]
        infos = [i for i in issues if i.severity == "info"]

        # Format errors
        if errors:
            lines.append("### 🔴 Errors")
            lines.append("")
            for issue in errors[:10]:  # Limit to 10 per category
                lines.append(self._format_single_issue(issue))
            if len(errors) > 10:
                lines.append(f"*... and {len(errors) - 10} more error(s)*")
            lines.append("")

        # Format warnings
        if warnings:
            lines.append("### 🟡 Warnings")
            lines.append("")
            for issue in warnings[:10]:
                lines.append(self._format_single_issue(issue))
            if len(warnings) > 10:
                lines.append(f"*... and {len(warnings) - 10} more warning(s)*")
            lines.append("")

        # Format infos (only if no errors/warnings)
        if infos and not errors and not warnings:
            lines.append("### ℹ️ Suggestions")
            lines.append("")
            for issue in infos[:5]:
                lines.append(self._format_single_issue(issue))
            if len(infos) > 5:
                lines.append(f"*... and {len(infos) - 5} more suggestion(s)*")
            lines.append("")

        # Footer
        lines.extend(
            [
                "---",
                "",
                "💡 **Tips:**",
                "- Run `ruff check . --fix` to auto-fix some issues",
                "- Run `ruff format .` to format your code",
                "- See [CONTRIBUTING.md](CONTRIBUTING.md) for more guidance",
                "",
                "*This is an automated code review. These are suggestions to help improve code quality.*",
            ]
        )

        return "\n".join(lines)

    def _format_single_issue(self, issue: CodeIssue) -> str:
        """Format a single issue"""
        # Line reference
        line_ref = f"L{issue.line}"
        if issue.column:
            line_ref += f":{issue.column}"

        # Severity emoji
        severity_emoji = {"error": "🔴", "warning": "🟡", "info": "ℹ️"}.get(
            issue.severity, "•"
        )

        # Fixable indicator
        fixable_text = " (auto-fixable)" if issue.fixable else ""

        # Format
        lines = [
            f"{severity_emoji} **{line_ref}** - `{issue.rule}`{fixable_text}",
            f"   {issue.message}",
        ]

        return "\n".join(lines)

    def format_summary_comment(self, total_issues: int, files_affected: int) -> str:
        """Format a summary comment"""
        if total_issues == 0:
            return (
                "## ✅ Code Review Summary\n\n"
                "🎉 Great job! No code quality issues found.\n\n"
                "*This is an automated code review.*"
            )

        lines = [
            "## 📊 Code Review Summary",
            "",
            f"Found **{total_issues}** issue(s) across **{files_affected}** file(s).",
            "",
            "💡 **Next steps:**",
            "- Review the file-specific comments above",
            "- Fix errors first (🔴), then warnings (🟡)",
            "- Run `ruff check . --fix` to auto-fix some issues",
            "",
            "*This is an automated code review to help improve code quality.*",
        ]

        return "\n".join(lines)
