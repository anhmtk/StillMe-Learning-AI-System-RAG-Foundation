"""
Hacker News Learning Source
===========================

Fetches learning content from Hacker News API.
"""

import asyncio
import logging
from datetime import datetime
from typing import Any, Dict, List

import aiohttp

from .base import BaseLearningSource, LearningContent

logger = logging.getLogger(__name__)


class HackerNewsSource(BaseLearningSource):
    """Hacker News learning source"""
    
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__("hackernews", config)
        self.base_url = "https://hacker-news.firebaseio.com/v0"
        self.min_score = self.config.get("min_score", 100)
        self.min_comments = self.config.get("min_comments", 10)
    
    async def fetch_content(self, limit: int = 10) -> List[LearningContent]:
        """Fetch top stories from Hacker News"""
        try:
            async with aiohttp.ClientSession() as session:
                # Get top stories
                async with session.get(f"{self.base_url}/topstories.json") as response:
                    if response.status != 200:
                        self.logger.error(f"Failed to fetch HN stories: {response.status}")
                        return []
                    
                    story_ids = await response.json()
                
                # Fetch story details
                contents = []
                for story_id in story_ids[:limit * 2]:  # Get more to filter
                    try:
                        async with session.get(f"{self.base_url}/item/{story_id}.json") as response:
                            if response.status != 200:
                                continue
                            
                            story = await response.json()
                            
                            # Filter by score and comments
                            if (story.get("score", 0) >= self.min_score and 
                                story.get("descendants", 0) >= self.min_comments and
                                story.get("type") == "story"):
                                
                                content = LearningContent(
                                    title=story.get("title", ""),
                                    description=f"Score: {story.get('score', 0)}, Comments: {story.get('descendants', 0)}",
                                    content=story.get("title", ""),
                                    url=story.get("url", f"https://news.ycombinator.com/item?id={story_id}"),
                                    source="hackernews",
                                    published_at=datetime.fromtimestamp(story.get("time", 0)),
                                    tags=["tech", "programming", "startup", "ai"],
                                    quality_score=min(story.get("score", 0) / 1000, 1.0),
                                    metadata={
                                        "story_id": story_id,
                                        "score": story.get("score", 0),
                                        "comments": story.get("descendants", 0),
                                        "author": story.get("by", ""),
                                    }
                                )
                                contents.append(content)
                                
                                if len(contents) >= limit:
                                    break
                                    
                    except Exception as e:
                        self.logger.warning(f"Failed to fetch story {story_id}: {e}")
                        continue
                
                self.logger.info(f"Fetched {len(contents)} stories from Hacker News")
                return contents
                
        except Exception as e:
            self.logger.error(f"Error fetching Hacker News content: {e}")
            return []
    
    async def health_check(self) -> bool:
        """Check if Hacker News API is accessible"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.base_url}/topstories.json", timeout=5) as response:
                    return response.status == 200
        except Exception as e:
            self.logger.error(f"Hacker News health check failed: {e}")
            return False
