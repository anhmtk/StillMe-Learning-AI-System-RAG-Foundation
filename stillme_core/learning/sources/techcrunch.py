"""
TechCrunch Learning Source
==========================

Fetches learning content from TechCrunch RSS feed.
"""

import asyncio
import logging
from datetime import datetime
from typing import Any, Dict, List
from xml.etree import ElementTree

import aiohttp

from .base import BaseLearningSource, LearningContent

logger = logging.getLogger(__name__)


class TechCrunchSource(BaseLearningSource):
    """TechCrunch learning source"""
    
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__("techcrunch", config)
        self.rss_url = "https://techcrunch.com/feed/"
    
    async def fetch_content(self, limit: int = 10) -> List[LearningContent]:
        """Fetch latest articles from TechCrunch RSS"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(self.rss_url) as response:
                    if response.status != 200:
                        self.logger.error(f"Failed to fetch TechCrunch RSS: {response.status}")
                        return []
                    
                    xml_content = await response.text()
                    root = ElementTree.fromstring(xml_content)
                    
                    contents = []
                    items = root.findall(".//item")[:limit]
                    
                    for item in items:
                        title = item.find("title")
                        description = item.find("description")
                        link = item.find("link")
                        pub_date = item.find("pubDate")
                        
                        if all([title, description, link]):
                            content = LearningContent(
                                title=title.text or "",
                                description=description.text or "",
                                content=description.text or "",
                                url=link.text or "",
                                source="techcrunch",
                                published_at=datetime.now(),  # Parse pub_date if needed
                                tags=["tech", "startup", "innovation", "business"],
                                quality_score=0.8,
                                metadata={
                                    "source": "techcrunch",
                                    "category": "technology",
                                }
                            )
                            contents.append(content)
                    
                    self.logger.info(f"Fetched {len(contents)} articles from TechCrunch")
                    return contents
                    
        except Exception as e:
            self.logger.error(f"Error fetching TechCrunch content: {e}")
            return []
    
    async def health_check(self) -> bool:
        """Check if TechCrunch RSS is accessible"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(self.rss_url, timeout=5) as response:
                    return response.status == 200
        except Exception as e:
            self.logger.error(f"TechCrunch health check failed: {e}")
            return False
