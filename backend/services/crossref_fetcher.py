"""
CrossRef Fetcher for StillMe
Fetches academic paper metadata from CrossRef API
License: Metadata is open (CC0), content license varies by publisher
"""

import requests
import time
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

# Rate limiting configuration
CROSSREF_RATE_LIMIT_DELAY = 1.0  # Seconds between requests (CrossRef is more lenient)
CROSSREF_MAX_RETRIES = 3
CROSSREF_RETRY_DELAY = 2.0

# CrossRef API configuration
CROSSREF_API_BASE = "https://api.crossref.org/works"
CROSSREF_MAX_RESULTS = 20
CROSSREF_USER_AGENT = "StillMe-Learning-AI-System/1.0 (https://github.com/anhmtk/StillMe-Learning-AI-System-RAG-Foundation; mailto:contact@example.com)"  # Update with real contact


class CrossrefFetcher:
    """Fetches academic paper metadata from CrossRef with rate limiting"""
    
    def __init__(self):
        """Initialize CrossRef fetcher"""
        self.last_request_time: Optional[datetime] = None
        self.request_count = 0
        logger.info("CrossRef Fetcher initialized")
    
    def _rate_limit(self):
        """Enforce rate limiting (1 second between requests)"""
        if self.last_request_time:
            elapsed = (datetime.now() - self.last_request_time).total_seconds()
            if elapsed < CROSSREF_RATE_LIMIT_DELAY:
                sleep_time = CROSSREF_RATE_LIMIT_DELAY - elapsed
                logger.debug(f"Rate limiting: sleeping {sleep_time:.2f}s")
                time.sleep(sleep_time)
        
        self.last_request_time = datetime.now()
        self.request_count += 1
    
    def _fetch_with_retry(self, url: str, params: Dict[str, Any]) -> Optional[requests.Response]:
        """Fetch with exponential backoff retry"""
        headers = {
            "User-Agent": CROSSREF_USER_AGENT,
            "Accept": "application/json"
        }
        
        for attempt in range(CROSSREF_MAX_RETRIES):
            try:
                self._rate_limit()
                response = requests.get(url, params=params, headers=headers, timeout=30)
                response.raise_for_status()
                return response
            except requests.exceptions.RequestException as e:
                if attempt < CROSSREF_MAX_RETRIES - 1:
                    delay = CROSSREF_RETRY_DELAY * (2 ** attempt)
                    logger.warning(f"CrossRef API request failed (attempt {attempt + 1}/{CROSSREF_MAX_RETRIES}): {e}. Retrying in {delay}s...")
                    time.sleep(delay)
                else:
                    logger.error(f"CrossRef API request failed after {CROSSREF_MAX_RETRIES} attempts: {e}")
                    return None
        return None
    
    def fetch_recent_works(self,
                          query: Optional[str] = None,
                          filter_query: Optional[str] = None,
                          max_results: int = CROSSREF_MAX_RESULTS,
                          sort: str = "relevance") -> List[Dict[str, Any]]:
        """
        Fetch recent works from CrossRef
        
        Args:
            query: Search query (optional)
            filter_query: Filter query (e.g., "from-pub-date:2024-01-01")
            max_results: Maximum number of works to fetch
            sort: Sort order (relevance, published, updated)
            
        Returns:
            List of work entries with metadata
        """
        works = []
        
        try:
            params = {
                "rows": min(max_results, CROSSREF_MAX_RESULTS),
                "sort": sort
            }
            
            if query:
                params["query"] = query
            if filter_query:
                params["filter"] = filter_query
            
            response = self._fetch_with_retry(CROSSREF_API_BASE, params)
            if not response:
                return works
            
            data = response.json()
            
            if "message" not in data or "items" not in data["message"]:
                logger.warning("Unexpected CrossRef API response format")
                return works
            
            items = data["message"]["items"]
            
            for item in items:
                try:
                    # Extract metadata
                    title = item.get("title", [""])[0] if item.get("title") else ""
                    
                    # Get abstract (may be in different formats)
                    abstract = ""
                    if "abstract" in item:
                        abstract = item["abstract"]
                    elif "abstract-html" in item:
                        abstract = item["abstract-html"]
                    
                    # Get DOI and URL
                    doi = item.get("DOI", "")
                    url = f"https://doi.org/{doi}" if doi else ""
                    
                    # Get authors
                    authors = []
                    if "author" in item:
                        for author in item["author"]:
                            given = author.get("given", "")
                            family = author.get("family", "")
                            author_name = f"{given} {family}".strip()
                            if author_name:
                                authors.append(author_name)
                    
                    # Get published date
                    published_date = datetime.now().isoformat()
                    if "published-print" in item and "date-parts" in item["published-print"]:
                        date_parts = item["published-print"]["date-parts"][0]
                        if len(date_parts) >= 3:
                            published_date = f"{date_parts[0]}-{date_parts[1]:02d}-{date_parts[2]:02d}"
                    
                    # Get journal/publisher
                    container_title = item.get("container-title", [""])[0] if item.get("container-title") else ""
                    publisher = item.get("publisher", "")
                    
                    # Combine title and abstract for content
                    content = f"{title}\n\n{abstract}" if abstract else title
                    
                    work_entry = {
                        "title": title,
                        "summary": abstract[:500] if abstract else "",  # Truncate for summary
                        "content": content,
                        "link": url,
                        "published": published_date,
                        "source": "crossref",
                        "source_url": url,
                        "content_type": "knowledge",
                        "metadata": {
                            "doi": doi,
                            "authors": authors,
                            "journal": container_title,
                            "publisher": publisher,
                            "license": "Metadata: CC0 (open), Content: varies by publisher",
                            "source_type": "crossref"
                        }
                    }
                    
                    works.append(work_entry)
                    
                except Exception as e:
                    logger.warning(f"Error parsing CrossRef item: {e}")
                    continue
            
            logger.info(f"Fetched {len(works)} works from CrossRef")
            
        except Exception as e:
            logger.error(f"Error fetching from CrossRef: {e}")
        
        return works
    
    def fetch_by_keywords(self,
                         keywords: List[str],
                         max_results: int = CROSSREF_MAX_RESULTS) -> List[Dict[str, Any]]:
        """
        Fetch works by keywords
        
        Args:
            keywords: List of keywords to search
            max_results: Maximum number of works
            
        Returns:
            List of work entries
        """
        query = " ".join(keywords)
        return self.fetch_recent_works(query=query, max_results=max_results)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get fetcher statistics"""
        return {
            "source": "crossref",
            "request_count": self.request_count,
            "last_request_time": self.last_request_time.isoformat() if self.last_request_time else None,
            "rate_limit_delay": CROSSREF_RATE_LIMIT_DELAY
        }

