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
    
    def run(self, answer: str, ctx_docs: List[str], is_philosophical: bool = False, user_question: str = "") -> ValidationResult:
        """
        Check if answer contains citations and auto-enforce if missing
        
        Args:
            answer: The answer to validate
            ctx_docs: List of context documents - if empty, citations are not required
            is_philosophical: If True, relax citation requirements for pure philosophical questions (but still require for factual claims)
            user_question: User's original question (to detect if it's a factual question with philosophical elements)
            
        Returns:
            ValidationResult with passed status and patched answer if citation was added
        """
        if not self.required:
            return ValidationResult(passed=True)
        
        # CRITICAL FIX: Real factual questions (history, science, events) ALWAYS need citations
        # Even if they have philosophical elements, they are still factual questions
        # Examples: "Bretton Woods 1944", "Popper vs Kuhn", "Gödel's incompleteness theorem"
        is_real_factual_question = False
        if user_question:
            question_lower = user_question.lower()
            # Detect factual indicators: years, historical events, specific people, conferences, treaties
            factual_indicators = [
                r"\b\d{4}\b",  # Years (e.g., 1944, 1943)
                r"\b(conference|hội nghị|treaty|hiệp ước|agreement|hiệp định)\b",
                r"\b(bretton\s+woods|popper|kuhn|gödel|keynes|imf|world\s+bank)\b",
                r"\b(historical|history|lịch sử|sự kiện|event)\b",
                r"\b(scientist|philosopher|nhà khoa học|triết gia)\s+\w+",  # Named people
            ]
            for pattern in factual_indicators:
                if re.search(pattern, question_lower):
                    is_real_factual_question = True
                    break
        
        # For pure philosophical questions (no factual elements), skip citation requirement
        # BUT: If question has factual elements (years, events, named people), ALWAYS require citations
        if is_philosophical and not is_real_factual_question:
            logger.debug("Pure philosophical question detected (no factual elements) - skipping citation requirement")
            return ValidationResult(passed=True)
        
        # If it's a factual question (even with philosophical elements), require citations
        if is_real_factual_question:
            logger.debug(f"Real factual question detected - citations REQUIRED even if philosophical elements present")
        
        # CRITICAL FIX: For real factual questions, we should still try to enforce citations
        # even if context is empty, because the LLM might have base knowledge about these topics
        # However, we can only auto-add citations if we have context documents
        
        # If no context documents available:
        if not ctx_docs or len(ctx_docs) == 0:
            # For real factual questions, log a warning but don't auto-add citation (no context to cite)
            if is_real_factual_question:
                logger.warning(f"Real factual question detected but no context documents available - cannot auto-add citation. Question: {user_question[:100]}")
                # Still mark as failed to track the issue, but can't auto-fix without context
                return ValidationResult(
                    passed=False,
                    reasons=["missing_citation_no_context"],
                    patched_answer=None  # Can't patch without context
                )
            else:
                logger.debug("No context documents available, citations not required")
                return ValidationResult(passed=True)
        
        # CRITICAL FIX: Even if context is not relevant, we MUST cite for transparency
        # The citation instruction says: "When context documents are available, you MUST include at least one citation [1], [2], or [3] in your response for transparency."
        # So we should ALWAYS require citation when context is available, regardless of relevance
        
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

