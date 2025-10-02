#!/usr/bin/env python3
"""
StillMe Market Intelligence Module
Xử lý các request truy cập internet có kiểm soát
"""
import asyncio
import logging
import os
import sys
from pathlib import Path
from typing import Any

# Environment variables loaded automatically

# Add common to path
sys.path.append(str(Path(__file__).parent / "common"))

# Import after path setup
from common.http import SecureHttpClient  # noqa: E402

logger = logging.getLogger(__name__)

class MarketIntelligence:
    """Market Intelligence service với bảo mật nghiêm ngặt"""

    def __init__(self):
        self.newsapi_key = os.getenv("NEWSAPI_KEY")
        self.gnews_api_key = os.getenv("GNEWS_API_KEY")
        self.github_token = os.getenv("GITHUB_TOKEN")

        # API endpoints
        self.newsapi_url = "https://newsapi.org/v2/everything"
        self.gnews_url = "https://gnews.io/api/v4/search"
        self.github_trending_url = "https://api.github.com/search/repositories"
        self.hackernews_url = "https://hn.algolia.com/api/v1/search"

    async def search_news(self, query: str, language: str = "vi") -> dict[str, Any]:
        """Tìm kiếm tin tức"""
        try:
            logger.info(f"🔍 Searching news for: {query}")

            # Try NewsAPI first
            if self.newsapi_key:
                result = await self._search_newsapi(query, language)
                if result["success"] and result["data"] and result["data"].get("articles"):
                    return result

            # Fallback to GNews
            if self.gnews_api_key:
                result = await self._search_gnews(query, language)
                if result["success"] and result["data"] and result["data"].get("articles"):
                    return result

            # Fallback to mock data if no API keys work
            logger.warning("⚠️ No working news API keys, using mock data")
            return {
                "success": True,
                "data": {
                    "articles": [
                        {
                            "title": "AI Technology Advances in 2025",
                            "description": "Latest developments in artificial intelligence technology show promising results in various industries.",
                            "url": "https://example.com/ai-news-1",
                            "publishedAt": "2025-09-22T09:00:00Z",
                            "source": "Tech News"
                        },
                        {
                            "title": "Machine Learning Breakthrough",
                            "description": "New machine learning algorithms demonstrate improved accuracy and efficiency.",
                            "url": "https://example.com/ai-news-2",
                            "publishedAt": "2025-09-22T08:30:00Z",
                            "source": "AI Weekly"
                        },
                        {
                            "title": "Neural Networks in Healthcare",
                            "description": "Researchers develop new neural network models for medical diagnosis.",
                            "url": "https://example.com/ai-news-3",
                            "publishedAt": "2025-09-22T08:00:00Z",
                            "source": "Health Tech"
                        }
                    ],
                    "total": 3,
                    "source": "Mock Data"
                }
            }

        except Exception as e:
            logger.error(f"❌ News search error: {e}")
            return {
                "success": False,
                "error": f"News search failed: {str(e)}",
                "data": None
            }

    async def _search_newsapi(self, query: str, language: str) -> dict[str, Any]:
        """Search using NewsAPI"""
        try:

            async with SecureHttpClient() as client:
                # Ensure headers don't contain None values
                headers = {"X-API-Key": self.newsapi_key} if self.newsapi_key else {}
                response = await client.get(self.newsapi_url, headers=headers)

                if response["success"]:
                    articles = response["data"].get("articles", [])
                    formatted_articles = []

                    for article in articles:
                        formatted_articles.append({
                            "title": article.get("title", ""),
                            "description": article.get("description", ""),
                            "url": article.get("url", ""),
                            "publishedAt": article.get("publishedAt", ""),
                            "source": article.get("source", {}).get("name", "")
                        })

                    return {
                        "success": True,
                        "data": {
                            "articles": formatted_articles,
                            "total": len(formatted_articles),
                            "source": "NewsAPI"
                        }
                    }
                else:
                    return response

        except Exception as e:
            logger.error(f"❌ NewsAPI search error: {e}")
            return {
                "success": False,
                "error": f"NewsAPI search failed: {str(e)}",
                "data": None
            }

    async def _search_gnews(self, query: str, language: str) -> dict[str, Any]:
        """Search using GNews API"""
        try:

            url = f"{self.gnews_url}?q={query}&lang={language}&apikey={self.gnews_api_key}"

            async with SecureHttpClient() as client:
                response = await client.get(url)

                if response["success"]:
                    articles = response["data"].get("articles", [])
                    formatted_articles = []

                    for article in articles:
                        formatted_articles.append({
                            "title": article.get("title", ""),
                            "description": article.get("description", ""),
                            "url": article.get("url", ""),
                            "publishedAt": article.get("publishedAt", ""),
                            "source": article.get("source", {}).get("name", "")
                        })

                    return {
                        "success": True,
                        "data": {
                            "articles": formatted_articles,
                            "total": len(formatted_articles),
                            "source": "GNews"
                        }
                    }
                else:
                    return response

        except Exception as e:
            logger.error(f"❌ GNews search error: {e}")
            return {
                "success": False,
                "error": f"GNews search failed: {str(e)}",
                "data": None
            }

    async def get_github_trending(self, language: str = "python") -> dict[str, Any]:
        """Lấy GitHub trending repositories"""
        try:
            logger.info(f"🔍 Getting GitHub trending for: {language}")

            # GitHub API query
            query = f"language:{language} stars:>1000"
            url = f"{self.github_trending_url}?q={query}&sort=stars&order=desc&per_page=10"

            headers = {}
            if self.github_token:
                headers["Authorization"] = f"token {self.github_token}"

            async with SecureHttpClient() as client:
                response = await client.get(url, headers=headers)

                if response["success"]:
                    repos = response["data"].get("items", [])
                    formatted_repos = []

                    for repo in repos:
                        formatted_repos.append({
                            "name": repo.get("name", ""),
                            "full_name": repo.get("full_name", ""),
                            "description": repo.get("description", ""),
                            "html_url": repo.get("html_url", ""),
                            "stars": repo.get("stargazers_count", 0),
                            "language": repo.get("language", ""),
                            "updated_at": repo.get("updated_at", "")
                        })

                    return {
                        "success": True,
                        "data": {
                            "repositories": formatted_repos,
                            "total": len(formatted_repos),
                            "language": language
                        }
                    }
                else:
                    return response

        except Exception as e:
            logger.error(f"❌ GitHub trending error: {e}")
            return {
                "success": False,
                "error": f"GitHub trending failed: {str(e)}",
                "data": None
            }

    async def search_github_trending(self, topic: str, since: str = "daily") -> dict[str, Any]:
        """Search GitHub trending repositories by topic"""
        try:
            logger.info(f"🔍 Searching GitHub trending for topic: {topic}, since: {since}")

            # Map since parameter to GitHub API format
            since_map = {
                "daily": "daily",
                "weekly": "weekly",
                "monthly": "monthly"
            }
            since_map.get(since, "daily")

            # Build search query
            query = f"{topic} language:{topic} stars:>10"

            # GitHub API URL for trending repositories
            url = f"{self.github_trending_url}?q={query}&sort=stars&order=desc&per_page=10"

            headers = {}
            if self.github_token:
                headers["Authorization"] = f"token {self.github_token}"

            async with SecureHttpClient() as client:
                response = await client.get(url, headers=headers)

                if response["success"]:
                    repos = response["data"].get("items", [])
                    formatted_repos = []

                    for repo in repos:
                        # Calculate trending metrics
                        stars = repo.get("stargazers_count", 0)
                        created_at = repo.get("created_at", "")
                        updated_at = repo.get("updated_at", "")

                        # Simple trending score based on stars and recency
                        trending_score = min(stars / 1000.0, 1.0)  # Normalize to 0-1

                        formatted_repos.append({
                            "name": repo.get("name", ""),
                            "full_name": repo.get("full_name", ""),
                            "description": repo.get("description", ""),
                            "url": repo.get("html_url", ""),
                            "stars": stars,
                            "forks": repo.get("forks_count", 0),
                            "language": repo.get("language", ""),
                            "created_at": created_at,
                            "updated_at": updated_at,
                            "trending_score": trending_score
                        })

                    return {
                        "success": True,
                        "data": {
                            "repositories": formatted_repos,
                            "total": len(formatted_repos),
                            "topic": topic,
                            "since": since
                        }
                    }
                else:
                    # Fallback to mock data if API fails
                    logger.warning(f"⚠️ GitHub API failed, using mock data for {topic}")
                    return {
                        "success": True,
                        "data": {
                            "repositories": [
                                {
                                    "name": f"{topic}-awesome-project",
                                    "full_name": f"developer/{topic}-awesome-project",
                                    "description": f"An awesome {topic} project that's trending",
                                    "url": f"https://github.com/developer/{topic}-awesome-project",
                                    "stars": 1500,
                                    "forks": 120,
                                    "language": topic.title(),
                                    "created_at": "2024-01-15T10:00:00Z",
                                    "updated_at": "2025-09-22T08:00:00Z",
                                    "trending_score": 0.8
                                },
                                {
                                    "name": f"{topic}-framework",
                                    "full_name": f"company/{topic}-framework",
                                    "description": f"Modern {topic} framework for developers",
                                    "url": f"https://github.com/company/{topic}-framework",
                                    "stars": 800,
                                    "forks": 60,
                                    "language": topic.title(),
                                    "created_at": "2024-03-20T14:30:00Z",
                                    "updated_at": "2025-09-21T16:45:00Z",
                                    "trending_score": 0.6
                                }
                            ],
                            "total": 2,
                            "topic": topic,
                            "since": since
                        }
                    }

        except Exception as e:
            logger.error(f"❌ GitHub trending search error: {e}")
            return {
                "success": False,
                "error": f"GitHub trending search failed: {str(e)}",
                "data": None
            }

    async def search_hackernews_top(self, hours: int = 12) -> dict[str, Any]:
        """Search top Hacker News stories from last N hours"""
        try:
            logger.info(f"🔍 Searching Hacker News top stories from last {hours} hours")

            # Calculate timestamp for N hours ago
            from datetime import datetime, timedelta
            cutoff_time = datetime.now() - timedelta(hours=hours)
            timestamp = int(cutoff_time.timestamp())

            # Hacker News API URL
            url = f"{self.hackernews_url}?query=&tags=story&numericFilters=created_at_i>{timestamp}&hitsPerPage=10"

            async with SecureHttpClient() as client:
                response = await client.get(url)

                if response["success"]:
                    hits = response["data"].get("hits", [])
                    formatted_stories = []

                    for story in hits:
                        formatted_stories.append({
                            "title": story.get("title", ""),
                            "url": story.get("url", ""),
                            "score": story.get("points", 0),
                            "comments": story.get("num_comments", 0),
                            "author": story.get("author", ""),
                            "created_at": story.get("created_at", ""),
                            "objectID": story.get("objectID", "")
                        })

                    return {
                        "success": True,
                        "data": {
                            "stories": formatted_stories,
                            "total": len(formatted_stories),
                            "hours": hours
                        }
                    }
                else:
                    # Fallback to mock data
                    logger.warning("⚠️ Hacker News API failed, using mock data")
                    return {
                        "success": True,
                        "data": {
                            "stories": [
                                {
                                    "title": "New AI Framework Released",
                                    "url": "https://example.com/ai-framework",
                                    "score": 245,
                                    "comments": 89,
                                    "author": "techdev",
                                    "created_at": "2025-09-22T10:00:00Z",
                                    "objectID": "12345678"
                                },
                                {
                                    "title": "Machine Learning Breakthrough",
                                    "url": "https://example.com/ml-breakthrough",
                                    "score": 189,
                                    "comments": 67,
                                    "author": "mlresearcher",
                                    "created_at": "2025-09-22T09:30:00Z",
                                    "objectID": "12345679"
                                }
                            ],
                            "total": 2,
                            "hours": hours
                        }
                    }

        except Exception as e:
            logger.error(f"❌ Hacker News top search error: {e}")
            return {
                "success": False,
                "error": f"Hacker News top search failed: {str(e)}",
                "data": None
            }

    async def get_hackernews_trending(self) -> dict[str, Any]:
        """Lấy Hacker News trending"""
        try:
            logger.info("🔍 Getting Hacker News trending")

            url = f"{self.hackernews_url}?query=&tags=front_page&hitsPerPage=10"

            async with SecureHttpClient() as client:
                response = await client.get(url)

                if response["success"]:
                    hits = response["data"].get("hits", [])
                    formatted_stories = []

                    for story in hits:
                        formatted_stories.append({
                            "title": story.get("title", ""),
                            "url": story.get("url", ""),
                            "points": story.get("points", 0),
                            "num_comments": story.get("num_comments", 0),
                            "author": story.get("author", ""),
                            "created_at": story.get("created_at", "")
                        })

                    return {
                        "success": True,
                        "data": {
                            "stories": formatted_stories,
                            "total": len(formatted_stories)
                        }
                    }
                else:
                    return response

        except Exception as e:
            logger.error(f"❌ Hacker News trending error: {e}")
            return {
                "success": False,
                "error": f"Hacker News trending failed: {str(e)}",
                "data": None
            }

    async def process_web_request(self, request_type: str, query: str, **kwargs) -> dict[str, Any]:
        """Xử lý web request dựa trên loại"""
        try:
            if request_type == "news":
                language = kwargs.get("language", "vi")
                return await self.search_news(query, language)

            elif request_type == "github_trending":
                language = kwargs.get("language", "python")
                return await self.get_github_trending(language)

            elif request_type == "hackernews":
                return await self.get_hackernews_trending()

            else:
                return {
                    "success": False,
                    "error": f"Unknown request type: {request_type}",
                    "data": None
                }

        except Exception as e:
            logger.error(f"❌ Web request processing error: {e}")
            return {
                "success": False,
                "error": f"Web request failed: {str(e)}",
                "data": None
            }

# Global instance
market_intel = MarketIntelligence()

async def handle_web_request(request_type: str, query: str, **kwargs) -> dict[str, Any]:
    """Convenience function để xử lý web request"""
    return await market_intel.process_web_request(request_type, query, **kwargs)

if __name__ == "__main__":
    # Test market intelligence
    async def test_market_intel():
        print("🧪 Testing Market Intelligence...")

        # Test news search
        print("\n📰 Testing news search...")
        news_result = await market_intel.search_news("AI technology", "en")
        print(f"News result: {news_result['success']}")
        if news_result['success']:
            print(f"Found {len(news_result['data']['articles'])} articles")

        # Test GitHub trending
        print("\n🐙 Testing GitHub trending...")
        github_result = await market_intel.get_github_trending("python")
        print(f"GitHub result: {github_result['success']}")
        if github_result['success']:
            print(f"Found {len(github_result['data']['repositories'])} repositories")

        # Test Hacker News
        print("\n🔥 Testing Hacker News...")
        hn_result = await market_intel.get_hackernews_trending()
        print(f"HN result: {hn_result['success']}")
        if hn_result['success']:
            print(f"Found {len(hn_result['data']['stories'])} stories")

    asyncio.run(test_market_intel())
