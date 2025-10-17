#!/usr/bin/env python3
"""
Debug Scheduler Issues
"""

import asyncio
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


async def debug_scheduler():
    """Debug scheduler issues"""
    print("🔍 Debugging Scheduler Issues")
    print("=" * 50)
    
    try:
        from stillme_core.modules.automated_scheduler import AutomatedScheduler
        
        # Create scheduler
        scheduler = AutomatedScheduler()
        print("✅ Scheduler created")
        
        # Check config
        print(f"📅 Learning times: {scheduler.config.daily_learning_times}")
        print(f"⏱️  Interval: {scheduler.config.auto_learning_interval} minutes")
        
        # Initialize scheduler
        print("\n🔄 Initializing scheduler...")
        await scheduler.initialize()
        print("✅ Scheduler initialized")
        
        # Start scheduler
        print("\n🚀 Starting scheduler...")
        await scheduler.start()
        print("✅ Scheduler started")
        
        # Get status
        status = scheduler.get_status()
        print(f"\n📊 Scheduler Status:")
        print(f"  Status: {status['status']}")
        print(f"  Jobs: {len(status['jobs'])}")
        
        for job_info in status['jobs']:
            print(f"    - {job_info.get('id', 'N/A')}: {job_info.get('name', 'N/A')} - {job_info.get('next_run', 'N/A')}")
        
        # Check if jobs are actually scheduled
        if scheduler.scheduler:
            jobs = scheduler.scheduler.get_jobs()
            print(f"\n📋 APScheduler Jobs: {len(jobs)}")
            for job in jobs:
                print(f"    - {job.id}: {job.name} - Next: {job.next_run_time}")
        
        # Stop scheduler
        await scheduler.stop()
        print("\n⏹️  Scheduler stopped")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(debug_scheduler())
