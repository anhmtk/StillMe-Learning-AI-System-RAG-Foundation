"""
URL Fetcher for StillMe
Fetches content from arbitrary URLs (articles, RSS feeds, etc.) for community proposals
"""

import requests
import feedparser
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
from urllib.parse import urlparse
import re

logger = logging.getLogger(__name__)

# Request configuration
REQUEST_TIMEOUT = 30  # seconds
MAX_CONTENT_LENGTH = 1_000_000  # 1MB max content
USER_AGENT = "StillMe-Learning-AI/1.0 (Community Proposal Fetcher)"


class URLFetcher:
    """Fetches content from URLs for community proposals"""
    
    def __init__(self):
        """Initialize URL fetcher"""
        logger.info("URL Fetcher initialized")
    
    def fetch_content(self, url: str, proposal_type: str = "Article") -> Optional[Dict[str, Any]]:
        """
        Fetch content from a URL
        
        Args:
            url: URL to fetch
            proposal_type: Type of proposal (RSS Feed, Article, etc.)
            
        Returns:
            Dict with content data or None if failed
        """
        try:
            # Check if it's an RSS feed
            if proposal_type.lower() == "rss feed" or self._is_rss_feed(url):
                return self._fetch_rss_feed(url)
            else:
                return self._fetch_article(url)
        except Exception as e:
            logger.error(f"Error fetching content from {url}: {e}")
            return None
    
    def _is_rss_feed(self, url: str) -> bool:
        """Check if URL is an RSS feed"""
        parsed = urlparse(url)
        path_lower = parsed.path.lower()
        return any(ext in path_lower for ext in ['.rss', '.xml', '/feed', '/rss', '/atom'])
    
    def _fetch_rss_feed(self, url: str) -> Optional[Dict[str, Any]]:
        """Fetch content from RSS feed"""
        try:
            feed = feedparser.parse(url)
            
            if feed.bozo and feed.bozo_exception:
                logger.warning(f"RSS feed parse error for {url}: {feed.bozo_exception}")
                return None
            
            if not feed.entries:
                logger.warning(f"RSS feed has no entries: {url}")
                return None
            
            # Get the most recent entry
            entry = feed.entries[0]
            
            return {
                "title": entry.get("title", ""),
                "summary": entry.get("summary", entry.get("description", "")),
                "link": entry.get("link", url),
                "published": entry.get("published", datetime.now().isoformat()),
                "source": url,
                "content_type": "rss_feed",
                "success": True
            }
        except Exception as e:
            logger.error(f"Error fetching RSS feed {url}: {e}")
            return None
    
    def _fetch_article(self, url: str) -> Optional[Dict[str, Any]]:
        """Fetch content from article URL"""
        try:
            headers = {
                "User-Agent": USER_AGENT,
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
            }
            
            response = requests.get(url, headers=headers, timeout=REQUEST_TIMEOUT)
            response.raise_for_status()
            
            # Check content length
            if len(response.content) > MAX_CONTENT_LENGTH:
                logger.warning(f"Content too large ({len(response.content)} bytes): {url}")
                return None
            
            # Extract text content (simple extraction, can be enhanced with BeautifulSoup)
            content = self._extract_text_from_html(response.text)
            
            if not content or len(content.strip()) < 150:
                logger.warning(f"Content too short or empty: {url}")
                return None
            
            # Extract title (try multiple methods)
            title = self._extract_title(response.text, url)
            
            # Get first 500 chars as summary
            summary = content[:500] + "..." if len(content) > 500 else content
            
            return {
                "title": title,
                "summary": summary,
                "link": url,
                "published": datetime.now().isoformat(),  # Use current time if not available
                "source": url,
                "content_type": "article",
                "full_content": content[:5000],  # Store first 5000 chars
                "success": True
            }
        except requests.exceptions.RequestException as e:
            logger.error(f"HTTP error fetching {url}: {e}")
            return None
        except Exception as e:
            logger.error(f"Error fetching article {url}: {e}")
            return None
    
    def _extract_text_from_html(self, html: str) -> str:
        """Extract text content from HTML (simple implementation)"""
        # Remove script and style tags
        html = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.DOTALL | re.IGNORECASE)
        html = re.sub(r'<style[^>]*>.*?</style>', '', html, flags=re.DOTALL | re.IGNORECASE)
        
        # Extract text from common content tags
        text_patterns = [
            r'<article[^>]*>(.*?)</article>',
            r'<main[^>]*>(.*?)</main>',
            r'<div[^>]*class="[^"]*content[^"]*"[^>]*>(.*?)</div>',
            r'<p[^>]*>(.*?)</p>',
        ]
        
        extracted_text = []
        for pattern in text_patterns:
            matches = re.findall(pattern, html, flags=re.DOTALL | re.IGNORECASE)
            extracted_text.extend(matches)
        
        if not extracted_text:
            # Fallback: extract all text between tags
            text = re.sub(r'<[^>]+>', ' ', html)
        else:
            text = ' '.join(extracted_text)
        
        # Clean up whitespace
        text = re.sub(r'\s+', ' ', text)
        text = text.strip()
        
        return text
    
    def _extract_title(self, html: str, url: str) -> str:
        """Extract title from HTML"""
        # Try <title> tag
        title_match = re.search(r'<title[^>]*>(.*?)</title>', html, re.IGNORECASE | re.DOTALL)
        if title_match:
            title = re.sub(r'<[^>]+>', '', title_match.group(1)).strip()
            if title:
                return title[:200]  # Limit length
        
        # Try <h1> tag
        h1_match = re.search(r'<h1[^>]*>(.*?)</h1>', html, re.IGNORECASE | re.DOTALL)
        if h1_match:
            title = re.sub(r'<[^>]+>', '', h1_match.group(1)).strip()
            if title:
                return title[:200]
        
        # Fallback: use URL
        parsed = urlparse(url)
        return parsed.path.split('/')[-1] or url


def get_url_fetcher() -> URLFetcher:
    """Get singleton URL fetcher instance"""
    if not hasattr(get_url_fetcher, '_instance'):
        get_url_fetcher._instance = URLFetcher()
    return get_url_fetcher._instance

