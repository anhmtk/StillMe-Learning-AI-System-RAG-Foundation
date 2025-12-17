"""
Knowledge Type Classifier - Formally categorizes knowledge claims

This classifier provides a formal taxonomy for citation policy:
- Factual Claim: Requires citation
- General Knowledge: Well-established, pre-2023, citation optional
- Reasoning: Logical inference, no citation needed
- StillMe Self-Knowledge: Uses foundational knowledge

This addresses the ambiguity in citation policy where "every factual claim is cited"
but "general knowledge" has no sources.
"""

import re
import logging
from enum import Enum
from typing import Optional, List

logger = logging.getLogger(__name__)


class KnowledgeType(Enum):
    """Formal taxonomy of knowledge types"""
    FACTUAL_CLAIM = "factual_claim"  # Requires citation [1], [2]
    GENERAL_KNOWLEDGE = "general_knowledge"  # Well-established, pre-2023, citation optional
    REASONING = "reasoning"  # Logical inference, no citation needed
    STILLME_SELF_KNOWLEDGE = "stillme_self_knowledge"  # Uses foundational knowledge


class KnowledgeTypeClassifier:
    """
    Formally classifies knowledge claims for citation policy
    
    Rules:
    1. If about StillMe → STILLME_SELF_KNOWLEDGE
    2. If has RAG context → FACTUAL_CLAIM (requires citation)
    3. If no RAG context but well-established fact → GENERAL_KNOWLEDGE
    4. If logical inference → REASONING
    """
    
    def __init__(self):
        """Initialize classifier"""
        # Well-established facts (common knowledge, pre-2023)
        self.well_established_patterns = [
            r"\b(water|nước) is (H2O|H₂O)\b",
            r"\b(2\+2|two plus two) (equals|is) (4|four)\b",
            r"\b(shakespeare|Shakespeare) (wrote|wrote)\b",
            r"\b(earth|trái đất) (orbits|quay quanh) (the sun|mặt trời)\b",
            r"\b(gravity|trọng lực) (exists|tồn tại)\b",
            r"\b(photosynthesis|quang hợp) (converts|chuyển đổi)\b",
        ]
        
        # Reasoning indicators (logical connectors, philosophical terms)
        self.reasoning_indicators = [
            r"\bif (.*) then (.*)\b",  # Logical inference
            r"\bfrom (.*) perspective\b",  # Philosophical analysis
            r"\bby (induction|deduction|abduction)\b",  # Mathematical proof
            r"\btherefore\b",
            r"\bthus\b",
            r"\bhence\b",
            r"\bconsequently\b",
            r"\bnếu (.*) thì (.*)\b",  # Vietnamese logical inference
            r"\btừ (.*) quan điểm\b",  # Vietnamese philosophical
            r"\bdo đó\b",
            r"\bvì vậy\b",
        ]
        
        # StillMe self-knowledge indicators
        self.stillme_indicators = [
            r"\bstillme\b",
            r"\bstill me\b",
            r"\bmình (là|sử dụng|học|theo dõi)\b",  # Vietnamese "I am/use/learn/track"
            r"\bi (am|use|learn|track)\b",  # English
            r"\bstillme's (architecture|capabilities|limitations)\b",
        ]
        
        # Factual claim indicators (dates, events, people, places)
        self.factual_indicators = [
            r"\b\d{4}\b",  # Years
            r"\b(conference|hội nghị|treaty|hiệp ước|war|chiến tranh)\s+\d{4}\b",
            r"\b(according to|theo|based on)\s+[A-Z][a-z]+\b",  # Named sources
            r"\b([A-Z][a-z]+)\s+(proposed|đề xuất|discovered|phát hiện|invented|phát minh)\b",
            r"\b(capital|thủ đô) of [A-Z][a-z]+\b",
        ]
        
        # Compile patterns
        self.well_established_re = [
            re.compile(pattern, re.IGNORECASE) 
            for pattern in self.well_established_patterns
        ]
        self.reasoning_re = [
            re.compile(pattern, re.IGNORECASE) 
            for pattern in self.reasoning_indicators
        ]
        self.stillme_re = [
            re.compile(pattern, re.IGNORECASE) 
            for pattern in self.stillme_indicators
        ]
        self.factual_re = [
            re.compile(pattern, re.IGNORECASE) 
            for pattern in self.factual_indicators
        ]
    
    def classify(
        self, 
        claim: str, 
        has_rag_context: bool, 
        is_about_stillme: bool = False,
        user_question: Optional[str] = None
    ) -> KnowledgeType:
        """
        Formally classify a knowledge claim
        
        Args:
            claim: The claim to classify
            has_rag_context: Whether RAG context is available
            is_about_stillme: Whether claim is about StillMe itself
            user_question: Optional user question for context
            
        Returns:
            KnowledgeType enum
        """
        claim_lower = claim.lower()
        question_lower = (user_question or "").lower()
        
        # Rule 1: If about StillMe → STILLME_SELF_KNOWLEDGE
        if is_about_stillme:
            logger.debug(f"KnowledgeTypeClassifier: Classified as STILLME_SELF_KNOWLEDGE (is_about_stillme=True)")
            return KnowledgeType.STILLME_SELF_KNOWLEDGE
        
        # Check if claim or question mentions StillMe
        if any(pattern.search(claim_lower) or pattern.search(question_lower) for pattern in self.stillme_re):
            logger.debug(f"KnowledgeTypeClassifier: Classified as STILLME_SELF_KNOWLEDGE (StillMe mentioned)")
            return KnowledgeType.STILLME_SELF_KNOWLEDGE
        
        # Rule 2: If has RAG context → FACTUAL_CLAIM (requires citation)
        if has_rag_context:
            logger.debug(f"KnowledgeTypeClassifier: Classified as FACTUAL_CLAIM (has_rag_context=True)")
            return KnowledgeType.FACTUAL_CLAIM
        
        # Rule 3: Check if reasoning (logical inference, philosophical analysis)
        if any(pattern.search(claim_lower) for pattern in self.reasoning_re):
            logger.debug(f"KnowledgeTypeClassifier: Classified as REASONING (reasoning indicators found)")
            return KnowledgeType.REASONING
        
        # Rule 4: Check if well-established fact (common knowledge, pre-2023)
        if any(pattern.search(claim_lower) for pattern in self.well_established_re):
            logger.debug(f"KnowledgeTypeClassifier: Classified as GENERAL_KNOWLEDGE (well-established fact)")
            return KnowledgeType.GENERAL_KNOWLEDGE
        
        # Rule 5: Check if factual claim indicators present
        if any(pattern.search(claim_lower) for pattern in self.factual_re):
            logger.debug(f"KnowledgeTypeClassifier: Classified as FACTUAL_CLAIM (factual indicators found)")
            return KnowledgeType.FACTUAL_CLAIM
        
        # Default: If no RAG context and not clearly reasoning/general knowledge → FACTUAL_CLAIM (requires citation)
        # This is conservative: when in doubt, require citation
        logger.debug(f"KnowledgeTypeClassifier: Classified as FACTUAL_CLAIM (default, no RAG context)")
        return KnowledgeType.FACTUAL_CLAIM
    
    def get_citation_requirement(self, knowledge_type: KnowledgeType) -> tuple[bool, str]:
        """
        Get citation requirement for a knowledge type
        
        Args:
            knowledge_type: The classified knowledge type
            
        Returns:
            Tuple of (requires_citation: bool, citation_format: str)
        """
        if knowledge_type == KnowledgeType.FACTUAL_CLAIM:
            return (True, "[1]")  # Requires RAG citation
        elif knowledge_type == KnowledgeType.GENERAL_KNOWLEDGE:
            return (False, "[general knowledge]")  # Optional, but recommended
        elif knowledge_type == KnowledgeType.REASONING:
            return (False, "")  # No citation needed
        elif knowledge_type == KnowledgeType.STILLME_SELF_KNOWLEDGE:
            return (False, "[foundational knowledge]")  # Uses foundational knowledge
        else:
            # Default: require citation
            return (True, "[1]")

