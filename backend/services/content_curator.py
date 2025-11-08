"""
Content Curator for StillMe
Prioritizes and optimizes learning content based on quality and effectiveness
Includes Pre-Filter mechanism to reduce costs by filtering before embedding
"""

from typing import List, Dict, Any, Optional, Tuple
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

# Pre-Filter Configuration
MINIMUM_CONTENT_LENGTH = 150  # Minimum characters (reduced from 500 to allow shorter summaries)
KEYWORD_SCORING_THRESHOLD = 0.5  # Minimum keyword score to pass filter

# Important keywords for StillMe's mission (weighted)
# Enhanced with keywords for new sources (arXiv, CrossRef, Wikipedia)
IMPORTANT_KEYWORDS = {
    # High priority (weight: 1.0)
    "đạo đức": 1.0, "ethics": 1.0, "ethical": 1.0,
    "minh bạch": 1.0, "transparency": 1.0, "transparent": 1.0,
    "quản trị ai": 1.0, "ai governance": 1.0, "governance": 1.0,
    "rag": 1.0, "retrieval-augmented": 1.0,
    "spice": 1.0, "self-play": 1.0, "self-evolving": 1.0,
    "stillme": 1.0,
    # Research & Academic (for arXiv, CrossRef)
    "llm eval": 1.0, "llm evaluation": 1.0, "evaluation": 1.0,
    "safety": 1.0, "security": 1.0,
    "citation": 1.0, "citation graph": 1.0,
    # Medium priority (weight: 0.7)
    "machine learning": 0.7, "deep learning": 0.7, "neural network": 0.7,
    "artificial intelligence": 0.7, "ai system": 0.7,
    "vector database": 0.7, "embedding": 0.7,
    "open source": 0.7, "open-source": 0.7,
    "research": 0.7, "paper": 0.7, "publication": 0.7,
    "arxiv": 0.7, "crossref": 0.7,
    # Lower priority (weight: 0.5)
    "algorithm": 0.5, "model": 0.5, "training": 0.5,
    "data": 0.5, "dataset": 0.5,
    "method": 0.5, "approach": 0.5, "framework": 0.5
}

class ContentCurator:
    """Curates and prioritizes learning content with Pre-Filter for cost optimization"""
    
    def __init__(self):
        self.source_quality_scores: Dict[str, float] = {}
        self.content_priorities: Dict[str, float] = {}
        logger.info("Content Curator initialized with Pre-Filter")
    
    def pre_filter_content(self, content_list: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        Pre-Filter content BEFORE embedding to reduce costs
        
        Filters based on:
        1. Minimum content length (MINIMUM_CONTENT_LENGTH)
        2. Keyword scoring (KEYWORD_SCORING_THRESHOLD)
        
        Args:
            content_list: List of content items to filter
            
        Returns:
            Tuple of (filtered_content, rejected_content)
        """
        if not content_list:
            return [], []
        
        filtered = []
        rejected = []
        
        for content in content_list:
            title = content.get("title", "")
            summary = content.get("summary", "")
            full_text = f"{title} {summary}"
            content_length = len(full_text)
            
            # Filter 1: Minimum content length
            if content_length < MINIMUM_CONTENT_LENGTH:
                rejected.append({
                    **content,
                    "rejection_reason": f"Content too short ({content_length} chars < {MINIMUM_CONTENT_LENGTH})"
                })
                continue
            
            # Filter 2: Keyword scoring
            keyword_score = self._calculate_keyword_score(full_text)
            if keyword_score < KEYWORD_SCORING_THRESHOLD:
                rejected.append({
                    **content,
                    "rejection_reason": f"Low keyword score ({keyword_score:.2f} < {KEYWORD_SCORING_THRESHOLD})",
                    "keyword_score": keyword_score
                })
                continue
            
            # Passed both filters
            filtered.append({
                **content,
                "keyword_score": keyword_score,
                "content_length": content_length
            })
        
        logger.info(
            f"Pre-Filter: {len(filtered)}/{len(content_list)} passed. "
            f"Rejected {len(rejected)} items (length: {sum(1 for r in rejected if 'too short' in r.get('rejection_reason', ''))}, "
            f"keyword: {sum(1 for r in rejected if 'Low keyword' in r.get('rejection_reason', ''))})"
        )
        
        return filtered, rejected
    
    def _calculate_keyword_score(self, text: str) -> float:
        """
        Calculate keyword score based on important keywords
        
        Args:
            text: Text to score (title + summary)
            
        Returns:
            Score from 0.0 to 1.0
        """
        text_lower = text.lower()
        total_score = 0.0
        matches = 0
        
        for keyword, weight in IMPORTANT_KEYWORDS.items():
            if keyword.lower() in text_lower:
                total_score += weight
                matches += 1
        
        # Normalize: divide by max possible score (if all high-priority keywords matched)
        # Use average weight of matched keywords, capped at 1.0
        if matches == 0:
            return 0.0
        
        # Average score per match, normalized
        avg_score = total_score / matches
        normalized = min(1.0, avg_score)
        
        return normalized
    
    def prioritize_learning_content(self, 
                                   content_list: List[Dict[str, Any]],
                                   knowledge_gaps: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """Prioritize content based on multiple factors
        
        Args:
            content_list: List of content items to prioritize (should be pre-filtered)
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
    
    def calculate_importance_score(self, content: Dict[str, Any]) -> float:
        """
        Calculate importance score for knowledge entry
        
        Factors:
        1. Keyword relevance (AI, ethics, StillMe, SPICE, RAG)
        2. Content length (longer = more detailed = higher importance)
        3. Source quality
        
        Returns:
            Importance score from 0.0 to 1.0
        """
        title = content.get("title", "")
        summary = content.get("summary", "")
        full_text = f"{title} {summary}"
        
        # Factor 1: Keyword score (same as pre-filter)
        keyword_score = self._calculate_keyword_score(full_text)
        
        # Factor 2: Content length (normalized)
        content_length = len(full_text)
        length_score = min(1.0, content_length / 2000.0)  # 2000 chars = max score
        
        # Factor 3: Source quality
        source = content.get("source", "")
        source_score = self.source_quality_scores.get(source, 0.5)
        
        # Weighted combination
        importance = (
            keyword_score * 0.5 +  # Keyword relevance is most important
            length_score * 0.3 +   # Length indicates detail
            source_score * 0.2     # Source quality matters
        )
        
        return min(1.0, importance)
    
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

