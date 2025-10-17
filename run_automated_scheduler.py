#!/usr/bin/env python3
"""
Run Automated Scheduler - Standalone script to run automated learning scheduler

Author: StillMe AI Framework
Version: 1.0.0
"""

import asyncio
import logging
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


async def main():
    """Main function to run automated scheduler"""
    print("🚀 StillMe Automated Learning Scheduler")
    print("=" * 50)

    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    try:
        # Import and initialize scheduler
        from stillme_core.modules.automated_scheduler import AutomatedScheduler
        
        print("📋 Environment Check:")
        import os
        print(f"  STILLME_DRY_RUN: {os.getenv('STILLME_DRY_RUN', 'NOT_SET')}")
        print(f"  STILLME_LEARNING_ENABLED: {os.getenv('STILLME_LEARNING_ENABLED', 'NOT_SET')}")
        print(f"  STILLME_ALERTS_ENABLED: {os.getenv('STILLME_ALERTS_ENABLED', 'NOT_SET')}")
        print(f"  TELEGRAM_BOT_TOKEN: {'SET' if os.getenv('TELEGRAM_BOT_TOKEN') else 'NOT_SET'}")
        print(f"  SMTP_SERVER: {'SET' if os.getenv('SMTP_SERVER') else 'NOT_SET'}")
        print()

        # Create scheduler instance
        scheduler = AutomatedScheduler()
        
        print("🔄 Starting automated scheduler...")
        
        # Initialize scheduler first
        await scheduler.initialize()
        
        # Setup signal handlers for graceful shutdown
        def signal_handler(signum, frame):
            print(f"\n🛑 Received signal {signum}, shutting down gracefully...")
            scheduler.stop()
            sys.exit(0)
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        # Start scheduler
        await scheduler.start()
        
        print("✅ Scheduler started successfully!")
        print("📱 Monitoring for learning opportunities...")
        print("🔄 Press Ctrl+C to stop")
        
        # Keep running
        while scheduler.is_running:
            await asyncio.sleep(1)
            
    except KeyboardInterrupt:
        print("\n🛑 Shutdown requested by user")
    except Exception as e:
        print(f"❌ Error starting scheduler: {e}")
        logging.exception("Scheduler error")
        return 1
    
    print("👋 Scheduler stopped")
    return 0


if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
        sys.exit(0)
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        sys.exit(1)
