#!/usr/bin/env python3
"""
🚀 Start AgentDev - Khởi động AgentDev
=====================================

Script khởi động AgentDev với:
1. Tự động phát hiện lỗi
2. Tự động sửa lỗi
3. Background monitoring
4. Real-time alerts

Usage:
    python scripts/start_agentdev.py [--interval 30] [--auto-fix] [--daemon]

Author: StillMe AI Framework
Version: 1.0.0
Date: 2025-09-30
"""

import argparse
import signal
import sys
import time
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

sys.path.insert(0, str(project_root / "agent_dev" / "core"))
from agent_dev.core.agentdev import AgentDev


class AgentDevService:
    """Service wrapper for AgentDev"""

    def __init__(self, interval: int = 30, auto_fix: bool = True, daemon: bool = False):
        self.interval = interval
        self.auto_fix = auto_fix
        self.daemon = daemon
        self.agentdev = None
        self.running = False

        # Setup signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        print(f"\n🛑 Received signal {signum}, shutting down...")
        self.stop()
        sys.exit(0)

    def start(self):
        """Start the service"""
        print("🚀 Starting AgentDev Service...")

        # Initialize AgentDev
        self.agentdev = AgentDev(project_root=str(project_root), auto_fix=self.auto_fix)

        # Start monitoring
        self.agentdev.start_monitoring(interval=self.interval)
        self.running = True

        print("✅ AgentDev Service started")
        print(f"   📊 Monitoring interval: {self.interval}s")
        print(f"   🔧 Auto-fix enabled: {self.auto_fix}")
        print(f"   🏠 Project root: {project_root}")

        if self.daemon:
            print("   🔄 Running in daemon mode")
            self._daemon_loop()
        else:
            print("   ⌨️  Press Ctrl+C to stop")
            self._interactive_loop()

    def stop(self):
        """Stop the service"""
        if self.agentdev and self.running:
            print("🛑 Stopping AgentDev Service...")
            self.agentdev.stop_monitoring()
            self.running = False
            print("✅ AgentDev Service stopped")

    def _daemon_loop(self):
        """Daemon mode loop"""
        try:
            while self.running:
                time.sleep(60)  # Check every minute

                # Print status
                status = self.agentdev.get_status()
                print(
                    f"📊 Status: {status['errors_in_queue']} errors in queue, "
                    f"{status['successful_fixes']} fixes applied"
                )

        except KeyboardInterrupt:
            self.stop()

    def _interactive_loop(self):
        """Interactive mode loop"""
        try:
            while self.running:
                time.sleep(10)  # Check every 10 seconds

                # Print status
                status = self.agentdev.get_status()
                if status["errors_in_queue"] > 0:
                    print(f"🔍 {status['errors_in_queue']} errors in queue")

        except KeyboardInterrupt:
            self.stop()

    def force_scan_and_fix(self):
        """Force scan and fix errors"""
        if self.agentdev:
            print("🔍 Force scanning and fixing errors...")
            result = self.agentdev.force_scan_and_fix()
            print(f"✅ {result['message']}")
            return result
        return None

    def get_status(self):
        """Get current status"""
        if self.agentdev:
            return self.agentdev.get_status()
        return None

    def get_fix_history(self):
        """Get fix history"""
        if self.agentdev:
            return self.agentdev.get_fix_history()
        return []


def main():
    """Main function"""
    parser = argparse.ArgumentParser(
        description="Start AgentDev Service",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/start_agentdev.py                    # Start with default settings
  python scripts/start_agentdev.py --interval 60      # Check every 60 seconds
  python scripts/start_agentdev.py --no-auto-fix      # Disable auto-fix
  python scripts/start_agentdev.py --daemon           # Run in daemon mode
        """,
    )

    parser.add_argument(
        "--interval",
        type=int,
        default=30,
        help="Monitoring interval in seconds (default: 30)",
    )

    parser.add_argument(
        "--auto-fix",
        action="store_true",
        default=True,
        help="Enable auto-fix (default: True)",
    )

    parser.add_argument("--no-auto-fix", action="store_true", help="Disable auto-fix")

    parser.add_argument("--daemon", action="store_true", help="Run in daemon mode")

    parser.add_argument(
        "--force-scan",
        action="store_true",
        help="Force scan and fix errors once, then exit",
    )

    args = parser.parse_args()

    # Handle auto-fix flag
    auto_fix = args.auto_fix and not args.no_auto_fix

    # Create service
    service = AgentDevService(
        interval=args.interval, auto_fix=auto_fix, daemon=args.daemon
    )

    try:
        if args.force_scan:
            # Force scan mode
            service.start()
            result = service.force_scan_and_fix()
            print(f"📊 Scan result: {result}")
            service.stop()
        else:
            # Normal service mode
            service.start()

    except Exception as e:
        print(f"❌ Error: {e}")
        service.stop()
        sys.exit(1)


if __name__ == "__main__":
    main()
