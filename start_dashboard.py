#!/usr/bin/env python3
"""
StillMe Dashboard Auto-Start Script
"""

import subprocess
import sys
import time
from pathlib import Path

def start_dashboard():
    """Start the StillMe dashboard"""
    print("🚀 Starting StillMe IPC Learning Dashboard...")
    
    # Get the dashboard directory
    dashboard_dir = Path(__file__).parent / "dashboards" / "streamlit"
    dashboard_file = dashboard_dir / "integrated_dashboard.py"
    
    if not dashboard_file.exists():
        print(f"❌ Dashboard file not found: {dashboard_file}")
        return False
    
    try:
        # Start streamlit in a new process
        cmd = [
            sys.executable, "-m", "streamlit", "run", 
            str(dashboard_file),
            "--server.port", "8529",
            "--server.headless", "true"
        ]
        
        print(f"📁 Running from: {dashboard_dir}")
        print(f"🌐 Dashboard will be available at: http://localhost:8529")
        print("⏳ Starting dashboard...")
        
        # Start the process
        process = subprocess.Popen(
            cmd,
            cwd=dashboard_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Wait a moment for startup
        time.sleep(3)
        
        # Check if process is still running
        if process.poll() is None:
            print("✅ Dashboard started successfully!")
            print("🌐 Open your browser and go to: http://localhost:8529")
            print("💬 You should see the integrated chat panel on the right side")
            print("🔄 Dashboard will continue running in the background")
            return True
        else:
            stdout, stderr = process.communicate()
            print(f"❌ Dashboard failed to start:")
            print(f"STDOUT: {stdout}")
            print(f"STDERR: {stderr}")
            return False
            
    except Exception as e:
        print(f"❌ Error starting dashboard: {e}")
        return False

if __name__ == "__main__":
    success = start_dashboard()
    if success:
        print("\n🎉 Dashboard is ready!")
        print("📱 You can now chat with StillMe and monitor learning progress")
    else:
        print("\n❌ Failed to start dashboard")
        sys.exit(1)
