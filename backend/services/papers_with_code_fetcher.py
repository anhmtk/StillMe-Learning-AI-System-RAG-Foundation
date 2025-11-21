"""
Papers with Code Fetcher for StillMe
Fetches recent papers with code from paperswithcode.com
"""

import httpx
import feedparser  # type: ignore[import-untyped]
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class PapersWithCodeFetcher:
    """Fetcher for Papers with Code"""
    
    def __init__(self):
        self.base_url = "https://paperswithcode.com"
        self.api_url = "https://paperswithcode.com/api/v1/papers/"
        self.last_error: Optional[str] = None
        self.error_count = 0
        self.last_success_time: Optional[datetime] = None
        self.successful_fetches = 0
        self.failed_fetches = 0
    
    async def fetch_recent_papers_async(self, max_results: int = 5) -> List[Dict[str, Any]]:
        """
        Async fetch recent papers with code
        
        Args:
            max_results: Maximum number of papers to fetch
            
        Returns:
            List of paper entries
        """
        entries = []
        
        try:
            async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
                # Try to fetch from API
                response = await client.get(
                    f"{self.api_url}",
                    params={"ordering": "-added", "page_size": max_results}
                )
                
                if response.status_code == 200:
                    data = response.json()
                    if "results" in data:
                        for paper in data["results"][:max_results]:
                            entry = {
                                "title": paper.get("title", ""),
                                "summary": paper.get("abstract", ""),
                                "link": f"{self.base_url}/paper/{paper.get('id', '')}",
                                "published": paper.get("published", datetime.now().isoformat()),
                                "source": "papers_with_code",
                                "content_type": "knowledge",
                                "metadata": {
                                    "paper_id": paper.get("id"),
                                    "authors": paper.get("authors", []),
                                    "categories": paper.get("categories", []),
                                    "has_code": paper.get("repository", {}).get("url") is not None if isinstance(paper.get("repository"), dict) else False
                                }
                            }
                            entries.append(entry)
                        self.successful_fetches += 1
                        self.last_success_time = datetime.now()
                        logger.info(f"Fetched {len(entries)} papers from Papers with Code API")
                        return entries
                
                # Fallback: Try RSS feed if API fails
                rss_url = f"{self.base_url}/latest"
                try:
                    rss_response = await client.get(rss_url, follow_redirects=True)
                    if rss_response.status_code == 200:
                        feed = feedparser.parse(rss_response.text)
                        for entry_data in feed.entries[:max_results]:
                            entry = {
                                "title": entry_data.get("title", ""),
                                "summary": entry_data.get("summary", ""),
                                "link": entry_data.get("link", ""),
                                "published": entry_data.get("published", datetime.now().isoformat()),
                                "source": "papers_with_code",
                                "content_type": "knowledge"
                            }
                            entries.append(entry)
                        if entries:
                            self.successful_fetches += 1
                            self.last_success_time = datetime.now()
                            logger.info(f"Fetched {len(entries)} papers from Papers with Code RSS")
                            return entries
                except Exception as rss_error:
                    logger.warning(f"RSS fallback failed: {rss_error}")
                
                raise Exception(f"API returned status {response.status_code}")
                
        except Exception as e:
            error_msg = f"Failed to fetch Papers with Code: {e}"
            self.last_error = error_msg
            self.error_count += 1
            self.failed_fetches += 1
            logger.error(error_msg)
            raise
        
        return entries
    
    def fetch_recent_papers(self, max_results: int = 5) -> List[Dict[str, Any]]:
        """
        Fetch recent papers with code (synchronous wrapper)
        
        Args:
            max_results: Maximum number of papers to fetch
            
        Returns:
            List of paper entries
        """
        try:
            import asyncio
            import concurrent.futures
            
            # Check if we're in an async context
            try:
                loop = asyncio.get_running_loop()
                # Event loop is already running - use thread executor
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(self._run_async_in_thread, max_results)
                    return future.result(timeout=60.0)
            except RuntimeError:
                # No event loop running - safe to use asyncio.run
                return asyncio.run(self.fetch_recent_papers_async(max_results))
        except Exception as e:
            logger.error(f"Error in fetch_recent_papers: {e}")
            return []
    
    def _run_async_in_thread(self, max_results: int) -> List[Dict[str, Any]]:
        """Run async function in a new thread with its own event loop"""
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(self.fetch_recent_papers_async(max_results))
        finally:
            loop.close()
    
    def get_stats(self) -> Dict[str, Any]:
        """Get fetcher statistics"""
        return {
            "source": "papers_with_code",
            "successful_fetches": self.successful_fetches,
            "failed_fetches": self.failed_fetches,
            "error_count": self.error_count,
            "last_error": self.last_error,
            "last_success_time": self.last_success_time.isoformat() if self.last_success_time else None,
            "status": "error" if self.last_error and (not self.last_success_time or self.failed_fetches > 0) else "ok"
        }

