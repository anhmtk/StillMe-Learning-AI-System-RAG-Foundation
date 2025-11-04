#!/usr/bin/env python3
"""Wrapper script to start Streamlit dashboard with Railway PORT environment variable."""
import os
import subprocess
import sys

# Get PORT from environment (Railway injects this)
port = os.getenv("PORT", "8080")

# Convert to integer to ensure valid port
try:
    port_int = int(port)
except ValueError:
    print(f"Error: Invalid PORT value '{port}'. Using default 8080.")
    port_int = 8080

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

print(f"Starting Streamlit dashboard on port {port_int}...")
print(f"API_BASE: {os.getenv('STILLME_API_BASE', 'NOT SET')}")
sys.exit(subprocess.run(cmd).returncode)

