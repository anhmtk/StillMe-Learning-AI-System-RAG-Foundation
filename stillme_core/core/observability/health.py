"""
Health Monitor Module
=====================

Monitors system health and provides health check endpoints.
"""

import json
import sqlite3
import threading
import time
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any

import psutil


class HealthStatus(Enum):
    """Health status levels"""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


@dataclass
class HealthCheck:
    """Individual health check result"""

    name: str
    status: HealthStatus
    message: str
    details: dict[str, Any] | None = None
    response_time_ms: float | None = None
    last_checked: str | None = None


@dataclass
class SystemHealth:
    """Overall system health status"""

    status: HealthStatus
    timestamp: str
    checks: list[HealthCheck]
    summary: dict[str, Any]


class HealthMonitor:
    """System health monitoring"""

    def __init__(self, db_path: str = "health.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        # Thread lock for database operations
        self._lock = threading.Lock()

        # Health check functions
        self._health_checks: dict[str, Callable[[], HealthCheck]] = {}

        # Initialize database
        self._init_database()

        # Register default health checks
        self._register_default_checks()

    def _init_database(self):
        """Initialize SQLite database for health check storage"""
        with self._lock:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Create health_checks table
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS health_checks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    status TEXT NOT NULL,
                    message TEXT NOT NULL,
                    details TEXT,
                    response_time_ms REAL,
                    timestamp TEXT NOT NULL
                )
            """
            )

            # Create index for faster queries
            cursor.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_health_checks_name_timestamp
                ON health_checks(name, timestamp)
            """
            )

            conn.commit()
            conn.close()

    def _register_default_checks(self):
        """Register default system health checks"""
        self.register_check("system_cpu", self._check_cpu_usage)
        self.register_check("system_memory", self._check_memory_usage)
        self.register_check("system_disk", self._check_disk_usage)
        self.register_check("system_load", self._check_system_load)
        self.register_check("database_connectivity", self._check_database_connectivity)
        self.register_check("log_files", self._check_log_files)

    def register_check(self, name: str, check_function: Callable[[], HealthCheck]):
        """Register a health check function"""
        self._health_checks[name] = check_function

    def unregister_check(self, name: str):
        """Unregister a health check"""
        if name in self._health_checks:
            del self._health_checks[name]

    def run_health_checks(self) -> SystemHealth:
        """Run all registered health checks"""
        checks = []
        overall_status = HealthStatus.HEALTHY

        for name, check_function in self._health_checks.items():
            try:
                start_time = time.time()
                check_result = check_function()
                response_time = (time.time() - start_time) * 1000

                # Update response time
                check_result.response_time_ms = response_time
                check_result.last_checked = datetime.now().isoformat()

                checks.append(check_result)

                # Update overall status
                if check_result.status == HealthStatus.UNHEALTHY:
                    overall_status = HealthStatus.UNHEALTHY
                elif (
                    check_result.status == HealthStatus.DEGRADED
                    and overall_status == HealthStatus.HEALTHY
                ):
                    overall_status = HealthStatus.DEGRADED

                # Store in database
                self._store_health_check(check_result)

            except Exception as e:
                error_check = HealthCheck(
                    name=name,
                    status=HealthStatus.UNHEALTHY,
                    message=f"Health check failed: {e!s}",
                    response_time_ms=(time.time() - start_time) * 1000,
                    last_checked=datetime.now().isoformat(),
                )
                checks.append(error_check)
                overall_status = HealthStatus.UNHEALTHY

        # Create summary
        summary = self._create_summary(checks)

        system_health = SystemHealth(
            status=overall_status,
            timestamp=datetime.now().isoformat(),
            checks=checks,
            summary=summary,
        )

        return system_health

    def get_health_status(self) -> SystemHealth:
        """Get current health status"""
        return self.run_health_checks()

    def get_health_history(
        self, check_name: str | None = None, hours: int = 24
    ) -> list[HealthCheck]:
        """Get health check history"""
        with self._lock:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cutoff_time = (datetime.now() - timedelta(hours=hours)).isoformat()

            query = "SELECT * FROM health_checks WHERE timestamp >= ?"
            params = [cutoff_time]

            if check_name:
                query += " AND name = ?"
                params.append(check_name)

            query += " ORDER BY timestamp DESC"

            cursor.execute(query, params)
            rows = cursor.fetchall()
            conn.close()

            checks = []
            for row in rows:
                check = HealthCheck(
                    name=row[1],
                    status=HealthStatus(row[2]),
                    message=row[3],
                    details=json.loads(row[4]) if row[4] else None,
                    response_time_ms=row[5],
                    last_checked=row[6],
                )
                checks.append(check)

            return checks

    def get_health_summary(self, hours: int = 24) -> dict[str, Any]:
        """Get health summary statistics"""
        history = self.get_health_history(hours=hours)

        if not history:
            return {"error": "No health check data available"}

        # Group by check name
        check_groups = {}
        for check in history:
            if check.name not in check_groups:
                check_groups[check.name] = []
            check_groups[check.name].append(check)

        summary = {
            "time_range_hours": hours,
            "total_checks": len(history),
            "unique_checks": len(check_groups),
            "check_summaries": {},
        }

        for name, checks in check_groups.items():
            status_counts = {}
            response_times = []

            for check in checks:
                status = check.status.value
                status_counts[status] = status_counts.get(status, 0) + 1

                if check.response_time_ms:
                    response_times.append(check.response_time_ms)

            check_summary = {
                "total_runs": len(checks),
                "status_counts": status_counts,
                "latest_status": checks[0].status.value,
                "latest_message": checks[0].message,
            }

            if response_times:
                check_summary.update(
                    {
                        "avg_response_time_ms": sum(response_times)
                        / len(response_times),
                        "min_response_time_ms": min(response_times),
                        "max_response_time_ms": max(response_times),
                    }
                )

            summary["check_summaries"][name] = check_summary

        return summary

    def _check_cpu_usage(self) -> HealthCheck:
        """Check CPU usage"""
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            cpu_count = psutil.cpu_count()

            if cpu_percent > 90:
                status = HealthStatus.UNHEALTHY
                message = f"High CPU usage: {cpu_percent:.1f}%"
            elif cpu_percent > 70:
                status = HealthStatus.DEGRADED
                message = f"Elevated CPU usage: {cpu_percent:.1f}%"
            else:
                status = HealthStatus.HEALTHY
                message = f"CPU usage normal: {cpu_percent:.1f}%"

            return HealthCheck(
                name="system_cpu",
                status=status,
                message=message,
                details={
                    "cpu_percent": cpu_percent,
                    "cpu_count": cpu_count,
                    "thresholds": {"warning": 70, "critical": 90},
                },
            )
        except Exception as e:
            return HealthCheck(
                name="system_cpu",
                status=HealthStatus.UNHEALTHY,
                message=f"Failed to check CPU usage: {e!s}",
            )

    def _check_memory_usage(self) -> HealthCheck:
        """Check memory usage"""
        try:
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            available_gb = memory.available / (1024**3)

            if memory_percent > 90:
                status = HealthStatus.UNHEALTHY
                message = f"High memory usage: {memory_percent:.1f}%"
            elif memory_percent > 80:
                status = HealthStatus.DEGRADED
                message = f"Elevated memory usage: {memory_percent:.1f}%"
            else:
                status = HealthStatus.HEALTHY
                message = f"Memory usage normal: {memory_percent:.1f}%"

            return HealthCheck(
                name="system_memory",
                status=status,
                message=message,
                details={
                    "memory_percent": memory_percent,
                    "available_gb": available_gb,
                    "total_gb": memory.total / (1024**3),
                    "thresholds": {"warning": 80, "critical": 90},
                },
            )
        except Exception as e:
            return HealthCheck(
                name="system_memory",
                status=HealthStatus.UNHEALTHY,
                message=f"Failed to check memory usage: {e!s}",
            )

    def _check_disk_usage(self) -> HealthCheck:
        """Check disk usage"""
        try:
            disk = psutil.disk_usage("/")
            disk_percent = (disk.used / disk.total) * 100
            free_gb = disk.free / (1024**3)

            if disk_percent > 95:
                status = HealthStatus.UNHEALTHY
                message = f"Critical disk usage: {disk_percent:.1f}%"
            elif disk_percent > 85:
                status = HealthStatus.DEGRADED
                message = f"High disk usage: {disk_percent:.1f}%"
            else:
                status = HealthStatus.HEALTHY
                message = f"Disk usage normal: {disk_percent:.1f}%"

            return HealthCheck(
                name="system_disk",
                status=status,
                message=message,
                details={
                    "disk_percent": disk_percent,
                    "free_gb": free_gb,
                    "total_gb": disk.total / (1024**3),
                    "thresholds": {"warning": 85, "critical": 95},
                },
            )
        except Exception as e:
            return HealthCheck(
                name="system_disk",
                status=HealthStatus.UNHEALTHY,
                message=f"Failed to check disk usage: {e!s}",
            )

    def _check_system_load(self) -> HealthCheck:
        """Check system load average"""
        try:
            if hasattr(psutil, "getloadavg"):
                load_avg = psutil.getloadavg()
                cpu_count = psutil.cpu_count()

                # Calculate load as percentage of CPU cores
                load_percent = (load_avg[0] / cpu_count) * 100  # type: ignore

                if load_percent > 100:
                    status = HealthStatus.UNHEALTHY
                    message = f"System overloaded: {load_avg[0]:.2f} load average"
                elif load_percent > 80:
                    status = HealthStatus.DEGRADED
                    message = f"High system load: {load_avg[0]:.2f} load average"
                else:
                    status = HealthStatus.HEALTHY
                    message = f"System load normal: {load_avg[0]:.2f} load average"

                return HealthCheck(
                    name="system_load",
                    status=status,
                    message=message,
                    details={
                        "load_1min": load_avg[0],
                        "load_5min": load_avg[1],
                        "load_15min": load_avg[2],
                        "cpu_count": cpu_count,
                        "load_percent": load_percent,
                    },
                )
            else:
                return HealthCheck(
                    name="system_load",
                    status=HealthStatus.UNKNOWN,
                    message="Load average not available on this system",
                )
        except Exception as e:
            return HealthCheck(
                name="system_load",
                status=HealthStatus.UNHEALTHY,
                message=f"Failed to check system load: {e!s}",
            )

    def _check_database_connectivity(self) -> HealthCheck:
        """Check database connectivity"""
        try:
            # Test SQLite database connectivity
            test_db = Path("test_health.db")
            conn = sqlite3.connect(test_db)
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
            conn.close()
            test_db.unlink()  # Clean up test file

            if result and result[0] == 1:
                return HealthCheck(
                    name="database_connectivity",
                    status=HealthStatus.HEALTHY,
                    message="Database connectivity normal",
                )
            else:
                return HealthCheck(
                    name="database_connectivity",
                    status=HealthStatus.UNHEALTHY,
                    message="Database connectivity test failed",
                )
        except Exception as e:
            return HealthCheck(
                name="database_connectivity",
                status=HealthStatus.UNHEALTHY,
                message=f"Database connectivity failed: {e!s}",
            )

    def _check_log_files(self) -> HealthCheck:
        """Check log file status"""
        try:
            log_dir = Path("logs")
            if not log_dir.exists():
                return HealthCheck(
                    name="log_files",
                    status=HealthStatus.HEALTHY,
                    message="No log directory found (normal for new installations)",
                )

            log_files = list(log_dir.glob("*.jsonl"))
            if not log_files:
                return HealthCheck(
                    name="log_files",
                    status=HealthStatus.HEALTHY,
                    message="No log files found",
                )

            total_size = sum(f.stat().st_size for f in log_files)
            total_size_mb = total_size / (1024 * 1024)

            if total_size_mb > 1000:  # > 1GB
                status = HealthStatus.DEGRADED
                message = f"Large log files: {total_size_mb:.1f} MB"
            else:
                status = HealthStatus.HEALTHY
                message = f"Log files normal: {total_size_mb:.1f} MB"

            return HealthCheck(
                name="log_files",
                status=status,
                message=message,
                details={
                    "log_file_count": len(log_files),
                    "total_size_mb": total_size_mb,
                    "log_files": [str(f) for f in log_files],
                },
            )
        except Exception as e:
            return HealthCheck(
                name="log_files",
                status=HealthStatus.UNHEALTHY,
                message=f"Failed to check log files: {e!s}",
            )

    def _create_summary(self, checks: list[HealthCheck]) -> dict[str, Any]:
        """Create summary from health checks"""
        total_checks = len(checks)
        healthy_checks = sum(1 for c in checks if c.status == HealthStatus.HEALTHY)
        degraded_checks = sum(1 for c in checks if c.status == HealthStatus.DEGRADED)
        unhealthy_checks = sum(1 for c in checks if c.status == HealthStatus.UNHEALTHY)

        avg_response_time = None
        response_times = [
            c.response_time_ms for c in checks if c.response_time_ms is not None
        ]
        if response_times:
            avg_response_time = sum(response_times) / len(response_times)

        return {
            "total_checks": total_checks,
            "healthy_checks": healthy_checks,
            "degraded_checks": degraded_checks,
            "unhealthy_checks": unhealthy_checks,
            "health_percentage": (
                (healthy_checks / total_checks * 100) if total_checks > 0 else 0
            ),
            "avg_response_time_ms": avg_response_time,
        }

    def _store_health_check(self, check: HealthCheck):
        """Store health check result in database"""
        with self._lock:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute(
                """
                INSERT INTO health_checks (name, status, message, details, response_time_ms, timestamp)
                VALUES (?, ?, ?, ?, ?, ?)
            """,
                (
                    check.name,
                    check.status.value,
                    check.message,
                    json.dumps(check.details) if check.details else None,
                    check.response_time_ms,
                    check.last_checked,
                ),
            )

            conn.commit()
            conn.close()

    def cleanup_old_checks(self, days_to_keep: int = 7):
        """Remove health checks older than specified days"""
        cutoff_date = (datetime.now() - timedelta(days=days_to_keep)).isoformat()

        with self._lock:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute(
                "DELETE FROM health_checks WHERE timestamp < ?", (cutoff_date,)
            )
            deleted_count = cursor.rowcount

            conn.commit()
            conn.close()

            return deleted_count


# Global health monitor instance
_global_health_monitor: HealthMonitor | None = None


def get_health_monitor() -> HealthMonitor:
    """Get or create global health monitor"""
    global _global_health_monitor
    if _global_health_monitor is None:
        _global_health_monitor = HealthMonitor()
    return _global_health_monitor


def setup_health_monitoring(db_path: str = "health.db") -> HealthMonitor:
    """Setup global health monitoring"""
    global _global_health_monitor
    _global_health_monitor = HealthMonitor(db_path)
    return _global_health_monitor
