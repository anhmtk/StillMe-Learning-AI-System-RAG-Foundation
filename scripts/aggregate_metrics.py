#!/usr/bin/env python3
"""
📊 StillMe Metrics Aggregator
============================

Script tổng hợp metrics từ JSONL và SQLite thành daily/weekly rollups.
Tạo CSV reports cho dashboard và CI integration.

Tính năng:
- Daily/weekly/monthly rollups
- CSV export
- Performance optimization
- Data validation
- Retention management

Author: StillMe AI Framework
Version: 1.0.0
Date: 2025-09-28
"""

import argparse
import asyncio
import csv
import gzip
import json
import logging
import shutil

# Add project root to path
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Optional

sys.path.append(str(Path(__file__).parent.parent))

from stillme_core.metrics.queries import MetricsQueries

logger = logging.getLogger(__name__)


class MetricsAggregator:
    """
    Metrics aggregation system

    Tổng hợp metrics từ JSONL và SQLite thành rollups
    cho dashboard và reporting.
    """

    def __init__(
        self,
        db_path: str = "data/metrics/metrics.db",
        events_dir: str = "data/metrics/events",
        output_dir: str = "artifacts/metrics",
    ):
        self.db_path = db_path
        self.events_dir = Path(events_dir)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.queries = MetricsQueries(db_path)

        logger.info(f"MetricsAggregator initialized: db={db_path}, output={output_dir}")

    def aggregate_daily_metrics(self, date: Optional[str] = None) -> dict[str, Any]:
        """Aggregate daily metrics"""
        if date is None:
            date = datetime.now().strftime("%Y-%m-%d")

        logger.info(f"Aggregating daily metrics for {date}")

        # Get daily summary
        daily_summary = self.queries.get_daily_summary(date)

        # Get learning curve data
        learning_curve = self.queries.get_learning_curve(1)

        # Get performance metrics
        performance = self.queries.get_performance_metrics(1)

        # Get ingest volume
        ingest_volume = self.queries.get_ingest_volume(1)

        # Get token usage
        token_usage = self.queries.get_token_usage(1)

        # Get error analysis
        error_analysis = self.queries.get_error_analysis(1)

        # Get approval metrics
        approval_metrics = self.queries.get_approval_metrics(1)

        aggregated_data = {
            "date": date,
            "summary": daily_summary,
            "learning_curve": learning_curve,
            "performance": performance,
            "ingest_volume": ingest_volume,
            "token_usage": token_usage,
            "error_analysis": error_analysis,
            "approval_metrics": approval_metrics,
        }

        return aggregated_data

    def create_daily_summary_csv(self, date: Optional[str] = None) -> str:
        """Create daily summary CSV"""
        if date is None:
            date = datetime.now().strftime("%Y-%m-%d")

        aggregated_data = self.aggregate_daily_metrics(date)
        summary = aggregated_data["summary"]

        csv_path = self.output_dir / f"daily_summary_{date}.csv"

        with open(csv_path, "w", newline="", encoding="utf-8") as csvfile:
            writer = csv.writer(csvfile)

            # Header
            writer.writerow(
                [
                    "date",
                    "total_runs",
                    "successful_runs",
                    "success_rate",
                    "total_errors",
                    "pass_rate",
                    "accuracy",
                    "self_assessment",
                    "avg_latency_ms",
                    "max_latency_ms",
                    "avg_memory_mb",
                    "max_memory_mb",
                    "total_tokens",
                    "ingested_items",
                ]
            )

            # Data row
            metrics = summary.get("metrics", {})
            runs = summary.get("runs", {})
            errors = summary.get("errors", {})

            writer.writerow(
                [
                    date,
                    runs.get("total", 0),
                    runs.get("successful", 0),
                    runs.get("success_rate", 0.0),
                    errors.get("total", 0),
                    metrics.get("learning_pass_rate", {}).get("avg", 0.0),
                    metrics.get("learning_accuracy", {}).get("avg", 0.0),
                    metrics.get("self_assessment_score", {}).get("avg", 0.0),
                    metrics.get("latency_ms", {}).get("avg", 0.0),
                    metrics.get("latency_ms", {}).get("max", 0.0),
                    metrics.get("memory_usage_mb", {}).get("avg", 0.0),
                    metrics.get("memory_usage_mb", {}).get("max", 0.0),
                    metrics.get("tokens_used", {}).get("avg", 0.0),
                    metrics.get("ingested_items", {}).get("avg", 0.0),
                ]
            )

        logger.info(f"Created daily summary CSV: {csv_path}")
        return str(csv_path)

    def create_by_source_csv(self, days: int = 7) -> str:
        """Create by-source CSV"""
        ingest_volume = self.queries.get_ingest_volume(days)

        csv_path = self.output_dir / f"by_source_{days}d.csv"

        with open(csv_path, "w", newline="", encoding="utf-8") as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(["date", "source", "total_items", "pass_rate"])

            for item in ingest_volume:
                writer.writerow(
                    [
                        item["date"],
                        item["source"],
                        item["total_items"],
                        0.0,  # TODO: Calculate pass rate by source
                    ]
                )

        logger.info(f"Created by-source CSV: {csv_path}")
        return str(csv_path)

    def create_learning_curve_csv(self, days: int = 30) -> str:
        """Create learning curve CSV"""
        learning_curve = self.queries.get_learning_curve(days)

        csv_path = self.output_dir / f"learning_curve_{days}d.csv"

        with open(csv_path, "w", newline="", encoding="utf-8") as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(["date", "pass_rate", "accuracy", "self_assessment"])

            for day in learning_curve:
                writer.writerow(
                    [
                        day["date"],
                        day["pass_rate"],
                        day["accuracy"],
                        day["self_assessment"],
                    ]
                )

        logger.info(f"Created learning curve CSV: {csv_path}")
        return str(csv_path)

    def create_performance_csv(self, days: int = 7) -> str:
        """Create performance metrics CSV"""
        performance = self.queries.get_performance_metrics(days)

        csv_path = self.output_dir / f"performance_{days}d.csv"

        with open(csv_path, "w", newline="", encoding="utf-8") as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(
                ["metric", "operation", "avg_value", "min_value", "max_value"]
            )

            # Latency metrics
            for operation, metrics in performance.get("latency", {}).items():
                writer.writerow(
                    [
                        "latency_ms",
                        operation,
                        metrics.get("avg", 0.0),
                        metrics.get("min", 0.0),
                        metrics.get("max", 0.0),
                    ]
                )

            # Memory metrics
            memory = performance.get("memory", {})
            writer.writerow(
                [
                    "memory_usage_mb",
                    "system",
                    memory.get("avg_mb", 0.0),
                    memory.get("avg_mb", 0.0),
                    memory.get("max_mb", 0.0),
                ]
            )

            # CPU metrics
            cpu = performance.get("cpu", {})
            writer.writerow(
                [
                    "cpu_usage_percent",
                    "system",
                    cpu.get("avg_percent", 0.0),
                    cpu.get("avg_percent", 0.0),
                    cpu.get("max_percent", 0.0),
                ]
            )

        logger.info(f"Created performance CSV: {csv_path}")
        return str(csv_path)

    def create_error_analysis_csv(self, days: int = 7) -> str:
        """Create error analysis CSV"""
        error_analysis = self.queries.get_error_analysis(days)

        csv_path = self.output_dir / f"error_analysis_{days}d.csv"

        with open(csv_path, "w", newline="", encoding="utf-8") as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(["error_type", "date", "count"])

            for error_type, error_data in error_analysis.get("by_type", {}).items():
                for day_data in error_data:
                    writer.writerow([error_type, day_data["date"], day_data["count"]])

        logger.info(f"Created error analysis CSV: {csv_path}")
        return str(csv_path)

    def compress_old_events(self, days_to_keep: int = 90):
        """Compress old event files"""
        cutoff_date = datetime.now() - timedelta(days=days_to_keep)

        for event_file in self.events_dir.glob("*.jsonl"):
            try:
                file_date = datetime.strptime(event_file.stem, "%Y-%m-%d")
                if file_date < cutoff_date:
                    # Compress file
                    compressed_file = event_file.with_suffix(".jsonl.gz")
                    with open(event_file, "rb") as f_in:
                        with gzip.open(compressed_file, "wb") as f_out:
                            shutil.copyfileobj(f_in, f_out)

                    # Remove original
                    event_file.unlink()
                    logger.info(f"Compressed {event_file} to {compressed_file}")
            except ValueError:
                # Skip files that don't match date format
                continue

    def generate_all_reports(self, days: int = 7):
        """Generate all CSV reports"""
        logger.info(f"Generating all reports for {days} days")

        reports = []

        # Daily summary
        reports.append(self.create_daily_summary_csv())

        # By source
        reports.append(self.create_by_source_csv(days))

        # Learning curve
        reports.append(self.create_learning_curve_csv(30))

        # Performance
        reports.append(self.create_performance_csv(days))

        # Error analysis
        reports.append(self.create_error_analysis_csv(days))

        # Compress old events
        self.compress_old_events()

        logger.info(f"Generated {len(reports)} reports")
        return reports

    def create_metrics_summary(self) -> dict[str, Any]:
        """Create overall metrics summary"""
        summary = {
            "generated_at": datetime.now().isoformat(),
            "database_path": self.db_path,
            "output_directory": str(self.output_dir),
            "reports": [],
        }

        # List generated reports
        for csv_file in self.output_dir.glob("*.csv"):
            summary["reports"].append(
                {
                    "filename": csv_file.name,
                    "size_bytes": csv_file.stat().st_size,
                    "modified": datetime.fromtimestamp(
                        csv_file.stat().st_mtime
                    ).isoformat(),
                }
            )

        # Save summary
        summary_path = self.output_dir / "metrics_summary.json"
        with open(summary_path, "w", encoding="utf-8") as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)

        logger.info(f"Created metrics summary: {summary_path}")
        return summary


async def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="StillMe Metrics Aggregator")
    parser.add_argument(
        "--days", type=int, default=7, help="Number of days to aggregate"
    )
    parser.add_argument(
        "--date", type=str, help="Specific date to aggregate (YYYY-MM-DD)"
    )
    parser.add_argument(
        "--output-dir", type=str, default="artifacts/metrics", help="Output directory"
    )
    parser.add_argument(
        "--db-path", type=str, default="data/metrics/metrics.db", help="Database path"
    )
    parser.add_argument(
        "--events-dir", type=str, default="data/metrics/events", help="Events directory"
    )
    parser.add_argument(
        "--compress-days", type=int, default=90, help="Days to keep before compressing"
    )
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose logging")

    args = parser.parse_args()

    # Setup logging
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=log_level, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    # Initialize aggregator
    aggregator = MetricsAggregator(
        db_path=args.db_path, events_dir=args.events_dir, output_dir=args.output_dir
    )

    try:
        if args.date:
            # Aggregate specific date
            aggregator.aggregate_daily_metrics(args.date)
            csv_path = aggregator.create_daily_summary_csv(args.date)
            print(f"✅ Daily summary created: {csv_path}")
        else:
            # Generate all reports
            reports = aggregator.generate_all_reports(args.days)
            print(f"✅ Generated {len(reports)} reports:")
            for report in reports:
                print(f"  - {report}")

        # Create summary
        summary = aggregator.create_metrics_summary()
        print(f"✅ Metrics summary created: {summary['reports']}")

    except Exception as e:
        logger.error(f"Error during aggregation: {e}")
        return 1

    return 0


if __name__ == "__main__":
    exit(asyncio.run(main()))
