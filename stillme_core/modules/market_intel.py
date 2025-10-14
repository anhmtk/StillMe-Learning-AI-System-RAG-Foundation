#!/usr/bin/env python3
"""
Market Intelligence Module - StillMe AI Framework
=================================================

Module tổng hợp dữ liệu từ nhiều nguồn API uy tín để phân tích xu hướng thị trường.
Tập trung vào các nguồn dữ liệu tổng hợp thay vì scrape trực tiếp.

Author: StillMe Framework Team
Version: 1.0.0
"""

import asyncio
import json
import logging
import os
import random
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

import aiohttp

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class TrendData:
    """Data structure for trend information"""

    source: str
    title: str
    description: str
    url: str
    score: float
    timestamp: datetime
    category: str
    metadata: dict[str, Any]


@dataclass
class MarketIntelligenceReport:
    """Comprehensive market intelligence report"""

    timestamp: datetime
    summary: str
    trends: list[TrendData]
    sources_used: list[str]
    confidence_score: float
    recommendations: list[str]


class MarketIntelligence:
    """
    Market Intelligence Module

    Tổng hợp dữ liệu từ nhiều nguồn API để phân tích xu hướng thị trường:
    - GitHub Trending (gtrending library)
    - Google Trends (pytrends library)
    - News API (GNews/NewsAPI)
    - Hacker News API
    """

    def __init__(self, cache_duration_hours: int = 2):
        """
        Initialize Market Intelligence Module

        Args:
            cache_duration_hours: Thời gian cache dữ liệu (mặc định 2 giờ)
        """
        self.cache_duration = timedelta(hours=cache_duration_hours)
        self.cache_file = Path("cache/market_intel_cache.json")
        self.cache_file.parent.mkdir(exist_ok=True)

        # API Keys (từ environment variables)
        self.news_api_key = os.getenv("NEWSAPI_KEY")  # Updated to match .env
        self.gnews_api_key = os.getenv("GNEWS_API_KEY")
        self.reddit_client_id = os.getenv("REDDIT_CLIENT_ID")
        self.reddit_client_secret = os.getenv("REDDIT_CLIENT_SECRET")
        self.reddit_user_agent = os.getenv("REDDIT_USER_AGENT", "StillMeAI/1.0")

        # Load from .env file if not in environment
        if not self.news_api_key or not self.gnews_api_key:
            self._load_env_file()

        # Rate limiting và proxy rotation
        self.last_request_time = {}
        self.min_request_interval = 2.0  # 2 seconds between requests
        self.request_count = 0

        # Analytics tracking
        self.analytics = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "source_stats": {
                "github": {"requests": 0, "success": 0, "failures": 0},
                "google_trends": {"requests": 0, "success": 0, "failures": 0},
                "news": {"requests": 0, "success": 0, "failures": 0},
                "reddit": {"requests": 0, "success": 0, "failures": 0},
                "stackoverflow": {"requests": 0, "success": 0, "failures": 0},
            },
            "report_stats": {
                "total_reports": 0,
                "avg_report_length": 0,
                "avg_confidence_score": 0,
                "avg_sources_used": 0,
            },
        }

        # Proxy rotation for Google Trends
        self.proxy_list = [
            None,  # No proxy
            # Thêm proxy servers nếu có
        ]
        self.current_proxy_index = 0

        # User agents for rotation
        self.user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:109.0) Gecko/20100101 Firefox/121.0",
        ]

        # Initialize Prediction Engine
        try:
            from modules.prediction_engine import PredictionEngine

            self.prediction_engine = PredictionEngine()
            logger.info("✅ PredictionEngine integrated")
        except ImportError:
            self.prediction_engine = None
            logger.warning("⚠️ PredictionEngine not available")

        logger.info("✅ MarketIntelligence module initialized")

    def _load_env_file(self):
        """Load API keys from .env file"""
        try:
            env_file = Path(".env")
            if env_file.exists():
                with open(env_file, encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith("#") and "=" in line:
                            key, value = line.split("=", 1)
                            if key == "NEWSAPI_KEY" and not self.news_api_key:
                                self.news_api_key = value
                            elif key == "GNEWS_API_KEY" and not self.gnews_api_key:
                                self.gnews_api_key = value

                logger.info("✅ Loaded API keys from .env file")
                logger.info(f"   NEWSAPI_KEY: {'✅' if self.news_api_key else '❌'}")
                logger.info(f"   GNEWS_API_KEY: {'✅' if self.gnews_api_key else '❌'}")
            else:
                logger.warning("⚠️ .env file not found")
        except Exception as e:
            logger.error(f"❌ Error loading .env file: {e}")

    def _track_request(self, source: str, success: bool):
        """Track API request statistics"""
        self.analytics["total_requests"] += 1
        if success:
            self.analytics["successful_requests"] += 1
            self.analytics["source_stats"][source]["success"] += 1
        else:
            self.analytics["failed_requests"] += 1
            self.analytics["source_stats"][source]["failures"] += 1

        self.analytics["source_stats"][source]["requests"] += 1

    def _track_report(
        self, report_length: int, confidence_score: float, sources_count: int
    ):
        """Track report statistics"""
        self.analytics["report_stats"]["total_reports"] += 1

        # Update running averages
        total_reports = self.analytics["report_stats"]["total_reports"]
        current_avg_length = self.analytics["report_stats"]["avg_report_length"]
        current_avg_confidence = self.analytics["report_stats"]["avg_confidence_score"]
        current_avg_sources = self.analytics["report_stats"]["avg_sources_used"]

        self.analytics["report_stats"]["avg_report_length"] = (
            current_avg_length * (total_reports - 1) + report_length
        ) / total_reports
        self.analytics["report_stats"]["avg_confidence_score"] = (
            current_avg_confidence * (total_reports - 1) + confidence_score
        ) / total_reports
        self.analytics["report_stats"]["avg_sources_used"] = (
            current_avg_sources * (total_reports - 1) + sources_count
        ) / total_reports

    def get_analytics_summary(self) -> dict[str, Any]:
        """Get analytics summary"""
        total_requests = self.analytics["total_requests"]
        success_rate = (
            (self.analytics["successful_requests"] / total_requests * 100)
            if total_requests > 0
            else 0
        )

        return {
            "total_requests": total_requests,
            "success_rate": f"{success_rate:.1f}%",
            "source_performance": {
                source: {
                    "requests": stats["requests"],
                    "success_rate": (
                        f"{(stats['success'] / stats['requests'] * 100):.1f}%"
                        if stats["requests"] > 0
                        else "0%"
                    ),
                }
                for source, stats in self.analytics["source_stats"].items()
            },
            "report_metrics": self.analytics["report_stats"],
        }

    def _check_rate_limit(self, source: str) -> bool:
        """Check if enough time has passed since last request to this source"""
        now = time.time()
        if source in self.last_request_time:
            if now - self.last_request_time[source] < self.min_request_interval:
                return False
        self.last_request_time[source] = now
        return True

    def _get_next_proxy(self) -> dict[str, str] | None:
        """Get next proxy in rotation"""
        if not self.proxy_list:
            return None

        proxy = self.proxy_list[self.current_proxy_index]
        self.current_proxy_index = (self.current_proxy_index + 1) % len(self.proxy_list)
        return proxy

    def _get_random_user_agent(self) -> str:
        """Get random user agent for request"""
        return random.choice(self.user_agents)

    def _wait_for_rate_limit(self, source: str) -> None:
        """Wait for rate limit to reset"""
        if source in self.last_request_time:
            time_since_last = time.time() - self.last_request_time[source]
            if time_since_last < self.min_request_interval:
                wait_time = self.min_request_interval - time_since_last
                logger.info(f"⏳ Waiting {wait_time:.1f}s for rate limit reset...")
                time.sleep(wait_time)

    def _load_cache(self) -> dict[str, Any]:
        """Load cached data if still valid"""
        try:
            if self.cache_file.exists():
                with open(self.cache_file, encoding="utf-8") as f:
                    cache_data = json.load(f)

                cache_time = datetime.fromisoformat(cache_data.get("timestamp", ""))
                if datetime.now() - cache_time < self.cache_duration:
                    logger.info("📦 Using cached market intelligence data")
                    return cache_data
        except Exception as e:
            logger.warning(f"⚠️ Failed to load cache: {e}")

        return {}

    def _save_cache(self, data: dict[str, Any]) -> None:
        """Save data to cache"""
        try:
            # Convert datetime objects to ISO format strings
            serializable_data = {}
            for key, value in data.items():
                if key == "trends":
                    serializable_data[key] = []
                    for trend in value:
                        if hasattr(trend, "__dict__"):
                            trend_dict = asdict(trend)
                        else:
                            trend_dict = trend
                        if "timestamp" in trend_dict and hasattr(
                            trend_dict["timestamp"], "isoformat"
                        ):
                            trend_dict["timestamp"] = trend_dict[
                                "timestamp"
                            ].isoformat()
                        serializable_data[key].append(trend_dict)
                else:
                    serializable_data[key] = value

            cache_data = {
                "timestamp": datetime.now().isoformat(),
                "data": serializable_data,
            }
            with open(self.cache_file, "w", encoding="utf-8") as f:
                json.dump(cache_data, f, indent=2, ensure_ascii=False)
            logger.info("💾 Market intelligence data cached")
        except Exception as e:
            logger.warning(f"⚠️ Failed to save cache: {e}")

    async def get_github_trending(
        self, language: str = "python", since: str = "daily"
    ) -> list[TrendData]:
        """
        Lấy danh sách repositories trending từ GitHub

        Args:
            language: Ngôn ngữ lập trình (python, javascript, etc.)
            since: Khoảng thời gian (daily, weekly, monthly)

        Returns:
            List[TrendData]: Danh sách repositories trending
        """
        if not self._check_rate_limit("github"):
            await asyncio.sleep(self.min_request_interval)

        try:
            # Sử dụng gtrending library
            try:
                from gtrending import fetch_repos  # type: ignore
            except ImportError:
                logger.warning("gtrending not available, using fallback")
                return []

            logger.info(f"🔍 Fetching GitHub trending repos for {language}")
            trending_repos = fetch_repos(language=language, since=since)

            trends = []
            for repo in trending_repos[:10]:  # Top 10
                trend = TrendData(
                    source="GitHub",
                    title=repo.get("name", "Unknown"),
                    description=repo.get("description", "No description"),
                    url=repo.get("url", ""),
                    score=repo.get("stars", 0),
                    timestamp=datetime.now(),
                    category="Programming",
                    metadata={
                        "author": repo.get("author", ""),
                        "language": repo.get("language", language),
                        "stars": repo.get("stars", 0),
                        "forks": repo.get("forks", 0),
                    },
                )
                trends.append(trend)

            logger.info(f"✅ Found {len(trends)} trending GitHub repos")
            self._track_request("github", True)
            return trends

        except ImportError:
            logger.warning(
                "⚠️ gtrending library not installed. Install with: pip install gtrending"
            )
            return []
        except Exception as e:
            logger.error(f"❌ Error fetching GitHub trending: {e}")
            self._track_request("github", False)
            return []

    async def get_google_trends(
        self, keywords: list[str], timeframe: str = "today 3-m"
    ) -> list[TrendData]:
        """
        Lấy dữ liệu xu hướng từ Google Trends với proxy rotation và rate limiting

        Args:
            keywords: Danh sách từ khóa cần tìm kiếm
            timeframe: Khoảng thời gian (today 3-m, today 1-m, etc.)

        Returns:
            List[TrendData]: Danh sách xu hướng từ Google Trends
        """
        # Wait for rate limit reset
        self._wait_for_rate_limit("google_trends")

        try:
            # Sử dụng pytrends library
            try:
                from pytrends.request import TrendReq  # type: ignore
            except ImportError:
                logger.warning("pytrends not available, using fallback")
                return []

            logger.info(f"🔍 Fetching Google Trends for keywords: {keywords}")

            # Get proxy and user agent for this request
            proxy = self._get_next_proxy()
            user_agent = self._get_random_user_agent()

            # Initialize pytrends with proxy rotation
            if proxy:
                logger.info(f"🔄 Using proxy: {proxy}")
                pytrends = TrendReq(hl="en-US", tz=360, proxies=proxy)
            else:
                pytrends = TrendReq(hl="en-US", tz=360)

            # Set custom user agent
            pytrends.headers["User-Agent"] = user_agent

            trends = []
            for i, keyword in enumerate(keywords[:5]):  # Limit to 5 keywords
                try:
                    # Add delay between requests to avoid rate limiting
                    if i > 0:
                        delay = random.uniform(1.0, 3.0)  # Random delay 1-3 seconds
                        logger.info(f"⏳ Waiting {delay:.1f}s before next request...")
                        await asyncio.sleep(delay)

                    # Build payload
                    pytrends.build_payload(
                        [keyword], cat=0, timeframe=timeframe, geo="", gprop=""
                    )

                    # Get interest over time
                    interest_df = pytrends.interest_over_time()

                    if not interest_df.empty:
                        # Calculate average interest
                        avg_interest = interest_df[keyword].mean()

                        # Get related queries
                        related_queries = pytrends.related_queries()

                        trend = TrendData(
                            source="Google Trends",
                            title=f"Trend: {keyword}",
                            description=f"Average interest: {avg_interest:.1f}",
                            url=f"https://trends.google.com/trends/explore?q={keyword}",
                            score=float(avg_interest),
                            timestamp=datetime.now(),
                            category="Search Trends",
                            metadata={
                                "keyword": keyword,
                                "timeframe": timeframe,
                                "avg_interest": float(avg_interest),
                                "related_queries": (
                                    related_queries.get(keyword, {}).get("top", [])[:3]
                                    if related_queries
                                    else []
                                ),
                            },
                        )
                        trends.append(trend)
                        logger.info(f"✅ Successfully fetched trend for: {keyword}")

                except Exception as e:
                    error_msg = str(e)
                    if "429" in error_msg or "rate limit" in error_msg.lower():
                        logger.warning(
                            f"⚠️ Rate limit hit for {keyword}, trying next proxy..."
                        )
                        # Try with next proxy
                        proxy = self._get_next_proxy()
                        if proxy:
                            pytrends = TrendReq(hl="en-US", tz=360, proxies=proxy)
                            pytrends.headers["User-Agent"] = (
                                self._get_random_user_agent()
                            )
                        continue
                    else:
                        logger.warning(f"⚠️ Error fetching trend for {keyword}: {e}")
                        continue

            logger.info(f"✅ Found {len(trends)} Google Trends")
            return trends

        except ImportError:
            logger.warning(
                "⚠️ pytrends library not installed. Install with: pip install pytrends"
            )
            return []
        except Exception as e:
            logger.error(f"❌ Error fetching Google Trends: {e}")
            return []

    async def get_tech_news(
        self, keywords: list[str], max_articles: int = 10
    ) -> list[TrendData]:
        """
        Lấy tin tức công nghệ từ News API

        Args:
            keywords: Danh sách từ khóa tìm kiếm
            max_articles: Số lượng bài viết tối đa

        Returns:
            List[TrendData]: Danh sách tin tức công nghệ
        """
        if not self._check_rate_limit("news"):
            await asyncio.sleep(self.min_request_interval)

        try:
            # Thử GNews API trước
            if self.gnews_api_key:
                return await self._get_gnews(keywords, max_articles)

            # Fallback to NewsAPI
            if self.news_api_key:
                return await self._get_newsapi(keywords, max_articles)

            # Fallback to Hacker News
            return await self._get_hacker_news(max_articles)

        except Exception as e:
            logger.error(f"❌ Error fetching tech news: {e}")
            return []

    async def _get_gnews(
        self, keywords: list[str], max_articles: int
    ) -> list[TrendData]:
        """Get news from GNews API"""
        try:
            try:
                from gnews import GNews  # type: ignore
            except ImportError:
                logger.warning("gnews not available, using fallback")
                return []

            logger.info("🔍 Fetching news from GNews API")
            # GNews doesn't use api_key parameter in constructor
            gnews = GNews(language="en", country="US")

            trends = []
            for keyword in keywords[:3]:  # Limit keywords
                try:
                    articles = gnews.get_news(keyword)[: max_articles // len(keywords)]

                    for article in articles:
                        trend = TrendData(
                            source="GNews",
                            title=article.get("title", "No title"),
                            description=article.get("description", "No description"),
                            url=article.get("url", ""),
                            score=1.0,  # Default score
                            timestamp=datetime.now(),
                            category="Tech News",
                            metadata={
                                "published_date": article.get("published date", ""),
                                "publisher": article.get("publisher", {}).get(
                                    "title", ""
                                ),
                                "keyword": keyword,
                            },
                        )
                        trends.append(trend)

                except Exception as e:
                    logger.warning(f"⚠️ Error fetching GNews for {keyword}: {e}")
                    continue

            logger.info(f"✅ Found {len(trends)} news articles from GNews")
            return trends

        except ImportError:
            logger.warning(
                "⚠️ gnews library not installed. Install with: pip install gnews"
            )
            return []

    async def _get_newsapi(
        self, keywords: list[str], max_articles: int
    ) -> list[TrendData]:
        """Get news from NewsAPI"""
        try:
            logger.info("🔍 Fetching news from NewsAPI")

            trends = []
            for keyword in keywords[:3]:
                try:
                    url = "https://newsapi.org/v2/everything"
                    params = {
                        "q": keyword,
                        "apiKey": self.news_api_key,
                        "language": "en",
                        "sortBy": "publishedAt",
                        "pageSize": max_articles // len(keywords),
                    }

                    async with aiohttp.ClientSession() as session:
                        async with session.get(url, params=params) as response:
                            if response.status == 200:
                                data = await response.json()

                                for article in data.get("articles", []):
                                    trend = TrendData(
                                        source="NewsAPI",
                                        title=article.get("title", "No title"),
                                        description=article.get(
                                            "description", "No description"
                                        ),
                                        url=article.get("url", ""),
                                        score=1.0,
                                        timestamp=datetime.now(),
                                        category="Tech News",
                                        metadata={
                                            "published_at": article.get(
                                                "publishedAt", ""
                                            ),
                                            "source": article.get("source", {}).get(
                                                "name", ""
                                            ),
                                            "keyword": keyword,
                                        },
                                    )
                                    trends.append(trend)

                except Exception as e:
                    logger.warning(f"⚠️ Error fetching NewsAPI for {keyword}: {e}")
                    continue

            logger.info(f"✅ Found {len(trends)} news articles from NewsAPI")
            return trends

        except Exception as e:
            logger.error(f"❌ Error with NewsAPI: {e}")
            return []

    async def _get_hacker_news(self, max_articles: int) -> list[TrendData]:
        """Get top stories from Hacker News API (no API key required)"""
        try:
            logger.info("🔍 Fetching top stories from Hacker News")

            async with aiohttp.ClientSession() as session:
                # Get top story IDs
                async with session.get(
                    "https://hacker-news.firebaseio.com/v0/topstories.json"
                ) as response:
                    if response.status == 200:
                        story_ids = await response.json()

                        trends = []
                        for story_id in story_ids[:max_articles]:
                            try:
                                # Get story details
                                async with session.get(
                                    f"https://hacker-news.firebaseio.com/v0/item/{story_id}.json"
                                ) as story_response:
                                    if story_response.status == 200:
                                        story = await story_response.json()

                                        if story and story.get("type") == "story":
                                            trend = TrendData(
                                                source="Hacker News",
                                                title=story.get("title", "No title"),
                                                description=f"Score: {story.get('score', 0)}",
                                                url=story.get(
                                                    "url",
                                                    f"https://news.ycombinator.com/item?id={story_id}",
                                                ),
                                                score=float(story.get("score", 0)),
                                                timestamp=datetime.now(),
                                                category="Tech News",
                                                metadata={
                                                    "by": story.get("by", ""),
                                                    "time": story.get("time", 0),
                                                    "descendants": story.get(
                                                        "descendants", 0
                                                    ),
                                                },
                                            )
                                            trends.append(trend)

                            except Exception as e:
                                logger.warning(
                                    f"⚠️ Error fetching HN story {story_id}: {e}"
                                )
                                continue

                        logger.info(f"✅ Found {len(trends)} stories from Hacker News")
                        return trends

            return []

        except Exception as e:
            logger.error(f"❌ Error fetching Hacker News: {e}")
            return []

    async def get_reddit_trends(
        self, subreddits: list[str] | None = None, max_posts: int = 10
    ) -> list[TrendData]:
        """
        Lấy trending posts từ Reddit

        Args:
            subreddits: Danh sách subreddits (mặc định: r/programming, r/technology, r/startups)
            max_posts: Số lượng posts tối đa

        Returns:
            List[TrendData]: Danh sách trending posts từ Reddit
        """
        if not self._check_rate_limit("reddit"):
            await asyncio.sleep(self.min_request_interval)

        if subreddits is None:
            subreddits = [
                "programming",
                "technology",
                "startups",
                "MachineLearning",
                "Python",
            ]

        try:
            logger.info(f"🔍 Fetching Reddit trends from subreddits: {subreddits}")

            trends = []
            for subreddit in subreddits[:3]:  # Limit to 3 subreddits
                try:
                    # Use Reddit API without authentication for public data
                    url = f"https://www.reddit.com/r/{subreddit}/hot.json"
                    headers = {"User-Agent": self.reddit_user_agent}

                    async with aiohttp.ClientSession() as session:
                        async with session.get(url, headers=headers) as response:
                            if response.status == 200:
                                data = await response.json()
                                posts = data.get("data", {}).get("children", [])

                                for post in posts[: max_posts // len(subreddits)]:
                                    post_data = post.get("data", {})

                                    # Calculate score based on upvotes and comments
                                    score = post_data.get("score", 0)
                                    num_comments = post_data.get("num_comments", 0)
                                    combined_score = score + (num_comments * 0.1)

                                    trend = TrendData(
                                        source="Reddit",
                                        title=post_data.get("title", "No title"),
                                        description=f"r/{subreddit} - {num_comments} comments",
                                        url=f"https://reddit.com{post_data.get('permalink', '')}",
                                        score=float(combined_score),
                                        timestamp=datetime.now(),
                                        category="Reddit Trends",
                                        metadata={
                                            "subreddit": subreddit,
                                            "upvotes": score,
                                            "comments": num_comments,
                                            "author": post_data.get(
                                                "author", "Unknown"
                                            ),
                                            "created_utc": post_data.get(
                                                "created_utc", 0
                                            ),
                                        },
                                    )
                                    trends.append(trend)

                            else:
                                logger.warning(
                                    f"⚠️ Reddit API error for r/{subreddit}: {response.status}"
                                )

                except Exception as e:
                    logger.warning(
                        f"⚠️ Error fetching Reddit data for r/{subreddit}: {e}"
                    )
                    continue

            logger.info(f"✅ Found {len(trends)} Reddit trends")
            return trends

        except Exception as e:
            logger.error(f"❌ Error fetching Reddit trends: {e}")
            return []

    async def get_stackoverflow_trends(
        self, tags: list[str] | None = None, max_questions: int = 10
    ) -> list[TrendData]:
        """
        Lấy trending questions từ Stack Overflow

        Args:
            tags: Danh sách tags (mặc định: python, javascript, ai, machine-learning)
            max_questions: Số lượng questions tối đa

        Returns:
            List[TrendData]: Danh sách trending questions từ Stack Overflow
        """
        if not self._check_rate_limit("stackoverflow"):
            await asyncio.sleep(self.min_request_interval)

        if tags is None:
            tags = ["python", "javascript", "ai", "machine-learning", "react", "vue.js"]

        try:
            logger.info(f"🔍 Fetching Stack Overflow trends for tags: {tags}")

            trends = []
            for tag in tags[:3]:  # Limit to 3 tags
                try:
                    # Stack Exchange API
                    url = "https://api.stackexchange.com/2.3/questions"
                    params = {
                        "order": "desc",
                        "sort": "votes",
                        "tagged": tag,
                        "site": "stackoverflow",
                        "pagesize": max_questions // len(tags),
                        "filter": "withbody",
                    }

                    async with aiohttp.ClientSession() as session:
                        async with session.get(url, params=params) as response:
                            if response.status == 200:
                                data = await response.json()
                                questions = data.get("items", [])

                                for question in questions:
                                    # Calculate score based on votes, answers, and views
                                    score = question.get("score", 0)
                                    answer_count = question.get("answer_count", 0)
                                    view_count = question.get("view_count", 0)
                                    combined_score = (
                                        score
                                        + (answer_count * 2)
                                        + (view_count * 0.001)
                                    )

                                    trend = TrendData(
                                        source="Stack Overflow",
                                        title=question.get("title", "No title"),
                                        description=f"Tag: {tag} - {answer_count} answers, {view_count} views",
                                        url=question.get("link", ""),
                                        score=float(combined_score),
                                        timestamp=datetime.now(),
                                        category="Stack Overflow Trends",
                                        metadata={
                                            "tag": tag,
                                            "votes": score,
                                            "answers": answer_count,
                                            "views": view_count,
                                            "is_answered": question.get(
                                                "is_answered", False
                                            ),
                                            "question_id": question.get(
                                                "question_id", 0
                                            ),
                                            "tags": question.get("tags", []),
                                        },
                                    )
                                    trends.append(trend)

                            else:
                                logger.warning(
                                    f"⚠️ Stack Overflow API error for tag {tag}: {response.status}"
                                )

                except Exception as e:
                    logger.warning(
                        f"⚠️ Error fetching Stack Overflow data for tag {tag}: {e}"
                    )
                    continue

            logger.info(f"✅ Found {len(trends)} Stack Overflow trends")
            return trends

        except Exception as e:
            logger.error(f"❌ Error fetching Stack Overflow trends: {e}")
            return []

    async def consolidate_trends(
        self, keywords: list[str] | None = None
    ) -> MarketIntelligenceReport:
        """
        Tổng hợp dữ liệu từ tất cả các nguồn và tạo báo cáo xu hướng

        Args:
            keywords: Danh sách từ khóa tìm kiếm (mặc định: ['AI', 'Python', 'JavaScript', 'Machine Learning'])

        Returns:
            MarketIntelligenceReport: Báo cáo tổng hợp xu hướng thị trường
        """
        if keywords is None:
            keywords = [
                "AI",
                "Python",
                "JavaScript",
                "Machine Learning",
                "React",
                "Vue.js",
            ]

        logger.info("🔍 Starting comprehensive market intelligence analysis")

        # Check cache first
        cached_data = self._load_cache()
        if cached_data:
            return self._create_report_from_cache(cached_data)

        # Collect data from all sources
        all_trends = []
        sources_used = []

        try:
            # GitHub Trending
            github_trends = await self.get_github_trending()
            all_trends.extend(github_trends)
            if github_trends:
                sources_used.append("GitHub")

            # Google Trends
            google_trends = await self.get_google_trends(keywords)
            all_trends.extend(google_trends)
            if google_trends:
                sources_used.append("Google Trends")

            # Tech News
            news_trends = await self.get_tech_news(keywords)
            all_trends.extend(news_trends)
            if news_trends:
                sources_used.append("Tech News")

            # Reddit Trends
            reddit_trends = await self.get_reddit_trends()
            all_trends.extend(reddit_trends)
            if reddit_trends:
                sources_used.append("Reddit")

            # Stack Overflow Trends
            stackoverflow_trends = await self.get_stackoverflow_trends()
            all_trends.extend(stackoverflow_trends)
            if stackoverflow_trends:
                sources_used.append("Stack Overflow")

            # Create comprehensive report
            report = self._create_intelligence_report(
                all_trends, sources_used, keywords
            )

            # Cache the results
            self._save_cache(
                {
                    "trends": [asdict(trend) for trend in all_trends],
                    "sources_used": sources_used,
                    "keywords": keywords,
                }
            )

            logger.info(
                f"✅ Market intelligence analysis completed. Found {len(all_trends)} trends from {len(sources_used)} sources"
            )

            # Track report analytics
            self._track_report(
                len(str(report)), report.confidence_score, len(sources_used)
            )

            return report

        except Exception as e:
            logger.error(f"❌ Error in consolidate_trends: {e}")
            return self._create_error_report(str(e))

    def _create_report_from_cache(
        self, cached_data: dict[str, Any]
    ) -> MarketIntelligenceReport:
        """Create report from cached data"""
        trends_data = cached_data.get("data", {}).get("trends", [])
        sources_used = cached_data.get("data", {}).get("sources_used", [])
        keywords = cached_data.get("data", {}).get("keywords", [])

        trends = []
        for trend_dict in trends_data:
            trend_dict["timestamp"] = datetime.fromisoformat(trend_dict["timestamp"])
            trends.append(TrendData(**trend_dict))

        return self._create_intelligence_report(trends, sources_used, keywords)

    def _create_intelligence_report(
        self, trends: list[TrendData], sources_used: list[str], keywords: list[str]
    ) -> MarketIntelligenceReport:
        """Create comprehensive intelligence report"""

        # Analyze trends
        top_trends = sorted(trends, key=lambda x: x.score, reverse=True)[:10]

        # Generate summary
        summary = self._generate_summary(top_trends, sources_used, keywords)

        # Generate recommendations
        recommendations = self._generate_recommendations(top_trends)

        # Calculate confidence score
        confidence_score = min(
            len(sources_used) / 3.0, 1.0
        )  # Max confidence with 3+ sources

        return MarketIntelligenceReport(
            timestamp=datetime.now(),
            summary=summary,
            trends=top_trends,
            sources_used=sources_used,
            confidence_score=confidence_score,
            recommendations=recommendations,
        )

    def _generate_summary(
        self, trends: list[TrendData], sources_used: list[str], keywords: list[str]
    ) -> str:
        """Generate summary of market intelligence"""
        if not trends:
            return "No significant trends found in the current market analysis."

        summary_parts = [
            f"Market Intelligence Report - {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            f"Data sources: {', '.join(sources_used)}",
            f"Keywords analyzed: {', '.join(keywords)}",
            "",
            "Top Trends:",
        ]

        for i, trend in enumerate(trends[:5], 1):
            summary_parts.append(
                f"{i}. {trend.title} ({trend.source}) - Score: {trend.score:.1f}"
            )
            if trend.description:
                summary_parts.append(f"   {trend.description}")

        return "\n".join(summary_parts)

    def _generate_recommendations(self, trends: list[TrendData]) -> list[str]:
        """Generate actionable recommendations based on trends"""
        recommendations = []

        # Analyze programming languages
        languages = [t for t in trends if t.category == "Programming"]
        if languages:
            top_lang = max(languages, key=lambda x: x.score)
            recommendations.append(
                f"Consider focusing on {top_lang.title} - trending with score {top_lang.score:.1f}"
            )

        # Analyze search trends
        search_trends = [t for t in trends if t.category == "Search Trends"]
        if search_trends:
            recommendations.append(
                "Monitor search trends for emerging technologies and user interests"
            )

        # Analyze news trends
        news_trends = [t for t in trends if t.category == "Tech News"]
        if news_trends:
            recommendations.append(
                "Stay updated with latest tech news and industry developments"
            )

        return recommendations

    def _create_error_report(self, error_message: str) -> MarketIntelligenceReport:
        """Create error report when analysis fails"""
        return MarketIntelligenceReport(
            timestamp=datetime.now(),
            summary=f"Market intelligence analysis failed: {error_message}",
            trends=[],
            sources_used=[],
            confidence_score=0.0,
            recommendations=["Please check your internet connection and API keys"],
        )

    async def get_predictive_analysis(
        self, keywords: list[str] | None = None
    ) -> dict[str, Any]:
        """
        Lấy phân tích dự báo xu hướng với khuyến nghị kinh doanh

        Args:
            keywords: Danh sách từ khóa cần phân tích

        Returns:
            Dict[str, Any]: Báo cáo dự báo với khuyến nghị
        """
        if not self.prediction_engine:
            return {"error": "Prediction Engine not available"}

        # Get market data
        market_report = await self.consolidate_trends(keywords)

        # Convert to format for prediction engine
        market_data = []
        for trend in market_report.trends:
            market_data.append(
                {
                    "title": trend.title,
                    "source": trend.source,
                    "score": trend.score,
                    "metadata": trend.metadata,
                    "category": trend.category,
                }
            )

        # Generate predictions
        predictions = self.prediction_engine.analyze_trends(market_data)

        # Generate business recommendations
        recommendations = self.prediction_engine.generate_business_recommendations(
            predictions
        )

        return {
            "market_report": {
                "summary": market_report.summary,
                "confidence_score": market_report.confidence_score,
                "sources_used": market_report.sources_used,
                "timestamp": market_report.timestamp.isoformat(),
            },
            "predictions": [
                {
                    "name": p.name,
                    "category": p.category,
                    "potential_score": p.potential_score,
                    "confidence_score": p.confidence_score,
                    "direction": p.direction.value,
                    "time_horizon": p.time_horizon,
                    "reasoning": p.reasoning,
                    "signal_count": len(p.signals),
                }
                for p in predictions[:5]  # Top 5 predictions
            ],
            "recommendations": [
                {
                    "type": r.recommendation_type,
                    "priority": r.priority,
                    "description": r.description,
                    "expected_impact": r.expected_impact,
                    "timeline": r.timeline,
                    "confidence": r.confidence,
                }
                for r in recommendations[:5]  # Top 5 recommendations
            ],
            "analysis_metadata": {
                "total_predictions": len(predictions),
                "total_recommendations": len(recommendations),
                "high_confidence_predictions": len(
                    [p for p in predictions if p.confidence_score > 0.8]
                ),
                "analysis_timestamp": datetime.now().isoformat(),
            },
        }


# Convenience functions for easy integration
async def get_market_intelligence(
    keywords: list[str] | None = None,
) -> MarketIntelligenceReport:
    """
    Convenience function to get market intelligence report

    Args:
        keywords: List of keywords to analyze

    Returns:
        MarketIntelligenceReport: Comprehensive market intelligence report
    """
    mi = MarketIntelligence()
    return await mi.consolidate_trends(keywords)


def get_market_intelligence_sync(
    keywords: list[str] | None = None,
) -> MarketIntelligenceReport:
    """
    Synchronous version of get_market_intelligence

    Args:
        keywords: List of keywords to analyze

    Returns:
        MarketIntelligenceReport: Comprehensive market intelligence report
    """
    return asyncio.run(get_market_intelligence(keywords))


if __name__ == "__main__":
    # Test the module
    async def test_market_intelligence():
        print("🧪 Testing Market Intelligence Module")
        print("=" * 50)

        mi = MarketIntelligence()

        # Test individual functions
        print("\n1. Testing GitHub Trending...")
        github_trends = await mi.get_github_trending()
        print(f"   Found {len(github_trends)} trending repos")

        print("\n2. Testing Google Trends...")
        google_trends = await mi.get_google_trends(["Python", "AI"])
        print(f"   Found {len(google_trends)} trends")

        print("\n3. Testing Tech News...")
        news_trends = await mi.get_tech_news(["AI", "Python"])
        print(f"   Found {len(news_trends)} news articles")

        print("\n4. Testing Consolidated Report...")
        report = await mi.consolidate_trends(["AI", "Python", "JavaScript"])
        print(f"   Report generated with {len(report.trends)} trends")
        print(f"   Sources used: {report.sources_used}")
        print(f"   Confidence score: {report.confidence_score:.2f}")

        print("\n📊 Summary:")
        print(report.summary)

        print("\n💡 Recommendations:")
        for rec in report.recommendations:
            print(f"   - {rec}")

    asyncio.run(test_market_intelligence())