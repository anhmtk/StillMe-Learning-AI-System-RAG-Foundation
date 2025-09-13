"""
Quality Metrics - Theo dõi và phân tích xu hướng chất lượng code

Module này cung cấp khả năng theo dõi và phân tích xu hướng chất lượng code
theo thời gian, giúp AgentDev đưa ra quyết định chiến lược về chất lượng.
"""

import json
import sqlite3
import statistics
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

from stillme_core.quality.code_quality_enforcer import QualityIssue, QualityReport


@dataclass
class QualityTrend:
    """Represents quality trend over time"""

    period_start: datetime
    period_end: datetime
    quality_score: float
    total_issues: int
    issues_by_severity: Dict[str, int]
    issues_by_tool: Dict[str, int]
    files_analyzed: int
    auto_fixes_applied: int


@dataclass
class QualityBenchmark:
    """Quality benchmark for comparison"""

    name: str
    quality_score: float
    max_issues_per_file: float
    max_errors_per_file: float
    max_warnings_per_file: float
    description: str


class QualityMetrics:
    """
    Quality metrics tracking and analysis.

    This class provides comprehensive quality metrics tracking,
    trend analysis, and benchmarking capabilities.
    """

    def __init__(self, db_path: str = "quality_metrics.db"):
        """
        Initialize Quality Metrics.

        Args:
            db_path: Path to SQLite database for storing metrics
        """
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_database()

        # Default benchmarks
        self.benchmarks = {
            "excellent": QualityBenchmark(
                name="excellent",
                quality_score=95.0,
                max_issues_per_file=0.5,
                max_errors_per_file=0.0,
                max_warnings_per_file=0.2,
                description="Excellent code quality - production ready",
            ),
            "good": QualityBenchmark(
                name="good",
                quality_score=85.0,
                max_issues_per_file=1.0,
                max_errors_per_file=0.1,
                max_warnings_per_file=0.5,
                description="Good code quality - minor improvements needed",
            ),
            "acceptable": QualityBenchmark(
                name="acceptable",
                quality_score=75.0,
                max_issues_per_file=2.0,
                max_errors_per_file=0.3,
                max_warnings_per_file=1.0,
                description="Acceptable code quality - improvements recommended",
            ),
            "needs_work": QualityBenchmark(
                name="needs_work",
                quality_score=60.0,
                max_issues_per_file=5.0,
                max_errors_per_file=1.0,
                max_warnings_per_file=2.0,
                description="Code quality needs improvement",
            ),
        }

    def _init_database(self) -> None:
        """Initialize SQLite database for metrics storage"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS quality_reports (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    target_path TEXT NOT NULL,
                    quality_score REAL NOT NULL,
                    total_issues INTEGER NOT NULL,
                    total_files INTEGER NOT NULL,
                    issues_by_tool TEXT NOT NULL,
                    issues_by_severity TEXT NOT NULL,
                    issues_by_category TEXT NOT NULL,
                    auto_fixes_applied INTEGER DEFAULT 0,
                    execution_time REAL DEFAULT 0.0,
                    report_data TEXT NOT NULL
                )
            """
            )

            conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_timestamp ON quality_reports(timestamp)
            """
            )

            conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_target_path ON quality_reports(target_path)
            """
            )

    def store_report(self, report: QualityReport) -> None:
        """Store quality report in database"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                INSERT INTO quality_reports (
                    timestamp, target_path, quality_score, total_issues, total_files,
                    issues_by_tool, issues_by_severity, issues_by_category,
                    auto_fixes_applied, execution_time, report_data
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    report.timestamp.isoformat(),
                    report.target_path,
                    report.quality_score,
                    report.total_issues,
                    report.total_files,
                    json.dumps(report.issues_by_tool),
                    json.dumps(report.issues_by_severity),
                    json.dumps(report.issues_by_category),
                    report.auto_fixes_applied,
                    report.execution_time,
                    json.dumps(asdict(report)),
                ),
            )

    def get_reports(
        self,
        target_path: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: Optional[int] = None,
    ) -> List[QualityReport]:
        """Get quality reports from database"""
        query = "SELECT report_data FROM quality_reports WHERE 1=1"
        params = []

        if target_path:
            query += " AND target_path = ?"
            params.append(target_path)

        if start_date:
            query += " AND timestamp >= ?"
            params.append(start_date.isoformat())

        if end_date:
            query += " AND timestamp <= ?"
            params.append(end_date.isoformat())

        query += " ORDER BY timestamp DESC"

        if limit:
            query += " LIMIT ?"
            params.append(limit)

        reports = []
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(query, params)
            for row in cursor.fetchall():
                report_data = json.loads(row[0])
                # Convert timestamp back to datetime
                report_data["timestamp"] = datetime.fromisoformat(
                    report_data["timestamp"]
                )
                # Convert issues back to QualityIssue objects
                issues = []
                for issue_dict in report_data["issues"]:
                    issue = QualityIssue(**issue_dict)
                    issues.append(issue)
                report_data["issues"] = issues
                reports.append(QualityReport(**report_data))

        return reports

    def get_quality_trends(
        self, target_path: str, days: int = 30, group_by: str = "day"
    ) -> List[QualityTrend]:
        """Get quality trends over time"""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)

        reports = self.get_reports(target_path, start_date, end_date)

        if not reports:
            return []

        # Group reports by time period
        if group_by == "day":
            group_key = lambda r: r.timestamp.date()
        elif group_by == "week":
            group_key = lambda r: r.timestamp.isocalendar()[:2]  # (year, week)
        elif group_by == "month":
            group_key = lambda r: (r.timestamp.year, r.timestamp.month)
        else:
            raise ValueError(f"Invalid group_by: {group_by}")

        grouped_reports = {}
        for report in reports:
            key = group_key(report)
            if key not in grouped_reports:
                grouped_reports[key] = []
            grouped_reports[key].append(report)

        # Calculate trends
        trends = []
        for key, group_reports in grouped_reports.items():
            # Calculate averages
            quality_scores = [r.quality_score for r in group_reports]
            total_issues = sum(r.total_issues for r in group_reports)
            total_files = sum(r.total_files for r in group_reports)
            auto_fixes = sum(r.auto_fixes_applied for r in group_reports)

            # Aggregate issues by severity and tool
            issues_by_severity = {}
            issues_by_tool = {}

            for report in group_reports:
                for severity, count in report.issues_by_severity.items():
                    issues_by_severity[severity] = (
                        issues_by_severity.get(severity, 0) + count
                    )
                for tool, count in report.issues_by_tool.items():
                    issues_by_tool[tool] = issues_by_tool.get(tool, 0) + count

            # Determine period start/end
            timestamps = [r.timestamp for r in group_reports]
            period_start = min(timestamps)
            period_end = max(timestamps)

            trend = QualityTrend(
                period_start=period_start,
                period_end=period_end,
                quality_score=statistics.mean(quality_scores),
                total_issues=total_issues,
                issues_by_severity=issues_by_severity,
                issues_by_tool=issues_by_tool,
                files_analyzed=total_files,
                auto_fixes_applied=auto_fixes,
            )
            trends.append(trend)

        return sorted(trends, key=lambda t: t.period_start)

    def get_quality_summary(self, target_path: str, days: int = 7) -> Dict[str, Any]:
        """Get quality summary for recent period"""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)

        reports = self.get_reports(target_path, start_date, end_date)

        if not reports:
            return {
                "status": "no_data",
                "message": f"No quality reports found for {target_path} in the last {days} days",
            }

        # Calculate summary statistics
        quality_scores = [r.quality_score for r in reports]
        total_issues = sum(r.total_issues for r in reports)
        total_files = sum(r.total_files for r in reports)
        auto_fixes = sum(r.auto_fixes_applied for r in reports)

        # Aggregate issues
        issues_by_severity = {}
        issues_by_tool = {}
        issues_by_category = {}

        for report in reports:
            for severity, count in report.issues_by_severity.items():
                issues_by_severity[severity] = (
                    issues_by_severity.get(severity, 0) + count
                )
            for tool, count in report.issues_by_tool.items():
                issues_by_tool[tool] = issues_by_tool.get(tool, 0) + count
            for category, count in report.issues_by_category.items():
                issues_by_category[category] = (
                    issues_by_category.get(category, 0) + count
                )

        # Determine quality level
        avg_quality_score = statistics.mean(quality_scores)
        quality_level = self._determine_quality_level(
            avg_quality_score, total_issues, total_files
        )

        # Calculate trends
        if len(reports) >= 2:
            recent_trend = (
                "improving" if quality_scores[-1] > quality_scores[0] else "declining"
            )
        else:
            recent_trend = "stable"

        return {
            "status": "success",
            "period_days": days,
            "reports_count": len(reports),
            "quality_score": {
                "current": quality_scores[-1] if quality_scores else 0,
                "average": round(statistics.mean(quality_scores), 1),
                "min": min(quality_scores) if quality_scores else 0,
                "max": max(quality_scores) if quality_scores else 0,
                "trend": recent_trend,
            },
            "issues": {
                "total": total_issues,
                "by_severity": issues_by_severity,
                "by_tool": issues_by_tool,
                "by_category": issues_by_category,
                "per_file": (
                    round(total_issues / total_files, 2) if total_files > 0 else 0
                ),
            },
            "files": {
                "total_analyzed": total_files,
                "average_per_report": (
                    round(total_files / len(reports), 1) if reports else 0
                ),
            },
            "auto_fixes": {
                "total_applied": auto_fixes,
                "average_per_report": (
                    round(auto_fixes / len(reports), 1) if reports else 0
                ),
            },
            "quality_level": quality_level,
            "benchmark": self.benchmarks[quality_level],
        }

    def _determine_quality_level(
        self, quality_score: float, total_issues: int, total_files: int
    ) -> str:
        """Determine quality level based on score and issues"""
        issues_per_file = total_issues / total_files if total_files > 0 else 0

        for level_name, benchmark in self.benchmarks.items():
            if (
                quality_score >= benchmark.quality_score
                and issues_per_file <= benchmark.max_issues_per_file
            ):
                return level_name

        return "needs_work"

    def get_comparison_report(
        self, target_path: str, baseline_days: int = 30, current_days: int = 7
    ) -> Dict[str, Any]:
        """Compare current quality with baseline"""
        end_date = datetime.now()
        current_start = end_date - timedelta(days=current_days)
        baseline_start = end_date - timedelta(days=baseline_days)
        baseline_end = current_start

        # Get reports for both periods
        current_reports = self.get_reports(target_path, current_start, end_date)
        baseline_reports = self.get_reports(target_path, baseline_start, baseline_end)

        if not current_reports or not baseline_reports:
            return {
                "status": "insufficient_data",
                "message": "Not enough data for comparison",
            }

        # Calculate metrics for both periods
        current_quality = statistics.mean([r.quality_score for r in current_reports])
        baseline_quality = statistics.mean([r.quality_score for r in baseline_reports])

        current_issues = sum(r.total_issues for r in current_reports)
        baseline_issues = sum(r.total_issues for r in baseline_reports)

        current_files = sum(r.total_files for r in current_reports)
        baseline_files = sum(r.total_files for r in baseline_reports)

        # Calculate changes
        quality_change = current_quality - baseline_quality
        quality_change_pct = (
            (quality_change / baseline_quality * 100) if baseline_quality > 0 else 0
        )

        current_issues_per_file = (
            current_issues / current_files if current_files > 0 else 0
        )
        baseline_issues_per_file = (
            baseline_issues / baseline_files if baseline_files > 0 else 0
        )
        issues_change = current_issues_per_file - baseline_issues_per_file

        return {
            "status": "success",
            "comparison_period": {
                "baseline": f"{baseline_days} days ago",
                "current": f"last {current_days} days",
            },
            "quality_score": {
                "current": round(current_quality, 1),
                "baseline": round(baseline_quality, 1),
                "change": round(quality_change, 1),
                "change_percent": round(quality_change_pct, 1),
                "trend": (
                    "improving"
                    if quality_change > 0
                    else "declining" if quality_change < 0 else "stable"
                ),
            },
            "issues_per_file": {
                "current": round(current_issues_per_file, 2),
                "baseline": round(baseline_issues_per_file, 2),
                "change": round(issues_change, 2),
                "trend": (
                    "improving"
                    if issues_change < 0
                    else "declining" if issues_change > 0 else "stable"
                ),
            },
            "summary": {
                "overall_trend": (
                    "improving"
                    if quality_change > 0 and issues_change < 0
                    else (
                        "declining"
                        if quality_change < 0 and issues_change > 0
                        else "mixed"
                    )
                ),
                "recommendation": self._get_comparison_recommendation(
                    quality_change, issues_change
                ),
            },
        }

    def _get_comparison_recommendation(
        self, quality_change: float, issues_change: float
    ) -> str:
        """Get recommendation based on comparison results"""
        if quality_change > 5 and issues_change < -0.5:
            return "Excellent progress! Quality is significantly improving."
        elif quality_change > 0 and issues_change < 0:
            return "Good progress! Continue current practices."
        elif quality_change < -5 or issues_change > 1.0:
            return "Quality is declining. Immediate attention needed."
        elif quality_change < 0 or issues_change > 0:
            return "Quality needs attention. Review recent changes."
        else:
            return "Quality is stable. Consider setting higher standards."

    def export_metrics(
        self, output_path: str, target_path: Optional[str] = None
    ) -> None:
        """Export metrics to JSON file"""
        reports = self.get_reports(target_path)

        export_data = {
            "export_timestamp": datetime.now().isoformat(),
            "target_path": target_path,
            "total_reports": len(reports),
            "reports": [asdict(report) for report in reports],
        }

        # Convert datetime objects to ISO format
        for report in export_data["reports"]:
            report["timestamp"] = report["timestamp"].isoformat()

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False)

    def get_quality_dashboard_data(self, target_path: str) -> Dict[str, Any]:
        """Get data for quality dashboard"""
        # Get recent trends
        trends = self.get_quality_trends(target_path, days=30, group_by="day")

        # Get current summary
        summary = self.get_quality_summary(target_path, days=7)

        # Get comparison
        comparison = self.get_comparison_report(
            target_path, baseline_days=30, current_days=7
        )

        return {
            "trends": [asdict(trend) for trend in trends],
            "summary": summary,
            "comparison": comparison,
            "benchmarks": {
                name: asdict(benchmark) for name, benchmark in self.benchmarks.items()
            },
        }
