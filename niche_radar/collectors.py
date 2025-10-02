#!/usr/bin/env python3
"""
🎯 NicheRadar Collectors - Data Collection Module
================================================

Đồng bộ hóa dữ liệu từ các tool đã có trong StillMe framework.
Mỗi collector trả về records có trường chung: source, url, title, timestamp, metrics{...} + raw.

Author: StillMe Framework Team
Version: 1.5.0
"""

import asyncio
import json
import logging
import time
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Optional

# Import existing StillMe modules
from market_intel import MarketIntelligence
from web_tools import github_trending, google_trends, hackernews_top, search_news

logger = logging.getLogger(__name__)

@dataclass
class NicheRecord:
    """Standardized record format for all collectors"""
    source: str
    url: str
    title: str
    timestamp: datetime
    metrics: dict[str, Any]
    raw: dict[str, Any]
    topic: str
    category: str = "general"
    confidence: float = 0.0

class BaseCollector:
    """Base class for all niche collectors"""

    def __init__(self, name: str):
        self.name = name
        self.logger = logging.getLogger(f"niche_radar.collectors.{name}")

    async def collect(self, **kwargs) -> list[NicheRecord]:
        """Collect data and return standardized records"""
        raise NotImplementedError

    def _create_record(self, source: str, url: str, title: str,
                      metrics: dict[str, Any], raw: dict[str, Any],
                      topic: str, category: str = "general",
                      confidence: float = 0.0) -> NicheRecord:
        """Create standardized NicheRecord"""
        return NicheRecord(
            source=source,
            url=url,
            title=title,
            timestamp=datetime.now(),
            metrics=metrics,
            raw=raw,
            topic=topic,
            category=category,
            confidence=confidence
        )

class GitHubTrendingCollector(BaseCollector):
    """Collect GitHub trending repositories"""

    def __init__(self):
        super().__init__("github_trending")
        self.market_intel = MarketIntelligence()

    async def collect(self, topic: str = "python", since: str = "daily") -> list[NicheRecord]:
        """Collect GitHub trending repositories"""
        try:
            self.logger.info(f"🔍 Collecting GitHub trending for topic: {topic}, since: {since}")

            # Use existing web_tools.github_trending
            result = await github_trending(topic, since)

            if not result.success or not result.data:
                self.logger.warning(f"⚠️ GitHub trending failed for {topic}")
                return []

            records = []
            repositories = result.data.get("repositories", [])

            for repo in repositories:
                # Calculate velocity metrics
                stars = repo.get("stars", 0)
                created_at = repo.get("created_at", "")
                language = repo.get("language", "unknown")

                # Estimate velocity (stars per day since creation)
                velocity = 0.0
                if created_at:
                    try:
                        created_date = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                        days_since_creation = (datetime.now() - created_date.replace(tzinfo=None)).days
                        if days_since_creation > 0:
                            velocity = stars / days_since_creation
                    except:
                        velocity = stars / 30  # Default to 30 days

                metrics = {
                    "stars": stars,
                    "velocity": velocity,
                    "language": language,
                    "created_at": created_at,
                    "description": repo.get("description", ""),
                    "trending_score": min(velocity * 0.1, 1.0)  # Normalize to 0-1
                }

                record = self._create_record(
                    source="GitHub",
                    url=repo.get("url", ""),
                    title=repo.get("name", ""),
                    metrics=metrics,
                    raw=repo,
                    topic=topic,
                    category="development",
                    confidence=0.8 if velocity > 10 else 0.5
                )
                records.append(record)

            self.logger.info(f"✅ Collected {len(records)} GitHub trending records")
            return records

        except Exception as e:
            self.logger.error(f"❌ GitHub trending collection failed: {e}")
            return []

class HackerNewsCollector(BaseCollector):
    """Collect Hacker News top stories"""

    def __init__(self):
        super().__init__("hackernews")

    async def collect(self, hours: int = 12) -> list[NicheRecord]:
        """Collect Hacker News top stories"""
        try:
            self.logger.info(f"🔍 Collecting Hacker News top stories for {hours} hours")

            # Use existing web_tools.hackernews_top
            result = await hackernews_top(hours)

            if not result.success or not result.data:
                self.logger.warning("⚠️ Hacker News collection failed")
                return []

            records = []
            stories = result.data.get("stories", [])

            for story in stories:
                score = story.get("score", 0)
                url = story.get("url", "")
                title = story.get("title", "")

                # Calculate heat metrics
                heat_score = min(score / 100.0, 1.0)  # Normalize to 0-1

                # Extract topic from title (simple keyword matching)
                topic = self._extract_topic_from_title(title)

                metrics = {
                    "score": score,
                    "heat_score": heat_score,
                    "engagement": score * 0.1,  # Estimate comments/engagement
                    "time_factor": 1.0 - (hours / 24.0)  # Decay over time
                }

                record = self._create_record(
                    source="Hacker News",
                    url=url,
                    title=title,
                    metrics=metrics,
                    raw=story,
                    topic=topic,
                    category="tech_news",
                    confidence=0.7 if score > 50 else 0.4
                )
                records.append(record)

            self.logger.info(f"✅ Collected {len(records)} Hacker News records")
            return records

        except Exception as e:
            self.logger.error(f"❌ Hacker News collection failed: {e}")
            return []

    def _extract_topic_from_title(self, title: str) -> str:
        """Extract topic from title using keyword matching"""
        title_lower = title.lower()

        # Tech topics
        if any(word in title_lower for word in ["ai", "artificial intelligence", "machine learning", "ml"]):
            return "ai"
        elif any(word in title_lower for word in ["python", "javascript", "react", "vue", "angular"]):
            return "programming"
        elif any(word in title_lower for word in ["startup", "funding", "venture", "investment"]):
            return "startup"
        elif any(word in title_lower for word in ["crypto", "bitcoin", "blockchain", "defi"]):
            return "crypto"
        elif any(word in title_lower for word in ["saas", "api", "cloud", "aws", "azure"]):
            return "saas"
        else:
            return "general"

class NewsDeltaCollector(BaseCollector):
    """Collect news with delta analysis"""

    def __init__(self):
        super().__init__("news_delta")

    async def collect(self, query: str, window: str = "24h") -> list[NicheRecord]:
        """Collect news with delta analysis"""
        try:
            self.logger.info(f"🔍 Collecting news delta for query: {query}, window: {window}")

            # Use existing web_tools.search_news
            result = await search_news(query, window)

            if not result.success or not result.data:
                self.logger.warning(f"⚠️ News collection failed for {query}")
                return []

            records = []
            # Handle case where result.data might be a string
            if isinstance(result.data, str):
                try:
                    data = json.loads(result.data)
                except:
                    self.logger.warning("⚠️ Failed to parse news data as JSON")
                    return []
            else:
                data = result.data

            articles = data.get("articles", [])

            for article in articles:
                title = article.get("title", "")
                description = article.get("description", "")
                published_at = article.get("publishedAt", "")
                source_name = article.get("source", {}).get("name", "unknown")

                # Calculate news delta metrics
                recency_score = self._calculate_recency_score(published_at)
                relevance_score = self._calculate_relevance_score(title, description, query)

                metrics = {
                    "recency_score": recency_score,
                    "relevance_score": relevance_score,
                    "source_credibility": self._get_source_credibility(source_name),
                    "engagement_estimate": len(description) / 100.0,  # Simple proxy
                    "delta_score": (recency_score + relevance_score) / 2.0
                }

                record = self._create_record(
                    source=source_name,
                    url=article.get("url", ""),
                    title=title,
                    metrics=metrics,
                    raw=article,
                    topic=query,
                    category="news",
                    confidence=0.6
                )
                records.append(record)

            self.logger.info(f"✅ Collected {len(records)} news records")
            return records

        except Exception as e:
            self.logger.error(f"❌ News collection failed: {e}")
            return []

    def _calculate_recency_score(self, published_at: str) -> float:
        """Calculate recency score based on publication time"""
        try:
            if not published_at:
                return 0.0

            pub_time = datetime.fromisoformat(published_at.replace('Z', '+00:00'))
            now = datetime.now(pub_time.tzinfo)
            hours_ago = (now - pub_time).total_seconds() / 3600

            # Exponential decay: 1.0 for 0 hours, 0.5 for 12 hours, 0.1 for 48 hours
            return max(0.0, 1.0 - (hours_ago / 48.0))
        except:
            return 0.5  # Default score

    def _calculate_relevance_score(self, title: str, description: str, query: str) -> float:
        """Calculate relevance score based on keyword matching"""
        text = (title + " " + description).lower()
        query_words = query.lower().split()

        matches = sum(1 for word in query_words if word in text)
        return min(matches / len(query_words), 1.0) if query_words else 0.0

    def _get_source_credibility(self, source_name: str) -> float:
        """Get source credibility score"""
        credible_sources = {
            "TechCrunch": 0.9,
            "Wired": 0.9,
            "Ars Technica": 0.8,
            "The Verge": 0.8,
            "MIT Technology Review": 0.9,
            "IEEE Spectrum": 0.9,
            "Nature": 0.95,
            "Science": 0.95
        }
        return credible_sources.get(source_name, 0.5)

class GoogleTrendsCollector(BaseCollector):
    """Collect Google Trends data"""

    def __init__(self):
        super().__init__("google_trends")

    async def collect(self, terms: list[str], region: str = "VN", days: int = 7) -> list[NicheRecord]:
        """Collect Google Trends data"""
        try:
            self.logger.info(f"🔍 Collecting Google Trends for terms: {terms}, region: {region}, days: {days}")

            # Use existing web_tools.google_trends
            result = await google_trends(terms, region, days)

            if not result.success or not result.data:
                self.logger.warning("⚠️ Google Trends collection failed")
                return []

            records = []
            trends = result.data.get("trends", [])

            for trend in trends:
                term = trend.get("term", "")
                value = trend.get("value", 0)
                trend.get("date", "")

                # Calculate trend momentum
                momentum_score = min(value / 100.0, 1.0)  # Normalize to 0-1

                metrics = {
                    "trend_value": value,
                    "momentum_score": momentum_score,
                    "region": region,
                    "timeframe_days": days,
                    "trend_direction": "up" if value > 50 else "down"
                }

                record = self._create_record(
                    source="Google Trends",
                    url=f"https://trends.google.com/trends/explore?q={term}&geo={region}",
                    title=f"Google Trends: {term}",
                    metrics=metrics,
                    raw=trend,
                    topic=term,
                    category="search_trends",
                    confidence=0.8 if value > 70 else 0.5
                )
                records.append(record)

            self.logger.info(f"✅ Collected {len(records)} Google Trends records")
            return records

        except Exception as e:
            self.logger.error(f"❌ Google Trends collection failed: {e}")
            return []

class RedditEngagementCollector(BaseCollector):
    """Collect Reddit engagement data"""

    def __init__(self):
        super().__init__("reddit_engagement")

    async def collect(self, query: str, window: str = "24h") -> list[NicheRecord]:
        """Collect Reddit engagement data"""
        try:
            self.logger.info(f"🔍 Collecting Reddit engagement for query: {query}, window: {window}")

            # For now, return mock data since Reddit API requires authentication
            # In production, integrate with Reddit API using REDDIT_CLIENT_ID/SECRET

            mock_posts = [
                {
                    "title": f"Discussion about {query}",
                    "url": "https://reddit.com/r/technology/comments/mock1",
                    "score": 150,
                    "comments": 45,
                    "subreddit": "technology",
                    "created_utc": time.time() - 3600  # 1 hour ago
                },
                {
                    "title": f"New developments in {query}",
                    "url": "https://reddit.com/r/programming/comments/mock2",
                    "score": 89,
                    "comments": 23,
                    "subreddit": "programming",
                    "created_utc": time.time() - 7200  # 2 hours ago
                }
            ]

            records = []
            for post in mock_posts:
                score = post.get("score", 0)
                comments = post.get("comments", 0)

                # Calculate engagement metrics
                engagement_score = min((score + comments * 2) / 200.0, 1.0)

                metrics = {
                    "score": score,
                    "comments": comments,
                    "engagement_score": engagement_score,
                    "subreddit": post.get("subreddit", ""),
                    "time_factor": 1.0 - ((time.time() - post.get("created_utc", 0)) / 86400.0)
                }

                record = self._create_record(
                    source="Reddit",
                    url=post.get("url", ""),
                    title=post.get("title", ""),
                    metrics=metrics,
                    raw=post,
                    topic=query,
                    category="social_engagement",
                    confidence=0.6
                )
                records.append(record)

            self.logger.info(f"✅ Collected {len(records)} Reddit engagement records (mock)")
            return records

        except Exception as e:
            self.logger.error(f"❌ Reddit engagement collection failed: {e}")
            return []

# Factory function to get all collectors
def get_all_collectors() -> dict[str, BaseCollector]:
    """Get all available collectors"""
    return {
        "github_trending": GitHubTrendingCollector(),
        "hackernews": HackerNewsCollector(),
        "news_delta": NewsDeltaCollector(),
        "google_trends": GoogleTrendsCollector(),
        "reddit_engagement": RedditEngagementCollector()
    }

async def collect_all_data(topics: Optional[list[str]] = None) -> dict[str, list[NicheRecord]]:
    """Collect data from all sources"""
    if topics is None:
        topics = ["python", "ai", "startup", "saas", "crypto"]

    collectors = get_all_collectors()
    all_data = {}

    # Collect from each source
    for name, collector in collectors.items():
        try:
            if name == "github_trending":
                records = await collector.collect(topic=topics[0], since="daily")
            elif name == "hackernews":
                records = await collector.collect(hours=12)
            elif name == "news_delta":
                records = await collector.collect(query=topics[0], window="24h")
            elif name == "google_trends":
                records = await collector.collect(terms=topics[:3], region="VN", days=7)
            elif name == "reddit_engagement":
                records = await collector.collect(query=topics[0], window="24h")
            else:
                records = []

            all_data[name] = records

        except Exception as e:
            logger.error(f"❌ Failed to collect from {name}: {e}")
            all_data[name] = []

    return all_data

if __name__ == "__main__":
    # Test collectors
    async def test_collectors():
        print("🧪 Testing NicheRadar Collectors...")

        data = await collect_all_data(["python", "ai"])

        for source, records in data.items():
            print(f"\n📊 {source}: {len(records)} records")
            for record in records[:2]:  # Show first 2 records
                print(f"  - {record.title[:50]}... (confidence: {record.confidence:.2f})")

    asyncio.run(test_collectors())
