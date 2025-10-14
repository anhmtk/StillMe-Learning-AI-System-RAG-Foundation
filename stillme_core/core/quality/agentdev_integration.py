"""
AgentDev Quality Integration

Integration layer that connects CodeQualityEnforcer, QualityMetrics, and AutoFixer
into AgentDev's workflow for automated code quality management.
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from stillme_core.quality.auto_fixer import AutoFixer
from stillme_core.quality.code_quality_enforcer import (
    CodeQualityEnforcer,
    QualityReport,
)
from stillme_core.quality.quality_metrics import QualityMetrics


class AgentDevQualityIntegration:
    """
    Integration layer for AgentDev quality management.

    This class provides high-level functions to integrate code quality tools
    into AgentDev's workflow, including analysis, fixing, monitoring, and reporting.
    """

    def __init__(self, metrics_db_path: str = "quality_metrics.db"):
        """
        Initialize the quality integration.

        Args:
            metrics_db_path: Path to SQLite database for storing quality metrics
        """
        self.enforcer = CodeQualityEnforcer()
        self.metrics = QualityMetrics(metrics_db_path)
        self.auto_fixer = AutoFixer(create_backups=True)
        self.logger = logging.getLogger(__name__)

    async def analyze_and_fix(
        self,
        target_path: str,
        auto_fix: bool = True,
        tools: list[str] | None = None,
        save_metrics: bool = True,
    ) -> dict[str, Any]:
        """
        Analyze code quality and optionally apply fixes.

        Args:
            target_path: Path to analyze
            auto_fix: Whether to apply automatic fixes
            tools: List of tools to run (default: all)
            save_metrics: Whether to save results to metrics database

        Returns:
            Dictionary with analysis results and quality assessment
        """
        try:
            self.logger.info(f"Starting quality analysis for: {target_path}")

            # Run quality analysis
            report = await self.enforcer.analyze_directory(
                target_path=target_path, tools=tools, auto_fix=auto_fix
            )

            # Save metrics if requested
            if save_metrics:
                self.metrics.store_report(report)

            # Determine quality level
            quality_level = self._assess_quality_level(report.quality_score)

            # Generate recommendations
            recommendations = self._generate_quality_recommendations(report)

            result = {
                "status": "success",
                "analysis": {
                    "quality_score": report.quality_score,
                    "total_files": report.total_files,
                    "total_issues": report.total_issues,
                    "issues_by_tool": report.issues_by_tool,
                    "issues_by_severity": report.issues_by_severity,
                    "execution_time": report.execution_time,
                    "auto_fixes_applied": report.auto_fixes_applied,
                },
                "quality_level": quality_level,
                "recommendations": recommendations,
                "timestamp": report.timestamp,
            }

            self.logger.info(
                f"Quality analysis completed. Score: {report.quality_score}"
            )
            return result

        except Exception as e:
            self.logger.error(f"Quality analysis failed: {e!s}")
            return {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
            }

    async def pre_commit_quality_check(
        self,
        target_path: str,
        min_quality_score: float = 80.0,
        max_issues_per_file: float = 2.0,
    ) -> dict[str, Any]:
        """
        Run pre-commit quality check with configurable thresholds.

        Args:
            target_path: Path to check
            min_quality_score: Minimum acceptable quality score
            max_issues_per_file: Maximum acceptable issues per file

        Returns:
            Dictionary with check results and pass/fail status
        """
        try:
            self.logger.info(f"Running pre-commit quality check for: {target_path}")

            # Run analysis without auto-fix for pre-commit
            report = await self.enforcer.analyze_directory(
                target_path=target_path, auto_fix=False
            )

            # Calculate issues per file
            issues_per_file = (
                report.total_issues / report.total_files
                if report.total_files > 0
                else 0
            )

            # Check thresholds
            quality_pass = report.quality_score >= min_quality_score
            issues_pass = issues_per_file <= max_issues_per_file

            passed = quality_pass and issues_pass

            result = {
                "status": "success",
                "passed": passed,
                "quality_score": report.quality_score,
                "issues_per_file": issues_per_file,
                "total_issues": report.total_issues,
                "total_files": report.total_files,
                "thresholds": {
                    "min_quality_score": min_quality_score,
                    "max_issues_per_file": max_issues_per_file,
                },
                "checks": {
                    "quality_score_pass": quality_pass,
                    "issues_per_file_pass": issues_pass,
                },
                "recommendations": report.recommendations,
                "timestamp": report.timestamp,
            }

            if not passed:
                self.logger.warning(
                    f"Pre-commit check failed. Score: {report.quality_score}"
                )
            else:
                self.logger.info(
                    f"Pre-commit check passed. Score: {report.quality_score}"
                )

            return result

        except Exception as e:
            self.logger.error(f"Pre-commit check failed: {e!s}")
            return {
                "status": "error",
                "error": str(e),
                "passed": False,
                "timestamp": datetime.now().isoformat(),
            }

    async def continuous_quality_monitoring(
        self, target_path: str, check_interval: int = 3600
    ) -> dict[str, Any]:
        """
        Set up continuous quality monitoring (placeholder for future implementation).

        Args:
            target_path: Path to monitor
            check_interval: Check interval in seconds

        Returns:
            Dictionary with monitoring setup status
        """
        # This is a placeholder for future continuous monitoring implementation
        # Could integrate with file watchers, CI/CD systems, or scheduled tasks

        return {
            "status": "info",
            "message": "Continuous monitoring not yet implemented",
            "target_path": target_path,
            "check_interval": check_interval,
            "timestamp": datetime.now().isoformat(),
        }

    async def run_quality_workflow(
        self, target_path: str, workflow_type: str = "full"
    ) -> dict[str, Any]:
        """
        Run a complete quality workflow.

        Args:
            target_path: Path to analyze
            workflow_type: Type of workflow ("quick", "full", "pre-commit")

        Returns:
            Dictionary with workflow results
        """
        try:
            self.logger.info(
                f"Starting {workflow_type} quality workflow for: {target_path}"
            )

            if workflow_type == "quick":
                # Quick analysis with basic tools
                tools = ["ruff"]
                auto_fix = True

            elif workflow_type == "pre-commit":
                # Pre-commit check without auto-fix
                tools = ["ruff", "pylint"]
                auto_fix = False

            else:  # full
                # Full analysis with all tools
                tools = None  # Use all tools
                auto_fix = True

            # Run analysis
            result = await self.analyze_and_fix(
                target_path=target_path,
                auto_fix=auto_fix,
                tools=tools,
                save_metrics=True,
            )

            # Add workflow metadata
            result["workflow_type"] = workflow_type
            result["workflow_completed"] = True

            self.logger.info(f"Quality workflow completed: {workflow_type}")
            return result

        except Exception as e:
            self.logger.error(f"Quality workflow failed: {e!s}")
            return {
                "status": "error",
                "error": str(e),
                "workflow_type": workflow_type,
                "workflow_completed": False,
                "timestamp": datetime.now().isoformat(),
            }

    def get_quality_dashboard(self, target_path: str) -> dict[str, Any]:
        """
        Get quality dashboard data for a target path.

        Args:
            target_path: Path to get dashboard data for

        Returns:
            Dictionary with dashboard data including trends, summary, and comparison
        """
        try:
            # Get recent trends
            trends = self.metrics.get_quality_trends(target_path, days=30)

            # Get current summary
            summary = self.metrics.get_quality_summary(target_path, days=7)

            # Get comparison with baseline
            comparison = self.metrics.get_comparison_report(
                target_path, baseline_days=30, current_days=7
            )

            # Get benchmarks (placeholder)
            benchmarks = self._get_quality_benchmarks()

            return {
                "status": "success",
                "target_path": target_path,
                "trends": trends,
                "summary": summary,
                "comparison": comparison,
                "benchmarks": benchmarks,
                "timestamp": datetime.now().isoformat(),
            }

        except Exception as e:
            self.logger.error(f"Failed to get dashboard data: {e!s}")
            return {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
            }

    def export_quality_report(
        self, target_path: str, output_path: str, days: int = 30
    ) -> dict[str, Any]:
        """
        Export quality report to file.

        Args:
            target_path: Path to export data for
            output_path: Output file path
            days: Number of days to include

        Returns:
            Dictionary with export status
        """
        try:
            # Get reports for the specified period
            reports = self.metrics.get_reports()

            # Filter by target path and date range
            cutoff_date = datetime.now() - timedelta(days=days)
            filtered_reports = [
                r
                for r in reports
                if r.target_path == target_path
                and datetime.fromisoformat(
                    r.timestamp.isoformat()
                    if hasattr(r.timestamp, "isoformat")
                    else str(r.timestamp)
                )
                >= cutoff_date
            ]

            # Prepare export data
            export_data = {
                "target_path": target_path,
                "export_date": datetime.now().isoformat(),
                "days_included": days,
                "reports_count": len(filtered_reports),
                "reports": [
                    {
                        "timestamp": r.timestamp,
                        "quality_score": r.quality_score,
                        "total_files": r.total_files,
                        "total_issues": r.total_issues,
                        "issues_by_tool": r.issues_by_tool,
                        "issues_by_severity": r.issues_by_severity,
                        "recommendations": r.recommendations,
                    }
                    for r in filtered_reports
                ],
            }

            # Write to file
            output_file = Path(output_path)
            output_file.parent.mkdir(parents=True, exist_ok=True)

            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)

            return {
                "status": "success",
                "output_path": str(output_file),
                "reports_exported": len(filtered_reports),
                "timestamp": datetime.now().isoformat(),
            }

        except Exception as e:
            self.logger.error(f"Failed to export quality report: {e!s}")
            return {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
            }

    def _assess_quality_level(self, quality_score: float) -> str:
        """Assess quality level based on score."""
        if quality_score >= 90:
            return "excellent"
        elif quality_score >= 80:
            return "good"
        elif quality_score >= 70:
            return "fair"
        elif quality_score >= 60:
            return "poor"
        else:
            return "critical"

    def _generate_quality_recommendations(self, report: QualityReport) -> list[str]:
        """Generate quality recommendations based on report."""
        recommendations = []

        if report.quality_score < 80:
            recommendations.append(
                "Consider running auto-fixes to improve code quality"
            )

        if report.issues_by_severity.get("error", 0) > 0:
            recommendations.append("Address critical errors immediately")

        if report.issues_by_tool.get("pylint", 0) > 5:
            recommendations.append("Review pylint warnings for code improvements")

        if report.issues_by_tool.get("mypy", 0) > 0:
            recommendations.append("Add type hints to improve code clarity")

        if not recommendations:
            recommendations.append("Code quality is good, maintain current standards")

        return recommendations

    def _get_quality_benchmarks(self) -> dict[str, Any]:
        """Get quality benchmarks (placeholder implementation)."""
        return {
            "industry_standard": {
                "min_quality_score": 80.0,
                "max_issues_per_file": 2.0,
                "max_cyclomatic_complexity": 10,
            },
            "excellent": {
                "min_quality_score": 95.0,
                "max_issues_per_file": 0.5,
                "max_cyclomatic_complexity": 5,
            },
        }


# Convenience functions for direct use
async def run_agentdev_quality_check(
    target_path: str, workflow_type: str = "full"
) -> dict[str, Any]:
    """
    Convenience function to run AgentDev quality check.

    Args:
        target_path: Path to analyze
        workflow_type: Type of workflow to run

    Returns:
        Dictionary with quality check results
    """
    integration = AgentDevQualityIntegration()
    return await integration.run_quality_workflow(target_path, workflow_type)


async def run_pre_commit_check(
    target_path: str, min_quality_score: float = 80.0
) -> dict[str, Any]:
    """
    Convenience function to run pre-commit quality check.

    Args:
        target_path: Path to check
        min_quality_score: Minimum acceptable quality score

    Returns:
        Dictionary with pre-commit check results
    """
    integration = AgentDevQualityIntegration()
    return await integration.pre_commit_quality_check(
        target_path, min_quality_score=min_quality_score
    )


if __name__ == "__main__":
    # Example usage
    async def main():
        # Test the integration
        integration = AgentDevQualityIntegration()

        # Run quality analysis on current directory
        result = await integration.run_quality_workflow(".", "quick")
        print(json.dumps(result, indent=2))

    asyncio.run(main())