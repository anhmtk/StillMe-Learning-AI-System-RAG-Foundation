#!/usr/bin/env python3
"""
StillMe Learning Rollback CLI
============================

Command-line interface for rolling back learning updates.

Usage:
    python cli/rollback_learning.py --id <version_id>
    python cli/rollback_learning.py --list
    python cli/rollback_learning.py --history

Author: StillMe AI Framework Team
Version: 1.0.0
"""

import argparse
import asyncio
import sys
from pathlib import Path
from typing import Optional

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from stillme_core.control.learning_rollback import LearningRollback, LearningUpdateType

async def main():
    """Main CLI function"""
    parser = argparse.ArgumentParser(
        description="StillMe Learning Rollback CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python cli/rollback_learning.py --id v20250127_143022_abc12345
  python cli/rollback_learning.py --list
  python cli/rollback_learning.py --history --limit 10
  python cli/rollback_learning.py --id v20250127_143022_abc12345 --force
        """
    )
    
    # Main commands
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--id", 
        type=str, 
        help="Version ID to rollback to"
    )
    group.add_argument(
        "--list", 
        action="store_true", 
        help="List available rollback candidates"
    )
    group.add_argument(
        "--history", 
        action="store_true", 
        help="Show rollback history"
    )
    
    # Optional arguments
    parser.add_argument(
        "--force", 
        action="store_true", 
        help="Force rollback even if dependencies exist"
    )
    parser.add_argument(
        "--limit", 
        type=int, 
        default=20, 
        help="Limit number of results (default: 20)"
    )
    parser.add_argument(
        "--verbose", 
        action="store_true", 
        help="Enable verbose output"
    )
    
    args = parser.parse_args()
    
    # Initialize rollback system
    rollback_system = LearningRollback()
    
    try:
        if args.list:
            await list_rollback_candidates(rollback_system, args.limit, args.verbose)
        elif args.history:
            await show_rollback_history(rollback_system, args.limit, args.verbose)
        elif args.id:
            await rollback_to_version(rollback_system, args.id, args.force, args.verbose)
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

async def list_rollback_candidates(rollback_system: LearningRollback, limit: int, verbose: bool):
    """List available rollback candidates"""
    print("📋 Available Rollback Candidates:")
    print("=" * 50)
    
    candidates = await rollback_system.get_rollback_candidates()
    
    for i, candidate in enumerate(candidates[:limit]):
        status = "✅" if candidate["can_rollback"] else "❌"
        current = " (CURRENT)" if candidate["version_id"] == rollback_system.get_current_version() else ""
        
        print(f"{i+1:2d}. {status} {candidate['version_id']}{current}")
        print(f"    📅 {candidate['timestamp']}")
        print(f"    📝 {candidate['description']}")
        print(f"    🏷️  {candidate['update_type']}")
        
        if verbose and candidate["dependencies"]:
            print(f"    🔗 Dependencies: {', '.join(candidate['dependencies'])}")
        
        print()

async def show_rollback_history(rollback_system: LearningRollback, limit: int, verbose: bool):
    """Show rollback history"""
    print("📜 Rollback History:")
    print("=" * 50)
    
    history = await rollback_system.get_version_history(limit)
    
    for i, entry in enumerate(history):
        current = " (CURRENT)" if entry["is_current"] else ""
        
        print(f"{i+1:2d}. {entry['version_id']}{current}")
        print(f"    📅 {entry['timestamp']}")
        print(f"    📝 {entry['description']}")
        print(f"    🏷️  {entry['update_type']}")
        print(f"    🔐 {entry['state_hash']}")
        
        if verbose:
            print(f"    🔗 Dependencies: {entry.get('dependencies', [])}")
        
        print()

async def rollback_to_version(
    rollback_system: LearningRollback, 
    version_id: str, 
    force: bool, 
    verbose: bool
):
    """Rollback to specific version"""
    print(f"⏪ Rolling back to version: {version_id}")
    print("=" * 50)
    
    if force:
        print("⚠️  Force mode enabled - ignoring dependency checks")
    
    # Perform rollback
    result = await rollback_system.rollback_to_version(version_id, force)
    
    # Display results
    if result.status == "success":
        print(f"✅ Rollback completed successfully!")
        print(f"   📊 Changes reverted: {len(result.changes_reverted)}")
        print(f"   ⏱️  Duration: {result.rollback_duration:.2f}s")
        
        if verbose and result.changes_reverted:
            print("   📝 Reverted changes:")
            for change in result.changes_reverted:
                print(f"      - {change}")
    
    elif result.status == "not_needed":
        print(f"ℹ️  Rollback not needed - already at version {version_id}")
    
    else:
        print(f"❌ Rollback failed!")
        print(f"   📊 Status: {result.status}")
        print(f"   ⏱️  Duration: {result.rollback_duration:.2f}s")
        
        if result.errors:
            print("   🚨 Errors:")
            for error in result.errors:
                print(f"      - {error}")

if __name__ == "__main__":
    asyncio.run(main())
