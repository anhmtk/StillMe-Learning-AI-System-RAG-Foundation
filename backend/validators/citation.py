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
                r"\b(bretton\s+woods|popper|kuhn|gödel|keynes|imf|world\s+bank|searle|dennett|chinese\s+room)\b",
                r"\b(historical|history|lịch sử|sự kiện|event)\b",
                r"\b(scientist|philosopher|nhà khoa học|triết gia)\s+\w+",  # Named people
                # CRITICAL: Detect named philosophers/scientists (capitalized names)
                r"\b([A-Z][a-z]+\s+[A-Z][a-z]+)\b",  # Two capitalized words (e.g., "Searle và Dennett", "Popper và Kuhn")
                r"\b([A-Z][a-z]+)\s+(và|and|vs|versus)\s+([A-Z][a-z]+)\b",  # "Searle và Dennett", "Popper vs Kuhn"
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
        
        # CRITICAL FIX: Check if answer has URLs or source references that should be converted to citations
        # If answer has URLs like "Source: https://..." or "Sources: ...", convert them to [1] format
        # ALSO: Check for bare URLs (https://...) at end of answer or after "Sources:" or "-"
        if not has_citation:
            # Pattern 1: URLs with source prefix
            url_pattern_with_prefix = re.compile(r'(?:Source|Sources|Tham\s+Khảo|Tham\s+khảo|References?):\s*(?:https?://|www\.)', re.IGNORECASE)
            # Pattern 2: Bare URLs (https:// or www.) - often at end of answer or after "-"
            url_pattern_bare = re.compile(r'(?:^|\s|[-•])\s*(?:https?://[^\s]+|www\.[^\s]+)', re.IGNORECASE)
            
            has_urls_with_prefix = bool(url_pattern_with_prefix.search(answer))
            has_bare_urls = bool(url_pattern_bare.search(answer))
            
            if has_urls_with_prefix or has_bare_urls:
                # Convert URLs to citations
                logger.info(f"Found URLs in answer (with_prefix={has_urls_with_prefix}, bare={has_bare_urls}), converting to citation format [1]")
                patched_answer = self._convert_urls_to_citations(answer, ctx_docs)
                if patched_answer:
                    return ValidationResult(
                        passed=False,  # Still mark as failed to track the issue
                        reasons=["converted_urls_to_citations"],
                        patched_answer=patched_answer
                    )
        
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
    
    def _convert_urls_to_citations(self, answer: str, ctx_docs: List[str]) -> str:
        """
        Convert URLs or source references to citation format [1], [2]
        
        Examples:
        - "Source: https://example.com" → "According to [1], ..."
        - "Sources: https://example.com, https://example2.com" → "According to [1] and [2], ..."
        - "Tham Khảo: https://example.com" → "Theo [1], ..."
        - "- https://example.com" → "According to [1], ..."
        - Bare URLs at end: "https://example.com" → "[1]"
        
        Args:
            answer: Original answer with URLs
            ctx_docs: List of context documents
            
        Returns:
            Answer with URLs converted to citations, or None if conversion failed
        """
        if not answer or not ctx_docs:
            return None
        
        result = answer
        
        # Pattern 1: Source references with URLs (with prefix)
        source_pattern_with_prefix = re.compile(
            r'(?:Source|Sources|Tham\s+Khảo|Tham\s+khảo|References?):\s*(?:https?://[^\s]+|www\.[^\s]+)',
            re.IGNORECASE
        )
        
        # Pattern 2: Bare URLs (https:// or www.) - often at end of answer or after "-" or "•"
        bare_url_pattern = re.compile(
            r'(?:^|\s|[-•])\s*(https?://[^\s]+|www\.[^\s]+)',
            re.IGNORECASE
        )
        
        # Find all source references (with prefix)
        matches_with_prefix = list(source_pattern_with_prefix.finditer(result))
        
        # Find all bare URLs
        matches_bare = list(bare_url_pattern.finditer(result))
        
        # Combine and sort by position
        all_matches = []
        for match in matches_with_prefix:
            all_matches.append(('with_prefix', match))
        for match in matches_bare:
            # Only include if not already captured by prefix pattern
            url_text = match.group(1)
            is_duplicate = any(
                url_text in m.group(0) for _, m in all_matches if _ == 'with_prefix'
            )
            if not is_duplicate:
                all_matches.append(('bare', match))
        
        # Sort by position (reverse order for safe replacement)
        all_matches.sort(key=lambda x: x[1].start(), reverse=True)
        
        if not all_matches:
            return None
        
        # Replace each source reference with citation
        # Strategy: Replace "Source: URL" or bare URL with "[1]" at the beginning of the sentence/paragraph
        for i, (match_type, match) in enumerate(all_matches):  # Process in reverse order (already sorted)
            matched_text = match.group(0)
            start_pos = match.start()
            end_pos = match.end()
            
            # Determine citation number (1, 2, 3, etc.)
            citation_num = min(i + 1, len(ctx_docs))
            citation = f"[{citation_num}]"
            
            # For bare URLs, we need to handle the match differently
            if match_type == 'bare':
                # Bare URL match includes prefix (space, "-", etc.) in group(0), but URL is in group(1)
                url_start = match.start(1)  # Start of actual URL
                url_end = match.end(1)  # End of actual URL
                # Remove the entire match (including prefix like "- " or space)
                result = result[:start_pos] + f" {citation}" + result[end_pos:]
            else:
                # With prefix: "Source: https://..." - find sentence start
                sentence_start = result.rfind('\n', 0, start_pos)
                if sentence_start == -1:
                    sentence_start = 0
                else:
                    sentence_start += 1  # Skip the newline
                
                # Check if there's already a citation in this sentence
                sentence_text = result[sentence_start:end_pos]
                if CITE_RE.search(sentence_text):
                    # Already has citation, just remove the URL reference
                    result = result[:start_pos] + result[end_pos:]
                else:
                    # Replace URL reference with citation
                    # Try to insert citation at a natural position (after first sentence or at start)
                    first_sentence_end = re.search(r'[.!?]\s+', result[sentence_start:start_pos])
                    if first_sentence_end:
                        insert_pos = sentence_start + first_sentence_end.end()
                        result = result[:insert_pos] + f" {citation}" + result[insert_pos:start_pos] + result[end_pos:]
                    else:
                        # Insert at start of sentence
                        result = result[:sentence_start] + f"{citation} " + result[sentence_start:start_pos] + result[end_pos:]
        
        logger.info(f"Converted {len(all_matches)} URL reference(s) to citation format")
        return result

