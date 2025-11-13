"""
Self-Diagnosis Agent for StillMe
Identifies knowledge gaps and suggests learning focus using RAG
"""

from typing import List, Dict, Any, Optional
import logging
from backend.vector_db import RAGRetrieval

logger = logging.getLogger(__name__)

class SelfDiagnosisAgent:
    """Agent that identifies knowledge gaps and suggests improvements"""
    
    def __init__(self, rag_retrieval: Optional[RAGRetrieval] = None):
        self.rag_retrieval = rag_retrieval
        logger.info("Self-Diagnosis Agent initialized")
    
    def identify_knowledge_gaps(self, query: str, threshold: float = 0.5) -> Dict[str, Any]:
        """Identify knowledge gaps based on low similarity search results
        
        Args:
            query: Question or topic to check
            threshold: Minimum similarity score (below = gap)
            
        Returns:
            Dict with gap analysis
        """
        if not self.rag_retrieval:
            return {
                "has_gap": False,
                "reason": "RAG system not available"
            }
        
        try:
            # Retrieve context for query
            context = self.rag_retrieval.retrieve_context(
                query=query,
                knowledge_limit=5
            )
            
            # Filter by similarity threshold manually if needed
            # Note: retrieve_context doesn't support min_similarity parameter
            # Similarity filtering should be done at the search level if needed
            
            # Check if we have relevant knowledge
            knowledge_docs = context.get("knowledge_context", {}).get("documents", [])
            
            # Calculate average similarity (if distances available)
            distances = context.get("knowledge_context", {}).get("distances", [])
            avg_similarity = 1.0 - (sum(distances) / len(distances)) if distances else 1.0
            
            has_gap = len(knowledge_docs) == 0 or avg_similarity < threshold
            
            return {
                "has_gap": has_gap,
                "query": query,
                "documents_found": len(knowledge_docs),
                "average_similarity": avg_similarity,
                "threshold": threshold,
                "suggestion": self._suggest_learning_focus(query) if has_gap else None
            }
        except Exception as e:
            logger.error(f"Failed to identify knowledge gap: {e}")
            return {
                "has_gap": True,
                "error": str(e)
            }
    
    def _suggest_learning_focus(self, query: str) -> str:
        """Suggest what to learn based on gap"""
        return f"Consider learning more about: {query}. Low knowledge coverage detected."
    
    def analyze_knowledge_coverage(self, topics: List[str]) -> Dict[str, Any]:
        """Analyze coverage across multiple topics
        
        Args:
            topics: List of topics to check
            
        Returns:
            Coverage analysis per topic
        """
        coverage = {}
        gaps = []
        
        for topic in topics:
            result = self.identify_knowledge_gaps(topic)
            coverage[topic] = {
                "has_coverage": not result.get("has_gap", True),
                "similarity": result.get("average_similarity", 0.0)
            }
            if result.get("has_gap"):
                gaps.append(topic)
        
        return {
            "total_topics": len(topics),
            "covered_topics": len(topics) - len(gaps),
            "gap_topics": gaps,
            "coverage_percentage": (len(topics) - len(gaps)) / len(topics) * 100 if topics else 0,
            "details": coverage
        }
    
    def suggest_learning_focus(self, recent_queries: List[str], limit: int = 5) -> List[str]:
        """Suggest learning focus based on user query patterns
        
        Args:
            recent_queries: Recent user queries
            limit: Number of suggestions
            
        Returns:
            List of topics to learn about
        """
        if not self.rag_retrieval:
            return []
        
        # Find gaps in recent queries
        gaps = []
        for query in recent_queries[:20]:  # Check last 20 queries
            result = self.identify_knowledge_gaps(query)
            if result.get("has_gap"):
                gaps.append(query)
        
        # Return top gaps (most frequent)
        from collections import Counter
        gap_counts = Counter(gaps)
        return [topic for topic, _ in gap_counts.most_common(limit)]

