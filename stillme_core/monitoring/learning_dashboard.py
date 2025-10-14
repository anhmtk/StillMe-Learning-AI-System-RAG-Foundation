"""
Learning Dashboard - Real-time monitoring and visualization
Provides comprehensive monitoring of self-learning processes, metrics, and system health.
"""

import json
import logging
import statistics
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class DashboardMetrics:
    """Dashboard metrics data structure"""

    timestamp: str
    session_id: str
    success_rate: float
    reward_curve: list[float]
    rollback_count: int
    ethics_violations: int
    performance_metrics: dict[str, float]
    learning_progress: dict[str, Any]
    system_health: dict[str, Any]


@dataclass
class LearningSession:
    """Learning session data"""

    session_id: str
    start_time: str
    end_time: str | None
    status: str
    success_rate: float
    reward_score: float
    penalty_score: float
    rollback_count: int
    ethics_violations: int
    performance_delta: float


class LearningDashboard:
    """
    Real-time learning dashboard for monitoring self-learning processes
    """

    def __init__(self, artifacts_dir: str = "artifacts", logs_dir: str = "logs"):
        self.artifacts_dir = Path(artifacts_dir)
        self.logs_dir = Path(logs_dir)
        self.artifacts_dir.mkdir(exist_ok=True)
        self.logs_dir.mkdir(exist_ok=True)

        # Dashboard state
        self.sessions: list[LearningSession] = []
        self.metrics_history: list[DashboardMetrics] = []
        self.alerts: list[dict[str, Any]] = []

        logger.info("Learning Dashboard initialized")

    async def update_dashboard(
        self,
        session_id: str,
        success_rate: float,
        reward_curve: list[float],
        rollback_count: int,
        ethics_violations: int,
        performance_metrics: dict[str, float],
        learning_progress: dict[str, Any],
    ) -> DashboardMetrics:
        """
        Update dashboard with new metrics

        Args:
            session_id: Current session ID
            success_rate: Success rate for the session
            reward_curve: Reward curve data points
            rollback_count: Number of rollbacks
            ethics_violations: Number of ethics violations
            performance_metrics: Performance metrics
            learning_progress: Learning progress data

        Returns:
            Updated dashboard metrics
        """
        # Calculate system health
        system_health = await self._calculate_system_health(
            success_rate, rollback_count, ethics_violations, performance_metrics
        )

        # Create metrics object
        metrics = DashboardMetrics(
            timestamp=datetime.now().isoformat(),
            session_id=session_id,
            success_rate=success_rate,
            reward_curve=reward_curve,
            rollback_count=rollback_count,
            ethics_violations=ethics_violations,
            performance_metrics=performance_metrics,
            learning_progress=learning_progress,
            system_health=system_health,
        )

        # Store metrics
        self.metrics_history.append(metrics)

        # Check for alerts
        await self._check_alerts(metrics)

        # Update session data
        await self._update_session_data(session_id, metrics)

        logger.info(
            f"Dashboard updated for session {session_id}: success_rate={success_rate:.2f}"
        )

        return metrics

    async def _calculate_system_health(
        self,
        success_rate: float,
        rollback_count: int,
        ethics_violations: int,
        performance_metrics: dict[str, float],
    ) -> dict[str, Any]:
        """Calculate overall system health"""
        health_score = 100.0

        # Success rate impact
        if success_rate < 0.7:
            health_score -= 20
        elif success_rate < 0.8:
            health_score -= 10

        # Rollback impact
        if rollback_count > 5:
            health_score -= 15
        elif rollback_count > 2:
            health_score -= 5

        # Ethics violations impact
        if ethics_violations > 0:
            health_score -= ethics_violations * 10

        # Performance impact
        if performance_metrics.get("latency", 0) > 1000:  # ms
            health_score -= 10
        if performance_metrics.get("error_rate", 0) > 0.05:  # 5%
            health_score -= 15

        # Determine health status
        if health_score >= 90:
            status = "excellent"
        elif health_score >= 75:
            status = "good"
        elif health_score >= 60:
            status = "warning"
        else:
            status = "critical"

        return {
            "overall_score": max(0.0, min(100.0, health_score)),
            "status": status,
            "success_rate": success_rate,
            "rollback_count": rollback_count,
            "ethics_violations": ethics_violations,
            "performance_impact": performance_metrics.get("latency", 0) > 1000
            or performance_metrics.get("error_rate", 0) > 0.05,
        }

    async def _check_alerts(self, metrics: DashboardMetrics):
        """Check for alert conditions"""
        alerts = []

        # Success rate alerts
        if metrics.success_rate < 0.5:
            alerts.append(
                {
                    "type": "critical",
                    "message": f"Low success rate: {metrics.success_rate:.2f}",
                    "timestamp": metrics.timestamp,
                    "session_id": metrics.session_id,
                }
            )

        # Rollback alerts
        if metrics.rollback_count > 3:
            alerts.append(
                {
                    "type": "warning",
                    "message": f"High rollback count: {metrics.rollback_count}",
                    "timestamp": metrics.timestamp,
                    "session_id": metrics.session_id,
                }
            )

        # Ethics violation alerts
        if metrics.ethics_violations > 0:
            alerts.append(
                {
                    "type": "critical",
                    "message": f"Ethics violations detected: {metrics.ethics_violations}",
                    "timestamp": metrics.timestamp,
                    "session_id": metrics.session_id,
                }
            )

        # Performance alerts
        if metrics.performance_metrics.get("latency", 0) > 2000:  # 2 seconds
            alerts.append(
                {
                    "type": "warning",
                    "message": f"High latency: {metrics.performance_metrics['latency']}ms",
                    "timestamp": metrics.timestamp,
                    "session_id": metrics.session_id,
                }
            )

        # Add alerts to history
        self.alerts.extend(alerts)

        # Log critical alerts
        for alert in alerts:
            if alert["type"] == "critical":
                logger.critical(f"CRITICAL ALERT: {alert['message']}")

    async def _update_session_data(self, session_id: str, metrics: DashboardMetrics):
        """Update session data"""
        # Find existing session or create new one
        session = None
        for s in self.sessions:
            if s.session_id == session_id:
                session = s
                break

        if not session:
            session = LearningSession(
                session_id=session_id,
                start_time=metrics.timestamp,
                end_time=None,
                status="active",
                success_rate=metrics.success_rate,
                reward_score=sum(metrics.reward_curve) if metrics.reward_curve else 0.0,
                penalty_score=0.0,
                rollback_count=metrics.rollback_count,
                ethics_violations=metrics.ethics_violations,
                performance_delta=metrics.performance_metrics.get("improvement", 0.0),
            )
            self.sessions.append(session)
        else:
            # Update existing session
            session.success_rate = metrics.success_rate
            session.reward_score = (
                sum(metrics.reward_curve) if metrics.reward_curve else 0.0
            )
            session.rollback_count = metrics.rollback_count
            session.ethics_violations = metrics.ethics_violations
            session.performance_delta = metrics.performance_metrics.get(
                "improvement", 0.0
            )

    async def generate_dashboard_html(
        self, output_path: str = "artifacts/learning_dashboard.html"
    ) -> str:
        """Generate HTML dashboard"""
        try:
            # Calculate dashboard statistics
            stats = await self._calculate_dashboard_statistics()

            # Generate HTML content
            html_content = self._generate_html_content(stats)

            # Write to file
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(html_content)

            logger.info(f"Dashboard HTML generated: {output_path}")
            return output_path

        except Exception as e:
            logger.error(f"Failed to generate dashboard HTML: {e}")
            raise

    async def _calculate_dashboard_statistics(self) -> dict[str, Any]:
        """Calculate comprehensive dashboard statistics"""
        if not self.metrics_history:
            return {
                "total_sessions": 0,
                "avg_success_rate": 0.0,
                "total_rollbacks": 0,
                "total_ethics_violations": 0,
                "system_health": "unknown",
                "recent_trends": {},
                "alerts_summary": {},
            }

        # Basic statistics
        total_sessions = len(self.sessions)
        avg_success_rate = statistics.mean(
            [m.success_rate for m in self.metrics_history]
        )
        total_rollbacks = sum(m.rollback_count for m in self.metrics_history)
        total_ethics_violations = sum(m.ethics_violations for m in self.metrics_history)

        # System health
        recent_health_scores = [
            m.system_health["overall_score"] for m in self.metrics_history[-10:]
        ]
        avg_health_score = (
            statistics.mean(recent_health_scores) if recent_health_scores else 0.0
        )

        if avg_health_score >= 90:
            system_health = "excellent"
        elif avg_health_score >= 75:
            system_health = "good"
        elif avg_health_score >= 60:
            system_health = "warning"
        else:
            system_health = "critical"

        # Recent trends
        recent_trends = {
            "success_rate_trend": self._calculate_trend(
                [m.success_rate for m in self.metrics_history[-10:]]
            ),
            "rollback_trend": self._calculate_trend(
                [m.rollback_count for m in self.metrics_history[-10:]]
            ),
            "ethics_trend": self._calculate_trend(
                [m.ethics_violations for m in self.metrics_history[-10:]]
            ),
        }

        # Alerts summary
        alert_counts = {}
        for alert in self.alerts:
            alert_type = alert["type"]
            alert_counts[alert_type] = alert_counts.get(alert_type, 0) + 1

        return {
            "total_sessions": total_sessions,
            "avg_success_rate": avg_success_rate,
            "total_rollbacks": total_rollbacks,
            "total_ethics_violations": total_ethics_violations,
            "system_health": system_health,
            "avg_health_score": avg_health_score,
            "recent_trends": recent_trends,
            "alerts_summary": alert_counts,
            "last_updated": datetime.now().isoformat(),
        }

    def _calculate_trend(self, values: list[float]) -> str:
        """Calculate trend direction"""
        if len(values) < 2:
            return "stable"

        # Simple trend calculation
        first_half = statistics.mean(values[: len(values) // 2])
        second_half = statistics.mean(values[len(values) // 2 :])

        if second_half > first_half * 1.1:
            return "improving"
        elif second_half < first_half * 0.9:
            return "declining"
        else:
            return "stable"

    def _generate_html_content(self, stats: dict[str, Any]) -> str:
        """Generate HTML dashboard content"""
        return f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>StillMe Learning Dashboard</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        .dashboard {{
            max-width: 1200px;
            margin: 0 auto;
        }}
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            border-radius: 10px;
            margin-bottom: 20px;
            text-align: center;
        }}
        .metrics-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 20px;
        }}
        .metric-card {{
            background: white;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            text-align: center;
        }}
        .metric-value {{
            font-size: 2em;
            font-weight: bold;
            margin: 10px 0;
        }}
        .metric-label {{
            color: #666;
            font-size: 0.9em;
        }}
        .health-{stats['system_health']} {{
            color: {'#28a745' if stats['system_health'] == 'excellent' else '#ffc107' if stats['system_health'] == 'good' else '#fd7e14' if stats['system_health'] == 'warning' else '#dc3545'};
        }}
        .alerts {{
            background: white;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            margin-bottom: 20px;
        }}
        .alert-item {{
            padding: 10px;
            margin: 5px 0;
            border-radius: 5px;
            border-left: 4px solid;
        }}
        .alert-critical {{
            background-color: #f8d7da;
            border-left-color: #dc3545;
        }}
        .alert-warning {{
            background-color: #fff3cd;
            border-left-color: #ffc107;
        }}
        .footer {{
            text-align: center;
            color: #666;
            margin-top: 20px;
        }}
    </style>
</head>
<body>
    <div class="dashboard">
        <div class="header">
            <h1>🧠 StillMe Learning Dashboard</h1>
            <p>Real-time monitoring of self-learning processes</p>
            <p>Last updated: {stats['last_updated']}</p>
        </div>

        <div class="metrics-grid">
            <div class="metric-card">
                <div class="metric-value">{stats['total_sessions']}</div>
                <div class="metric-label">Total Sessions</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">{stats['avg_success_rate']:.1%}</div>
                <div class="metric-label">Avg Success Rate</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">{stats['total_rollbacks']}</div>
                <div class="metric-label">Total Rollbacks</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">{stats['total_ethics_violations']}</div>
                <div class="metric-label">Ethics Violations</div>
            </div>
            <div class="metric-card">
                <div class="metric-value health-{stats['system_health']}">{stats['system_health'].title()}</div>
                <div class="metric-label">System Health</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">{stats['avg_health_score']:.1f}</div>
                <div class="metric-label">Health Score</div>
            </div>
        </div>

        <div class="alerts">
            <h3>Recent Alerts</h3>
            {self._generate_alerts_html()}
        </div>

        <div class="footer">
            <p>StillMe AI Framework - Learning Dashboard v2.0</p>
            <p>Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        </div>
    </div>
</body>
</html>
        """

    def _generate_alerts_html(self) -> str:
        """Generate HTML for alerts section"""
        if not self.alerts:
            return "<p>No recent alerts</p>"

        # Get recent alerts (last 10)
        recent_alerts = self.alerts[-10:]

        alerts_html = ""
        for alert in recent_alerts:
            alert_class = f"alert-{alert['type']}"
            alerts_html += f"""
            <div class="alert-item {alert_class}">
                <strong>{alert['type'].title()}:</strong> {alert['message']}
                <br><small>Session: {alert['session_id']} | {alert['timestamp']}</small>
            </div>
            """

        return alerts_html

    def get_dashboard_data(self) -> dict[str, Any]:
        """Get current dashboard data"""
        return {
            "sessions": [asdict(session) for session in self.sessions],
            "metrics_history": [
                asdict(metrics) for metrics in self.metrics_history[-50:]
            ],  # Last 50 metrics
            "alerts": self.alerts[-20:],  # Last 20 alerts
            "statistics": asdict(
                DashboardMetrics(
                    timestamp=datetime.now().isoformat(),
                    session_id="dashboard",
                    success_rate=statistics.mean(
                        [m.success_rate for m in self.metrics_history]
                    )
                    if self.metrics_history
                    else 0.0,
                    reward_curve=[],
                    rollback_count=sum(m.rollback_count for m in self.metrics_history),
                    ethics_violations=sum(
                        m.ethics_violations for m in self.metrics_history
                    ),
                    performance_metrics={},
                    learning_progress={},
                    system_health={},
                )
            ),
        }

    async def export_metrics_json(
        self, output_path: str = "artifacts/learning_dashboard.json"
    ) -> str:
        """Export dashboard metrics to JSON"""
        try:
            dashboard_data = self.get_dashboard_data()

            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(dashboard_data, f, indent=2, ensure_ascii=False)

            logger.info(f"Dashboard metrics exported: {output_path}")
            return output_path

        except Exception as e:
            logger.error(f"Failed to export dashboard metrics: {e}")
            raise

    def clear_old_data(self, days_to_keep: int = 30):
        """Clear old dashboard data"""
        cutoff_date = datetime.now() - timedelta(days=days_to_keep)

        # Clear old metrics
        self.metrics_history = [
            m
            for m in self.metrics_history
            if datetime.fromisoformat(m.timestamp) > cutoff_date
        ]

        # Clear old alerts
        self.alerts = [
            a
            for a in self.alerts
            if datetime.fromisoformat(a["timestamp"]) > cutoff_date
        ]

        # Clear old sessions
        self.sessions = [
            s
            for s in self.sessions
            if datetime.fromisoformat(s.start_time) > cutoff_date
        ]

        logger.info(f"Cleared dashboard data older than {days_to_keep} days")