"""
Wikipedia Fetcher for StillMe
Fetches articles from Wikipedia API
License: CC BY-SA 3.0 (content), metadata is open
"""

import requests
import time
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
import html

logger = logging.getLogger(__name__)

# Rate limiting configuration
WIKIPEDIA_RATE_LIMIT_DELAY = 0.5  # Seconds between requests (Wikipedia is lenient)
WIKIPEDIA_MAX_RETRIES = 3
WIKIPEDIA_RETRY_DELAY = 2.0

# Wikipedia API configuration
WIKIPEDIA_API_BASE = "https://en.wikipedia.org/api/rest_v1"
WIKIPEDIA_MAX_RESULTS = 10


class WikipediaFetcher:
    """Fetches articles from Wikipedia with rate limiting"""
    
    def __init__(self, language: str = "en"):
        """
        Initialize Wikipedia fetcher
        
        Args:
            language: Wikipedia language code (default: en)
        """
        self.language = language
        self.api_base = f"https://{language}.wikipedia.org/api/rest_v1"
        self.last_request_time: Optional[datetime] = None
        self.request_count = 0
        logger.info(f"Wikipedia Fetcher initialized (language: {language})")
    
    def _rate_limit(self):
        """Enforce rate limiting (0.5 seconds between requests)"""
        if self.last_request_time:
            elapsed = (datetime.now() - self.last_request_time).total_seconds()
            if elapsed < WIKIPEDIA_RATE_LIMIT_DELAY:
                sleep_time = WIKIPEDIA_RATE_LIMIT_DELAY - elapsed
                logger.debug(f"Rate limiting: sleeping {sleep_time:.2f}s")
                time.sleep(sleep_time)
        
        self.last_request_time = datetime.now()
        self.request_count += 1
    
    def _fetch_with_retry(self, url: str, params: Optional[Dict[str, Any]] = None) -> Optional[requests.Response]:
        """Fetch with exponential backoff retry"""
        headers = {
            "User-Agent": "StillMe-Learning-AI-System/1.0 (https://github.com/anhmtk/StillMe-Learning-AI-System-RAG-Foundation)",
            "Accept": "application/json"
        }
        
        for attempt in range(WIKIPEDIA_MAX_RETRIES):
            try:
                self._rate_limit()
                response = requests.get(url, params=params, headers=headers, timeout=30)
                
                # Handle 404 - don't retry
                if response.status_code == 404:
                    logger.warning(f"Wikipedia API returned 404 for {url}")
                    return response
                
                # Handle 429 (rate limit) and 5xx - retry with backoff
                if response.status_code == 429 or response.status_code >= 500:
                    if attempt < WIKIPEDIA_MAX_RETRIES - 1:
                        delay = WIKIPEDIA_RETRY_DELAY * (2 ** attempt)
                        logger.warning(f"Wikipedia API returned {response.status_code} (attempt {attempt + 1}/{WIKIPEDIA_MAX_RETRIES}). Retrying in {delay}s...")
                        time.sleep(delay)
                        continue
                    else:
                        logger.error(f"Wikipedia API request failed after {WIKIPEDIA_MAX_RETRIES} attempts: {response.status_code}")
                        return None
                
                response.raise_for_status()
                return response
            except requests.exceptions.Timeout as e:
                if attempt < WIKIPEDIA_MAX_RETRIES - 1:
                    delay = WIKIPEDIA_RETRY_DELAY * (2 ** attempt)
                    logger.warning(f"Wikipedia API timeout (attempt {attempt + 1}/{WIKIPEDIA_MAX_RETRIES}). Retrying in {delay}s...")
                    time.sleep(delay)
                else:
                    logger.error(f"Wikipedia API request timed out after {WIKIPEDIA_MAX_RETRIES} attempts: {e}")
                    return None
            except requests.exceptions.RequestException as e:
                if attempt < WIKIPEDIA_MAX_RETRIES - 1:
                    delay = WIKIPEDIA_RETRY_DELAY * (2 ** attempt)
                    logger.warning(f"Wikipedia API request failed (attempt {attempt + 1}/{WIKIPEDIA_MAX_RETRIES}): {e}. Retrying in {delay}s...")
                    time.sleep(delay)
                else:
                    logger.error(f"Wikipedia API request failed after {WIKIPEDIA_MAX_RETRIES} attempts: {e}")
                    return None
        return None
    
    def _strip_html(self, text: str) -> str:
        """Strip HTML tags from text"""
        import re
        # Remove HTML tags
        text = re.sub(r'<[^>]+>', '', text)
        # Decode HTML entities
        text = html.unescape(text)
        return text.strip()
    
    def fetch_article(self, title: str) -> Optional[Dict[str, Any]]:
        """
        Fetch a single Wikipedia article by title
        
        Args:
            title: Article title (URL-encoded)
            
        Returns:
            Article entry with content
        """
        try:
            # Fetch page content
            url = f"{self.api_base}/page/summary/{title}"
            response = self._fetch_with_retry(url)
            
            if not response:
                return None
            
            data = response.json()
            
            # Extract metadata
            article_title = data.get("title", title)
            extract = data.get("extract", "")
            content_url = data.get("content_urls", {}).get("desktop", {}).get("page", "")
            
            # Fetch full page content if available
            # TODO: Use page_id to fetch full content if needed
            # if "pageid" in data:
            #     page_id = data["pageid"]
            #     # Try to get full content (may require different endpoint)
            
            # Clean HTML from extract
            extract = self._strip_html(extract)
            
            article_entry = {
                "title": article_title,
                "summary": extract[:500] if len(extract) > 500 else extract,
                "content": extract,
                "link": content_url,
                "published": datetime.now().isoformat(),  # Wikipedia doesn't have publish date
                "source": "wikipedia",
                "source_url": content_url,
                "content_type": "knowledge",
                "metadata": {
                    "page_id": data.get("pageid"),
                    "license": "CC BY-SA 3.0",
                    "source_type": "wikipedia",
                    "language": self.language
                }
            }
            
            logger.info(f"Fetched Wikipedia article: {article_title}")
            return article_entry
            
        except Exception as e:
            logger.error(f"Error fetching Wikipedia article '{title}': {e}")
            return None
    
    def search_articles(self,
                       query: str,
                       max_results: int = WIKIPEDIA_MAX_RESULTS) -> List[Dict[str, Any]]:
        """
        Search Wikipedia articles by query
        
        Args:
            query: Search query
            max_results: Maximum number of articles
            
        Returns:
            List of article entries
        """
        articles = []
        
        try:
            # Use REST v1 search API (fixed endpoint)
            # https://en.wikipedia.org/w/rest.php/v1/search/page?q=<q>&limit=<n>
            search_url = f"https://{self.language}.wikipedia.org/w/rest.php/v1/search/page"
            params = {
                "q": query,
                "limit": min(max_results, WIKIPEDIA_MAX_RESULTS)
            }
            
            response = self._fetch_with_retry(search_url, params)
            if not response:
                return articles
            
            # Handle 404 - don't retry
            if response.status_code == 404:
                logger.warning(f"Wikipedia search returned 404 for query: {query}")
                return articles
            
            data = response.json()
            
            # Extract search results from REST v1 format
            pages = data.get("pages", [])
            
            for page in pages[:max_results]:
                # REST v1 returns title directly
                title = page.get("title", "")
                if title:
                    article = self.fetch_article(title)
                    if article:
                        articles.append(article)
            
            logger.info(f"Found {len(articles)} Wikipedia articles for query: {query}")
            
        except Exception as e:
            logger.error(f"Error searching Wikipedia: {e}")
        
        return articles
    
    def fetch_by_category(self,
                         category: str,
                         max_results: int = WIKIPEDIA_MAX_RESULTS) -> List[Dict[str, Any]]:
        """
        Fetch articles by category
        
        Args:
            category: Category name (e.g., "Artificial_intelligence")
            max_results: Maximum number of articles
            
        Returns:
            List of article entries
        """
        # Wikipedia doesn't have direct category API in REST v1
        # Use search with category prefix
        query = f"Category:{category}"
        return self.search_articles(query, max_results=max_results)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get fetcher statistics"""
        return {
            "source": "wikipedia",
            "language": self.language,
            "request_count": self.request_count,
            "last_request_time": self.last_request_time.isoformat() if self.last_request_time else None,
            "rate_limit_delay": WIKIPEDIA_RATE_LIMIT_DELAY
        }

