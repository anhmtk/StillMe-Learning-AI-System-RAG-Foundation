"""
Metrics Collector Module
========================

Collects and stores application metrics for monitoring and analysis.
"""

import json
import sqlite3
import statistics
import threading
import time
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any


class MetricType(Enum):
    """Types of metrics"""

    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    TIMER = "timer"


@dataclass
class MetricPoint:
    """A single metric data point"""

    name: str
    value: float
    metric_type: str
    timestamp: str
    labels: dict[str, str] | None = None
    unit: str | None = None


@dataclass
class MetricSummary:
    """Summary statistics for a metric"""

    name: str
    metric_type: str
    count: int
    min_value: float
    max_value: float
    mean_value: float
    median_value: float
    p95_value: float
    p99_value: float
    total_value: float
    time_range: str


class MetricsCollector:
    """Collects and stores application metrics"""

    def __init__(self, db_path: str = "metrics.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        # Thread lock for database operations
        self._lock = threading.Lock()

        # In-memory cache for fast access
        self._cache: dict[str, list[MetricPoint]] = {}
        self._cache_lock = threading.Lock()

        # Initialize database
        self._init_database()

    def _init_database(self):
        """Initialize SQLite database for metrics storage"""
        with self._lock:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Create metrics table
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    value REAL NOT NULL,
                    metric_type TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    labels TEXT,
                    unit TEXT
                )
            """
            )

            # Create index for faster queries
            cursor.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_metrics_name_timestamp
                ON metrics(name, timestamp)
            """
            )

            cursor.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_metrics_type
                ON metrics(metric_type)
            """
            )

            conn.commit()
            conn.close()

    def _add_to_cache(self, metric: MetricPoint):
        """Add metric to in-memory cache"""
        with self._cache_lock:
            if metric.name not in self._cache:
                self._cache[metric.name] = []
            self._cache[metric.name].append(metric)

            # Keep only last 1000 points per metric to prevent memory issues
            if len(self._cache[metric.name]) > 1000:
                self._cache[metric.name] = self._cache[metric.name][-1000:]

    def _store_metric(self, metric: MetricPoint):
        """Store metric in database"""
        with self._lock:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            labels_json = json.dumps(metric.labels) if metric.labels else None

            cursor.execute(
                """
                INSERT INTO metrics (name, value, metric_type, timestamp, labels, unit)
                VALUES (?, ?, ?, ?, ?, ?)
            """,
                (
                    metric.name,
                    metric.value,
                    metric.metric_type,
                    metric.timestamp,
                    labels_json,
                    metric.unit,
                ),
            )

            conn.commit()
            conn.close()

    def record_metric(
        self,
        name: str,
        value: float,
        metric_type: MetricType = MetricType.GAUGE,
        labels: dict[str, str] | None = None,
        unit: str | None = None,
    ):
        """Record a metric"""
        metric = MetricPoint(
            name=name,
            value=value,
            metric_type=metric_type.value,
            timestamp=datetime.now().isoformat(),
            labels=labels,
            unit=unit,
        )

        # Add to cache for fast access
        self._add_to_cache(metric)

        # Store in database
        self._store_metric(metric)

    def increment_counter(
        self, name: str, value: float = 1.0, labels: dict[str, str] | None = None
    ):
        """Increment a counter metric"""
        self.record_metric(name, value, MetricType.COUNTER, labels)

    def set_gauge(
        self,
        name: str,
        value: float,
        labels: dict[str, str] | None = None,
        unit: str | None = None,
    ):
        """Set a gauge metric"""
        self.record_metric(name, value, MetricType.GAUGE, labels, unit)

    def record_histogram(
        self, name: str, value: float, labels: dict[str, str] | None = None
    ):
        """Record a histogram value"""
        self.record_metric(name, value, MetricType.HISTOGRAM, labels)

    def record_timer(
        self, name: str, duration_ms: float, labels: dict[str, str] | None = None
    ):
        """Record a timer metric"""
        self.record_metric(name, duration_ms, MetricType.TIMER, labels, "ms")

    def time_operation(self, name: str, labels: dict[str, str] | None = None):
        """Context manager for timing operations"""
        return TimerContext(self, name, labels)

    def get_metric_summary(
        self, name: str, time_range: timedelta | None = None
    ) -> MetricSummary | None:
        """Get summary statistics for a metric"""
        with self._lock:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Build query
            query = "SELECT value, metric_type FROM metrics WHERE name = ?"
            params = [name]

            if time_range:
                start_time = (datetime.now() - time_range).isoformat()
                query += " AND timestamp >= ?"
                params.append(start_time)

            query += " ORDER BY timestamp"

            cursor.execute(query, params)
            rows = cursor.fetchall()
            conn.close()

            if not rows:
                return None

            values = [row[0] for row in rows]
            metric_type = rows[0][1] if rows else "unknown"

            return MetricSummary(
                name=name,
                metric_type=metric_type,
                count=len(values),
                min_value=min(values),
                max_value=max(values),
                mean_value=statistics.mean(values),
                median_value=statistics.median(values),
                p95_value=self._percentile(values, 95),
                p99_value=self._percentile(values, 99),
                total_value=sum(values),
                time_range=f"Last {time_range}" if time_range else "All time",
            )

    def get_metrics_by_type(self, metric_type: MetricType) -> list[str]:
        """Get all metric names of a specific type"""
        with self._lock:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute(
                """
                SELECT DISTINCT name FROM metrics WHERE metric_type = ?
            """,
                (metric_type.value,),
            )

            names = [row[0] for row in cursor.fetchall()]
            conn.close()

            return names

    def get_recent_metrics(self, name: str, limit: int = 100) -> list[MetricPoint]:
        """Get recent metric values"""
        with self._lock:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute(
                """
                SELECT name, value, metric_type, timestamp, labels, unit
                FROM metrics WHERE name = ?
                ORDER BY timestamp DESC LIMIT ?
            """,
                (name, limit),
            )

            metrics = []
            for row in cursor.fetchall():
                labels = json.loads(row[4]) if row[4] else None
                metrics.append(
                    MetricPoint(
                        name=row[0],
                        value=row[1],
                        metric_type=row[2],
                        timestamp=row[3],
                        labels=labels,
                        unit=row[5],
                    )
                )

            conn.close()
            return list(reversed(metrics))  # Return in chronological order

    def get_metrics_overview(self) -> dict[str, Any]:
        """Get overview of all metrics"""
        with self._lock:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Get total metrics count
            cursor.execute("SELECT COUNT(*) FROM metrics")
            total_metrics = cursor.fetchone()[0]

            # Get metrics by type
            cursor.execute(
                """
                SELECT metric_type, COUNT(*) FROM metrics GROUP BY metric_type
            """
            )
            metrics_by_type = dict(cursor.fetchall())

            # Get unique metric names
            cursor.execute("SELECT COUNT(DISTINCT name) FROM metrics")
            unique_metrics = cursor.fetchone()[0]

            # Get time range
            cursor.execute("SELECT MIN(timestamp), MAX(timestamp) FROM metrics")
            time_range = cursor.fetchone()

            conn.close()

            return {
                "total_metrics": total_metrics,
                "unique_metrics": unique_metrics,
                "metrics_by_type": metrics_by_type,
                "time_range": {"start": time_range[0], "end": time_range[1]},
                "database_size": (
                    self.db_path.stat().st_size if self.db_path.exists() else 0
                ),
            }

    def export_metrics(
        self,
        output_file: str,
        time_range: timedelta | None = None,
        metric_names: list[str] | None = None,
    ) -> bool:
        """Export metrics to JSON file"""
        try:
            with self._lock:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()

                # Build query
                query = "SELECT * FROM metrics WHERE 1=1"
                params = []

                if time_range:
                    start_time = (datetime.now() - time_range).isoformat()
                    query += " AND timestamp >= ?"
                    params.append(start_time)

                if metric_names:
                    placeholders = ",".join("?" * len(metric_names))
                    query += f" AND name IN ({placeholders})"
                    params.extend(metric_names)

                query += " ORDER BY timestamp"

                cursor.execute(query, params)
                rows = cursor.fetchall()

                # Convert to list of dictionaries
                metrics = []
                for row in rows:
                    metric = {
                        "id": row[0],
                        "name": row[1],
                        "value": row[2],
                        "metric_type": row[3],
                        "timestamp": row[4],
                        "labels": json.loads(row[5]) if row[5] else None,
                        "unit": row[6],
                    }
                    metrics.append(metric)

                conn.close()

                # Write to file
                output_path = Path(output_file)
                output_path.parent.mkdir(parents=True, exist_ok=True)

                with open(output_path, "w", encoding="utf-8") as f:
                    json.dump(
                        {
                            "export_timestamp": datetime.now().isoformat(),
                            "total_metrics": len(metrics),
                            "metrics": metrics,
                        },
                        f,
                        indent=2,
                        ensure_ascii=False,
                    )

                return True

        except Exception as e:
            print(f"Error exporting metrics: {e}")
            return False

    def cleanup_old_metrics(self, days_to_keep: int = 30):
        """Remove metrics older than specified days"""
        cutoff_date = (datetime.now() - timedelta(days=days_to_keep)).isoformat()

        with self._lock:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute("DELETE FROM metrics WHERE timestamp < ?", (cutoff_date,))
            deleted_count = cursor.rowcount

            conn.commit()
            conn.close()

            return deleted_count

    def _percentile(self, values: list[float], percentile: int) -> float:
        """Calculate percentile of values"""
        if not values:
            return 0.0

        sorted_values = sorted(values)
        index = int((percentile / 100) * len(sorted_values))
        index = min(index, len(sorted_values) - 1)
        return sorted_values[index]


class TimerContext:
    """Context manager for timing operations"""

    def __init__(
        self,
        collector: MetricsCollector,
        name: str,
        labels: dict[str, str] | None = None,
    ):
        self.collector = collector
        self.name = name
        self.labels = labels
        self.start_time = None

    def __enter__(self):
        self.start_time = time.time()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.start_time:
            duration_ms = (time.time() - self.start_time) * 1000
            self.collector.record_timer(self.name, duration_ms, self.labels)


# Global metrics collector instance
_global_collector: MetricsCollector | None = None


def get_metrics_collector() -> MetricsCollector:
    """Get or create global metrics collector"""
    global _global_collector
    if _global_collector is None:
        _global_collector = MetricsCollector()
    return _global_collector


def setup_metrics(db_path: str = "metrics.db") -> MetricsCollector:
    """Setup global metrics collection"""
    global _global_collector
    _global_collector = MetricsCollector(db_path)
    return _global_collector