"""
Self-Improvement Mechanism
Analyzes validation patterns and suggests improvements for StillMe

This module:
1. Analyzes validation patterns from ValidationMetricsTracker
2. Identifies knowledge gaps from validation failures
3. Suggests learning content to improve performance
4. Provides feedback loop from validation → learning
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta

from stillme_core.validation.validation_metrics_tracker import get_validation_tracker, ValidationPattern

logger = logging.getLogger(__name__)


class SelfImprovementAnalyzer:
    """
    Analyzes validation patterns and suggests improvements
    """
    
    def __init__(self):
        self.tracker = get_validation_tracker()
    
    def analyze_and_suggest(self, days: int = 7) -> Dict[str, Any]:
        """
        Analyze validation patterns and suggest improvements
        
        Args:
            days: Number of days to analyze
            
        Returns:
            Dictionary with analysis and suggestions
        """
        # Get patterns
        patterns = self.tracker.analyze_patterns(days=days)
        
        # Get failure rates by category
        failure_rates = self.tracker.get_failure_rate_by_category(days=days)
        
        # Generate learning suggestions
        learning_suggestions = self._generate_learning_suggestions(patterns, failure_rates)
        
        # Generate improvement recommendations
        improvement_recommendations = self._generate_improvement_recommendations(patterns)
        
        return {
            "analysis_period_days": days,
            "patterns_detected": len(patterns),
            "patterns": [self._pattern_to_dict(p) for p in patterns],
            "failure_rates_by_category": failure_rates,
            "learning_suggestions": learning_suggestions,
            "improvement_recommendations": improvement_recommendations,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    def _pattern_to_dict(self, pattern: ValidationPattern) -> Dict[str, Any]:
        """Convert ValidationPattern to dictionary"""
        return {
            "type": pattern.pattern_type,
            "frequency": pattern.frequency,
            "affected_categories": pattern.affected_categories,
            "suggested_improvement": pattern.suggested_improvement
        }
    
    def _generate_learning_suggestions(
        self,
        patterns: List[ValidationPattern],
        failure_rates: Dict[str, float]
    ) -> List[Dict[str, str]]:
        """
        Generate learning suggestions based on validation patterns
        
        Returns:
            List of learning suggestions with topics and sources
        """
        suggestions = []
        
        # Analyze patterns for knowledge gaps
        for pattern in patterns:
            if pattern.pattern_type == "missing_citation":
                # Missing citations often indicate knowledge gaps
                suggestions.append({
                    "topic": "Citation and source attribution best practices",
                    "source": "Wikipedia: Citation, Academic writing",
                    "priority": "high",
                    "reason": f"Missing citations detected {pattern.frequency} times in categories: {', '.join(pattern.affected_categories)}"
                })
            
            elif pattern.pattern_type == "low_overlap":
                # Low overlap indicates RAG retrieval issues or knowledge gaps
                suggestions.append({
                    "topic": "RAG retrieval optimization and semantic search",
                    "source": "arXiv: cs.AI, cs.IR (Information Retrieval)",
                    "priority": "medium",
                    "reason": f"Low evidence overlap detected {pattern.frequency} times. May need better RAG retrieval or more relevant knowledge."
                })
            
            elif pattern.pattern_type == "hallucination":
                # Hallucinations indicate need for better grounding
                suggestions.append({
                    "topic": "Hallucination reduction techniques in RAG systems",
                    "source": "arXiv: cs.AI, cs.CL (Computation and Language)",
                    "priority": "high",
                    "reason": f"Hallucinations detected {pattern.frequency} times. Need stronger grounding mechanisms."
                })
        
        # Analyze failure rates by category
        for category, rate in failure_rates.items():
            if rate > 0.3:  # High failure rate (>30%)
                suggestions.append({
                    "topic": f"Knowledge about {category} topics",
                    "source": "Wikipedia, arXiv, or domain-specific sources",
                    "priority": "high",
                    "reason": f"High failure rate ({rate:.1%}) for {category} questions. Need more knowledge in this domain."
                })
        
        return suggestions
    
    def _generate_improvement_recommendations(
        self,
        patterns: List[ValidationPattern]
    ) -> List[Dict[str, str]]:
        """
        Generate improvement recommendations for validation logic
        
        Returns:
            List of improvement recommendations
        """
        recommendations = []
        
        for pattern in patterns:
            if pattern.pattern_type == "missing_citation":
                recommendations.append({
                    "component": "CitationRequired validator",
                    "recommendation": "Strengthen citation detection logic or improve citation instruction in prompts",
                    "priority": "high"
                })
            
            elif pattern.pattern_type == "low_overlap":
                recommendations.append({
                    "component": "EvidenceOverlap validator",
                    "recommendation": "Review overlap threshold or improve RAG retrieval relevance",
                    "priority": "medium"
                })
            
            elif pattern.pattern_type == "missing_uncertainty":
                recommendations.append({
                    "component": "ConfidenceValidator",
                    "recommendation": "Improve uncertainty detection or adjust confidence thresholds",
                    "priority": "medium"
                })
            
            elif pattern.pattern_type == "anthropomorphic_language":
                recommendations.append({
                    "component": "EgoNeutralityValidator / RewriteLLM",
                    "recommendation": "Strengthen forbidden terms filtering or improve identity prompts",
                    "priority": "high"
                })
        
        return recommendations
    
    def get_knowledge_gaps_from_failures(self, days: int = 7) -> List[Dict[str, Any]]:
        """
        Extract knowledge gaps from validation failures
        
        This analyzes failed validations to identify topics where StillMe lacks knowledge
        
        Returns:
            List of knowledge gaps with topics and suggested sources
        """
        from datetime import timezone
        
        cutoff_time = datetime.now(timezone.utc) - timedelta(days=days)
        recent_failures = [
            r for r in self.tracker._records
            if datetime.fromisoformat(r.timestamp) >= cutoff_time
            and not r.passed
            and r.context_docs_count == 0  # No context = knowledge gap
        ]
        
        if not recent_failures:
            return []
        
        # Extract topics from questions (simple keyword extraction)
        knowledge_gaps = []
        for record in recent_failures:
            # Simple topic extraction (can be improved with NLP)
            question_lower = record.question.lower()
            
            # Extract potential topics (this is a simple heuristic)
            topics = []
            if "geneva" in question_lower or "1954" in question_lower:
                topics.append("Geneva Conference 1954")
            if "bretton woods" in question_lower or "1944" in question_lower:
                topics.append("Bretton Woods Conference 1944")
            if "popper" in question_lower or "kuhn" in question_lower:
                topics.append("Philosophy of Science (Popper, Kuhn)")
            
            if topics:
                knowledge_gaps.append({
                    "question": record.question[:200],
                    "topics": topics,
                    "suggested_sources": ["Wikipedia", "Stanford Encyclopedia of Philosophy", "Academic papers"],
                    "priority": "high" if "missing_citation" in record.validation_reasons else "medium"
                })
        
        return knowledge_gaps


# Global analyzer instance
_analyzer = SelfImprovementAnalyzer()


def get_self_improvement_analyzer() -> SelfImprovementAnalyzer:
    """Get global self-improvement analyzer instance"""
    return _analyzer

