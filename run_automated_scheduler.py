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

# Add modules to path
sys.path.append(str(Path(__file__).parent))


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
        # Import modules
        from framework import StillMeFramework

        from modules.automated_scheduler import AutomatedScheduler, SchedulerConfig

        print("1. Initializing StillMe Framework...")
        framework = StillMeFramework()
        print("✅ Framework initialized")

        print("\n2. Creating Automated Scheduler...")
        # Create scheduler config
        config = SchedulerConfig(
            daily_learning_time="09:00",
            daily_learning_timezone="Asia/Ho_Chi_Minh",
            weekly_analysis_day=0,  # Monday
            weekly_analysis_time="10:00",
            monthly_improvement_day=1,
            monthly_improvement_time="11:00",
            health_check_interval=30,  # 30 minutes
        )

        scheduler = AutomatedScheduler(config)
        print("✅ Scheduler created")

        print("\n3. Initializing Scheduler...")
        success = await scheduler.initialize(framework)
        if not success:
            print("❌ Failed to initialize scheduler")
            return

        print("✅ Scheduler initialized")

        print("\n4. Starting Scheduler...")
        success = await scheduler.start()
        if not success:
            print("❌ Failed to start scheduler")
            return

        print("✅ Scheduler started successfully!")

        # Display schedule
        status = scheduler.get_status()
        print("\n📅 Scheduled Jobs:")
        for job in status["jobs"]:
            print(f"   - {job['name']}: {job['next_run']}")

        print("\n⏰ Scheduler is running...")
        print(f"📊 Daily learning: {config.daily_learning_time}")
        print(f"📈 Weekly analysis: Monday at {config.weekly_analysis_time}")
        print(
            f"🔧 Monthly improvement: {config.monthly_improvement_day}st at {config.monthly_improvement_time}"
        )
        print(f"💚 Health check: Every {config.health_check_interval} minutes")

        print("\n🔄 Press Ctrl+C to stop the scheduler...")

        # Keep running until interrupted
        try:
            while True:
                await asyncio.sleep(60)  # Check every minute

                # Display status every hour
                if hasattr(main, "last_status_time"):
                    if (
                        asyncio.get_event_loop().time() - main.last_status_time > 3600
                    ):  # 1 hour
                        status = scheduler.get_status()
                        stats = status["job_stats"]
                        print("\n📊 Hourly Status Update:")
                        for job_id, job_stat in stats.items():
                            print(
                                f"   - {job_id}: executed={job_stat['executed']}, failed={job_stat['failed']}"
                            )
                        main.last_status_time = asyncio.get_event_loop().time()
                else:
                    main.last_status_time = asyncio.get_event_loop().time()

        except KeyboardInterrupt:
            print("\n🛑 Shutting down scheduler...")
            scheduler.stop()
            print("✅ Scheduler stopped successfully")

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    # Setup signal handlers
    def signal_handler(signum, frame):
        print(f"\n🛑 Received signal {signum}, shutting down...")
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Run the scheduler
    asyncio.run(main())
