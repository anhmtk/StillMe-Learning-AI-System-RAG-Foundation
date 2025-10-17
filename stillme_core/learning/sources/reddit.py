"""
Reddit Learning Source
======================

Fetches learning content from Reddit API.
"""

import asyncio
import logging
from datetime import datetime
from typing import Any, Dict, List

import aiohttp

from .base import BaseLearningSource, LearningContent

logger = logging.getLogger(__name__)


class RedditSource(BaseLearningSource):
    """Reddit learning source"""
    
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__("reddit", config)
        self.subreddits = self.config.get("subreddits", [
            "MachineLearning", "artificial", "programming", "Python", 
            "javascript", "webdev", "datascience", "compsci"
        ])
        self.min_score = self.config.get("min_score", 50)
        self.min_comments = self.config.get("min_comments", 5)
    
    async def fetch_content(self, limit: int = 10) -> List[LearningContent]:
        """Fetch top posts from Reddit subreddits"""
        try:
            contents = []
            posts_per_subreddit = max(1, limit // len(self.subreddits))
            
            async with aiohttp.ClientSession() as session:
                for subreddit in self.subreddits:
                    try:
                        url = f"https://www.reddit.com/r/{subreddit}/hot.json?limit={posts_per_subreddit}"
                        headers = {"User-Agent": "StillMe-AI-Learning/1.0"}
                        
                        async with session.get(url, headers=headers) as response:
                            if response.status != 200:
                                self.logger.warning(f"Failed to fetch r/{subreddit}: {response.status}")
                                continue
                            
                            data = await response.json()
                            posts = data.get("data", {}).get("children", [])
                            
                            for post_data in posts:
                                post = post_data.get("data", {})
                                
                                # Filter by score and comments
                                if (post.get("score", 0) >= self.min_score and 
                                    post.get("num_comments", 0) >= self.min_comments):
                                    
                                    content = LearningContent(
                                        title=post.get("title", ""),
                                        description=post.get("selftext", "")[:200] + "...",
                                        content=post.get("selftext", ""),
                                        url=f"https://reddit.com{post.get('permalink', '')}",
                                        source="reddit",
                                        published_at=datetime.fromtimestamp(post.get("created_utc", 0)),
                                        tags=[subreddit.lower(), "reddit", "discussion"],
                                        quality_score=min(post.get("score", 0) / 1000, 1.0),
                                        metadata={
                                            "subreddit": subreddit,
                                            "score": post.get("score", 0),
                                            "comments": post.get("num_comments", 0),
                                            "author": post.get("author", ""),
                                            "upvote_ratio": post.get("upvote_ratio", 0),
                                        }
                                    )
                                    contents.append(content)
                                    
                                    if len(contents) >= limit:
                                        break
                        
                        if len(contents) >= limit:
                            break
                            
                    except Exception as e:
                        self.logger.warning(f"Failed to fetch r/{subreddit}: {e}")
                        continue
            
            self.logger.info(f"Fetched {len(contents)} posts from Reddit")
            return contents[:limit]
            
        except Exception as e:
            self.logger.error(f"Error fetching Reddit content: {e}")
            return []
    
    async def health_check(self) -> bool:
        """Check if Reddit API is accessible"""
        try:
            async with aiohttp.ClientSession() as session:
                headers = {"User-Agent": "StillMe-AI-Learning/1.0"}
                async with session.get("https://www.reddit.com/r/programming/hot.json?limit=1", 
                                     headers=headers, timeout=5) as response:
                    return response.status == 200
        except Exception as e:
            self.logger.error(f"Reddit health check failed: {e}")
            return False
