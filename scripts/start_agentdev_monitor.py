#!/usr/bin/env python3
"""
🚀 AgentDev Operations Monitor - 24/7 Technical Manager
======================================================

Script để khởi động AgentDev Operations Monitor như một service 24/7.
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
import logging
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Import ops modules
from agent_dev.ops.monitor import PatrolRunner
from agent_dev.ops.escalation import EscalationManager

class AgentDevOpsService:
    """AgentDev Operations Service - 24/7 Technical Manager"""

    def __init__(self, config_file: str = None):
        self.config = self._load_config(config_file)
        self.patrol_runner = None
        self.escalation_manager = None
        self.running = False
        
        # Setup logging
        self._setup_logging()

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
            "quick_patrol_minutes": 15,
            "deep_patrol_hours": 6,
            "auto_fix_enabled": True,
            "notifications": {
                "console": True,
                "email": True,
                "telegram": True
            }
        }

    def _setup_logging(self):
        """Setup logging configuration"""
        log_dir = Path(self.config["project_root"]) / "logs"
        log_dir.mkdir(exist_ok=True)
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_dir / "agentdev_ops.log"),
                logging.StreamHandler()
            ]
        )

    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        print(f"\n🛑 Received signal {signum}, shutting down...")
        self.stop()

    def start(self):
        """Start the operations service"""
        print("🚀 Starting AgentDev Operations Service - 24/7 Technical Manager...")

        try:
            # Initialize components
            self.patrol_runner = PatrolRunner(self.config["project_root"])
            self.escalation_manager = EscalationManager()
            self.running = True

            print("✅ AgentDev Operations Service started successfully")
            print("📊 Service Status: Active")
            print(f"⏰ Quick patrol every {self.config['quick_patrol_minutes']} minutes")
            print(f"🔍 Deep patrol every {self.config['deep_patrol_hours']} hours")

            # Keep running
            self._run_forever()

        except Exception as e:
            print(f"❌ Failed to start service: {e}")
            sys.exit(1)

    def stop(self):
        """Stop the operations service"""
        if self.running:
            print("🛑 Stopping AgentDev Operations Service...")
            self.running = False
            print("✅ Service stopped")

    def _run_forever(self):
        """Run the service forever with patrol scheduling"""
        try:
            while self.running:
                current_time = time.time()
                
                # Check if quick patrol should run
                if self.patrol_runner.should_run_quick_patrol():
                    print("🔍 Running quick patrol...")
                    patrol_result = self.patrol_runner.run_quick_patrol()
                    escalation_result = self.escalation_manager.handle_incident(patrol_result)
                    self._log_patrol_result("quick", patrol_result, escalation_result)
                
                # Check if deep patrol should run
                if self.patrol_runner.should_run_deep_patrol():
                    print("🔍 Running deep patrol...")
                    patrol_result = self.patrol_runner.run_deep_patrol()
                    escalation_result = self.escalation_manager.handle_incident(patrol_result)
                    self._log_patrol_result("deep", patrol_result, escalation_result)
                
                # Sleep for 1 minute before next check
                time.sleep(60)

        except KeyboardInterrupt:
            self.stop()
    
    def _log_patrol_result(self, patrol_type: str, patrol_result: dict, escalation_result: dict):
        """Log patrol results"""
        logger.info(f"{patrol_type.capitalize()} patrol completed")
        logger.info(f"  - Success: {patrol_result.get('success', False)}")
        logger.info(f"  - Duration: {patrol_result.get('duration_seconds', 0):.2f}s")
        logger.info(f"  - Incidents: {escalation_result.get('incidents_found', 0)}")
        logger.info(f"  - Escalations: {escalation_result.get('escalations_sent', 0)}")
        logger.info(f"  - Auto-fixes: {escalation_result.get('auto_fixes_applied', 0)}")

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="AgentDev Operations Service - 24/7 Technical Manager")
    parser.add_argument("--config", help="Configuration file path")
    parser.add_argument("--daemon", action="store_true", help="Run as daemon")
    parser.add_argument("--status", action="store_true", help="Show status and exit")
    parser.add_argument("--dry-run", action="store_true", help="Run one patrol cycle and exit")

    args = parser.parse_args()

    # Create service
    service = AgentDevOpsService(args.config)

    if args.status:
        # Show status
        print("📊 AgentDev Operations Service Status:")
        print("  - Service: Ready")
        print("  - Patrol Runner: Initialized")
        print("  - Escalation Manager: Initialized")
        return

    if args.dry_run:
        # Run one patrol cycle
        print("🔍 Running dry-run patrol...")
        service.patrol_runner = PatrolRunner(service.config["project_root"])
        service.escalation_manager = EscalationManager()
        
        patrol_result = service.patrol_runner.run_quick_patrol()
        escalation_result = service.escalation_manager.handle_incident(patrol_result)
        
        print("📊 Dry-run Results:")
        print(f"  - Patrol Success: {patrol_result.get('success', False)}")
        print(f"  - Incidents Found: {escalation_result.get('incidents_found', 0)}")
        print(f"  - Escalations Sent: {escalation_result.get('escalations_sent', 0)}")
        return

    if args.daemon:
        # Run as daemon (simplified)
        print("🔄 Running as daemon...")
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
