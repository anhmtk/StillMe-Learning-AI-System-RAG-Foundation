#!/usr/bin/env python3
"""
🕐 StillMe Learning Scheduler CLI
================================

CLI tool để quản lý learning scheduler và automation service.
Hỗ trợ start/stop/status scheduler, cấu hình cron jobs, và monitoring.

Usage:
    python -m cli.learning_scheduler start --cron "30 2 * * *" --tz Asia/Ho_Chi_Minh
    python -m cli.learning_scheduler stop
    python -m cli.learning_scheduler status
    python -m cli.learning_scheduler config --enable --cron "0 3 * * *"
    python -m cli.learning_scheduler test --dry-run

Author: StillMe AI Framework
Version: 2.0.0
"""

import argparse
import asyncio
import json
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Any

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from stillme_core.learning.scheduler import LearningScheduler, SchedulerConfig
from stillme_core.learning.automation_service import LearningAutomationService, AutomationServiceConfig
from stillme_core.learning.evolutionary_learning_system import EvolutionaryConfig

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class LearningSchedulerCLI:
    """CLI for Learning Scheduler Management"""
    
    def __init__(self):
        self.service: Optional[LearningAutomationService] = None
        self.scheduler: Optional[LearningScheduler] = None
    
    async def start(self, args):
        """Start automation service"""
        print("🚀 Starting StillMe Learning Automation Service...")
        print("=" * 50)
        
        try:
            # Create scheduler config
            scheduler_config = SchedulerConfig(
                enabled=True,
                cron_expression=args.cron or "30 2 * * *",
                timezone=getattr(args, 'timezone', None) or getattr(args, 'tz', None) or "Asia/Ho_Chi_Minh",
                jitter_seconds=args.jitter or 300,
                max_concurrent_sessions=args.max_concurrent or 1,
                skip_if_cpu_high=not args.no_cpu_check,
                cpu_threshold=args.cpu_threshold or 70.0,
                skip_if_memory_high=not args.no_memory_check,
                memory_threshold_mb=args.memory_threshold or 1024,
                skip_if_tokens_low=not args.no_token_check,
                min_tokens_required=args.min_tokens or 1000
            )
            
            # Create automation service config
            service_config = AutomationServiceConfig(
                enabled=True,
                scheduler_config=scheduler_config,
                learning_config=EvolutionaryConfig(),
                health_check_interval=args.health_interval or 60,
                log_level=args.log_level or "INFO",
                enable_metrics=not args.no_metrics
            )
            
            # Create and start service
            self.service = LearningAutomationService(service_config)
            
            if await self.service.start():
                print("✅ Learning Automation Service started successfully!")
                print(f"📅 Schedule: {scheduler_config.cron_expression} ({scheduler_config.timezone})")
                print(f"⏰ Next run: {self.service.scheduler.get_next_run_time()}")
                print(f"🔍 Health check interval: {service_config.health_check_interval}s")
                print(f"📊 Metrics enabled: {service_config.enable_metrics}")
                print()
                print("Press Ctrl+C to stop the service...")
                
                # Keep running until interrupted
                try:
                    await self.service.shutdown_event.wait()
                except KeyboardInterrupt:
                    print("\n⏹️ Received interrupt signal...")
                finally:
                    await self.service.shutdown()
                    print("✅ Service stopped gracefully")
            else:
                print("❌ Failed to start Learning Automation Service")
                return False
                
        except Exception as e:
            logger.error(f"Failed to start service: {e}")
            print(f"❌ Error: {e}")
            return False
    
    async def stop(self, args):
        """Stop automation service"""
        print("⏹️ Stopping Learning Automation Service...")
        print("=" * 40)
        
        try:
            # Try to find running service
            service = LearningAutomationService()
            if await service.stop():
                print("✅ Service stopped successfully")
            else:
                print("⚠️ Service was not running or failed to stop")
                
        except Exception as e:
            logger.error(f"Failed to stop service: {e}")
            print(f"❌ Error: {e}")
    
    async def status(self, args):
        """Show scheduler status"""
        print("📊 StillMe Learning Scheduler Status")
        print("=" * 40)
        
        try:
            # Create scheduler to get status
            config = SchedulerConfig()
            scheduler = LearningScheduler(config)
            await scheduler.initialize()
            
            status = scheduler.get_status()
            
            print(f"Status: {'🟢 Running' if status['running'] else '🔴 Stopped'}")
            print(f"Enabled: {'✅ Yes' if status['enabled'] else '❌ No'}")
            print(f"Timezone: {status['timezone']}")
            print(f"Cron Expression: {status['cron_expression']}")
            print(f"APScheduler Available: {'✅ Yes' if status['apscheduler_available'] else '❌ No'}")
            print()
            
            if status['scheduled_jobs']:
                print("📅 Scheduled Jobs:")
                for job_id, job in status['scheduled_jobs'].items():
                    print(f"  • {job['name']}")
                    print(f"    Trigger: {job['trigger']}")
                    print(f"    Next Run: {job['next_run'] or 'Not scheduled'}")
                    print(f"    Last Run: {job['last_run'] or 'Never'}")
                    print(f"    Status: {job['status']}")
                    print()
            else:
                print("📅 No scheduled jobs")
            
            if status['statistics']:
                stats = status['statistics']
                print("📈 Statistics:")
                print(f"  Total Jobs: {stats['total_jobs']}")
                print(f"  Successful: {stats['successful_jobs']}")
                print(f"  Failed: {stats['failed_jobs']}")
                print(f"  Skipped: {stats['skipped_jobs']}")
                print(f"  Last Run: {stats['last_run'] or 'Never'}")
                print(f"  Next Run: {stats['next_run'] or 'Not scheduled'}")
            
        except Exception as e:
            logger.error(f"Failed to get status: {e}")
            print(f"❌ Error: {e}")
    
    async def config(self, args):
        """Configure scheduler settings"""
        print("⚙️ Configuring Learning Scheduler...")
        print("=" * 40)
        
        try:
            # Load current config
            config_file = Path("config/learning.toml")
            if config_file.exists():
                import toml
                config_data = toml.load(config_file)
            else:
                config_data = {}
            
            # Update scheduler config
            if not 'scheduler' in config_data:
                config_data['scheduler'] = {}
            
            scheduler_config = config_data['scheduler']
            
            if args.enable:
                scheduler_config['enabled'] = True
                print("✅ Scheduler enabled")
            
            if args.disable:
                scheduler_config['enabled'] = False
                print("❌ Scheduler disabled")
            
            if args.cron:
                scheduler_config['cron_expression'] = args.cron
                print(f"📅 Cron expression set to: {args.cron}")
            
            if args.timezone:
                scheduler_config['timezone'] = args.timezone
                print(f"🌍 Timezone set to: {args.timezone}")
            
            if args.jitter:
                scheduler_config['jitter_seconds'] = args.jitter
                print(f"⏱️ Jitter set to: {args.jitter} seconds")
            
            if args.cpu_threshold:
                scheduler_config['cpu_threshold'] = args.cpu_threshold
                print(f"💻 CPU threshold set to: {args.cpu_threshold}%")
            
            if args.memory_threshold:
                scheduler_config['memory_threshold_mb'] = args.memory_threshold
                print(f"🧠 Memory threshold set to: {args.memory_threshold}MB")
            
            # Save config
            import toml
            with open(config_file, 'w', encoding='utf-8') as f:
                toml.dump(config_data, f)
            
            print(f"💾 Configuration saved to {config_file}")
            
        except Exception as e:
            logger.error(f"Failed to configure scheduler: {e}")
            print(f"❌ Error: {e}")
    
    async def test(self, args):
        """Test scheduler configuration"""
        print("🧪 Testing Scheduler Configuration...")
        print("=" * 40)
        
        try:
            # Create test config
            config = SchedulerConfig(
                enabled=True,
                cron_expression=args.cron or "30 2 * * *",
                timezone=args.timezone or "Asia/Ho_Chi_Minh",
                jitter_seconds=args.jitter or 300
            )
            
            # Create scheduler
            scheduler = LearningScheduler(config)
            await scheduler.initialize()
            
            print("✅ Scheduler initialized successfully")
            print(f"📅 Cron Expression: {config.cron_expression}")
            print(f"🌍 Timezone: {config.timezone}")
            print(f"⏱️ Jitter: {config.jitter_seconds} seconds")
            
            if not args.dry_run:
                # Schedule test job
                async def test_training():
                    print("🧪 Test training session executed!")
                    return {"status": "success", "test": True}
                
                success = await scheduler.schedule_daily_training(test_training)
                
                if success:
                    print("✅ Test job scheduled successfully")
                    next_run = scheduler.get_next_run_time()
                    print(f"⏰ Next run: {next_run}")
                else:
                    print("❌ Failed to schedule test job")
            else:
                print("🔍 Dry run mode - no actual scheduling performed")
            
        except Exception as e:
            logger.error(f"Test failed: {e}")
            print(f"❌ Error: {e}")
    
    async def logs(self, args):
        """Show recent logs"""
        print("📋 Recent Learning Scheduler Logs")
        print("=" * 40)
        
        try:
            # This would read from log files
            # For now, just show a placeholder
            print("📝 Log functionality not yet implemented")
            print("💡 Logs are currently output to console")
            print("🔧 Future: Will read from logs/learning_scheduler.log")
            
        except Exception as e:
            logger.error(f"Failed to show logs: {e}")
            print(f"❌ Error: {e}")

def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description="StillMe Learning Scheduler CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s start --cron "30 2 * * *" --tz Asia/Ho_Chi_Minh
  %(prog)s stop
  %(prog)s status
  %(prog)s config --enable --cron "0 3 * * *"
  %(prog)s test --dry-run
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Start command
    start_parser = subparsers.add_parser('start', help='Start automation service')
    start_parser.add_argument('--cron', help='Cron expression (default: "30 2 * * *")')
    start_parser.add_argument('--tz', '--timezone', help='Timezone (default: Asia/Ho_Chi_Minh)')
    start_parser.add_argument('--jitter', type=int, help='Jitter in seconds (default: 300)')
    start_parser.add_argument('--max-concurrent', type=int, help='Max concurrent sessions (default: 1)')
    start_parser.add_argument('--no-cpu-check', action='store_true', help='Disable CPU check')
    start_parser.add_argument('--cpu-threshold', type=float, help='CPU threshold percentage (default: 70)')
    start_parser.add_argument('--no-memory-check', action='store_true', help='Disable memory check')
    start_parser.add_argument('--memory-threshold', type=int, help='Memory threshold in MB (default: 1024)')
    start_parser.add_argument('--no-token-check', action='store_true', help='Disable token check')
    start_parser.add_argument('--min-tokens', type=int, help='Minimum tokens required (default: 1000)')
    start_parser.add_argument('--health-interval', type=int, help='Health check interval in seconds (default: 60)')
    start_parser.add_argument('--log-level', choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'], help='Log level')
    start_parser.add_argument('--no-metrics', action='store_true', help='Disable metrics collection')
    
    # Stop command
    stop_parser = subparsers.add_parser('stop', help='Stop automation service')
    
    # Status command
    status_parser = subparsers.add_parser('status', help='Show scheduler status')
    
    # Config command
    config_parser = subparsers.add_parser('config', help='Configure scheduler settings')
    config_parser.add_argument('--enable', action='store_true', help='Enable scheduler')
    config_parser.add_argument('--disable', action='store_true', help='Disable scheduler')
    config_parser.add_argument('--cron', help='Set cron expression')
    config_parser.add_argument('--timezone', help='Set timezone')
    config_parser.add_argument('--jitter', type=int, help='Set jitter in seconds')
    config_parser.add_argument('--cpu-threshold', type=float, help='Set CPU threshold')
    config_parser.add_argument('--memory-threshold', type=int, help='Set memory threshold')
    
    # Test command
    test_parser = subparsers.add_parser('test', help='Test scheduler configuration')
    test_parser.add_argument('--cron', help='Test cron expression')
    test_parser.add_argument('--timezone', help='Test timezone')
    test_parser.add_argument('--jitter', type=int, help='Test jitter')
    test_parser.add_argument('--dry-run', action='store_true', help='Dry run mode')
    
    # Logs command
    logs_parser = subparsers.add_parser('logs', help='Show recent logs')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    # Create CLI instance and run command
    cli = LearningSchedulerCLI()
    
    try:
        if args.command == 'start':
            asyncio.run(cli.start(args))
        elif args.command == 'stop':
            asyncio.run(cli.stop(args))
        elif args.command == 'status':
            asyncio.run(cli.status(args))
        elif args.command == 'config':
            asyncio.run(cli.config(args))
        elif args.command == 'test':
            asyncio.run(cli.test(args))
        elif args.command == 'logs':
            asyncio.run(cli.logs(args))
    except KeyboardInterrupt:
        print("\n⏹️ Operation cancelled by user")
    except Exception as e:
        logger.error(f"CLI error: {e}")
        print(f"❌ Error: {e}")

if __name__ == '__main__':
    main()
