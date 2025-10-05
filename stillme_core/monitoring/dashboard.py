"""
📊 StillMe AGI Monitoring Dashboard
==================================

Real-time monitoring dashboard for AGI learning automation.
Provides comprehensive visualization of resource usage, performance
metrics, learning progress, and AGI evolution status.

Tính năng:
- Real-time resource monitoring dashboard
- AGI learning progress visualization
- Performance analytics và trends
- Alert management và notifications
- Evolution milestone tracking
- Interactive charts và metrics
- Export capabilities

Author: StillMe AI Framework
Version: 2.0.0
Date: 2025-09-28
"""

import asyncio
import json
import logging
import threading
from dataclasses import asdict
from datetime import datetime
from typing import TYPE_CHECKING, Any

# Import monitoring components
from .performance_analyzer import PerformanceAnalyzer, get_performance_analyzer
from .resource_monitor import ResourceMonitor, get_resource_monitor

# Initialize FASTAPI_AVAILABLE
FASTAPI_AVAILABLE = False

if TYPE_CHECKING:
    from fastapi import FastAPI, WebSocket, WebSocketDisconnect
    from fastapi.responses import HTMLResponse, JSONResponse
else:
    try:
        from fastapi import FastAPI, WebSocket, WebSocketDisconnect
        from fastapi.responses import HTMLResponse, JSONResponse

        FASTAPI_AVAILABLE = True
    except ImportError:
        FASTAPI_AVAILABLE = False

        # Create dummy classes for runtime when FastAPI is not available
        class FastAPI:
            def __init__(self, *args: Any, **kwargs: Any) -> None:
                pass

            def get(self, *args: Any, **kwargs: Any) -> Any:
                return lambda: None

            def websocket(self, *args: Any, **kwargs: Any) -> Any:
                return lambda: None

        class WebSocket:
            async def accept(self) -> None:
                pass

            async def receive_text(self) -> str:
                return ""

            async def send_text(self, text: str) -> None:
                pass

            async def close(self) -> None:
                pass

        class WebSocketDisconnect(Exception):
            pass

        class HTMLResponse:
            def __init__(self, content: str) -> None:
                pass

        class JSONResponse:
            def __init__(self, content: Any) -> None:
                pass

        logging.warning(
            "FastAPI not available. Install with: pip install fastapi uvicorn"
        )

logger = logging.getLogger(__name__)


class MonitoringDashboard:
    """
    Real-time monitoring dashboard for AGI learning automation
    """

    def __init__(self, port: int = 8080, host: str = "localhost"):
        self.port = port
        self.host = host
        self.logger = logging.getLogger(__name__)

        # Components
        self.resource_monitor: ResourceMonitor | None = None
        self.performance_analyzer: PerformanceAnalyzer | None = None

        # WebSocket connections
        self.active_connections: list[WebSocket] = []
        self.connection_lock = threading.Lock()

        # Dashboard state
        self.is_running = False
        self.app: FastAPI | None = None
        self.broadcast_task: asyncio.Task[None] | None = None

        # Dashboard data
        self.dashboard_data: dict[str, Any] = {
            "last_update": None,
            "resource_metrics": None,
            "performance_analysis": None,
            "alerts": [],
            "learning_sessions": [],
            "evolution_milestones": [],
            "system_status": "unknown",
        }

        if not FASTAPI_AVAILABLE:
            raise ImportError(
                "FastAPI is required for dashboard. Install with: pip install fastapi uvicorn"
            )

    async def initialize(self):
        """Initialize dashboard components"""
        try:
            # Get monitor instances
            self.resource_monitor = get_resource_monitor()
            self.performance_analyzer = get_performance_analyzer()

            # Create FastAPI app
            self.app = FastAPI(
                title="StillMe AGI Monitoring Dashboard",
                description="Real-time monitoring for AGI learning automation",
                version="2.0.0",
            )

            # Setup routes
            self._setup_routes()

            self.logger.info("Monitoring dashboard initialized")
            return True

        except Exception as e:
            self.logger.error(f"Failed to initialize dashboard: {e}")
            return False

    def _setup_routes(self):
        """Setup FastAPI routes"""

        if self.app is not None:

            @self.app.get("/")
            async def dashboard_home() -> HTMLResponse:
                """Dashboard home page"""
                return HTMLResponse(self._get_dashboard_html())

            @self.app.get("/api/status")
            async def get_status() -> JSONResponse:
                """Get system status"""
                return JSONResponse(self._get_system_status())

            @self.app.get("/api/metrics")
            async def get_metrics() -> JSONResponse:
                """Get current metrics"""
                return JSONResponse(self._get_current_metrics())

            @self.app.get("/api/analysis")
            async def get_analysis() -> JSONResponse:
                """Get performance analysis"""
                return JSONResponse(self._get_performance_analysis())

            @self.app.get("/api/alerts")
            async def get_alerts() -> JSONResponse:
                """Get active alerts"""
                return JSONResponse(self._get_active_alerts())

            @self.app.get("/api/learning-sessions")
            async def get_learning_sessions() -> JSONResponse:
                """Get learning sessions"""
                return JSONResponse(self._get_learning_sessions())

            @self.app.get("/api/evolution-milestones")
            async def get_evolution_milestones() -> JSONResponse:
                """Get evolution milestones"""
                return JSONResponse(self._get_evolution_milestones())

            @self.app.websocket("/ws")
            async def websocket_endpoint(websocket: WebSocket) -> None:
                """WebSocket endpoint for real-time updates"""
                await websocket.accept()

                with self.connection_lock:
                    self.active_connections.append(websocket)

                try:
                    while True:
                        # Keep connection alive
                        await websocket.receive_text()
                except WebSocketDisconnect:
                    with self.connection_lock:
                        if websocket in self.active_connections:
                            self.active_connections.remove(websocket)

    async def start(self):
        """Start dashboard server"""
        if not await self.initialize():
            return False

        try:
            import uvicorn

            # Start broadcast task
            self.broadcast_task = asyncio.create_task(self._broadcast_updates())

            # Start server
            if self.app is not None:
                config = uvicorn.Config(
                    self.app, host=self.host, port=self.port, log_level="info"
                )
            else:
                raise RuntimeError("FastAPI app not initialized")
            server = uvicorn.Server(config)

            self.is_running = True
            self.logger.info(f"Dashboard started at http://{self.host}:{self.port}")

            await server.serve()

        except Exception as e:
            self.logger.error(f"Failed to start dashboard: {e}")
            return False

    async def stop(self):
        """Stop dashboard server"""
        self.is_running = False

        if self.broadcast_task:
            self.broadcast_task.cancel()
            try:
                await self.broadcast_task
            except asyncio.CancelledError:
                pass

        # Close all WebSocket connections
        with self.connection_lock:
            for connection in self.active_connections:
                try:
                    await connection.close()
                except Exception:
                    pass
            self.active_connections.clear()

        self.logger.info("Dashboard stopped")

    async def _broadcast_updates(self):
        """Broadcast updates to connected clients"""
        while self.is_running:
            try:
                # Update dashboard data
                await self._update_dashboard_data()

                # Broadcast to all connected clients
                if self.active_connections:
                    message = json.dumps(self.dashboard_data, default=str)

                    with self.connection_lock:
                        disconnected: list[WebSocket] = []
                        for connection in self.active_connections:
                            try:
                                await connection.send_text(message)
                            except Exception:
                                disconnected.append(connection)

                        # Remove disconnected connections
                        for conn in disconnected:
                            if conn in self.active_connections:
                                self.active_connections.remove(conn)

                await asyncio.sleep(5)  # Update every 5 seconds

            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error in broadcast loop: {e}")
                await asyncio.sleep(5)

    async def _update_dashboard_data(self):
        """Update dashboard data"""
        try:
            # Resource metrics
            if self.resource_monitor:
                metrics = self.resource_monitor.get_current_metrics()
                if metrics:
                    self.dashboard_data["resource_metrics"] = asdict(metrics)

            # Performance analysis
            if self.performance_analyzer:
                analysis = self.performance_analyzer.get_analysis_report()
                self.dashboard_data["performance_analysis"] = analysis

            # Alerts
            if self.resource_monitor:
                alerts = [a for a in self.resource_monitor.alerts if not a.resolved]
                self.dashboard_data["alerts"] = [
                    asdict(a) for a in alerts[-10:]
                ]  # Last 10

            # Learning sessions
            if self.resource_monitor:
                # Type cast to help type checker understand the types
                learning_processes: set[str] = self.resource_monitor.learning_processes
                process_start_times: dict[str, datetime] = (
                    self.resource_monitor.process_start_times
                )

                sessions: list[str] = list(learning_processes)
                self.dashboard_data["learning_sessions"] = [
                    {
                        "session_id": session_id,
                        "start_time": process_start_times.get(session_id),
                        "duration": str(
                            datetime.now()
                            - process_start_times.get(session_id, datetime.now())
                        ),
                    }
                    for session_id in sessions
                ]

            # Evolution milestones
            if self.performance_analyzer:
                # Type cast to help type checker understand the types
                evolution_milestones: list[Any] = (
                    self.performance_analyzer.evolution_milestones
                )
                milestones: list[Any] = evolution_milestones[-5:]  # Last 5
                self.dashboard_data["evolution_milestones"] = milestones

            # System status
            self.dashboard_data["system_status"] = self._determine_system_status()
            self.dashboard_data["last_update"] = datetime.now().isoformat()

        except Exception as e:
            self.logger.error(f"Error updating dashboard data: {e}")

    def _determine_system_status(self) -> str:
        """Determine overall system status"""
        if not self.resource_monitor or not self.performance_analyzer:
            return "initializing"

        # Check for critical alerts
        critical_alerts = [
            a
            for a in self.resource_monitor.alerts
            if not a.resolved and a.severity == "critical"
        ]

        if critical_alerts:
            return "critical"

        # Check for high severity alerts
        high_alerts = [
            a
            for a in self.resource_monitor.alerts
            if not a.resolved and a.severity == "high"
        ]

        if high_alerts:
            return "warning"

        # Check resource usage
        metrics = self.resource_monitor.get_current_metrics()
        if metrics:
            if (
                metrics.cpu_percent > 80
                or metrics.memory_percent > 80
                or metrics.disk_percent > 90
            ):
                return "warning"

        return "healthy"

    def _get_system_status(self) -> dict[str, Any]:
        """Get system status"""
        return {
            "status": self.dashboard_data["system_status"],
            "last_update": self.dashboard_data["last_update"],
            "components": {
                "resource_monitor": self.resource_monitor is not None,
                "performance_analyzer": self.performance_analyzer is not None,
                "dashboard": self.is_running,
            },
        }

    def _get_current_metrics(self) -> dict[str, Any]:
        """Get current metrics"""
        if self.resource_monitor:
            return self.resource_monitor.get_metrics_summary()
        return {"error": "Resource monitor not available"}

    def _get_performance_analysis(self) -> dict[str, Any]:
        """Get performance analysis"""
        if self.performance_analyzer:
            return self.performance_analyzer.get_analysis_report()
        return {"error": "Performance analyzer not available"}

    def _get_active_alerts(self) -> list[dict[str, Any]]:
        """Get active alerts"""
        if self.resource_monitor:
            alerts = [a for a in self.resource_monitor.alerts if not a.resolved]
            return [asdict(a) for a in alerts]
        return []

    def _get_learning_sessions(self) -> list[dict[str, Any]]:
        """Get learning sessions"""
        if self.resource_monitor:
            # Type cast to help type checker understand the types
            learning_processes: set[str] = self.resource_monitor.learning_processes
            process_start_times: dict[str, datetime] = (
                self.resource_monitor.process_start_times
            )

            sessions: list[str] = list(learning_processes)
            return [
                {
                    "session_id": session_id,
                    "start_time": process_start_times.get(session_id),
                    "duration": str(
                        datetime.now()
                        - process_start_times.get(session_id, datetime.now())
                    ),
                }
                for session_id in sessions
            ]
        return []

    def _get_evolution_milestones(self) -> list[dict[str, Any]]:
        """Get evolution milestones"""
        if self.performance_analyzer:
            # Type cast to help type checker understand the types
            evolution_milestones: list[Any] = (
                self.performance_analyzer.evolution_milestones
            )
            return evolution_milestones[-10:]  # Last 10
        return []

    def _get_dashboard_html(self) -> str:
        """Get dashboard HTML"""
        return """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>StillMe AGI Monitoring Dashboard</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
        }
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            border-radius: 10px;
            margin-bottom: 20px;
            text-align: center;
        }
        .status-indicator {
            display: inline-block;
            width: 12px;
            height: 12px;
            border-radius: 50%;
            margin-right: 8px;
        }
        .status-healthy { background-color: #4CAF50; }
        .status-warning { background-color: #FF9800; }
        .status-critical { background-color: #F44336; }
        .status-unknown { background-color: #9E9E9E; }
        .grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin-bottom: 20px;
        }
        .card {
            background: white;
            border-radius: 10px;
            padding: 20px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        .card h3 {
            margin-top: 0;
            color: #333;
            border-bottom: 2px solid #667eea;
            padding-bottom: 10px;
        }
        .metric {
            display: flex;
            justify-content: space-between;
            margin: 10px 0;
            padding: 5px 0;
            border-bottom: 1px solid #eee;
        }
        .metric:last-child {
            border-bottom: none;
        }
        .metric-value {
            font-weight: bold;
            color: #667eea;
        }
        .alert {
            padding: 10px;
            margin: 5px 0;
            border-radius: 5px;
            border-left: 4px solid;
        }
        .alert-critical { background-color: #ffebee; border-color: #f44336; }
        .alert-high { background-color: #fff3e0; border-color: #ff9800; }
        .alert-medium { background-color: #fff8e1; border-color: #ffc107; }
        .alert-low { background-color: #e8f5e8; border-color: #4caf50; }
        .chart-container {
            position: relative;
            height: 300px;
            margin: 20px 0;
        }
        .connection-status {
            position: fixed;
            top: 10px;
            right: 10px;
            padding: 10px;
            border-radius: 5px;
            color: white;
            font-weight: bold;
        }
        .connected { background-color: #4CAF50; }
        .disconnected { background-color: #F44336; }
    </style>
</head>
<body>
    <div class="connection-status" id="connectionStatus">Connecting...</div>

    <div class="header">
        <h1>🧠 StillMe AGI Monitoring Dashboard</h1>
        <p>Real-time monitoring for AGI learning automation</p>
        <div>
            <span class="status-indicator" id="systemStatus"></span>
            <span id="systemStatusText">System Status: Unknown</span>
        </div>
    </div>

    <div class="grid">
        <div class="card">
            <h3>📊 Resource Metrics</h3>
            <div id="resourceMetrics">
                <div class="metric">
                    <span>CPU Usage:</span>
                    <span class="metric-value" id="cpuUsage">-</span>
                </div>
                <div class="metric">
                    <span>Memory Usage:</span>
                    <span class="metric-value" id="memoryUsage">-</span>
                </div>
                <div class="metric">
                    <span>Disk Usage:</span>
                    <span class="metric-value" id="diskUsage">-</span>
                </div>
                <div class="metric">
                    <span>Network Speed:</span>
                    <span class="metric-value" id="networkSpeed">-</span>
                </div>
            </div>
        </div>

        <div class="card">
            <h3>🎯 Learning Sessions</h3>
            <div id="learningSessions">
                <div class="metric">
                    <span>Active Sessions:</span>
                    <span class="metric-value" id="activeSessions">-</span>
                </div>
                <div class="metric">
                    <span>Total Sessions:</span>
                    <span class="metric-value" id="totalSessions">-</span>
                </div>
            </div>
        </div>

        <div class="card">
            <h3>🚨 Active Alerts</h3>
            <div id="alertsList">
                <p>No active alerts</p>
            </div>
        </div>

        <div class="card">
            <h3>🌟 Evolution Milestones</h3>
            <div id="milestonesList">
                <p>No recent milestones</p>
            </div>
        </div>
    </div>

    <div class="card">
        <h3>📈 Performance Trends</h3>
        <div class="chart-container">
            <canvas id="performanceChart"></canvas>
        </div>
    </div>

    <script>
        let ws;
        let performanceChart;
        let performanceData = {
            labels: [],
            datasets: [{
                label: 'CPU Usage (%)',
                data: [],
                borderColor: 'rgb(75, 192, 192)',
                tension: 0.1
            }, {
                label: 'Memory Usage (%)',
                data: [],
                borderColor: 'rgb(255, 99, 132)',
                tension: 0.1
            }]
        };

        function connectWebSocket() {
            const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
            const wsUrl = `${protocol}//${window.location.host}/ws`;

            ws = new WebSocket(wsUrl);

            ws.onopen = function() {
                document.getElementById('connectionStatus').textContent = 'Connected';
                document.getElementById('connectionStatus').className = 'connection-status connected';
            };

            ws.onmessage = function(event) {
                const data = JSON.parse(event.data);
                updateDashboard(data);
            };

            ws.onclose = function() {
                document.getElementById('connectionStatus').textContent = 'Disconnected';
                document.getElementById('connectionStatus').className = 'connection-status disconnected';
                setTimeout(connectWebSocket, 5000);
            };

            ws.onerror = function(error) {
                console.error('WebSocket error:', error);
            };
        }

        function updateDashboard(data) {
            // Update system status
            const statusElement = document.getElementById('systemStatus');
            const statusTextElement = document.getElementById('systemStatusText');
            statusElement.className = `status-indicator status-${data.system_status}`;
            statusTextElement.textContent = `System Status: ${data.system_status.toUpperCase()}`;

            // Update resource metrics
            if (data.resource_metrics) {
                document.getElementById('cpuUsage').textContent = `${data.resource_metrics.cpu_percent.toFixed(1)}%`;
                document.getElementById('memoryUsage').textContent = `${data.resource_metrics.memory_percent.toFixed(1)}%`;
                document.getElementById('diskUsage').textContent = `${data.resource_metrics.disk_percent.toFixed(1)}%`;
                document.getElementById('networkSpeed').textContent = `${data.resource_metrics.network_speed_mbps.toFixed(2)} Mbps`;

                // Update performance chart
                updatePerformanceChart(data.resource_metrics);
            }

            // Update learning sessions
            if (data.learning_sessions) {
                document.getElementById('activeSessions').textContent = data.learning_sessions.length;
                document.getElementById('totalSessions').textContent = data.learning_sessions.length;
            }

            // Update alerts
            updateAlerts(data.alerts || []);

            // Update milestones
            updateMilestones(data.evolution_milestones || []);
        }

        function updatePerformanceChart(metrics) {
            const now = new Date().toLocaleTimeString();

            performanceData.labels.push(now);
            performanceData.datasets[0].data.push(metrics.cpu_percent);
            performanceData.datasets[1].data.push(metrics.memory_percent);

            // Keep only last 20 data points
            if (performanceData.labels.length > 20) {
                performanceData.labels.shift();
                performanceData.datasets[0].data.shift();
                performanceData.datasets[1].data.shift();
            }

            performanceChart.update();
        }

        function updateAlerts(alerts) {
            const alertsContainer = document.getElementById('alertsList');

            if (alerts.length === 0) {
                alertsContainer.innerHTML = '<p>No active alerts</p>';
                return;
            }

            alertsContainer.innerHTML = alerts.map(alert => `
                <div class="alert alert-${alert.severity}">
                    <strong>${alert.alert_type.toUpperCase()}</strong><br>
                    ${alert.message}<br>
                    <small>${new Date(alert.timestamp).toLocaleString()}</small>
                </div>
            `).join('');
        }

        function updateMilestones(milestones) {
            const milestonesContainer = document.getElementById('milestonesList');

            if (milestones.length === 0) {
                milestonesContainer.innerHTML = '<p>No recent milestones</p>';
                return;
            }

            milestonesContainer.innerHTML = milestones.map(milestone => `
                <div class="metric">
                    <span>${milestone.stage}:</span>
                    <span class="metric-value">${milestone.achievement}</span>
                </div>
            `).join('');
        }

        // Initialize chart
        const ctx = document.getElementById('performanceChart').getContext('2d');
        performanceChart = new Chart(ctx, {
            type: 'line',
            data: performanceData,
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        beginAtZero: true,
                        max: 100
                    }
                }
            }
        });

        // Connect WebSocket
        connectWebSocket();
    </script>
</body>
</html>
        """


# Global dashboard instance
_dashboard_instance: MonitoringDashboard | None = None


def get_monitoring_dashboard(
    port: int = 8080, host: str = "localhost"
) -> MonitoringDashboard:
    """Get global monitoring dashboard instance"""
    global _dashboard_instance
    if _dashboard_instance is None:
        _dashboard_instance = MonitoringDashboard(port, host)
    return _dashboard_instance


async def start_monitoring_dashboard(
    port: int = 8080, host: str = "localhost"
) -> MonitoringDashboard:
    """Start monitoring dashboard"""
    dashboard = get_monitoring_dashboard(port, host)
    await dashboard.start()
    return dashboard
