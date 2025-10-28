"""
GitHub Learning Source
======================

Fetches learning content from GitHub API.
"""

import asyncio
import logging
from datetime import datetime
from typing import Any, Dict, List

import aiohttp

from .base import BaseLearningSource, LearningContent

logger = logging.getLogger(__name__)


class GitHubSource(BaseLearningSource):
    """GitHub learning source"""
    
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__("github", config)
        self.token = self.config.get("github_token")
        self.topics = self.config.get("topics", [
            "machine-learning", "artificial-intelligence", "python", 
            "javascript", "react", "nodejs", "data-science"
        ])
        self.min_stars = self.config.get("min_stars", 100)
    
    async def fetch_content(self, limit: int = 10) -> List[LearningContent]:
        """Fetch trending repositories from GitHub"""
        try:
            contents = []
            repos_per_topic = max(1, limit // len(self.topics))
            
            headers = {}
            if self.token:
                headers["Authorization"] = f"token {self.token}"
            
            async with aiohttp.ClientSession() as session:
                for topic in self.topics:
                    try:
                        # Search for trending repositories
                        url = f"https://api.github.com/search/repositories"
                        params = {
                            "q": f"topic:{topic} stars:>={self.min_stars}",
                            "sort": "stars",
                            "order": "desc",
                            "per_page": repos_per_topic
                        }
                        
                        async with session.get(url, params=params, headers=headers) as response:
                            if response.status != 200:
                                self.logger.warning(f"Failed to fetch GitHub repos for {topic}: {response.status}")
                                continue
                            
                            data = await response.json()
                            repos = data.get("items", [])
                            
                            for repo in repos:
                                content = LearningContent(
                                    title=f"{repo.get('name', '')} - {repo.get('description', '')[:100]}",
                                    description=repo.get("description", ""),
                                    content=f"Repository: {repo.get('full_name', '')}\n"
                                           f"Description: {repo.get('description', '')}\n"
                                           f"Language: {repo.get('language', 'N/A')}\n"
                                           f"Stars: {repo.get('stargazers_count', 0)}",
                                    url=repo.get("html_url", ""),
                                    source="github",
                                    published_at=datetime.fromisoformat(repo.get("updated_at", "").replace("Z", "+00:00")),
                                    tags=[topic, repo.get("language", "").lower(), "github", "repository"],
                                    quality_score=min(repo.get("stargazers_count", 0) / 10000, 1.0),
                                    metadata={
                                        "full_name": repo.get("full_name", ""),
                                        "stars": repo.get("stargazers_count", 0),
                                        "forks": repo.get("forks_count", 0),
                                        "language": repo.get("language", ""),
                                        "topics": repo.get("topics", []),
                                        "size": repo.get("size", 0),
                                    }
                                )
                                contents.append(content)
                                
                                if len(contents) >= limit:
                                    break
                        
                        if len(contents) >= limit:
                            break
                            
                    except Exception as e:
                        self.logger.warning(f"Failed to fetch GitHub repos for {topic}: {e}")
                        continue
            
            self.logger.info(f"Fetched {len(contents)} repositories from GitHub")
            return contents[:limit]
            
        except Exception as e:
            self.logger.error(f"Error fetching GitHub content: {e}")
            return []
    
    async def health_check(self) -> bool:
        """Check if GitHub API is accessible"""
        try:
            headers = {}
            if self.token:
                headers["Authorization"] = f"token {self.token}"
            
            async with aiohttp.ClientSession() as session:
                async with session.get("https://api.github.com/search/repositories?q=python&per_page=1", 
                                     headers=headers, timeout=5) as response:
                    return response.status == 200
        except Exception as e:
            self.logger.error(f"GitHub health check failed: {e}")
            return False
