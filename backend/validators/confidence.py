"""
ConfidenceValidator - Detects when AI should express uncertainty
"""

import re
from typing import List
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
    
    def run(self, answer: str, ctx_docs: List[str]) -> ValidationResult:
        """
        Check if answer appropriately expresses uncertainty
        
        Args:
            answer: The answer to validate
            ctx_docs: List of context documents from RAG
            
        Returns:
            ValidationResult with passed status and reasons
        """
        answer_lower = answer.lower()
        
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
            if self.require_uncertainty_when_no_context:
                # Check if AI acknowledges using base knowledge/training data (transparency)
                transparency_patterns = [
                    r"based on (general knowledge|training data|my training)",
                    r"from (my|general) (training data|knowledge base)",
                    r"not from (stillme|rag) (knowledge base|knowledge)",
                    r"general knowledge",
                    r"training data",
                    r"không (từ|phải từ) (stillme|rag)",
                    r"dựa trên (kiến thức|dữ liệu) (chung|huấn luyện)"
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

