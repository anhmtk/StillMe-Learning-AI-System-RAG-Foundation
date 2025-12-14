"""
Epistemic Reasoning for StillMe

This module provides reasoning about WHY StillMe is uncertain,
not just THAT StillMe is uncertain.

Based on StillMe Manifesto Principle 5: "EMBRACE 'I DON'T KNOW' AS INTELLECTUAL HONESTY"
- We value HONESTY over APPEARING KNOWLEDGEABLE
- We explain WHY we don't know, WHERE the limits are, WHAT that means
- Not just "I don't know" but "I don't know BECAUSE..."

This enables StillMe to be transparent about the REASONS for uncertainty,
not just express uncertainty.
"""

import logging
from typing import List, Optional, Dict, Any
from enum import Enum

logger = logging.getLogger(__name__)


class UncertaintyReason(Enum):
    """Reasons for uncertainty"""
    LIMITED_CONTEXT = "limited_relevant_context"
    CONFLICTING_SOURCES = "conflicting_information_in_sources"
    OUTDATED_INFORMATION = "potentially_outdated_information"
    LOW_SIMILARITY = "low_similarity_between_question_and_context"
    NO_CONTEXT = "no_context_available"
    LOW_CONFIDENCE = "low_confidence_score"
    VALIDATION_WARNINGS = "validation_warnings_detected"
    TEMPORAL_RELEVANCE = "temporal_relevance_concerns"


class EpistemicReasoning:
    """
    Provides reasoning about epistemic state - WHY StillMe is uncertain.
    
    This goes beyond just expressing uncertainty to EXPLAINING the reasons
    for uncertainty, enabling deeper transparency.
    """
    
    def __init__(self):
        """Initialize epistemic reasoning"""
        pass
    
    def analyze_uncertainty_reasons(
        self,
        context_quality: Optional[float] = None,
        source_agreement: Optional[float] = None,
        temporal_relevance: Optional[float] = None,
        max_similarity: Optional[float] = None,
        confidence_score: Optional[float] = None,
        has_context: bool = False,
        has_validation_warnings: bool = False,
        conflicting_sources: bool = False
    ) -> List[UncertaintyReason]:
        """
        Analyze reasons for uncertainty based on available information.
        
        Args:
            context_quality: Quality of context (0.0-1.0), typically max_similarity
            source_agreement: Agreement between sources (0.0-1.0)
            temporal_relevance: Temporal relevance of information (0.0-1.0)
            max_similarity: Maximum similarity score (alternative to context_quality)
            confidence_score: Confidence score from validator (0.0-1.0)
            has_context: Whether context documents are available
            has_validation_warnings: Whether validation produced warnings
            conflicting_sources: Whether sources conflict
            
        Returns:
            List of UncertaintyReason enums explaining why StillMe is uncertain
        """
        reasons = []
        
        # Use max_similarity if provided, otherwise use context_quality
        similarity = max_similarity if max_similarity is not None else context_quality
        
        # Check for limited context
        if not has_context:
            reasons.append(UncertaintyReason.NO_CONTEXT)
        elif similarity is not None and similarity < 0.3:
            reasons.append(UncertaintyReason.LIMITED_CONTEXT)
        elif similarity is not None and similarity < 0.5:
            reasons.append(UncertaintyReason.LOW_SIMILARITY)
        
        # Check for conflicting sources
        if conflicting_sources or (source_agreement is not None and source_agreement < 0.5):
            reasons.append(UncertaintyReason.CONFLICTING_SOURCES)
        
        # Check for temporal relevance
        if temporal_relevance is not None and temporal_relevance < 0.7:
            reasons.append(UncertaintyReason.TEMPORAL_RELEVANCE)
        elif temporal_relevance is not None and temporal_relevance < 0.5:
            reasons.append(UncertaintyReason.OUTDATED_INFORMATION)
        
        # Check for low confidence
        if confidence_score is not None and confidence_score < 0.4:
            reasons.append(UncertaintyReason.LOW_CONFIDENCE)
        
        # Check for validation warnings
        if has_validation_warnings:
            reasons.append(UncertaintyReason.VALIDATION_WARNINGS)
        
        return reasons
    
    def explain_uncertainty(
        self,
        reasons: List[UncertaintyReason],
        detected_lang: str = "vi"
    ) -> str:
        """
        Generate human-readable explanation of uncertainty reasons.
        
        Based on StillMe Manifesto Principle 5:
        - Not just "I don't know"
        - But "I don't know BECAUSE..."
        
        Args:
            reasons: List of UncertaintyReason enums
            detected_lang: Language code (default: "vi")
            
        Returns:
            Human-readable explanation string
        """
        if not reasons:
            # No specific reasons - generic uncertainty
            if detected_lang == "vi":
                return "Mình không chắc chắn về thông tin này."
            else:
                return "I'm uncertain about this information."
        
        # Build explanation based on reasons
        if detected_lang == "vi":
            explanations = []
            
            if UncertaintyReason.NO_CONTEXT in reasons:
                explanations.append("không có ngữ cảnh liên quan")
            elif UncertaintyReason.LIMITED_CONTEXT in reasons:
                explanations.append("ngữ cảnh có độ liên quan thấp")
            elif UncertaintyReason.LOW_SIMILARITY in reasons:
                explanations.append("ngữ cảnh có độ tương đồng thấp với câu hỏi")
            
            if UncertaintyReason.CONFLICTING_SOURCES in reasons:
                explanations.append("các nguồn thông tin mâu thuẫn nhau")
            
            if UncertaintyReason.OUTDATED_INFORMATION in reasons:
                explanations.append("thông tin có thể đã lỗi thời")
            elif UncertaintyReason.TEMPORAL_RELEVANCE in reasons:
                explanations.append("thông tin có thể không còn phù hợp với thời điểm hiện tại")
            
            if UncertaintyReason.LOW_CONFIDENCE in reasons:
                explanations.append("độ tin cậy thấp")
            
            if UncertaintyReason.VALIDATION_WARNINGS in reasons:
                explanations.append("có cảnh báo từ hệ thống kiểm tra")
            
            if explanations:
                reasons_text = ", ".join(explanations)
                return f"Mình không chắc chắn về thông tin này vì: {reasons_text}."
            else:
                return "Mình không chắc chắn về thông tin này."
        else:
            # English
            explanations = []
            
            if UncertaintyReason.NO_CONTEXT in reasons:
                explanations.append("no relevant context available")
            elif UncertaintyReason.LIMITED_CONTEXT in reasons:
                explanations.append("limited relevant context")
            elif UncertaintyReason.LOW_SIMILARITY in reasons:
                explanations.append("low similarity between question and context")
            
            if UncertaintyReason.CONFLICTING_SOURCES in reasons:
                explanations.append("conflicting information in sources")
            
            if UncertaintyReason.OUTDATED_INFORMATION in reasons:
                explanations.append("potentially outdated information")
            elif UncertaintyReason.TEMPORAL_RELEVANCE in reasons:
                explanations.append("temporal relevance concerns")
            
            if UncertaintyReason.LOW_CONFIDENCE in reasons:
                explanations.append("low confidence score")
            
            if UncertaintyReason.VALIDATION_WARNINGS in reasons:
                explanations.append("validation warnings detected")
            
            if explanations:
                reasons_text = ", ".join(explanations)
                return f"I'm uncertain about this information because: {reasons_text}."
            else:
                return "I'm uncertain about this information."
    
    def get_epistemic_explanation(
        self,
        context_quality: Optional[float] = None,
        source_agreement: Optional[float] = None,
        temporal_relevance: Optional[float] = None,
        max_similarity: Optional[float] = None,
        confidence_score: Optional[float] = None,
        has_context: bool = False,
        has_validation_warnings: bool = False,
        conflicting_sources: bool = False,
        detected_lang: str = "vi"
    ) -> str:
        """
        Get complete epistemic explanation combining analysis and explanation.
        
        This is the main entry point for epistemic reasoning.
        
        Args:
            context_quality: Quality of context (0.0-1.0)
            source_agreement: Agreement between sources (0.0-1.0)
            temporal_relevance: Temporal relevance (0.0-1.0)
            max_similarity: Maximum similarity score
            confidence_score: Confidence score
            has_context: Whether context is available
            has_validation_warnings: Whether validation has warnings
            conflicting_sources: Whether sources conflict
            detected_lang: Language code
            
        Returns:
            Human-readable epistemic explanation
        """
        reasons = self.analyze_uncertainty_reasons(
            context_quality=context_quality,
            source_agreement=source_agreement,
            temporal_relevance=temporal_relevance,
            max_similarity=max_similarity,
            confidence_score=confidence_score,
            has_context=has_context,
            has_validation_warnings=has_validation_warnings,
            conflicting_sources=conflicting_sources
        )
        
        return self.explain_uncertainty(reasons, detected_lang)


# Global epistemic reasoning instance
_epistemic_reasoning: Optional[EpistemicReasoning] = None


def get_epistemic_reasoning() -> EpistemicReasoning:
    """Get global epistemic reasoning instance"""
    global _epistemic_reasoning
    if _epistemic_reasoning is None:
        _epistemic_reasoning = EpistemicReasoning()
    return _epistemic_reasoning

