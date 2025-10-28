"""
Subreddits Learning Source
==========================

Fetches learning content from specific subreddits.
"""

import asyncio
import logging
from datetime import datetime
from typing import Any, Dict, List

import aiohttp

from .base import BaseLearningSource, LearningContent

logger = logging.getLogger(__name__)


class SubredditsSource(BaseLearningSource):
    """Subreddits learning source"""
    
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__("subreddits", config)
        self.subreddits = self.config.get("subreddits", [
            "learnprogramming", "learnpython", "learnjavascript", 
            "learnmachinelearning", "datascience", "compsci",
            "programming", "webdev", "cscareerquestions"
        ])
        self.min_score = self.config.get("min_score", 20)
    
    async def fetch_content(self, limit: int = 10) -> List[LearningContent]:
        """Fetch top posts from learning subreddits"""
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
                                
                                # Filter by score and ensure it's educational content
                                if (post.get("score", 0) >= self.min_score and 
                                    any(keyword in post.get("title", "").lower() for keyword in 
                                        ["learn", "tutorial", "guide", "how to", "explain", "help"])):
                                    
                                    content = LearningContent(
                                        title=post.get("title", ""),
                                        description=post.get("selftext", "")[:200] + "...",
                                        content=post.get("selftext", ""),
                                        url=f"https://reddit.com{post.get('permalink', '')}",
                                        source="subreddits",
                                        published_at=datetime.fromtimestamp(post.get("created_utc", 0)),
                                        tags=[subreddit.lower(), "reddit", "learning", "education"],
                                        quality_score=min(post.get("score", 0) / 500, 1.0),
                                        metadata={
                                            "subreddit": subreddit,
                                            "score": post.get("score", 0),
                                            "comments": post.get("num_comments", 0),
                                            "author": post.get("author", ""),
                                            "flair": post.get("link_flair_text", ""),
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
            
            self.logger.info(f"Fetched {len(contents)} learning posts from subreddits")
            return contents[:limit]
            
        except Exception as e:
            self.logger.error(f"Error fetching subreddits content: {e}")
            return []
    
    async def health_check(self) -> bool:
        """Check if subreddits are accessible"""
        try:
            async with aiohttp.ClientSession() as session:
                headers = {"User-Agent": "StillMe-AI-Learning/1.0"}
                async with session.get("https://www.reddit.com/r/learnprogramming/hot.json?limit=1", 
                                     headers=headers, timeout=5) as response:
                    return response.status == 200
        except Exception as e:
            self.logger.error(f"Subreddits health check failed: {e}")
            return False
