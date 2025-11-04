#!/usr/bin/env python3
"""Wrapper script to start FastAPI backend with Railway PORT environment variable."""
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

# Start uvicorn with the port
cmd = [
    sys.executable, "-m", "uvicorn",
    "backend.api.main:app",
    "--host", "0.0.0.0",
    "--port", str(port_int)
]

print(f"Starting FastAPI backend on port {port_int}...")
sys.exit(subprocess.run(cmd).returncode)

