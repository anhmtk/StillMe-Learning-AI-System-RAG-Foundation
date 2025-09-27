#!/usr/bin/env python3
"""
StillMe Kill Switch CLI
Command-line interface for kill switch operations.
"""

import argparse
import json
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from stillme_core.kill_switch import KillSwitchManager, KillSwitchAction

def format_status(status: dict) -> str:
    """Format status output."""
    state_emoji = {
        "disarmed": "✅",
        "armed": "⚠️",
        "fired": "🚨"
    }
    
    emoji = state_emoji.get(status["state"], "❓")
    
    output = f"{emoji} Kill Switch Status: {status['state'].upper()}\n"
    output += f"   Created: {status.get('created_at', 'Unknown')}\n"
    output += f"   Last Updated: {status.get('last_updated', 'Unknown')}\n"
    
    if status.get("armed_at"):
        output += f"   Armed At: {status['armed_at']}\n"
        output += f"   Armed By: {status.get('armed_by', 'Unknown')}\n"
        if status.get("reason"):
            output += f"   Reason: {status['reason']}\n"
    
    if status.get("fired_at"):
        output += f"   Fired At: {status['fired_at']}\n"
        output += f"   Fired By: {status.get('fired_by', 'Unknown')}\n"
        if status.get("reason"):
            output += f"   Reason: {status['reason']}\n"
    
    return output

def format_audit_log(entries: list) -> str:
    """Format audit log output."""
    if not entries:
        return "No audit log entries found."
    
    output = "📋 Recent Kill Switch Actions:\n"
    output += "=" * 60 + "\n"
    
    for entry in entries[-10:]:  # Show last 10 entries
        timestamp = entry.get("timestamp", "Unknown")
        level = entry.get("level", "INFO")
        data = entry.get("data", {})
        
        action = data.get("action", "unknown")
        actor = data.get("actor", "unknown")
        result = data.get("result", "unknown")
        reason = data.get("reason", "")
        
        result_emoji = "✅" if result == "SUCCESS" else "❌"
        
        output += f"{timestamp} | {result_emoji} {action.upper()} by {actor}\n"
        if reason:
            output += f"   Reason: {reason}\n"
        output += f"   Result: {result}\n"
        output += "-" * 40 + "\n"
    
    return output

def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="StillMe Kill Switch CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --status                    # Check current status
  %(prog)s --arm --actor admin         # Arm kill switch
  %(prog)s --fire --actor admin --reason "Emergency stop"  # Fire kill switch
  %(prog)s --disarm --actor admin      # Disarm kill switch
  %(prog)s --audit                     # Show audit log
  %(prog)s --audit --limit 20          # Show last 20 audit entries
        """
    )
    
    # Action arguments (mutually exclusive)
    action_group = parser.add_mutually_exclusive_group(required=True)
    action_group.add_argument("--status", action="store_true", 
                             help="Show kill switch status")
    action_group.add_argument("--arm", action="store_true", 
                             help="Arm the kill switch")
    action_group.add_argument("--fire", action="store_true", 
                             help="Fire the kill switch (emergency stop)")
    action_group.add_argument("--disarm", action="store_true", 
                             help="Disarm the kill switch")
    action_group.add_argument("--audit", action="store_true", 
                             help="Show audit log")
    
    # Common arguments
    parser.add_argument("--actor", default="cli-user", 
                       help="Actor performing the action (default: cli-user)")
    parser.add_argument("--reason", 
                       help="Reason for the action")
    parser.add_argument("--limit", type=int, default=100, 
                       help="Limit audit log entries (default: 100)")
    parser.add_argument("--json", action="store_true", 
                       help="Output in JSON format")
    parser.add_argument("--state-file", 
                       help="Custom state file path")
    parser.add_argument("--audit-file", 
                       help="Custom audit file path")
    
    args = parser.parse_args()
    
    try:
        # Initialize kill switch manager
        manager = KillSwitchManager(
            state_file=args.state_file or "logs/kill_switch_state.json",
            audit_file=args.audit_file or "logs/audit/kill_switch.log"
        )
        
        result = None
        
        if args.status:
            result = manager.status()
            
        elif args.arm:
            result = manager.arm(args.actor, args.reason)
            
        elif args.fire:
            # Confirmation for firing
            if not args.json:
                print("🚨 WARNING: This will immediately stop the system!")
                if not args.reason:
                    print("No reason provided. This action will be logged.")
                confirm = input("Type 'FIRE' to confirm: ")
                if confirm != "FIRE":
                    print("❌ Action cancelled.")
                    sys.exit(0)
            
            result = manager.fire(args.actor, args.reason)
            
        elif args.disarm:
            result = manager.disarm(args.actor, args.reason)
            
        elif args.audit:
            entries = manager.get_audit_log(args.limit)
            if args.json:
                result = {"audit_entries": entries}
            else:
                print(format_audit_log(entries))
                sys.exit(0)
        
        # Output result
        if args.json:
            print(json.dumps(result, indent=2))
        else:
            if args.status:
                print(format_status(result))
            else:
                # Action result
                success_emoji = "✅" if result.get("success") else "❌"
                print(f"{success_emoji} {result.get('message', 'Action completed')}")
                
                if result.get("success") and not args.status:
                    # Show updated status
                    print("\n" + format_status(manager.status()))
        
        # Exit with appropriate code
        if result and not result.get("success", True):
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n❌ Operation cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error: {e}")
        if args.json:
            print(json.dumps({"error": str(e)}, indent=2))
        sys.exit(1)

if __name__ == "__main__":
    main()
