#!/usr/bin/env python3
"""Wrapper script to start Streamlit dashboard with Railway PORT environment variable."""
import os
import subprocess
import sys

# Get PORT from environment (Railway injects this)
port = os.getenv("PORT", "8080")

# Start Streamlit with the port
cmd = [
    "streamlit", "run", "dashboard.py",
    "--server.port", str(port),
    "--server.address", "0.0.0.0",
    "--server.headless", "true"
]

print(f"Starting Streamlit dashboard on port {port}...")
sys.exit(subprocess.run(cmd).returncode)

