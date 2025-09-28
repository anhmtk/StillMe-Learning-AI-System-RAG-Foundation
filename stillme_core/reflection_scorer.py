"""Reflection Scorer for StillMe Framework"""

import logging
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)

class ScoringCriteria(Enum):
    RELEVANCE = "relevance"
    ACCURACY = "accuracy"
    COMPLETENESS = "completeness"
    CLARITY = "clarity"
    USEFULNESS = "usefulness"

@dataclass
class Score:
    """Score record"""
    criteria: ScoringCriteria
    value: float
    weight: float
    explanation: str
    timestamp: datetime

@dataclass
class ReflectionScore:
    """Reflection score record"""
    score_id: str
    reflection_id: str
    overall_score: float
    individual_scores: List[Score]
    confidence: float
    timestamp: datetime
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

@dataclass
class ScoringResult:
    """Scoring result record"""
    result_id: str
    reflection_id: str
    overall_score: float
    individual_scores: List[Score]
    confidence: float
    recommendations: List[str]
    timestamp: datetime
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}
        if self.recommendations is None:
            self.recommendations = []

class ReflectionScorer:
    """Reflection scorer for StillMe Framework"""
    
    def __init__(self):
        self.logger = logger
        self.scores: List[ReflectionScore] = []
        self.scoring_weights = self._initialize_scoring_weights()
        self.logger.info("✅ ReflectionScorer initialized")
    
    def _initialize_scoring_weights(self) -> Dict[ScoringCriteria, float]:
        """Initialize scoring weights"""
        return {
            ScoringCriteria.RELEVANCE: 0.25,
            ScoringCriteria.ACCURACY: 0.30,
            ScoringCriteria.COMPLETENESS: 0.20,
            ScoringCriteria.CLARITY: 0.15,
            ScoringCriteria.USEFULNESS: 0.10
        }
    
    def score_reflection(self, 
                        reflection_id: str,
                        content: str,
                        context: Dict[str, Any] = None) -> ReflectionScore:
        """Score a reflection"""
        try:
            score_id = f"score_{len(self.scores) + 1}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            # Calculate individual scores
            individual_scores = []
            for criteria in ScoringCriteria:
                score_value = self._calculate_criteria_score(criteria, content, context)
                weight = self.scoring_weights[criteria]
                explanation = self._get_score_explanation(criteria, score_value)
                
                score = Score(
                    criteria=criteria,
                    value=score_value,
                    weight=weight,
                    explanation=explanation,
                    timestamp=datetime.now()
                )
                individual_scores.append(score)
            
            # Calculate overall score
            overall_score = sum(score.value * score.weight for score in individual_scores)
            
            # Calculate confidence
            confidence = self._calculate_confidence(individual_scores)
            
            reflection_score = ReflectionScore(
                score_id=score_id,
                reflection_id=reflection_id,
                overall_score=overall_score,
                individual_scores=individual_scores,
                confidence=confidence,
                timestamp=datetime.now(),
                metadata={
                    "content_length": len(content),
                    "context": context or {}
                }
            )
            
            self.scores.append(reflection_score)
            self.logger.info(f"📊 Reflection scored: {overall_score:.2f} (confidence: {confidence:.2f})")
            return reflection_score
            
        except Exception as e:
            self.logger.error(f"❌ Failed to score reflection: {e}")
            raise
    
    def _calculate_criteria_score(self, criteria: ScoringCriteria, content: str, context: Dict[str, Any] = None) -> float:
        """Calculate score for specific criteria"""
        try:
            if criteria == ScoringCriteria.RELEVANCE:
                # Simple relevance scoring based on content length and keywords
                base_score = min(1.0, len(content) / 100)  # Normalize by content length
                if context and "topic" in context:
                    if context["topic"].lower() in content.lower():
                        base_score += 0.2
                return min(1.0, base_score)
            
            elif criteria == ScoringCriteria.ACCURACY:
                # Simple accuracy scoring (in real implementation, this would be more sophisticated)
                accuracy_indicators = ["fact", "evidence", "research", "study", "data"]
                accuracy_count = sum(1 for indicator in accuracy_indicators if indicator in content.lower())
                return min(1.0, accuracy_count * 0.2)
            
            elif criteria == ScoringCriteria.COMPLETENESS:
                # Simple completeness scoring
                completeness_indicators = ["because", "therefore", "however", "furthermore", "additionally"]
                completeness_count = sum(1 for indicator in completeness_indicators if indicator in content.lower())
                return min(1.0, completeness_count * 0.15 + 0.5)
            
            elif criteria == ScoringCriteria.CLARITY:
                # Simple clarity scoring
                clarity_indicators = ["clear", "obvious", "simple", "understand", "explain"]
                clarity_count = sum(1 for indicator in clarity_indicators if indicator in content.lower())
                return min(1.0, clarity_count * 0.1 + 0.6)
            
            elif criteria == ScoringCriteria.USEFULNESS:
                # Simple usefulness scoring
                usefulness_indicators = ["help", "useful", "benefit", "improve", "solve"]
                usefulness_count = sum(1 for indicator in usefulness_indicators if indicator in content.lower())
                return min(1.0, usefulness_count * 0.15 + 0.5)
            
            else:
                return 0.5  # Default score
                
        except Exception as e:
            self.logger.error(f"❌ Failed to calculate criteria score: {e}")
            return 0.0
    
    def _get_score_explanation(self, criteria: ScoringCriteria, score_value: float) -> str:
        """Get explanation for score"""
        if score_value >= 0.8:
            return f"Excellent {criteria.value}"
        elif score_value >= 0.6:
            return f"Good {criteria.value}"
        elif score_value >= 0.4:
            return f"Fair {criteria.value}"
        else:
            return f"Poor {criteria.value}"
    
    def _calculate_confidence(self, individual_scores: List[Score]) -> float:
        """Calculate confidence in the scoring"""
        try:
            # Simple confidence calculation based on score consistency
            scores = [score.value for score in individual_scores]
            if not scores:
                return 0.0
            
            # Calculate variance
            mean_score = sum(scores) / len(scores)
            variance = sum((score - mean_score) ** 2 for score in scores) / len(scores)
            
            # Convert variance to confidence (lower variance = higher confidence)
            confidence = max(0.0, 1.0 - variance)
            return confidence
            
        except Exception as e:
            self.logger.error(f"❌ Failed to calculate confidence: {e}")
            return 0.5
    
    def get_scores_by_reflection(self, reflection_id: str) -> List[ReflectionScore]:
        """Get scores for a specific reflection"""
        return [s for s in self.scores if s.reflection_id == reflection_id]
    
    def get_average_score(self, criteria: ScoringCriteria = None) -> float:
        """Get average score"""
        try:
            if not self.scores:
                return 0.0
            
            if criteria:
                # Get average for specific criteria
                criteria_scores = []
                for score in self.scores:
                    for individual_score in score.individual_scores:
                        if individual_score.criteria == criteria:
                            criteria_scores.append(individual_score.value)
                
                return sum(criteria_scores) / len(criteria_scores) if criteria_scores else 0.0
            else:
                # Get overall average
                return sum(score.overall_score for score in self.scores) / len(self.scores)
                
        except Exception as e:
            self.logger.error(f"❌ Failed to get average score: {e}")
            return 0.0
    
    def get_scoring_summary(self) -> Dict[str, Any]:
        """Get scoring summary"""
        try:
            total_scores = len(self.scores)
            
            if total_scores == 0:
                return {
                    "total_scores": 0,
                    "average_overall_score": 0.0,
                    "average_confidence": 0.0,
                    "scores_by_criteria": {},
                    "timestamp": datetime.now().isoformat()
                }
            
            # Calculate averages
            average_overall_score = sum(score.overall_score for score in self.scores) / total_scores
            average_confidence = sum(score.confidence for score in self.scores) / total_scores
            
            # Calculate scores by criteria
            scores_by_criteria = {}
            for criteria in ScoringCriteria:
                criteria_scores = []
                for score in self.scores:
                    for individual_score in score.individual_scores:
                        if individual_score.criteria == criteria:
                            criteria_scores.append(individual_score.value)
                
                if criteria_scores:
                    scores_by_criteria[criteria.value] = sum(criteria_scores) / len(criteria_scores)
                else:
                    scores_by_criteria[criteria.value] = 0.0
            
            return {
                "total_scores": total_scores,
                "average_overall_score": average_overall_score,
                "average_confidence": average_confidence,
                "scores_by_criteria": scores_by_criteria,
                "scoring_weights": {k.value: v for k, v in self.scoring_weights.items()},
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"❌ Failed to get scoring summary: {e}")
            return {"error": str(e)}
    
    def score_with_recommendations(self, 
                                  reflection_id: str,
                                  content: str,
                                  context: Dict[str, Any] = None) -> ScoringResult:
        """Score reflection with recommendations"""
        try:
            # Get basic score
            reflection_score = self.score_reflection(reflection_id, content, context)
            
            # Generate recommendations
            recommendations = self._generate_recommendations(reflection_score)
            
            # Create scoring result
            result = ScoringResult(
                result_id=f"result_{len(self.scores) + 1}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                reflection_id=reflection_id,
                overall_score=reflection_score.overall_score,
                individual_scores=reflection_score.individual_scores,
                confidence=reflection_score.confidence,
                recommendations=recommendations,
                timestamp=datetime.now(),
                metadata=reflection_score.metadata
            )
            
            self.logger.info(f"📊 Scoring with recommendations completed: {len(recommendations)} recommendations")
            return result
            
        except Exception as e:
            self.logger.error(f"❌ Failed to score with recommendations: {e}")
            raise
    
    def _generate_recommendations(self, reflection_score: ReflectionScore) -> List[str]:
        """Generate recommendations based on score"""
        try:
            recommendations = []
            
            # Check individual scores and generate recommendations
            for score in reflection_score.individual_scores:
                if score.value < 0.6:  # Low score
                    if score.criteria == ScoringCriteria.RELEVANCE:
                        recommendations.append("Improve relevance by focusing more on the main topic")
                    elif score.criteria == ScoringCriteria.ACCURACY:
                        recommendations.append("Add more factual evidence and research to support claims")
                    elif score.criteria == ScoringCriteria.COMPLETENESS:
                        recommendations.append("Provide more comprehensive coverage of the topic")
                    elif score.criteria == ScoringCriteria.CLARITY:
                        recommendations.append("Improve clarity by using simpler language and better structure")
                    elif score.criteria == ScoringCriteria.USEFULNESS:
                        recommendations.append("Make the content more actionable and practical")
            
            # Overall recommendations
            if reflection_score.overall_score < 0.7:
                recommendations.append("Overall quality needs improvement - consider revising the content")
            
            if reflection_score.confidence < 0.6:
                recommendations.append("Scoring confidence is low - consider getting additional feedback")
            
            return recommendations
            
        except Exception as e:
            self.logger.error(f"❌ Failed to generate recommendations: {e}")
            return []
    
    def clear_scores(self):
        """Clear all scores"""
        self.scores.clear()
        self.logger.info("🧹 All reflection scores cleared")

# Global reflection scorer instance
_reflection_scorer_instance = None

def get_default_scorer() -> ReflectionScorer:
    """Get default reflection scorer instance"""
    global _reflection_scorer_instance
    if _reflection_scorer_instance is None:
        _reflection_scorer_instance = ReflectionScorer()
    return _reflection_scorer_instance
