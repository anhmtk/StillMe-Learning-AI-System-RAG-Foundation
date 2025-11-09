"""
arXiv Fetcher for StillMe
Fetches research papers from arXiv API with rate limiting and pre-filtering
License: CC BY-NC-SA (varies by paper, metadata is open)
"""

import requests
import time
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from xml.etree import ElementTree as ET

logger = logging.getLogger(__name__)

# Rate limiting configuration
ARXIV_RATE_LIMIT_DELAY = 3.0  # Seconds between requests (arXiv recommends 3s)
ARXIV_MAX_RETRIES = 3
ARXIV_RETRY_DELAY = 5.0  # Seconds to wait before retry

# arXiv API configuration
ARXIV_API_BASE = "http://export.arxiv.org/api/query"
ARXIV_MAX_RESULTS = 10  # Maximum papers per query


class ArxivFetcher:
    """Fetches research papers from arXiv with rate limiting and pre-filtering"""
    
    def __init__(self):
        """Initialize arXiv fetcher"""
        self.last_request_time: Optional[datetime] = None
        self.request_count = 0
        logger.info("arXiv Fetcher initialized")
    
    def _rate_limit(self):
        """Enforce rate limiting (3 seconds between requests)"""
        if self.last_request_time:
            elapsed = (datetime.now() - self.last_request_time).total_seconds()
            if elapsed < ARXIV_RATE_LIMIT_DELAY:
                sleep_time = ARXIV_RATE_LIMIT_DELAY - elapsed
                logger.debug(f"Rate limiting: sleeping {sleep_time:.2f}s")
                time.sleep(sleep_time)
        
        self.last_request_time = datetime.now()
        self.request_count += 1
    
    def _fetch_with_retry(self, url: str, params: Dict[str, Any]) -> Optional[requests.Response]:
        """Fetch with exponential backoff retry"""
        for attempt in range(ARXIV_MAX_RETRIES):
            try:
                self._rate_limit()
                response = requests.get(url, params=params, timeout=30)
                response.raise_for_status()
                return response
            except requests.exceptions.RequestException as e:
                if attempt < ARXIV_MAX_RETRIES - 1:
                    delay = ARXIV_RETRY_DELAY * (2 ** attempt)
                    logger.warning(f"arXiv API request failed (attempt {attempt + 1}/{ARXIV_MAX_RETRIES}): {e}. Retrying in {delay}s...")
                    time.sleep(delay)
                else:
                    logger.error(f"arXiv API request failed after {ARXIV_MAX_RETRIES} attempts: {e}")
                    return None
        return None
    
    def fetch_recent_papers(self, 
                           search_query: str = "cat:cs.AI OR cat:cs.LG OR cat:cs.CL",
                           max_results: int = ARXIV_MAX_RESULTS,
                           sort_by: str = "submittedDate",
                           sort_order: str = "descending") -> List[Dict[str, Any]]:
        """
        Fetch recent papers from arXiv
        
        Args:
            search_query: arXiv search query (default: AI/ML/NLP categories)
            max_results: Maximum number of papers to fetch
            sort_by: Sort field (submittedDate, lastUpdatedDate, relevance)
            sort_order: Sort order (ascending, descending)
            
        Returns:
            List of paper entries with metadata
        """
        papers = []
        
        try:
            params = {
                "search_query": search_query,
                "start": 0,
                "max_results": min(max_results, ARXIV_MAX_RESULTS),
                "sortBy": sort_by,
                "sortOrder": sort_order
            }
            
            response = self._fetch_with_retry(ARXIV_API_BASE, params)
            if not response:
                return papers
            
            # Parse Atom XML response
            root = ET.fromstring(response.content)
            
            # Namespace for Atom feed
            ns = {'atom': 'http://www.w3.org/2005/Atom'}
            
            entries = root.findall('atom:entry', ns)
            
            for entry in entries:
                try:
                    # Extract metadata
                    title = entry.find('atom:title', ns)
                    title_text = title.text.strip() if title is not None and title.text else ""
                    
                    summary = entry.find('atom:summary', ns)
                    summary_text = summary.text.strip() if summary is not None and summary.text else ""
                    
                    # Get paper ID and link
                    id_elem = entry.find('atom:id', ns)
                    paper_id = id_elem.text.split('/')[-1] if id_elem is not None and id_elem.text else ""
                    paper_url = f"https://arxiv.org/abs/{paper_id}"
                    
                    # Get authors
                    authors = []
                    for author in entry.findall('atom:author', ns):
                        name_elem = author.find('atom:name', ns)
                        if name_elem is not None and name_elem.text:
                            authors.append(name_elem.text.strip())
                    
                    # Get published date
                    published = entry.find('atom:published', ns)
                    published_date = published.text if published is not None and published.text else datetime.now().isoformat()
                    
                    # Get categories
                    categories = []
                    for category in entry.findall('atom:category', ns):
                        term = category.get('term', '')
                        if term:
                            categories.append(term)
                    
                    # Combine title and summary for content
                    content = f"{title_text}\n\n{summary_text}"
                    
                    paper_entry = {
                        "title": title_text,
                        "summary": summary_text,
                        "content": content,
                        "link": paper_url,
                        "published": published_date,
                        "source": "arxiv",
                        "source_url": paper_url,
                        "content_type": "knowledge",
                        "metadata": {
                            "paper_id": paper_id,
                            "authors": authors,
                            "categories": categories,
                            "license": "CC BY-NC-SA (varies by paper, check individual paper)",
                            "source_type": "arxiv"
                        }
                    }
                    
                    papers.append(paper_entry)
                    
                except Exception as e:
                    logger.warning(f"Error parsing arXiv entry: {e}")
                    continue
            
            logger.info(f"Fetched {len(papers)} papers from arXiv")
            
        except Exception as e:
            logger.error(f"Error fetching from arXiv: {e}")
        
        return papers
    
    def fetch_by_category(self, 
                         category: str = "cs.AI",
                         max_results: int = ARXIV_MAX_RESULTS) -> List[Dict[str, Any]]:
        """
        Fetch papers by arXiv category
        
        Args:
            category: arXiv category (e.g., cs.AI, cs.LG, cs.CL)
            max_results: Maximum number of papers
            
        Returns:
            List of paper entries
        """
        search_query = f"cat:{category}"
        return self.fetch_recent_papers(search_query=search_query, max_results=max_results)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get fetcher statistics"""
        return {
            "source": "arxiv",
            "request_count": self.request_count,
            "last_request_time": self.last_request_time.isoformat() if self.last_request_time else None,
            "rate_limit_delay": ARXIV_RATE_LIMIT_DELAY
        }

