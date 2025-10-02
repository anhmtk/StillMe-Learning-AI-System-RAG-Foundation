#!/usr/bin/env python3
"""
AI Router - Main Entry Point

This script provides a unified interface to all AI router testing and monitoring tools.

Usage:
    python scripts/router.py test                    # Run all tests
    python scripts/router.py debug "your prompt"     # Debug a prompt
    python scripts/router.py benchmark               # Run benchmark
    python scripts/router.py monitor                 # Start monitoring
    python scripts/router.py status                  # Show status
    python scripts/router.py config                  # Show configuration
    python scripts/router.py interactive             # Interactive mode
"""

import argparse
import os
import subprocess
import sys


class RouterCLI:
    def __init__(self):
        self.script_dir = os.path.dirname(os.path.abspath(__file__))
        self.available_commands = {
            'test': 'test_router.py',
            'debug': 'debug_router.py',
            'benchmark': 'benchmark_router.py',
            'monitor': 'monitor_router.py',
            'status': 'router_manager.py',
            'config': 'router_manager.py',
            'interactive': 'router_cli.py',
            'validate': 'validate_router.py',
            'calibrate': 'calibrate_router.py',
            'dashboard': 'router_dashboard.py',
            'tools': 'router_tools.py'
        }

    def run_command(self, command: str, args: list[str] = None):
        """Run a command with optional arguments"""
        if command not in self.available_commands:
            print(f"❌ Unknown command: {command}")
            print(f"Available commands: {', '.join(self.available_commands.keys())}")
            return False

        script_name = self.available_commands[command]
        script_path = os.path.join(self.script_dir, script_name)

        if not os.path.exists(script_path):
            print(f"❌ Script not found: {script_path}")
            return False

        # Prepare command
        cmd = [sys.executable, script_path]

        # Add command-specific arguments
        if command == 'test':
            cmd.append('--all')
        elif command == 'debug' and args:
            cmd.extend(['--prompt', args[0]])
        elif command == 'benchmark':
            cmd.append('--full')
        elif command == 'monitor':
            cmd.append('--live')
        elif command == 'status':
            cmd.append('--status')
        elif command == 'config':
            cmd.append('--config')
        elif command == 'interactive':
            cmd.append('--interactive')
        elif command == 'validate':
            cmd.append('--full')
        elif command == 'calibrate':
            cmd.append('--test-suite')
        elif command == 'dashboard':
            cmd.append('--live')
        elif command == 'tools':
            cmd.append('--test')

        # Add any additional arguments
        if args and command != 'debug':
            cmd.extend(args)

        try:
            print(f"🚀 Running: {' '.join(cmd)}")
            print("=" * 60)

            result = subprocess.run(cmd, cwd=os.path.dirname(self.script_dir))
            return result.returncode == 0
        except Exception as e:
            print(f"❌ Error running command: {e}")
            return False

    def show_help(self):
        """Show help information"""
        print("🔍 AI Router - Main Entry Point")
        print("=" * 60)
        print("Unified interface to all AI router testing and monitoring tools.")
        print()
        print("Usage:")
        print("  python scripts/router.py <command> [arguments]")
        print()
        print("Available Commands:")
        print("  test                    Run comprehensive test suite")
        print("  debug <prompt>          Debug routing for a specific prompt")
        print("  benchmark               Run performance benchmark")
        print("  monitor                 Start real-time monitoring")
        print("  status                  Show router status")
        print("  config                  Show router configuration")
        print("  interactive             Start interactive CLI")
        print("  validate                Run validation checks")
        print("  calibrate               Calibrate router settings")
        print("  dashboard               Start live dashboard")
        print("  tools                   Run router tools")
        print()
        print("Examples:")
        print("  python scripts/router.py test")
        print("  python scripts/router.py debug \"viết code Python\"")
        print("  python scripts/router.py benchmark")
        print("  python scripts/router.py monitor")
        print("  python scripts/router.py status")
        print("  python scripts/router.py interactive")
        print()
        print("For detailed help on a specific command:")
        print("  python scripts/router.py <command> --help")
        print()
        print("For more information, see scripts/README.md")

    def show_status(self):
        """Show quick status overview"""
        print("📊 AI Router Quick Status")
        print("=" * 40)

        # Check if stillme_core is available
        stillme_core_path = os.path.join(os.path.dirname(self.script_dir), 'stillme_core')
        if os.path.exists(stillme_core_path):
            print("✅ stillme_core: Available")
        else:
            print("❌ stillme_core: Not found")

        # Check if scripts are available
        missing_scripts = []
        for _command, script_name in self.available_commands.items():
            script_path = os.path.join(self.script_dir, script_name)
            if not os.path.exists(script_path):
                missing_scripts.append(script_name)

        if missing_scripts:
            print(f"⚠️  Missing scripts: {', '.join(missing_scripts)}")
        else:
            print("✅ All scripts: Available")

        # Check environment
        env_vars = [
            'COMPLEXITY_WEIGHT_LENGTH',
            'COMPLEXITY_WEIGHT_COMPLEX_INDICATORS',
            'COMPLEXITY_WEIGHT_ACADEMIC_TERMS',
            'COMPLEXITY_WEIGHT_ABSTRACT_CONCEPTS',
            'COMPLEXITY_WEIGHT_MULTI_PART',
            'COMPLEXITY_WEIGHT_CONDITIONAL',
            'COMPLEXITY_WEIGHT_DOMAIN_SPECIFIC',
            'COMPLEXITY_THRESHOLD_SIMPLE',
            'COMPLEXITY_THRESHOLD_MEDIUM'
        ]

        configured_vars = [var for var in env_vars if os.getenv(var)]
        print(f"⚙️  Environment: {len(configured_vars)}/{len(env_vars)} variables configured")

        if configured_vars:
            print("  Configured variables:")
            for var in configured_vars:
                value = os.getenv(var)
                print(f"    {var}: {value}")
        else:
            print("  Using default configuration")

        print()
        print("💡 Quick Commands:")
        print("  python scripts/router.py test        # Run tests")
        print("  python scripts/router.py status      # Detailed status")
        print("  python scripts/router.py interactive # Interactive mode")

def main():
    parser = argparse.ArgumentParser(
        description='AI Router - Main Entry Point',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/router.py test
  python scripts/router.py debug "viết code Python"
  python scripts/router.py benchmark
  python scripts/router.py monitor
  python scripts/router.py status
  python scripts/router.py interactive

For detailed help on a specific command:
  python scripts/router.py <command> --help

For more information, see scripts/README.md
        """
    )

    parser.add_argument('command', nargs='?', help='Command to run')
    parser.add_argument('args', nargs='*', help='Command arguments')
    parser.add_argument('--help-commands', action='store_true', help='Show available commands')

    args = parser.parse_args()

    cli = RouterCLI()

    if args.help_commands or not args.command:
        cli.show_help()
        return

    if args.command == 'help':
        cli.show_help()
        return

    if args.command == 'status':
        cli.show_status()
        return

    # Run the command
    success = cli.run_command(args.command, args.args)

    if not success:
        sys.exit(1)

if __name__ == "__main__":
    main()
