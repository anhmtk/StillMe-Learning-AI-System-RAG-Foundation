"""
CitationRelevance validator - Checks if citations are relevant to the answer
"""

import re
from typing import List, Dict, Any
from .base import ValidationResult
import logging

logger = logging.getLogger(__name__)

# Pattern to match citations like [1], [2], [123]
CITE_RE = re.compile(r"\[(\d+)\]")


class CitationRelevance:
    """
    Validator that checks if citations are relevant to the answer content.
    
    This validator uses simple heuristics to detect potential citation relevance issues:
    - Keyword overlap between answer and context
    - Detection of citation without clear connection to answer content
    """
    
    def __init__(self, min_keyword_overlap: float = 0.1):
        """
        Initialize citation relevance validator
        
        Args:
            min_keyword_overlap: Minimum keyword overlap ratio (0.0-1.0) to consider citation relevant
                                Default 0.1 means at least 10% of answer keywords should appear in context
        """
        self.min_keyword_overlap = min_keyword_overlap
    
    def run(self, answer: str, ctx_docs: List[str]) -> ValidationResult:
        """
        Check if citations in answer are relevant to the context documents
        
        Args:
            answer: The answer to validate
            ctx_docs: List of context document texts
            ctx_metadata: Optional list of context document metadata (for future use)
            
        Returns:
            ValidationResult with passed status and warnings if relevance issues detected
        """
        if not ctx_docs or len(ctx_docs) == 0:
            # No context = no relevance check needed
            return ValidationResult(passed=True)
        
        # Extract citations from answer
        citations = CITE_RE.findall(answer)
        if not citations:
            # No citations = not a relevance issue (handled by CitationRequired)
            return ValidationResult(passed=True)
        
        # Check relevance for each cited document
        relevance_issues = []
        answer_keywords = self._extract_keywords(answer.lower())
        
        for cite_num in citations:
            try:
                doc_index = int(cite_num) - 1  # [1] = index 0, [2] = index 1, etc.
                if doc_index < 0 or doc_index >= len(ctx_docs):
                    # Invalid citation number
                    relevance_issues.append(f"Invalid citation [{cite_num}] - document index out of range")
                    continue
                
                doc_text = ctx_docs[doc_index].lower()
                doc_keywords = self._extract_keywords(doc_text)
                
                # Calculate keyword overlap
                overlap_ratio = self._calculate_keyword_overlap(answer_keywords, doc_keywords)
                
                if overlap_ratio < self.min_keyword_overlap:
                    # Low overlap = potential relevance issue
                    relevance_issues.append(
                        f"Citation [{cite_num}] may not be relevant (keyword overlap: {overlap_ratio:.2%}, "
                        f"minimum: {self.min_keyword_overlap:.2%})"
                    )
                    logger.warning(
                        f"Citation relevance issue: [{cite_num}] has low keyword overlap "
                        f"({overlap_ratio:.2%} < {self.min_keyword_overlap:.2%})"
                    )
            except (ValueError, IndexError) as e:
                logger.warning(f"Error checking citation relevance for [{cite_num}]: {e}")
                relevance_issues.append(f"Error checking citation [{cite_num}]")
        
        if relevance_issues:
            # Tier 3.5: Remove citations with low relevance instead of just warning
            # Remove citations from answer
            patched_answer = answer
            citations_to_remove = []
            
            for issue in relevance_issues:
                # Extract citation number from issue message
                cite_match = re.search(r'\[(\d+)\]', issue)
                if cite_match:
                    cite_num = cite_match.group(1)
                    citations_to_remove.append(cite_num)
            
            # Remove citations from answer
            if citations_to_remove:
                for cite_num in citations_to_remove:
                    # Remove [N] pattern
                    patched_answer = re.sub(rf'\[{cite_num}\]', '', patched_answer)
                    logger.info(f"🗑️ Removed citation [{cite_num}] due to low relevance")
            
            # Clean up multiple spaces
            patched_answer = re.sub(r'\s+', ' ', patched_answer).strip()
            
            logger.warning(f"Citation relevance issues detected: {relevance_issues}")
            return ValidationResult(
                passed=True,  # Don't fail, just remove citations
                reasons=[f"citation_relevance_warning: {issue}" for issue in relevance_issues],
                patched_answer=patched_answer if citations_to_remove else None
            )
        
        return ValidationResult(passed=True)
    
    def _extract_keywords(self, text: str) -> set:
        """
        Extract meaningful keywords from text (simple approach)
        
        Args:
            text: Input text (should be lowercase)
            
        Returns:
            Set of keywords (words with length >= 3, excluding common stop words)
        """
        # Simple stop words list (can be expanded)
        stop_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with',
            'by', 'from', 'as', 'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has',
            'had', 'do', 'does', 'did', 'will', 'would', 'should', 'could', 'may', 'might', 'must',
            'can', 'this', 'that', 'these', 'those', 'i', 'you', 'he', 'she', 'it', 'we', 'they',
            'what', 'which', 'who', 'when', 'where', 'why', 'how', 'all', 'each', 'every', 'some',
            'any', 'no', 'not', 'only', 'just', 'also', 'more', 'most', 'very', 'too', 'so', 'than',
            'then', 'now', 'here', 'there', 'when', 'where', 'why', 'how', 'about', 'into', 'over',
            'after', 'before', 'during', 'through', 'under', 'above', 'below', 'up', 'down', 'out',
            'off', 'away', 'back', 'again', 'further', 'once', 'twice', 'first', 'second', 'third',
            'one', 'two', 'three', 'four', 'five', 'six', 'seven', 'eight', 'nine', 'ten',
            'vietnamese', 'english', 'chinese', 'japanese', 'korean', 'french', 'german', 'spanish'
        }
        
        # Extract words (alphanumeric sequences)
        words = re.findall(r'\b[a-z0-9]{3,}\b', text)
        
        # Filter out stop words and return unique set
        keywords = {w for w in words if w not in stop_words and len(w) >= 3}
        
        return keywords
    
    def _calculate_keyword_overlap(self, answer_keywords: set, doc_keywords: set) -> float:
        """
        Calculate keyword overlap ratio between answer and document
        
        Args:
            answer_keywords: Set of keywords from answer
            doc_keywords: Set of keywords from document
            
        Returns:
            Overlap ratio (0.0-1.0): intersection / union
        """
        if not answer_keywords:
            return 0.0
        
        intersection = answer_keywords & doc_keywords
        union = answer_keywords | doc_keywords
        
        if not union:
            return 0.0
        
        # Jaccard similarity: intersection / union
        return len(intersection) / len(union)

