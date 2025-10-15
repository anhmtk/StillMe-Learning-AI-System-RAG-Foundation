"""
StillMe Health Check System
Provides liveness and readiness probes for Kubernetes/Docker deployments
"""

import logging
import sqlite3
import time
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any

import psutil

logger = logging.getLogger(__name__)


class HealthStatus(Enum):
    """Health check status enumeration"""

    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"
    DEGRADED = "degraded"


@dataclass
class HealthCheck:
    """Individual health check result"""

    name: str
    status: HealthStatus
    message: str
    duration_ms: float
    timestamp: datetime
    details: dict[str, Any] | None = None


@dataclass
class HealthResponse:
    """Overall health response"""

    status: HealthStatus
    timestamp: datetime
    version: str
    environment: str
    uptime_seconds: float
    checks: dict[str, HealthCheck]
    metrics: dict[str, Any]


class HealthChecker:
    """Main health check orchestrator"""

    def __init__(self, config: dict[str, Any] | None = None):
        self.config = config or {}
        self.start_time = time.time()
        self._version = self.config.get("version", "1.0.0")
        self.environment = self.config.get("environment", "development")
        self.checks = {}

    @property
    def version(self) -> str:
        """Get version string - deterministic fallback"""
        try:
            import importlib.metadata

            return importlib.metadata.version("stillme_core")
        except Exception:
            return self._version or "0.1.0"

    def check_health(self) -> dict[str, Any]:
        """Check overall system health - lightweight, no external calls"""
        try:
            # Basic system checks without external dependencies
            components = {
                "core": "ok",
                "storage": "ok" if self._check_basic_storage() else "degraded",
            }

            return {
                "status": "ok",
                "components": components,
                "version": self.version,
                "timestamp": time.time(),
            }
        except Exception as e:
            return {
                "status": "error",
                "components": {"core": "error"},
                "version": self.version,
                "error": str(e),
                "timestamp": time.time(),
            }

    def get_status(self) -> dict[str, Any]:
        """Get simplified status - calls check_health and extracts key info"""
        health = self.check_health()
        return {
            "status": health["status"],
            "version": health["version"],
            "uptime": time.time() - self.start_time,
        }

    def _check_basic_storage(self) -> bool:
        """Basic storage check without external dependencies"""
        try:
            import tempfile

            # Try to create a temp file to check basic storage
            with tempfile.NamedTemporaryFile(delete=True) as f:
                f.write(b"test")
                return True
        except Exception:
            return False

    def check_database(self) -> HealthCheck:
        """Check database connectivity and performance"""
        start_time = time.time()

        try:
            # Check database connection
            db_path = self.config.get("database", {}).get("path", "./data/stillme.db")
            conn = sqlite3.connect(db_path, timeout=5.0)
            cursor = conn.cursor()

            # Simple query to test connectivity
            cursor.execute("SELECT 1")
            cursor.fetchone()

            # Check database size and performance
            cursor.execute("PRAGMA database_list")
            db_info = cursor.fetchall()

            conn.close()

            duration_ms = max(0.001, (time.time() - start_time) * 1000)

            return HealthCheck(
                name="database",
                status=HealthStatus.HEALTHY,
                message="Database connection successful",
                duration_ms=duration_ms,
                timestamp=datetime.now(),
                details={
                    "db_path": db_path,
                    "db_count": len(db_info),
                    "response_time_ms": duration_ms,
                },
            )

        except Exception as e:
            duration_ms = max(0.001, (time.time() - start_time) * 1000)
            logger.error(f"Database health check failed: {e}")

            return HealthCheck(
                name="database",
                status=HealthStatus.UNHEALTHY,
                message=f"Database connection failed: {str(e)}",
                duration_ms=duration_ms,
                timestamp=datetime.now(),
                details={"error": str(e)},
            )

    def check_memory(self) -> HealthCheck:
        """Check memory usage"""
        start_time = time.time()

        try:
            memory = psutil.virtual_memory()
            process = psutil.Process()
            process_memory = process.memory_info()

            # Check if memory usage is within acceptable limits
            memory_usage_percent = memory.percent
            process_memory_mb = process_memory.rss / 1024 / 1024

            # Define thresholds
            memory_threshold = 90.0  # 90% system memory
            process_memory_threshold = 2048  # 2GB process memory

            if memory_usage_percent > memory_threshold:
                status = HealthStatus.UNHEALTHY
                message = f"System memory usage too high: {memory_usage_percent:.1f}%"
            elif process_memory_mb > process_memory_threshold:
                status = HealthStatus.DEGRADED
                message = f"Process memory usage high: {process_memory_mb:.1f}MB"
            else:
                status = HealthStatus.HEALTHY
                message = "Memory usage within normal limits"

            duration_ms = max(0.001, (time.time() - start_time) * 1000)

            return HealthCheck(
                name="memory",
                status=status,
                message=message,
                duration_ms=duration_ms,
                timestamp=datetime.now(),
                details={
                    "system_memory_percent": memory_usage_percent,
                    "process_memory_mb": process_memory_mb,
                    "available_memory_gb": memory.available / 1024 / 1024 / 1024,
                },
            )

        except Exception as e:
            duration_ms = max(0.001, (time.time() - start_time) * 1000)
            logger.error(f"Memory health check failed: {e}")

            return HealthCheck(
                name="memory",
                status=HealthStatus.UNHEALTHY,
                message=f"Memory check failed: {str(e)}",
                duration_ms=duration_ms,
                timestamp=datetime.now(),
                details={"error": str(e)},
            )

    def check_disk(self) -> HealthCheck:
        """Check disk space"""
        start_time = time.time()

        try:
            disk = psutil.disk_usage("/")
            disk_usage_percent = (disk.used / disk.total) * 100

            # Define threshold
            disk_threshold = 90.0  # 90% disk usage

            if disk_usage_percent > disk_threshold:
                status = HealthStatus.UNHEALTHY
                message = f"Disk usage too high: {disk_usage_percent:.1f}%"
            else:
                status = HealthStatus.HEALTHY
                message = "Disk usage within normal limits"

            duration_ms = (time.time() - start_time) * 1000

            return HealthCheck(
                name="disk",
                status=status,
                message=message,
                duration_ms=duration_ms,
                timestamp=datetime.now(),
                details={
                    "disk_usage_percent": disk_usage_percent,
                    "free_space_gb": disk.free / 1024 / 1024 / 1024,
                    "total_space_gb": disk.total / 1024 / 1024 / 1024,
                },
            )

        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            logger.error(f"Disk health check failed: {e}")

            return HealthCheck(
                name="disk",
                status=HealthStatus.UNHEALTHY,
                message=f"Disk check failed: {str(e)}",
                duration_ms=duration_ms,
                timestamp=datetime.now(),
                details={"error": str(e)},
            )

    def check_agentdev(self) -> HealthCheck:
        """Check AgentDev system health"""
        start_time = time.time()

        try:
            # Check if AgentDev modules are importable
            from agent_dev.core.agentdev import AgentDev

            # Create a simple test instance
            agentdev = AgentDev(project_root=".")

            # Test basic functionality
            test_result = agentdev.execute_task("health check test")

            if (
                "success" in str(test_result).lower()
                or "completed" in str(test_result).lower()
            ):
                status = HealthStatus.HEALTHY
                message = "AgentDev system operational"
            else:
                status = HealthStatus.DEGRADED
                message = "AgentDev system responding but with issues"

            duration_ms = max(0.001, (time.time() - start_time) * 1000)

            return HealthCheck(
                name="agentdev",
                status=status,
                message=message,
                duration_ms=duration_ms,
                timestamp=datetime.now(),
                details={
                    "test_result": test_result[:100],  # Truncate for brevity
                    "response_time_ms": duration_ms,
                },
            )

        except Exception as e:
            duration_ms = max(0.001, (time.time() - start_time) * 1000)
            logger.error(f"AgentDev health check failed: {e}")

            return HealthCheck(
                name="agentdev",
                status=HealthStatus.UNHEALTHY,
                message=f"AgentDev system failed: {str(e)}",
                duration_ms=duration_ms,
                timestamp=datetime.now(),
                details={"error": str(e)},
            )

    def run_all_checks(self) -> HealthResponse:
        """Run all health checks and return comprehensive response"""
        checks = {}

        # Run individual checks
        checks["database"] = self.check_database()
        checks["memory"] = self.check_memory()
        checks["disk"] = self.check_disk()
        checks["agentdev"] = self.check_agentdev()

        # Determine overall status
        unhealthy_count = sum(
            1 for check in checks.values() if check.status == HealthStatus.UNHEALTHY
        )
        degraded_count = sum(
            1 for check in checks.values() if check.status == HealthStatus.DEGRADED
        )

        if unhealthy_count > 0:
            overall_status = HealthStatus.UNHEALTHY
        elif degraded_count > 0:
            overall_status = HealthStatus.DEGRADED
        else:
            overall_status = HealthStatus.HEALTHY

        # Calculate metrics
        total_duration = sum(check.duration_ms for check in checks.values())
        uptime_seconds = time.time() - self.start_time

        metrics = {
            "total_checks": len(checks),
            "healthy_checks": sum(
                1 for check in checks.values() if check.status == HealthStatus.HEALTHY
            ),
            "degraded_checks": degraded_count,
            "unhealthy_checks": unhealthy_count,
            "total_check_duration_ms": total_duration,
            "uptime_seconds": uptime_seconds,
        }

        return HealthResponse(
            status=overall_status,
            timestamp=datetime.now(),
            version=self.version,
            environment=self.environment,
            uptime_seconds=uptime_seconds,
            checks=checks,
            metrics=metrics,
        )


def create_health_endpoints(app, config: dict[str, Any]):
    """Create health check endpoints for the application"""
    from .health_integration import (
        register_health_endpoint,
        register_liveness_endpoint,
        register_metrics_endpoint,
    )

    health_checker = HealthChecker(config)

    # Register endpoints using adapter for compatibility (liveness first for test compatibility)
    liveness_result = register_liveness_endpoint(app, health_checker)
    health_result = register_health_endpoint(app, health_checker)
    metrics_result = register_metrics_endpoint(app, health_checker)

    logger.info(
        f"Health endpoints registered: health={health_result['used_style']}, liveness={liveness_result['used_style']}, metrics={metrics_result['used_style']}"
    )

    # Fallback: if adapter failed, use decorator style
    if "failed" in health_result["used_style"]:

        @app.route("/healthz")
        def health_probe():
            """Health probe - comprehensive check"""
            try:
                health_response = health_checker.run_all_checks()
                if health_response.status == HealthStatus.HEALTHY:
                    return health_response.__dict__, 200
                elif health_response.status == HealthStatus.DEGRADED:
                    return health_response.__dict__, 200
                else:
                    return health_response.__dict__, 503
            except Exception as e:
                logger.error(f"Health probe failed: {e}")
                return {"status": "error", "error": str(e)}, 503

    if "failed" in liveness_result["used_style"]:

        @app.route("/readyz")
        def liveness_probe():
            """Liveness probe - simple check"""
            try:
                return {"status": "alive", "timestamp": datetime.now().isoformat()}, 200
            except Exception as e:
                logger.error(f"Liveness probe failed: {e}")
                return {"status": "dead", "error": str(e)}, 503

    @app.route("/metrics")
    def metrics_endpoint():
        """Prometheus metrics endpoint"""
        try:
            health_response = health_checker.run_all_checks()

            # Convert to Prometheus format
            metrics = []
            metrics.append(
                f'stillme_health_status{{environment="{health_response.environment}"}} {1 if health_response.status == HealthStatus.HEALTHY else 0}'
            )
            metrics.append(f"stillme_uptime_seconds {health_response.uptime_seconds}")
            metrics.append(
                f'stillme_version_info{{version="{health_response.version}"}} 1'
            )

            for check_name, check in health_response.checks.items():
                status_value = 1 if check.status == HealthStatus.HEALTHY else 0
                metrics.append(
                    f'stillme_health_check_status{{check="{check_name}"}} {status_value}'
                )
                metrics.append(
                    f'stillme_health_check_duration_ms{{check="{check_name}"}} {check.duration_ms}'
                )

            return "\n".join(metrics), 200, {"Content-Type": "text/plain"}

        except Exception as e:
            logger.error(f"Metrics endpoint failed: {e}")
            return f"# Error: {e}\n", 500, {"Content-Type": "text/plain"}
