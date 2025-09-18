#!/usr/bin/env python3
"""
Test script for StillMe Email Notifications
"""

import asyncio
import os
import sys
from datetime import datetime
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from stillme_platform.gateway.services.email_notifier import (
    EmailNotifier, 
    send_alert_email, 
    send_health_email,
    email_notifier
)
from stillme_platform.gateway.services.notification_manager import (
    NotificationManager,
    NotificationChannel,
    AlertSeverity,
    send_alert,
    send_critical_alert,
    send_health_alert
)


async def test_email_notifier():
    """Test email notifier directly"""
    print("🧪 Testing Email Notifier...")
    
    # Test basic email sending
    success = await email_notifier.test_email("anhnguyen.nk86@gmail.com")
    
    if success:
        print("✅ Email Notifier test passed!")
    else:
        print("❌ Email Notifier test failed!")
    
    return success


async def test_alert_emails():
    """Test alert email functions"""
    print("🧪 Testing Alert Emails...")
    
    # Test alert email
    success1 = await send_alert_email(
        to="anhnguyen.nk86@gmail.com",
        title="StillMe System Alert",
        message="This is a test alert from StillMe AI System. The notification system is working correctly.",
        severity="medium",
        service="Test Service"
    )
    
    # Test health email
    success2 = await send_health_email(
        to="anhnguyen.nk86@gmail.com",
        service="Gateway Server",
        status="up",
        details="All systems are running normally. No issues detected."
    )
    
    if success1 and success2:
        print("✅ Alert emails test passed!")
    else:
        print("❌ Alert emails test failed!")
    
    return success1 and success2


async def test_notification_manager():
    """Test notification manager"""
    print("🧪 Testing Notification Manager...")
    
    # Initialize notification manager
    notification_manager = NotificationManager()
    await notification_manager.start()
    
    try:
        # Test basic notification
        message_id = await send_alert(
            title="StillMe Notification Test",
            body="This is a test notification from StillMe AI System. The notification manager is working correctly.",
            severity=AlertSeverity.INFO,
            channels=[NotificationChannel.EMAIL, NotificationChannel.INTERNAL]
        )
        
        print(f"📨 Notification sent with ID: {message_id}")
        
        # Test critical alert
        critical_id = await send_critical_alert(
            title="Critical System Alert",
            body="This is a critical alert test. Please check the system immediately."
        )
        
        print(f"🚨 Critical alert sent with ID: {critical_id}")
        
        # Test health alert
        health_id = await send_health_alert(
            service="Gateway Server",
            status="down",
            details="Gateway server is not responding to health checks."
        )
        
        print(f"🏥 Health alert sent with ID: {health_id}")
        
        # Wait a bit for processing
        await asyncio.sleep(2)
        
        # Get statistics
        stats = notification_manager.get_statistics()
        print(f"📊 Notification Statistics: {stats}")
        
        print("✅ Notification Manager test passed!")
        return True
        
    except Exception as e:
        print(f"❌ Notification Manager test failed: {e}")
        return False
    
    finally:
        await notification_manager.stop()


async def test_environment_setup():
    """Test environment setup"""
    print("🧪 Testing Environment Setup...")
    
    # Check required environment variables
    required_vars = [
        "SMTP_SERVER",
        "SMTP_USERNAME", 
        "SMTP_PASSWORD",
        "ALERT_EMAIL"
    ]
    
    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        print(f"❌ Missing environment variables: {missing_vars}")
        print("\n📋 Please set the following environment variables:")
        for var in missing_vars:
            print(f"   export {var}=\"your_value_here\"")
        return False
    
    print("✅ Environment setup test passed!")
    return True


async def main():
    """Main test function"""
    print("🚀 StillMe Email Notification Test Suite")
    print("=" * 50)
    
    # Test environment setup
    env_ok = await test_environment_setup()
    if not env_ok:
        print("\n❌ Environment setup failed. Please configure environment variables first.")
        return
    
    print("\n" + "=" * 50)
    
    # Test email notifier
    email_ok = await test_email_notifier()
    
    print("\n" + "=" * 50)
    
    # Test alert emails
    alert_ok = await test_alert_emails()
    
    print("\n" + "=" * 50)
    
    # Test notification manager
    manager_ok = await test_notification_manager()
    
    print("\n" + "=" * 50)
    print("📊 TEST RESULTS:")
    print(f"   Environment Setup: {'✅ PASS' if env_ok else '❌ FAIL'}")
    print(f"   Email Notifier: {'✅ PASS' if email_ok else '❌ FAIL'}")
    print(f"   Alert Emails: {'✅ PASS' if alert_ok else '❌ FAIL'}")
    print(f"   Notification Manager: {'✅ PASS' if manager_ok else '❌ FAIL'}")
    
    if all([env_ok, email_ok, alert_ok, manager_ok]):
        print("\n🎉 ALL TESTS PASSED! Email notification system is working correctly.")
    else:
        print("\n❌ Some tests failed. Please check the configuration and try again.")


if __name__ == "__main__":
    # Check if we're in the right directory
    if not Path("stillme_platform").exists():
        print("❌ Please run this script from the project root directory")
        sys.exit(1)
    
    # Run tests
    asyncio.run(main())
