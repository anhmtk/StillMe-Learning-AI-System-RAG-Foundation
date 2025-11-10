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
        # Use correct REST v1 endpoint base URL
        self.api_base = f"https://{language}.wikipedia.org/w/rest.php/v1"
        self.last_request_time: Optional[datetime] = None
        self.request_count = 0
        # Track error states for self-diagnosis
        self.last_error: Optional[str] = None
        self.error_count = 0
        self.last_success_time: Optional[datetime] = None
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
            # Fetch page content using correct REST v1 endpoint
            # URL format: https://{language}.wikipedia.org/w/rest.php/v1/page/summary/{title}
            # Wikipedia page titles use underscores, not spaces
            # Title from search results may already have underscores, or may have spaces
            from urllib.parse import quote
            
            # Normalize title: replace spaces with underscores (Wikipedia format)
            # But preserve existing underscores
            normalized_title = title.replace(" ", "_")
            # URL encode special characters, but keep underscores and alphanumeric
            # safe="_" means underscores won't be encoded
            encoded_title = quote(normalized_title, safe="_")
            url = f"{self.api_base}/page/summary/{encoded_title}"
            response = self._fetch_with_retry(url)
            
            # Track success
            if response and response.status_code == 200:
                self.last_success_time = datetime.now()
                self.last_error = None
            
            if not response:
                self.last_error = "No response from Wikipedia API"
                self.error_count += 1
                return None
            
            # Track 404 errors
            if response.status_code == 404:
                self.last_error = f"404 Not Found: Article '{title}' not found"
                self.error_count += 1
                logger.warning(f"Wikipedia article not found: {title}")
                return None
            
            # Track other errors
            if response.status_code != 200:
                self.last_error = f"HTTP {response.status_code}: {response.reason}"
                self.error_count += 1
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
            error_msg = f"Error fetching Wikipedia article '{title}': {e}"
            self.last_error = error_msg
            self.error_count += 1
            logger.error(error_msg)
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
            # Try REST API v1 search endpoint first
            # Documentation: https://www.mediawiki.org/wiki/API:REST_API
            # Endpoint: /w/rest.php/v1/search/page
            search_url = f"https://{self.language}.wikipedia.org/w/rest.php/v1/search/page"
            params = {
                "q": query,
                "limit": min(max_results, WIKIPEDIA_MAX_RESULTS)
            }
            
            response = self._fetch_with_retry(search_url, params)
            
            # Handle 404 or other errors - try alternative endpoint
            if not response or response.status_code == 404:
                logger.warning(
                    f"Wikipedia REST v1 search returned {response.status_code if response else 'None'} "
                    f"for query: {query}. Trying alternative search method..."
                )
                
                # Fallback: Use MediaWiki Action API search
                # Documentation: https://www.mediawiki.org/wiki/API:Search
                fallback_url = f"https://{self.language}.wikipedia.org/w/api.php"
                fallback_params = {
                    "action": "query",
                    "list": "search",
                    "srsearch": query,
                    "srlimit": min(max_results, WIKIPEDIA_MAX_RESULTS),
                    "format": "json",
                    "formatversion": "2"
                }
                
                fallback_response = self._fetch_with_retry(fallback_url, fallback_params)
                if fallback_response and fallback_response.status_code == 200:
                    fallback_data = fallback_response.json()
                    search_results = fallback_data.get("query", {}).get("search", [])
                    
                    # Convert MediaWiki format to our format
                    for result in search_results[:max_results]:
                        title = result.get("title", "")
                        if title:
                            article = self.fetch_article(title)
                            if article:
                                articles.append(article)
                    
                    logger.info(f"Found {len(articles)} Wikipedia articles using fallback API for query: {query}")
                    return articles
                else:
                    logger.error(f"Wikipedia fallback search also failed for query: {query}")
                    return articles
            
            # Parse REST v1 response
            if response.status_code != 200:
                error_msg = f"Wikipedia search returned {response.status_code} for query: {query}"
                self.last_error = error_msg
                self.error_count += 1
                logger.error(error_msg)
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
            
            # Track success if we found articles
            if articles:
                self.last_success_time = datetime.now()
                self.last_error = None
            
        except Exception as e:
            error_msg = f"Error searching Wikipedia: {e}"
            self.last_error = error_msg
            self.error_count += 1
            logger.error(error_msg)
        
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
            "rate_limit_delay": WIKIPEDIA_RATE_LIMIT_DELAY,
            "error_count": self.error_count,
            "last_error": self.last_error,
            "last_success_time": self.last_success_time.isoformat() if self.last_success_time else None,
            "status": "error" if self.last_error and (not self.last_success_time or self.error_count > 0) else "ok"
        }

