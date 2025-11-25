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
        # ALSO: Simple factual questions (geography, math, science, literature) need citations too
        is_real_factual_question = False
        is_simple_factual_question = False
        if user_question:
            question_lower = user_question.lower()
            
            # CRITICAL: Detect simple factual questions (geography, math, science, literature)
            # These are factual questions that need citations even if not historical/philosophical
            simple_factual_patterns = [
                r"\b(what is|what's|what are|what were|who is|who's|who are|who were|when is|when was|where is|where was|how many|how much)\b",  # Question words
                r"\b(capital|largest|smallest|fastest|slowest|biggest|tallest|longest|shortest|highest|lowest)\b",  # Comparative/superlative
                r"\b(wrote|author|novel|book|poem|play)\b",  # Literature
                r"\b(chemical symbol|element|atomic|molecule)\b",  # Chemistry
                r"\b(planet|solar system|star|galaxy|universe|earth|moon|sun)\b",  # Astronomy
                r"\b(speed|velocity|distance|time|light|sound|gravity)\b",  # Physics
                r"\b(prime number|even|odd|sum|difference|product|quotient|equation)\b",  # Math
                r"\b(country|city|nation|continent|ocean|sea|river|mountain)\b",  # Geography
                r"\b(boiling point|melting point|freezing point|temperature)\b",  # Science
            ]
            
            for pattern in simple_factual_patterns:
                try:
                    if re.search(pattern, question_lower, re.IGNORECASE):
                        is_simple_factual_question = True
                        logger.debug(f"✅ Detected simple factual question with pattern: {pattern[:50]}... (question: {user_question[:100]})")
                        break
                except Exception as e:
                    logger.warning(f"⚠️ Error matching simple factual pattern {pattern[:50]}: {e}")
                    continue
            
            # Detect factual indicators: years, historical events, specific people, conferences, treaties
            # CRITICAL: Expanded patterns to catch ALL factual questions, including philosophical ones with factual elements
            factual_indicators = [
                r"\b\d{4}\b",  # Years (e.g., 1944, 1943, 1954)
                r"\b(conference|hội nghị|treaty|hiệp ước|agreement|hiệp định)\b",
                r"\b(bretton\s+woods|popper|kuhn|gödel|godel|keynes|imf|world\s+bank|searle|dennett|chinese\s+room|russell|plato|aristotle|kant|hume|descartes|spinoza)\b",
                r"\b(historical|history|lịch sử|sự kiện|event)\b",
                r"\b(scientist|philosopher|nhà khoa học|triết gia)\s+\w+",  # Named people
                # CRITICAL: Detect named philosophers/scientists (capitalized names)
                r"\b([A-Z][a-z]+\s+[A-Z][a-z]+)\b",  # Two capitalized words (e.g., "Searle và Dennett", "Popper và Kuhn")
                r"\b([A-Z][a-z]+)\s+(và|and|vs|versus)\s+([A-Z][a-z]+)\b",  # "Searle và Dennett", "Popper vs Kuhn", "Plato và Aristotle", "Kant và Hume", "Descartes và Spinoza"
                # CRITICAL: Detect theorems, debates, arguments about specific people/concepts
                r"\b(định\s+lý|theorem|tranh\s+luận|debate|argument|paradox|nghịch\s+lý)\s+(của|of|về|about)\s+([A-Z][a-z]+)",  # "Định lý của Gödel", "Tranh luận về Searle", "Paradox của Russell"
                r"\b(gödel|godel|searle|dennett|popper|kuhn|russell|plato|aristotle|kant|hume|descartes|spinoza)\b",  # Direct mentions of well-known philosophers/scientists (case-insensitive)
                r"\b(incompleteness|bất\s+toàn|chinese\s+room|russell.*paradox|paradox.*russell|russell.*tập\s+hợp)\b",  # Well-known concepts/theorems
                # CRITICAL: Detect "Paradox của Russell" or "Russell's paradox" (case-insensitive)
                r"\b(russell|russell's)\s+(paradox|nghịch\s+lý)\b",
                r"\b(paradox|nghịch\s+lý)\s+(của|of)\s+(russell|russell's)\b",
                r"\b(russell|russell's)\b.*\b(paradox|nghịch\s+lý)\b",  # "Russell...paradox" (words can be separated)
                r"\b(paradox|nghịch\s+lý)\b.*\b(russell|russell's)\b",  # "paradox...Russell" (words can be separated)
                # CRITICAL: Detect "Tranh luận giữa X và Y" pattern (case-insensitive)
                r"\b(tranh\s+luận|debate|argument)\s+(giữa|between)\s+([A-Z][a-z]+)\s+(và|and)\s+([A-Z][a-z]+)\b",
                # CRITICAL: Detect "forms" (hình thức) with Plato/Aristotle (case-insensitive)
                r"\b(plato|aristotle).*(forms|hình\s+thức|thực\s+tại|reality)\b",
                r"\b(forms|hình\s+thức).*(plato|aristotle)\b",
                # CRITICAL: Detect "causality" (quan hệ nhân quả) with Kant/Hume (case-insensitive)
                r"\b(kant|hume).*(causality|quan\s+hệ\s+nhân\s+quả|causation)\b",
                r"\b(causality|quan\s+hệ\s+nhân\s+quả|causation).*(kant|hume)\b",
                # CRITICAL: Detect "mind-body" (tâm-thể) with Descartes/Spinoza (case-insensitive)
                r"\b(descartes|spinoza).*(mind.*body|tâm.*thể|consciousness|ý\s+thức|matter|vật\s+chất)\b",
                r"\b(mind.*body|tâm.*thể).*(descartes|spinoza)\b",
                # CRITICAL: Detect "Geneva 1954" or "Hiệp ước Geneva 1954" (case-insensitive)
                r"\b(geneva|genève)\s+\d{4}\b",
                r"\b(hiệp\s+ước|hiệp\s+định|treaty|agreement)\s+(geneva|genève)\b",
                # CRITICAL: Detect "Bretton Woods 1944" (case-insensitive)
                r"\b(bretton\s+woods)\s+\d{4}\b",
                r"\b(hội\s+nghị|conference)\s+(bretton\s+woods)\b",
                # CRITICAL: Detect "17th parallel" or "vĩ tuyến 17" (case-insensitive)
                r"\b(\d+th|\d+st|\d+nd|\d+rd)\s+parallel\b",
                r"\b(vĩ\s+tuyến|parallel)\s+\d+\b",
                # CRITICAL: Detect "Gödel's incompleteness theorem" or "Định lý bất toàn của Gödel" (case-insensitive)
                r"\b(gödel|godel).*(incompleteness|bất\s+toàn)\b",
                r"\b(incompleteness|bất\s+toàn).*(gödel|godel)\b",
                # CRITICAL: Detect "Chinese Room" with Searle/Dennett (case-insensitive)
                r"\b(chinese\s+room|phòng\s+trung\s+quốc).*(searle|dennett)\b",
                r"\b(searle|dennett).*(chinese\s+room|phòng\s+trung\s+quốc)\b",
            ]
            for pattern in factual_indicators:
                try:
                    if re.search(pattern, question_lower, re.IGNORECASE):
                        is_real_factual_question = True
                        logger.debug(f"✅ Detected real factual question with pattern: {pattern[:50]}... (question: {user_question[:100]})")
                        break
                except Exception as e:
                    logger.warning(f"⚠️ Error matching pattern {pattern[:50]}: {e}")
                    continue
        
        # For pure philosophical questions (no factual elements), skip citation requirement
        # BUT: If question has factual elements (years, events, named people), ALWAYS require citations
        if is_philosophical and not is_real_factual_question:
            logger.debug("Pure philosophical question detected (no factual elements) - skipping citation requirement")
            return ValidationResult(passed=True)
        
        # If it's a factual question (even with philosophical elements), require citations
        if is_real_factual_question:
            logger.debug(f"Real factual question detected - citations REQUIRED even if philosophical elements present")
        
        # CRITICAL FIX: Simple factual questions (geography, math, science, literature) also need citations
        # These are factual questions that should be cited for transparency
        if is_simple_factual_question:
            logger.debug(f"Simple factual question detected - citations REQUIRED for transparency")
        
        # Combine both types of factual questions
        is_any_factual_question = is_real_factual_question or is_simple_factual_question
        
        # CRITICAL FIX: For ANY factual questions, we should still try to enforce citations
        # even if context is empty, because the LLM might have base knowledge about these topics
        # However, we can only auto-add citations if we have context documents
        
        # If no context documents available:
        if not ctx_docs or len(ctx_docs) == 0:
            # For ANY factual questions, we should still add citation for transparency
            # Even if no RAG context, the answer is based on base knowledge and should be cited
            if is_any_factual_question:
                logger.warning(f"Factual question detected but no context documents available - adding citation for base knowledge transparency. Question: {user_question[:100]}")
                # CRITICAL: Add citation [1] even without RAG context to indicate base knowledge source
                # This ensures transparency: user knows answer is from base knowledge, not RAG
                patched_answer = self._add_citation_for_base_knowledge(answer)
                return ValidationResult(
                    passed=False,  # Still mark as failed to track that RAG context was missing
                    reasons=["missing_citation_no_context", "added_citation_for_base_knowledge"],
                    patched_answer=patched_answer
                )
            else:
                logger.debug("No context documents available, citations not required")
                return ValidationResult(passed=True)
        
        # CRITICAL: Even if context is available, check if answer already has citation
        # If not, we MUST add it (this is the main path for missing citations)
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
        
        # CRITICAL FIX: Even if context is not relevant, we MUST cite for transparency
        # The citation instruction says: "When context documents are available, you MUST include at least one citation [1], [2], or [3] in your response for transparency."
        # So we should ALWAYS require citation when context is available, regardless of relevance
        # BUT: For real factual questions, we MUST cite even if context is empty (use base knowledge citation)
        
        if has_citation:
            logger.debug("Citation found in answer")
            return ValidationResult(passed=True)
        else:
            logger.warning("Missing citation in answer (context documents available but no citations found)")
            
            # CRITICAL: For ANY factual questions (real or simple), ALWAYS add citation
            # Even if context is available, if it's a factual question and answer doesn't have citation, we MUST add it
            if is_any_factual_question:
                if not ctx_docs or len(ctx_docs) == 0:
                    # No context - use base knowledge citation
                    logger.warning(f"Factual question detected but no context - adding base knowledge citation. Question: {user_question[:100] if user_question else 'unknown'}")
                    patched_answer = self._add_citation_for_base_knowledge(answer)
                    return ValidationResult(
                        passed=False,  # Still mark as failed to track that RAG context was missing
                        reasons=["missing_citation_no_context", "added_citation_for_base_knowledge"],
                        patched_answer=patched_answer
                    )
                else:
                    # Context available but no citation - MUST add citation for factual questions
                    logger.warning(f"Factual question detected with context but missing citation - adding citation. Question: {user_question[:100] if user_question else 'unknown'}")
                    patched_answer = self._add_citation(answer, ctx_docs)
                    return ValidationResult(
                        passed=False,  # Still mark as failed to track the issue
                        reasons=["missing_citation_factual_question", "added_citation"],
                        patched_answer=patched_answer
                    )
            
            # AUTO-ENFORCE: Add citation to response for ALL questions when context is available
            # CRITICAL: Always add citation when context is available, regardless of question type
            # This ensures transparency - user knows what sources were reviewed
            if ctx_docs and len(ctx_docs) > 0:
                logger.info(f"Context available ({len(ctx_docs)} docs) but no citation - auto-adding citation for transparency")
                patched_answer = self._add_citation(answer, ctx_docs)
                return ValidationResult(
                    passed=False,  # Still mark as failed to track the issue
                    reasons=["missing_citation"],
                    patched_answer=patched_answer
                )
            else:
                # No context and not a factual question - citations not required
                logger.debug("No context documents available and not a factual question - citations not required")
                return ValidationResult(passed=True)
    
    def _add_citation_for_base_knowledge(self, answer: str) -> str:
        """
        Add citation [1] for base knowledge answers (when no RAG context available)
        
        Args:
            answer: Original answer without citation
            
        Returns:
            Answer with citation [1] added to indicate base knowledge source
        """
        # Use same logic as _add_citation but always use [1] for base knowledge
        if not answer or len(answer.strip()) == 0:
            return answer + " [1]" if answer else "[1]"
        
        if len(answer.strip()) < 5:
            return answer.rstrip() + " [1]"
        
        # Find the best place to add citation
        sentence_end = re.search(r'[.!?]\s+', answer)
        if sentence_end:
            insert_pos = sentence_end.end()
            return answer[:insert_pos] + "[1] " + answer[insert_pos:]
        
        # If no sentence end found, add at the end
        return answer.rstrip() + " [1]"
    
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

