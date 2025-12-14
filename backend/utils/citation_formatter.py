"""
Citation Formatter for StillMe
Provides human-readable citation formats instead of [1], [2]
"""

import re
import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

# Citation format mapping
CITATION_FORMATS = {
    "base_knowledge": "[general knowledge]",
    "wikipedia": "[research: Wikipedia]",
    "arxiv": "[learning: arXiv]",
    "conversation": "[discussion context]",
    "rss_feed": "[news: {source_name}]",
    "textbook": "[reference: {book_title}]",
    "foundational": "[foundational knowledge]",
    "verified_sources": "[research: verified sources]",
    "needs_research": "[needs research]",
    "personal_analysis": "[personal analysis]"
}


class CitationFormatter:
    """Formatter for human-readable citations"""
    
    def __init__(self):
        """Initialize citation formatter"""
        self.base_knowledge_patterns = [
            # Basic facts
            r'capital of',
            r'what is 2\+2',
            r'who wrote (romeo and juliet|1984|harry potter)',
            r'largest planet',
            r'speed of light',
            # Common science
            r'how many planets',
            r'chemical symbol for',
            r'gravity on earth',
            # Basic math (fix regex: escape - in character class or use separate pattern)
            r'what is \d+ [+\-*/] \d+',  # Fixed: escape - in character class
            r'what is \d+\s*[+\-*/]\s*\d+',  # Alternative: with optional spaces
            r'prime number',
        ]
    
    def analyze_source_types(self, context_docs: List[Any]) -> List[str]:
        """
        Analyze source types from context documents
        
        Args:
            context_docs: List of context documents (dicts with metadata)
            
        Returns:
            List of detected source types (e.g., ['wikipedia', 'arxiv'])
        """
        source_types = []
        
        if not context_docs:
            return source_types
        
        for doc in context_docs:
            # Handle both dict format and object format
            if isinstance(doc, dict):
                metadata = doc.get('metadata', {})
            elif hasattr(doc, 'metadata'):
                metadata = doc.metadata if isinstance(doc.metadata, dict) else {}
            else:
                metadata = {}
            
            # Extract source information
            source = str(metadata.get('source', '')).lower()
            doc_type = str(metadata.get('type', '')).lower()
            content_type = str(metadata.get('content_type', '')).lower()
            domain = str(metadata.get('domain', '')).lower()
            title = str(metadata.get('title', '')).lower()
            
            # Detect source types
            if 'wikipedia' in source or 'wikipedia' in title:
                source_types.append('wikipedia')
            elif 'arxiv' in source or 'arxiv' in title or 'arxiv' in content_type:
                source_types.append('arxiv')
            elif any(feed in source for feed in ['rss', 'news', 'blog', 'feed']):
                # Extract source name if available
                source_name = metadata.get('source_name', source)
                source_types.append(f'rss:{source_name}')
            elif 'textbook' in source or 'reference' in source or 'book' in source:
                book_title = metadata.get('book_title', metadata.get('title', 'reference'))
                source_types.append(f'textbook:{book_title}')
            elif 'foundational' in source or 'foundational' in doc_type or 'foundational' in domain:
                source_types.append('foundational')
            elif 'conversation' in doc_type or 'conversation' in content_type:
                source_types.append('conversation')
            elif source and source != 'unknown':
                # Generic verified source
                source_types.append('verified')
        
        # Remove duplicates while preserving order
        seen = set()
        unique_types = []
        for st in source_types:
            if st not in seen:
                seen.add(st)
                unique_types.append(st)
        
        return unique_types
    
    def format_citation(self, source_types: List[str], question: Optional[str] = None) -> str:
        """
        Format citation based on source types
        
        Args:
            source_types: List of detected source types
            question: Optional question to help determine citation type
            
        Returns:
            Human-readable citation string
        """
        if not source_types:
            # No sources - check if base knowledge question
            if question and self.is_base_knowledge_question(question):
                return CITATION_FORMATS["base_knowledge"]
            return CITATION_FORMATS["base_knowledge"]
        
        # Prioritize source types (most specific first)
        if 'wikipedia' in source_types:
            return CITATION_FORMATS["wikipedia"]
        elif 'arxiv' in source_types:
            return CITATION_FORMATS["arxiv"]
        elif any(st.startswith('rss:') for st in source_types):
            # Extract RSS source name
            rss_source = next((st.split(':', 1)[1] for st in source_types if st.startswith('rss:')), 'RSS feed')
            return CITATION_FORMATS["rss_feed"].format(source_name=rss_source)
        elif any(st.startswith('textbook:') for st in source_types):
            # Extract textbook title
            textbook_title = next((st.split(':', 1)[1] for st in source_types if st.startswith('textbook:')), 'reference')
            return CITATION_FORMATS["textbook"].format(book_title=textbook_title)
        elif 'foundational' in source_types:
            return CITATION_FORMATS["foundational"]
        elif 'conversation' in source_types:
            return CITATION_FORMATS["conversation"]
        elif 'verified' in source_types:
            return CITATION_FORMATS["verified_sources"]
        else:
            # Default to verified sources
            return CITATION_FORMATS["verified_sources"]
    
    def is_base_knowledge_question(self, question: str) -> bool:
        """
        Detect if question is about base/common knowledge
        
        Args:
            question: User question
            
        Returns:
            True if question is about base knowledge
        """
        if not question:
            return False
        
        question_lower = question.lower()
        
        for pattern in self.base_knowledge_patterns:
            try:
                if re.search(pattern, question_lower, re.IGNORECASE):
                    return True
            except Exception as e:
                logger.warning(f"Error matching base knowledge pattern {pattern}: {e}")
                continue
        
        return False
    
    def get_citation_strategy(self, question: str, context_docs: List[Any], 
                             similarity_scores: Optional[List[float]] = None) -> str:
        """
        Get citation strategy based on question, context, and similarity scores
        
        PHASE 1 FIX: Implement citation hierarchy with 4 levels based on similarity and metadata
        This ensures citations trace to actual sources, not default to [general knowledge]
        
        Hierarchy:
        1. High similarity (>0.8) + metadata → [Document Title, Source, Date]
        2. Medium similarity (>0.5) + metadata → [Information from {Source} documents]
        3. Low similarity (>0.3) + metadata → [Background knowledge informed by retrieved context]
        4. No similarity or no metadata → [General knowledge] + "I don't have specific sources"
        
        Args:
            question: User question
            context_docs: List of context documents
            similarity_scores: Optional list of similarity scores for each context doc
            
        Returns:
            Human-readable citation string
        """
        if not context_docs:
            # No context - use base knowledge citation with transparency
            return "[general knowledge] (I don't have specific sources for this information)"
        
        # Analyze source types from context
        source_types = self.analyze_source_types(context_docs)
        
        # Extract similarity scores if available
        if similarity_scores and len(similarity_scores) == len(context_docs):
            max_similarity = max(similarity_scores)
            max_similarity_idx = similarity_scores.index(max_similarity)
            best_doc = context_docs[max_similarity_idx]
        else:
            # If no similarity scores, try to extract from doc metadata
            max_similarity = 0.0
            best_doc = context_docs[0] if context_docs else None
            # Try to get similarity from doc metadata
            for i, doc in enumerate(context_docs):
                if isinstance(doc, dict):
                    doc_similarity = doc.get('similarity', 0.0)
                elif hasattr(doc, 'similarity'):
                    doc_similarity = doc.similarity if isinstance(doc.similarity, (int, float)) else 0.0
                else:
                    doc_similarity = 0.0
                
                if doc_similarity > max_similarity:
                    max_similarity = doc_similarity
                    best_doc = doc
        
        # Hierarchy 1: High similarity (>0.8) + specific source metadata
        if max_similarity > 0.8 and best_doc:
            # Extract document metadata
            if isinstance(best_doc, dict):
                metadata = best_doc.get('metadata', {})
                if not metadata and 'metadata' not in best_doc:
                    metadata = best_doc  # Doc itself might be metadata dict
            elif hasattr(best_doc, 'metadata'):
                metadata = best_doc.metadata if isinstance(best_doc.metadata, dict) else {}
            else:
                metadata = {}
            
            title = metadata.get('title', '') or metadata.get('document_title', '')
            source = metadata.get('source', '') or metadata.get('source_name', '')
            date = metadata.get('date', '') or metadata.get('published_date', '') or metadata.get('timestamp', '')
            
            # Clean up values
            title = str(title).strip() if title else ''
            source = str(source).strip() if source else ''
            date = str(date).strip() if date else ''
            
            # If we have title and source, use specific citation
            if title and source:
                if date:
                    return f"[{title}, {source}, {date}]"
                else:
                    return f"[{title}, {source}]"
            # If we have source type but not specific metadata, use source type
            elif source_types:
                primary_source = self._get_primary_source_name(source_types)
                return f"[Information from {primary_source}]"
        
        # Hierarchy 2: Medium similarity (>0.5) + source type
        elif max_similarity > 0.5 and source_types:
            primary_source = self._get_primary_source_name(source_types)
            return f"[Information from {primary_source} documents]"
        
        # Hierarchy 3: Low similarity (>0.3) but has context
        elif max_similarity > 0.3:
            if source_types:
                primary_source = self._get_primary_source_name(source_types)
                return f"[Background knowledge informed by {primary_source} context]"
            else:
                return "[Background knowledge informed by retrieved context]"
        
        # Hierarchy 4: No meaningful context or very low similarity
        else:
            # If we have source types but low similarity, still acknowledge context
            if source_types:
                primary_source = self._get_primary_source_name(source_types)
                return f"[general knowledge] (Context from {primary_source} was reviewed but had low relevance)"
            else:
                return "[general knowledge] (I don't have specific sources for this information)"
    
    def _get_primary_source_name(self, source_types: List[str]) -> str:
        """
        Get primary source name from source types list
        
        Args:
            source_types: List of source types (e.g., ['wikipedia', 'arxiv', 'rss:CNN'])
            
        Returns:
            Primary source name (human-readable)
        """
        if not source_types:
            return "retrieved"
        
        # Priority order: Wikipedia > arXiv > RSS > others
        if 'wikipedia' in source_types:
            return "Wikipedia"
        elif 'arxiv' in source_types:
            return "arXiv"
        elif any(st.startswith('rss:') for st in source_types):
            rss_source = next((st.split(':', 1)[1] for st in source_types if st.startswith('rss:')), 'RSS feed')
            return rss_source
        elif 'foundational' in source_types:
            return "foundational knowledge"
        elif 'verified' in source_types:
            return "verified sources"
        else:
            # Return first source type, capitalized
            return source_types[0].replace('_', ' ').title()
    
    def replace_numeric_citations(self, text: str, citation: str) -> str:
        """
        Replace numeric citations [1], [2] with human-readable citation
        
        Args:
            text: Text with numeric citations
            citation: Human-readable citation to use
            
        Returns:
            Text with human-readable citation
        """
        # Pattern to match [1], [2], [123] etc.
        numeric_cite_pattern = re.compile(r'\[\d+\]')
        
        # Replace all numeric citations with human-readable one
        result = numeric_cite_pattern.sub(citation, text)
        
        return result
    
    def add_citation_to_response(self, response: str, citation: str) -> str:
        """
        Add citation to response in a natural way
        
        Args:
            response: Original response
            citation: Citation to add
            
        Returns:
            Response with citation added
        """
        if not response or not response.strip():
            return citation
        
        # Remove any existing numeric citations first
        response = re.sub(r'\[\d+\]', '', response).strip()
        
        # Check if response already has this citation
        if citation in response:
            return response
        
        # Add citation at the end
        if response.endswith(('.', '!', '?')):
            return f"{response} {citation}"
        else:
            return f"{response}. {citation}"


# Global formatter instance
_citation_formatter: Optional[CitationFormatter] = None


def get_citation_formatter() -> CitationFormatter:
    """Get global citation formatter instance"""
    global _citation_formatter
    if _citation_formatter is None:
        _citation_formatter = CitationFormatter()
    return _citation_formatter

