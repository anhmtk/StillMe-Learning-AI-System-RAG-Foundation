#!/usr/bin/env python3
"""
Test StillMe Notification System
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


async def test_notifications():
    """Test all notification channels"""
    print("🧪 Testing StillMe Notification System")
    print("=" * 50)
    
    try:
        from stillme_core.alerting.alert_manager import send_alert
        
        # Test Telegram
        print("📱 Testing Telegram notification...")
        result = await send_alert(
            alert_type='test',
            severity='medium',
            title='🧪 Test notification from StillMe Learning System',
            message='This is a test alert to verify notification system is working properly.',
            component='learning_system',
            channels=['telegram']
        )
        print(f"  Telegram result: {result}")
        
        # Test Email
        print("📧 Testing Email notification...")
        result = await send_alert(
            alert_type='test',
            severity='medium', 
            title='🧪 Test Email from StillMe Learning System',
            message='This is a test email to verify email notification system.',
            component='learning_system',
            channels=['email']
        )
        print(f"  Email result: {result}")
        
        # Test Desktop
        print("🖥️ Testing Desktop notification...")
        result = await send_alert(
            alert_type='test',
            severity='medium',
            title='🧪 Test Desktop from StillMe Learning System', 
            message='This is a test desktop notification.',
            component='learning_system',
            channels=['desktop']
        )
        print(f"  Desktop result: {result}")
        
        print("\n✅ Notification tests completed!")
        
    except Exception as e:
        print(f"❌ Error testing notifications: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_notifications())
