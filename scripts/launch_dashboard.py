#!/usr/bin/env python3
"""
🚀 StillMe Dashboard Launcher
============================

Script khởi chạy dashboard với cấu hình tùy chỉnh.
Hỗ trợ Streamlit và FastAPI dashboards.

Tính năng:
- Auto-detect environment
- Config validation
- Port management
- Error handling
- Development mode

Author: StillMe AI Framework
Version: 1.0.0
Date: 2025-09-28
"""

import argparse
import os
import sys
import subprocess
import time
from pathlib import Path
import logging

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

logger = logging.getLogger(__name__)

def check_dependencies():
    """Check if required dependencies are installed"""
    required_packages = [
        'streamlit',
        'plotly',
        'pandas'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print(f"❌ Missing packages: {', '.join(missing_packages)}")
        print("📦 Install with: pip install -r requirements-dashboard.txt")
        return False
    
    return True

def check_data_availability():
    """Check if metrics data is available"""
    db_path = "data/metrics/metrics.db"
    events_dir = "data/metrics/events"
    
    if not Path(db_path).exists():
        print(f"⚠️  Database not found: {db_path}")
        print("📊 Run: python scripts/backfill_metrics.py --days 7")
        return False
    
    if not Path(events_dir).exists():
        print(f"⚠️  Events directory not found: {events_dir}")
        print("📊 Run: python scripts/backfill_metrics.py --days 7")
        return False
    
    return True

def launch_streamlit(port: int = 8501, host: str = "localhost", theme: str = "light"):
    """Launch Streamlit dashboard"""
    print(f"🚀 Launching Streamlit dashboard on {host}:{port}")
    
    # Set environment variables
    os.environ['STILLME_DASHBOARD_PORT'] = str(port)
    os.environ['STILLME_DASHBOARD_HOST'] = host
    os.environ['STILLME_DASHBOARD_THEME'] = theme
    
    # Streamlit command
    cmd = [
        sys.executable, "-m", "streamlit", "run",
        "dashboards/streamlit/app.py",
        "--server.port", str(port),
        "--server.address", host,
        "--theme.base", theme,
        "--browser.gatherUsageStats", "false"
    ]
    
    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to launch Streamlit: {e}")
        return False
    except KeyboardInterrupt:
        print("\n🛑 Dashboard stopped by user")
        return True
    
    return True

def launch_fastapi(port: int = 8000, host: str = "localhost"):
    """Launch FastAPI dashboard"""
    print(f"🚀 Launching FastAPI dashboard on {host}:{port}")
    
    # Set environment variables
    os.environ['STILLME_DASHBOARD_PORT'] = str(port)
    os.environ['STILLME_DASHBOARD_HOST'] = host
    
    # FastAPI command
    cmd = [
        sys.executable, "-m", "uvicorn",
        "dashboards.fastapi.app:app",
        "--host", host,
        "--port", str(port),
        "--reload"
    ]
    
    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to launch FastAPI: {e}")
        return False
    except KeyboardInterrupt:
        print("\n🛑 Dashboard stopped by user")
        return True
    
    return True

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="StillMe Dashboard Launcher")
    parser.add_argument("--type", choices=["streamlit", "fastapi"], default="streamlit", help="Dashboard type")
    parser.add_argument("--port", type=int, default=8501, help="Port number")
    parser.add_argument("--host", type=str, default="localhost", help="Host address")
    parser.add_argument("--theme", choices=["light", "dark"], default="light", help="Theme (Streamlit only)")
    parser.add_argument("--skip-checks", action="store_true", help="Skip dependency and data checks")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose logging")
    
    args = parser.parse_args()
    
    # Setup logging
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    print("🧠 StillMe Dashboard Launcher")
    print("=" * 40)
    
    # Check dependencies
    if not args.skip_checks:
        print("🔍 Checking dependencies...")
        if not check_dependencies():
            return 1
        
        print("📊 Checking data availability...")
        if not check_data_availability():
            return 1
        
        print("✅ All checks passed!")
    
    # Launch dashboard
    if args.type == "streamlit":
        success = launch_streamlit(args.port, args.host, args.theme)
    elif args.type == "fastapi":
        success = launch_fastapi(args.port, args.host)
    else:
        print(f"❌ Unknown dashboard type: {args.type}")
        return 1
    
    return 0 if success else 1

if __name__ == "__main__":
    exit(main())
