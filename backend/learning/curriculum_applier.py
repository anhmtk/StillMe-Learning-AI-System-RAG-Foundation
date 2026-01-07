"""
Curriculum Applier for Meta-Learning (Stage 2, Phase 2)

Applies curriculum to learning system by adjusting priorities.
This enables auto-adjustment of learning priorities based on curriculum.

Part of Stage 2: Meta-Learning - "AI improves HOW it learns"
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime

from backend.learning.curriculum_generator import get_curriculum_generator, CurriculumItem
from stillme_core.learning.curator import ContentCurator

logger = logging.getLogger(__name__)


class CurriculumApplier:
    """
    Applies curriculum to learning system by:
    1. Updating ContentCurator priorities
    2. Updating source priorities in LearningScheduler
    3. Adjusting search keyword priorities
    """
    
    def __init__(self, curator: Optional[ContentCurator] = None):
        """
        Initialize curriculum applier
        
        Args:
            curator: ContentCurator instance (optional)
        """
        self.curriculum_generator = get_curriculum_generator()
        self.curator = curator
        logger.info("CurriculumApplier initialized")
    
    def apply_curriculum(
        self,
        days: int = 30,
        update_curator: bool = True,
        update_scheduler: bool = True
    ) -> Dict[str, Any]:
        """
        Apply curriculum to learning system
        
        Args:
            days: Number of days to analyze for curriculum
            update_curator: Whether to update ContentCurator priorities
            update_scheduler: Whether to update LearningScheduler source priorities
        
        Returns:
            Dictionary with application results
        """
        logger.info(f"📚 Applying curriculum to learning system...")
        
        # Generate curriculum
        curriculum = self.curriculum_generator.generate_curriculum(days=days)
        
        if not curriculum:
            logger.warning("No curriculum items generated")
            return {
                "status": "no_curriculum",
                "message": "No curriculum items generated",
                "timestamp": datetime.utcnow().isoformat()
            }
        
        results = {
            "curriculum_items": len(curriculum),
            "updates_applied": {},
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Update ContentCurator priorities
        if update_curator and self.curator:
            curator_updates = self._update_curator_priorities(curriculum)
            results["updates_applied"]["curator"] = curator_updates
        
        # Update LearningScheduler source priorities
        if update_scheduler:
            scheduler_updates = self._update_scheduler_priorities(curriculum)
            results["updates_applied"]["scheduler"] = scheduler_updates
        
        logger.info(f"✅ Applied curriculum: {len(curriculum)} items")
        return results
    
    def _update_curator_priorities(self, curriculum: List[CurriculumItem]) -> Dict[str, Any]:
        """Update ContentCurator content priorities based on curriculum"""
        if not self.curator:
            return {"status": "skipped", "reason": "No curator instance"}
        
        updates = {}
        
        for item in curriculum:
            # Update content priority for this topic
            topic_key = item.topic.lower()
            self.curator.content_priorities[topic_key] = item.priority
            
            # Also update source quality if curriculum recommends this source
            if item.priority > 0.7:  # High priority
                current_quality = self.curator.source_quality_scores.get(item.source, 0.5)
                # Boost source quality slightly based on curriculum priority
                new_quality = min(1.0, current_quality + (item.priority - 0.7) * 0.2)
                self.curator.update_source_quality(item.source, new_quality)
                updates[item.source] = {
                    "old_quality": current_quality,
                    "new_quality": new_quality,
                    "reason": f"Curriculum priority: {item.priority:.2f}"
                }
        
        return {
            "status": "success",
            "topics_updated": len(curriculum),
            "sources_updated": len(updates),
            "updates": updates
        }
    
    def _update_scheduler_priorities(self, curriculum: List[CurriculumItem]) -> Dict[str, Any]:
        """Update LearningScheduler source priorities based on curriculum"""
        try:
            import backend.api.main as main_module
            scheduler = main_module.learning_scheduler
            
            if not scheduler:
                return {"status": "skipped", "reason": "No scheduler instance"}
            
            # Group curriculum items by source
            source_priorities: Dict[str, float] = {}
            for item in curriculum:
                if item.source not in source_priorities:
                    source_priorities[item.source] = []
                source_priorities[item.source].append(item.priority)
            
            # Calculate average priority per source
            source_avg_priorities = {
                source: sum(priorities) / len(priorities)
                for source, priorities in source_priorities.items()
            }
            
            # Update scheduler source priorities (if scheduler has this capability)
            # Note: This is a placeholder - actual implementation depends on scheduler API
            updates = {}
            for source, avg_priority in source_avg_priorities.items():
                # If scheduler has source_priorities attribute, update it
                if hasattr(scheduler, 'source_priorities'):
                    scheduler.source_priorities[source] = avg_priority
                    updates[source] = avg_priority
                elif hasattr(scheduler, 'content_curator') and scheduler.content_curator:
                    # Update via content curator
                    scheduler.content_curator.update_source_quality(source, avg_priority)
                    updates[source] = avg_priority
            
            return {
                "status": "success",
                "sources_updated": len(updates),
                "updates": updates
            }
        except Exception as e:
            logger.warning(f"Failed to update scheduler priorities: {e}")
            return {"status": "error", "error": str(e)}


# Global applier instance
_curriculum_applier_instance: Optional[CurriculumApplier] = None


def get_curriculum_applier(curator: Optional[ContentCurator] = None) -> CurriculumApplier:
    """Get global CurriculumApplier instance"""
    global _curriculum_applier_instance
    if _curriculum_applier_instance is None:
        _curriculum_applier_instance = CurriculumApplier(curator=curator)
    elif curator and _curriculum_applier_instance.curator is None:
        _curriculum_applier_instance.curator = curator
    return _curriculum_applier_instance

