#!/usr/bin/env python3
"""
Start Frontend Dashboard
"""

import os
import sys
import subprocess

def start_frontend():
    """Start frontend dashboard"""
    try:
        print("Starting StillMe V2 Frontend...")
        
        # Change to stillme_v2 directory
        os.chdir(os.path.dirname(os.path.abspath(__file__)))
        
        # Start streamlit server
        subprocess.run([
            sys.executable, "-m", "streamlit", "run", 
            "dashboard.py", 
            "--server.port", "8501"
        ])
        
    except Exception as e:
        print(f"Error starting frontend: {e}")

if __name__ == "__main__":
    start_frontend()
