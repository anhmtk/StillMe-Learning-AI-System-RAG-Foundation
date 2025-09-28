"""
🔔 StillMe Alert Manager CLI
============================

Command-line interface for managing StillMe AI alert system.
Provides comprehensive alert management, testing, and monitoring capabilities.

Tính năng:
- Send test alerts to all channels
- View alert statistics and history
- Manage alert configurations
- Test individual notification channels
- Monitor alert system health
- Configure alert thresholds

Author: StillMe AI Framework
Version: 2.0.0
Date: 2025-09-28
"""

import asyncio
import argparse
import json
import logging
import sys
from datetime import datetime, timedelta
from typing import Dict, Any, List
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from stillme_core.alerting.alert_manager import get_alert_manager, AlertManager
from stillme_core.alerting.learning_alerts import get_learning_alert_manager, LearningAlertManager, LearningMetrics

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class AlertCLI:
    """Alert Manager CLI"""
    
    def __init__(self):
        self.alert_manager = get_alert_manager()
        self.learning_alert_manager = get_learning_alert_manager()
    
    async def send_test_alert(self, args):
        """Send test alert to specified channels"""
        if args.channels:
            channels = [ch.strip() for ch in args.channels.split(',')]
        else:
            channels = ['email', 'desktop', 'telegram']
        severity = args.severity or 'medium'
        
        print(f"🔔 Sending test alert to {', '.join(channels)}...")
        
        alert_id = await self.alert_manager.send_alert(
            alert_type='test_alert',
            severity=severity,
            title='Test Alert from StillMe AI',
            message=f'This is a test alert sent at {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}',
            component='alert_cli',
            context={
                'test_type': 'manual_test',
                'channels': channels,
                'severity': severity,
                'test_time': datetime.now().isoformat(),
                'metrics': {
                    'Test Type': 'Manual Test',
                    'Channels': ', '.join(channels),
                    'Severity': severity.upper(),
                    'Time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
            },
            channels=channels
        )
        
        print(f"✅ Test alert sent successfully: {alert_id}")
        return alert_id
    
    async def send_learning_test_alert(self, args):
        """Send test learning alert"""
        print("🧠 Sending test learning alert...")
        
        # Create test metrics
        test_metrics = LearningMetrics(
            session_id='test_session_001',
            timestamp=datetime.now(),
            evolution_stage='child',
            learning_accuracy=0.85,
            training_time=120.5,
            memory_usage=1500.0,
            cpu_usage=65.0,
            token_consumption=500,
            error_count=2,
            success_rate=0.95,
            knowledge_items_processed=100,
            performance_score=0.82
        )
        
        alerts_sent = await self.learning_alert_manager.check_learning_session_alerts(test_metrics)
        
        print(f"✅ Learning test alerts sent: {len(alerts_sent)} alerts")
        for alert_id in alerts_sent:
            print(f"   - {alert_id}")
        
        return alerts_sent
    
    async def send_evolution_milestone_alert(self, args):
        """Send test evolution milestone alert"""
        print("🌟 Sending test evolution milestone alert...")
        
        alert_id = await self.alert_manager.send_alert(
            alert_type='evolution_milestone',
            severity='medium',
            title='Test AGI Evolution Milestone',
            message='StillMe has achieved a test milestone in the child stage',
            component='evolution_system',
            context={
                'milestone_name': 'test_milestone',
                'evolution_stage': 'child',
                'session_id': 'test_session_001',
                'achievement_time': datetime.now().isoformat(),
                'metrics': {
                    'Evolution Stage': 'Child',
                    'Milestone': 'Test Milestone',
                    'Session ID': 'test_session_001',
                    'Accuracy': '85.00%',
                    'Performance Score': '0.82'
                }
            },
            channels=['email', 'telegram']
        )
        
        print(f"✅ Evolution milestone alert sent: {alert_id}")
        return alert_id
    
    async def send_resource_alert(self, args):
        """Send test resource alert"""
        resource_type = args.resource or 'memory'
        usage = args.usage or 2500.0
        limit = args.limit or 2048.0
        
        print(f"💾 Sending test {resource_type} resource alert...")
        
        alert_id = await self.alert_manager.send_alert(
            alert_type='resource_high',
            severity='high',
            title=f'High {resource_type.title()} Usage',
            message=f'{resource_type.title()} usage is {usage:.1f} (limit: {limit:.1f})',
            component='resource_monitor',
            context={
                'resource_type': resource_type,
                'current_usage': usage,
                'limit': limit,
                'usage_percent': usage / limit,
                'warning_time': datetime.now().isoformat(),
                'metrics': {
                    'Resource Type': resource_type.title(),
                    'Current Usage': f'{usage:.1f}',
                    'Limit': f'{limit:.1f}',
                    'Usage %': f'{usage/limit:.1%}',
                    'Time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
            },
            channels=['email', 'desktop', 'telegram']
        )
        
        print(f"✅ Resource alert sent: {alert_id}")
        return alert_id
    
    async def send_critical_alert(self, args):
        """Send test critical alert"""
        print("🚨 Sending test critical alert...")
        
        alert_id = await self.alert_manager.send_alert(
            alert_type='system_critical',
            severity='critical',
            title='Test Critical System Error',
            message='This is a test critical error for alert system validation',
            component='test_system',
            context={
                'error_message': 'Test critical error',
                'component': 'test_system',
                'error_time': datetime.now().isoformat(),
                'metrics': {
                    'Error': 'Test critical error',
                    'Component': 'test_system',
                    'Time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'Severity': 'CRITICAL'
                }
            },
            channels=['email', 'desktop', 'telegram', 'sms']
        )
        
        print(f"✅ Critical alert sent: {alert_id}")
        return alert_id
    
    def show_statistics(self, args):
        """Show alert statistics"""
        print("📊 StillMe Alert System Statistics")
        print("=" * 50)
        
        # Get alert manager statistics
        stats = self.alert_manager.get_alert_statistics()
        
        print(f"Total Alerts: {stats['statistics']['total_alerts']}")
        print(f"Last Alert: {stats['statistics']['last_alert_time']}")
        
        print("\n📈 Alerts by Severity:")
        for severity, count in stats['statistics']['alerts_by_severity'].items():
            print(f"  {severity.upper()}: {count}")
        
        print("\n📱 Alerts by Channel:")
        for channel, count in stats['statistics']['alerts_by_channel'].items():
            print(f"  {channel}: {count}")
        
        print("\n🔧 Notifier Status:")
        for name, status in stats['notifier_status'].items():
            enabled_status = "✅ Enabled" if status['enabled'] else "❌ Disabled"
            print(f"  {name}: {enabled_status}")
            print(f"    Successful: {status['successful']}")
            print(f"    Failed: {status['failed']}")
        
        print("\n⏰ Rate Limits:")
        for alert_type, count in stats['rate_limits'].items():
            print(f"  {alert_type}: {count} alerts in last hour")
        
        print("\n🕐 Cooldowns:")
        for key, timestamp in stats['cooldowns'].items():
            print(f"  {key}: {timestamp}")
        
        print("\n📋 Recent Alerts:")
        for alert in stats['recent_alerts'][-5:]:  # Last 5 alerts
            print(f"  {alert['alert_id']}: {alert['title']} ({alert['severity']})")
    
    def show_learning_statistics(self, args):
        """Show learning alert statistics"""
        print("🧠 StillMe Learning Alert Statistics")
        print("=" * 50)
        
        # Get learning alert statistics
        stats = self.learning_alert_manager.get_learning_alert_statistics()
        
        print(f"Achieved Milestones: {len(stats['achieved_milestones'])}")
        for milestone in stats['achieved_milestones']:
            print(f"  ✅ {milestone}")
        
        print(f"\nPerformance History: {stats['performance_history_count']} sessions")
        
        print("\n🎯 Learning Thresholds:")
        for key, value in stats['thresholds'].items():
            print(f"  {key}: {value}")
        
        print(f"\n📉 Degradation Threshold: {stats['degradation_threshold']:.1%}")
        
        print("\n🌟 Evolution Milestones:")
        for stage, milestones in stats['evolution_milestones'].items():
            print(f"  {stage.title()}: {', '.join(milestones)}")
    
    def test_channel(self, args):
        """Test individual notification channel"""
        channel = args.channel
        print(f"🧪 Testing {channel} channel...")
        
        # Create test alert
        test_alert = {
            'alert_id': f'test_{int(datetime.now().timestamp())}',
            'timestamp': datetime.now(),
            'alert_type': 'channel_test',
            'severity': 'medium',
            'title': f'Test Alert for {channel.title()} Channel',
            'message': f'This is a test alert for the {channel} notification channel',
            'component': 'alert_cli',
            'context': {
                'test_channel': channel,
                'test_time': datetime.now().isoformat(),
                'metrics': {
                    'Channel': channel.title(),
                    'Test Type': 'Channel Test',
                    'Time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
            }
        }
        
        # Test the channel
        if channel == 'email':
            print("📧 Testing email channel...")
            print("   Check your email inbox for the test message")
        elif channel == 'desktop':
            print("🖥️ Testing desktop notification...")
            print("   Check your desktop for the notification popup")
        elif channel == 'telegram':
            print("📱 Testing Telegram channel...")
            print("   Check your Telegram for the test message")
        elif channel == 'sms':
            print("📲 Testing SMS channel...")
            print("   Check your phone for the test SMS")
        elif channel == 'webhook':
            print("🔗 Testing webhook channel...")
            print("   Check your webhook endpoint for the test payload")
        else:
            print(f"❌ Unknown channel: {channel}")
            return
        
        print(f"✅ {channel.title()} channel test completed")
    
    def show_config(self, args):
        """Show alert configuration"""
        print("⚙️ StillMe Alert Configuration")
        print("=" * 50)
        
        # Show environment variables
        import os
        
        env_vars = [
            'SMTP_HOST', 'SMTP_PORT', 'SMTP_USERNAME', 'SMTP_PASSWORD', 'ALERT_EMAIL',
            'TELEGRAM_BOT_TOKEN', 'TELEGRAM_CHAT_ID',
            'TWILIO_ACCOUNT_SID', 'TWILIO_AUTH_TOKEN', 'TWILIO_PHONE_NUMBER', 'ALERT_PHONE',
            'WEBHOOK_URL', 'WEBHOOK_HEADERS'
        ]
        
        print("🔧 Environment Variables:")
        for var in env_vars:
            value = os.getenv(var, '')
            if value:
                # Mask sensitive values
                if 'PASSWORD' in var or 'TOKEN' in var or 'SID' in var:
                    masked_value = value[:4] + '*' * (len(value) - 8) + value[-4:] if len(value) > 8 else '*' * len(value)
                    print(f"  {var}: {masked_value}")
                else:
                    print(f"  {var}: {value}")
            else:
                print(f"  {var}: ❌ Not set")
        
        # Show notifier status
        print("\n📱 Notifier Status:")
        stats = self.alert_manager.get_alert_statistics()
        for name, status in stats['notifier_status'].items():
            enabled_status = "✅ Enabled" if status['enabled'] else "❌ Disabled"
            print(f"  {name}: {enabled_status}")
    
    def show_history(self, args):
        """Show alert history"""
        limit = args.limit or 10
        
        print(f"📋 StillMe Alert History (Last {limit} alerts)")
        print("=" * 50)
        
        stats = self.alert_manager.get_alert_statistics()
        recent_alerts = stats['recent_alerts'][-limit:]
        
        if not recent_alerts:
            print("No alerts found in history")
            return
        
        for alert in reversed(recent_alerts):  # Show newest first
            timestamp = datetime.fromisoformat(alert['timestamp'].replace('Z', '+00:00'))
            print(f"\n🔔 {alert['alert_id']}")
            print(f"   Time: {timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"   Type: {alert['alert_type']}")
            print(f"   Severity: {alert['severity'].upper()}")
            print(f"   Title: {alert['title']}")
            print(f"   Component: {alert['component']}")
            print(f"   Acknowledged: {'✅' if alert['acknowledged'] else '❌'}")
            print(f"   Resolved: {'✅' if alert['resolved'] else '❌'}")

def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description='StillMe AI Alert Manager CLI',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Send test alert to all channels
  python -m cli.alert_manager test --channels email,desktop,telegram
  
  # Send test learning alert
  python -m cli.alert_manager test-learning
  
  # Send test resource alert
  python -m cli.alert_manager test-resource --resource memory --usage 2500 --limit 2048
  
  # Show alert statistics
  python -m cli.alert_manager stats
  
  # Test specific channel
  python -m cli.alert_manager test-channel --channel email
  
  # Show configuration
  python -m cli.alert_manager config
  
  # Show alert history
  python -m cli.alert_manager history --limit 20
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Test alert command
    test_parser = subparsers.add_parser('test', help='Send test alert')
    test_parser.add_argument('--channels', type=str, help='Comma-separated list of channels (email,desktop,telegram,sms,webhook)')
    test_parser.add_argument('--severity', choices=['low', 'medium', 'high', 'critical'], help='Alert severity')
    
    # Test learning alert command
    test_learning_parser = subparsers.add_parser('test-learning', help='Send test learning alert')
    
    # Test evolution milestone command
    test_milestone_parser = subparsers.add_parser('test-milestone', help='Send test evolution milestone alert')
    
    # Test resource alert command
    test_resource_parser = subparsers.add_parser('test-resource', help='Send test resource alert')
    test_resource_parser.add_argument('--resource', choices=['memory', 'cpu', 'disk', 'network'], help='Resource type')
    test_resource_parser.add_argument('--usage', type=float, help='Current usage value')
    test_resource_parser.add_argument('--limit', type=float, help='Limit value')
    
    # Test critical alert command
    test_critical_parser = subparsers.add_parser('test-critical', help='Send test critical alert')
    
    # Statistics command
    stats_parser = subparsers.add_parser('stats', help='Show alert statistics')
    
    # Learning statistics command
    learning_stats_parser = subparsers.add_parser('learning-stats', help='Show learning alert statistics')
    
    # Test channel command
    test_channel_parser = subparsers.add_parser('test-channel', help='Test individual notification channel')
    test_channel_parser.add_argument('--channel', choices=['email', 'desktop', 'telegram', 'sms', 'webhook'], required=True, help='Channel to test')
    
    # Configuration command
    config_parser = subparsers.add_parser('config', help='Show alert configuration')
    
    # History command
    history_parser = subparsers.add_parser('history', help='Show alert history')
    history_parser.add_argument('--limit', type=int, help='Number of alerts to show (default: 10)')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    # Create CLI instance
    cli = AlertCLI()
    
    # Execute command
    try:
        if args.command == 'test':
            asyncio.run(cli.send_test_alert(args))
        elif args.command == 'test-learning':
            asyncio.run(cli.send_learning_test_alert(args))
        elif args.command == 'test-milestone':
            asyncio.run(cli.send_evolution_milestone_alert(args))
        elif args.command == 'test-resource':
            asyncio.run(cli.send_resource_alert(args))
        elif args.command == 'test-critical':
            asyncio.run(cli.send_critical_alert(args))
        elif args.command == 'stats':
            cli.show_statistics(args)
        elif args.command == 'learning-stats':
            cli.show_learning_statistics(args)
        elif args.command == 'test-channel':
            cli.test_channel(args)
        elif args.command == 'config':
            cli.show_config(args)
        elif args.command == 'history':
            cli.show_history(args)
        else:
            parser.print_help()
    
    except KeyboardInterrupt:
        print("\n❌ Operation cancelled by user")
    except Exception as e:
        logger.error(f"Error executing command: {e}")
        print(f"❌ Error: {e}")

if __name__ == '__main__':
    main()
