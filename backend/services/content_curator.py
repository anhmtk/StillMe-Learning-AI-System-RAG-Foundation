"""
Content Curator for StillMe
Prioritizes and optimizes learning content based on quality and effectiveness
"""

from typing import List, Dict, Any, Optional
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class ContentCurator:
    """Curates and prioritizes learning content"""
    
    def __init__(self):
        self.source_quality_scores: Dict[str, float] = {}
        self.content_priorities: Dict[str, float] = {}
        logger.info("Content Curator initialized")
    
    def prioritize_learning_content(self, 
                                   content_list: List[Dict[str, Any]],
                                   knowledge_gaps: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """Prioritize content based on multiple factors
        
        Args:
            content_list: List of content items to prioritize
            knowledge_gaps: Topics with knowledge gaps (higher priority)
            
        Returns:
            Sorted list by priority
        """
        if not content_list:
            return []
        
        knowledge_gaps_set = set(knowledge_gaps or [])
        
        # Score each content item
        scored_content = []
        for content in content_list:
            score = self._calculate_priority_score(content, knowledge_gaps_set)
            scored_content.append({
                **content,
                "priority_score": score
            })
        
        # Sort by priority (highest first)
        scored_content.sort(key=lambda x: x["priority_score"], reverse=True)
        
        logger.info(f"Prioritized {len(scored_content)} content items")
        return scored_content
    
    def _calculate_priority_score(self, content: Dict[str, Any], knowledge_gaps: set) -> float:
        """Calculate priority score for content"""
        score = 0.5  # Base score
        
        # Factor 1: Source quality
        source = content.get("source", "")
        if source in self.source_quality_scores:
            score += self.source_quality_scores[source] * 0.3
        
        # Factor 2: Relevance to knowledge gaps
        title = content.get("title", "").lower()
        summary = content.get("summary", "").lower()
        content_text = f"{title} {summary}"
        
        for gap in knowledge_gaps:
            if gap.lower() in content_text:
                score += 0.2  # Boost if related to gap
        
        # Factor 3: Recency (newer = slightly higher)
        published = content.get("published")
        if published:
            try:
                pub_date = datetime.fromisoformat(published.replace("Z", "+00:00"))
                days_old = (datetime.now(pub_date.tzinfo) - pub_date).days
                if days_old < 7:
                    score += 0.1  # Boost for recent content
            except:
                pass
        
        return min(1.0, score)  # Cap at 1.0
    
    def update_source_quality(self, source: str, quality_score: float):
        """Update quality score for a source
        
        Args:
            source: RSS feed URL or source name
            quality_score: Quality score (0.0-1.0)
        """
        self.source_quality_scores[source] = quality_score
        logger.info(f"Updated quality score for {source}: {quality_score}")
    
    def optimize_rss_sources(self, sources: List[str]) -> List[str]:
        """Optimize RSS source list based on quality scores
        
        Args:
            sources: List of RSS feed URLs
            
        Returns:
            Optimized list (sorted by quality, filtered by threshold)
        """
        # Score sources
        scored_sources = []
        for source in sources:
            quality = self.source_quality_scores.get(source, 0.5)  # Default 0.5
            scored_sources.append({
                "source": source,
                "quality": quality
            })
        
        # Sort by quality (highest first)
        scored_sources.sort(key=lambda x: x["quality"], reverse=True)
        
        # Filter low-quality sources (below 0.3)
        optimized = [
            s["source"] for s in scored_sources 
            if s["quality"] >= 0.3
        ]
        
        logger.info(f"Optimized RSS sources: {len(optimized)}/{len(sources)} passed quality threshold")
        return optimized
    
    def get_curation_stats(self) -> Dict[str, Any]:
        """Get curation statistics"""
        return {
            "sources_tracked": len(self.source_quality_scores),
            "average_source_quality": sum(self.source_quality_scores.values()) / len(self.source_quality_scores) if self.source_quality_scores else 0.0,
            "high_quality_sources": len([s for s in self.source_quality_scores.values() if s >= 0.7]),
            "low_quality_sources": len([s for s in self.source_quality_scores.values() if s < 0.3])
        }

