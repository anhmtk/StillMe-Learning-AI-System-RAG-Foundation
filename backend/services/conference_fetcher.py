"""
Conference Proceedings Fetcher for StillMe
Fetches papers from NeurIPS, ICML, and other major AI conferences
"""

import httpx
import feedparser
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class ConferenceFetcher:
    """Fetcher for conference proceedings"""
    
    def __init__(self):
        # Conference RSS feeds and APIs
        self.conferences = {
            "neurips": {
                "name": "NeurIPS",
                "rss": None,  # papers.nips.cc/rss returns wrong content-type (HTML)
                "base_url": "https://papers.nips.cc",
                "api": None  # May require API key
            },
            "icml": {
                "name": "ICML",
                "rss": None,  # ICML doesn't have public RSS
                "base_url": "https://proceedings.mlr.press",
                "api": None
            },
            "acl": {
                "name": "ACL",
                "rss": "https://aclanthology.org/feed/",  # ACL Anthology RSS (has XML syntax errors - will attempt recovery)
                "base_url": "https://aclanthology.org",
                "api": None
            },
            "iclr": {
                "name": "ICLR",
                "rss": None,
                "base_url": "https://openreview.net",
                "api": None
            }
        }
        
        self.last_error: Optional[str] = None
        self.error_count = 0
        self.last_success_time: Optional[datetime] = None
        self.successful_fetches = 0
        self.failed_fetches = 0
    
    def fetch_recent_papers(self, max_results: int = 5, conference: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Fetch recent papers from conferences
        
        Args:
            max_results: Maximum number of papers per conference
            conference: Specific conference name (neurips, icml, acl, iclr) or None for all
            
        Returns:
            List of paper entries
        """
        all_entries = []
        conferences_to_fetch = [conference] if conference else list(self.conferences.keys())
        
        for conf_key in conferences_to_fetch:
            if conf_key not in self.conferences:
                continue
            
            conf_info = self.conferences[conf_key]
            
            try:
                # Try RSS feed first
                if conf_info.get("rss"):
                    entries = self._fetch_from_rss(conf_info["rss"], conf_info["name"], max_results)
                    all_entries.extend(entries)
                    self.successful_fetches += 1
                else:
                    # For conferences without RSS, we'll need to scrape or use API
                    # For now, log that it's not available
                    logger.warning(f"RSS feed not available for {conf_info['name']}. Manual scraping required.")
                    # TODO: Implement web scraping for conferences without RSS
                    
            except Exception as e:
                error_msg = f"Failed to fetch {conf_info['name']}: {e}"
                self.last_error = error_msg
                self.error_count += 1
                self.failed_fetches += 1
                logger.error(error_msg)
        
        if all_entries:
            self.last_success_time = datetime.now()
        
        logger.info(f"Fetched {len(all_entries)} papers from conferences")
        return all_entries
    
    def _fetch_from_rss(self, rss_url: str, conference_name: str, max_results: int) -> List[Dict[str, Any]]:
        """Fetch papers from RSS feed with error recovery"""
        entries = []
        
        try:
            # Fetch with httpx to check content-type
            import httpx
            with httpx.Client(timeout=30.0, follow_redirects=True) as client:
                response = client.get(rss_url)
                
                # Check content-type
                content_type = response.headers.get("content-type", "").lower()
                if "text/html" in content_type:
                    logger.warning(f"RSS feed {rss_url} returned HTML instead of XML - may need HTML scraping")
                    # Try to parse anyway (some feeds return HTML with RSS content)
                
                # Try to parse as RSS/XML
                feed = feedparser.parse(response.text)
                
                # Handle parse errors with recovery
                if feed.bozo and feed.bozo_exception:
                    error_type = type(feed.bozo_exception).__name__
                    error_msg = str(feed.bozo_exception)
                    
                    # Try to recover from common XML errors
                    if "not well-formed" in error_msg.lower() or "malformed" in error_msg.lower():
                        logger.warning(f"Malformed XML for {rss_url}, attempting recovery...")
                        # Try sanitizing XML
                        from backend.services.rss_fetcher_enhanced import sanitize_xml
                        sanitized = sanitize_xml(response.text)
                        feed = feedparser.parse(sanitized)
                        if feed.bozo:
                            raise Exception(f"RSS parse error (recovery failed): {feed.bozo_exception}")
                    elif "mismatched tag" in error_msg.lower():
                        logger.warning(f"Mismatched tag for {rss_url}, attempting recovery...")
                        from backend.services.rss_fetcher_enhanced import sanitize_xml
                        sanitized = sanitize_xml(response.text)
                        feed = feedparser.parse(sanitized)
                        if feed.bozo:
                            raise Exception(f"RSS parse error (recovery failed): {feed.bozo_exception}")
                    else:
                        raise Exception(f"RSS parse error: {feed.bozo_exception}")
                
                for entry in feed.entries[:max_results]:
                    entry_data = {
                        "title": entry.get("title", ""),
                        "summary": entry.get("summary", entry.get("description", "")),
                        "link": entry.get("link", ""),
                        "published": entry.get("published", datetime.now().isoformat()),
                        "source": f"conference_{conference_name.lower()}",
                        "content_type": "knowledge",
                        "metadata": {
                            "conference": conference_name,
                            "authors": entry.get("authors", []) if hasattr(entry, "authors") else []
                        }
                    }
                    entries.append(entry_data)
                    
        except Exception as e:
            logger.error(f"Error fetching RSS from {rss_url}: {e}")
            raise
        
        return entries
    
    def get_stats(self) -> Dict[str, Any]:
        """Get fetcher statistics"""
        return {
            "source": "conference_proceedings",
            "conferences": list(self.conferences.keys()),
            "successful_fetches": self.successful_fetches,
            "failed_fetches": self.failed_fetches,
            "error_count": self.error_count,
            "last_error": self.last_error,
            "last_success_time": self.last_success_time.isoformat() if self.last_success_time else None,
            "status": "error" if self.last_error and (not self.last_success_time or self.failed_fetches > 0) else "ok"
        }

