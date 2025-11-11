"""
RSS Feed Fetcher for StillMe
Simple RSS fetching service to populate knowledge base
"""

import feedparser
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class RSSFetcher:
    """Simple RSS feed fetcher"""
    
    def __init__(self):
        # Default trusted RSS feeds
        self.feeds = [
            # Existing feeds
            "https://news.ycombinator.com/rss",
            "https://rss.nytimes.com/services/xml/rss/nyt/Technology.xml",
            
            # Statistics
            "https://www.r-bloggers.com/feed/",
            "https://feeds.feedburner.com/StatisticalModelingCausalInferenceAndSocialScience",
            
            # Psychology
            "https://www.psychologicalscience.org/feed",
            
            # Biology
            "https://www.nature.com/nature.rss",
            "https://www.sciencedaily.com/rss/matter_energy.xml",  # ScienceDaily Biology
            
            # Physics
            "https://physicsworld.com/feed/",
            "https://phys.org/rss-feed/physics-news/",  # Phys.org Physics
            
            # Chemistry
            # Note: Some chemistry feeds may be empty - will be monitored and replaced if needed
        ]
        # Track error states for self-diagnosis
        self.last_error: Optional[str] = None
        self.error_count = 0
        self.last_success_time: Optional[datetime] = None
        self.successful_feeds = 0
        self.failed_feeds = 0
    
    def fetch_feeds(self, max_items_per_feed: int = 5) -> List[Dict[str, Any]]:
        """Fetch entries from all RSS feeds
        
        Args:
            max_items_per_feed: Maximum items to fetch per feed
            
        Returns:
            List of feed entries
        """
        all_entries = []
        self.successful_feeds = 0
        self.failed_feeds = 0
        errors = []
        
        for feed_url in self.feeds:
            try:
                feed = feedparser.parse(feed_url)
                
                # Check if feed parsing was successful
                if feed.bozo and feed.bozo_exception:
                    error_msg = f"RSS feed parse error for {feed_url}: {feed.bozo_exception}"
                    errors.append(error_msg)
                    self.failed_feeds += 1
                    logger.warning(error_msg)
                    continue
                
                for entry in feed.entries[:max_items_per_feed]:
                    entry_data = {
                        "title": entry.get("title", ""),
                        "summary": entry.get("summary", entry.get("description", "")),
                        "link": entry.get("link", ""),
                        "published": entry.get("published", datetime.now().isoformat()),
                        "source": feed_url,
                        "content_type": "knowledge"
                    }
                    all_entries.append(entry_data)
                
                self.successful_feeds += 1
                logger.info(f"Fetched {len(feed.entries[:max_items_per_feed])} items from {feed_url}")
                
            except Exception as e:
                error_msg = f"Failed to fetch {feed_url}: {e}"
                errors.append(error_msg)
                self.failed_feeds += 1
                self.error_count += 1
                logger.error(error_msg)
        
        # Update error state
        if errors:
            self.last_error = "; ".join(errors[:3])  # Keep first 3 errors
        else:
            self.last_error = None
            self.last_success_time = datetime.now()
        
        logger.info(f"Total entries fetched: {len(all_entries)} (successful: {self.successful_feeds}, failed: {self.failed_feeds})")
        return all_entries
    
    def fetch_single_feed(self, feed_url: str, max_items: int = 5) -> List[Dict[str, Any]]:
        """Fetch entries from a single RSS feed"""
        try:
            feed = feedparser.parse(feed_url)
            entries = []
            
            for entry in feed.entries[:max_items]:
                entry_data = {
                    "title": entry.get("title", ""),
                    "summary": entry.get("summary", entry.get("description", "")),
                    "link": entry.get("link", ""),
                    "published": entry.get("published", datetime.now().isoformat()),
                    "source": feed_url,
                    "content_type": "knowledge"
                }
                entries.append(entry_data)
            
            return entries
            
        except Exception as e:
            error_msg = f"Failed to fetch {feed_url}: {e}"
            self.last_error = error_msg
            self.error_count += 1
            logger.error(error_msg)
            return []
    
    def get_stats(self) -> Dict[str, Any]:
        """Get fetcher statistics"""
        return {
            "source": "rss",
            "feeds_count": len(self.feeds),
            "successful_feeds": self.successful_feeds,
            "failed_feeds": self.failed_feeds,
            "error_count": self.error_count,
            "last_error": self.last_error,
            "last_success_time": self.last_success_time.isoformat() if self.last_success_time else None,
            "status": "error" if self.last_error and (not self.last_success_time or self.failed_feeds > 0) else "ok"
        }

