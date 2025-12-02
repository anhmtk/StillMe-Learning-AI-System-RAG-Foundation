"""
AI Self Model Validator - CRITICAL VALIDATION LAYER
Validates that AI_SELF_MODEL responses contain NO philosophy
"""

import re
import logging
from typing import List
from .base import Validator, ValidationResult

logger = logging.getLogger(__name__)

# Forbidden patterns that indicate philosophy violation
FORBIDDEN_PATTERNS = [
    # Philosophers
    r'\b(nagel|chalmers|dennett|searle|tononi|baars)\b',
    # Theories
    r'\b(iit|integrated information theory|global workspace theory|gwt)\b',
    r'\b(hard problem|vấn đề khó)\b',
    r'\b(phenomenal consciousness|functional consciousness)\b',
    # Meta-philosophy
    r'\b(meta-philosophy|philosophy of mind|triết học tâm trí)\b',
    r'\b(epistemology of consciousness|nhận thức luận về ý thức)\b',
    # Uncertainty about consciousness
    r'\b(không biết chắc|uncertain|unclear|debated)\s+(về|about)\s+(ý thức|consciousness)\b',
    r'\b(có thể có|might have|possibly|perhaps)\s+(ý thức|consciousness)\b',
    # Philosophical speculation
    r'\b(phân tích|analyze|analysis)\s+(vấn đề|problem)\s+(khó|hard)\s+(của|of)\s+(ý thức|consciousness)\b',
]


class AISelfModelValidator(Validator):
    """
    Validator for AI_SELF_MODEL domain responses.
    
    CRITICAL: Ensures NO philosophy in answers about StillMe's consciousness.
    """
    
    def __init__(self):
        """Initialize AI Self Model validator"""
        super().__init__()
    
    def run(self, answer: str, ctx_docs: List[str]) -> ValidationResult:
        """
        Validate that answer contains NO forbidden philosophy terms.
        
        Args:
            answer: Answer text to validate
            ctx_docs: Context documents (not used for this validator)
            
        Returns:
            ValidationResult with passed=False if violations found
        """
        answer_lower = answer.lower()
        violations = []
        
        # Check for forbidden patterns
        for pattern in FORBIDDEN_PATTERNS:
            matches = re.findall(pattern, answer_lower, re.IGNORECASE)
            if matches:
                violations.append(f"forbidden_philosophy_term: {pattern}")
                logger.error(f"🚨 AI_SELF_MODEL violation: Found forbidden pattern '{pattern}' in answer")
        
        # Check for uncertainty about consciousness
        uncertainty_patterns = [
            r'\b(không biết chắc|uncertain|not sure)\s+(liệu|whether)\s+(mình|i|stillme)\s+(có|have)\s+(ý thức|consciousness)\b',
            r'\b(có thể có|might have|possibly)\s+(ý thức|consciousness)\b',
        ]
        for pattern in uncertainty_patterns:
            if re.search(pattern, answer_lower, re.IGNORECASE):
                violations.append(f"uncertainty_about_consciousness: {pattern}")
                logger.error(f"🚨 AI_SELF_MODEL violation: Uncertainty about consciousness found")
        
        # Check for philosophical analysis instead of technical explanation
        philosophy_analysis_patterns = [
            r'\b(phân tích|analyze|analysis)\s+(như|as)\s+(một|a)\s+(triết gia|philosopher)\b',
            r'\b(meta-philosophy|meta-philosophical)\b',
        ]
        for pattern in philosophy_analysis_patterns:
            if re.search(pattern, answer_lower, re.IGNORECASE):
                violations.append(f"philosophical_analysis: {pattern}")
                logger.error(f"🚨 AI_SELF_MODEL violation: Philosophical analysis found")
        
        if violations:
            return ValidationResult(
                passed=False,
                reasons=violations,
                patched_answer=None  # Cannot auto-patch - must be rewritten
            )
        
        return ValidationResult(
            passed=True,
            reasons=[],
            patched_answer=None
        )

