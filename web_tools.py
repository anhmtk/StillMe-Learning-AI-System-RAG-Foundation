#!/usr/bin/env python3
"""
Web Tools Registry - Controlled Internet Access Tools
Provides pure tools without LLM dependencies for web access
"""
import asyncio
import json
import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from urllib.parse import urljoin, urlparse

from common.http import SecureHttpClient
from content_integrity_filter import ContentIntegrityFilter
from market_intel import MarketIntelligence
from sandbox_controller import SandboxController

# Setup logging
logger = logging.getLogger(__name__)

@dataclass
class WebResult:
    """Standardized web result with attribution"""
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    attribution: Optional[Dict[str, Any]] = None
    cache_hit: bool = False
    latency_ms: float = 0.0

@dataclass
class Attribution:
    """Attribution metadata for web content"""
    source_name: str
    url: str
    retrieved_at: str
    snippet: str
    domain: str

class WebToolsRegistry:
    """Registry of controlled web access tools"""

    def __init__(self):
        self.http_client = SecureHttpClient()
        self.market_intel = MarketIntelligence()
        self.content_filter = ContentIntegrityFilter()
        self.sandbox = SandboxController()

        # Tool registry
        self.tools = {
            'web.search_news': self._search_news,
            'web.github_trending': self._github_trending,
            'web.hackernews_top': self._hackernews_top,
            'web.google_trends': self._google_trends
        }

        logger.info("🔧 Web Tools Registry initialized")

    async def call_tool(self, tool_name: str, **kwargs) -> WebResult:
        """Call a specific web tool"""
        if tool_name not in self.tools:
            return WebResult(
                success=False,
                error=f"Unknown tool: {tool_name}"
            )

        start_time = datetime.now()

        try:
            # Check sandbox permission
            if not self.sandbox.is_sandbox_enabled():
                return WebResult(
                    success=False,
                    error="Sandbox is disabled - web access blocked"
                )

            # Call the tool
            result = await self.tools[tool_name](**kwargs)

            # Calculate latency
            latency_ms = (datetime.now() - start_time).total_seconds() * 1000
            result.latency_ms = latency_ms

            logger.info(f"🔧 Tool {tool_name} completed in {latency_ms:.1f}ms")
            return result

        except Exception as e:
            logger.error(f"❌ Tool {tool_name} failed: {e}")
            return WebResult(
                success=False,
                error=f"Tool execution failed: {str(e)}",
                latency_ms=(datetime.now() - start_time).total_seconds() * 1000
            )

    async def _search_news(self, query: str, window: str = '24h') -> WebResult:
        """Search news with attribution"""
        try:
            # Parse window parameter
            hours = self._parse_time_window(window)

            # Search news
            result = await self.market_intel.search_news(query, "vi")

            if not result["success"]:
                return WebResult(
                    success=False,
                    error=result.get("error", "News search failed")
                )

            # Filter content
            filtered = self.content_filter.filter_json_response(
                result["data"], "news_search"
            )

            if not filtered["success"]:
                return WebResult(
                    success=False,
                    error="Content filtering failed"
                )

            # Create attribution
            attribution = Attribution(
                source_name="News API / GNews",
                url="https://newsapi.org/ or https://gnews.io/",
                retrieved_at=datetime.now().isoformat(),
                snippet=f"News search for '{query}' in last {window}",
                domain="newsapi.org"
            )

            return WebResult(
                success=True,
                data=filtered["content"],
                attribution=attribution.__dict__
            )

        except Exception as e:
            logger.error(f"❌ News search failed: {e}")
            return WebResult(
                success=False,
                error=f"News search failed: {str(e)}"
            )

    async def _github_trending(self, topic: str, since: str = 'daily') -> WebResult:
        """Get GitHub trending repositories"""
        try:
            # Search GitHub trending
            result = await self.market_intel.search_github_trending(topic, since)

            if not result["success"]:
                return WebResult(
                    success=False,
                    error=result.get("error", "GitHub trending search failed")
                )

            # Filter content
            filtered = self.content_filter.filter_json_response(
                result["data"], "github_trending"
            )

            if not filtered["success"]:
                return WebResult(
                    success=False,
                    error="Content filtering failed"
                )

            # Create attribution
            attribution = Attribution(
                source_name="GitHub Trending",
                url="https://github.com/trending",
                retrieved_at=datetime.now().isoformat(),
                snippet=f"GitHub trending repositories for '{topic}' since {since}",
                domain="github.com"
            )

            return WebResult(
                success=True,
                data=filtered["content"],
                attribution=attribution.__dict__
            )

        except Exception as e:
            logger.error(f"❌ GitHub trending failed: {e}")
            return WebResult(
                success=False,
                error=f"GitHub trending failed: {str(e)}"
            )

    async def _hackernews_top(self, hours: int = 12) -> WebResult:
        """Get top Hacker News stories"""
        try:
            # Search Hacker News
            result = await self.market_intel.search_hackernews_top(hours)

            if not result["success"]:
                return WebResult(
                    success=False,
                    error=result.get("error", "Hacker News search failed")
                )

            # Filter content
            filtered = self.content_filter.filter_json_response(
                result["data"], "hackernews"
            )

            if not filtered["success"]:
                return WebResult(
                    success=False,
                    error="Content filtering failed"
                )

            # Create attribution
            attribution = Attribution(
                source_name="Hacker News",
                url="https://hn.algolia.com/",
                retrieved_at=datetime.now().isoformat(),
                snippet=f"Top Hacker News stories from last {hours} hours",
                domain="hn.algolia.com"
            )

            return WebResult(
                success=True,
                data=filtered["content"],
                attribution=attribution.__dict__
            )

        except Exception as e:
            logger.error(f"❌ Hacker News search failed: {e}")
            return WebResult(
                success=False,
                error=f"Hacker News search failed: {str(e)}"
            )

    async def _google_trends(self, terms: List[str], region: str = 'VN', days: int = 7) -> WebResult:
        """Get Google Trends data (mock implementation)"""
        try:
            # Mock Google Trends data (real implementation would require API)
            trends_data = {
                "terms": terms,
                "region": region,
                "days": days,
                "trends": [
                    {
                        "term": term,
                        "score": 100 - (i * 10),  # Mock trending score
                        "change": f"+{i * 5}%" if i > 0 else "0%"
                    }
                    for i, term in enumerate(terms)
                ],
                "retrieved_at": datetime.now().isoformat()
            }

            # Create attribution
            attribution = Attribution(
                source_name="Google Trends",
                url="https://trends.google.com/",
                retrieved_at=datetime.now().isoformat(),
                snippet=f"Google Trends for {', '.join(terms)} in {region} over {days} days",
                domain="trends.google.com"
            )

            return WebResult(
                success=True,
                data=trends_data,
                attribution=attribution.__dict__
            )

        except Exception as e:
            logger.error(f"❌ Google Trends failed: {e}")
            return WebResult(
                success=False,
                error=f"Google Trends failed: {str(e)}"
            )

    def _parse_time_window(self, window: str) -> int:
        """Parse time window string to hours"""
        window = window.lower()
        if window.endswith('h'):
            return int(window[:-1])
        elif window.endswith('d'):
            return int(window[:-1]) * 24
        elif window.endswith('w'):
            return int(window[:-1]) * 24 * 7
        else:
            return 24  # Default to 24 hours

    def get_available_tools(self) -> List[str]:
        """Get list of available tools"""
        return list(self.tools.keys())

    def get_tool_info(self, tool_name: str) -> Dict[str, Any]:
        """Get information about a specific tool"""
        if tool_name not in self.tools:
            return {"error": "Tool not found"}

        # Tool metadata
        tool_info = {
            "name": tool_name,
            "description": self._get_tool_description(tool_name),
            "parameters": self._get_tool_parameters(tool_name),
            "estimated_cost": self._estimate_tool_cost(tool_name)
        }

        return tool_info

    def _get_tool_description(self, tool_name: str) -> str:
        """Get tool description"""
        descriptions = {
            'web.search_news': 'Search for news articles with time window filtering',
            'web.github_trending': 'Get trending GitHub repositories by topic and time',
            'web.hackernews_top': 'Get top stories from Hacker News',
            'web.google_trends': 'Get Google Trends data for specified terms'
        }
        return descriptions.get(tool_name, "Unknown tool")

    def _get_tool_parameters(self, tool_name: str) -> Dict[str, Any]:
        """Get tool parameters schema"""
        schemas = {
            'web.search_news': {
                "query": {"type": "string", "required": True, "description": "Search query"},
                "window": {"type": "string", "required": False, "default": "24h", "description": "Time window (e.g., 24h, 7d)"}
            },
            'web.github_trending': {
                "topic": {"type": "string", "required": True, "description": "Topic to search for"},
                "since": {"type": "string", "required": False, "default": "daily", "description": "Time period (daily, weekly, monthly)"}
            },
            'web.hackernews_top': {
                "hours": {"type": "integer", "required": False, "default": 12, "description": "Number of hours to look back"}
            },
            'web.google_trends': {
                "terms": {"type": "array", "required": True, "description": "List of terms to search"},
                "region": {"type": "string", "required": False, "default": "VN", "description": "Region code"},
                "days": {"type": "integer", "required": False, "default": 7, "description": "Number of days"}
            }
        }
        return schemas.get(tool_name, {})

    def _estimate_tool_cost(self, tool_name: str) -> Dict[str, Any]:
        """Estimate tool execution cost"""
        costs = {
            'web.search_news': {"requests": 1, "complexity": "low", "estimated_ms": 2000},
            'web.github_trending': {"requests": 1, "complexity": "medium", "estimated_ms": 3000},
            'web.hackernews_top': {"requests": 1, "complexity": "low", "estimated_ms": 1500},
            'web.google_trends': {"requests": 1, "complexity": "high", "estimated_ms": 5000}
        }
        return costs.get(tool_name, {"requests": 1, "complexity": "unknown", "estimated_ms": 1000})

# Global instance
web_tools = WebToolsRegistry()

# Export functions for easy access
async def search_news(query: str, window: str = '24h') -> WebResult:
    """Search news with attribution"""
    return await web_tools.call_tool('web.search_news', query=query, window=window)

async def github_trending(topic: str, since: str = 'daily') -> WebResult:
    """Get GitHub trending repositories"""
    return await web_tools.call_tool('web.github_trending', topic=topic, since=since)

async def hackernews_top(hours: int = 12) -> WebResult:
    """Get top Hacker News stories"""
    return await web_tools.call_tool('web.hackernews_top', hours=hours)

async def google_trends(terms: List[str], region: str = 'VN', days: int = 7) -> WebResult:
    """Get Google Trends data"""
    return await web_tools.call_tool('web.google_trends', terms=terms, region=region, days=days)

if __name__ == "__main__":
    # Test the registry
    async def test_tools():
        print("🔧 Testing Web Tools Registry...")

        # Test news search
        result = await search_news("AI technology", "24h")
        print(f"News search: {result.success}")
        if result.success:
            print(f"Attribution: {result.attribution}")

        # Test GitHub trending
        result = await github_trending("python", "daily")
        print(f"GitHub trending: {result.success}")

        # Test Hacker News
        result = await hackernews_top(12)
        print(f"Hacker News: {result.success}")

        # Test Google Trends
        result = await google_trends(["AI", "machine learning"], "VN", 7)
        print(f"Google Trends: {result.success}")

        print("✅ Web Tools Registry test completed")

    asyncio.run(test_tools())
