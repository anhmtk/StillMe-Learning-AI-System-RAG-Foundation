#!/usr/bin/env python3
"""
StillMe Learning Manager CLI
============================

Command-line interface for managing learning systems and resolving conflicts.

Usage:
    python cli/learning_manager.py --status
    python cli/learning_manager.py --switch-mode new
    python cli/learning_manager.py --migrate --from old --to new
    python cli/learning_manager.py --validate
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Dict, Any

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from stillme_core.learning.unified_learning_manager import (
    get_unified_learning_manager,
    LearningSystemMode
)


def print_status(manager) -> None:
    """Print current learning system status"""
    print("🔍 StillMe Learning Systems Status")
    print("=" * 50)
    
    stats = manager.get_stats()
    
    print(f"Mode: {stats['mode']}")
    print(f"Systems:")
    
    for system_name, system_stats in stats['systems'].items():
        print(f"  {system_name}:")
        if 'error' in system_stats:
            print(f"    ❌ Error: {system_stats['error']}")
        else:
            print(f"    ✅ Active")
            if 'status' in system_stats:
                print(f"    Status: {system_stats['status']}")
    
    print()


def print_recommendations(manager, context: Dict[str, Any]) -> None:
    """Print learning recommendations"""
    print("💡 Learning Recommendations")
    print("=" * 50)
    
    recommendations = manager.get_recommendations(context)
    
    if not recommendations:
        print("No recommendations available")
        return
    
    for i, rec in enumerate(recommendations, 1):
        print(f"{i}. {rec.get('title', 'Untitled')}")
        print(f"   Source: {rec.get('source', 'unknown')}")
        print(f"   Confidence: {rec.get('confidence', 0.0):.2f}")
        if 'description' in rec:
            print(f"   Description: {rec['description']}")
        print()


def switch_mode(manager, new_mode: str) -> bool:
    """Switch learning system mode"""
    try:
        mode_enum = LearningSystemMode(new_mode)
        success = manager.switch_mode(mode_enum)
        
        if success:
            print(f"✅ Switched to {new_mode} mode")
        else:
            print(f"❌ Failed to switch to {new_mode} mode")
        
        return success
    except ValueError:
        print(f"❌ Invalid mode: {new_mode}")
        print(f"Valid modes: {', '.join([mode.value for mode in LearningSystemMode])}")
        return False


def migrate_data(manager, from_system: str, to_system: str) -> bool:
    """Migrate data between systems"""
    print(f"🔄 Migrating data from {from_system} to {to_system}")
    
    try:
        result = manager.migrate_data(from_system, to_system)
        
        if 'error' in result:
            print(f"❌ Migration failed: {result['error']}")
            return False
        
        print(f"✅ Migration completed:")
        print(f"   Status: {result.get('status', 'unknown')}")
        print(f"   From: {result.get('from_system', 'unknown')}")
        print(f"   To: {result.get('to_system', 'unknown')}")
        
        return True
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        return False


def validate_systems(manager) -> bool:
    """Validate learning systems"""
    print("🔍 Validating Learning Systems")
    print("=" * 50)
    
    stats = manager.get_stats()
    all_valid = True
    
    for system_name, system_stats in stats['systems'].items():
        print(f"{system_name}: ", end="")
        
        if 'error' in system_stats:
            print(f"❌ Error: {system_stats['error']}")
            all_valid = False
        else:
            print("✅ Valid")
    
    print(f"\nOverall Status: {'✅ All systems valid' if all_valid else '❌ Some systems have errors'}")
    return all_valid


def test_experience_storage(manager) -> None:
    """Test experience storage functionality"""
    print("🧪 Testing Experience Storage")
    print("=" * 50)
    
    test_experience = {
        "type": "test",
        "category": "technical",
        "context": {"test": "data", "timestamp": "2025-09-27"},
        "action": "test_action",
        "outcome": {"success": True, "result": "test_passed"},
        "success": True,
        "lessons": ["Test lesson 1", "Test lesson 2"],
        "tags": ["test", "validation"],
        "confidence": 0.9,
        "impact_score": 0.8
    }
    
    try:
        results = manager.store_experience(test_experience)
        
        print("✅ Experience stored successfully:")
        for system, exp_id in results.items():
            print(f"   {system}: {exp_id}")
        
        # Test recommendations
        context = {"action": "test", "tags": ["test"]}
        recommendations = manager.get_recommendations(context)
        
        print(f"\n📊 Retrieved {len(recommendations)} recommendations")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")


def export_config(manager, output_file: str) -> None:
    """Export current configuration"""
    print(f"📤 Exporting configuration to {output_file}")
    
    config_data = {
        "mode": manager.config.mode.value,
        "auto_migrate": manager.config.auto_migrate,
        "backup_before_migrate": manager.config.backup_before_migrate,
        "batch_size": manager.config.batch_size,
        "conflict_resolution": manager.config.conflict_resolution,
        "parallel_mode": manager.config.parallel_mode,
        "sync_data": manager.config.sync_data
    }
    
    try:
        with open(output_file, 'w') as f:
            json.dump(config_data, f, indent=2)
        print(f"✅ Configuration exported to {output_file}")
    except Exception as e:
        print(f"❌ Export failed: {e}")


def main():
    """Main CLI interface"""
    parser = argparse.ArgumentParser(description="StillMe Learning Manager CLI")
    
    # Main commands
    parser.add_argument("--status", action="store_true", help="Show learning systems status")
    parser.add_argument("--switch-mode", choices=[mode.value for mode in LearningSystemMode], 
                       help="Switch learning system mode")
    parser.add_argument("--migrate", action="store_true", help="Migrate data between systems")
    parser.add_argument("--from", dest="from_system", choices=["old", "new"], 
                       help="Source system for migration")
    parser.add_argument("--to", dest="to_system", choices=["old", "new"], 
                       help="Target system for migration")
    parser.add_argument("--validate", action="store_true", help="Validate learning systems")
    parser.add_argument("--test", action="store_true", help="Test experience storage")
    parser.add_argument("--export-config", help="Export configuration to file")
    
    # Recommendation options
    parser.add_argument("--recommendations", action="store_true", help="Show recommendations")
    parser.add_argument("--context", help="Context for recommendations (JSON string)")
    
    args = parser.parse_args()
    
    try:
        # Initialize learning manager
        manager = get_unified_learning_manager()
        
        if args.status:
            print_status(manager)
        
        if args.switch_mode:
            switch_mode(manager, args.switch_mode)
        
        if args.migrate:
            if not args.from_system or not args.to_system:
                print("❌ Migration requires --from and --to arguments")
                sys.exit(1)
            migrate_data(manager, args.from_system, args.to_system)
        
        if args.validate:
            success = validate_systems(manager)
            sys.exit(0 if success else 1)
        
        if args.test:
            test_experience_storage(manager)
        
        if args.export_config:
            export_config(manager, args.export_config)
        
        if args.recommendations:
            context = {}
            if args.context:
                try:
                    context = json.loads(args.context)
                except json.JSONDecodeError as e:
                    print(f"❌ Invalid JSON context: {e}")
                    sys.exit(1)
            print_recommendations(manager, context)
        
        # If no specific command, show status
        if not any([args.status, args.switch_mode, args.migrate, args.validate, 
                   args.test, args.export_config, args.recommendations]):
            print_status(manager)
    
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
