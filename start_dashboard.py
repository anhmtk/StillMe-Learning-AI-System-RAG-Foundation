#!/usr/bin/env python3
"""Wrapper script to start Streamlit dashboard with Railway PORT environment variable."""
import os
import subprocess
import sys

# Force stdout to be unbuffered for Railway
sys.stdout.reconfigure(line_buffering=True)

# Get PORT from environment (Railway injects this)
port = os.getenv("PORT", "8080")

# Convert to integer to ensure valid port
try:
    port_int = int(port)
except ValueError:
    print(f"Error: Invalid PORT value '{port}'. Using default 8080.", flush=True)
    port_int = 8080

print("=" * 60, flush=True)
print("StillMe Dashboard - Starting Streamlit Server", flush=True)
print("=" * 60, flush=True)
print(f"Port: {port_int}", flush=True)
print("Host: 0.0.0.0", flush=True)
print(f"API_BASE: {os.getenv('STILLME_API_BASE', 'NOT SET')}", flush=True)
print("=" * 60, flush=True)

# Start Streamlit with the port
# Additional flags for Railway compatibility:
# - enableCORS=false: Disable CORS (Railway handles this)
# - enableXsrfProtection=false: Disable XSRF protection for Railway
# - server.enableWebsocketCompression=false: Reduce overhead
cmd = [
    "streamlit", "run", "dashboard.py",
    "--server.port", str(port_int),
    "--server.address", "0.0.0.0",
    "--server.headless", "true",
    "--server.enableCORS", "false",
    "--server.enableXsrfProtection", "false",
    "--browser.gatherUsageStats", "false"
]

print(f"Starting Streamlit dashboard on port {port_int}...", flush=True)
sys.exit(subprocess.run(cmd).returncode)

