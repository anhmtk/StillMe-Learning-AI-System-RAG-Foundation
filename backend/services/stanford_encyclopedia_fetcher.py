"""
Stanford Encyclopedia of Philosophy Fetcher for StillMe
Fetches articles from Stanford Encyclopedia of Philosophy
Note: SEP doesn't have RSS feed, so we use web scraping
"""

import httpx
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging
import re
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


class StanfordEncyclopediaFetcher:
    """Fetcher for Stanford Encyclopedia of Philosophy"""
    
    def __init__(self):
        self.base_url = "https://plato.stanford.edu"
        self.entries_url = "https://plato.stanford.edu/entries/"
        self.last_error: Optional[str] = None
        self.error_count = 0
        self.last_success_time: Optional[datetime] = None
        self.successful_fetches = 0
        self.failed_fetches = 0
    
    async def fetch_recent_entries_async(self, max_results: int = 5, topics: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """
        Fetch recent entries from Stanford Encyclopedia
        
        Args:
            max_results: Maximum number of entries to fetch
            topics: Optional list of topics to focus on (e.g., ["ethics", "ai", "consciousness"])
            
        Returns:
            List of entry data
        """
        entries = []
        
        # Default topics relevant to StillMe
        if topics is None:
            topics = ["artificial-intelligence", "ethics", "consciousness", "knowledge", "truth"]
        
        try:
            async def fetch_async():
                async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
                    # Fetch entry list page
                    response = await client.get(self.entries_url)
                    
                    if response.status_code == 200:
                        soup = BeautifulSoup(response.text, 'html.parser')
                        
                        # Find all entry links
                        entry_links = []
                        for link in soup.find_all('a', href=True):
                            href = link.get('href', '')
                            # Match SEP entry URLs: /entries/topic-name/
                            if '/entries/' in href and href.count('/') >= 3:
                                entry_name = href.split('/entries/')[-1].rstrip('/')
                                if entry_name and entry_name not in ['', 'index.html']:
                                    entry_links.append({
                                        "name": entry_name,
                                        "url": f"{self.base_url}{href}" if not href.startswith('http') else href,
                                        "title": link.get_text(strip=True)
                                    })
                        
                        # Filter by topics if provided
                        if topics:
                            filtered_links = [
                                link for link in entry_links
                                if any(topic.lower() in link["name"].lower() or topic.lower() in link["title"].lower() 
                                       for topic in topics)
                            ]
                            entry_links = filtered_links[:max_results] if filtered_links else entry_links[:max_results]
                        else:
                            entry_links = entry_links[:max_results]
                        
                        # Fetch content for each entry
                        for entry_link in entry_links:
                            try:
                                entry_response = await client.get(entry_link["url"])
                                if entry_response.status_code == 200:
                                    entry_soup = BeautifulSoup(entry_response.text, 'html.parser')
                                    
                                    # Extract main content
                                    main_content = entry_soup.find('div', {'id': 'main-text'}) or entry_soup.find('div', class_='entry-content')
                                    if not main_content:
                                        main_content = entry_soup.find('article') or entry_soup.find('main')
                                    
                                    if main_content:
                                        # Get text content (first 2000 chars for summary)
                                        text_content = main_content.get_text(separator=' ', strip=True)
                                        summary = text_content[:2000] + "..." if len(text_content) > 2000 else text_content
                                        
                                        entry = {
                                            "title": entry_link["title"] or entry_link["name"].replace('-', ' ').title(),
                                            "summary": summary,
                                            "link": entry_link["url"],
                                            "published": datetime.now().isoformat(),  # SEP doesn't provide publish dates
                                            "source": "stanford_encyclopedia",
                                            "content_type": "knowledge",
                                            "metadata": {
                                                "entry_name": entry_link["name"],
                                                "topic": entry_link["name"]
                                            }
                                        }
                                        entries.append(entry)
                                        
                            except Exception as e:
                                logger.warning(f"Failed to fetch entry {entry_link['url']}: {e}")
                                continue
                        
                        return entries
                    else:
                        raise Exception(f"HTTP {response.status_code}")
            
            if entries:
                self.successful_fetches += 1
                self.last_success_time = datetime.now()
                logger.info(f"Fetched {len(entries)} entries from Stanford Encyclopedia")
            
            return entries
                
        except Exception as e:
            error_msg = f"Failed to fetch Stanford Encyclopedia: {e}"
            self.last_error = error_msg
            self.error_count += 1
            self.failed_fetches += 1
            logger.error(error_msg)
            return []
    
    def fetch_recent_entries(self, max_results: int = 5, topics: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """
        Fetch recent entries (synchronous wrapper)
        
        Args:
            max_results: Maximum number of entries to fetch
            topics: Optional list of topics to focus on
            
        Returns:
            List of entry data
        """
        try:
            import asyncio
            try:
                return asyncio.run(self.fetch_recent_entries_async(max_results, topics))
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                result = loop.run_until_complete(self.fetch_recent_entries_async(max_results, topics))
                loop.close()
                return result
        except Exception as e:
            logger.error(f"Error in fetch_recent_entries: {e}")
            return []
    
    def get_stats(self) -> Dict[str, Any]:
        """Get fetcher statistics"""
        return {
            "source": "stanford_encyclopedia",
            "successful_fetches": self.successful_fetches,
            "failed_fetches": self.failed_fetches,
            "error_count": self.error_count,
            "last_error": self.last_error,
            "last_success_time": self.last_success_time.isoformat() if self.last_success_time else None,
            "status": "error" if self.last_error and (not self.last_success_time or self.failed_fetches > 0) else "ok"
        }

