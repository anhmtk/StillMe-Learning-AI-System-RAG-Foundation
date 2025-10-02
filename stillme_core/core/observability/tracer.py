"""
Request Tracer Module
=====================

Provides distributed tracing for request flow tracking and performance analysis.
"""

import json
import sqlite3
import threading
import uuid
from contextvars import ContextVar
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Optional

# Context variables for tracing
trace_id_var: ContextVar[Optional[str]] = ContextVar("trace_id", default=None)
span_id_var: ContextVar[Optional[str]] = ContextVar("span_id", default=None)


@dataclass
class TraceSpan:
    """A single trace span"""

    trace_id: str
    span_id: str
    parent_span_id: Optional[str]
    operation_name: str
    start_time: str
    end_time: Optional[str]
    duration_ms: Optional[float]
    tags: Optional[dict[str, Any]]
    logs: Optional[list[dict[str, Any]]]
    status: str  # "started", "completed", "error"
    error_message: Optional[str] = None


@dataclass
class TraceContext:
    """Trace context for request tracking"""

    trace_id: str
    span_id: str
    parent_span_id: Optional[str] = None
    baggage: Optional[dict[str, str]] = None


class RequestTracer:
    """Distributed request tracer"""

    def __init__(self, db_path: str = "traces.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        # Thread lock for database operations
        self._lock = threading.Lock()

        # In-memory cache for active spans
        self._active_spans: dict[str, TraceSpan] = {}
        self._cache_lock = threading.Lock()

        # Initialize database
        self._init_database()

    def _init_database(self):
        """Initialize SQLite database for trace storage"""
        with self._lock:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Create traces table
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS traces (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    trace_id TEXT NOT NULL,
                    span_id TEXT NOT NULL,
                    parent_span_id TEXT,
                    operation_name TEXT NOT NULL,
                    start_time TEXT NOT NULL,
                    end_time TEXT,
                    duration_ms REAL,
                    tags TEXT,
                    logs TEXT,
                    status TEXT NOT NULL,
                    error_message TEXT
                )
            """
            )

            # Create indexes for faster queries
            cursor.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_traces_trace_id
                ON traces(trace_id)
            """
            )

            cursor.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_traces_span_id
                ON traces(span_id)
            """
            )

            cursor.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_traces_start_time
                ON traces(start_time)
            """
            )

            conn.commit()
            conn.close()

    def start_span(
        self,
        operation_name: str,
        trace_id: Optional[str] = None,
        parent_span_id: Optional[str] = None,
        tags: Optional[dict[str, Any]] = None,
    ) -> TraceSpan:
        """Start a new trace span"""
        # Generate IDs if not provided
        if not trace_id:
            trace_id = str(uuid.uuid4())

        span_id = str(uuid.uuid4())

        # Create span
        span = TraceSpan(
            trace_id=trace_id,
            span_id=span_id,
            parent_span_id=parent_span_id,
            operation_name=operation_name,
            start_time=datetime.now().isoformat(),
            end_time=None,
            duration_ms=None,
            tags=tags or {},
            logs=[],
            status="started",
        )

        # Store in active spans
        with self._cache_lock:
            self._active_spans[span_id] = span

        # Set context variables
        trace_id_var.set(trace_id)
        span_id_var.set(span_id)

        # Store in database
        self._store_span(span)

        return span

    def finish_span(self, span_id: str, error_message: Optional[str] = None):
        """Finish a trace span"""
        with self._cache_lock:
            if span_id not in self._active_spans:
                return

            span = self._active_spans[span_id]
            span.end_time = datetime.now().isoformat()
            span.duration_ms = self._calculate_duration(span.start_time, span.end_time)
            span.status = "error" if error_message else "completed"
            span.error_message = error_message

            # Update in database
            self._update_span(span)

            # Remove from active spans
            del self._active_spans[span_id]

    def add_span_log(self, span_id: str, message: str, level: str = "info", **kwargs):
        """Add a log entry to a span"""
        with self._cache_lock:
            if span_id in self._active_spans:
                span = self._active_spans[span_id]
                if span.logs is None:
                    span.logs = []

                log_entry = {
                    "timestamp": datetime.now().isoformat(),
                    "level": level,
                    "message": message,
                    **kwargs,
                }
                span.logs.append(log_entry)

    def add_span_tag(self, span_id: str, key: str, value: Any):
        """Add a tag to a span"""
        with self._cache_lock:
            if span_id in self._active_spans:
                span = self._active_spans[span_id]
                if span.tags is None:
                    span.tags = {}
                span.tags[key] = value

    def get_trace(self, trace_id: str) -> list[TraceSpan]:
        """Get all spans for a trace"""
        with self._lock:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute(
                """
                SELECT trace_id, span_id, parent_span_id, operation_name,
                       start_time, end_time, duration_ms, tags, logs, status, error_message
                FROM traces WHERE trace_id = ? ORDER BY start_time
            """,
                (trace_id,),
            )

            spans = []
            for row in cursor.fetchall():
                span = TraceSpan(
                    trace_id=row[0],
                    span_id=row[1],
                    parent_span_id=row[2],
                    operation_name=row[3],
                    start_time=row[4],
                    end_time=row[5],
                    duration_ms=row[6],
                    tags=json.loads(row[7]) if row[7] else {},
                    logs=json.loads(row[8]) if row[8] else [],
                    status=row[9],
                    error_message=row[10],
                )
                spans.append(span)

            conn.close()
            return spans

    def get_span(self, span_id: str) -> Optional[TraceSpan]:
        """Get a specific span"""
        with self._lock:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute(
                """
                SELECT trace_id, span_id, parent_span_id, operation_name,
                       start_time, end_time, duration_ms, tags, logs, status, error_message
                FROM traces WHERE span_id = ?
            """,
                (span_id,),
            )

            row = cursor.fetchone()
            conn.close()

            if row:
                return TraceSpan(
                    trace_id=row[0],
                    span_id=row[1],
                    parent_span_id=row[2],
                    operation_name=row[3],
                    start_time=row[4],
                    end_time=row[5],
                    duration_ms=row[6],
                    tags=json.loads(row[7]) if row[7] else {},
                    logs=json.loads(row[8]) if row[8] else [],
                    status=row[9],
                    error_message=row[10],
                )

            return None

    def get_traces_overview(self, limit: int = 100) -> list[dict[str, Any]]:
        """Get overview of recent traces"""
        with self._lock:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Get unique traces with summary info
            cursor.execute(
                """
                SELECT trace_id,
                       MIN(start_time) as start_time,
                       MAX(end_time) as end_time,
                       COUNT(*) as span_count,
                       SUM(duration_ms) as total_duration,
                       MAX(CASE WHEN status = 'error' THEN 1 ELSE 0 END) as has_error
                FROM traces
                WHERE end_time IS NOT NULL
                GROUP BY trace_id
                ORDER BY start_time DESC
                LIMIT ?
            """,
                (limit,),
            )

            traces = []
            for row in cursor.fetchall():
                traces.append(
                    {
                        "trace_id": row[0],
                        "start_time": row[1],
                        "end_time": row[2],
                        "span_count": row[3],
                        "total_duration": row[4],
                        "has_error": bool(row[5]),
                    }
                )

            conn.close()
            return traces

    def get_performance_stats(
        self,
        operation_name: Optional[str] = None,
        time_range: Optional[timedelta] = None,
    ) -> dict[str, Any]:
        """Get performance statistics for operations"""
        with self._lock:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Build query
            query = """
                SELECT operation_name, duration_ms, status
                FROM traces
                WHERE end_time IS NOT NULL AND duration_ms IS NOT NULL
            """
            params = []

            if operation_name:
                query += " AND operation_name = ?"
                params.append(operation_name)

            if time_range:
                start_time = (datetime.now() - time_range).isoformat()
                query += " AND start_time >= ?"
                params.append(start_time)

            cursor.execute(query, params)
            rows = cursor.fetchall()
            conn.close()

            if not rows:
                return {"error": "No data found"}

            # Calculate statistics
            durations = [row[1] for row in rows if row[1] is not None]
            error_count = sum(1 for row in rows if row[2] == "error")

            if not durations:
                return {"error": "No duration data found"}

            durations.sort()
            count = len(durations)

            return {
                "operation_name": operation_name or "all",
                "total_operations": count,
                "error_count": error_count,
                "error_rate": error_count / count * 100,
                "min_duration_ms": min(durations),
                "max_duration_ms": max(durations),
                "mean_duration_ms": sum(durations) / count,
                "median_duration_ms": durations[count // 2],
                "p95_duration_ms": durations[int(count * 0.95)],
                "p99_duration_ms": durations[int(count * 0.99)],
            }

    def cleanup_old_traces(self, days_to_keep: int = 7):
        """Remove traces older than specified days"""
        cutoff_date = (datetime.now() - timedelta(days=days_to_keep)).isoformat()

        with self._lock:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute("DELETE FROM traces WHERE start_time < ?", (cutoff_date,))
            deleted_count = cursor.rowcount

            conn.commit()
            conn.close()

            return deleted_count

    def export_traces(
        self,
        output_file: str,
        trace_ids: Optional[list[str]] = None,
        time_range: Optional[timedelta] = None,
    ) -> bool:
        """Export traces to JSON file"""
        try:
            with self._lock:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()

                # Build query
                query = "SELECT * FROM traces WHERE 1=1"
                params = []

                if trace_ids:
                    placeholders = ",".join("?" * len(trace_ids))
                    query += f" AND trace_id IN ({placeholders})"
                    params.extend(trace_ids)

                if time_range:
                    start_time = (datetime.now() - time_range).isoformat()
                    query += " AND start_time >= ?"
                    params.append(start_time)

                query += " ORDER BY start_time"

                cursor.execute(query, params)
                rows = cursor.fetchall()

                # Convert to list of dictionaries
                traces = []
                for row in rows:
                    trace = {
                        "id": row[0],
                        "trace_id": row[1],
                        "span_id": row[2],
                        "parent_span_id": row[3],
                        "operation_name": row[4],
                        "start_time": row[5],
                        "end_time": row[6],
                        "duration_ms": row[7],
                        "tags": json.loads(row[8]) if row[8] else {},
                        "logs": json.loads(row[9]) if row[9] else [],
                        "status": row[10],
                        "error_message": row[11],
                    }
                    traces.append(trace)

                conn.close()

                # Write to file
                output_path = Path(output_file)
                output_path.parent.mkdir(parents=True, exist_ok=True)

                with open(output_path, "w", encoding="utf-8") as f:
                    json.dump(
                        {
                            "export_timestamp": datetime.now().isoformat(),
                            "total_traces": len(traces),
                            "traces": traces,
                        },
                        f,
                        indent=2,
                        ensure_ascii=False,
                    )

                return True

        except Exception as e:
            print(f"Error exporting traces: {e}")
            return False

    def _store_span(self, span: TraceSpan):
        """Store span in database"""
        with self._lock:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute(
                """
                INSERT INTO traces (trace_id, span_id, parent_span_id, operation_name,
                                  start_time, end_time, duration_ms, tags, logs, status, error_message)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    span.trace_id,
                    span.span_id,
                    span.parent_span_id,
                    span.operation_name,
                    span.start_time,
                    span.end_time,
                    span.duration_ms,
                    json.dumps(span.tags) if span.tags else None,
                    json.dumps(span.logs) if span.logs else None,
                    span.status,
                    span.error_message,
                ),
            )

            conn.commit()
            conn.close()

    def _update_span(self, span: TraceSpan):
        """Update span in database"""
        with self._lock:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute(
                """
                UPDATE traces
                SET end_time = ?, duration_ms = ?, tags = ?, logs = ?, status = ?, error_message = ?
                WHERE span_id = ?
            """,
                (
                    span.end_time,
                    span.duration_ms,
                    json.dumps(span.tags) if span.tags else None,
                    json.dumps(span.logs) if span.logs else None,
                    span.status,
                    span.error_message,
                    span.span_id,
                ),
            )

            conn.commit()
            conn.close()

    def _calculate_duration(self, start_time: str, end_time: str) -> float:
        """Calculate duration in milliseconds"""
        start = datetime.fromisoformat(start_time)
        end = datetime.fromisoformat(end_time)
        return (end - start).total_seconds() * 1000


# Global tracer instance
_global_tracer: Optional[RequestTracer] = None


def get_tracer() -> RequestTracer:
    """Get or create global tracer"""
    global _global_tracer
    if _global_tracer is None:
        _global_tracer = RequestTracer()
    return _global_tracer


def setup_tracing(db_path: str = "traces.db") -> RequestTracer:
    """Setup global tracing"""
    global _global_tracer
    _global_tracer = RequestTracer(db_path)
    return _global_tracer


# Context manager for tracing
class TraceContext:
    """Context manager for tracing operations"""

    def __init__(self, operation_name: str, tags: Optional[dict[str, Any]] = None):
        self.operation_name = operation_name
        self.tags = tags or {}
        self.tracer = get_tracer()
        self.span = None

    def __enter__(self):
        self.span = self.tracer.start_span(self.operation_name, tags=self.tags)
        return self.span

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.span:
            error_message = str(exc_val) if exc_val else None
            self.tracer.finish_span(self.span.span_id, error_message)
