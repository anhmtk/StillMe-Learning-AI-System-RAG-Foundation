"""
Source Integration Service for StillMe
Integrates multiple data sources (RSS, arXiv, CrossRef, Wikipedia) into unified pipeline
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
import os

from backend.services.rss_fetcher import RSSFetcher
from backend.services.arxiv_fetcher import ArxivFetcher
from backend.services.crossref_fetcher import CrossrefFetcher
from backend.services.wikipedia_fetcher import WikipediaFetcher
from backend.services.content_curator import ContentCurator

logger = logging.getLogger(__name__)

# Feature flags for new sources
ENABLE_ARXIV = os.getenv("ENABLE_ARXIV", "true").lower() == "true"
ENABLE_CROSSREF = os.getenv("ENABLE_CROSSREF", "true").lower() == "true"
ENABLE_WIKIPEDIA = os.getenv("ENABLE_WIKIPEDIA", "true").lower() == "true"


class SourceIntegration:
    """Integrates multiple data sources into unified learning pipeline"""
    
    def __init__(self,
                 content_curator: Optional[ContentCurator] = None):
        """
        Initialize source integration service
        
        Args:
            content_curator: ContentCurator instance for pre-filtering
        """
        self.rss_fetcher = RSSFetcher()
        self.arxiv_fetcher = ArxivFetcher() if ENABLE_ARXIV else None
        self.crossref_fetcher = CrossrefFetcher() if ENABLE_CROSSREF else None
        self.wikipedia_fetcher = WikipediaFetcher() if ENABLE_WIKIPEDIA else None
        self.content_curator = content_curator or ContentCurator()
        
        logger.info(f"Source Integration initialized: arXiv={ENABLE_ARXIV}, CrossRef={ENABLE_CROSSREF}, Wikipedia={ENABLE_WIKIPEDIA}")
    
    def fetch_all_sources(self,
                         max_items_per_source: int = 5,
                         use_pre_filter: bool = True) -> List[Dict[str, Any]]:
        """
        Fetch content from all enabled sources
        
        Args:
            max_items_per_source: Maximum items per source
            use_pre_filter: Whether to apply pre-filter
            
        Returns:
            List of all fetched entries (filtered if use_pre_filter=True)
        """
        all_entries = []
        
        # Fetch from RSS (always enabled)
        try:
            rss_entries = self.rss_fetcher.fetch_feeds(max_items_per_feed=max_items_per_source)
            all_entries.extend(rss_entries)
            logger.info(f"Fetched {len(rss_entries)} entries from RSS")
        except Exception as e:
            logger.error(f"Error fetching RSS: {e}")
        
        # Fetch from arXiv
        if self.arxiv_fetcher and ENABLE_ARXIV:
            try:
                arxiv_entries = self.arxiv_fetcher.fetch_recent_papers(max_results=max_items_per_source)
                all_entries.extend(arxiv_entries)
                logger.info(f"Fetched {len(arxiv_entries)} entries from arXiv")
            except Exception as e:
                logger.error(f"Error fetching arXiv: {e}")
        
        # Fetch from CrossRef
        if self.crossref_fetcher and ENABLE_CROSSREF:
            try:
                # Search for AI/ML/NLP related works
                crossref_entries = self.crossref_fetcher.fetch_recent_works(
                    query="artificial intelligence OR machine learning OR natural language processing",
                    max_results=max_items_per_source
                )
                all_entries.extend(crossref_entries)
                logger.info(f"Fetched {len(crossref_entries)} entries from CrossRef")
            except Exception as e:
                logger.error(f"Error fetching CrossRef: {e}")
        
        # Fetch from Wikipedia
        if self.wikipedia_fetcher and ENABLE_WIKIPEDIA:
            try:
                # Search for AI-related articles
                wikipedia_entries = self.wikipedia_fetcher.search_articles(
                    query="artificial intelligence",
                    max_results=max_items_per_source
                )
                all_entries.extend(wikipedia_entries)
                logger.info(f"Fetched {len(wikipedia_entries)} entries from Wikipedia")
            except Exception as e:
                logger.error(f"Error fetching Wikipedia: {e}")
        
        # Apply pre-filter if enabled
        if use_pre_filter and all_entries:
            filtered, rejected = self.content_curator.pre_filter_content(all_entries)
            logger.info(f"Pre-filter: {len(filtered)} passed, {len(rejected)} rejected")
            return filtered
        
        return all_entries
    
    def get_source_stats(self) -> Dict[str, Any]:
        """Get statistics for all sources"""
        stats = {
            "rss": {
                "enabled": True,
                "feeds_count": len(self.rss_fetcher.feeds) if self.rss_fetcher else 0
            },
            "arxiv": {
                "enabled": ENABLE_ARXIV,
                "stats": self.arxiv_fetcher.get_stats() if self.arxiv_fetcher else None
            },
            "crossref": {
                "enabled": ENABLE_CROSSREF,
                "stats": self.crossref_fetcher.get_stats() if self.crossref_fetcher else None
            },
            "wikipedia": {
                "enabled": ENABLE_WIKIPEDIA,
                "stats": self.wikipedia_fetcher.get_stats() if self.wikipedia_fetcher else None
            }
        }
        return stats

