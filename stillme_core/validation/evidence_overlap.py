"""
EvidenceOverlap validator - Checks if answer overlaps with RAG context
"""

from typing import List
from .base import ValidationResult
import logging
import os

logger = logging.getLogger(__name__)


def ngram_overlap(text_a: str, text_b: str, n: int = 3) -> float:
    """
    Calculate n-gram overlap between two texts
    
    Args:
        text_a: First text
        text_b: Second text
        n: N-gram size (default: 3)
        
    Returns:
        Overlap ratio (0.0 to 1.0)
    """
    a_tokens = text_a.split()
    b_tokens = text_b.split()
    
    if len(a_tokens) < n or len(b_tokens) < n:
        return 0.0
    
    # Generate n-grams
    a_ngrams = set(
        tuple(a_tokens[i:i+n]) for i in range(len(a_tokens) - n + 1)
    )
    b_ngrams = set(
        tuple(b_tokens[i:i+n]) for i in range(len(b_tokens) - n + 1)
    )
    
    # Calculate intersection over union (simplified: intersection over a_size)
    intersection = len(a_ngrams & b_ngrams)
    base = max(1, len(a_ngrams))
    
    return intersection / base


class EvidenceOverlap:
    """Validator that checks answer overlaps with RAG context"""
    
    def __init__(self, threshold: float = 0.01):
        """
        Initialize evidence overlap validator
        
        Args:
            threshold: Minimum overlap ratio (default: 0.01 = 1%)
                     Lowered from 0.08 to prevent false positives when LLM
                     translates/summarizes content, reducing vocabulary overlap
        """
        self.threshold = float(
            os.getenv("VALIDATOR_EVIDENCE_THRESHOLD", str(threshold))
        )
        logger.info(f"EvidenceOverlap initialized with threshold={self.threshold}")
    
    def run(self, answer: str, ctx_docs: List[str]) -> ValidationResult:
        """
        Check if answer overlaps with context documents
        
        Args:
            answer: The answer to validate
            ctx_docs: List of context documents from RAG
            
        Returns:
            ValidationResult with overlap score
        """
        if not ctx_docs:
            # No context means no overlap check needed - this is handled by ConfidenceValidator
            # Don't fail here, let ConfidenceValidator handle the no-context case
            logger.debug("No context documents provided for overlap check - skipping (ConfidenceValidator will handle)")
            return ValidationResult(passed=True)
        
        # Calculate overlap with each context doc, take maximum
        overlaps = [
            ngram_overlap(answer, doc) for doc in ctx_docs
        ]
        best_overlap = max(overlaps, default=0.0)
        
        logger.debug(
            f"Best overlap: {best_overlap:.3f} (threshold: {self.threshold})"
        )
        
        if best_overlap >= self.threshold:
            return ValidationResult(passed=True)
        else:
            return ValidationResult(
                passed=False,
                reasons=[f"low_overlap:{best_overlap:.3f}"]
            )

