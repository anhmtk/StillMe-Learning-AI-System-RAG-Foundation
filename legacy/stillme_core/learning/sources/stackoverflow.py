"""
Stack Overflow Learning Source
==============================

Fetches learning content from Stack Overflow API.
"""

import asyncio
import logging
from datetime import datetime
from typing import Any, Dict, List

import aiohttp

from .base import BaseLearningSource, LearningContent

logger = logging.getLogger(__name__)


class StackOverflowSource(BaseLearningSource):
    """Stack Overflow learning source"""
    
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__("stackoverflow", config)
        self.tags = self.config.get("tags", ["python", "javascript", "machine-learning", "ai"])
        self.min_score = self.config.get("min_score", 10)
    
    async def fetch_content(self, limit: int = 10) -> List[LearningContent]:
        """Fetch top questions from Stack Overflow"""
        try:
            contents = []
            questions_per_tag = max(1, limit // len(self.tags))
            
            async with aiohttp.ClientSession() as session:
                for tag in self.tags:
                    try:
                        url = "https://api.stackexchange.com/2.3/questions"
                        params = {
                            "order": "desc",
                            "sort": "votes",
                            "tagged": tag,
                            "site": "stackoverflow",
                            "pagesize": questions_per_tag,
                            "filter": "withbody"
                        }
                        
                        async with session.get(url, params=params) as response:
                            if response.status != 200:
                                self.logger.warning(f"Failed to fetch SO questions for {tag}: {response.status}")
                                continue
                            
                            data = await response.json()
                            questions = data.get("items", [])
                            
                            for question in questions:
                                if question.get("score", 0) >= self.min_score:
                                    content = LearningContent(
                                        title=question.get("title", ""),
                                        description=question.get("body", "")[:200] + "...",
                                        content=question.get("body", ""),
                                        url=question.get("link", ""),
                                        source="stackoverflow",
                                        published_at=datetime.fromtimestamp(question.get("creation_date", 0)),
                                        tags=[tag, "stackoverflow", "programming", "q&a"],
                                        quality_score=min(question.get("score", 0) / 100, 1.0),
                                        metadata={
                                            "question_id": question.get("question_id"),
                                            "score": question.get("score", 0),
                                            "answers": question.get("answer_count", 0),
                                            "views": question.get("view_count", 0),
                                            "tags": question.get("tags", []),
                                        }
                                    )
                                    contents.append(content)
                                    
                                    if len(contents) >= limit:
                                        break
                        
                        if len(contents) >= limit:
                            break
                            
                    except Exception as e:
                        self.logger.warning(f"Failed to fetch SO questions for {tag}: {e}")
                        continue
            
            self.logger.info(f"Fetched {len(contents)} questions from Stack Overflow")
            return contents[:limit]
            
        except Exception as e:
            self.logger.error(f"Error fetching Stack Overflow content: {e}")
            return []
    
    async def health_check(self) -> bool:
        """Check if Stack Overflow API is accessible"""
        try:
            async with aiohttp.ClientSession() as session:
                url = "https://api.stackexchange.com/2.3/questions"
                params = {"order": "desc", "sort": "votes", "tagged": "python", "site": "stackoverflow", "pagesize": 1}
                async with session.get(url, params=params, timeout=5) as response:
                    return response.status == 200
        except Exception as e:
            self.logger.error(f"Stack Overflow health check failed: {e}")
            return False
