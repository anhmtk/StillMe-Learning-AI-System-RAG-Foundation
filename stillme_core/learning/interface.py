"""
StillMe Learning Interface - Unified Learning Systems
=====================================================

This module provides a unified interface for both old and new learning systems.
"""

import logging
from typing import Any, Dict, List, Optional, Union
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
import toml
from pathlib import Path

logger = logging.getLogger(__name__)


class LearningSystemType(Enum):
    """Learning system types"""
    OLD = "old"
    NEW = "new"
    BOTH = "both"


@dataclass
class LearningConfig:
    """Learning configuration"""
    system_type: LearningSystemType = LearningSystemType.NEW
    auto_migrate: bool = False
    backup_before_migrate: bool = True
    parallel_mode: bool = False
    sync_data: bool = False
    conflict_resolution: str = "new_wins"


class LearningInterface(ABC):
    """Abstract base class for learning systems"""
    
    @abstractmethod
    def store_experience(self, experience_data: Dict[str, Any]) -> str:
        """Store learning experience"""
        pass
    
    @abstractmethod
    def get_recommendations(self, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Get learning recommendations"""
        pass
    
    @abstractmethod
    def get_stats(self) -> Dict[str, Any]:
        """Get learning statistics"""
        pass
    
    @abstractmethod
    def cleanup(self) -> bool:
        """Cleanup learning data"""
        pass


class OldLearningAdapter(LearningInterface):
    """Adapter for old learning system (ExperienceMemory)"""
    
    def __init__(self):
        """Initialize old learning adapter"""
        self.experience_memory = None
        try:
            from stillme_core.core.self_learning.experience_memory import ExperienceMemory
            self.experience_memory = ExperienceMemory()
            logger.info("Old learning system adapter initialized")
        except ImportError as e:
            logger.warning(f"Old learning system not available: {e}")
    
    def store_experience(self, experience_data: Dict[str, Any]) -> str:
        """Store experience using old system"""
        if not self.experience_memory:
            raise NotImplementedError("Old learning system not available")
        
        # Convert new format to old format
        from stillme_core.core.self_learning.experience_memory import ExperienceType, ExperienceCategory
        
        experience_type = ExperienceType(experience_data.get("type", "learning"))
        category = ExperienceCategory(experience_data.get("category", "technical"))
        
        return self.experience_memory.store_experience(
            experience_type=experience_type,
            category=category,
            context=experience_data.get("context", {}),
            action=experience_data.get("action", ""),
            outcome=experience_data.get("outcome", {}),
            success=experience_data.get("success", True),
            lessons_learned=experience_data.get("lessons", []),
            tags=experience_data.get("tags", []),
            confidence=experience_data.get("confidence", 0.5),
            impact_score=experience_data.get("impact_score", 0.5)
        )
    
    def get_recommendations(self, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Get recommendations from old system"""
        if not self.experience_memory:
            return []
        
        try:
            return self.experience_memory.get_recommendations(
                context=context,
                action=context.get("action", ""),
                tags=context.get("tags", [])
            )
        except Exception as e:
            logger.error(f"Failed to get old system recommendations: {e}")
            return []
    
    def get_stats(self) -> Dict[str, Any]:
        """Get stats from old system"""
        if not self.experience_memory:
            return {"status": "unavailable"}
        
        try:
            return self.experience_memory.get_learning_stats()
        except Exception as e:
            logger.error(f"Failed to get old system stats: {e}")
            return {"status": "error", "error": str(e)}
    
    def cleanup(self) -> bool:
        """Cleanup old system data"""
        if not self.experience_memory:
            return True
        
        try:
            self.experience_memory.cleanup_old_data()
            return True
        except Exception as e:
            logger.error(f"Old system cleanup failed: {e}")
            return False


class NewLearningAdapter(LearningInterface):
    """Adapter for new learning system (RSS + Vector Store)"""
    
    def __init__(self):
        """Initialize new learning adapter"""
        self.pipeline = None
        try:
            from stillme_core.learning.pipeline import LearningPipeline
            self.pipeline = LearningPipeline()
            logger.info("New learning system adapter initialized")
        except ImportError as e:
            logger.warning(f"New learning system not available: {e}")
    
    def store_experience(self, experience_data: Dict[str, Any]) -> str:
        """Store experience using new system"""
        if not self.pipeline:
            raise NotImplementedError("New learning system not available")
        
        # Convert old format to new format
        # This would involve ingesting the experience as content
        logger.warning("New system doesn't directly store experiences - use content ingestion")
        return "new_system_experience_id"
    
    def get_recommendations(self, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Get recommendations from new system"""
        if not self.pipeline:
            return []
        
        # Get recommendations from approval queue
        try:
            from stillme_core.learning.approve.queue import get_approval_queue
            queue = get_approval_queue()
            return queue.get_pending_recommendations()
        except Exception as e:
            logger.error(f"Failed to get new system recommendations: {e}")
            return []
    
    def get_stats(self) -> Dict[str, Any]:
        """Get stats from new system"""
        if not self.pipeline:
            return {"status": "unavailable"}
        
        try:
            from stillme_core.learning.reports.digest import get_digest_generator
            generator = get_digest_generator()
            return generator.get_metrics()
        except Exception as e:
            logger.error(f"Failed to get new system stats: {e}")
            return {"status": "error", "error": str(e)}
    
    def cleanup(self) -> bool:
        """Cleanup new system data"""
        try:
            # Cleanup vector store
            from stillme_core.learning.ingest.vector_store import get_vector_store
            vector_store = get_vector_store()
            if hasattr(vector_store, 'clear'):
                vector_store.clear()
            
            # Cleanup claims store
            from stillme_core.learning.ingest.claims_store import get_claims_store
            claims_store = get_claims_store()
            if hasattr(claims_store, 'clear_all_claims'):
                claims_store.clear_all_claims()
            
            return True
        except Exception as e:
            logger.error(f"New system cleanup failed: {e}")
            return False


# Global instance
_learning_manager = None


def get_learning_manager() -> 'UnifiedLearningManager':
    """Get global learning manager instance"""
    global _learning_manager
    if _learning_manager is None:
        from stillme_core.learning.unified_learning_manager import get_unified_learning_manager
        _learning_manager = get_unified_learning_manager()
    return _learning_manager