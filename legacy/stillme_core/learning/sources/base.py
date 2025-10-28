"""
Base Learning Source
===================

Base class for all learning sources with common functionality.
"""

import asyncio
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class LearningContent:
    """Learning content from a source"""
    
    title: str
    description: str
    content: str
    url: str
    source: str
    published_at: datetime
    tags: List[str]
    quality_score: float
    metadata: Dict[str, Any]


class BaseLearningSource(ABC):
    """Base class for all learning sources"""
    
    def __init__(self, name: str, config: Dict[str, Any] = None):
        self.name = name
        self.config = config or {}
        self.logger = logging.getLogger(f"learning.source.{name}")
        
    @abstractmethod
    async def fetch_content(self, limit: int = 10) -> List[LearningContent]:
        """Fetch learning content from the source"""
        pass
    
    @abstractmethod
    async def health_check(self) -> bool:
        """Check if the source is healthy and accessible"""
        pass
    
    def get_source_info(self) -> Dict[str, Any]:
        """Get information about this source"""
        return {
            "name": self.name,
            "config": self.config,
            "type": self.__class__.__name__,
        }
    
    async def process_content(self, content: LearningContent) -> Dict[str, Any]:
        """Process content for learning proposals"""
        return {
            "title": content.title,
            "description": content.description,
            "content": content.content,
            "source": self.name,
            "url": content.url,
            "tags": content.tags,
            "quality_score": content.quality_score,
            "metadata": content.metadata,
        }
