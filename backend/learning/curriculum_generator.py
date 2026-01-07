"""
Curriculum Generator for Meta-Learning (Stage 2, Phase 2)

Generates optimal learning order based on learning effectiveness analysis.
This enables curriculum learning - learning topics in the order that maximizes improvement.

Part of Stage 2: Meta-Learning - "AI improves HOW it learns"
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime

from backend.learning.learning_pattern_analyzer import (
    get_learning_pattern_analyzer,
    LearningEffectiveness,
    CurriculumItem
)
from backend.validators.self_improvement import get_self_improvement_analyzer

logger = logging.getLogger(__name__)


class CurriculumGenerator:
    """
    Generates optimal learning curriculum based on:
    1. Learning effectiveness (which topics provide most improvement)
    2. Knowledge gaps (topics with high failure rates)
    3. Source quality (retention-based trust scores)
    """
    
    def __init__(self):
        self.pattern_analyzer = get_learning_pattern_analyzer()
        self.self_improvement = get_self_improvement_analyzer()
        logger.info("CurriculumGenerator initialized")
    
    def generate_curriculum(
        self,
        days: int = 30,
        max_items: int = 20
    ) -> List[CurriculumItem]:
        """
        Generate optimal learning curriculum
        
        Args:
            days: Number of days to analyze
            max_items: Maximum number of curriculum items to generate
        
        Returns:
            List of CurriculumItem objects, sorted by priority (descending)
        """
        logger.info(f"📚 Generating learning curriculum (max {max_items} items)...")
        
        curriculum_items = []
        
        # Factor 1: Learning effectiveness (topics that provide most improvement)
        effectiveness_list = self.pattern_analyzer.get_top_effective_topics(days=days, top_n=10)
        
        for effectiveness in effectiveness_list:
            priority = min(1.0, 0.5 + effectiveness.improvement * 2.0)  # Map improvement to priority
            curriculum_items.append(CurriculumItem(
                topic=effectiveness.topic,
                source=effectiveness.source,
                priority=priority,
                reason=f"High improvement: {effectiveness.improvement:.1%} validation improvement",
                estimated_improvement=effectiveness.improvement,
                knowledge_gap_urgency=0.5  # Will be updated by knowledge gaps
            ))
        
        # Factor 2: Knowledge gaps (topics with high failure rates)
        knowledge_gaps = self.self_improvement.get_knowledge_gaps_from_failures(days=days)
        
        for gap in knowledge_gaps:
            # Check if topic already in curriculum
            existing_item = next(
                (item for item in curriculum_items if item.topic.lower() == gap.get("topics", [""])[0].lower()),
                None
            )
            
            if existing_item:
                # Update urgency
                existing_item.knowledge_gap_urgency = gap.get("priority", 0.5)
                existing_item.priority = min(1.0, existing_item.priority + 0.2)  # Boost priority
                existing_item.reason += f" + High knowledge gap urgency"
            else:
                # Add new curriculum item
                topic = gap.get("topics", ["unknown"])[0]
                curriculum_items.append(CurriculumItem(
                    topic=topic,
                    source=gap.get("suggested_source", "unknown"),
                    priority=gap.get("priority", 0.5),
                    reason=f"Knowledge gap: {gap.get('reason', 'High failure rate')}",
                    estimated_improvement=0.1,  # Estimate based on gap priority
                    knowledge_gap_urgency=gap.get("priority", 0.5)
                ))
        
        # Factor 3: Source quality (from Phase 1 - retention-based trust)
        # Boost priority for high-trust sources
        try:
            from backend.learning.source_trust_calculator import get_source_trust_calculator
            trust_calculator = get_source_trust_calculator()
            retention_rates = self.pattern_analyzer.usage_tracker.get_source_retention_rates(days=days)
            
            for item in curriculum_items:
                source_retention = retention_rates.get(item.source, 0.0)
                if source_retention > 0.20:  # High retention
                    item.priority = min(1.0, item.priority + 0.1)
                    item.reason += f" + High source retention ({source_retention:.0%})"
        except Exception as e:
            logger.debug(f"Could not apply source trust boost: {e}")
        
        # Sort by priority (descending)
        curriculum_items.sort(key=lambda x: x.priority, reverse=True)
        
        # Limit to max_items
        curriculum_items = curriculum_items[:max_items]
        
        logger.info(f"✅ Generated curriculum with {len(curriculum_items)} items")
        return curriculum_items
    
    def get_curriculum_summary(self, days: int = 30) -> Dict[str, Any]:
        """
        Get summary of learning curriculum
        
        Returns:
            Dictionary with curriculum summary and recommendations
        """
        curriculum = self.generate_curriculum(days=days)
        
        # Group by source
        by_source: Dict[str, List[CurriculumItem]] = {}
        for item in curriculum:
            if item.source not in by_source:
                by_source[item.source] = []
            by_source[item.source].append(item)
        
        # Calculate statistics
        avg_priority = sum(item.priority for item in curriculum) / len(curriculum) if curriculum else 0.0
        avg_improvement = sum(item.estimated_improvement for item in curriculum) / len(curriculum) if curriculum else 0.0
        
        return {
            "total_items": len(curriculum),
            "avg_priority": avg_priority,
            "avg_estimated_improvement": avg_improvement,
            "top_5_topics": [
                {
                    "topic": item.topic,
                    "source": item.source,
                    "priority": item.priority,
                    "reason": item.reason
                }
                for item in curriculum[:5]
            ],
            "by_source": {
                source: len(items)
                for source, items in by_source.items()
            },
            "timestamp": datetime.utcnow().isoformat()
        }


# Global generator instance
_curriculum_generator_instance: Optional[CurriculumGenerator] = None


def get_curriculum_generator() -> CurriculumGenerator:
    """Get global CurriculumGenerator instance"""
    global _curriculum_generator_instance
    if _curriculum_generator_instance is None:
        _curriculum_generator_instance = CurriculumGenerator()
    return _curriculum_generator_instance

