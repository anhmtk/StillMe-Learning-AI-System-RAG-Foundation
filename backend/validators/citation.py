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
        Check if answer contains citations and auto-enforce if missing
        
        Args:
            answer: The answer to validate
            ctx_docs: List of context documents - if empty, citations are not required
            
        Returns:
            ValidationResult with passed status and patched answer if citation was added
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
            
            # AUTO-ENFORCE: Add citation to response
            patched_answer = self._add_citation(answer, ctx_docs)
            
            return ValidationResult(
                passed=False,  # Still mark as failed to track the issue
                reasons=["missing_citation"],
                patched_answer=patched_answer
            )
    
    def _add_citation(self, answer: str, ctx_docs: List[str]) -> str:
        """
        Automatically add citation to answer when missing
        
        Args:
            answer: Original answer without citation
            ctx_docs: List of context documents
            
        Returns:
            Answer with citation added
        """
        # Edge case: Empty or whitespace-only answer
        if not answer or len(answer.strip()) == 0:
            logger.warning("Cannot add citation to empty answer")
            return answer + " [1]" if answer else "[1]"
        
        # Edge case: Very short answer (< 5 chars) - just add at the end
        if len(answer.strip()) < 5:
            return answer.rstrip() + " [1]"
        
        # Find the best place to add citation
        # Strategy: Add [1] after the first sentence or first paragraph
        
        # Try to find first sentence (ends with . ! ?)
        sentence_end = re.search(r'[.!?]\s+', answer)
        if sentence_end:
            # Insert citation after first sentence
            insert_pos = sentence_end.end()
            citation = " [1]"
            patched = answer[:insert_pos] + citation + answer[insert_pos:]
        else:
            # If no sentence end found, add at the end of first line or beginning
            first_newline = answer.find('\n')
            if first_newline > 0 and first_newline < 100:  # Reasonable paragraph break
                insert_pos = first_newline
                citation = " [1]"
                patched = answer[:insert_pos] + citation + answer[insert_pos:]
            else:
                # Add at the end
                patched = answer.rstrip() + " [1]"
        
        logger.info(f"Auto-added citation [1] to response (context docs: {len(ctx_docs)})")
        return patched

