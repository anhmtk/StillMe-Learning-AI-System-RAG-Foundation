#!/usr/bin/env python3
"""
Start Backend Server
"""

import os
import sys
import subprocess

# Add current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def start_backend():
    """Start backend server"""
    try:
        print("Starting StillMe V2 Backend...")
        
        # Change to stillme_v2 directory
        os.chdir(os.path.dirname(os.path.abspath(__file__)))
        
        # Start uvicorn server
        subprocess.run([
            sys.executable, "-m", "uvicorn", 
            "backend.api.main:app", 
            "--host", "127.0.0.1", 
            "--port", "8000",
            "--reload"
        ])
        
    except Exception as e:
        print(f"Error starting backend: {e}")

if __name__ == "__main__":
    start_backend()
