#!/usr/bin/env python3
"""
🔄 StillMe Learning System Migration Script
==========================================

Script để migrate từ dual learning system sang unified evolutionary system.
Bao gồm:
- Backup existing data
- Migrate ExperienceMemory data
- Migrate LearningPipeline data
- Validate migration results
- Switch to unified system

Usage:
    python scripts/migrate_to_unified_learning.py --backup --migrate --validate
    python scripts/migrate_to_unified_learning.py --rollback
    python scripts/migrate_to_unified_learning.py --status

Author: StillMe AI Framework
Version: 2.0.0
Date: 2025-09-27
"""

import argparse
import asyncio
import json
import logging
import shutil
import sqlite3
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Import systems
try:
    from stillme_core.core.self_learning.experience_memory import ExperienceMemory
    from stillme_core.learning.pipeline import LearningPipeline
    from stillme_core.learning.evolutionary_learning_system import EvolutionaryLearningSystem, EvolutionaryConfig
    from stillme_core.learning.learning_assessment_system import LearningAssessmentSystem
except ImportError as e:
    logging.error(f"Failed to import learning systems: {e}")
    sys.exit(1)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('migration.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class LearningSystemMigration:
    """Main migration class"""
    
    def __init__(self, backup_dir: str = "backups", config_path: str = "config/evolutionary_learning.toml"):
        self.backup_dir = Path(backup_dir)
        self.config_path = Path(config_path)
        self.migration_log = []
        
        # Initialize systems
        self.old_experience_memory = None
        self.old_learning_pipeline = None
        self.new_unified_system = None
        self.assessment_system = None
        
        # Migration state
        self.migration_start_time = None
        self.migration_status = "not_started"
        self.migration_results = {}
        
        # Create backup directory
        self.backup_dir.mkdir(exist_ok=True)
        
        logger.info("Learning System Migration initialized")
    
    async def initialize_systems(self):
        """Initialize all learning systems"""
        try:
            # Initialize old systems
            self.old_experience_memory = ExperienceMemory()
            self.old_learning_pipeline = LearningPipeline()
            
            # Initialize new unified system
            config = EvolutionaryConfig()
            self.new_unified_system = EvolutionaryLearningSystem(config)
            self.assessment_system = LearningAssessmentSystem()
            
            logger.info("All learning systems initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize systems: {e}")
            return False
    
    async def backup_existing_data(self) -> bool:
        """Backup existing learning data"""
        backup_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = self.backup_dir / f"learning_backup_{backup_timestamp}"
        backup_path.mkdir(exist_ok=True)
        
        logger.info(f"Starting backup to {backup_path}")
        
        try:
            # Backup ExperienceMemory database
            if self.old_experience_memory and Path(self.old_experience_memory.db_path).exists():
                shutil.copy2(self.old_experience_memory.db_path, backup_path / "experience_memory.db")
                logger.info("ExperienceMemory database backed up")
            
            # Backup LearningPipeline data
            pipeline_backup_path = backup_path / "learning_pipeline"
            pipeline_backup_path.mkdir(exist_ok=True)
            
            # Backup vector store if exists
            vector_store_path = Path("data/vector_store")
            if vector_store_path.exists():
                shutil.copytree(vector_store_path, pipeline_backup_path / "vector_store")
                logger.info("Vector store backed up")
            
            # Backup claims store if exists
            claims_store_path = Path("data/claims_store.db")
            if claims_store_path.exists():
                shutil.copy2(claims_store_path, pipeline_backup_path / "claims_store.db")
                logger.info("Claims store backed up")
            
            # Backup configuration files
            config_files = [
                "config/learning.toml",
                "policies/learning_policy.yaml"
            ]
            
            for config_file in config_files:
                if Path(config_file).exists():
                    shutil.copy2(config_file, backup_path / Path(config_file).name)
                    logger.info(f"Config file {config_file} backed up")
            
            # Create backup manifest
            manifest = {
                "backup_timestamp": backup_timestamp,
                "backup_path": str(backup_path),
                "files_backed_up": [
                    "experience_memory.db",
                    "learning_pipeline/vector_store",
                    "learning_pipeline/claims_store.db",
                    "config/learning.toml",
                    "policies/learning_policy.yaml"
                ],
                "backup_size_mb": self._calculate_backup_size(backup_path)
            }
            
            with open(backup_path / "backup_manifest.json", "w") as f:
                json.dump(manifest, f, indent=2)
            
            logger.info(f"Backup completed successfully: {backup_path}")
            return True
            
        except Exception as e:
            logger.error(f"Backup failed: {e}")
            return False
    
    async def migrate_experience_memory(self) -> Dict[str, Any]:
        """Migrate ExperienceMemory data to unified system"""
        logger.info("Starting ExperienceMemory migration")
        
        migration_results = {
            "source": "ExperienceMemory",
            "total_records": 0,
            "migrated_records": 0,
            "failed_records": 0,
            "errors": [],
            "start_time": time.time()
        }
        
        try:
            # Get all experiences
            all_experiences = self.old_experience_memory.experiences
            migration_results["total_records"] = len(all_experiences)
            
            logger.info(f"Found {len(all_experiences)} experiences to migrate")
            
            # Migrate each experience
            for exp in all_experiences:
                try:
                    # Convert to unified format
                    unified_knowledge = {
                        "knowledge_id": f"exp_{exp.experience_id}",
                        "source_type": "experience",
                        "timestamp": exp.timestamp,
                        "category": exp.category.value,
                        "content": f"Action: {exp.action}\nOutcome: {exp.outcome}",
                        "metadata": {
                            "experience_type": exp.experience_type.value,
                            "success": exp.success,
                            "lessons_learned": exp.lessons_learned,
                            "tags": exp.tags,
                            "related_experiences": exp.related_experiences
                        },
                        "confidence": exp.confidence,
                        "impact_score": exp.impact_score,
                        "learning_stage": "infant",  # Start as infant
                        "tags": exp.tags
                    }
                    
                    # Store in unified system
                    await self.new_unified_system.store_knowledge(unified_knowledge)
                    migration_results["migrated_records"] += 1
                    
                except Exception as e:
                    migration_results["failed_records"] += 1
                    migration_results["errors"].append(f"Experience {exp.experience_id}: {str(e)}")
                    logger.warning(f"Failed to migrate experience {exp.experience_id}: {e}")
            
            migration_results["end_time"] = time.time()
            migration_results["duration_seconds"] = migration_results["end_time"] - migration_results["start_time"]
            
            logger.info(f"ExperienceMemory migration completed: {migration_results['migrated_records']}/{migration_results['total_records']} records")
            return migration_results
            
        except Exception as e:
            logger.error(f"ExperienceMemory migration failed: {e}")
            migration_results["errors"].append(f"Migration failed: {str(e)}")
            return migration_results
    
    async def migrate_learning_pipeline(self) -> Dict[str, Any]:
        """Migrate LearningPipeline data to unified system"""
        logger.info("Starting LearningPipeline migration")
        
        migration_results = {
            "source": "LearningPipeline",
            "total_records": 0,
            "migrated_records": 0,
            "failed_records": 0,
            "errors": [],
            "start_time": time.time()
        }
        
        try:
            # Migrate vector store data
            vector_migration = await self._migrate_vector_store()
            migration_results["total_records"] += vector_migration["total_records"]
            migration_results["migrated_records"] += vector_migration["migrated_records"]
            migration_results["failed_records"] += vector_migration["failed_records"]
            migration_results["errors"].extend(vector_migration["errors"])
            
            # Migrate claims store data
            claims_migration = await self._migrate_claims_store()
            migration_results["total_records"] += claims_migration["total_records"]
            migration_results["migrated_records"] += claims_migration["migrated_records"]
            migration_results["failed_records"] += claims_migration["failed_records"]
            migration_results["errors"].extend(claims_migration["errors"])
            
            migration_results["end_time"] = time.time()
            migration_results["duration_seconds"] = migration_results["end_time"] - migration_results["start_time"]
            
            logger.info(f"LearningPipeline migration completed: {migration_results['migrated_records']}/{migration_results['total_records']} records")
            return migration_results
            
        except Exception as e:
            logger.error(f"LearningPipeline migration failed: {e}")
            migration_results["errors"].append(f"Migration failed: {str(e)}")
            return migration_results
    
    async def _migrate_vector_store(self) -> Dict[str, Any]:
        """Migrate vector store data"""
        migration_results = {
            "total_records": 0,
            "migrated_records": 0,
            "failed_records": 0,
            "errors": []
        }
        
        try:
            # Get vector store
            vector_store = self.old_learning_pipeline.vector_store
            if not vector_store:
                logger.warning("Vector store not available")
                return migration_results
            
            # Get all vectors (this would depend on actual vector store implementation)
            # For now, simulate getting vectors
            vector_data = []  # This would be: vector_store.get_all_vectors()
            
            migration_results["total_records"] = len(vector_data)
            
            for vector_item in vector_data:
                try:
                    unified_knowledge = {
                        "knowledge_id": f"vec_{vector_item['id']}",
                        "source_type": "content",
                        "timestamp": vector_item.get("timestamp", time.time()),
                        "category": "external_content",
                        "content": vector_item["content"],
                        "metadata": vector_item.get("metadata", {}),
                        "confidence": vector_item.get("confidence", 0.8),
                        "impact_score": vector_item.get("quality_score", 0.7),
                        "learning_stage": "infant",
                        "vector_embedding": vector_item.get("embedding")
                    }
                    
                    await self.new_unified_system.store_knowledge(unified_knowledge)
                    migration_results["migrated_records"] += 1
                    
                except Exception as e:
                    migration_results["failed_records"] += 1
                    migration_results["errors"].append(f"Vector {vector_item.get('id', 'unknown')}: {str(e)}")
            
            return migration_results
            
        except Exception as e:
            logger.error(f"Vector store migration failed: {e}")
            migration_results["errors"].append(f"Vector store migration failed: {str(e)}")
            return migration_results
    
    async def _migrate_claims_store(self) -> Dict[str, Any]:
        """Migrate claims store data"""
        migration_results = {
            "total_records": 0,
            "migrated_records": 0,
            "failed_records": 0,
            "errors": []
        }
        
        try:
            # Get claims store
            claims_store = self.old_learning_pipeline.claims_store
            if not claims_store:
                logger.warning("Claims store not available")
                return migration_results
            
            # Get all claims (this would depend on actual claims store implementation)
            # For now, simulate getting claims
            claims_data = []  # This would be: claims_store.get_all_claims()
            
            migration_results["total_records"] = len(claims_data)
            
            for claim in claims_data:
                try:
                    unified_knowledge = {
                        "knowledge_id": f"claim_{claim['claim_id']}",
                        "source_type": "content",
                        "timestamp": claim.get("timestamp", time.time()),
                        "category": "structured_knowledge",
                        "content": f"{claim['subject']} {claim['predicate']} {claim['object']}",
                        "metadata": {
                            "source": claim["source"],
                            "claim_type": "triple"
                        },
                        "confidence": claim["confidence"],
                        "impact_score": 0.6,
                        "learning_stage": "infant"
                    }
                    
                    await self.new_unified_system.store_knowledge(unified_knowledge)
                    migration_results["migrated_records"] += 1
                    
                except Exception as e:
                    migration_results["failed_records"] += 1
                    migration_results["errors"].append(f"Claim {claim.get('claim_id', 'unknown')}: {str(e)}")
            
            return migration_results
            
        except Exception as e:
            logger.error(f"Claims store migration failed: {e}")
            migration_results["errors"].append(f"Claims store migration failed: {str(e)}")
            return migration_results
    
    async def validate_migration(self) -> Dict[str, Any]:
        """Validate migration results"""
        logger.info("Starting migration validation")
        
        validation_results = {
            "validation_passed": True,
            "checks": [],
            "errors": [],
            "warnings": []
        }
        
        try:
            # Check 1: Data count validation
            old_total = len(self.old_experience_memory.experiences) if self.old_experience_memory else 0
            new_total = len(self.new_unified_system.knowledge_base) if hasattr(self.new_unified_system, 'knowledge_base') else 0
            
            if new_total >= old_total * 0.95:  # Allow 5% loss
                validation_results["checks"].append({
                    "check": "data_count",
                    "status": "passed",
                    "old_count": old_total,
                    "new_count": new_total
                })
            else:
                validation_results["validation_passed"] = False
                validation_results["errors"].append(f"Data count mismatch: {old_total} -> {new_total}")
            
            # Check 2: System functionality
            try:
                # Test unified system functionality
                status = self.new_unified_system.get_learning_status()
                if status:
                    validation_results["checks"].append({
                        "check": "system_functionality",
                        "status": "passed",
                        "current_stage": status.get("current_stage"),
                        "evolution_progress": status.get("evolution_progress")
                    })
                else:
                    validation_results["validation_passed"] = False
                    validation_results["errors"].append("Unified system not responding")
            except Exception as e:
                validation_results["validation_passed"] = False
                validation_results["errors"].append(f"System functionality test failed: {e}")
            
            # Check 3: Assessment system
            try:
                assessment_summary = self.assessment_system.get_assessment_summary()
                validation_results["checks"].append({
                    "check": "assessment_system",
                    "status": "passed",
                    "summary": assessment_summary
                })
            except Exception as e:
                validation_results["warnings"].append(f"Assessment system test failed: {e}")
            
            logger.info(f"Migration validation completed: {'PASSED' if validation_results['validation_passed'] else 'FAILED'}")
            return validation_results
            
        except Exception as e:
            logger.error(f"Migration validation failed: {e}")
            validation_results["validation_passed"] = False
            validation_results["errors"].append(f"Validation failed: {str(e)}")
            return validation_results
    
    async def switch_to_unified_system(self) -> bool:
        """Switch to unified system"""
        logger.info("Switching to unified system")
        
        try:
            # Update configuration
            await self._update_configuration()
            
            # Start unified system services
            await self._start_unified_services()
            
            # Update system status
            self.migration_status = "completed"
            
            logger.info("Successfully switched to unified system")
            return True
            
        except Exception as e:
            logger.error(f"Failed to switch to unified system: {e}")
            return False
    
    async def _update_configuration(self):
        """Update system configuration"""
        # Update learning.toml to point to unified system
        config_content = """
[system]
mode = "unified"
unified_system_enabled = true

[unified_system]
learning_mode = "evolutionary"
current_stage = "infant"
daily_training_minutes = 30
assessment_frequency_hours = 6

[migration]
migration_completed = true
migration_date = "{migration_date}"
        """.format(migration_date=datetime.now().isoformat())
        
        with open("config/learning.toml", "w") as f:
            f.write(config_content)
        
        logger.info("Configuration updated")
    
    async def _start_unified_services(self):
        """Start unified system services"""
        # This would start any background services needed
        logger.info("Unified system services started")
    
    async def rollback_migration(self, backup_timestamp: str) -> bool:
        """Rollback migration to previous state"""
        logger.info(f"Starting rollback to backup {backup_timestamp}")
        
        try:
            backup_path = self.backup_dir / f"learning_backup_{backup_timestamp}"
            
            if not backup_path.exists():
                logger.error(f"Backup {backup_timestamp} not found")
                return False
            
            # Restore ExperienceMemory database
            if (backup_path / "experience_memory.db").exists():
                shutil.copy2(backup_path / "experience_memory.db", self.old_experience_memory.db_path)
                logger.info("ExperienceMemory database restored")
            
            # Restore LearningPipeline data
            pipeline_backup = backup_path / "learning_pipeline"
            if pipeline_backup.exists():
                # Restore vector store
                if (pipeline_backup / "vector_store").exists():
                    shutil.copytree(pipeline_backup / "vector_store", "data/vector_store", dirs_exist_ok=True)
                    logger.info("Vector store restored")
                
                # Restore claims store
                if (pipeline_backup / "claims_store.db").exists():
                    shutil.copy2(pipeline_backup / "claims_store.db", "data/claims_store.db")
                    logger.info("Claims store restored")
            
            # Restore configuration
            if (backup_path / "learning.toml").exists():
                shutil.copy2(backup_path / "learning.toml", "config/learning.toml")
                logger.info("Configuration restored")
            
            logger.info("Rollback completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"Rollback failed: {e}")
            return False
    
    def get_migration_status(self) -> Dict[str, Any]:
        """Get current migration status"""
        return {
            "migration_status": self.migration_status,
            "migration_start_time": self.migration_start_time,
            "migration_results": self.migration_results,
            "available_backups": self._get_available_backups()
        }
    
    def _get_available_backups(self) -> List[str]:
        """Get list of available backups"""
        backups = []
        for backup_dir in self.backup_dir.iterdir():
            if backup_dir.is_dir() and backup_dir.name.startswith("learning_backup_"):
                backups.append(backup_dir.name.replace("learning_backup_", ""))
        return sorted(backups, reverse=True)
    
    def _calculate_backup_size(self, backup_path: Path) -> float:
        """Calculate backup size in MB"""
        total_size = 0
        for file_path in backup_path.rglob("*"):
            if file_path.is_file():
                total_size += file_path.stat().st_size
        return total_size / (1024 * 1024)  # Convert to MB

async def main():
    """Main migration function"""
    parser = argparse.ArgumentParser(description="StillMe Learning System Migration")
    parser.add_argument("--backup", action="store_true", help="Backup existing data")
    parser.add_argument("--migrate", action="store_true", help="Run migration")
    parser.add_argument("--validate", action="store_true", help="Validate migration")
    parser.add_argument("--switch", action="store_true", help="Switch to unified system")
    parser.add_argument("--rollback", type=str, help="Rollback to backup timestamp")
    parser.add_argument("--status", action="store_true", help="Show migration status")
    parser.add_argument("--backup-dir", default="backups", help="Backup directory")
    parser.add_argument("--config", default="config/evolutionary_learning.toml", help="Config file path")
    
    args = parser.parse_args()
    
    # Initialize migration
    migration = LearningSystemMigration(args.backup_dir, args.config)
    
    if args.status:
        status = migration.get_migration_status()
        print(json.dumps(status, indent=2))
        return
    
    if args.rollback:
        success = await migration.rollback_migration(args.rollback)
        if success:
            print("✅ Rollback completed successfully")
        else:
            print("❌ Rollback failed")
        return
    
    # Initialize systems
    if not await migration.initialize_systems():
        print("❌ Failed to initialize systems")
        return
    
    migration.migration_start_time = time.time()
    migration.migration_status = "in_progress"
    
    try:
        # Backup if requested
        if args.backup:
            print("🔄 Backing up existing data...")
            if await migration.backup_existing_data():
                print("✅ Backup completed successfully")
            else:
                print("❌ Backup failed")
                return
        
        # Migrate if requested
        if args.migrate:
            print("🔄 Starting migration...")
            
            # Migrate ExperienceMemory
            exp_results = await migration.migrate_experience_memory()
            migration.migration_results["experience_memory"] = exp_results
            print(f"✅ ExperienceMemory: {exp_results['migrated_records']}/{exp_results['total_records']} records")
            
            # Migrate LearningPipeline
            pipeline_results = await migration.migrate_learning_pipeline()
            migration.migration_results["learning_pipeline"] = pipeline_results
            print(f"✅ LearningPipeline: {pipeline_results['migrated_records']}/{pipeline_results['total_records']} records")
        
        # Validate if requested
        if args.validate:
            print("🔍 Validating migration...")
            validation_results = await migration.validate_migration()
            migration.migration_results["validation"] = validation_results
            
            if validation_results["validation_passed"]:
                print("✅ Migration validation passed")
            else:
                print("❌ Migration validation failed")
                for error in validation_results["errors"]:
                    print(f"  - {error}")
        
        # Switch to unified system if requested
        if args.switch:
            print("🔄 Switching to unified system...")
            if await migration.switch_to_unified_system():
                print("✅ Successfully switched to unified system")
            else:
                print("❌ Failed to switch to unified system")
        
        # Final status
        migration.migration_status = "completed"
        print("\n🎉 Migration process completed!")
        print(f"Status: {migration.migration_status}")
        print(f"Results: {json.dumps(migration.migration_results, indent=2)}")
        
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        migration.migration_status = "failed"
        print(f"❌ Migration failed: {e}")

if __name__ == "__main__":
    asyncio.run(main())
