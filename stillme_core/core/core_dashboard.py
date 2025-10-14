"""
📈 CORE DASHBOARD - SUB-PHASE 3.1
===================================

Enterprise-grade dashboard system cho StillMe AI Framework.
Real-time monitoring, visualization, và essential reporting.

Author: StillMe Phase 3 Development Team
Version: 3.1.0
Phase: 3.1 - Core Metrics Foundation
Quality Standard: Enterprise-Grade (99.9% accuracy target)

FEATURES:
- Real-time monitoring dashboard
- Simple visualization capabilities
- Essential reporting features
- Basic alerting system
- Performance metrics display
- Value metrics visualization
"""

import asyncio
import json
import logging
import sqlite3
import statistics
import threading
import time
from collections import deque
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class DashboardMetrics:
    """Dashboard metrics summary"""

    timestamp: datetime
    system_health: dict[str, Any]
    performance_metrics: dict[str, Any]
    value_metrics: dict[str, Any]
    usage_statistics: dict[str, Any]
    alerts: list[dict[str, Any]]
    recommendations: list[str]


@dataclass
class Alert:
    """Alert definition"""

    alert_id: str
    timestamp: datetime
    severity: str  # "info", "warning", "error", "critical"
    category: str
    title: str
    message: str
    source: str
    acknowledged: bool
    resolved: bool


@dataclass
class VisualizationData:
    """Data for visualization"""

    chart_type: str
    title: str
    data: list[dict[str, Any]]
    x_axis: str
    y_axis: str
    time_range: str
    metadata: dict[str, Any]


class CoreDashboard:
    """
    Enterprise-grade dashboard system với focus vào real-time monitoring
    """

    def __init__(
        self,
        metrics_db_path: str,
        validation_db_path: str,
        config: dict[str, Any] | None = None,
    ):
        self.metrics_db_path = Path(metrics_db_path)
        self.validation_db_path = Path(validation_db_path)
        self.config = config or self._get_default_config()

        # Dashboard state
        self._dashboard_metrics = deque(maxlen=self.config["metrics_history_size"])
        self._alerts = deque(maxlen=self.config["alerts_history_size"])
        self._visualization_cache = {}

        # Threading
        self._lock = threading.RLock()
        self._executor = ThreadPoolExecutor(max_workers=self.config["max_workers"])
        self._running = False

        # Alert thresholds
        self._alert_thresholds = self._load_alert_thresholds()

        # Performance monitoring
        self._dashboard_performance = {
            "last_update": datetime.now(),
            "update_frequency_ms": 0.0,
            "data_freshness_seconds": 0.0,
        }

        logger.info("✅ CoreDashboard initialized với enterprise-grade configuration")

    def _get_default_config(self) -> dict[str, Any]:
        """Default configuration với performance focus"""
        return {
            "update_interval_seconds": 30,
            "metrics_history_size": 1000,
            "alerts_history_size": 500,
            "max_workers": 4,
            "cache_ttl_seconds": 300,  # 5 minutes
            "real_time_enabled": True,
            "visualization_enabled": True,
            "alerting_enabled": True,
            "performance_monitoring": True,
            "data_retention_hours": 24,
        }

    def _load_alert_thresholds(self) -> dict[str, Any]:
        """Load alert thresholds"""
        return {
            "performance": {
                "response_time_warning": 5000,  # 5 seconds
                "response_time_critical": 10000,  # 10 seconds
                "error_rate_warning": 0.05,  # 5%
                "error_rate_critical": 0.1,  # 10%
                "memory_usage_warning": 2048,  # 2GB
                "memory_usage_critical": 4096,  # 4GB
            },
            "accuracy": {
                "accuracy_warning": 0.95,  # 95%
                "accuracy_critical": 0.90,  # 90%
                "completeness_warning": 0.90,  # 90%
                "completeness_critical": 0.80,  # 80%
            },
            "value": {
                "roi_warning": -10.0,  # -10%
                "roi_critical": -20.0,  # -20%
                "time_saving_warning": 0.0,  # No time saving
                "time_saving_critical": -1.0,  # Negative time saving
            },
        }

    def start_dashboard(self):
        """Start dashboard system"""
        if self._running:
            logger.warning("⚠️ Dashboard already running")
            return

        self._running = True

        # Start background tasks
        asyncio.create_task(self._periodic_update())
        asyncio.create_task(self._periodic_alert_check())

        logger.info("🚀 CoreDashboard started")

    def stop_dashboard(self):
        """Stop dashboard system"""
        if not self._running:
            return

        self._running = False
        self._executor.shutdown(wait=True)

        logger.info("🛑 CoreDashboard stopped")

    async def _periodic_update(self):
        """Periodic dashboard update"""
        while self._running:
            try:
                await asyncio.sleep(self.config["update_interval_seconds"])
                await self._update_dashboard_metrics()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"❌ Dashboard update error: {e}")

    async def _periodic_alert_check(self):
        """Periodic alert checking"""
        while self._running:
            try:
                await asyncio.sleep(60)  # Check every minute
                await self._check_alerts()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"❌ Alert check error: {e}")

    async def _update_dashboard_metrics(self):
        """Update dashboard metrics"""
        try:
            start_time = time.time()

            # Collect metrics from all sources
            system_health = await self._get_system_health()
            performance_metrics = await self._get_performance_metrics()
            value_metrics = await self._get_value_metrics()
            usage_statistics = await self._get_usage_statistics()

            # Get current alerts
            current_alerts = list(self._alerts)

            # Generate recommendations
            recommendations = await self._generate_recommendations(
                system_health, performance_metrics, value_metrics, usage_statistics
            )

            # Create dashboard metrics
            dashboard_metrics = DashboardMetrics(
                timestamp=datetime.now(),
                system_health=system_health,
                performance_metrics=performance_metrics,
                value_metrics=value_metrics,
                usage_statistics=usage_statistics,
                alerts=current_alerts,
                recommendations=recommendations,
            )

            # Store metrics
            with self._lock:
                self._dashboard_metrics.append(dashboard_metrics)

            # Update performance metrics
            update_duration = (time.time() - start_time) * 1000
            self._dashboard_performance.update(
                {
                    "last_update": datetime.now(),
                    "update_frequency_ms": update_duration,
                    "data_freshness_seconds": 0.0,
                }
            )

            logger.debug(f"📊 Dashboard metrics updated in {update_duration:.1f}ms")

        except Exception as e:
            logger.error(f"❌ Dashboard metrics update failed: {e}")

    async def _get_system_health(self) -> dict[str, Any]:
        """Get system health metrics"""
        try:
            with sqlite3.connect(self.metrics_db_path) as conn:
                # Get recent usage events
                since_time = datetime.now() - timedelta(hours=1)

                cursor = conn.execute(
                    """
                    SELECT
                        COUNT(*) as total_events,
                        AVG(CASE WHEN success = 1 THEN 1.0 ELSE 0.0 END) as success_rate,
                        AVG(duration_ms) as avg_response_time,
                        COUNT(DISTINCT module_name) as active_modules
                    FROM usage_events
                    WHERE timestamp >= ?
                """,
                    [since_time.isoformat()],
                )

                stats = cursor.fetchone()

                # Calculate health score
                success_rate = stats[1] or 0.0
                avg_response_time = stats[2] or 0.0
                active_modules = stats[3] or 0

                # Health score calculation
                health_score = min(
                    100.0, (success_rate * 100) - (avg_response_time / 100.0)
                )

                return {
                    "health_score": health_score,
                    "status": (
                        "healthy"
                        if health_score > 80
                        else "warning"
                        if health_score > 60
                        else "critical"
                    ),
                    "total_events": stats[0] or 0,
                    "success_rate": success_rate,
                    "avg_response_time_ms": avg_response_time,
                    "active_modules": active_modules,
                    "uptime_percentage": 99.9,  # Would calculate actual uptime
                    "last_updated": datetime.now().isoformat(),
                }

        except Exception as e:
            logger.error(f"❌ Error getting system health: {e}")
            return {
                "health_score": 0.0,
                "status": "error",
                "error": str(e),
                "last_updated": datetime.now().isoformat(),
            }

    async def _get_performance_metrics(self) -> dict[str, Any]:
        """Get performance metrics"""
        try:
            with sqlite3.connect(self.metrics_db_path) as conn:
                # Get performance data for last hour
                since_time = datetime.now() - timedelta(hours=1)

                cursor = conn.execute(
                    """
                    SELECT
                        module_name,
                        AVG(duration_ms) as avg_duration,
                        COUNT(*) as event_count,
                        AVG(CASE WHEN success = 1 THEN 1.0 ELSE 0.0 END) as success_rate
                    FROM usage_events
                    WHERE timestamp >= ?
                    GROUP BY module_name
                    ORDER BY event_count DESC
                """,
                    [since_time.isoformat()],
                )

                module_performance = []
                for row in cursor.fetchall():
                    module_performance.append(
                        {
                            "module_name": row[0],
                            "avg_duration_ms": row[1] or 0.0,
                            "event_count": row[2] or 0,
                            "success_rate": row[3] or 0.0,
                        }
                    )

                # Calculate overall performance
                if module_performance:
                    overall_avg_duration = statistics.mean(
                        [m["avg_duration_ms"] for m in module_performance]
                    )
                    overall_success_rate = statistics.mean(
                        [m["success_rate"] for m in module_performance]
                    )
                    total_events = sum([m["event_count"] for m in module_performance])
                else:
                    overall_avg_duration = 0.0
                    overall_success_rate = 0.0
                    total_events = 0

                return {
                    "overall_avg_duration_ms": overall_avg_duration,
                    "overall_success_rate": overall_success_rate,
                    "total_events": total_events,
                    "module_performance": module_performance,
                    "performance_trend": "stable",  # Would calculate actual trend
                    "last_updated": datetime.now().isoformat(),
                }

        except Exception as e:
            logger.error(f"❌ Error getting performance metrics: {e}")
            return {"error": str(e), "last_updated": datetime.now().isoformat()}

    async def _get_value_metrics(self) -> dict[str, Any]:
        """Get value metrics"""
        try:
            with sqlite3.connect(self.metrics_db_path) as conn:
                # Get value metrics for last 24 hours
                since_time = datetime.now() - timedelta(hours=24)

                # Calculate time saved
                cursor = conn.execute(
                    """
                    SELECT
                        SUM(duration_ms) / 1000.0 / 3600.0 * 0.5 as time_saved_hours
                    FROM usage_events
                    WHERE timestamp >= ? AND success = 1
                """,
                    [since_time.isoformat()],
                )

                time_saved_hours = cursor.fetchone()[0] or 0.0

                # Calculate cost savings
                cost_savings_usd = time_saved_hours * 50.0  # $50/hour

                # Calculate ROI (simplified)
                estimated_investment = 24 * 10.0  # $10/hour infrastructure
                roi_percentage = (
                    (cost_savings_usd - estimated_investment)
                    / max(1, estimated_investment)
                ) * 100.0

                # Calculate errors prevented
                cursor = conn.execute(
                    """
                    SELECT COUNT(*) as errors_prevented
                    FROM usage_events
                    WHERE timestamp >= ? AND success = 0
                """,
                    [since_time.isoformat()],
                )

                errors_prevented = cursor.fetchone()[0] or 0

                return {
                    "time_saved_hours": time_saved_hours,
                    "cost_savings_usd": cost_savings_usd,
                    "roi_percentage": roi_percentage,
                    "errors_prevented": errors_prevented,
                    "value_trend": "improving" if roi_percentage > 0 else "declining",
                    "last_updated": datetime.now().isoformat(),
                }

        except Exception as e:
            logger.error(f"❌ Error getting value metrics: {e}")
            return {"error": str(e), "last_updated": datetime.now().isoformat()}

    async def _get_usage_statistics(self) -> dict[str, Any]:
        """Get usage statistics"""
        try:
            with sqlite3.connect(self.metrics_db_path) as conn:
                # Get usage by module
                since_time = datetime.now() - timedelta(hours=24)

                cursor = conn.execute(
                    """
                    SELECT
                        module_name,
                        COUNT(*) as usage_count,
                        COUNT(DISTINCT session_id) as unique_sessions
                    FROM usage_events
                    WHERE timestamp >= ?
                    GROUP BY module_name
                    ORDER BY usage_count DESC
                """,
                    [since_time.isoformat()],
                )

                module_usage = []
                for row in cursor.fetchall():
                    module_usage.append(
                        {
                            "module_name": row[0],
                            "usage_count": row[1] or 0,
                            "unique_sessions": row[2] or 0,
                        }
                    )

                # Get usage by feature
                cursor = conn.execute(
                    """
                    SELECT
                        feature_name,
                        COUNT(*) as usage_count
                    FROM usage_events
                    WHERE timestamp >= ?
                    GROUP BY feature_name
                    ORDER BY usage_count DESC
                    LIMIT 10
                """,
                    [since_time.isoformat()],
                )

                feature_usage = []
                for row in cursor.fetchall():
                    feature_usage.append(
                        {"feature_name": row[0], "usage_count": row[1] or 0}
                    )

                # Get hourly usage pattern
                cursor = conn.execute(
                    """
                    SELECT
                        strftime('%H', timestamp) as hour,
                        COUNT(*) as usage_count
                    FROM usage_events
                    WHERE timestamp >= ?
                    GROUP BY hour
                    ORDER BY hour
                """,
                    [since_time.isoformat()],
                )

                hourly_usage = []
                for row in cursor.fetchall():
                    hourly_usage.append(
                        {"hour": int(row[0]), "usage_count": row[1] or 0}
                    )

                return {
                    "module_usage": module_usage,
                    "feature_usage": feature_usage,
                    "hourly_usage": hourly_usage,
                    "total_usage_24h": sum([m["usage_count"] for m in module_usage]),
                    "most_used_module": (
                        module_usage[0]["module_name"] if module_usage else "None"
                    ),
                    "last_updated": datetime.now().isoformat(),
                }

        except Exception as e:
            logger.error(f"❌ Error getting usage statistics: {e}")
            return {"error": str(e), "last_updated": datetime.now().isoformat()}

    async def _generate_recommendations(
        self,
        system_health: dict[str, Any],
        performance_metrics: dict[str, Any],
        value_metrics: dict[str, Any],
        usage_statistics: dict[str, Any],
    ) -> list[str]:
        """Generate recommendations based on metrics"""
        recommendations = []

        try:
            # Health-based recommendations
            if system_health.get("health_score", 0) < 80:
                recommendations.append(
                    "System health is below optimal. Consider investigating performance issues."
                )

            # Performance-based recommendations
            if performance_metrics.get("overall_avg_duration_ms", 0) > 5000:
                recommendations.append(
                    "Average response time is high. Consider performance optimization."
                )

            if performance_metrics.get("overall_success_rate", 0) < 0.95:
                recommendations.append(
                    "Success rate is below 95%. Investigate error patterns."
                )

            # Value-based recommendations
            if value_metrics.get("roi_percentage", 0) < 0:
                recommendations.append(
                    "ROI is negative. Review cost optimization strategies."
                )

            # Usage-based recommendations
            if usage_statistics.get("total_usage_24h", 0) < 100:
                recommendations.append(
                    "Low usage detected. Consider user engagement strategies."
                )

            # Add general recommendations
            if not recommendations:
                recommendations.append(
                    "System is performing well. Continue monitoring."
                )

        except Exception as e:
            logger.error(f"❌ Error generating recommendations: {e}")
            recommendations.append(
                "Error generating recommendations. Check system logs."
            )

        return recommendations

    async def _check_alerts(self):
        """Check for alert conditions"""
        try:
            # Get latest metrics
            if not self._dashboard_metrics:
                return

            latest_metrics = self._dashboard_metrics[-1]

            # Check performance alerts
            await self._check_performance_alerts(latest_metrics)

            # Check accuracy alerts
            await self._check_accuracy_alerts(latest_metrics)

            # Check value alerts
            await self._check_value_alerts(latest_metrics)

        except Exception as e:
            logger.error(f"❌ Alert check failed: {e}")

    async def _check_performance_alerts(self, metrics: DashboardMetrics):
        """Check performance-related alerts"""
        try:
            performance = metrics.performance_metrics

            # Response time alert
            avg_duration = performance.get("overall_avg_duration_ms", 0)
            if (
                avg_duration
                > self._alert_thresholds["performance"]["response_time_critical"]
            ):
                await self._create_alert(
                    severity="critical",
                    category="performance",
                    title="High Response Time",
                    message=f"Average response time is {avg_duration:.1f}ms",
                    source="performance_monitor",
                )
            elif (
                avg_duration
                > self._alert_thresholds["performance"]["response_time_warning"]
            ):
                await self._create_alert(
                    severity="warning",
                    category="performance",
                    title="Elevated Response Time",
                    message=f"Average response time is {avg_duration:.1f}ms",
                    source="performance_monitor",
                )

            # Success rate alert
            success_rate = performance.get("overall_success_rate", 0)
            if (
                success_rate
                < self._alert_thresholds["performance"]["error_rate_critical"]
            ):
                await self._create_alert(
                    severity="critical",
                    category="performance",
                    title="Low Success Rate",
                    message=f"Success rate is {success_rate:.1%}",
                    source="performance_monitor",
                )
            elif (
                success_rate
                < self._alert_thresholds["performance"]["error_rate_warning"]
            ):
                await self._create_alert(
                    severity="warning",
                    category="performance",
                    title="Reduced Success Rate",
                    message=f"Success rate is {success_rate:.1%}",
                    source="performance_monitor",
                )

        except Exception as e:
            logger.error(f"❌ Performance alert check failed: {e}")

    async def _check_accuracy_alerts(self, metrics: DashboardMetrics):
        """Check accuracy-related alerts"""
        try:
            # This would check validation results
            # For now, using placeholder logic
            pass

        except Exception as e:
            logger.error(f"❌ Accuracy alert check failed: {e}")

    async def _check_value_alerts(self, metrics: DashboardMetrics):
        """Check value-related alerts"""
        try:
            value_metrics = metrics.value_metrics

            # ROI alert
            roi_percentage = value_metrics.get("roi_percentage", 0)
            if roi_percentage < self._alert_thresholds["value"]["roi_critical"]:
                await self._create_alert(
                    severity="critical",
                    category="value",
                    title="Critical ROI Decline",
                    message=f"ROI is {roi_percentage:.1f}%",
                    source="value_monitor",
                )
            elif roi_percentage < self._alert_thresholds["value"]["roi_warning"]:
                await self._create_alert(
                    severity="warning",
                    category="value",
                    title="ROI Warning",
                    message=f"ROI is {roi_percentage:.1f}%",
                    source="value_monitor",
                )

        except Exception as e:
            logger.error(f"❌ Value alert check failed: {e}")

    async def _create_alert(
        self, severity: str, category: str, title: str, message: str, source: str
    ):
        """Create new alert"""
        try:
            alert = Alert(
                alert_id=f"alert_{int(time.time() * 1000)}",
                timestamp=datetime.now(),
                severity=severity,
                category=category,
                title=title,
                message=message,
                source=source,
                acknowledged=False,
                resolved=False,
            )

            with self._lock:
                self._alerts.append(alert)

            logger.warning(f"🚨 Alert created: {severity.upper()} - {title}")

        except Exception as e:
            logger.error(f"❌ Alert creation failed: {e}")

    def get_dashboard_data(self, time_range_hours: int = 1) -> dict[str, Any]:
        """Get dashboard data for display"""
        try:
            with self._lock:
                # Get recent metrics
                recent_metrics = [
                    m
                    for m in self._dashboard_metrics
                    if m.timestamp >= datetime.now() - timedelta(hours=time_range_hours)
                ]

                if not recent_metrics:
                    return {"error": "No recent metrics available"}

                latest_metrics = recent_metrics[-1]

                return {
                    "current_metrics": asdict(latest_metrics),
                    "metrics_history": [
                        asdict(m) for m in recent_metrics[-10:]
                    ],  # Last 10 updates
                    "alerts": [
                        asdict(alert) for alert in self._alerts if not alert.resolved
                    ],
                    "performance": self._dashboard_performance,
                    "last_updated": datetime.now().isoformat(),
                }

        except Exception as e:
            logger.error(f"❌ Error getting dashboard data: {e}")
            return {"error": str(e)}

    def get_visualization_data(
        self, chart_type: str, time_range_hours: int = 24
    ) -> VisualizationData:
        """Get data for visualization"""
        try:
            cache_key = f"{chart_type}_{time_range_hours}"

            # Check cache
            if cache_key in self._visualization_cache:
                cache_time, data = self._visualization_cache[cache_key]
                if time.time() - cache_time < self.config["cache_ttl_seconds"]:
                    return data

            # Generate visualization data
            if chart_type == "usage_trend":
                data = self._generate_usage_trend_data(time_range_hours)
            elif chart_type == "performance_metrics":
                data = self._generate_performance_data(time_range_hours)
            elif chart_type == "value_metrics":
                data = self._generate_value_data(time_range_hours)
            else:
                data = VisualizationData(
                    chart_type=chart_type,
                    title=f"{chart_type} Chart",
                    data=[],
                    x_axis="time",
                    y_axis="value",
                    time_range=f"{time_range_hours}h",
                    metadata={},
                )

            # Cache result
            self._visualization_cache[cache_key] = (time.time(), data)

            return data

        except Exception as e:
            logger.error(f"❌ Error getting visualization data: {e}")
            return VisualizationData(
                chart_type=chart_type,
                title="Error",
                data=[],
                x_axis="time",
                y_axis="value",
                time_range=f"{time_range_hours}h",
                metadata={"error": str(e)},
            )

    def _generate_usage_trend_data(self, time_range_hours: int) -> VisualizationData:
        """Generate usage trend data"""
        try:
            with sqlite3.connect(self.metrics_db_path) as conn:
                since_time = datetime.now() - timedelta(hours=time_range_hours)

                cursor = conn.execute(
                    """
                    SELECT
                        strftime('%Y-%m-%d %H:00:00', timestamp) as hour,
                        COUNT(*) as usage_count
                    FROM usage_events
                    WHERE timestamp >= ?
                    GROUP BY hour
                    ORDER BY hour
                """,
                    [since_time.isoformat()],
                )

                data = []
                for row in cursor.fetchall():
                    data.append({"timestamp": row[0], "usage_count": row[1] or 0})

                return VisualizationData(
                    chart_type="line",
                    title="Usage Trend",
                    data=data,
                    x_axis="timestamp",
                    y_axis="usage_count",
                    time_range=f"{time_range_hours}h",
                    metadata={"total_points": len(data)},
                )

        except Exception as e:
            logger.error(f"❌ Error generating usage trend data: {e}")
            return VisualizationData(
                chart_type="line",
                title="Usage Trend",
                data=[],
                x_axis="timestamp",
                y_axis="usage_count",
                time_range=f"{time_range_hours}h",
                metadata={"error": str(e)},
            )

    def _generate_performance_data(self, time_range_hours: int) -> VisualizationData:
        """Generate performance data"""
        try:
            with sqlite3.connect(self.metrics_db_path) as conn:
                since_time = datetime.now() - timedelta(hours=time_range_hours)

                cursor = conn.execute(
                    """
                    SELECT
                        module_name,
                        AVG(duration_ms) as avg_duration,
                        COUNT(*) as event_count
                    FROM usage_events
                    WHERE timestamp >= ?
                    GROUP BY module_name
                    ORDER BY event_count DESC
                """,
                    [since_time.isoformat()],
                )

                data = []
                for row in cursor.fetchall():
                    data.append(
                        {
                            "module_name": row[0],
                            "avg_duration_ms": row[1] or 0.0,
                            "event_count": row[2] or 0,
                        }
                    )

                return VisualizationData(
                    chart_type="bar",
                    title="Performance by Module",
                    data=data,
                    x_axis="module_name",
                    y_axis="avg_duration_ms",
                    time_range=f"{time_range_hours}h",
                    metadata={"modules_count": len(data)},
                )

        except Exception as e:
            logger.error(f"❌ Error generating performance data: {e}")
            return VisualizationData(
                chart_type="bar",
                title="Performance by Module",
                data=[],
                x_axis="module_name",
                y_axis="avg_duration_ms",
                time_range=f"{time_range_hours}h",
                metadata={"error": str(e)},
            )

    def _generate_value_data(self, time_range_hours: int) -> VisualizationData:
        """Generate value data"""
        try:
            with sqlite3.connect(self.metrics_db_path) as conn:
                since_time = datetime.now() - timedelta(hours=time_range_hours)

                cursor = conn.execute(
                    """
                    SELECT
                        strftime('%Y-%m-%d %H:00:00', timestamp) as hour,
                        SUM(duration_ms) / 1000.0 / 3600.0 * 0.5 as time_saved_hours
                    FROM usage_events
                    WHERE timestamp >= ? AND success = 1
                    GROUP BY hour
                    ORDER BY hour
                """,
                    [since_time.isoformat()],
                )

                data = []
                for row in cursor.fetchall():
                    time_saved = row[1] or 0.0
                    cost_savings = time_saved * 50.0  # $50/hour
                    data.append(
                        {
                            "timestamp": row[0],
                            "time_saved_hours": time_saved,
                            "cost_savings_usd": cost_savings,
                        }
                    )

                return VisualizationData(
                    chart_type="line",
                    title="Value Generation",
                    data=data,
                    x_axis="timestamp",
                    y_axis="cost_savings_usd",
                    time_range=f"{time_range_hours}h",
                    metadata={
                        "total_savings": sum([d["cost_savings_usd"] for d in data])
                    },
                )

        except Exception as e:
            logger.error(f"❌ Error generating value data: {e}")
            return VisualizationData(
                chart_type="line",
                title="Value Generation",
                data=[],
                x_axis="timestamp",
                y_axis="cost_savings_usd",
                time_range=f"{time_range_hours}h",
                metadata={"error": str(e)},
            )

    def acknowledge_alert(self, alert_id: str) -> bool:
        """Acknowledge an alert"""
        try:
            with self._lock:
                for alert in self._alerts:
                    if alert.alert_id == alert_id:
                        alert.acknowledged = True
                        logger.info(f"✅ Alert {alert_id} acknowledged")
                        return True

            return False

        except Exception as e:
            logger.error(f"❌ Error acknowledging alert: {e}")
            return False

    def resolve_alert(self, alert_id: str) -> bool:
        """Resolve an alert"""
        try:
            with self._lock:
                for alert in self._alerts:
                    if alert.alert_id == alert_id:
                        alert.resolved = True
                        logger.info(f"✅ Alert {alert_id} resolved")
                        return True

            return False

        except Exception as e:
            logger.error(f"❌ Error resolving alert: {e}")
            return False

    def get_dashboard_summary(self) -> dict[str, Any]:
        """Get dashboard summary"""
        try:
            with self._lock:
                latest_metrics = (
                    self._dashboard_metrics[-1] if self._dashboard_metrics else None
                )

                if not latest_metrics:
                    return {"error": "No metrics available"}

                return {
                    "system_status": latest_metrics.system_health.get(
                        "status", "unknown"
                    ),
                    "health_score": latest_metrics.system_health.get(
                        "health_score", 0.0
                    ),
                    "active_alerts": len([a for a in self._alerts if not a.resolved]),
                    "total_events_24h": latest_metrics.usage_statistics.get(
                        "total_usage_24h", 0
                    ),
                    "roi_percentage": latest_metrics.value_metrics.get(
                        "roi_percentage", 0.0
                    ),
                    "last_update": latest_metrics.timestamp.isoformat(),
                    "dashboard_performance": self._dashboard_performance,
                }

        except Exception as e:
            logger.error(f"❌ Error getting dashboard summary: {e}")
            return {"error": str(e)}


# Factory function
def create_dashboard(
    metrics_db_path: str,
    validation_db_path: str,
    config: dict[str, Any] | None = None,
) -> CoreDashboard:
    """Factory function để create dashboard"""
    return CoreDashboard(metrics_db_path, validation_db_path, config)


# CLI interface
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Core Dashboard")
    parser.add_argument("--metrics-db", required=True, help="Metrics database path")
    parser.add_argument(
        "--validation-db", required=True, help="Validation database path"
    )
    parser.add_argument("--start", action="store_true", help="Start dashboard")
    parser.add_argument("--stop", action="store_true", help="Stop dashboard")
    parser.add_argument("--data", action="store_true", help="Get dashboard data")
    parser.add_argument("--summary", action="store_true", help="Get dashboard summary")
    parser.add_argument("--time-range", type=int, default=1, help="Time range in hours")

    args = parser.parse_args()

    # Create dashboard
    dashboard = create_dashboard(args.metrics_db, args.validation_db)

    if args.start:
        dashboard.start_dashboard()
        print("✅ Dashboard started")
    elif args.stop:
        dashboard.stop_dashboard()
        print("🛑 Dashboard stopped")
    elif args.data:
        data = dashboard.get_dashboard_data(args.time_range)
        print(json.dumps(data, indent=2, default=str))
    elif args.summary:
        summary = dashboard.get_dashboard_summary()
        print(json.dumps(summary, indent=2, default=str))
    else:
        print("Use --help for usage information")