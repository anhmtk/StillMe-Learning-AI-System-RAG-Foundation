"""
RSS Feed Fetcher for StillMe
Simple RSS fetching service to populate knowledge base
"""

import feedparser
from typing import List, Dict, Any
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class RSSFetcher:
    """Simple RSS feed fetcher"""
    
    def __init__(self):
        # Default trusted RSS feeds
        self.feeds = [
            "https://news.ycombinator.com/rss",
            "https://rss.nytimes.com/services/xml/rss/nyt/Technology.xml",
            # Add more trusted feeds here
        ]
    
    def fetch_feeds(self, max_items_per_feed: int = 5) -> List[Dict[str, Any]]:
        """Fetch entries from all RSS feeds
        
        Args:
            max_items_per_feed: Maximum items to fetch per feed
            
        Returns:
            List of feed entries
        """
        all_entries = []
        
        for feed_url in self.feeds:
            try:
                feed = feedparser.parse(feed_url)
                
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
                
                logger.info(f"Fetched {len(feed.entries[:max_items_per_feed])} items from {feed_url}")
                
            except Exception as e:
                logger.error(f"Failed to fetch {feed_url}: {e}")
        
        logger.info(f"Total entries fetched: {len(all_entries)}")
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
            logger.error(f"Failed to fetch {feed_url}: {e}")
            return []

