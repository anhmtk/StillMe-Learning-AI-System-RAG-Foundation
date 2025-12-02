"""
Abstract Learning Pipeline Interface

Defines the interface for learning systems that can:
- Fetch content from various sources
- Filter and curate content
- Add to knowledge base
- Track learning metrics
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Optional, Any
from dataclasses import dataclass
from datetime import datetime


@dataclass
class LearningResult:
    """Result of a learning cycle"""
    cycle_number: int
    timestamp: str  # ISO format
    entries_fetched: int
    entries_added: int
    entries_filtered: int
    sources: Dict[str, int]  # source -> entries_fetched
    duration_seconds: float
    error: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class LearningFetcher(ABC):
    """
    Abstract interface for content fetchers
    
    Implementations should fetch content from specific sources
    (RSS, arXiv, CrossRef, Wikipedia, etc.)
    """
    
    @abstractmethod
    def fetch(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Fetch content from source
        
        Args:
            limit: Maximum number of entries to fetch (None = no limit)
            
        Returns:
            List of content entries (dicts with title, content, source, etc.)
        """
        pass
    
    @abstractmethod
    def get_source_name(self) -> str:
        """Get name of the source"""
        pass


class LearningPipeline(ABC):
    """
    Abstract learning pipeline interface
    
    Defines the contract for learning systems that can:
    1. Fetch content from multiple sources
    2. Filter and curate content
    3. Add curated content to knowledge base
    4. Track metrics
    """
    
    @abstractmethod
    def run_learning_cycle(self) -> LearningResult:
        """
        Run a single learning cycle
        
        Returns:
            LearningResult with cycle metrics
        """
        pass
    
    @abstractmethod
    def get_fetchers(self) -> List[LearningFetcher]:
        """
        Get list of content fetchers
        
        Returns:
            List of LearningFetcher instances
        """
        pass
    
    @abstractmethod
    def filter_content(self, entries: List[Dict[str, Any]]) -> tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        Filter content entries
        
        Args:
            entries: List of content entries to filter
            
        Returns:
            Tuple of (accepted_entries, filtered_entries)
        """
        pass
    
    @abstractmethod
    def add_to_knowledge_base(self, entries: List[Dict[str, Any]]) -> int:
        """
        Add entries to knowledge base
        
        Args:
            entries: List of content entries to add
            
        Returns:
            Number of entries successfully added
        """
        pass

