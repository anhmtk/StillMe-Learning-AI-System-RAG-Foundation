"""
Knowledge Taxonomy for StillMe

This module provides a taxonomy for classifying knowledge types,
enabling more nuanced and transparent citations.

Based on StillMe Manifesto Principle 3: "NO ILLUSIONS" PRINCIPLE
- We value VERIFIABILITY over CREATIVITY
- Citation is better than no citation
- But citation must be MEANINGFUL, not just present

Knowledge Types:
1. SPECIFIC_SOURCE - High similarity (>=0.8) with specific document metadata
2. INFORMED_BY_CONTEXT - Medium similarity (>=0.5) with source type
3. SUPPLEMENTED_BY_CONTEXT - Low similarity (>=0.3) but has context
4. GENERAL_REASONING - No context or very low similarity (<0.3)
5. NO_INFORMATION - No context available at all
"""

import logging
from typing import List, Dict, Any, Optional, Tuple
from enum import Enum

logger = logging.getLogger(__name__)


class KnowledgeType(Enum):
    """Knowledge type classification"""
    SPECIFIC_SOURCE = "specific_source"
    INFORMED_BY_CONTEXT = "informed_by_context"
    SUPPLEMENTED_BY_CONTEXT = "supplemented_by_context"
    GENERAL_REASONING = "general_reasoning"
    NO_INFORMATION = "no_information"


class KnowledgeTaxonomy:
    """
    Classify knowledge types based on context quality and source specificity.
    
    This taxonomy enables StillMe to be transparent about the TYPE of knowledge
    being used, not just whether a citation exists.
    """
    
    def __init__(self):
        """Initialize knowledge taxonomy"""
        pass
    
    def classify_knowledge(
        self,
        context_quality: float,
        source_specificity: float,
        has_context: bool = False,
        max_similarity: Optional[float] = None,
        has_metadata: bool = False
    ) -> Tuple[KnowledgeType, str]:
        """
        Classify knowledge type based on context quality and source specificity.
        
        Args:
            context_quality: Quality of context (0.0-1.0), typically max_similarity
            source_specificity: Specificity of source (0.0-1.0), based on metadata presence
            has_context: Whether context documents are available
            max_similarity: Maximum similarity score (alternative to context_quality)
            has_metadata: Whether document metadata (title, source, date) is available
            
        Returns:
            Tuple of (KnowledgeType, human-readable description)
        """
        # Use max_similarity if provided, otherwise use context_quality
        similarity = max_similarity if max_similarity is not None else context_quality
        
        # Determine source_specificity from metadata if not provided
        if has_metadata and source_specificity == 0.0:
            source_specificity = 0.8  # High specificity if metadata available
        
        # Classification logic
        if not has_context or similarity is None or similarity < 0.1:
            return (
                KnowledgeType.NO_INFORMATION,
                "No information available - general reasoning"
            )
        
        elif similarity >= 0.8 and source_specificity > 0.7:
            return (
                KnowledgeType.SPECIFIC_SOURCE,
                "Specific information from source"
            )
        
        elif similarity >= 0.5:
            return (
                KnowledgeType.INFORMED_BY_CONTEXT,
                "Informed by retrieved context documents"
            )
        
        elif similarity >= 0.3:
            return (
                KnowledgeType.SUPPLEMENTED_BY_CONTEXT,
                "Background knowledge supplemented by context"
            )
        
        else:
            return (
                KnowledgeType.GENERAL_REASONING,
                "General knowledge inference"
            )
    
    def get_citation_for_knowledge_type(
        self,
        knowledge_type: KnowledgeType,
        source_name: Optional[str] = None,
        document_title: Optional[str] = None,
        document_date: Optional[str] = None,
        source_types: Optional[List[str]] = None
    ) -> str:
        """
        Get citation string for a specific knowledge type.
        
        Args:
            knowledge_type: Classified knowledge type
            source_name: Name of the source (if available)
            document_title: Title of the document (if available)
            document_date: Date of the document (if available)
            source_types: List of source types (e.g., ["wikipedia", "arxiv"])
            
        Returns:
            Human-readable citation string
        """
        if knowledge_type == KnowledgeType.SPECIFIC_SOURCE:
            # Level 1: Specific source with metadata
            if document_title and source_name:
                if document_date:
                    return f"[{document_title}, {source_name}, {document_date}]"
                else:
                    return f"[{document_title}, {source_name}]"
            elif source_name:
                return f"[Information from {source_name}]"
            elif source_types:
                primary_source = self._get_primary_source_name(source_types)
                return f"[Information from {primary_source} documents]"
            else:
                return "[Information from retrieved documents]"
        
        elif knowledge_type == KnowledgeType.INFORMED_BY_CONTEXT:
            # Level 2: Informed by context
            if source_types:
                primary_source = self._get_primary_source_name(source_types)
                return f"[Information from {primary_source} documents]"
            else:
                return "[Information from retrieved documents]"
        
        elif knowledge_type == KnowledgeType.SUPPLEMENTED_BY_CONTEXT:
            # Level 3: Supplemented by context
            if source_types:
                primary_source = self._get_primary_source_name(source_types)
                return f"[Background knowledge informed by {primary_source} context]"
            else:
                return "[Background knowledge informed by retrieved context]"
        
        elif knowledge_type == KnowledgeType.GENERAL_REASONING:
            # Level 4: General reasoning
            if source_types:
                primary_source = self._get_primary_source_name(source_types)
                return f"[general knowledge] (Context from {primary_source} was reviewed but had low relevance)"
            else:
                return "[general knowledge] (I don't have specific sources for this information)"
        
        else:  # NO_INFORMATION
            # Level 5: No information
            if source_types:
                primary_source = self._get_primary_source_name(source_types)
                return f"[general knowledge] (Retrieved {primary_source} documents were reviewed but had no relevant information)"
            else:
                return "[general knowledge] (No relevant sources found in knowledge base)"
    
    def _get_primary_source_name(self, source_types: List[str]) -> str:
        """
        Get primary source name from source types list.
        
        Priority: Wikipedia > arXiv > RSS > Conversation > Other
        
        Args:
            source_types: List of source type strings
            
        Returns:
            Primary source name
        """
        if not source_types:
            return "retrieved"
        
        # Priority order
        priority_sources = {
            "wikipedia": "Wikipedia",
            "arxiv": "arXiv",
            "rss_feed": "RSS",
            "conversation": "conversation",
            "textbook": "textbook",
            "foundational": "foundational knowledge"
        }
        
        for source_type in source_types:
            source_lower = source_type.lower()
            for key, name in priority_sources.items():
                if key in source_lower:
                    return name
        
        # Default to first source type or "retrieved"
        return source_types[0] if source_types else "retrieved"


# Global taxonomy instance
_knowledge_taxonomy: Optional[KnowledgeTaxonomy] = None


def get_knowledge_taxonomy() -> KnowledgeTaxonomy:
    """Get global knowledge taxonomy instance"""
    global _knowledge_taxonomy
    if _knowledge_taxonomy is None:
        _knowledge_taxonomy = KnowledgeTaxonomy()
    return _knowledge_taxonomy

