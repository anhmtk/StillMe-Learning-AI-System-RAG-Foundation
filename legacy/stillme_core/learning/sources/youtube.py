"""
YouTube Learning Source
======================

Fetches learning content from YouTube API.
"""

import asyncio
import logging
from datetime import datetime
from typing import Any, Dict, List

import aiohttp

from .base import BaseLearningSource, LearningContent

logger = logging.getLogger(__name__)


class YouTubeSource(BaseLearningSource):
    """YouTube learning source"""
    
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__("youtube", config)
        self.api_key = self.config.get("youtube_api_key")
        self.channels = self.config.get("channels", [
            "UC8butISFwT-Wl7EV0hUK0BQ",  # freeCodeCamp
            "UCbfYPyITQ-7l4upoX8nvctg",  # 2 Minute Papers
            "UC9-y-6csu5WGm29I7JiwpnA"   # Computerphile
        ])
    
    async def fetch_content(self, limit: int = 10) -> List[LearningContent]:
        """Fetch latest videos from YouTube channels"""
        try:
            contents = []
            
            if not self.api_key:
                self.logger.warning("No YouTube API key provided")
                return contents
            
            videos_per_channel = max(1, limit // len(self.channels))
            
            async with aiohttp.ClientSession() as session:
                for channel_id in self.channels:
                    try:
                        url = "https://www.googleapis.com/youtube/v3/search"
                        params = {
                            "part": "snippet",
                            "channelId": channel_id,
                            "order": "date",
                            "type": "video",
                            "maxResults": videos_per_channel,
                            "key": self.api_key
                        }
                        
                        async with session.get(url, params=params) as response:
                            if response.status != 200:
                                self.logger.warning(f"Failed to fetch YouTube videos for channel {channel_id}: {response.status}")
                                continue
                            
                            data = await response.json()
                            videos = data.get("items", [])
                            
                            for video in videos:
                                snippet = video.get("snippet", {})
                                
                                content = LearningContent(
                                    title=snippet.get("title", ""),
                                    description=snippet.get("description", ""),
                                    content=snippet.get("description", ""),
                                    url=f"https://www.youtube.com/watch?v={video.get('id', {}).get('videoId', '')}",
                                    source="youtube",
                                    published_at=datetime.now(),
                                    tags=["youtube", "video", "tutorial", "education"],
                                    quality_score=0.8,
                                    metadata={
                                        "video_id": video.get("id", {}).get("videoId", ""),
                                        "channel_id": channel_id,
                                        "channel_title": snippet.get("channelTitle", ""),
                                    }
                                )
                                contents.append(content)
                                
                                if len(contents) >= limit:
                                    break
                        
                        if len(contents) >= limit:
                            break
                            
                    except Exception as e:
                        self.logger.warning(f"Failed to fetch YouTube videos for channel {channel_id}: {e}")
                        continue
            
            self.logger.info(f"Fetched {len(contents)} videos from YouTube")
            return contents[:limit]
            
        except Exception as e:
            self.logger.error(f"Error fetching YouTube content: {e}")
            return []
    
    async def health_check(self) -> bool:
        """Check if YouTube API is accessible"""
        try:
            if not self.api_key:
                return False
                
            async with aiohttp.ClientSession() as session:
                url = "https://www.googleapis.com/youtube/v3/search"
                params = {
                    "part": "snippet",
                    "q": "python programming",
                    "type": "video",
                    "maxResults": 1,
                    "key": self.api_key
                }
                async with session.get(url, params=params, timeout=5) as response:
                    return response.status == 200
        except Exception as e:
            self.logger.error(f"YouTube health check failed: {e}")
            return False
