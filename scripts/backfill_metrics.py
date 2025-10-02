#!/usr/bin/env python3
"""
📊 StillMe Metrics Backfill
==========================

Script tạo sample data cho metrics system.
Hỗ trợ testing và demo dashboard với dữ liệu realistic.

Tính năng:
- Sample data generation
- Realistic learning curves
- Performance simulation
- Error simulation
- Historical backfill

Author: StillMe AI Framework
Version: 1.0.0
Date: 2025-09-28
"""

import argparse
import asyncio
import json
import logging
import random

# Add project root to path
import sys
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Optional

sys.path.append(str(Path(__file__).parent.parent))

from stillme_core.metrics.emitter import Metric, MetricsEmitter
from stillme_core.metrics.registry import get_metrics_registry

logger = logging.getLogger(__name__)


class MetricsBackfill:
    """
    Metrics backfill system

    Tạo sample data realistic cho testing và demo
    learning dashboard.
    """

    def __init__(
        self,
        db_path: str = "data/metrics/metrics.db",
        events_dir: str = "data/metrics/events",
    ):
        self.db_path = db_path
        self.events_dir = Path(events_dir)
        self.events_dir.mkdir(parents=True, exist_ok=True)

        self.emitter = MetricsEmitter(db_path=db_path, events_dir=str(events_dir))
        self.registry = get_metrics_registry()

        # Sample data templates
        self.sources = ["rss", "experience", "manual", "api"]
        self.stages = ["infant", "child", "adolescent", "adult"]
        self.components = ["learning", "memory", "router", "api", "agentdev"]
        self.operations = ["ingest", "embed", "assess", "route", "train"]
        self.error_types = ["timeout", "memory", "validation", "network", "parsing"]

        logger.info(f"MetricsBackfill initialized: db={db_path}")

    def generate_learning_curve_data(
        self, days: int, start_date: Optional[datetime] = None
    ) -> list[dict[str, Any]]:
        """Generate realistic learning curve data"""
        if start_date is None:
            start_date = datetime.now() - timedelta(days=days)

        learning_data = []

        for i in range(days):
            date = start_date + timedelta(days=i)

            # Simulate learning progression with some noise
            progress = i / days

            # Pass rate: starts low, improves over time
            pass_rate = 0.3 + (progress * 0.6) + random.uniform(-0.1, 0.1)
            pass_rate = max(0.0, min(1.0, pass_rate))

            # Accuracy: similar to pass rate but with different curve
            accuracy = 0.4 + (progress * 0.5) + random.uniform(-0.05, 0.05)
            accuracy = max(0.0, min(1.0, accuracy))

            # Self-assessment: more conservative
            self_assessment = 0.2 + (progress * 0.7) + random.uniform(-0.08, 0.08)
            self_assessment = max(0.0, min(1.0, self_assessment))

            learning_data.append(
                {
                    "date": date.strftime("%Y-%m-%d"),
                    "pass_rate": round(pass_rate, 3),
                    "accuracy": round(accuracy, 3),
                    "self_assessment": round(self_assessment, 3),
                }
            )

        return learning_data

    def generate_performance_data(self, days: int) -> list[dict[str, Any]]:
        """Generate performance metrics data"""
        performance_data = []

        for i in range(days):
            date = datetime.now() - timedelta(days=days - i)

            # Latency: improves over time with some variation
            base_latency = 1000 - (i * 10)  # Improve by 10ms per day
            latency = max(100, base_latency + random.uniform(-50, 50))

            # Memory usage: relatively stable with some spikes
            memory = 500 + random.uniform(-100, 200)

            # CPU usage: varies based on load
            cpu = 30 + random.uniform(-10, 40)

            performance_data.append(
                {
                    "date": date.strftime("%Y-%m-%d"),
                    "latency_ms": round(latency, 1),
                    "memory_mb": round(memory, 1),
                    "cpu_percent": round(cpu, 1),
                }
            )

        return performance_data

    def generate_ingest_data(self, days: int) -> list[dict[str, Any]]:
        """Generate ingest volume data"""
        ingest_data = []

        for i in range(days):
            date = datetime.now() - timedelta(days=days - i)

            for source in self.sources:
                # Different sources have different volumes
                base_volume = {"rss": 50, "experience": 30, "manual": 10, "api": 20}[
                    source
                ]

                # Add some variation
                volume = base_volume + random.randint(-10, 20)
                volume = max(0, volume)

                ingest_data.append(
                    {
                        "date": date.strftime("%Y-%m-%d"),
                        "source": source,
                        "items": volume,
                    }
                )

        return ingest_data

    def generate_error_data(self, days: int) -> list[dict[str, Any]]:
        """Generate error data"""
        error_data = []

        for i in range(days):
            date = datetime.now() - timedelta(days=days - i)

            # Errors decrease over time as system improves
            error_probability = 0.1 - (i * 0.001)  # Decrease by 0.1% per day
            error_probability = max(0.01, error_probability)

            for error_type in self.error_types:
                if random.random() < error_probability:
                    count = random.randint(1, 5)
                    error_data.append(
                        {
                            "date": date.strftime("%Y-%m-%d"),
                            "type": error_type,
                            "count": count,
                        }
                    )

        return error_data

    def generate_evolution_data(self, days: int) -> list[dict[str, Any]]:
        """Generate evolution stage data"""
        evolution_data = []

        for i in range(days):
            date = datetime.now() - timedelta(days=days - i)

            # Evolution stages: 0=infant, 1=child, 2=adolescent, 3=adult
            if i < days * 0.25:
                stage = 0  # Infant
            elif i < days * 0.5:
                stage = 1  # Child
            elif i < days * 0.75:
                stage = 2  # Adolescent
            else:
                stage = 3  # Adult

            evolution_data.append({"date": date.strftime("%Y-%m-%d"), "stage": stage})

        return evolution_data

    async def backfill_daily_data(self, date: str, data: dict[str, Any]):
        """Backfill data for a specific date"""
        # Start session
        self.emitter.start_session(
            stage="backfill", notes=f"Backfill data for {date}", version="1.0.0"
        )

        try:
            # Log events
            for component in self.components:
                self.emitter.log_event(
                    event="start",
                    component=component,
                    metrics={
                        "items_processed": random.randint(10, 100),
                        "success_rate": random.uniform(0.8, 1.0),
                    },
                    meta={"date": date, "backfill": True},
                )

            # Log metrics
            metrics_to_log = [
                # Learning metrics
                Metric(
                    "learning_pass_rate", data.get("pass_rate", 0.8), "ratio", "daily"
                ),
                Metric(
                    "learning_accuracy", data.get("accuracy", 0.85), "ratio", "daily"
                ),
                Metric(
                    "self_assessment_score",
                    data.get("self_assessment", 0.75),
                    "ratio",
                    "daily",
                ),
                # Performance metrics
                Metric("latency_ms", data.get("latency_ms", 500), "ms", "system"),
                Metric("memory_usage_mb", data.get("memory_mb", 600), "MB", "system"),
                Metric("cpu_usage_percent", data.get("cpu_percent", 40), "%", "system"),
                # Ingest metrics
                Metric(
                    "ingested_items", data.get("ingested_items", 100), "count", "rss"
                ),
                Metric(
                    "ingested_items",
                    data.get("ingested_experience", 50),
                    "count",
                    "experience",
                ),
                Metric(
                    "ingested_items", data.get("ingested_manual", 20), "count", "manual"
                ),
                # Token usage
                Metric(
                    "tokens_used", data.get("tokens_used", 5000), "tokens", "learning"
                ),
                # Evolution
                Metric(
                    "evolution_stage", data.get("evolution_stage", 2), "count", "system"
                ),
                # Quality metrics
                Metric(
                    "quality_score", data.get("quality_score", 0.8), "ratio", "content"
                ),
                Metric("risk_score", data.get("risk_score", 0.2), "ratio", "content"),
                Metric(
                    "approval_rate", data.get("approval_rate", 0.9), "ratio", "content"
                ),
            ]

            for metric in metrics_to_log:
                self.emitter.log_metric(metric)

            # Log some errors
            if data.get("errors", 0) > 0:
                for _ in range(data["errors"]):
                    self.emitter.log_event(
                        event="error",
                        component=random.choice(self.components),
                        metrics={"error_count": 1},
                        meta={
                            "error_type": random.choice(self.error_types),
                            "message": "Sample error for backfill",
                        },
                    )

            # End session
            self.emitter.end_session(
                success=True, notes=f"Backfill completed for {date}"
            )

        except Exception as e:
            logger.error(f"Error backfilling data for {date}: {e}")
            self.emitter.end_session(success=False, notes=f"Backfill failed: {e}")

    async def backfill_historical_data(self, days: int):
        """Backfill historical data"""
        logger.info(f"Backfilling {days} days of historical data")

        # Generate data
        learning_data = self.generate_learning_curve_data(days)
        performance_data = self.generate_performance_data(days)
        ingest_data = self.generate_ingest_data(days)
        error_data = self.generate_error_data(days)
        evolution_data = self.generate_evolution_data(days)

        # Combine data by date
        combined_data = {}

        for i, learning in enumerate(learning_data):
            date = learning["date"]
            combined_data[date] = {
                "pass_rate": learning["pass_rate"],
                "accuracy": learning["accuracy"],
                "self_assessment": learning["self_assessment"],
                "latency_ms": performance_data[i]["latency_ms"],
                "memory_mb": performance_data[i]["memory_mb"],
                "cpu_percent": performance_data[i]["cpu_percent"],
                "evolution_stage": evolution_data[i]["stage"],
                "ingested_items": sum(
                    item["items"] for item in ingest_data if item["date"] == date
                ),
                "ingested_experience": next(
                    (
                        item["items"]
                        for item in ingest_data
                        if item["date"] == date and item["source"] == "experience"
                    ),
                    0,
                ),
                "ingested_manual": next(
                    (
                        item["items"]
                        for item in ingest_data
                        if item["date"] == date and item["source"] == "manual"
                    ),
                    0,
                ),
                "tokens_used": random.randint(3000, 8000),
                "quality_score": random.uniform(0.7, 0.95),
                "risk_score": random.uniform(0.1, 0.3),
                "approval_rate": random.uniform(0.85, 0.98),
                "errors": len([e for e in error_data if e["date"] == date]),
            }

        # Backfill each day
        for date, data in combined_data.items():
            await self.backfill_daily_data(date, data)
            logger.info(f"Backfilled data for {date}")

        logger.info(f"Completed backfilling {days} days of data")

    def create_sample_events(self, days: int):
        """Create sample event files"""
        logger.info(f"Creating sample event files for {days} days")

        for i in range(days):
            date = datetime.now() - timedelta(days=days - i)
            date_str = date.strftime("%Y-%m-%d")

            event_file = self.events_dir / f"{date_str}.jsonl"

            with open(event_file, "w", encoding="utf-8") as f:
                # Generate 10-50 events per day
                num_events = random.randint(10, 50)

                for _ in range(num_events):
                    event = {
                        "ts": (
                            date
                            + timedelta(
                                hours=random.randint(0, 23),
                                minutes=random.randint(0, 59),
                            )
                        ).isoformat(),
                        "session_id": f"sess_{date_str}_{uuid.uuid4().hex[:4]}",
                        "stage": random.choice(self.stages),
                        "component": random.choice(self.components),
                        "event": random.choice(["start", "end", "metric", "error"]),
                        "meta": {
                            "model": "stillme-v1",
                            "source": random.choice(self.sources),
                            "operation": random.choice(self.operations),
                        },
                        "metrics": {
                            "latency_ms": random.randint(100, 2000),
                            "items": random.randint(1, 100),
                            "tokens": random.randint(100, 5000),
                        },
                    }
                    f.write(json.dumps(event, ensure_ascii=False) + "\n")

            logger.info(f"Created {num_events} events for {date_str}")


async def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="StillMe Metrics Backfill")
    parser.add_argument(
        "--days", type=int, default=7, help="Number of days to backfill"
    )
    parser.add_argument(
        "--db-path", type=str, default="data/metrics/metrics.db", help="Database path"
    )
    parser.add_argument(
        "--events-dir", type=str, default="data/metrics/events", help="Events directory"
    )
    parser.add_argument(
        "--events-only", action="store_true", help="Only create event files"
    )
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose logging")

    args = parser.parse_args()

    # Setup logging
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=log_level, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    # Initialize backfill
    backfill = MetricsBackfill(db_path=args.db_path, events_dir=args.events_dir)

    try:
        if args.events_only:
            # Only create event files
            backfill.create_sample_events(args.days)
            print(f"✅ Created sample event files for {args.days} days")
        else:
            # Full backfill
            await backfill.backfill_historical_data(args.days)
            backfill.create_sample_events(args.days)
            print(f"✅ Backfilled {args.days} days of metrics data")

    except Exception as e:
        logger.error(f"Error during backfill: {e}")
        return 1

    return 0


if __name__ == "__main__":
    exit(asyncio.run(main()))
