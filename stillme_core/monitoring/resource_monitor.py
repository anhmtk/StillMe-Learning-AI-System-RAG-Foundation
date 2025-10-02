"""
📊 StillMe Resource Monitor
==========================

Advanced resource monitoring system for AGI learning automation.
Monitors CPU, RAM, disk, network, and token usage with intelligent
resource management and predictive scaling.

Tính năng:
- Real-time resource monitoring với psutil
- Token budget tracking và management
- Predictive resource scaling
- Resource-aware learning scheduling
- Memory leak detection
- Performance bottleneck identification
- AGI-optimized resource allocation

Author: StillMe AI Framework
Version: 2.0.0
Date: 2025-09-28
"""

import asyncio
import json
import logging
import threading
import time
from collections import deque
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from typing import Any, Callable, Optional

try:
    import psutil

    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False
    logging.warning("psutil not available. Install with: pip install psutil")

logger = logging.getLogger(__name__)


@dataclass
class ResourceThresholds:
    """Resource thresholds for monitoring"""

    cpu_percent: float = 70.0
    memory_percent: float = 80.0
    memory_mb: int = 1024
    disk_percent: float = 90.0
    network_bandwidth_mbps: float = 100.0
    token_budget_daily: int = 10000
    token_budget_hourly: int = 1000
    learning_session_duration_minutes: int = 30
    max_concurrent_sessions: int = 1


@dataclass
class ResourceMetrics:
    """Current resource metrics"""

    timestamp: datetime
    cpu_percent: float
    memory_percent: float
    memory_used_mb: float
    memory_available_mb: float
    disk_percent: float
    disk_free_gb: float
    network_sent_mb: float
    network_recv_mb: float
    network_speed_mbps: float
    processes_count: int
    load_average: tuple[float, float, float]
    token_usage_daily: int
    token_usage_hourly: int
    token_remaining_daily: int
    token_remaining_hourly: int
    learning_sessions_active: int
    learning_sessions_total: int


@dataclass
class ResourceAlert:
    """Resource alert"""

    alert_id: str
    timestamp: datetime
    alert_type: str  # cpu_high, memory_high, disk_full, token_low, etc.
    severity: str  # low, medium, high, critical
    message: str
    current_value: float
    threshold_value: float
    recommendation: str
    resolved: bool = False


class TokenBudgetManager:
    """Token budget management for AGI learning"""

    def __init__(self, daily_budget: int = 10000, hourly_budget: int = 1000):
        self.daily_budget = daily_budget
        self.hourly_budget = hourly_budget
        self.daily_usage = 0
        self.hourly_usage = 0
        self.last_reset_daily = datetime.now().date()
        self.last_reset_hourly = datetime.now().hour
        self.usage_history = deque(maxlen=1000)
        self.lock = threading.Lock()

    def reset_if_needed(self):
        """Reset counters if needed"""
        now = datetime.now()

        with self.lock:
            # Reset daily counter
            if now.date() != self.last_reset_daily:
                self.daily_usage = 0
                self.last_reset_daily = now.date()
                logger.info("Daily token budget reset")

            # Reset hourly counter
            if now.hour != self.last_reset_hourly:
                self.hourly_usage = 0
                self.last_reset_hourly = now.hour
                logger.info("Hourly token budget reset")

    def consume_tokens(self, tokens: int) -> bool:
        """
        Consume tokens if budget allows

        Args:
            tokens: Number of tokens to consume

        Returns:
            bool: True if consumption successful, False if budget exceeded
        """
        self.reset_if_needed()

        with self.lock:
            if (
                self.daily_usage + tokens <= self.daily_budget
                and self.hourly_usage + tokens <= self.hourly_budget
            ):
                self.daily_usage += tokens
                self.hourly_usage += tokens

                # Record usage
                self.usage_history.append(
                    {
                        "timestamp": datetime.now(),
                        "tokens": tokens,
                        "daily_usage": self.daily_usage,
                        "hourly_usage": self.hourly_usage,
                    }
                )

                logger.debug(
                    f"Consumed {tokens} tokens. Daily: {self.daily_usage}/{self.daily_budget}, Hourly: {self.hourly_usage}/{self.hourly_budget}"
                )
                return True
            else:
                logger.warning(
                    f"Token budget exceeded. Requested: {tokens}, Daily: {self.daily_usage}/{self.daily_budget}, Hourly: {self.hourly_usage}/{self.hourly_budget}"
                )
                return False

    def get_remaining_tokens(self) -> tuple[int, int]:
        """Get remaining tokens (daily, hourly)"""
        self.reset_if_needed()

        with self.lock:
            return (
                max(0, self.daily_budget - self.daily_usage),
                max(0, self.hourly_budget - self.hourly_usage),
            )

    def get_usage_stats(self) -> dict[str, Any]:
        """Get usage statistics"""
        self.reset_if_needed()

        with self.lock:
            return {
                "daily_budget": self.daily_budget,
                "hourly_budget": self.hourly_budget,
                "daily_usage": self.daily_usage,
                "hourly_usage": self.hourly_usage,
                "daily_remaining": max(0, self.daily_budget - self.daily_usage),
                "hourly_remaining": max(0, self.hourly_budget - self.hourly_usage),
                "daily_usage_percent": (self.daily_usage / self.daily_budget) * 100,
                "hourly_usage_percent": (self.hourly_usage / self.hourly_budget) * 100,
                "usage_history_count": len(self.usage_history),
            }


class ResourceMonitor:
    """
    Advanced resource monitoring system for AGI learning
    """

    def __init__(self, thresholds: ResourceThresholds = None):
        self.thresholds = thresholds or ResourceThresholds()
        self.logger = logging.getLogger(__name__)

        # Token budget manager
        self.token_manager = TokenBudgetManager(
            self.thresholds.token_budget_daily, self.thresholds.token_budget_hourly
        )

        # Monitoring state
        self.is_monitoring = False
        self.monitoring_task: Optional[asyncio.Task] = None
        self.metrics_history = deque(maxlen=1000)
        self.alerts: list[ResourceAlert] = []
        self.alert_callbacks: list[Callable[[ResourceAlert], None]] = []

        # Performance tracking
        self.performance_baseline = None
        self.performance_degradation_threshold = 0.2  # 20% degradation

        # Network monitoring
        self.network_baseline = None
        self.last_network_check = None

        # Process tracking
        self.learning_processes = set()
        self.process_start_times = {}

        if not PSUTIL_AVAILABLE:
            self.logger.warning(
                "psutil not available. Resource monitoring will be limited."
            )

    async def start_monitoring(self, interval: int = 10):
        """
        Start resource monitoring

        Args:
            interval: Monitoring interval in seconds
        """
        if self.is_monitoring:
            self.logger.warning("Resource monitoring already started")
            return

        self.is_monitoring = True
        self.monitoring_task = asyncio.create_task(self._monitoring_loop(interval))
        self.logger.info(f"Resource monitoring started with {interval}s interval")

    async def stop_monitoring(self):
        """Stop resource monitoring"""
        if not self.is_monitoring:
            return

        self.is_monitoring = False
        if self.monitoring_task:
            self.monitoring_task.cancel()
            try:
                await self.monitoring_task
            except asyncio.CancelledError:
                pass

        self.logger.info("Resource monitoring stopped")

    async def _monitoring_loop(self, interval: int):
        """Main monitoring loop"""
        while self.is_monitoring:
            try:
                # Collect metrics
                metrics = await self._collect_metrics()
                self.metrics_history.append(metrics)

                # Check thresholds and generate alerts
                await self._check_thresholds(metrics)

                # Update performance baseline
                self._update_performance_baseline(metrics)

                # Clean up old alerts
                self._cleanup_old_alerts()

                await asyncio.sleep(interval)

            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error in monitoring loop: {e}")
                await asyncio.sleep(interval)

    async def _collect_metrics(self) -> ResourceMetrics:
        """Collect current resource metrics"""
        if not PSUTIL_AVAILABLE:
            # Return dummy metrics if psutil not available
            return ResourceMetrics(
                timestamp=datetime.now(),
                cpu_percent=0.0,
                memory_percent=0.0,
                memory_used_mb=0.0,
                memory_available_mb=0.0,
                disk_percent=0.0,
                disk_free_gb=0.0,
                network_sent_mb=0.0,
                network_recv_mb=0.0,
                network_speed_mbps=0.0,
                processes_count=0,
                load_average=(0.0, 0.0, 0.0),
                token_usage_daily=self.token_manager.daily_usage,
                token_usage_hourly=self.token_manager.hourly_usage,
                token_remaining_daily=self.token_manager.get_remaining_tokens()[0],
                token_remaining_hourly=self.token_manager.get_remaining_tokens()[1],
                learning_sessions_active=len(self.learning_processes),
                learning_sessions_total=len(self.process_start_times),
            )

        # Collect system metrics
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage("/")

        # Network metrics
        network = psutil.net_io_counters()
        network_sent_mb = network.bytes_sent / (1024 * 1024)
        network_recv_mb = network.bytes_recv / (1024 * 1024)

        # Calculate network speed
        network_speed_mbps = 0.0
        if self.last_network_check:
            time_diff = time.time() - self.last_network_check
            if time_diff > 0:
                sent_diff = network_sent_mb - getattr(self, "_last_sent_mb", 0)
                recv_diff = network_recv_mb - getattr(self, "_last_recv_mb", 0)
                total_diff = sent_diff + recv_diff
                network_speed_mbps = (total_diff * 8) / time_diff  # Convert to Mbps

        self._last_sent_mb = network_sent_mb
        self._last_recv_mb = network_recv_mb
        self.last_network_check = time.time()

        # Process count
        processes_count = len(psutil.pids())

        # Load average (Unix-like systems)
        try:
            load_average = psutil.getloadavg()
        except AttributeError:
            load_average = (0.0, 0.0, 0.0)

        # Token usage
        daily_remaining, hourly_remaining = self.token_manager.get_remaining_tokens()

        return ResourceMetrics(
            timestamp=datetime.now(),
            cpu_percent=cpu_percent,
            memory_percent=memory.percent,
            memory_used_mb=memory.used / (1024 * 1024),
            memory_available_mb=memory.available / (1024 * 1024),
            disk_percent=disk.percent,
            disk_free_gb=disk.free / (1024 * 1024 * 1024),
            network_sent_mb=network_sent_mb,
            network_recv_mb=network_recv_mb,
            network_speed_mbps=network_speed_mbps,
            processes_count=processes_count,
            load_average=load_average,
            token_usage_daily=self.token_manager.daily_usage,
            token_usage_hourly=self.token_manager.hourly_usage,
            token_remaining_daily=daily_remaining,
            token_remaining_hourly=hourly_remaining,
            learning_sessions_active=len(self.learning_processes),
            learning_sessions_total=len(self.process_start_times),
        )

    async def _check_thresholds(self, metrics: ResourceMetrics):
        """Check resource thresholds and generate alerts"""
        alerts = []

        # CPU threshold
        if metrics.cpu_percent > self.thresholds.cpu_percent:
            alerts.append(
                ResourceAlert(
                    alert_id=f"cpu_high_{int(time.time())}",
                    timestamp=datetime.now(),
                    alert_type="cpu_high",
                    severity="high" if metrics.cpu_percent > 90 else "medium",
                    message=f"High CPU usage: {metrics.cpu_percent:.1f}%",
                    current_value=metrics.cpu_percent,
                    threshold_value=self.thresholds.cpu_percent,
                    recommendation="Consider reducing concurrent learning sessions or optimizing algorithms",
                )
            )

        # Memory threshold
        if metrics.memory_percent > self.thresholds.memory_percent:
            alerts.append(
                ResourceAlert(
                    alert_id=f"memory_high_{int(time.time())}",
                    timestamp=datetime.now(),
                    alert_type="memory_high",
                    severity="critical" if metrics.memory_percent > 95 else "high",
                    message=f"High memory usage: {metrics.memory_percent:.1f}% ({metrics.memory_used_mb:.1f}MB)",
                    current_value=metrics.memory_percent,
                    threshold_value=self.thresholds.memory_percent,
                    recommendation="Consider freeing memory or reducing batch sizes",
                )
            )

        # Disk threshold
        if metrics.disk_percent > self.thresholds.disk_percent:
            alerts.append(
                ResourceAlert(
                    alert_id=f"disk_high_{int(time.time())}",
                    timestamp=datetime.now(),
                    alert_type="disk_high",
                    severity="critical",
                    message=f"High disk usage: {metrics.disk_percent:.1f}% ({metrics.disk_free_gb:.1f}GB free)",
                    current_value=metrics.disk_percent,
                    threshold_value=self.thresholds.disk_percent,
                    recommendation="Clean up temporary files or expand storage",
                )
            )

        # Token budget
        if (
            metrics.token_remaining_daily < self.thresholds.token_budget_daily * 0.1
        ):  # Less than 10% remaining
            alerts.append(
                ResourceAlert(
                    alert_id=f"token_low_daily_{int(time.time())}",
                    timestamp=datetime.now(),
                    alert_type="token_low_daily",
                    severity="high",
                    message=f"Low daily token budget: {metrics.token_remaining_daily} remaining",
                    current_value=metrics.token_remaining_daily,
                    threshold_value=self.thresholds.token_budget_daily * 0.1,
                    recommendation="Consider reducing learning frequency or increasing budget",
                )
            )

        if (
            metrics.token_remaining_hourly < self.thresholds.token_budget_hourly * 0.1
        ):  # Less than 10% remaining
            alerts.append(
                ResourceAlert(
                    alert_id=f"token_low_hourly_{int(time.time())}",
                    timestamp=datetime.now(),
                    alert_type="token_low_hourly",
                    severity="medium",
                    message=f"Low hourly token budget: {metrics.token_remaining_hourly} remaining",
                    current_value=metrics.token_remaining_hourly,
                    threshold_value=self.thresholds.token_budget_hourly * 0.1,
                    recommendation="Wait for hourly reset or reduce learning intensity",
                )
            )

        # Add alerts and notify callbacks
        for alert in alerts:
            self.alerts.append(alert)
            for callback in self.alert_callbacks:
                try:
                    callback(alert)
                except Exception as e:
                    self.logger.error(f"Error in alert callback: {e}")

    def _update_performance_baseline(self, metrics: ResourceMetrics):
        """Update performance baseline for degradation detection"""
        if not self.performance_baseline:
            self.performance_baseline = {
                "cpu_percent": metrics.cpu_percent,
                "memory_percent": metrics.memory_percent,
                "response_time": 1.0,  # Placeholder
                "timestamp": metrics.timestamp,
            }
        else:
            # Update baseline with exponential moving average
            alpha = 0.1  # Smoothing factor
            self.performance_baseline["cpu_percent"] = (
                alpha * metrics.cpu_percent
                + (1 - alpha) * self.performance_baseline["cpu_percent"]
            )
            self.performance_baseline["memory_percent"] = (
                alpha * metrics.memory_percent
                + (1 - alpha) * self.performance_baseline["memory_percent"]
            )

    def _cleanup_old_alerts(self):
        """Clean up old resolved alerts"""
        cutoff_time = datetime.now() - timedelta(hours=24)
        self.alerts = [
            alert
            for alert in self.alerts
            if not alert.resolved or alert.timestamp > cutoff_time
        ]

    def add_alert_callback(self, callback: Callable[[ResourceAlert], None]):
        """Add alert callback function"""
        self.alert_callbacks.append(callback)

    def remove_alert_callback(self, callback: Callable[[ResourceAlert], None]):
        """Remove alert callback function"""
        if callback in self.alert_callbacks:
            self.alert_callbacks.remove(callback)

    def can_start_learning_session(self) -> tuple[bool, str]:
        """
        Check if a new learning session can be started

        Returns:
            Tuple[bool, str]: (can_start, reason)
        """
        if not self.metrics_history:
            return True, "No metrics available"

        latest_metrics = self.metrics_history[-1]

        # Check concurrent sessions
        if (
            latest_metrics.learning_sessions_active
            >= self.thresholds.max_concurrent_sessions
        ):
            return (
                False,
                f"Maximum concurrent sessions reached ({self.thresholds.max_concurrent_sessions})",
            )

        # Check CPU usage
        if latest_metrics.cpu_percent > self.thresholds.cpu_percent:
            return (
                False,
                f"CPU usage too high: {latest_metrics.cpu_percent:.1f}% > {self.thresholds.cpu_percent}%",
            )

        # Check memory usage
        if latest_metrics.memory_percent > self.thresholds.memory_percent:
            return (
                False,
                f"Memory usage too high: {latest_metrics.memory_percent:.1f}% > {self.thresholds.memory_percent}%",
            )

        # Check token budget
        if latest_metrics.token_remaining_daily < 100:  # Minimum tokens needed
            return (
                False,
                f"Insufficient daily token budget: {latest_metrics.token_remaining_daily}",
            )

        if latest_metrics.token_remaining_hourly < 50:  # Minimum tokens needed
            return (
                False,
                f"Insufficient hourly token budget: {latest_metrics.token_remaining_hourly}",
            )

        return True, "All checks passed"

    def start_learning_session(self, session_id: str) -> bool:
        """Start tracking a learning session"""
        self.learning_processes.add(session_id)
        self.process_start_times[session_id] = datetime.now()
        self.logger.info(f"Started tracking learning session: {session_id}")
        return True

    def end_learning_session(self, session_id: str) -> bool:
        """End tracking a learning session"""
        if session_id in self.learning_processes:
            self.learning_processes.remove(session_id)
            if session_id in self.process_start_times:
                duration = datetime.now() - self.process_start_times[session_id]
                del self.process_start_times[session_id]
                self.logger.info(
                    f"Ended tracking learning session: {session_id} (duration: {duration})"
                )
            return True
        return False

    def get_current_metrics(self) -> Optional[ResourceMetrics]:
        """Get current resource metrics"""
        if self.metrics_history:
            return self.metrics_history[-1]
        return None

    def get_metrics_summary(self) -> dict[str, Any]:
        """Get metrics summary"""
        if not self.metrics_history:
            return {"error": "No metrics available"}

        latest = self.metrics_history[-1]
        recent_metrics = list(self.metrics_history)[-10:]  # Last 10 measurements

        # Calculate averages
        avg_cpu = sum(m.cpu_percent for m in recent_metrics) / len(recent_metrics)
        avg_memory = sum(m.memory_percent for m in recent_metrics) / len(recent_metrics)

        return {
            "current": asdict(latest),
            "averages": {
                "cpu_percent": avg_cpu,
                "memory_percent": avg_memory,
                "samples": len(recent_metrics),
            },
            "token_budget": self.token_manager.get_usage_stats(),
            "alerts_count": len([a for a in self.alerts if not a.resolved]),
            "learning_sessions": {
                "active": len(self.learning_processes),
                "total_tracked": len(self.process_start_times),
            },
            "monitoring_status": {
                "is_monitoring": self.is_monitoring,
                "metrics_count": len(self.metrics_history),
                "thresholds": asdict(self.thresholds),
            },
        }

    def export_metrics(self, file_path: str):
        """Export metrics to JSON file"""
        try:
            export_data = {
                "export_timestamp": datetime.now().isoformat(),
                "metrics_summary": self.get_metrics_summary(),
                "recent_metrics": [
                    asdict(m) for m in list(self.metrics_history)[-100:]
                ],  # Last 100
                "active_alerts": [asdict(a) for a in self.alerts if not a.resolved],
                "thresholds": asdict(self.thresholds),
            }

            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False, default=str)

            self.logger.info(f"Metrics exported to {file_path}")

        except Exception as e:
            self.logger.error(f"Failed to export metrics: {e}")


# Global resource monitor instance
_resource_monitor_instance: Optional[ResourceMonitor] = None


def get_resource_monitor(thresholds: ResourceThresholds = None) -> ResourceMonitor:
    """Get global resource monitor instance"""
    global _resource_monitor_instance
    if _resource_monitor_instance is None:
        _resource_monitor_instance = ResourceMonitor(thresholds)
    return _resource_monitor_instance


async def initialize_resource_monitoring(
    thresholds: ResourceThresholds = None, interval: int = 10
) -> ResourceMonitor:
    """Initialize and start resource monitoring"""
    monitor = get_resource_monitor(thresholds)
    await monitor.start_monitoring(interval)
    return monitor
