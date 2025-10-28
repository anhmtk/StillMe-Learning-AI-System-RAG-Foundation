"""
ArXiv Learning Source
=====================

Fetches learning content from ArXiv API.
"""

import asyncio
import logging
from datetime import datetime
from typing import Any, Dict, List
from xml.etree import ElementTree

import aiohttp

from .base import BaseLearningSource, LearningContent

logger = logging.getLogger(__name__)


class ArXivSource(BaseLearningSource):
    """ArXiv learning source"""
    
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__("arxiv", config)
        self.categories = self.config.get("categories", [
            "cs.AI", "cs.LG", "cs.CV", "cs.NLP", "cs.CL", "cs.IR"
        ])
    
    async def fetch_content(self, limit: int = 10) -> List[LearningContent]:
        """Fetch latest papers from ArXiv"""
        try:
            contents = []
            papers_per_category = max(1, limit // len(self.categories))
            
            # Use SSL context that doesn't verify certificates for ArXiv
            import ssl
            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE
            
            connector = aiohttp.TCPConnector(ssl=ssl_context)
            async with aiohttp.ClientSession(connector=connector) as session:
                for category in self.categories:
                    try:
                        url = f"http://export.arxiv.org/api/query"
                        params = {
                            "search_query": f"cat:{category}",
                            "start": 0,
                            "max_results": papers_per_category,
                            "sortBy": "submittedDate",
                            "sortOrder": "descending"
                        }
                        
                        async with session.get(url, params=params) as response:
                            if response.status != 200:
                                self.logger.warning(f"Failed to fetch ArXiv papers for {category}: {response.status}")
                                continue
                            
                            xml_content = await response.text()
                            root = ElementTree.fromstring(xml_content)
                            
                            entries = root.findall(".//{http://www.w3.org/2005/Atom}entry")
                            
                            for entry in entries:
                                title = entry.find(".//{http://www.w3.org/2005/Atom}title")
                                summary = entry.find(".//{http://www.w3.org/2005/Atom}summary")
                                link = entry.find(".//{http://www.w3.org/2005/Atom}id")
                                published = entry.find(".//{http://www.w3.org/2005/Atom}published")
                                
                                if all([title, summary, link]):
                                    content = LearningContent(
                                        title=title.text or "",
                                        description=summary.text or "",
                                        content=summary.text or "",
                                        url=link.text or "",
                                        source="arxiv",
                                        published_at=datetime.now(),  # Parse published if needed
                                        tags=["research", "ai", "machine-learning", "academic"],
                                        quality_score=0.9,
                                        metadata={
                                            "category": category,
                                            "source": "arxiv",
                                            "type": "research_paper",
                                        }
                                    )
                                    contents.append(content)
                                    
                                    if len(contents) >= limit:
                                        break
                        
                        if len(contents) >= limit:
                            break
                            
                    except Exception as e:
                        self.logger.warning(f"Failed to fetch ArXiv papers for {category}: {e}")
                        continue
            
            self.logger.info(f"Fetched {len(contents)} papers from ArXiv")
            return contents[:limit]
            
        except Exception as e:
            self.logger.error(f"Error fetching ArXiv content: {e}")
            return []
    
    async def health_check(self) -> bool:
        """Check if ArXiv API is accessible"""
        try:
            # Use SSL context that doesn't verify certificates for ArXiv
            import ssl
            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE
            
            connector = aiohttp.TCPConnector(ssl=ssl_context)
            async with aiohttp.ClientSession(connector=connector) as session:
                async with session.get("http://export.arxiv.org/api/query?search_query=cat:cs.AI&max_results=1", 
                                     timeout=5) as response:
                    return response.status == 200
        except Exception as e:
            self.logger.error(f"ArXiv health check failed: {e}")
            return False
