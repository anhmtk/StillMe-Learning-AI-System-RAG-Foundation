"""
StillMe RSS Fetcher
RSS/API-only content fetching with no HTML crawling.
"""

import logging
import requests
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from urllib.parse import urlparse, urljoin
import time
import json

from stillme_core.learning.connectors.rss_registry import get_rss_registry, validate_source_url

log = logging.getLogger(__name__)

@dataclass
class ContentItem:
    """Represents a fetched content item."""
    title: str
    url: str
    content: str
    summary: str
    author: Optional[str] = None
    published_date: Optional[str] = None
    source: str = ""
    domain: str = ""
    content_type: str = "unknown"
    tags: List[str] = None
    license: Optional[str] = None
    word_count: int = 0
    
    def __post_init__(self):
        if self.tags is None:
            self.tags = []
        if self.word_count == 0:
            self.word_count = len(self.content.split())

class RSSFetcher:
    """Fetches content from RSS feeds and APIs."""
    
    def __init__(self, timeout: int = 30, max_retries: int = 3):
        self.timeout = timeout
        self.max_retries = max_retries
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'StillMe-AI-Learning/1.0 (Educational Research)',
            'Accept': 'application/rss+xml, application/atom+xml, application/json, text/xml',
            'Accept-Encoding': 'gzip, deflate'
        })
        self.registry = get_rss_registry()
    
    def _make_request(self, url: str) -> Optional[requests.Response]:
        """Make HTTP request with retries."""
        for attempt in range(self.max_retries):
            try:
                # Validate URL domain
                if not validate_source_url(url):
                    log.error(f"URL not in allowlist: {url}")
                    return None
                
                response = self.session.get(url, timeout=self.timeout)
                response.raise_for_status()
                return response
                
            except requests.exceptions.RequestException as e:
                log.warning(f"Request attempt {attempt + 1} failed for {url}: {e}")
                if attempt < self.max_retries - 1:
                    time.sleep(2 ** attempt)  # Exponential backoff
                else:
                    log.error(f"All retry attempts failed for {url}")
                    return None
        
        return None
    
    def _parse_arxiv_api(self, response_text: str, source_name: str) -> List[ContentItem]:
        """Parse arXiv API response."""
        items = []
        
        try:
            root = ET.fromstring(response_text)
            
            # Handle arXiv API namespace
            ns = {'atom': 'http://www.w3.org/2005/Atom'}
            
            for entry in root.findall('atom:entry', ns):
                try:
                    title_elem = entry.find('atom:title', ns)
                    title = title_elem.text.strip() if title_elem is not None else "Untitled"
                    
                    # Get arXiv ID from link
                    link_elem = entry.find('atom:id', ns)
                    url = link_elem.text if link_elem is not None else ""
                    
                    # Get summary
                    summary_elem = entry.find('atom:summary', ns)
                    summary = summary_elem.text.strip() if summary_elem is not None else ""
                    
                    # Get authors
                    authors = []
                    for author in entry.findall('atom:author', ns):
                        name_elem = author.find('atom:name', ns)
                        if name_elem is not None:
                            authors.append(name_elem.text.strip())
                    
                    # Get published date
                    published_elem = entry.find('atom:published', ns)
                    published_date = published_elem.text if published_elem is not None else None
                    
                    # Get categories/tags
                    tags = []
                    for category in entry.findall('atom:category', ns):
                        term = category.get('term')
                        if term:
                            tags.append(term)
                    
                    # Create content item
                    item = ContentItem(
                        title=title,
                        url=url,
                        content=summary,  # arXiv API provides summary as content
                        summary=summary[:500] + "..." if len(summary) > 500 else summary,
                        author=", ".join(authors) if authors else None,
                        published_date=published_date,
                        source=source_name,
                        domain="arxiv.org",
                        content_type="research",
                        tags=tags,
                        license="arXiv License",
                        word_count=len(summary.split())
                    )
                    
                    items.append(item)
                    
                except Exception as e:
                    log.warning(f"Failed to parse arXiv entry: {e}")
                    continue
        
        except Exception as e:
            log.error(f"Failed to parse arXiv API response: {e}")
        
        return items
    
    def _parse_rss_feed(self, response_text: str, source_name: str, domain: str) -> List[ContentItem]:
        """Parse RSS feed."""
        items = []
        
        try:
            root = ET.fromstring(response_text)
            
            # Handle different RSS namespaces
            ns = {
                'rss': 'http://purl.org/rss/1.0/',
                'atom': 'http://www.w3.org/2005/Atom',
                'dc': 'http://purl.org/dc/elements/1.1/',
                'content': 'http://purl.org/rss/1.0/modules/content/'
            }
            
            # Find items (RSS 2.0) or entries (Atom)
            items_elements = root.findall('.//item') or root.findall('.//atom:entry', ns)
            
            for item_elem in items_elements:
                try:
                    # Get title
                    title_elem = item_elem.find('title') or item_elem.find('atom:title', ns)
                    title = title_elem.text.strip() if title_elem is not None else "Untitled"
                    
                    # Get URL
                    link_elem = item_elem.find('link') or item_elem.find('atom:link', ns)
                    if link_elem is not None:
                        url = link_elem.text or link_elem.get('href', '')
                    else:
                        url = ""
                    
                    # Get content/description
                    content_elem = (item_elem.find('description') or 
                                  item_elem.find('content:encoded', ns) or
                                  item_elem.find('atom:content', ns) or
                                  item_elem.find('atom:summary', ns))
                    content = content_elem.text if content_elem is not None else ""
                    
                    # Clean HTML tags from content
                    import re
                    content = re.sub(r'<[^>]+>', '', content)
                    content = content.strip()
                    
                    # Get summary (truncated content)
                    summary = content[:500] + "..." if len(content) > 500 else content
                    
                    # Get author
                    author_elem = (item_elem.find('author') or 
                                 item_elem.find('dc:creator', ns) or
                                 item_elem.find('atom:author/atom:name', ns))
                    author = author_elem.text.strip() if author_elem is not None else None
                    
                    # Get published date
                    pub_date_elem = (item_elem.find('pubDate') or 
                                   item_elem.find('dc:date', ns) or
                                   item_elem.find('atom:published', ns))
                    published_date = pub_date_elem.text if pub_date_elem is not None else None
                    
                    # Get categories/tags
                    tags = []
                    for category in item_elem.findall('category') or item_elem.findall('atom:category', ns):
                        tag_text = category.text or category.get('term', '')
                        if tag_text:
                            tags.append(tag_text.strip())
                    
                    # Create content item
                    item = ContentItem(
                        title=title,
                        url=url,
                        content=content,
                        summary=summary,
                        author=author,
                        published_date=published_date,
                        source=source_name,
                        domain=domain,
                        content_type="blog",
                        tags=tags,
                        license="Unknown",  # Will be determined by license gate
                        word_count=len(content.split())
                    )
                    
                    items.append(item)
                    
                except Exception as e:
                    log.warning(f"Failed to parse RSS item: {e}")
                    continue
        
        except Exception as e:
            log.error(f"Failed to parse RSS feed: {e}")
        
        return items
    
    def fetch_source(self, source_name: str) -> List[ContentItem]:
        """Fetch content from a specific source."""
        source = self.registry.get_source(source_name)
        if not source or not source.enabled:
            log.warning(f"Source not found or disabled: {source_name}")
            return []
        
        log.info(f"Fetching from source: {source_name} ({source.url})")
        
        response = self._make_request(source.url)
        if not response:
            return []
        
        # Parse based on content type
        if "arxiv.org" in source.domain:
            items = self._parse_arxiv_api(response.text, source_name)
        else:
            items = self._parse_rss_feed(response.text, source_name, source.domain)
        
        # Limit items based on source configuration
        max_items = min(source.max_items, len(items))
        items = items[:max_items]
        
        log.info(f"Fetched {len(items)} items from {source_name}")
        return items
    
    def fetch_all_sources(self) -> List[ContentItem]:
        """Fetch content from all enabled sources."""
        all_items = []
        enabled_sources = self.registry.get_enabled_sources()
        
        log.info(f"Fetching from {len(enabled_sources)} enabled sources")
        
        for source in enabled_sources:
            try:
                items = self.fetch_source(source.name)
                all_items.extend(items)
                
                # Rate limiting - small delay between sources
                time.sleep(1)
                
            except Exception as e:
                log.error(f"Failed to fetch from source {source.name}: {e}")
                continue
        
        log.info(f"Total items fetched: {len(all_items)}")
        return all_items
    
    def fetch_by_category(self, category: str) -> List[ContentItem]:
        """Fetch content from sources in a specific category."""
        sources = self.registry.get_sources_by_category(category)
        all_items = []
        
        log.info(f"Fetching from {len(sources)} sources in category: {category}")
        
        for source in sources:
            try:
                items = self.fetch_source(source.name)
                all_items.extend(items)
                time.sleep(1)  # Rate limiting
            except Exception as e:
                log.error(f"Failed to fetch from source {source.name}: {e}")
                continue
        
        return all_items
    
    def get_fetch_statistics(self) -> Dict:
        """Get fetching statistics."""
        registry_stats = self.registry.get_statistics()
        
        return {
            "registry": registry_stats,
            "session_headers": dict(self.session.headers),
            "timeout": self.timeout,
            "max_retries": self.max_retries,
            "last_fetch": datetime.now(timezone.utc).isoformat()
        }

def fetch_content_from_sources(sources: Optional[List[str]] = None, 
                              category: Optional[str] = None) -> List[ContentItem]:
    """Convenience function to fetch content."""
    fetcher = RSSFetcher()
    
    if sources:
        all_items = []
        for source_name in sources:
            items = fetcher.fetch_source(source_name)
            all_items.extend(items)
        return all_items
    elif category:
        return fetcher.fetch_by_category(category)
    else:
        return fetcher.fetch_all_sources()
