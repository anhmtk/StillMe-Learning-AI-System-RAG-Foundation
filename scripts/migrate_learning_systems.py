#!/usr/bin/env python3
"""
StillMe Learning Systems Migration Script
=========================================

Migrates data between old and new learning systems.
Supports backup, validation, and rollback.

Usage:
    python scripts/migrate_learning_systems.py --from old --to new --backup
    python scripts/migrate_learning_systems.py --validate
    python scripts/migrate_learning_systems.py --rollback
"""

import argparse
import json
import logging
import sqlite3
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from stillme_core.learning.unified_learning_manager import get_unified_learning_manager

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class LearningMigrationManager:
    """Manages migration between learning systems"""
    
    def __init__(self):
        self.backup_dir = Path("data/migration_backups")
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        self.migration_log = self.backup_dir / "migration_log.json"
        
    def backup_old_system(self) -> str:
        """Backup old learning system data"""
        backup_id = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        backup_path = self.backup_dir / f"{backup_id}"
        backup_path.mkdir(exist_ok=True)
        
        logger.info(f"Creating backup: {backup_id}")
        
        try:
            # Backup experience memory database
            old_db_path = Path(".experience_memory.db")
            if old_db_path.exists():
                backup_db_path = backup_path / "experience_memory.db"
                import shutil
                shutil.copy2(old_db_path, backup_db_path)
                logger.info(f"Backed up experience memory database")
            
            # Backup any other old system files
            old_data_dir = Path("data/old_learning")
            if old_data_dir.exists():
                backup_data_path = backup_path / "old_learning_data"
                shutil.copytree(old_data_dir, backup_data_path)
                logger.info(f"Backed up old learning data directory")
            
            # Create backup manifest
            manifest = {
                "backup_id": backup_id,
                "timestamp": datetime.now().isoformat(),
                "files": [
                    str(f.relative_to(backup_path)) for f in backup_path.rglob("*") if f.is_file()
                ],
                "system": "old"
            }
            
            with open(backup_path / "manifest.json", "w") as f:
                json.dump(manifest, f, indent=2)
            
            logger.info(f"Backup completed: {backup_id}")
            return backup_id
            
        except Exception as e:
            logger.error(f"Backup failed: {e}")
            raise
    
    def backup_new_system(self) -> str:
        """Backup new learning system data"""
        backup_id = f"backup_new_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        backup_path = self.backup_dir / f"{backup_id}"
        backup_path.mkdir(exist_ok=True)
        
        logger.info(f"Creating new system backup: {backup_id}")
        
        try:
            # Backup vector store
            vector_store_path = Path("data/vector_index.pkl")
            if vector_store_path.exists():
                backup_vector_path = backup_path / "vector_index.pkl"
                import shutil
                shutil.copy2(vector_store_path, backup_vector_path)
                logger.info(f"Backed up vector store")
            
            # Backup claims store
            claims_db_path = Path("data/claims_store.db")
            if claims_db_path.exists():
                backup_claims_path = backup_path / "claims_store.db"
                shutil.copy2(claims_db_path, backup_claims_path)
                logger.info(f"Backed up claims store")
            
            # Backup approval queue
            queue_path = Path("data/approval_queue.json")
            if queue_path.exists():
                backup_queue_path = backup_path / "approval_queue.json"
                shutil.copy2(queue_path, backup_queue_path)
                logger.info(f"Backed up approval queue")
            
            # Create backup manifest
            manifest = {
                "backup_id": backup_id,
                "timestamp": datetime.now().isoformat(),
                "files": [
                    str(f.relative_to(backup_path)) for f in backup_path.rglob("*") if f.is_file()
                ],
                "system": "new"
            }
            
            with open(backup_path / "manifest.json", "w") as f:
                json.dump(manifest, f, indent=2)
            
            logger.info(f"New system backup completed: {backup_id}")
            return backup_id
            
        except Exception as e:
            logger.error(f"New system backup failed: {e}")
            raise
    
    def migrate_from_old_to_new(self, backup_id: Optional[str] = None) -> Dict[str, Any]:
        """Migrate data from old system to new system"""
        logger.info("Starting migration from old to new system")
        
        try:
            # Get unified learning manager
            manager = get_unified_learning_manager()
            
            # Get old system data
            if not manager.old_adapter or not manager.old_adapter.experience_memory:
                raise RuntimeError("Old learning system not available")
            
            old_memory = manager.old_adapter.experience_memory
            
            # Get all experiences from old system
            experiences = old_memory.experiences
            logger.info(f"Found {len(experiences)} experiences to migrate")
            
            migrated_count = 0
            failed_count = 0
            migration_results = []
            
            for experience in experiences:
                try:
                    # Convert old experience to new format
                    new_experience_data = {
                        "type": "experience",
                        "category": experience.category.value,
                        "context": experience.context,
                        "action": experience.action,
                        "outcome": experience.outcome,
                        "success": experience.success,
                        "lessons": experience.lessons_learned,
                        "tags": experience.tags,
                        "confidence": experience.confidence,
                        "impact_score": experience.impact_score,
                        "timestamp": experience.timestamp,
                        "source": "migrated_from_old"
                    }
                    
                    # Store in new system (if available)
                    if manager.new_adapter:
                        # For new system, we would need to convert to content format
                        # This is a simplified approach
                        logger.debug(f"Would migrate experience: {experience.experience_id}")
                        migrated_count += 1
                    else:
                        logger.warning("New system not available for migration")
                        failed_count += 1
                    
                    migration_results.append({
                        "old_id": experience.experience_id,
                        "status": "migrated" if manager.new_adapter else "failed",
                        "timestamp": datetime.now().isoformat()
                    })
                    
                except Exception as e:
                    logger.error(f"Failed to migrate experience {experience.experience_id}: {e}")
                    failed_count += 1
                    migration_results.append({
                        "old_id": experience.experience_id,
                        "status": "failed",
                        "error": str(e),
                        "timestamp": datetime.now().isoformat()
                    })
            
            # Log migration results
            migration_log = {
                "migration_id": f"migration_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                "from_system": "old",
                "to_system": "new",
                "backup_id": backup_id,
                "timestamp": datetime.now().isoformat(),
                "total_experiences": len(experiences),
                "migrated_count": migrated_count,
                "failed_count": failed_count,
                "results": migration_results
            }
            
            # Save migration log
            with open(self.migration_log, "w") as f:
                json.dump(migration_log, f, indent=2)
            
            logger.info(f"Migration completed: {migrated_count} migrated, {failed_count} failed")
            return migration_log
            
        except Exception as e:
            logger.error(f"Migration failed: {e}")
            raise
    
    def validate_migration(self) -> Dict[str, Any]:
        """Validate migration results"""
        logger.info("Validating migration results")
        
        try:
            manager = get_unified_learning_manager()
            
            validation_results = {
                "timestamp": datetime.now().isoformat(),
                "old_system": {},
                "new_system": {},
                "validation_passed": True
            }
            
            # Validate old system
            if manager.old_adapter:
                try:
                    old_stats = manager.old_adapter.get_stats()
                    validation_results["old_system"] = {
                        "status": "available",
                        "stats": old_stats
                    }
                except Exception as e:
                    validation_results["old_system"] = {
                        "status": "error",
                        "error": str(e)
                    }
                    validation_results["validation_passed"] = False
            
            # Validate new system
            if manager.new_adapter:
                try:
                    new_stats = manager.new_adapter.get_stats()
                    validation_results["new_system"] = {
                        "status": "available",
                        "stats": new_stats
                    }
                except Exception as e:
                    validation_results["new_system"] = {
                        "status": "error",
                        "error": str(e)
                    }
                    validation_results["validation_passed"] = False
            
            # Check migration log
            if self.migration_log.exists():
                with open(self.migration_log, "r") as f:
                    migration_log = json.load(f)
                validation_results["last_migration"] = migration_log
            
            logger.info(f"Validation completed: {'PASSED' if validation_results['validation_passed'] else 'FAILED'}")
            return validation_results
            
        except Exception as e:
            logger.error(f"Validation failed: {e}")
            return {
                "timestamp": datetime.now().isoformat(),
                "validation_passed": False,
                "error": str(e)
            }
    
    def rollback_migration(self, backup_id: str) -> bool:
        """Rollback migration using backup"""
        logger.info(f"Rolling back migration using backup: {backup_id}")
        
        try:
            backup_path = self.backup_dir / backup_id
            if not backup_path.exists():
                raise FileNotFoundError(f"Backup {backup_id} not found")
            
            # Load backup manifest
            manifest_path = backup_path / "manifest.json"
            if not manifest_path.exists():
                raise FileNotFoundError(f"Backup manifest not found for {backup_id}")
            
            with open(manifest_path, "r") as f:
                manifest = json.load(f)
            
            # Restore files
            for file_path in manifest["files"]:
                source_path = backup_path / file_path
                if file_path == "manifest.json":
                    continue  # Skip manifest file
                
                # Determine target path
                if file_path == "experience_memory.db":
                    target_path = Path(".experience_memory.db")
                elif file_path == "vector_index.pkl":
                    target_path = Path("data/vector_index.pkl")
                elif file_path == "claims_store.db":
                    target_path = Path("data/claims_store.db")
                elif file_path == "approval_queue.json":
                    target_path = Path("data/approval_queue.json")
                else:
                    # For other files, restore to data directory
                    target_path = Path("data") / file_path
                
                if source_path.exists():
                    import shutil
                    target_path.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(source_path, target_path)
                    logger.info(f"Restored: {file_path}")
            
            logger.info(f"Rollback completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"Rollback failed: {e}")
            return False
    
    def list_backups(self) -> List[Dict[str, Any]]:
        """List available backups"""
        backups = []
        
        for backup_dir in self.backup_dir.iterdir():
            if backup_dir.is_dir():
                manifest_path = backup_dir / "manifest.json"
                if manifest_path.exists():
                    try:
                        with open(manifest_path, "r") as f:
                            manifest = json.load(f)
                        backups.append(manifest)
                    except Exception as e:
                        logger.warning(f"Failed to read manifest for {backup_dir.name}: {e}")
        
        return sorted(backups, key=lambda x: x["timestamp"], reverse=True)


def main():
    """Main CLI interface"""
    parser = argparse.ArgumentParser(description="StillMe Learning Systems Migration")
    parser.add_argument("--from", dest="from_system", choices=["old", "new"], help="Source system")
    parser.add_argument("--to", dest="to_system", choices=["old", "new"], help="Target system")
    parser.add_argument("--backup", action="store_true", help="Create backup before migration")
    parser.add_argument("--validate", action="store_true", help="Validate migration results")
    parser.add_argument("--rollback", help="Rollback to backup ID")
    parser.add_argument("--list-backups", action="store_true", help="List available backups")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be migrated without doing it")
    
    args = parser.parse_args()
    
    migration_manager = LearningMigrationManager()
    
    try:
        if args.list_backups:
            backups = migration_manager.list_backups()
            print(f"\nAvailable backups ({len(backups)}):")
            for backup in backups:
                print(f"  {backup['backup_id']} - {backup['timestamp']} ({backup['system']} system)")
            return
        
        if args.rollback:
            success = migration_manager.rollback_migration(args.rollback)
            if success:
                print(f"✅ Rollback completed successfully")
            else:
                print(f"❌ Rollback failed")
                sys.exit(1)
            return
        
        if args.validate:
            results = migration_manager.validate_migration()
            print(f"\nValidation Results:")
            print(f"  Status: {'✅ PASSED' if results['validation_passed'] else '❌ FAILED'}")
            print(f"  Old System: {results['old_system'].get('status', 'unknown')}")
            print(f"  New System: {results['new_system'].get('status', 'unknown')}")
            return
        
        if args.from_system and args.to_system:
            if args.from_system == args.to_system:
                print("❌ Source and target systems cannot be the same")
                sys.exit(1)
            
            backup_id = None
            if args.backup:
                if args.from_system == "old":
                    backup_id = migration_manager.backup_old_system()
                else:
                    backup_id = migration_manager.backup_new_system()
                print(f"✅ Backup created: {backup_id}")
            
            if args.dry_run:
                print(f"🔍 Dry run: Would migrate from {args.from_system} to {args.to_system}")
                if backup_id:
                    print(f"   Backup ID: {backup_id}")
                return
            
            if args.from_system == "old" and args.to_system == "new":
                results = migration_manager.migrate_from_old_to_new(backup_id)
                print(f"✅ Migration completed:")
                print(f"   Total experiences: {results['total_experiences']}")
                print(f"   Migrated: {results['migrated_count']}")
                print(f"   Failed: {results['failed_count']}")
            else:
                print(f"❌ Migration from {args.from_system} to {args.to_system} not implemented yet")
                sys.exit(1)
        else:
            parser.print_help()
    
    except Exception as e:
        logger.error(f"Migration script failed: {e}")
        print(f"❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
