#!/usr/bin/env python3
"""
Wrapper script to start Streamlit dashboard with Railway PORT and health check endpoint.
Uses a simple HTTP server to provide health check while Streamlit runs.
"""
import os
import subprocess
import sys
import threading
import time
from http.server import HTTPServer, BaseHTTPRequestHandler

# Get PORT from environment (Railway injects this)
port = os.getenv("PORT", "8080")

# Convert to integer to ensure valid port
try:
    port_int = int(port)
except ValueError:
    print(f"Error: Invalid PORT value '{port}'. Using default 8080.")
    port_int = 8080

# Health check handler
class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/health' or self.path == '/healthz':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(b'{"status":"healthy","service":"dashboard"}')
        else:
            # Redirect all other requests to Streamlit
            self.send_response(307)
            self.send_header('Location', f'http://localhost:{port_int}{self.path}')
            self.end_headers()
    
    def log_message(self, format, *args):
        # Suppress health check logs
        if '/health' not in args[0]:
            super().log_message(format, *args)

# Start health check server on a different port (port + 1)
health_port = port_int + 1
health_server = HTTPServer(('0.0.0.0', health_port), HealthHandler)

def run_health_server():
    print(f"Starting health check server on port {health_port}...")
    health_server.serve_forever()

# Start health check server in background thread
health_thread = threading.Thread(target=run_health_server, daemon=True)
health_thread.start()

# Wait a bit for health server to start
time.sleep(1)

# Start Streamlit with the port
cmd = [
    "streamlit", "run", "dashboard.py",
    "--server.port", str(port_int),
    "--server.address", "0.0.0.0",
    "--server.headless", "true",
    "--server.enableCORS", "false",
    "--server.enableXsrfProtection", "false",
    "--browser.gatherUsageStats", "false"
]

print(f"Starting Streamlit dashboard on port {port_int}...")
print(f"Health check available on port {health_port}...")
print(f"API_BASE: {os.getenv('STILLME_API_BASE', 'NOT SET')}")

# Run Streamlit (this will block)
sys.exit(subprocess.run(cmd).returncode)

