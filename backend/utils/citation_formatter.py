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
            # Basic math
            r'what is \d+ [+-\*/] \d+',
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
    
    def get_citation_strategy(self, question: str, context_docs: List[Any]) -> str:
        """
        Get citation strategy based on question and context
        
        Args:
            question: User question
            context_docs: List of context documents
            
        Returns:
            Human-readable citation string
        """
        # 1. Analyze source types from context
        source_types = self.analyze_source_types(context_docs)
        
        # 2. If we have context, use research citation
        if source_types:
            return self.format_citation(source_types, question)
        
        # 3. If no context but base knowledge question, use general knowledge citation
        if self.is_base_knowledge_question(question):
            return CITATION_FORMATS["base_knowledge"]
        
        # 4. Default to general knowledge
        return CITATION_FORMATS["base_knowledge"]
    
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

