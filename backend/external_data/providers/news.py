"""
News Data Provider - GNews API

GNews provides free tier with 100 requests/day.
"""

import httpx
import logging
import os
from datetime import datetime
from typing import Dict, Any, Optional
from .base import ExternalDataProvider, ExternalDataResult

logger = logging.getLogger(__name__)


class NewsProvider(ExternalDataProvider):
    """News provider using GNews API"""
    
    BASE_URL = "https://gnews.io/api/v4/search"
    
    def __init__(self, api_key: Optional[str] = None, timeout: int = 10):
        """
        Initialize GNews provider
        
        Args:
            api_key: GNews API key (from GNEWS_API_KEY env var if not provided)
            timeout: Request timeout
        """
        # Get API key from env if not provided
        if not api_key:
            api_key = os.getenv("GNEWS_API_KEY")
        
        super().__init__(api_key=api_key, timeout=timeout)
    
    def get_provider_name(self) -> str:
        return "GNews"
    
    def supports(self, intent_type: str, params: Dict[str, Any]) -> bool:
        """Check if this provider supports news intent"""
        return intent_type == "news"
    
    async def fetch(self, intent_type: str, params: Dict[str, Any]) -> ExternalDataResult:
        """
        Fetch news from GNews API
        
        Args:
            intent_type: Should be "news"
            params: Should contain "query" (search query) and optionally "max_results" (default: 5)
            
        Returns:
            ExternalDataResult with news data
        """
        if intent_type != "news":
            return ExternalDataResult(
                data={},
                source=self.get_provider_name(),
                timestamp=datetime.utcnow(),
                cached=False,
                success=False,
                error_message=f"Invalid intent type: {intent_type}"
            )
        
        if not self.api_key:
            return ExternalDataResult(
                data={},
                source=self.get_provider_name(),
                timestamp=datetime.utcnow(),
                cached=False,
                success=False,
                error_message="GNews API key not configured (set GNEWS_API_KEY env var)"
            )
        
        query = params.get("query", "")
        max_results = params.get("max_results", 5)
        
        if not query:
            return ExternalDataResult(
                data={},
                source=self.get_provider_name(),
                timestamp=datetime.utcnow(),
                cached=False,
                success=False,
                error_message="Query parameter is required"
            )
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    self.BASE_URL,
                    params={
                        "q": query,
                        "apikey": self.api_key,
                        "max": max_results,
                        "lang": "en",  # Can be made configurable later
                        "sortby": "publishedAt"
                    }
                )
                
                response.raise_for_status()
                raw_data = response.json()
                
                # Parse and structure data
                articles = raw_data.get("articles", [])
                news_data = {
                    "query": query,
                    "total_results": raw_data.get("totalArticles", len(articles)),
                    "articles": [
                        {
                            "title": article.get("title", ""),
                            "description": article.get("description", ""),
                            "url": article.get("url", ""),
                            "source": article.get("source", {}).get("name", "Unknown"),
                            "published_at": article.get("publishedAt", ""),
                        }
                        for article in articles[:max_results]
                    ]
                }
                
                return ExternalDataResult(
                    data=news_data,
                    source=self.get_provider_name(),
                    timestamp=datetime.utcnow(),
                    cached=False,
                    raw_response=response.text,
                    success=True
                )
                
        except httpx.TimeoutException:
            return ExternalDataResult(
                data={},
                source=self.get_provider_name(),
                timestamp=datetime.utcnow(),
                cached=False,
                success=False,
                error_message="Request timeout"
            )
        except httpx.HTTPStatusError as e:
            error_msg = f"HTTP error: {e.response.status_code}"
            try:
                error_data = e.response.json()
                error_msg = error_data.get("message", error_msg)
            except:
                pass
            
            return ExternalDataResult(
                data={},
                source=self.get_provider_name(),
                timestamp=datetime.utcnow(),
                cached=False,
                success=False,
                error_message=error_msg
            )
        except Exception as e:
            logger.error(f"News API error: {e}", exc_info=True)
            return ExternalDataResult(
                data={},
                source=self.get_provider_name(),
                timestamp=datetime.utcnow(),
                cached=False,
                success=False,
                error_message=f"Error: {str(e)}"
            )

