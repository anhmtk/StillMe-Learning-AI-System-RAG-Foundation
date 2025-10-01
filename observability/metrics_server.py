"""
Prometheus Metrics Server
========================

Exposes Prometheus metrics for monitoring and observability.
Provides /metrics endpoint with comprehensive system metrics.

Author: StillMe AI Framework
Created: 2025-01-08
"""

import time
import threading
from typing import Dict, Any
from http.server import HTTPServer, BaseHTTPRequestHandler
import json


class MetricsCollector:
    """Collects and stores metrics for Prometheus export"""

    def __init__(self):
        """Initialize metrics collector"""
        self.metrics = {
            # Request metrics
            'requests_total': 0,
            'requests_duration_seconds': 0.0,
            'requests_duration_bucket': {},

            # Clarification metrics
            'clarify_trigger_total': 0,
            'clarify_trigger_by_type': {},

            # Error metrics
            'errors_total': 0,
            'errors_by_type': {},

            # Detector metrics
            'detector_hits_total': 0,
            'detector_hits_by_type': {},

            # System metrics
            'system_uptime_seconds': 0.0,
            'system_memory_usage_bytes': 0,
            'system_cpu_usage_percent': 0.0,
        }
        self.start_time = time.time()
        self.lock = threading.Lock()

    def increment_requests(self, duration: float = 0.0):
        """Increment request counter"""
        with self.lock:
            self.metrics['requests_total'] += 1
            self.metrics['requests_duration_seconds'] += duration

            # Update duration buckets
            bucket_key = self._get_duration_bucket(duration)
            self.metrics['requests_duration_bucket'][bucket_key] = \
                self.metrics['requests_duration_bucket'].get(bucket_key, 0) + 1

    def increment_clarify_trigger(self, trigger_type: str):
        """Increment clarification trigger counter"""
        with self.lock:
            self.metrics['clarify_trigger_total'] += 1
            self.metrics['clarify_trigger_by_type'][trigger_type] = \
                self.metrics['clarify_trigger_by_type'].get(trigger_type, 0) + 1

    def increment_errors(self, error_type: str):
        """Increment error counter"""
        with self.lock:
            self.metrics['errors_total'] += 1
            self.metrics['errors_by_type'][error_type] = \
                self.metrics['errors_by_type'].get(error_type, 0) + 1

    def increment_detector_hits(self, detector_type: str):
        """Increment detector hits counter"""
        with self.lock:
            self.metrics['detector_hits_total'] += 1
            self.metrics['detector_hits_by_type'][detector_type] = \
                self.metrics['detector_hits_by_type'].get(detector_type, 0) + 1

    def update_system_metrics(self, memory_bytes: int, cpu_percent: float):
        """Update system metrics"""
        with self.lock:
            self.metrics['system_uptime_seconds'] = time.time() - self.start_time
            self.metrics['system_memory_usage_bytes'] = memory_bytes
            self.metrics['system_cpu_usage_percent'] = cpu_percent

    def _get_duration_bucket(self, duration: float) -> str:
        """Get duration bucket for histogram"""
        if duration < 0.1:
            return "0.1"
        elif duration < 0.5:
            return "0.5"
        elif duration < 1.0:
            return "1.0"
        elif duration < 2.0:
            return "2.0"
        else:
            return "5.0"

    def get_metrics(self) -> str:
        """Get metrics in Prometheus format"""
        with self.lock:
            lines = []

            # Request metrics
            lines.append(f"# HELP requests_total Total number of requests")
            lines.append(f"# TYPE requests_total counter")
            lines.append(f"requests_total {self.metrics['requests_total']}")

            lines.append(f"# HELP requests_duration_seconds Total request duration")
            lines.append(f"# TYPE requests_duration_seconds counter")
            lines.append(f"requests_duration_seconds {self.metrics['requests_duration_seconds']:.3f}")

            # Duration buckets
            lines.append(f"# HELP requests_duration_bucket Request duration buckets")
            lines.append(f"# TYPE requests_duration_bucket histogram")
            for bucket, count in self.metrics['requests_duration_bucket'].items():
                lines.append(f'requests_duration_bucket{{le="{bucket}"}} {count}')
            lines.append(f'requests_duration_bucket{{le="+Inf"}} {self.metrics["requests_total"]}')

            # Clarification metrics
            lines.append(f"# HELP clarify_trigger_total Total clarification triggers")
            lines.append(f"# TYPE clarify_trigger_total counter")
            lines.append(f"clarify_trigger_total {self.metrics['clarify_trigger_total']}")

            for trigger_type, count in self.metrics['clarify_trigger_by_type'].items():
                lines.append(f'clarify_trigger_total{{type="{trigger_type}"}} {count}')

            # Error metrics
            lines.append(f"# HELP errors_total Total errors")
            lines.append(f"# TYPE errors_total counter")
            lines.append(f"errors_total {self.metrics['errors_total']}")

            for error_type, count in self.metrics['errors_by_type'].items():
                lines.append(f'errors_total{{type="{error_type}"}} {count}')

            # Detector metrics
            lines.append(f"# HELP detector_hits_total Total detector hits")
            lines.append(f"# TYPE detector_hits_total counter")
            lines.append(f"detector_hits_total {self.metrics['detector_hits_total']}")

            for detector_type, count in self.metrics['detector_hits_by_type'].items():
                lines.append(f'detector_hits_total{{type="{detector_type}"}} {count}')

            # System metrics
            lines.append(f"# HELP system_uptime_seconds System uptime in seconds")
            lines.append(f"# TYPE system_uptime_seconds gauge")
            lines.append(f"system_uptime_seconds {self.metrics['system_uptime_seconds']:.3f}")

            lines.append(f"# HELP system_memory_usage_bytes System memory usage in bytes")
            lines.append(f"# TYPE system_memory_usage_bytes gauge")
            lines.append(f"system_memory_usage_bytes {self.metrics['system_memory_usage_bytes']}")

            lines.append(f"# HELP system_cpu_usage_percent System CPU usage percentage")
            lines.append(f"# TYPE system_cpu_usage_percent gauge")
            lines.append(f"system_cpu_usage_percent {self.metrics['system_cpu_usage_percent']:.3f}")

            return "\n".join(lines)


# Global metrics collector
metrics_collector = MetricsCollector()


class MetricsHandler(BaseHTTPRequestHandler):
    """HTTP handler for metrics endpoint"""

    def do_GET(self):
        """Handle GET requests"""
        if self.path == '/metrics':
            # Update system metrics
            try:
                import psutil
                process = psutil.Process()
                memory_bytes = process.memory_info().rss
                cpu_percent = psutil.cpu_percent(interval=0.1)
                metrics_collector.update_system_metrics(memory_bytes, cpu_percent)
            except ImportError:
                # Fallback if psutil not available
                metrics_collector.update_system_metrics(0, 0.0)

            # Get metrics
            metrics_data = metrics_collector.get_metrics()

            self.send_response(200)
            self.send_header('Content-type', 'text/plain; version=0.0.4; charset=utf-8')
            self.end_headers()
            self.wfile.write(metrics_data.encode('utf-8'))

        elif self.path == '/health':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            health_data = {
                'status': 'healthy',
                'timestamp': time.time(),
                'uptime': metrics_collector.metrics['system_uptime_seconds']
            }
            self.wfile.write(json.dumps(health_data).encode())

        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        """Suppress default logging"""
        pass


def start_metrics_server(port=9090):
    """Start the metrics server"""
    server = HTTPServer(('localhost', port), MetricsHandler)
    print(f"Metrics server started on http://localhost:{port}")
    print("Available endpoints:")
    print("  GET /metrics - Prometheus metrics")
    print("  GET /health - Health check")
    print("Press Ctrl+C to stop")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down metrics server...")
        server.shutdown()


if __name__ == "__main__":
    start_metrics_server()
