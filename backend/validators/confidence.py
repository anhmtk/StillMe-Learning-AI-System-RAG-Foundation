"""
ConfidenceValidator - Detects when AI should express uncertainty
"""

import re
from typing import List, Optional
from .base import ValidationResult
import logging

logger = logging.getLogger(__name__)

# Patterns that indicate uncertainty (good!)
UNCERTAINTY_PATTERNS = [
    r"i don't know",
    r"i'm not (certain|sure)",
    r"i cannot (answer|determine|verify)",
    r"i don't have (sufficient|enough) (information|context|data)",
    r"based on the context (provided|available),? i (cannot|don't)",
    r"my knowledge base (doesn't|does not) (contain|have)",
    r"not (certain|sure|confident) (about|regarding)",
    r"unable to (answer|determine|verify)",
    r"không (biết|chắc|rõ)",
    r"không có (đủ|thông tin|dữ liệu)",
    r"không thể (trả lời|xác định|xác minh)",
    r"tôi (không|chưa) (biết|có|rõ)",
    r"hiện tại (tôi|mình) (không|chưa) (có|biết)"
]

# Patterns that indicate overconfidence (bad!)
OVERCONFIDENCE_PATTERNS = [
    r"definitely",
    r"absolutely (certain|sure)",
    r"without a doubt",
    r"i'm 100% (sure|certain)",
    r"chắc chắn 100%",
    r"hoàn toàn chắc chắn"
]


class ConfidenceValidator:
    """Validator that checks if AI appropriately expresses uncertainty"""
    
    def __init__(self, require_uncertainty_when_no_context: bool = True):
        """
        Initialize confidence validator
        
        Args:
            require_uncertainty_when_no_context: If True, require uncertainty expressions when no context
        """
        self.require_uncertainty_when_no_context = require_uncertainty_when_no_context
        logger.info(f"ConfidenceValidator initialized (require_uncertainty_when_no_context={require_uncertainty_when_no_context})")
    
    def run(self, answer: str, ctx_docs: List[str], context_quality: Optional[str] = None, 
            avg_similarity: Optional[float] = None, is_philosophical: bool = False) -> ValidationResult:
        """
        Check if answer appropriately expresses uncertainty
        
        Args:
            answer: The answer to validate
            ctx_docs: List of context documents from RAG
            context_quality: Context quality from RAG ("high", "medium", "low")
            avg_similarity: Average similarity score of retrieved context (0.0-1.0)
            is_philosophical: If True, relax uncertainty requirements for philosophical questions (don't force "I don't know" for theoretical reasoning)
            
        Returns:
            ValidationResult with passed status and reasons
        """
        answer_lower = answer.lower()
        
        # Tier 3.5: Force uncertainty when context quality is low
        # BUT: Skip for philosophical questions (theoretical reasoning doesn't need context)
        if not is_philosophical and (context_quality == "low" or (avg_similarity is not None and avg_similarity < 0.3)):
            # Check if answer already expresses uncertainty
            has_uncertainty = any(
                re.search(pattern, answer_lower, re.IGNORECASE)
                for pattern in UNCERTAINTY_PATTERNS
            )
            
            if not has_uncertainty:
                # Force uncertainty template
                uncertainty_template = (
                    "I don't have sufficient information to answer this accurately. "
                    "The retrieved context has low relevance to your question."
                )
                # Prepend uncertainty to answer
                patched_answer = f"{uncertainty_template}\n\n{answer}"
                logger.warning("⚠️ Forced uncertainty expression due to low context quality")
                return ValidationResult(
                    passed=True,
                    reasons=["forced_uncertainty_low_context_quality"],
                    patched_answer=patched_answer
                )
        
        # Check for uncertainty expressions
        has_uncertainty = any(
            re.search(pattern, answer_lower, re.IGNORECASE)
            for pattern in UNCERTAINTY_PATTERNS
        )
        
        # Check for overconfidence
        has_overconfidence = any(
            re.search(pattern, answer_lower, re.IGNORECASE)
            for pattern in OVERCONFIDENCE_PATTERNS
        )
        
        # If no context, check for transparency about knowledge source
        if not ctx_docs or len(ctx_docs) == 0:
            # For philosophical questions, don't force uncertainty (theoretical reasoning doesn't need context)
            if is_philosophical:
                logger.debug("Philosophical question with no context - allowing theoretical reasoning without forcing uncertainty")
                return ValidationResult(passed=True)
            
            if self.require_uncertainty_when_no_context:
                # Check if AI acknowledges using base knowledge/training data (transparency)
                transparency_patterns = [
                    r"based on (general knowledge|training data|my training|base knowledge)",
                    r"from (my|general|base) (training data|knowledge base|knowledge)",
                    r"not from (stillme|rag) (knowledge base|knowledge)",
                    r"(general|base) knowledge",
                    r"training data",
                    r"kiến thức (chung|cơ bản)",
                    r"dữ liệu (huấn luyện|training)",
                    r"không (từ|phải từ) (stillme|rag)",
                    r"dựa trên (kiến thức|dữ liệu) (chung|huấn luyện|cơ bản)",
                    r"tuy nhiên.*stillme.*không.*có",  # "However, StillMe doesn't have..."
                    r"however.*stillme.*(doesn't|does not).*have",  # English version
                    r"dựa trên.*kiến thức.*chung",  # "Based on general knowledge"
                    r"theo.*kiến thức.*chung"  # "According to general knowledge"
                ]
                has_transparency = any(
                    re.search(pattern, answer_lower, re.IGNORECASE)
                    for pattern in transparency_patterns
                )
                
                # If AI is transparent about using base knowledge, that's acceptable
                if has_transparency:
                    logger.debug("✅ Good: AI is transparent about using base knowledge when no RAG context")
                    return ValidationResult(passed=True)
                elif has_uncertainty:
                    logger.debug("✅ Good: AI expressed uncertainty when no context available")
                    return ValidationResult(passed=True)
                else:
                    logger.warning("❌ AI should express uncertainty OR acknowledge using base knowledge when no context is available")
                    return ValidationResult(
                        passed=False,
                        reasons=["missing_uncertainty_no_context"]
                    )
            else:
                return ValidationResult(passed=True)
        
        # If context exists but answer is overconfident, warn
        if has_overconfidence and not has_uncertainty:
            logger.warning("⚠️ AI expressed overconfidence - may need more humility")
            # Don't fail, just warn
            return ValidationResult(
                passed=True,
                reasons=["overconfidence_detected"]
            )
        
        return ValidationResult(passed=True)

