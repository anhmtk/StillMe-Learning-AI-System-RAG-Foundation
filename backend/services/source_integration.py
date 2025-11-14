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
from backend.services.papers_with_code_fetcher import PapersWithCodeFetcher
from backend.services.conference_fetcher import ConferenceFetcher
from backend.services.stanford_encyclopedia_fetcher import StanfordEncyclopediaFetcher

logger = logging.getLogger(__name__)

# Feature flags for new sources
ENABLE_ARXIV = os.getenv("ENABLE_ARXIV", "true").lower() == "true"
ENABLE_CROSSREF = os.getenv("ENABLE_CROSSREF", "true").lower() == "true"
ENABLE_WIKIPEDIA = os.getenv("ENABLE_WIKIPEDIA", "true").lower() == "true"
ENABLE_PAPERS_WITH_CODE = os.getenv("ENABLE_PAPERS_WITH_CODE", "true").lower() == "true"
ENABLE_CONFERENCES = os.getenv("ENABLE_CONFERENCES", "true").lower() == "true"
ENABLE_STANFORD_ENCYCLOPEDIA = os.getenv("ENABLE_STANFORD_ENCYCLOPEDIA", "true").lower() == "true"


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
        self.papers_with_code_fetcher = PapersWithCodeFetcher() if ENABLE_PAPERS_WITH_CODE else None
        self.conference_fetcher = ConferenceFetcher() if ENABLE_CONFERENCES else None
        self.stanford_encyclopedia_fetcher = StanfordEncyclopediaFetcher() if ENABLE_STANFORD_ENCYCLOPEDIA else None
        self.content_curator = content_curator or ContentCurator()
        
        logger.info(f"Source Integration initialized: arXiv={ENABLE_ARXIV}, CrossRef={ENABLE_CROSSREF}, Wikipedia={ENABLE_WIKIPEDIA}, "
                   f"PapersWithCode={ENABLE_PAPERS_WITH_CODE}, Conferences={ENABLE_CONFERENCES}, StanfordEncyclopedia={ENABLE_STANFORD_ENCYCLOPEDIA}")
    
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
            
            # Update system status tracker with RSS fetcher status
            from backend.services.system_status_tracker import get_system_status_tracker
            status_tracker = get_system_status_tracker()
            rss_stats = self.rss_fetcher.get_stats()
            if rss_stats.get("status") == "error":
                status_tracker.update_component_status(
                    component_name="rss_fetcher",
                    status="error",
                    error_message=rss_stats.get("last_error", "Unknown error"),
                    error_count=rss_stats.get("error_count", 0),
                    last_success=datetime.fromisoformat(rss_stats["last_success_time"]) if rss_stats.get("last_success_time") else None
                )
            else:
                status_tracker.update_component_status(
                    component_name="rss_fetcher",
                    status="ok",
                    error_message=None,
                    error_count=0,
                    last_success=datetime.now()
                )
        except Exception as e:
            logger.error(f"Error fetching RSS: {e}")
            # Track error in system status
            from backend.services.system_status_tracker import get_system_status_tracker
            status_tracker = get_system_status_tracker()
            status_tracker.update_component_status(
                component_name="rss_fetcher",
                status="error",
                error_message=str(e),
                error_count=1
            )
        
        # Fetch from arXiv
        if self.arxiv_fetcher and ENABLE_ARXIV:
            try:
                arxiv_entries = self.arxiv_fetcher.fetch_recent_papers(max_results=max_items_per_source)
                all_entries.extend(arxiv_entries)
                logger.info(f"Fetched {len(arxiv_entries)} entries from arXiv")
                
                # Update system status tracker with arXiv fetcher status
                from backend.services.system_status_tracker import get_system_status_tracker
                status_tracker = get_system_status_tracker()
                arxiv_stats = self.arxiv_fetcher.get_stats()
                if arxiv_stats.get("status") == "error":
                    status_tracker.update_component_status(
                        component_name="arxiv_fetcher",
                        status="error",
                        error_message=arxiv_stats.get("last_error", "Unknown error"),
                        error_count=arxiv_stats.get("error_count", 0),
                        last_success=datetime.fromisoformat(arxiv_stats["last_success_time"]) if arxiv_stats.get("last_success_time") else None
                    )
                else:
                    status_tracker.update_component_status(
                        component_name="arxiv_fetcher",
                        status="ok",
                        error_message=None,
                        error_count=0,
                        last_success=datetime.now()
                    )
            except Exception as e:
                logger.error(f"Error fetching arXiv: {e}")
                # Track error in system status
                from backend.services.system_status_tracker import get_system_status_tracker
                status_tracker = get_system_status_tracker()
                status_tracker.update_component_status(
                    component_name="arxiv_fetcher",
                    status="error",
                    error_message=str(e),
                    error_count=1
                )
        
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
                
                # Update system status tracker with CrossRef fetcher status
                from backend.services.system_status_tracker import get_system_status_tracker
                status_tracker = get_system_status_tracker()
                crossref_stats = self.crossref_fetcher.get_stats()
                if crossref_stats.get("status") == "error":
                    status_tracker.update_component_status(
                        component_name="crossref_fetcher",
                        status="error",
                        error_message=crossref_stats.get("last_error", "Unknown error"),
                        error_count=crossref_stats.get("error_count", 0),
                        last_success=datetime.fromisoformat(crossref_stats["last_success_time"]) if crossref_stats.get("last_success_time") else None
                    )
                else:
                    status_tracker.update_component_status(
                        component_name="crossref_fetcher",
                        status="ok",
                        error_message=None,
                        error_count=0,
                        last_success=datetime.now()
                    )
            except Exception as e:
                logger.error(f"Error fetching CrossRef: {e}")
                # Track error in system status
                from backend.services.system_status_tracker import get_system_status_tracker
                status_tracker = get_system_status_tracker()
                status_tracker.update_component_status(
                    component_name="crossref_fetcher",
                    status="error",
                    error_message=str(e),
                    error_count=1
                )
        
        # Fetch from Wikipedia
        if self.wikipedia_fetcher and ENABLE_WIKIPEDIA:
            try:
                # Search for diverse topics including AI, religion, philosophy
                wikipedia_queries = [
                    "artificial intelligence",
                    "Buddhism",
                    "religious studies",
                    "philosophy of religion",
                    "ethics"
                ]
                
                all_wikipedia_entries = []
                items_per_query = max(1, max_items_per_source // len(wikipedia_queries))
                
                for query in wikipedia_queries:
                    try:
                        query_entries = self.wikipedia_fetcher.search_articles(
                            query=query,
                            max_results=items_per_query
                        )
                        all_wikipedia_entries.extend(query_entries)
                        logger.debug(f"Fetched {len(query_entries)} Wikipedia entries for query: {query}")
                    except Exception as query_error:
                        logger.warning(f"Error fetching Wikipedia articles for query '{query}': {query_error}")
                        continue
                
                all_entries.extend(all_wikipedia_entries)
                logger.info(f"Fetched {len(all_wikipedia_entries)} total entries from Wikipedia ({len(wikipedia_queries)} queries)")
                
                # Update system status tracker with Wikipedia fetcher status
                from backend.services.system_status_tracker import get_system_status_tracker
                status_tracker = get_system_status_tracker()
                wikipedia_stats = self.wikipedia_fetcher.get_stats()
                if wikipedia_stats.get("status") == "error":
                    status_tracker.update_component_status(
                        component_name="wikipedia_fetcher",
                        status="error",
                        error_message=wikipedia_stats.get("last_error", "Unknown error"),
                        error_count=wikipedia_stats.get("error_count", 0),
                        last_success=datetime.fromisoformat(wikipedia_stats["last_success_time"]) if wikipedia_stats.get("last_success_time") else None
                    )
                else:
                    status_tracker.update_component_status(
                        component_name="wikipedia_fetcher",
                        status="ok",
                        error_message=None,
                        error_count=0,
                        last_success=datetime.now()
                    )
            except Exception as e:
                logger.error(f"Error fetching Wikipedia: {e}")
                # Track error in system status
                from backend.services.system_status_tracker import get_system_status_tracker
                status_tracker = get_system_status_tracker()
                status_tracker.update_component_status(
                    component_name="wikipedia_fetcher",
                    status="error",
                    error_message=str(e),
                    error_count=1
                )
        
        # Fetch from Papers with Code
        if self.papers_with_code_fetcher and ENABLE_PAPERS_WITH_CODE:
            try:
                papers_entries = self.papers_with_code_fetcher.fetch_recent_papers(max_results=max_items_per_source)
                all_entries.extend(papers_entries)
                logger.info(f"Fetched {len(papers_entries)} entries from Papers with Code")
                
                # Update system status tracker
                from backend.services.system_status_tracker import get_system_status_tracker
                status_tracker = get_system_status_tracker()
                papers_stats = self.papers_with_code_fetcher.get_stats()
                if papers_stats.get("status") == "error":
                    status_tracker.update_component_status(
                        component_name="papers_with_code_fetcher",
                        status="error",
                        error_message=papers_stats.get("last_error", "Unknown error"),
                        error_count=papers_stats.get("error_count", 0),
                        last_success=datetime.fromisoformat(papers_stats["last_success_time"]) if papers_stats.get("last_success_time") else None
                    )
                else:
                    status_tracker.update_component_status(
                        component_name="papers_with_code_fetcher",
                        status="ok",
                        error_message=None,
                        error_count=0,
                        last_success=datetime.now()
                    )
            except Exception as e:
                logger.error(f"Error fetching Papers with Code: {e}")
                from backend.services.system_status_tracker import get_system_status_tracker
                status_tracker = get_system_status_tracker()
                status_tracker.update_component_status(
                    component_name="papers_with_code_fetcher",
                    status="error",
                    error_message=str(e),
                    error_count=1
                )
        
        # Fetch from Conference Proceedings
        if self.conference_fetcher and ENABLE_CONFERENCES:
            try:
                conference_entries = self.conference_fetcher.fetch_recent_papers(max_results=max_items_per_source)
                all_entries.extend(conference_entries)
                logger.info(f"Fetched {len(conference_entries)} entries from Conference Proceedings")
                
                # Update system status tracker
                from backend.services.system_status_tracker import get_system_status_tracker
                status_tracker = get_system_status_tracker()
                conference_stats = self.conference_fetcher.get_stats()
                if conference_stats.get("status") == "error":
                    status_tracker.update_component_status(
                        component_name="conference_fetcher",
                        status="error",
                        error_message=conference_stats.get("last_error", "Unknown error"),
                        error_count=conference_stats.get("error_count", 0),
                        last_success=datetime.fromisoformat(conference_stats["last_success_time"]) if conference_stats.get("last_success_time") else None
                    )
                else:
                    status_tracker.update_component_status(
                        component_name="conference_fetcher",
                        status="ok",
                        error_message=None,
                        error_count=0,
                        last_success=datetime.now()
                    )
            except Exception as e:
                logger.error(f"Error fetching Conference Proceedings: {e}")
                from backend.services.system_status_tracker import get_system_status_tracker
                status_tracker = get_system_status_tracker()
                status_tracker.update_component_status(
                    component_name="conference_fetcher",
                    status="error",
                    error_message=str(e),
                    error_count=1
                )
        
        # Fetch from Stanford Encyclopedia of Philosophy
        if self.stanford_encyclopedia_fetcher and ENABLE_STANFORD_ENCYCLOPEDIA:
            try:
                sep_entries = self.stanford_encyclopedia_fetcher.fetch_recent_entries(max_results=max_items_per_source)
                all_entries.extend(sep_entries)
                logger.info(f"Fetched {len(sep_entries)} entries from Stanford Encyclopedia")
                
                # Update system status tracker
                from backend.services.system_status_tracker import get_system_status_tracker
                status_tracker = get_system_status_tracker()
                sep_stats = self.stanford_encyclopedia_fetcher.get_stats()
                if sep_stats.get("status") == "error":
                    status_tracker.update_component_status(
                        component_name="stanford_encyclopedia_fetcher",
                        status="error",
                        error_message=sep_stats.get("last_error", "Unknown error"),
                        error_count=sep_stats.get("error_count", 0),
                        last_success=datetime.fromisoformat(sep_stats["last_success_time"]) if sep_stats.get("last_success_time") else None
                    )
                else:
                    status_tracker.update_component_status(
                        component_name="stanford_encyclopedia_fetcher",
                        status="ok",
                        error_message=None,
                        error_count=0,
                        last_success=datetime.now()
                    )
            except Exception as e:
                logger.error(f"Error fetching Stanford Encyclopedia: {e}")
                from backend.services.system_status_tracker import get_system_status_tracker
                status_tracker = get_system_status_tracker()
                status_tracker.update_component_status(
                    component_name="stanford_encyclopedia_fetcher",
                    status="error",
                    error_message=str(e),
                    error_count=1
                )
        
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
            },
            "papers_with_code": {
                "enabled": ENABLE_PAPERS_WITH_CODE,
                "stats": self.papers_with_code_fetcher.get_stats() if self.papers_with_code_fetcher else None
            },
            "conferences": {
                "enabled": ENABLE_CONFERENCES,
                "stats": self.conference_fetcher.get_stats() if self.conference_fetcher else None
            },
            "stanford_encyclopedia": {
                "enabled": ENABLE_STANFORD_ENCYCLOPEDIA,
                "stats": self.stanford_encyclopedia_fetcher.get_stats() if self.stanford_encyclopedia_fetcher else None
            }
        }
        return stats

