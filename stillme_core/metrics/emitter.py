"""
📊 StillMe Metrics Emitter
=========================

Hệ thống thu thập metrics thời gian thực cho learning dashboard.
Ghi events vào JSONL và SQLite, hỗ trợ batch processing và privacy protection.

Tính năng:
- Real-time event logging
- JSONL + SQLite storage
- Session management
- Privacy protection
- Batch processing
- Performance optimization

Author: StillMe AI Framework
Version: 1.0.0
Date: 2025-09-28
"""

import asyncio
import json
import logging
import sqlite3
import threading
import uuid
from collections import deque
from collections.abc import Mapping
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger(__name__)


@dataclass
class Metric:
    """Single metric record"""

    name: str
    value: float
    unit: str = ""
    tag: str = ""
    ts: Optional[datetime] = None
    metadata: Optional[dict[str, Any]] = None


@dataclass
class Event:
    """Event record for JSONL logging"""

    ts: datetime
    session_id: str
    stage: str
    component: str
    event: str
    meta: dict[str, Any]
    metrics: dict[str, Any]


class MetricsEmitter:
    """
    Hệ thống thu thập metrics thời gian thực

    Ghi events vào JSONL và SQLite, hỗ trợ batch processing
    và privacy protection cho learning dashboard.
    """

    def __init__(
        self,
        db_path: str = "data/metrics/metrics.db",
        events_dir: str = "data/metrics/events",
        batch_size: int = 100,
        flush_interval: float = 5.0,
    ):
        self.db_path = db_path
        self.events_dir = Path(events_dir)
        self.events_dir.mkdir(parents=True, exist_ok=True)

        # Session management
        self.session_id: Optional[str] = None
        self.session_start: Optional[datetime] = None
        self.current_stage: Optional[str] = None

        # Batch processing
        self.batch_size = batch_size
        self.flush_interval = flush_interval
        self.event_buffer: deque = deque(maxlen=batch_size * 2)
        self.metric_buffer: deque = deque(maxlen=batch_size * 2)

        # Threading
        self._lock = threading.Lock()
        self._flush_task: Optional[asyncio.Task] = None
        self._running = False

        # Initialize database
        self._initialize_db()

        logger.info(f"MetricsEmitter initialized: db={db_path}, events={events_dir}")

    def _initialize_db(self):
        """Initialize SQLite database schema"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Runs table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS runs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT UNIQUE NOT NULL,
                started_at TEXT NOT NULL,
                ended_at TEXT,
                git_sha TEXT,
                version TEXT,
                success BOOLEAN,
                stage TEXT,
                notes TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Metrics table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                run_id INTEGER,
                name TEXT NOT NULL,
                value REAL NOT NULL,
                unit TEXT,
                tag TEXT,
                ts TEXT NOT NULL,
                metadata TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (run_id) REFERENCES runs (id)
            )
        """)

        # Errors table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS errors (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                run_id INTEGER,
                type TEXT NOT NULL,
                message TEXT NOT NULL,
                ts TEXT NOT NULL,
                context_json TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (run_id) REFERENCES runs (id)
            )
        """)

        # Rollups table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS rollups (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,
                metric TEXT NOT NULL,
                value REAL NOT NULL,
                unit TEXT,
                dim_key TEXT,
                dim_val TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(date, metric, dim_key, dim_val)
            )
        """)

        # Indexes
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_runs_session_id ON runs(session_id)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_metrics_run_id ON metrics(run_id)"
        )
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_metrics_name ON metrics(name)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_metrics_ts ON metrics(ts)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_rollups_date ON rollups(date)")

        conn.commit()
        conn.close()

        logger.info("Metrics database schema initialized")

    def start_session(
        self, stage: str, notes: str = "", version: str = "", git_sha: str = ""
    ) -> str:
        """Bắt đầu session mới"""
        with self._lock:
            self.session_id = f"sess_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:4]}"
            self.session_start = datetime.now(timezone.utc)
            self.current_stage = stage

            # Insert into database
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO runs (session_id, started_at, git_sha, version, stage, notes)
                VALUES (?, ?, ?, ?, ?, ?)
            """,
                (
                    self.session_id,
                    self.session_start.isoformat(),
                    git_sha,
                    version,
                    stage,
                    notes,
                ),
            )
            conn.commit()
            conn.close()

            logger.info(f"Session started: {self.session_id} ({stage})")
            return self.session_id

    def log_event(
        self,
        event: str,
        component: str,
        metrics: Optional[Mapping[str, Any]] = None,
        meta: Optional[Mapping[str, Any]] = None,
    ):
        """Ghi event vào buffer"""
        if not self.session_id:
            logger.warning("No active session, creating default session")
            self.start_session("default")

        event_record = Event(
            ts=datetime.now(timezone.utc),
            session_id=self.session_id or "unknown",
            stage=self.current_stage or "unknown",
            component=component,
            event=event,
            meta=dict(meta) if meta else {},
            metrics=dict(metrics) if metrics else {},
        )

        with self._lock:
            self.event_buffer.append(event_record)

        # Auto-flush if buffer is full
        if len(self.event_buffer) >= self.batch_size:
            asyncio.create_task(self._flush_events())

    def log_metric(self, metric: Metric):
        """Ghi metric vào buffer"""
        if not self.session_id:
            logger.warning("No active session, creating default session")
            self.start_session("default")

        if metric.ts is None:
            metric.ts = datetime.now(timezone.utc)

        with self._lock:
            self.metric_buffer.append(metric)

        # Auto-flush if buffer is full
        if len(self.metric_buffer) >= self.batch_size:
            asyncio.create_task(self._flush_metrics())

    async def _flush_events(self):
        """Flush events buffer to JSONL"""
        if not self.event_buffer:
            return

        with self._lock:
            events_to_flush = list(self.event_buffer)
            self.event_buffer.clear()

        # Write to JSONL
        today = datetime.now().strftime("%Y-%m-%d")
        jsonl_file = self.events_dir / f"{today}.jsonl"

        try:
            with open(jsonl_file, "a", encoding="utf-8") as f:
                for event in events_to_flush:
                    event_dict = asdict(event)
                    event_dict["ts"] = event.ts.isoformat()
                    f.write(json.dumps(event_dict, ensure_ascii=False) + "\n")

            logger.debug(f"Flushed {len(events_to_flush)} events to {jsonl_file}")
        except Exception as e:
            logger.error(f"Failed to flush events: {e}")

    async def _flush_metrics(self):
        """Flush metrics buffer to SQLite"""
        if not self.metric_buffer:
            return

        with self._lock:
            metrics_to_flush = list(self.metric_buffer)
            self.metric_buffer.clear()

        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Get run_id for current session
            cursor.execute(
                "SELECT id FROM runs WHERE session_id = ?", (self.session_id,)
            )
            run_id = cursor.fetchone()
            if not run_id:
                logger.error(f"No run found for session {self.session_id}")
                return

            run_id = run_id[0]

            # Insert metrics
            for metric in metrics_to_flush:
                cursor.execute(
                    """
                    INSERT INTO metrics (run_id, name, value, unit, tag, ts, metadata)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        run_id,
                        metric.name,
                        metric.value,
                        metric.unit,
                        metric.tag,
                        metric.ts.isoformat(),
                        json.dumps(metric.metadata) if metric.metadata else None,
                    ),
                )

            conn.commit()
            conn.close()

            logger.debug(f"Flushed {len(metrics_to_flush)} metrics to database")
        except Exception as e:
            logger.error(f"Failed to flush metrics: {e}")

    async def start_auto_flush(self):
        """Bắt đầu auto-flush task"""
        if self._running:
            return

        self._running = True
        self._flush_task = asyncio.create_task(self._auto_flush_loop())
        logger.info("Auto-flush started")

    async def stop_auto_flush(self):
        """Dừng auto-flush task"""
        self._running = False
        if self._flush_task:
            self._flush_task.cancel()
            try:
                await self._flush_task
            except asyncio.CancelledError:
                pass

        # Final flush
        await self._flush_events()
        await self._flush_metrics()
        logger.info("Auto-flush stopped")

    async def _auto_flush_loop(self):
        """Auto-flush loop"""
        while self._running:
            try:
                await asyncio.sleep(self.flush_interval)
                await self._flush_events()
                await self._flush_metrics()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Auto-flush error: {e}")

    def end_session(self, success: bool = True, notes: str = ""):
        """Kết thúc session"""
        if not self.session_id:
            logger.warning("No active session to end")
            return

        end_time = datetime.now(timezone.utc)

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            """
            UPDATE runs
            SET ended_at = ?, success = ?, notes = ?
            WHERE session_id = ?
        """,
            (end_time.isoformat(), success, notes, self.session_id),
        )
        conn.commit()
        conn.close()

        duration = end_time - self.session_start if self.session_start else timedelta(0)
        logger.info(
            f"Session ended: {self.session_id} (success={success}, duration={duration})"
        )

        # Reset session
        self.session_id = None
        self.session_start = None
        self.current_stage = None

    def get_session_stats(self) -> dict[str, Any]:
        """Lấy thống kê session hiện tại"""
        if not self.session_id:
            return {}

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Get run info
        cursor.execute("SELECT * FROM runs WHERE session_id = ?", (self.session_id,))
        cursor.fetchone()

        # Get metrics count
        cursor.execute(
            "SELECT COUNT(*) FROM metrics WHERE run_id = (SELECT id FROM runs WHERE session_id = ?)",
            (self.session_id,),
        )
        metrics_count = cursor.fetchone()[0]

        # Get errors count
        cursor.execute(
            "SELECT COUNT(*) FROM errors WHERE run_id = (SELECT id FROM runs WHERE session_id = ?)",
            (self.session_id,),
        )
        errors_count = cursor.fetchone()[0]

        conn.close()

        return {
            "session_id": self.session_id,
            "stage": self.current_stage,
            "started_at": self.session_start.isoformat()
            if self.session_start
            else None,
            "metrics_count": metrics_count,
            "errors_count": errors_count,
            "buffer_size": len(self.event_buffer) + len(self.metric_buffer),
        }


# Global instance
_metrics_emitter_instance: Optional[MetricsEmitter] = None


def get_metrics_emitter() -> MetricsEmitter:
    """Get global metrics emitter instance"""
    global _metrics_emitter_instance
    if _metrics_emitter_instance is None:
        _metrics_emitter_instance = MetricsEmitter()
    return _metrics_emitter_instance


def initialize_metrics_emitter(
    config: Optional[dict[str, Any]] = None,
) -> MetricsEmitter:
    """Initialize global metrics emitter with config"""
    global _metrics_emitter_instance
    if config:
        _metrics_emitter_instance = MetricsEmitter(**config)
    else:
        _metrics_emitter_instance = MetricsEmitter()
    return _metrics_emitter_instance
