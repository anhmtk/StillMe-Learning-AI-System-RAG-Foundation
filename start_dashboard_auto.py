#!/usr/bin/env python3
"""
StillMe Dashboard Auto-Start Script
Tự động khởi động dashboard khi hệ thống boot
"""

import os
import sys
import time
import subprocess
import logging
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("dashboard_auto_start.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def check_dashboard_running():
    """Kiểm tra dashboard có đang chạy không"""
    try:
        result = subprocess.run(
            ["netstat", "-ano"], 
            capture_output=True, 
            text=True, 
            shell=True
        )
        return ":8529" in result.stdout
    except Exception as e:
        logger.error(f"Error checking dashboard status: {e}")
        return False

def start_dashboard():
    """Khởi động dashboard"""
    try:
        logger.info("🚀 Starting StillMe Dashboard...")
        
        # Change to project directory
        project_dir = Path(__file__).parent
        os.chdir(project_dir)
        
        # Start dashboard
        process = subprocess.Popen(
            [sys.executable, "start_dashboard.py"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Wait a bit for startup
        time.sleep(5)
        
        # Check if process is still running
        if process.poll() is None:
            logger.info("✅ Dashboard started successfully!")
            logger.info("🌐 Dashboard available at: http://localhost:8529")
            return process
        else:
            stdout, stderr = process.communicate()
            logger.error(f"❌ Dashboard failed to start:")
            logger.error(f"STDOUT: {stdout}")
            logger.error(f"STDERR: {stderr}")
            return None
            
    except Exception as e:
        logger.error(f"❌ Error starting dashboard: {e}")
        return None

def main():
    """Main function"""
    logger.info("🔍 StillMe Dashboard Auto-Start Monitor")
    logger.info("=" * 50)
    
    dashboard_process = None
    
    try:
        while True:
            # Check if dashboard is running
            if not check_dashboard_running():
                logger.warning("⚠️ Dashboard not running, starting...")
                
                # Kill old process if exists
                if dashboard_process and dashboard_process.poll() is None:
                    dashboard_process.terminate()
                    dashboard_process.wait()
                
                # Start new dashboard
                dashboard_process = start_dashboard()
                
                if dashboard_process is None:
                    logger.error("❌ Failed to start dashboard, retrying in 30 seconds...")
                    time.sleep(30)
                    continue
            else:
                logger.info("✅ Dashboard is running normally")
            
            # Wait before next check
            time.sleep(60)  # Check every minute
            
    except KeyboardInterrupt:
        logger.info("🛑 Auto-start monitor stopped by user")
    except Exception as e:
        logger.error(f"❌ Unexpected error: {e}")
    finally:
        # Cleanup
        if dashboard_process and dashboard_process.poll() is None:
            logger.info("🔄 Stopping dashboard...")
            dashboard_process.terminate()
            dashboard_process.wait()
        logger.info("👋 Auto-start monitor shutdown complete")

if __name__ == "__main__":
    main()
