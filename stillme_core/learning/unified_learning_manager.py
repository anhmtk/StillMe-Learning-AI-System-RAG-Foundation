"""
StillMe Unified Learning Manager
===============================

Unified interface for managing both old and new learning systems.
Resolves conflicts and provides seamless migration path.

Author: StillMe AI Framework
Version: 1.0.0
"""

import logging
import toml
from typing import Dict, Any, List, Optional, Union
from pathlib import Path
from dataclasses import dataclass
from enum import Enum

# Import learning interfaces
from .interface import LearningInterface, OldLearningAdapter, NewLearningAdapter

logger = logging.getLogger(__name__)

class LearningSystemMode(Enum):
    """Learning system operation modes"""
    OLD_ONLY = "old_only"
    NEW_ONLY = "new_only"
    BOTH_PARALLEL = "both_parallel"
    MIGRATION = "migration"
    UNIFIED = "unified"

@dataclass
class LearningConfig:
    """Learning system configuration"""
    mode: LearningSystemMode
    auto_migrate: bool = False
    backup_before_migrate: bool = True
    batch_size: int = 100
    conflict_resolution: str = "new_wins"
    parallel_mode: bool = False
    sync_data: bool = False

class UnifiedLearningManager:
    """
    Unified Learning Manager - Resolves conflicts between old and new learning systems
    """
    
    def __init__(self, config_path: str = "config/learning.toml"):
        """Initialize unified learning manager"""
        self.config_path = Path(config_path)
        self.config = self._load_config()
        
        # Initialize adapters
        self.old_adapter: Optional[OldLearningAdapter] = None
        self.new_adapter: Optional[NewLearningAdapter] = None
        
        # Initialize based on config
        self._initialize_adapters()
        
        logger.info(f"Unified Learning Manager initialized in {self.config.mode.value} mode")
    
    def _load_config(self) -> LearningConfig:
        """Load learning configuration"""
        if not self.config_path.exists():
            logger.warning(f"Config file {self.config_path} not found, using defaults")
            return LearningConfig(mode=LearningSystemMode.NEW_ONLY)
        
        try:
            config_data = toml.load(self.config_path)
            
            # Parse system mode
            system_mode = config_data.get("system", "new")
            if system_mode == "new":
                mode = LearningSystemMode.NEW_ONLY
            elif system_mode == "old":
                mode = LearningSystemMode.OLD_ONLY
            elif system_mode == "both":
                mode = LearningSystemMode.BOTH_PARALLEL
            else:
                mode = LearningSystemMode.UNIFIED
            
            # Parse migration settings
            migration = config_data.get("migration", {})
            auto_migrate = migration.get("auto_migrate", False)
            backup_before_migrate = migration.get("backup_before_migrate", True)
            batch_size = migration.get("batch_size", 100)
            
            # Parse compatibility settings
            compatibility = config_data.get("compatibility", {})
            conflict_resolution = compatibility.get("conflict_resolution", "new_wins")
            parallel_mode = compatibility.get("parallel_mode", False)
            sync_data = compatibility.get("sync_data", False)
            
            return LearningConfig(
                mode=mode,
                auto_migrate=auto_migrate,
                backup_before_migrate=backup_before_migrate,
                batch_size=batch_size,
                conflict_resolution=conflict_resolution,
                parallel_mode=parallel_mode,
                sync_data=sync_data
            )
            
        except Exception as e:
            logger.error(f"Failed to load config: {e}")
            return LearningConfig(mode=LearningSystemMode.NEW_ONLY)
    
    def _initialize_adapters(self):
        """Initialize learning system adapters based on config"""
        try:
            if self.config.mode in [LearningSystemMode.OLD_ONLY, LearningSystemMode.BOTH_PARALLEL, LearningSystemMode.UNIFIED]:
                self.old_adapter = OldLearningAdapter()
                logger.info("Old learning adapter initialized")
        except Exception as e:
            logger.warning(f"Failed to initialize old learning adapter: {e}")
        
        try:
            if self.config.mode in [LearningSystemMode.NEW_ONLY, LearningSystemMode.BOTH_PARALLEL, LearningSystemMode.UNIFIED]:
                self.new_adapter = NewLearningAdapter()
                logger.info("New learning adapter initialized")
        except Exception as e:
            logger.warning(f"Failed to initialize new learning adapter: {e}")
    
    def store_experience(self, experience_data: Dict[str, Any]) -> Dict[str, str]:
        """
        Store experience using appropriate system(s)
        
        Returns:
            Dict with system names as keys and experience IDs as values
        """
        results = {}
        
        if self.config.mode == LearningSystemMode.OLD_ONLY and self.old_adapter:
            try:
                exp_id = self.old_adapter.store_experience(experience_data)
                results["old_system"] = exp_id
            except Exception as e:
                logger.error(f"Failed to store in old system: {e}")
        
        elif self.config.mode == LearningSystemMode.NEW_ONLY and self.new_adapter:
            try:
                exp_id = self.new_adapter.store_experience(experience_data)
                results["new_system"] = exp_id
            except Exception as e:
                logger.error(f"Failed to store in new system: {e}")
        
        elif self.config.mode == LearningSystemMode.BOTH_PARALLEL:
            # Store in both systems
            if self.old_adapter:
                try:
                    exp_id = self.old_adapter.store_experience(experience_data)
                    results["old_system"] = exp_id
                except Exception as e:
                    logger.error(f"Failed to store in old system: {e}")
            
            if self.new_adapter:
                try:
                    exp_id = self.new_adapter.store_experience(experience_data)
                    results["new_system"] = exp_id
                except Exception as e:
                    logger.error(f"Failed to store in new system: {e}")
        
        elif self.config.mode == LearningSystemMode.UNIFIED:
            # Use conflict resolution strategy
            if self.config.conflict_resolution == "new_wins" and self.new_adapter:
                try:
                    exp_id = self.new_adapter.store_experience(experience_data)
                    results["unified_system"] = exp_id
                except Exception as e:
                    logger.error(f"Failed to store in unified system: {e}")
            elif self.config.conflict_resolution == "old_wins" and self.old_adapter:
                try:
                    exp_id = self.old_adapter.store_experience(experience_data)
                    results["unified_system"] = exp_id
                except Exception as e:
                    logger.error(f"Failed to store in unified system: {e}")
        
        return results
    
    def get_recommendations(self, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Get recommendations from appropriate system(s)"""
        recommendations = []
        
        if self.config.mode == LearningSystemMode.OLD_ONLY and self.old_adapter:
            try:
                recs = self.old_adapter.get_recommendations(context)
                recommendations.extend(recs)
            except Exception as e:
                logger.error(f"Failed to get recommendations from old system: {e}")
        
        elif self.config.mode == LearningSystemMode.NEW_ONLY and self.new_adapter:
            try:
                recs = self.new_adapter.get_recommendations(context)
                recommendations.extend(recs)
            except Exception as e:
                logger.error(f"Failed to get recommendations from new system: {e}")
        
        elif self.config.mode == LearningSystemMode.BOTH_PARALLEL:
            # Get from both systems and merge
            if self.old_adapter:
                try:
                    recs = self.old_adapter.get_recommendations(context)
                    for rec in recs:
                        rec["source"] = "old_system"
                    recommendations.extend(recs)
                except Exception as e:
                    logger.error(f"Failed to get recommendations from old system: {e}")
            
            if self.new_adapter:
                try:
                    recs = self.new_adapter.get_recommendations(context)
                    for rec in recs:
                        rec["source"] = "new_system"
                    recommendations.extend(recs)
                except Exception as e:
                    logger.error(f"Failed to get recommendations from new system: {e}")
        
        elif self.config.mode == LearningSystemMode.UNIFIED:
            # Use conflict resolution strategy
            if self.config.conflict_resolution == "new_wins" and self.new_adapter:
                try:
                    recs = self.new_adapter.get_recommendations(context)
                    recommendations.extend(recs)
                except Exception as e:
                    logger.error(f"Failed to get recommendations from unified system: {e}")
            elif self.config.conflict_resolution == "old_wins" and self.old_adapter:
                try:
                    recs = self.old_adapter.get_recommendations(context)
                    recommendations.extend(recs)
                except Exception as e:
                    logger.error(f"Failed to get recommendations from unified system: {e}")
        
        return recommendations
    
    def get_stats(self) -> Dict[str, Any]:
        """Get statistics from all active systems"""
        stats = {
            "mode": self.config.mode.value,
            "systems": {}
        }
        
        if self.old_adapter:
            try:
                old_stats = self.old_adapter.get_stats()
                stats["systems"]["old_system"] = old_stats
            except Exception as e:
                logger.error(f"Failed to get old system stats: {e}")
                stats["systems"]["old_system"] = {"error": str(e)}
        
        if self.new_adapter:
            try:
                new_stats = self.new_adapter.get_stats()
                stats["systems"]["new_system"] = new_stats
            except Exception as e:
                logger.error(f"Failed to get new system stats: {e}")
                stats["systems"]["new_system"] = {"error": str(e)}
        
        return stats
    
    def migrate_data(self, from_system: str = "old", to_system: str = "new") -> Dict[str, Any]:
        """
        Migrate data between learning systems
        
        Args:
            from_system: Source system ("old" or "new")
            to_system: Target system ("old" or "new")
        
        Returns:
            Migration results
        """
        if not self.config.auto_migrate:
            return {"error": "Auto migration is disabled"}
        
        logger.info(f"Starting migration from {from_system} to {to_system}")
        
        try:
            # This would implement actual data migration logic
            # For now, return a placeholder
            return {
                "status": "migration_planned",
                "from_system": from_system,
                "to_system": to_system,
                "message": "Migration logic needs to be implemented"
            }
        except Exception as e:
            logger.error(f"Migration failed: {e}")
            return {"error": str(e)}
    
    def cleanup(self) -> bool:
        """Cleanup all learning systems"""
        success = True
        
        if self.old_adapter:
            try:
                if not self.old_adapter.cleanup():
                    success = False
            except Exception as e:
                logger.error(f"Old system cleanup failed: {e}")
                success = False
        
        if self.new_adapter:
            try:
                if not self.new_adapter.cleanup():
                    success = False
            except Exception as e:
                logger.error(f"New system cleanup failed: {e}")
                success = False
        
        return success
    
    def switch_mode(self, new_mode: LearningSystemMode) -> bool:
        """Switch learning system mode"""
        try:
            old_mode = self.config.mode
            self.config.mode = new_mode
            
            # Reinitialize adapters if needed
            self._initialize_adapters()
            
            logger.info(f"Switched from {old_mode.value} to {new_mode.value}")
            return True
        except Exception as e:
            logger.error(f"Failed to switch mode: {e}")
            return False

# Global instance
_unified_manager: Optional[UnifiedLearningManager] = None

def get_unified_learning_manager() -> UnifiedLearningManager:
    """Get global unified learning manager instance"""
    global _unified_manager
    if _unified_manager is None:
        _unified_manager = UnifiedLearningManager()
    return _unified_manager

def initialize_learning_systems(config_path: str = "config/learning.toml") -> UnifiedLearningManager:
    """Initialize learning systems with configuration"""
    global _unified_manager
    _unified_manager = UnifiedLearningManager(config_path)
    return _unified_manager
