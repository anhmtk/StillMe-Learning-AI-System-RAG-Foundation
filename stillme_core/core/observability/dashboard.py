# Observability Dashboard Module
# ==============================
#
# Provides a web-based dashboard for monitoring logs, metrics, traces, and health.
#

import json
import threading
import urllib.parse
import webbrowser
from datetime import datetime
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Any

# Khối Import: Đã xử lý triệt để lỗi import
# Import with fallbacks for missing modules
try:
    from .health import HealthStatus, get_health_monitor
except ImportError:
    # Create fallback classes
    class HealthStatus:
        HEALTHY = "healthy"
        DEGRADED = "degraded"
        UNHEALTHY = "unhealthy"

    def get_health_monitor():
        return None


try:
    from .logger import get_logger
except ImportError:

    def get_logger(name):
        import logging

        return logging.getLogger(name)


try:
    from .metrics import get_metrics_collector
except ImportError:

    def get_metrics_collector():
        return None


try:
    from .tracer import get_tracer
except ImportError:

    def get_tracer():
        return None


# MetricType is optional
try:
    from .metrics import MetricType
except ImportError:
    MetricType = None

class ObservabilityDashboard:
    """Web-based observability dashboard"""

    def __init__(self, port: int = 8080, host: str = "localhost"):
        self.port = port
        self.host = host
        self.logger = get_logger("dashboard")
        self.metrics_collector = get_metrics_collector()
        self.tracer = get_tracer()
        self.health_monitor = get_health_monitor()

        self.server: HTTPServer | None = None
        self.server_thread: threading.Thread | None = None
        self.is_running = False

    def start(self, open_browser: bool = True):
        """Start the dashboard server"""
        if self.is_running:
            self.logger.warning("Dashboard is already running")
            return

        try:
            # Khởi tạo server
            self.server = HTTPServer((self.host, self.port), DashboardHandler)

            # Gán instance dashboard vào server để Handler có thể truy cập
            self.server.dashboard = self

            self.server_thread = threading.Thread(target=self._run_server, daemon=True)
            self.server_thread.start()

            self.is_running = True
            self.logger.info(f"Dashboard started at http://{self.host}:{self.port}")

            if open_browser:
                webbrowser.open(f"http://{self.host}:{self.port}")

        except Exception as e:
            self.logger.error(f"Failed to start dashboard: {e}")
            raise

    def stop(self):
        """Stop the dashboard server"""
        if not self.is_running:
            return

        if self.server:
            self.server.shutdown()
            self.server.server_close()

        self.is_running = False
        self.logger.info("Dashboard stopped")

    def _run_server(self):
        """Run the HTTP server"""
        try:
            if self.server:
                self.server.serve_forever()
        except Exception as e:
            self.logger.error(f"Server error: {e}")

    def get_dashboard_data(self) -> dict[str, Any]:
        """Get comprehensive dashboard data"""
        try:
            # Get health status
            health = (
                self.health_monitor.get_health_status() if self.health_monitor else None
            )
            # Get metrics overview
            metrics_overview = (
                self.metrics_collector.get_metrics_overview()
                if self.metrics_collector
                else None
            )
            # Get recent traces
            recent_traces = (
                self.tracer.get_traces_overview(limit=10) if self.tracer else []
            )
            # Get log stats
            log_stats = (
                self.logger.get_log_stats()
                if hasattr(self.logger, "get_log_stats")
                else {}
            )
            # Xử lý datetime object
            health_timestamp_iso = (
                health.timestamp.isoformat()
                if health
                and hasattr(health, "timestamp")
                and isinstance(health.timestamp, datetime)
                else "unknown"
            )
            return {
                "timestamp": datetime.now().isoformat(),
                "health": {
                    "timestamp": health_timestamp_iso,
                    "status": health.status.value
                    if health and hasattr(health, "status")
                    else "unknown",                    "checks": [
                        {
                            "name": check.name,
                            "status": check.status.value,
                            "message": check.message,
                            "response_time_ms": check.response_time_ms,
                        }
                        for check in (
                            health.checks
                            if health and hasattr(health, "checks")
                            else []
                        )
                    ],
                    "summary": health.summary
                    if health and hasattr(health, "summary")
                    else {},                },
                "metrics": metrics_overview,
                "traces": {
                    "recent_traces": recent_traces,
                    "total_traces": len(recent_traces),
                },
                "logs": log_stats,
            }
        except Exception as e:
            self.logger.error(f"Failed to get dashboard data: {e}")
            return {"error": str(e)}


class DashboardHandler(BaseHTTPRequestHandler):
    """HTTP request handler for the dashboard"""

    # THAY ĐỔI NHỎ: Thêm __init__ để gán thuộc tính dashboard rõ ràng hơn
    def __init__(self, request, client_address, server):
        dashboard = getattr(server, "dashboard", None)
        if dashboard is None:
            raise ValueError("Dashboard instance not found in server")
        self.dashboard_instance: ObservabilityDashboard = dashboard
        super().__init__(request, client_address, server)

    def do_GET(self):
        """Handle GET requests"""
        try:
            parsed_path = urllib.parse.urlparse(self.path)
            path = parsed_path.path

            if path == "/":
                self._serve_dashboard()
            elif path == "/api/data":
                self._serve_api_data()
            elif path == "/api/health":
                self._serve_health()
            elif path == "/api/metrics":
                self._serve_metrics()
            elif path == "/api/traces":
                self._serve_traces()
            elif path == "/api/logs":
                self._serve_logs()
            else:
                self._serve_404()

        except Exception as e:
            # Truy cập dashboard qua self.dashboard_instance đã được gán trong __init__
            self.dashboard_instance.logger.error(
                f"Handler error processing request {self.path}: {e}"
            )
            self._serve_error(str(e))

    def _serve_dashboard(self):
        """Serve the main dashboard HTML"""
        html = self._get_dashboard_html()
        self._send_response(200, "text/html", html)

    def _serve_api_data(self):
        """Serve comprehensive dashboard data"""
        data = self.dashboard_instance.get_dashboard_data()
        self._send_json_response(200, data)

    def _serve_health(self):
        """Serve health status"""
        health = (
            self.dashboard_instance.health_monitor.get_health_status()
            if self.dashboard_instance.health_monitor
            else None
        )
        # Xử lý datetime object
        health_timestamp_iso = (
            health.timestamp.isoformat()
            if health
            and hasattr(health, "timestamp")
            and isinstance(health.timestamp, datetime)
            else "unknown"
        )
        health_dict = {
            "status": health.status.value
            if health and hasattr(health, "status")
            else "unknown",            "timestamp": health_timestamp_iso,
            "checks": [
                {
                    "name": check.name,
                    "status": check.status.value,
                    "message": check.message,
                    "response_time_ms": check.response_time_ms,
                    "details": check.details,
                }
                for check in (
                    health.checks if health and hasattr(health, "checks") else []
                )
            ],
            "summary": health.summary if health and hasattr(health, "summary") else {},        }
        self._send_json_response(200, health_dict)

    def _serve_metrics(self):
        """Serve metrics data"""
        overview = (
            self.dashboard_instance.metrics_collector.get_metrics_overview()
            if self.dashboard_instance.metrics_collector
            else {}
        )
        self._send_json_response(200, overview)

    def _serve_traces(self):
        """Serve traces data"""
        traces = (
            self.dashboard_instance.tracer.get_traces_overview(limit=50)
            if self.dashboard_instance.tracer
            else []
        )
        self._send_json_response(200, {"traces": traces})

    def _serve_logs(self):
        """Serve logs data"""
        log_stats = (
            self.dashboard_instance.logger.get_log_stats()
            if hasattr(self.dashboard_instance.logger, "get_log_stats")
            else {}
        )
        self._send_json_response(200, log_stats)

    def _serve_404(self):
        """Serve 404 error"""
        self._send_response(404, "text/plain", "Not Found")

    def _serve_error(self, error_message: str):
        """Serve error response"""
        error_data = {"error": error_message}
        self._send_json_response(500, error_data)

    def _send_response(self, status_code: int, content_type: str, content: str):
        """Send HTTP response"""
        self.send_response(status_code)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(content.encode("utf-8"))))
        self.end_headers()
        self.wfile.write(content.encode("utf-8"))

    def _send_json_response(self, status_code: int, data: dict[str, Any]):
        """Send JSON response"""
        json_content = json.dumps(data, indent=2, ensure_ascii=False, default=str)
        self._send_response(status_code, "application/json", json_content)

    def _get_dashboard_html(self) -> str:
        """Get dashboard HTML content"""
        # Giữ nguyên HTML content, đã kiểm tra kỹ lưỡng
        return """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>StillMe Observability Dashboard</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background-color: #f5f5f5;
            color: #333;
        }

        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 1rem 2rem;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }

        .header h1 {
            font-size: 1.5rem;
            font-weight: 600;
        }

        .container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 2rem;
        }

        .grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 1.5rem;
            margin-bottom: 2rem;
        }

        .card {
            background: white;
            border-radius: 8px;
            padding: 1.5rem;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            border: 1px solid #e1e5e9;
        }

        .card h2 {
            font-size: 1.25rem;
            margin-bottom: 1rem;
            color: #2c3e50;
        }

        .status {
            display: inline-block;
            padding: 0.25rem 0.75rem;
            border-radius: 20px;
            font-size: 0.875rem;
            font-weight: 500;
        }

        .status.healthy {
            background-color: #d4edda;
            color: #155724;
        }

        .status.degraded {
            background-color: #fff3cd;
            color: #856404;
        }

        .status.unhealthy {
            background-color: #f8d7da;
            color: #721c24;
        }

        .metric {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 0.5rem 0;
            border-bottom: 1px solid #f0f0f0;
        }

        .metric:last-child {
            border-bottom: none;
        }

        .metric-label {
            font-weight: 500;
        }

        .metric-value {
            color: #666;
        }

        .refresh-btn {
            background: #667eea;
            color: white;
            border: none;
            padding: 0.5rem 1rem;
            border-radius: 4px;
            cursor: pointer;
            font-size: 0.875rem;
            margin-bottom: 1rem;
        }

        .refresh-btn:hover {
            background: #5a6fd8;
        }

        .loading {
            text-align: center;
            color: #666;
            padding: 2rem;
        }

        .error {
            color: #e74c3c;
            background: #fdf2f2;
            padding: 1rem;
            border-radius: 4px;
            border: 1px solid #fecaca;
        }

        .health-check {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 0.75rem 0;
            border-bottom: 1px solid #f0f0f0;
        }

        .health-check:last-child {
            border-bottom: none;
        }

        .health-check-name {
            font-weight: 500;
        }

        .health-check-message {
            color: #666;
            font-size: 0.875rem;
        }

        .trace-item {
            padding: 0.75rem 0;
            border-bottom: 1px solid #f0f0f0;
        }

        .trace-item:last-child {
            border-bottom: none;
        }

        .trace-id {
            font-family: monospace;
            font-size: 0.875rem;
            color: #666;
        }

        .trace-duration {
            color: #28a745;
            font-weight: 500;
        }

        .trace-error {
            color: #dc3545;
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>🔍 StillMe Observability Dashboard</h1>
    </div>

    <div class="container">
        <button class="refresh-btn" onclick="refreshData()">🔄 Refresh</button>

        <div class="grid">
            <div class="card">
                <h2>🏥 System Health</h2>
                <div id="health-content">
                    <div class="loading">Loading health status...</div>
                </div>
            </div>

            <div class="card">
                <h2>📊 Metrics Overview</h2>
                <div id="metrics-content">
                    <div class="loading">Loading metrics...</div>
                </div>
            </div>

            <div class="card">
                <h2>🔍 Recent Traces</h2>
                <div id="traces-content">
                    <div class="loading">Loading traces...</div>
                </div>
            </div>

            <div class="card">
                <h2>📝 Log Statistics</h2>
                <div id="logs-content">
                    <div class="loading">Loading log stats...</div>
                </div>
            </div>
        </div>
    </div>

    <script>
        async function fetchData(url) {
            try {
                const response = await fetch(url);
                if (!response.ok) {
                    const errorText = await response.text();
                    try {
                        const errorJson = JSON.parse(errorText);
                        throw new Error(`API Error: ${errorJson.error || response.statusText}`);
                    } catch {
                        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                    }
                }
                return await response.json();
            } catch (error) {
                console.error('Fetch error:', error);
                throw error;
            }
        }

        function updateHealth(data) {
            const content = document.getElementById('health-content');

            if (data.error) {
                content.innerHTML = `<div class="error">Error: ${data.error}</div>`;
                return;
            }

            const statusClass = data.status.toLowerCase();
            const healthPercentage = data.summary.health_percentage || 0;

            let html = `
                <div class="metric">
                    <span class="metric-label">Overall Status</span>
                    <span class="status ${statusClass}">${data.status.toUpperCase()}</span>
                </div>
                <div class="metric">
                    <span class="metric-label">Health Percentage</span>
                    <span class="metric-value">${healthPercentage.toFixed(1)}%</span>
                </div>
                <div class="metric">
                    <span class="metric-label">Total Checks</span>
                    <span class="metric-value">${data.summary.total_checks}</span>
                </div>
            `;

            if (data.checks && data.checks.length > 0) {
                html += '<h3 style="margin-top: 1rem; margin-bottom: 0.5rem;">Health Checks</h3>';
                data.checks.forEach(check => {
                    const checkStatusClass = check.status.toLowerCase();
                    const responseTime = check.response_time_ms ? `${check.response_time_ms.toFixed(1)}ms` : 'N/A';

                    html += `
                        <div class="health-check">
                            <div>
                                <div class="health-check-name">${check.name}</div>
                                <div class="health-check-message">${check.message}</div>
                            </div>
                            <div>
                                <span class="status ${checkStatusClass}">${check.status.toUpperCase()}</span>
                                <div style="font-size: 0.75rem; color: #666; margin-top: 0.25rem;">${responseTime}</div>
                            </div>
                        </div>
                    `;
                });
            }

            content.innerHTML = html;
        }

        function updateMetrics(data) {
            const content = document.getElementById('metrics-content');

            if (data.error) {
                content.innerHTML = `<div class="error">Error: ${data.error}</div>`;
                return;
            }

            let html = '';

            if (data.total_metrics !== undefined) {
                html += `
                    <div class="metric">
                        <span class="metric-label">Total Metrics</span>
                        <span class="metric-value">${data.total_metrics.toLocaleString()}</span>
                    </div>
                `;
            }

            if (data.unique_metrics !== undefined) {
                html += `
                    <div class="metric">
                        <span class="metric-label">Unique Metrics</span>
                        <span class="metric-value">${data.unique_metrics}</span>
                    </div>
                `;
            }

            if (data.metrics_by_type) {
                html += '<h3 style="margin-top: 1rem; margin-bottom: 0.5rem;">By Type</h3>';
                Object.entries(data.metrics_by_type).forEach(([type, count]) => {
                    html += `
                        <div class="metric">
                            <span class="metric-label">${type}</span>
                            <span class="metric-value">${count}</span>
                        </div>
                    `;
                });
            }

            if (data.database_size !== undefined) {
                const sizeMB = (data.database_size / 1024 / 1024).toFixed(2);
                html += `
                    <div class="metric">
                        <span class="metric-label">Database Size</span>
                        <span class="metric-value">${sizeMB} MB</span>
                    </div>
                `;
            }

            content.innerHTML = html || '<div class="loading">No metrics data available</div>';
        }

        function updateTraces(data) {
            const content = document.getElementById('traces-content');

            if (data.error) {
                content.innerHTML = `<div class="error">Error: ${data.error}</div>`;
                return;
            }

            const tracesArray = data.traces?.recent_traces || data.traces || [];

            if (tracesArray.length === 0) {
                content.innerHTML = '<div class="loading">No traces available</div>';
                return;
            }

            let html = '';
            tracesArray.slice(0, 10).forEach(trace => {
                const duration = trace.total_duration ? `${trace.total_duration.toFixed(1)}ms` : 'N/A';
                const errorClass = trace.has_error ? 'trace-error' : '';

                html += `
                    <div class="trace-item">
                        <div class="trace-id">${trace.trace_id.substring(0, 8)}...</div>
                        <div style="display: flex; justify-content: space-between; align-items: center; margin-top: 0.25rem;">
                            <span>${trace.span_count} spans</span>
                            <span class="trace-duration ${errorClass}">${duration}</span>
                        </div>
                    </div>
                `;
            });

            content.innerHTML = html;
        }

        function updateLogs(data) {
            const content = document.getElementById('logs-content');

            if (data.error) {
                content.innerHTML = `<div class="error">Error: ${data.error}</div>`;
                return;
            }

            let html = '';

            if (data.total_logs !== undefined) {
                html += `
                    <div class="metric">
                        <span class="metric-label">Total Logs</span>
                        <span class="metric-value">${data.total_logs.toLocaleString()}</span>
                    </div>
                `;
            }

            if (data.file_size_mb !== undefined) {
                html += `
                    <div class="metric">
                        <span class="metric-label">Log File Size</span>
                        <span class="metric-value">${data.file_size_mb.toFixed(2)} MB</span>
                    </div>
                `;
            }

            if (data.level_counts) {
                html += '<h3 style="margin-top: 1rem; margin-bottom: 0.5rem;">By Level</h3>';
                Object.entries(data.level_counts).forEach(([level, count]) => {
                    html += `
                        <div class="metric">
                            <span class="metric-label">${level}</span>
                            <span class="metric-value">${count}</span>
                        </div>
                    `;
                });
            }

            content.innerHTML = html || '<div class="loading">No log data available</div>';
        }

        async function refreshData() {
            try {
                const healthData = await fetchData('/api/health');
                updateHealth(healthData);

                const metricsData = await fetchData('/api/metrics');
                updateMetrics(metricsData);

                const tracesData = await fetchData('/api/traces');
                updateTraces(tracesData);

                const logsData = await fetchData('/api/logs');
                updateLogs(logsData);

            } catch (error) {
                console.error('Failed to refresh data:', error);
                const errorMessage = error.message || 'Unknown error';
                const errorHtml = `<div class="error">Failed to load data: ${errorMessage}</div>`;
                document.getElementById('health-content').innerHTML = errorHtml;
                document.getElementById('metrics-content').innerHTML = errorHtml;
                document.getElementById('traces-content').innerHTML = errorHtml;
                document.getElementById('logs-content').innerHTML = errorHtml;
            }
        }

        document.addEventListener('DOMContentLoaded', refreshData);
        setInterval(refreshData, 30000);
    </script>
</body>
</html>
        """

    def log_message(self, format, *args):
        """Override to suppress default logging"""
        pass


# Global dashboard instance
_global_dashboard: ObservabilityDashboard | None = None


def get_dashboard(port: int = 8080, host: str = "localhost") -> ObservabilityDashboard:
    """Get or create global dashboard"""
    global _global_dashboard
    if _global_dashboard is None:
        _global_dashboard = ObservabilityDashboard(port, host)
    return _global_dashboard


def start_dashboard(
    port: int = 8080, host: str = "localhost", open_browser: bool = True
):
    """Start the observability dashboard"""
    dashboard = get_dashboard(port, host)
    dashboard.start(open_browser)
    return dashboard
