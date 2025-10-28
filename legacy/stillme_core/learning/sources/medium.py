"""
Medium Learning Source
=====================

Fetches learning content from Medium RSS feeds.
"""

import asyncio
import logging
from datetime import datetime
from typing import Any, Dict, List
from xml.etree import ElementTree

import aiohttp

from .base import BaseLearningSource, LearningContent

logger = logging.getLogger(__name__)


class MediumSource(BaseLearningSource):
    """Medium learning source"""
    
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__("medium", config)
        self.publications = self.config.get("publications", [
            "https://towardsdatascience.com/feed",
            "https://feeds.feedburner.com/oreilly/radar",
            "https://blog.openai.com/rss.xml"
        ])
    
    async def fetch_content(self, limit: int = 10) -> List[LearningContent]:
        """Fetch latest articles from Medium publications"""
        try:
            contents = []
            articles_per_publication = max(1, limit // len(self.publications))
            
            # Add headers to avoid blocking
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            async with aiohttp.ClientSession(headers=headers) as session:
                for publication_url in self.publications:
                    try:
                        async with session.get(publication_url) as response:
                            if response.status != 200:
                                self.logger.warning(f"Failed to fetch Medium publication: {response.status}")
                                continue
                            
                            xml_content = await response.text()
                            root = ElementTree.fromstring(xml_content)
                            
                            items = root.findall(".//item")[:articles_per_publication]
                            
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
                                        source="medium",
                                        published_at=datetime.now(),
                                        tags=["medium", "article", "blog", "tutorial"],
                                        quality_score=0.8,
                                        metadata={
                                            "source": "medium",
                                            "publication": publication_url,
                                        }
                                    )
                                    contents.append(content)
                                    
                                    if len(contents) >= limit:
                                        break
                        
                        if len(contents) >= limit:
                            break
                            
                    except Exception as e:
                        self.logger.warning(f"Failed to fetch Medium publication: {e}")
                        continue
            
            self.logger.info(f"Fetched {len(contents)} articles from Medium")
            return contents[:limit]
            
        except Exception as e:
            self.logger.error(f"Error fetching Medium content: {e}")
            return []
    
    async def health_check(self) -> bool:
        """Check if Medium RSS is accessible"""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            async with aiohttp.ClientSession(headers=headers) as session:
                async with session.get(self.publications[0], timeout=5) as response:
                    return response.status == 200
        except Exception as e:
            self.logger.error(f"Medium health check failed: {e}")
            return False
