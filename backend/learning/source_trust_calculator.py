"""
Source Trust Calculator for Meta-Learning (Stage 2)

Calculates and updates source trust scores based on retention metrics.
This enables retention-based source trust adjustment.

Part of Stage 2: Meta-Learning - "AI improves HOW it learns"
"""

import logging
from typing import Dict, Optional, List
from datetime import datetime, timedelta

from backend.learning.document_usage_tracker import get_document_usage_tracker

# Try to import ContentCurator from both possible locations
try:
    from backend.services.content_curator import ContentCurator
except ImportError:
    try:
        from stillme_core.learning.curator import ContentCurator
    except ImportError:
        # Fallback: define a minimal type hint
        from typing import TYPE_CHECKING
        if TYPE_CHECKING:
            ContentCurator = None

logger = logging.getLogger(__name__)


class SourceTrustCalculator:
    """
    Calculates source trust scores based on retention metrics.
    
    High retention (30%+) → High trust (0.8-1.0)
    Medium retention (10-30%) → Medium trust (0.5-0.8)
    Low retention (<10%) → Low trust (0.2-0.5)
    
    Auto-updates ContentCurator.source_quality_scores based on retention.
    """
    
    def __init__(self, curator: Optional[ContentCurator] = None):
        """
        Initialize source trust calculator
        
        Args:
            curator: ContentCurator instance (optional, will get from global if not provided)
        """
        self.usage_tracker = get_document_usage_tracker()
        self.curator = curator
        logger.info("SourceTrustCalculator initialized")
    
    def calculate_trust_score(self, retention_rate: float) -> float:
        """
        Calculate trust score based on retention rate
        
        Args:
            retention_rate: Retention rate (0.0-1.0)
        
        Returns:
            Trust score (0.0-1.0)
        """
        if retention_rate >= 0.30:  # High retention (30%+)
            # Linear mapping: 0.30 → 0.8, 1.0 → 1.0
            trust = 0.8 + (retention_rate - 0.30) * (1.0 - 0.8) / (1.0 - 0.30)
            return min(1.0, trust)
        elif retention_rate >= 0.10:  # Medium retention (10-30%)
            # Linear mapping: 0.10 → 0.5, 0.30 → 0.8
            trust = 0.5 + (retention_rate - 0.10) * (0.8 - 0.5) / (0.30 - 0.10)
            return trust
        else:  # Low retention (<10%)
            # Linear mapping: 0.0 → 0.2, 0.10 → 0.5
            trust = 0.2 + retention_rate * (0.5 - 0.2) / 0.10
            return max(0.2, trust)
    
    def update_source_trust_scores(self, days: int = 30, curator: Optional[ContentCurator] = None) -> Dict[str, float]:
        """
        Update source trust scores based on retention metrics
        
        Args:
            days: Number of days to analyze
            curator: ContentCurator instance (optional)
        
        Returns:
            Dictionary mapping source name to new trust score
        """
        if curator is None:
            curator = self.curator
        
        if curator is None:
            logger.warning("No ContentCurator provided, cannot update trust scores")
            return {}
        
        # Get retention metrics
        retention_metrics = self.usage_tracker.calculate_retention_metrics(days=days)
        
        if not retention_metrics:
            logger.info("No retention metrics available, skipping trust score update")
            return {}
        
        # Calculate and update trust scores
        updated_scores: Dict[str, float] = {}
        
        for source, metrics in retention_metrics.items():
            retention_rate = metrics.get("retention_rate", 0.0)
            
            # Calculate trust score
            trust_score = self.calculate_trust_score(retention_rate)
            
            # Update ContentCurator
            curator.update_source_quality(source, trust_score)
            updated_scores[source] = trust_score
            
            logger.info(
                f"Updated source trust: {source[:50]} → "
                f"retention={retention_rate:.2%}, trust={trust_score:.2f}"
            )
        
        return updated_scores
    
    def get_recommended_sources(self, days: int = 30, min_retention: float = 0.20) -> List[str]:
        """
        Get list of recommended sources based on retention
        
        Args:
            days: Number of days to analyze
            min_retention: Minimum retention rate to recommend (default: 20%)
        
        Returns:
            List of source names with retention >= min_retention, sorted by retention (descending)
        """
        retention_metrics = self.usage_tracker.calculate_retention_metrics(days=days)
        
        recommended = [
            (source, metrics.get("retention_rate", 0.0))
            for source, metrics in retention_metrics.items()
            if metrics.get("retention_rate", 0.0) >= min_retention
        ]
        
        # Sort by retention rate (descending)
        recommended.sort(key=lambda x: x[1], reverse=True)
        
        return [source for source, _ in recommended]


# Global calculator instance (singleton pattern)
_trust_calculator_instance: Optional[SourceTrustCalculator] = None


def get_source_trust_calculator(curator: Optional[ContentCurator] = None) -> SourceTrustCalculator:
    """Get global SourceTrustCalculator instance"""
    global _trust_calculator_instance
    if _trust_calculator_instance is None:
        _trust_calculator_instance = SourceTrustCalculator(curator=curator)
    elif curator and _trust_calculator_instance.curator is None:
        _trust_calculator_instance.curator = curator
    return _trust_calculator_instance

