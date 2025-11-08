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

# Log startup information
print("=" * 60)
print("StillMe Backend - Starting FastAPI Server")
print("=" * 60)
print(f"Port: {port_int}")
print(f"Host: 0.0.0.0")
print(f"Python: {sys.executable}")
print(f"Python Version: {sys.version}")
print("=" * 60)

# Start uvicorn with the port
# Note: RAG components initialization happens during module import
# This may take 10-30 seconds, but /health endpoint will return 200 immediately
cmd = [
    sys.executable, "-m", "uvicorn",
    "backend.api.main:app",
    "--host", "0.0.0.0",
    "--port", str(port_int),
    "--log-level", "info"
]

print(f"Starting FastAPI backend on port {port_int}...")
print("Note: RAG components initialization may take 10-30 seconds.")
print("The /health endpoint will return 200 immediately, even during initialization.")
print("=" * 60)

# Run uvicorn (this will block until server stops)
sys.exit(subprocess.run(cmd).returncode)

