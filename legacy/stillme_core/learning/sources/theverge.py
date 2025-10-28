"""
The Verge Learning Source
=========================

Fetches learning content from The Verge RSS feed.
"""

import asyncio
import logging
from datetime import datetime
from typing import Any, Dict, List
from xml.etree import ElementTree

import aiohttp

from .base import BaseLearningSource, LearningContent

logger = logging.getLogger(__name__)


class TheVergeSource(BaseLearningSource):
    """The Verge learning source"""
    
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__("theverge", config)
        self.rss_url = "https://www.theverge.com/rss/index.xml"
    
    async def fetch_content(self, limit: int = 10) -> List[LearningContent]:
        """Fetch latest articles from The Verge RSS"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(self.rss_url) as response:
                    if response.status != 200:
                        self.logger.error(f"Failed to fetch The Verge RSS: {response.status}")
                        return []
                    
                    xml_content = await response.text()
                    root = ElementTree.fromstring(xml_content)
                    
                    contents = []
                    items = root.findall(".//item")[:limit]
                    
                    for item in items:
                        title = item.find("title")
                        description = item.find("description")
                        link = item.find("link")
                        
                        if all([title, description, link]):
                            content = LearningContent(
                                title=title.text or "",
                                description=description.text or "",
                                content=description.text or "",
                                url=link.text or "",
                                source="theverge",
                                published_at=datetime.now(),
                                tags=["tech", "gadgets", "reviews", "innovation"],
                                quality_score=0.8,
                                metadata={
                                    "source": "theverge",
                                    "category": "technology",
                                }
                            )
                            contents.append(content)
                    
                    self.logger.info(f"Fetched {len(contents)} articles from The Verge")
                    return contents
                    
        except Exception as e:
            self.logger.error(f"Error fetching The Verge content: {e}")
            return []
    
    async def health_check(self) -> bool:
        """Check if The Verge RSS is accessible"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(self.rss_url, timeout=5) as response:
                    return response.status == 200
        except Exception as e:
            self.logger.error(f"The Verge health check failed: {e}")
            return False
