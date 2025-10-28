#!/usr/bin/env python3
"""
StillMe V2 Launcher
Simple script to start both backend and frontend
"""

import subprocess
import sys
import time
import os
import signal
from pathlib import Path

def start_backend():
    """Start the FastAPI backend"""
    print("🚀 Starting StillMe V2 Backend...")
    backend_cmd = [
        sys.executable, "-m", "uvicorn", 
        "backend.api.main:app", 
        "--port", "8000",
        "--host", "127.0.0.1"
    ]
    return subprocess.Popen(backend_cmd, cwd=Path(__file__).parent)

def start_frontend():
    """Start the Streamlit frontend"""
    print("🎨 Starting StillMe V2 Frontend...")
    frontend_cmd = [
        sys.executable, "-m", "streamlit", "run", 
        "frontend/app.py",
        "--server.port", "8501",
        "--server.address", "127.0.0.1"
    ]
    return subprocess.Popen(frontend_cmd, cwd=Path(__file__).parent)

def main():
    """Main launcher function"""
    print("🧠 StillMe V2 - Self-Evolving AI System")
    print("=" * 50)
    
    # Start backend
    backend_process = start_backend()
    time.sleep(3)  # Wait for backend to start
    
    # Start frontend
    frontend_process = start_frontend()
    time.sleep(3)  # Wait for frontend to start
    
    print("\n✅ StillMe V2 is running!")
    print("📊 Backend API: http://127.0.0.1:8000")
    print("🎨 Frontend Dashboard: http://127.0.0.1:8501")
    print("📖 API Documentation: http://127.0.0.1:8000/docs")
    print("\nPress Ctrl+C to stop all services...")
    
    try:
        # Keep running until interrupted
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n🛑 Shutting down StillMe V2...")
        backend_process.terminate()
        frontend_process.terminate()
        print("✅ All services stopped.")

if __name__ == "__main__":
    main()
