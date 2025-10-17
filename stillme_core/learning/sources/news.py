"""
News Learning Source
===================

Fetches learning content from news APIs.
"""

import asyncio
import logging
from datetime import datetime
from typing import Any, Dict, List

import aiohttp

from .base import BaseLearningSource, LearningContent

logger = logging.getLogger(__name__)


class NewsSource(BaseLearningSource):
    """News learning source"""
    
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__("news", config)
        self.api_key = self.config.get("news_api_key")
        self.categories = self.config.get("categories", ["technology", "science", "business"])
    
    async def fetch_content(self, limit: int = 10) -> List[LearningContent]:
        """Fetch latest news articles"""
        try:
            contents = []
            
            if not self.api_key:
                self.logger.warning("No news API key provided")
                return contents
            
            async with aiohttp.ClientSession() as session:
                for category in self.categories:
                    try:
                        url = "https://newsapi.org/v2/top-headlines"
                        params = {
                            "category": category,
                            "apiKey": self.api_key,
                            "pageSize": min(limit, 100)
                        }
                        
                        async with session.get(url, params=params) as response:
                            if response.status != 200:
                                self.logger.warning(f"Failed to fetch news for {category}: {response.status}")
                                continue
                            
                            data = await response.json()
                            articles = data.get("articles", [])
                            
                            for article in articles:
                                if article.get("title") and article.get("description"):
                                    content = LearningContent(
                                        title=article.get("title", ""),
                                        description=article.get("description", ""),
                                        content=article.get("content", ""),
                                        url=article.get("url", ""),
                                        source="news",
                                        published_at=datetime.now(),
                                        tags=[category, "news", "current-events"],
                                        quality_score=0.7,
                                        metadata={
                                            "category": category,
                                            "source": article.get("source", {}).get("name", ""),
                                        }
                                    )
                                    contents.append(content)
                                    
                                    if len(contents) >= limit:
                                        break
                        
                        if len(contents) >= limit:
                            break
                            
                    except Exception as e:
                        self.logger.warning(f"Failed to fetch news for {category}: {e}")
                        continue
            
            self.logger.info(f"Fetched {len(contents)} news articles")
            return contents[:limit]
            
        except Exception as e:
            self.logger.error(f"Error fetching news content: {e}")
            return []
    
    async def health_check(self) -> bool:
        """Check if news API is accessible"""
        try:
            if not self.api_key:
                return False
                
            async with aiohttp.ClientSession() as session:
                url = "https://newsapi.org/v2/top-headlines"
                params = {"category": "technology", "apiKey": self.api_key, "pageSize": 1}
                async with session.get(url, params=params, timeout=5) as response:
                    return response.status == 200
        except Exception as e:
            self.logger.error(f"News health check failed: {e}")
            return False
