#!/usr/bin/env python3
"""
Simple Frontend Starter
"""

import os
import sys
import subprocess

def main():
    """Start frontend dashboard"""
    try:
        print("Starting StillMe V2 Frontend...")
        
        # Change to stillme_v2 directory
        os.chdir(os.path.dirname(os.path.abspath(__file__)))
        
        print("Starting dashboard on http://localhost:8501")
        
        # Start streamlit
        subprocess.run([
            sys.executable, "-m", "streamlit", "run", 
            "dashboard.py", 
            "--server.port", "8501",
            "--server.headless", "true"
        ])
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()