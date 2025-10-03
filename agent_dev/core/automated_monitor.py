#!/usr/bin/env python3
"""
🤖 AgentDev Automated Monitor - Hệ thống giám sát tự động
==========================================================

Hệ thống giám sát tự động cho AgentDev Unified để đảm bảo:
1. Continuous code quality monitoring
2. Proactive error detection
3. Automated alerts and notifications
4. Scheduled maintenance tasks
5. Integration with CI/CD pipeline

Author: StillMe AI Framework
Version: 1.0.0
Date: 2025-09-30
"""

import logging
import subprocess
import threading
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any

import psutil
import schedule


# Stub for AgentMode
class AgentMode:
    SENIOR = "senior"
    SIMPLE = "simple"


# Import AgentDev Unified
try:
    from agentdev import AgentDev
except ImportError:
    from agentdev import AgentDev

logger = logging.getLogger(__name__)


class MonitorStatus(Enum):
    """Trạng thái monitor"""

    ACTIVE = "active"
    INACTIVE = "inactive"
    ERROR = "error"
    MAINTENANCE = "maintenance"


class AlertLevel(Enum):
    """Mức độ cảnh báo"""

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class CodeQualityMetrics:
    """Metrics về code quality"""

    total_files: int
    files_with_errors: int
    total_errors: int
    syntax_errors: int
    import_errors: int
    undefined_names: int
    last_scan_time: datetime
    scan_duration_ms: float


@dataclass
class Alert:
    """Alert về code quality issues"""

    id: str
    level: AlertLevel
    title: str
    message: str
    timestamp: datetime
    file_path: str | None = None
    line_number: int | None = None
    error_type: str | None = None
    auto_fixable: bool = False


class AutomatedMonitor:
    """Hệ thống giám sát tự động cho AgentDev"""

    def __init__(self, project_root: str = ".", config: dict[str, Any] | None = None):
        self.project_root = Path(project_root)
        self.config = config or self._default_config()
        self.status = MonitorStatus.INACTIVE
        self.agentdev = None
        self.monitoring_thread = None
        self.stop_event = threading.Event()
        self.alerts = []
        self.metrics_history = []

        # Setup logging
        self._setup_logging()

        # Initialize AgentDev
        self._initialize_agentdev()

        # Setup monitoring schedules
        self._setup_schedules()

        logger.info("🤖 AgentDev Automated Monitor initialized")

    def _default_config(self) -> dict[str, Any]:
        """Default configuration"""
        return {
            "scan_interval_minutes": 15,  # Scan every 15 minutes
            "deep_scan_interval_hours": 2,  # Deep scan every 2 hours
            "alert_thresholds": {
                "max_errors_per_file": 10,
                "max_total_errors": 50,
                "max_syntax_errors": 5,
            },
            "auto_fix_enabled": True,
            "auto_fix_safe_only": True,
            "notifications": {"email": False, "slack": False, "console": True},
            "exclude_patterns": [
                "**/__pycache__/**",
                "**/node_modules/**",
                "**/venv/**",
                "**/.venv/**",
                "**/site-packages/**",
                "**/dist-packages/**",
                "**/backup_legacy/**",
                "**/tests/fixtures/**",
            ],
        }

    def _setup_logging(self):
        """Setup logging configuration"""
        log_dir = self.project_root / "logs"
        log_dir.mkdir(exist_ok=True)

        log_file = log_dir / f"agentdev_monitor_{datetime.now().strftime('%Y%m%d')}.log"

        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            handlers=[logging.FileHandler(log_file), logging.StreamHandler()],
        )

    def _initialize_agentdev(self):
        """Initialize AgentDev Unified"""
        try:
            self.agentdev = AgentDev(project_root=str(self.project_root))
            logger.info("✅ AgentDev Unified initialized successfully")
        except Exception as e:
            logger.error(f"❌ Failed to initialize AgentDev: {e}")
            self.status = MonitorStatus.ERROR

    def _setup_schedules(self):
        """Setup monitoring schedules"""
        # Regular code quality scan
        schedule.every(self.config["scan_interval_minutes"]).minutes.do(
            self._scheduled_quality_scan
        )

        # Deep scan with AgentDev analysis
        schedule.every(self.config["deep_scan_interval_hours"]).hours.do(
            self._scheduled_deep_scan
        )

        # Daily maintenance
        schedule.every().day.at("02:00").do(self._scheduled_maintenance)

        logger.info("📅 Monitoring schedules configured")

    def start_monitoring(self):
        """Start automated monitoring"""
        if self.status == MonitorStatus.ACTIVE:
            logger.warning("⚠️ Monitoring already active")
            return

        if not self.agentdev:
            logger.error("❌ Cannot start monitoring: AgentDev not initialized")
            return

        self.status = MonitorStatus.ACTIVE
        self.stop_event.clear()

        # Start monitoring thread
        self.monitoring_thread = threading.Thread(
            target=self._monitoring_loop, daemon=True
        )
        self.monitoring_thread.start()

        logger.info("🚀 Automated monitoring started")

        # Send startup alert
        self._send_alert(
            Alert(
                id=f"startup_{int(time.time())}",
                level=AlertLevel.INFO,
                title="AgentDev Monitor Started",
                message="Automated code quality monitoring is now active",
                timestamp=datetime.now(),
            )
        )

    def stop_monitoring(self):
        """Stop automated monitoring"""
        if self.status != MonitorStatus.ACTIVE:
            logger.warning("⚠️ Monitoring not active")
            return

        self.status = MonitorStatus.INACTIVE
        self.stop_event.set()

        if self.monitoring_thread:
            self.monitoring_thread.join(timeout=5)

        logger.info("🛑 Automated monitoring stopped")

    def _monitoring_loop(self):
        """Main monitoring loop"""
        logger.info("🔄 Monitoring loop started")

        while not self.stop_event.is_set():
            try:
                # Run scheduled tasks
                schedule.run_pending()

                # Check system health
                self._check_system_health()

                # Sleep for 1 minute
                time.sleep(60)

            except Exception as e:
                logger.error(f"❌ Error in monitoring loop: {e}")
                time.sleep(30)  # Short sleep on error

        logger.info("🔄 Monitoring loop stopped")

    def _scheduled_quality_scan(self):
        """Scheduled code quality scan"""
        logger.info("🔍 Running scheduled quality scan...")

        try:
            start_time = time.time()
            metrics = self._scan_code_quality()
            scan_duration = (time.time() - start_time) * 1000

            # Update metrics
            metrics.scan_duration_ms = scan_duration
            self.metrics_history.append(metrics)

            # Check for alerts
            self._check_quality_thresholds(metrics)

            logger.info(f"✅ Quality scan completed in {scan_duration:.1f}ms")
            logger.info(
                f"📊 Found {metrics.total_errors} errors in {metrics.files_with_errors} files"
            )

        except Exception as e:
            logger.error(f"❌ Error in quality scan: {e}")
            self._send_alert(
                Alert(
                    id=f"scan_error_{int(time.time())}",
                    level=AlertLevel.ERROR,
                    title="Quality Scan Failed",
                    message=f"Error during quality scan: {str(e)}",
                    timestamp=datetime.now(),
                )
            )

    def _scheduled_deep_scan(self):
        """Scheduled deep scan with AgentDev analysis"""
        logger.info("🔬 Running scheduled deep scan...")

        try:
            # Run comprehensive analysis
            task = "analyze code quality and identify critical issues"
            if self.agentdev and hasattr(self.agentdev, "execute_task"):
                result = self.agentdev.execute_task(task, AgentMode.SENIOR)
            else:
                result = "AgentDev not available"

            # Parse result and create alerts if needed
            if "❌" in result or "error" in result.lower():
                self._send_alert(
                    Alert(
                        id=f"deep_scan_{int(time.time())}",
                        level=AlertLevel.WARNING,
                        title="Deep Scan Issues Found",
                        message=f"AgentDev found issues: {result[:200]}...",
                        timestamp=datetime.now(),
                    )
                )

            logger.info("✅ Deep scan completed")

        except Exception as e:
            logger.error(f"❌ Error in deep scan: {e}")

    def _scheduled_maintenance(self):
        """Scheduled maintenance tasks"""
        logger.info("🔧 Running scheduled maintenance...")

        try:
            # Run cleanup tasks
            cleanup_task = "perform automated cleanup and optimization"
            if self.agentdev and hasattr(self.agentdev, "execute_task"):
                self.agentdev.execute_task(cleanup_task, AgentMode.SENIOR)

            # Clean up old metrics
            self._cleanup_old_metrics()

            # Clean up old alerts
            self._cleanup_old_alerts()

            logger.info("✅ Maintenance completed")

        except Exception as e:
            logger.error(f"❌ Error in maintenance: {e}")

    def _scan_code_quality(self) -> CodeQualityMetrics:
        """Scan code quality using flake8"""
        metrics = CodeQualityMetrics(
            total_files=0,
            files_with_errors=0,
            total_errors=0,
            syntax_errors=0,
            import_errors=0,
            undefined_names=0,
            last_scan_time=datetime.now(),
            scan_duration_ms=0,
        )

        try:
            # Run flake8 to scan for errors
            result = subprocess.run(
                [
                    "python",
                    "-m",
                    "flake8",
                    "--count",
                    "--select=E9,F63,F7,F82",
                    "--show-source",
                    "--statistics",
                    str(self.project_root),
                ],
                capture_output=True,
                text=True,
                timeout=60,
            )

            # Parse results
            if result.returncode != 0:
                output_lines = result.stdout.split("\n")
                for line in output_lines:
                    if ":" in line and ("E999" in line or "F821" in line):
                        metrics.total_errors += 1
                        if "E999" in line:
                            metrics.syntax_errors += 1
                        elif "F821" in line:
                            metrics.undefined_names += 1

            # Count files
            python_files = list(self.project_root.rglob("*.py"))
            metrics.total_files = len(python_files)

            # Count files with errors
            if metrics.total_errors > 0:
                metrics.files_with_errors = len(
                    {
                        line.split(":")[0]
                        for line in result.stdout.split("\n")
                        if ":" in line and ("E999" in line or "F821" in line)
                    }
                )

        except Exception as e:
            logger.error(f"❌ Error scanning code quality: {e}")

        return metrics

    def _check_quality_thresholds(self, metrics: CodeQualityMetrics):
        """Check if quality metrics exceed thresholds"""
        thresholds = self.config["alert_thresholds"]

        # Check total errors
        if metrics.total_errors > thresholds["max_total_errors"]:
            self._send_alert(
                Alert(
                    id=f"total_errors_{int(time.time())}",
                    level=AlertLevel.CRITICAL,
                    title="High Error Count",
                    message=f"Total errors ({metrics.total_errors}) exceeds threshold ({thresholds['max_total_errors']})",
                    timestamp=datetime.now(),
                    error_type="total_errors",
                )
            )

        # Check syntax errors
        if metrics.syntax_errors > thresholds["max_syntax_errors"]:
            self._send_alert(
                Alert(
                    id=f"syntax_errors_{int(time.time())}",
                    level=AlertLevel.ERROR,
                    title="High Syntax Error Count",
                    message=f"Syntax errors ({metrics.syntax_errors}) exceeds threshold ({thresholds['max_syntax_errors']})",
                    timestamp=datetime.now(),
                    error_type="syntax_errors",
                )
            )

        # Check files with errors
        if metrics.files_with_errors > 0:
            avg_errors_per_file = metrics.total_errors / metrics.files_with_errors
            if avg_errors_per_file > thresholds["max_errors_per_file"]:
                self._send_alert(
                    Alert(
                        id=f"errors_per_file_{int(time.time())}",
                        level=AlertLevel.WARNING,
                        title="High Errors Per File",
                        message=f"Average errors per file ({avg_errors_per_file:.1f}) exceeds threshold ({thresholds['max_errors_per_file']})",
                        timestamp=datetime.now(),
                        error_type="errors_per_file",
                    )
                )

    def _check_system_health(self):
        """Check system health"""
        try:
            # Check CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            if cpu_percent > 90:
                self._send_alert(
                    Alert(
                        id=f"high_cpu_{int(time.time())}",
                        level=AlertLevel.WARNING,
                        title="High CPU Usage",
                        message=f"CPU usage is {cpu_percent}%",
                        timestamp=datetime.now(),
                    )
                )

            # Check memory usage
            memory = psutil.virtual_memory()
            if memory.percent > 90:
                self._send_alert(
                    Alert(
                        id=f"high_memory_{int(time.time())}",
                        level=AlertLevel.WARNING,
                        title="High Memory Usage",
                        message=f"Memory usage is {memory.percent}%",
                        timestamp=datetime.now(),
                    )
                )

        except Exception as e:
            logger.error(f"❌ Error checking system health: {e}")

    def _send_alert(self, alert: Alert):
        """Send alert notification"""
        self.alerts.append(alert)

        # Console notification
        if self.config["notifications"]["console"]:
            level_emoji = {
                AlertLevel.INFO: "ℹ️",
                AlertLevel.WARNING: "⚠️",
                AlertLevel.ERROR: "❌",
                AlertLevel.CRITICAL: "🚨",
            }

            print(f"{level_emoji[alert.level]} {alert.title}: {alert.message}")

        # Log alert
        logger.info(f"Alert sent: {alert.title} - {alert.message}")

        # Auto-fix if enabled and fixable
        if (
            self.config["auto_fix_enabled"]
            and alert.auto_fixable
            and alert.level in [AlertLevel.WARNING, AlertLevel.ERROR]
        ):
            self._attempt_auto_fix(alert)

    def _attempt_auto_fix(self, alert: Alert):
        """Attempt to auto-fix the issue"""
        try:
            if alert.error_type == "syntax_errors":
                task = "fix critical syntax errors in the codebase"
                if self.agentdev and hasattr(self.agentdev, "execute_task"):
                    result = self.agentdev.execute_task(task, AgentMode.SENIOR)
                else:
                    result = "AgentDev not available"

                if "✅" in result:
                    logger.info("✅ Auto-fix successful")
                else:
                    logger.warning("⚠️ Auto-fix may have failed")

        except Exception as e:
            logger.error(f"❌ Error in auto-fix: {e}")

    def _cleanup_old_metrics(self):
        """Clean up old metrics data"""
        cutoff_time = datetime.now() - timedelta(days=7)
        self.metrics_history = [
            m for m in self.metrics_history if m.last_scan_time > cutoff_time
        ]

    def _cleanup_old_alerts(self):
        """Clean up old alerts"""
        cutoff_time = datetime.now() - timedelta(days=3)
        self.alerts = [a for a in self.alerts if a.timestamp > cutoff_time]

    def get_status(self) -> dict[str, Any]:
        """Get current monitor status"""
        return {
            "status": self.status.value,
            "agentdev_available": self.agentdev is not None,
            "total_alerts": len(self.alerts),
            "recent_alerts": len(
                [
                    a
                    for a in self.alerts
                    if a.timestamp > datetime.now() - timedelta(hours=1)
                ]
            ),
            "metrics_count": len(self.metrics_history),
            "last_scan": self.metrics_history[-1].last_scan_time.isoformat()
            if self.metrics_history
            else None,
        }

    def get_recent_alerts(self, hours: int = 24) -> list[dict]:
        """Get recent alerts"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        recent_alerts = [a for a in self.alerts if a.timestamp > cutoff_time]
        return [asdict(alert) for alert in recent_alerts]

    def get_metrics_summary(self) -> dict[str, Any]:
        """Get metrics summary"""
        if not self.metrics_history:
            return {"message": "No metrics available"}

        recent_metrics = self.metrics_history[-10:]  # Last 10 scans

        return {
            "total_scans": len(self.metrics_history),
            "recent_scans": len(recent_metrics),
            "avg_errors": sum(m.total_errors for m in recent_metrics)
            / len(recent_metrics),
            "avg_files_with_errors": sum(m.files_with_errors for m in recent_metrics)
            / len(recent_metrics),
            "avg_scan_duration_ms": sum(m.scan_duration_ms for m in recent_metrics)
            / len(recent_metrics),
            "last_scan": recent_metrics[-1].last_scan_time.isoformat(),
        }


# Example usage
if __name__ == "__main__":
    # Initialize monitor
    monitor = AutomatedMonitor(project_root=".")

    # Start monitoring
    monitor.start_monitoring()

    try:
        # Keep running
        while True:
            time.sleep(60)

            # Print status every hour
            if int(time.time()) % 3600 == 0:
                status = monitor.get_status()
                print(f"📊 Monitor Status: {status}")

    except KeyboardInterrupt:
        print("\n🛑 Stopping monitor...")
        monitor.stop_monitoring()
        print("✅ Monitor stopped")
