#!/usr/bin/env python3
"""
StillMe Auto-Start Learning System
=================================

Automatically starts the StillMe learning system with all 12 sources.
This script should be run at system startup to ensure continuous learning.

Author: StillMe AI Framework
Version: 2.0.0
"""

import asyncio
import logging
import os
import signal
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parent
sys.path.insert(0, str(project_root))

# Load environment variables
try:
    from stillme_core.env_loader import load_env_hierarchy
    load_env_hierarchy()
except ImportError:
    print("Warning: Could not import env_loader")
except Exception as e:
    print(f"Warning: Error loading environment: {e}")


class StillMeAutoStart:
    """Auto-start manager for StillMe learning system"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.scheduler = None
        self.is_running = False
        
    async def start(self):
        """Start the complete StillMe learning system"""
        print("🚀 StillMe Auto-Start Learning System")
        print("=" * 50)
        
        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            handlers=[
                logging.FileHandler("logs/stillme_autostart.log"),
                logging.StreamHandler()
            ]
        )
        
        try:
            # Initialize scheduler
            from stillme_core.modules.automated_scheduler import AutomatedScheduler
            self.scheduler = AutomatedScheduler()
            
            # Initialize with framework
            await self.scheduler.initialize()
            
            # Start scheduler
            await self.scheduler.start()
            self.is_running = True
            
            print("✅ StillMe Learning System started successfully!")
            print("📅 Auto-learning: 12 times per day (every 2 hours)")
            print("📊 Weekly analysis: Monday 10:00 AM")
            print("🔧 Monthly improvement: 1st of month 11:00 AM")
            print("💓 Health check: Every 30 minutes")
            print("\n🔄 System is now running automatically...")
            print("⏹️  Press Ctrl+C to stop")
            
            # Keep running
            while self.is_running:
                await asyncio.sleep(60)  # Check every minute
                
        except Exception as e:
            self.logger.error(f"Failed to start StillMe learning system: {e}")
            print(f"❌ Error: {e}")
            return False
            
        return True
    
    async def stop(self):
        """Stop the learning system"""
        if self.scheduler:
            await self.scheduler.stop()
        self.is_running = False
        print("\n👋 StillMe Learning System stopped.")


async def main():
    """Main function"""
    autostart = StillMeAutoStart()
    
    # Setup signal handlers
    def signal_handler():
        print("\n🛑 Signal received, stopping system...")
        asyncio.create_task(autostart.stop())
    
    if sys.platform != "win32":
        loop = asyncio.get_event_loop()
        loop.add_signal_handler(signal.SIGINT, signal_handler)
        loop.add_signal_handler(signal.SIGTERM, signal_handler)
    
    try:
        await autostart.start()
    except KeyboardInterrupt:
        print("\n🛑 Keyboard interrupt received")
    finally:
        await autostart.stop()


if __name__ == "__main__":
    # Create logs directory
    Path("logs").mkdir(exist_ok=True)
    
    # Run the system
    asyncio.run(main())
