#!/usr/bin/env python3
"""
🚀 AgentDev Monitor Startup Script
==================================

Script để khởi động AgentDev Automated Monitor như một service.
Có thể chạy như:
- Background process
- Windows Service
- Linux Systemd service
- Docker container

Usage:
    python scripts/start_agentdev_monitor.py [--daemon] [--config config.json]
"""

import os
import sys
import time
import json
import signal
import argparse
from pathlib import Path

# Add agent-dev to path
sys.path.insert(0, str(Path(__file__).parent.parent / "agent-dev" / "core"))

from automated_monitor import AutomatedMonitor

class AgentDevMonitorService:
    """AgentDev Monitor as a service"""
    
    def __init__(self, config_file: str = None):
        self.config = self._load_config(config_file)
        self.monitor = None
        self.running = False
        
        # Setup signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _load_config(self, config_file: str) -> dict:
        """Load configuration from file"""
        if config_file and Path(config_file).exists():
            with open(config_file, 'r') as f:
                return json.load(f)
        
        # Default config
        return {
            "project_root": ".",
            "scan_interval_minutes": 15,
            "deep_scan_interval_hours": 2,
            "alert_thresholds": {
                "max_errors_per_file": 10,
                "max_total_errors": 50,
                "max_syntax_errors": 5
            },
            "auto_fix_enabled": True,
            "notifications": {
                "console": True,
                "email": False,
                "slack": False
            }
        }
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        print(f"\n🛑 Received signal {signum}, shutting down...")
        self.stop()
    
    def start(self):
        """Start the monitor service"""
        print("🚀 Starting AgentDev Monitor Service...")
        
        try:
            # Initialize monitor
            self.monitor = AutomatedMonitor(
                project_root=self.config["project_root"],
                config=self.config
            )
            
            # Start monitoring
            self.monitor.start_monitoring()
            self.running = True
            
            print("✅ AgentDev Monitor Service started successfully")
            print("📊 Monitor Status:", self.monitor.get_status())
            
            # Keep running
            self._run_forever()
            
        except Exception as e:
            print(f"❌ Failed to start service: {e}")
            sys.exit(1)
    
    def stop(self):
        """Stop the monitor service"""
        if self.monitor and self.running:
            print("🛑 Stopping AgentDev Monitor Service...")
            self.monitor.stop_monitoring()
            self.running = False
            print("✅ Service stopped")
    
    def _run_forever(self):
        """Run the service forever"""
        try:
            while self.running:
                time.sleep(60)  # Check every minute
                
                # Print status every hour
                if int(time.time()) % 3600 == 0:
                    status = self.monitor.get_status()
                    print(f"📊 Hourly Status: {status}")
                    
        except KeyboardInterrupt:
            self.stop()

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="AgentDev Monitor Service")
    parser.add_argument("--config", help="Configuration file path")
    parser.add_argument("--daemon", action="store_true", help="Run as daemon")
    parser.add_argument("--status", action="store_true", help="Show status and exit")
    
    args = parser.parse_args()
    
    # Create service
    service = AgentDevMonitorService(args.config)
    
    if args.status:
        # Show status
        if service.monitor:
            status = service.monitor.get_status()
            print("📊 AgentDev Monitor Status:")
            print(json.dumps(status, indent=2))
        else:
            print("❌ Monitor not running")
        return
    
    if args.daemon:
        # Run as daemon (simplified)
        print("🔄 Running as daemon...")
        # In a real implementation, you'd use python-daemon or similar
        # For now, just run in background
        import subprocess
        subprocess.Popen([
            sys.executable, __file__, 
            "--config", args.config or "config.json"
        ])
        print("✅ Daemon started")
        return
    
    # Run normally
    service.start()

if __name__ == "__main__":
    main()
