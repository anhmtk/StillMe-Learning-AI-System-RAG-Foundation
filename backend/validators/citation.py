"""
CitationRequired validator - Ensures answers include citations
"""

import re
from typing import List
from .base import ValidationResult
import logging

logger = logging.getLogger(__name__)

# Pattern to match citations like [1], [2], [123]
CITE_RE = re.compile(r"\[(\d+)\]")


class CitationRequired:
    """Validator that requires citations in answers"""
    
    def __init__(self, required: bool = True):
        """
        Initialize citation validator
        
        Args:
            required: Whether citations are required (default: True)
        """
        self.required = required
    
    def run(self, answer: str, ctx_docs: List[str]) -> ValidationResult:
        """
        Check if answer contains citations
        
        Args:
            answer: The answer to validate
            ctx_docs: List of context documents - if empty, citations are not required
            
        Returns:
            ValidationResult with passed status
        """
        if not self.required:
            return ValidationResult(passed=True)
        
        # Only require citations if we have context documents
        # If no context, AI is using general knowledge and citations are optional
        if not ctx_docs or len(ctx_docs) == 0:
            logger.debug("No context documents available, citations not required")
            return ValidationResult(passed=True)
        
        has_citation = bool(CITE_RE.search(answer))
        
        if has_citation:
            logger.debug("Citation found in answer")
            return ValidationResult(passed=True)
        else:
            logger.warning("Missing citation in answer (context documents available but no citations found)")
            return ValidationResult(
                passed=False,
                reasons=["missing_citation"]
            )

