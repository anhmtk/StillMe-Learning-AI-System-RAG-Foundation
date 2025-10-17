#!/usr/bin/env python3
"""
Test Scheduler Manual - Test auto learning session manually
"""

import asyncio
import logging
from stillme_core.env_loader import load_env_hierarchy

# Load environment
load_env_hierarchy()

async def test_auto_learning_session():
    """Test auto learning session manually"""
    print("🧪 Testing Auto Learning Session...")
    
    try:
        from stillme_core.modules.automated_scheduler import AutomatedScheduler
        
        # Create scheduler
        scheduler = AutomatedScheduler()
        await scheduler.initialize()
        
        # Run auto learning session manually
        await scheduler._run_auto_learning_session()
        
        print("✅ Auto learning session test completed!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_auto_learning_session())
