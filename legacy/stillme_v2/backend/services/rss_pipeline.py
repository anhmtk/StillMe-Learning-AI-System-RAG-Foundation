"""
RSS Learning Pipeline for StillMe V2
Fetches, filters, and processes content from RSS sources
"""

import hashlib
import logging
import time
import requests
from dataclasses import dataclass
from datetime import datetime
from typing import Any, List, Dict
import sys
import os

try:
    import feedparser
except ImportError:
    feedparser = None

# Import advanced scoring systems
from .trust_score_manager import trust_score_manager
from .advanced_quality_scorer import advanced_quality_scorer
from ..core.safety import ethical_safety_filter

# Import config directly
try:
    from config import RSS_FEEDS, LEARNING_TOPICS
except ImportError:
    # Fallback if config not available
    RSS_FEEDS = []
    LEARNING_TOPICS = []

logger = logging.getLogger(__name__)

# Global pipeline instance (singleton)
_pipeline_instance = None

def get_pipeline_instance() -> 'RSSLearningPipeline':
    """Get or create the global pipeline instance"""
    global _pipeline_instance
    if _pipeline_instance is None:
        _pipeline_instance = RSSLearningPipeline()
    return _pipeline_instance


@dataclass
class RSSSource:
    """RSS source configuration"""

    name: str
    url: str
    category: str
    trust_score: float
    enabled: bool = True


@dataclass
class PublicAPISource:
    """Public API source configuration"""
    
    name: str
    api_url: str
    category: str
    trust_score: float
    api_key: str = ""
    rate_limit: int = 100  # requests per hour
    enabled: bool = True


@dataclass
class ContentProposal:
    """Learning content proposal from RSS"""

    proposal_id: str
    title: str
    content: str
    source_name: str
    source_url: str
    category: str
    quality_score: float
    relevance_score: float
    novelty_score: float
    created_at: str
    status: str = "pending"


class RSSLearningPipeline:
    """
    Enhanced Learning Pipeline with RSS + Public APIs
    Fetches daily content from multiple sources and generates learning proposals
    """

    def __init__(self):
        self.rss_sources = self._load_rss_sources()
        self.api_sources = self._load_public_api_sources()
        self.fetched_content: list[dict[str, Any]] = []
        self.proposals: list[ContentProposal] = []
        self.seen_hashes: set[str] = set()
        logger.info(f"✅ Enhanced Pipeline initialized with {len(self.rss_sources)} RSS + {len(self.api_sources)} API sources")

    def _load_rss_sources(self) -> list[RSSSource]:
        """Load RSS source configurations"""
        # Use RSS_FEEDS from config
        sources = []
        for i, url in enumerate(RSS_FEEDS):
            sources.append(RSSSource(
                name=f"RSS Source {i+1}",
                url=url,
                category="general",
                trust_score=0.8,
            ))
        
        # Add default sources if no RSS_FEEDS configured
        if not sources:
            sources = [
                RSSSource(
                    name="Hacker News",
                    url="https://news.ycombinator.com/rss",
                    category="technology",
                    trust_score=0.9,
                ),
                RSSSource(
                    name="ArXiv CS.AI",
                    url="https://export.arxiv.org/rss/cs.AI",
                    category="ai_research",
                    trust_score=0.95,
                ),
                RSSSource(
                    name="GitHub Trending",
                url="https://github.com/trending",
                category="development",
                trust_score=0.85,
            ),
            RSSSource(
                name="Reddit Machine Learning",
                url="https://www.reddit.com/r/MachineLearning/.rss",
                category="ai_community",
                trust_score=0.8,
            ),
            RSSSource(
                name="TechCrunch AI",
                url="https://techcrunch.com/category/artificial-intelligence/feed/",
                category="ai_news",
                trust_score=0.75,
            ),
            RSSSource(
                name="MIT Technology Review",
                url="https://www.technologyreview.com/feed/",
                category="technology",
                trust_score=0.9,
            ),
            RSSSource(
                name="Towards Data Science",
                url="https://towardsdatascience.com/feed",
                category="data_science",
                trust_score=0.85,
            ),
            RSSSource(
                name="AI Weekly",
                url="https://aiweekly.co/feed",
                category="ai_news",
                trust_score=0.8,
            ),
            RSSSource(
                name="Papers With Code",
                url="https://paperswithcode.com/latest",
                category="ai_research",
                trust_score=0.9,
            ),
            RSSSource(
                name="The Batch by deeplearning.ai",
                url="https://www.deeplearning.ai/the-batch/",
                category="ai_education",
                trust_score=0.9,
            ),
            RSSSource(
                name="OpenAI Blog",
                url="https://openai.com/blog/rss/",
                category="ai_research",
                trust_score=0.95,
            ),
            RSSSource(
                name="Google AI Blog",
                url="https://ai.googleblog.com/feeds/posts/default",
                category="ai_research",
                trust_score=0.95,
            ),
        ]

        return sources

    def _load_public_api_sources(self) -> list[PublicAPISource]:
        """Load Public API source configurations"""
        api_sources = [
            # News APIs
            PublicAPISource(
                name="Hacker News API",
                api_url="https://hacker-news.firebaseio.com/v0/topstories.json",
                category="technology",
                trust_score=0.9,
                rate_limit=1000
            ),
            PublicAPISource(
                name="GitHub Trending API",
                api_url="https://api.github.com/search/repositories",
                category="development",
                trust_score=0.85,
                rate_limit=500
            ),
            PublicAPISource(
                name="Reddit Machine Learning",
                api_url="https://www.reddit.com/r/MachineLearning/hot.json",
                category="ai_community",
                trust_score=0.8,
                rate_limit=100
            ),
            # Science APIs
            PublicAPISource(
                name="ArXiv API",
                api_url="http://export.arxiv.org/api/query",
                category="ai_research",
                trust_score=0.95,
                rate_limit=200
            ),
            # Weather API (for context)
            PublicAPISource(
                name="OpenWeatherMap",
                api_url="https://api.openweathermap.org/data/2.5/weather",
                category="weather",
                trust_score=0.9,
                rate_limit=1000
            ),
        ]
        
        logger.info(f"📡 Loaded {len(api_sources)} Public API sources")
        return api_sources

    def fetch_daily_content(self, max_items_per_source: int = 10) -> list[dict[str, Any]]:
        """
        Fetch content from RSS sources and Public APIs

        Returns:
            List of fetched content items
        """
        logger.info("🔍 Fetching daily content from RSS + Public APIs...")

        all_content = []
        fetch_stats = {"total": 0, "success": 0, "failed": 0, "duplicates": 0}

        # Fetch from RSS sources
        for source in self.rss_sources:
            if not source.enabled:
                continue

            try:
                logger.debug(f"Fetching from {source.name}...")

                content_items = self._fetch_from_source(source, max_items_per_source)

                for item in content_items:
                    content_hash = self._generate_content_hash(item["title"], item["content"])

                    if content_hash in self.seen_hashes:
                        fetch_stats["duplicates"] += 1
                        continue

                    # Ethical safety check for fetched content
                    safety_result = ethical_safety_filter.check_content_safety(
                        content=item["content"],
                        source_url=item.get("source_url"),
                        context=f"RSS fetch from {source.name}"
                    )
                    
                    if not safety_result.is_safe:
                        logger.warning(f"🚫 Content blocked during fetch: {item['title']} - {safety_result.reason}")
                        fetch_stats["failed"] += 1
                        continue

                    self.seen_hashes.add(content_hash)
                    item["content_hash"] = content_hash
                    all_content.append(item)
                    fetch_stats["success"] += 1

                fetch_stats["total"] += len(content_items)

            except Exception as e:
                logger.error(f"❌ Failed to fetch from {source.name}: {e}")
                fetch_stats["failed"] += 1

        # Fetch from Public APIs
        for api_source in self.api_sources:
            if not api_source.enabled:
                continue

            try:
                logger.debug(f"Fetching from {api_source.name}...")
                
                api_content = self._fetch_from_api_source(api_source, max_items_per_source)
                
                for item in api_content:
                    content_hash = self._generate_content_hash(item["title"], item["content"])
                    
                    if content_hash in self.seen_hashes:
                        fetch_stats["duplicates"] += 1
                        continue
                    
                    self.seen_hashes.add(content_hash)
                    item["content_hash"] = content_hash
                    all_content.append(item)
                    fetch_stats["success"] += 1
                    
            except Exception as e:
                logger.error(f"❌ Failed to fetch from {api_source.name}: {e}")
                fetch_stats["failed"] += 1

        self.fetched_content = all_content

        logger.info(
            f"📦 Fetched {fetch_stats['success']} items "
            f"({fetch_stats['duplicates']} duplicates, {fetch_stats['failed']} sources failed)"
        )

        return all_content

    def _fetch_from_source(
        self, source: RSSSource, max_items: int
    ) -> list[dict[str, Any]]:
        """Fetch content from a single RSS source"""
        try:
            if feedparser is None:
                logger.error("❌ feedparser not installed. Install with: pip install feedparser")
                return []

            feed = feedparser.parse(source.url)

            items = []
            for entry in feed.entries[:max_items]:
                title = entry.get("title", "")
                description = entry.get("description", "") or entry.get("summary", "")
                link = entry.get("link", "")
                published = entry.get("published", "")

                if title and (description or link):
                    items.append(
                        {
                            "title": title,
                            "content": description,
                            "source_name": source.name,
                            "source_url": link,
                            "source_category": source.category,
                            "source_trust_score": source.trust_score,
                            "published_at": published,
                            "fetched_at": datetime.now().isoformat(),
                        }
                    )

            return items

        except ImportError:
            logger.error("❌ feedparser not installed. Install: pip install feedparser")
            return []
        except Exception as e:
            logger.error(f"❌ Error fetching from {source.name}: {e}")
            return []

    def _generate_content_hash(self, title: str, content: str) -> str:
        """Generate hash for content deduplication"""
        combined = f"{title}{content}".lower().strip()
        return hashlib.sha256(combined.encode()).hexdigest()[:16]

    def generate_proposals(
        self, contents: list[dict[str, Any]] | None = None
    ) -> list[ContentProposal]:
        """
        Generate learning proposals from fetched content

        Returns:
            List of content proposals
        """
        if contents is None:
            contents = self.fetched_content

        logger.info(f"🧠 Generating proposals from {len(contents)} content items...")

        proposals = []

        for content in contents:
            try:
                # Ethical safety check first
                safety_result = ethical_safety_filter.check_content_safety(
                    content=content["content"],
                    source_url=content.get("source_url"),
                    context=f"RSS content from {content['source_name']}"
                )
                
                if not safety_result.is_safe:
                    logger.warning(f"🚫 Content blocked by ethical filter: {content['title']} - {safety_result.reason}")
                    # Log ethical violations for transparency
                    for violation in safety_result.ethical_violations:
                        logger.warning(f"   ⚠️ Ethical violation: {violation.principle.value} - {violation.description}")
                    continue
                
                quality_score = self._calculate_quality_score(content)
                relevance_score = self._calculate_relevance_score(content)
                novelty_score = self._calculate_novelty_score(content)

                if quality_score < 0.5:
                    logger.debug(f"⚠️ Low quality content skipped: {content['title']}")
                    continue

                proposal_id = self._generate_proposal_id(content)

                # Auto-approve high trust content using dynamic trust scores
                source_name = content["source_name"]
                dynamic_trust_score = trust_score_manager.get_trust_score(source_name)
                category = content.get("source_category", "general")
                
                # Get domain-specific threshold
                auto_approve_threshold = trust_score_manager.get_recommended_threshold(category)
                
                logger.debug(f"Content: {content['title'][:50]}... | Dynamic Trust: {dynamic_trust_score:.3f} | Quality: {quality_score:.3f} | Threshold: {auto_approve_threshold:.3f}")
                
                if dynamic_trust_score >= auto_approve_threshold and quality_score >= 0.8:
                    status = "approved"
                    logger.info(f"Auto-approved high-trust content: {content['title']}")
                else:
                    status = "pending"

                proposal = ContentProposal(
                    proposal_id=proposal_id,
                    title=content["title"],
                    content=content["content"],
                    source_name=content["source_name"],
                    source_url=content.get("source_url", ""),
                    category=content.get("source_category", "general"),
                    quality_score=quality_score,
                    relevance_score=relevance_score,
                    novelty_score=novelty_score,
                    created_at=datetime.now().isoformat(),
                    status=status,
                )

                proposals.append(proposal)

            except Exception as e:
                logger.error(f"❌ Failed to generate proposal: {e}")

        self.proposals = proposals

        logger.info(f"✅ Generated {len(proposals)} proposals")

        return proposals

    def _calculate_quality_score(self, content: dict[str, Any]) -> float:
        """Calculate content quality score using advanced scoring system"""
        try:
            # Use advanced quality scorer
            metrics = advanced_quality_scorer.calculate_quality_score(content)
            return metrics.overall_score
        except Exception as e:
            logger.error(f"Error in advanced quality scoring: {e}")
            # Fallback to simple scoring
            return self._calculate_simple_quality_score(content)
    
    def _calculate_simple_quality_score(self, content: dict[str, Any]) -> float:
        """Fallback simple quality score calculation"""
        score = 0.5

        trust_score = content.get("source_trust_score", 0.5)
        score += trust_score * 0.3

        title = content.get("title", "")
        content_text = content.get("content", "")

        if len(title) > 20 and len(title) < 200:
            score += 0.1

        if len(content_text) > 100:
            score += 0.1

        return min(1.0, score)

    def _calculate_relevance_score(self, content: dict[str, Any]) -> float:
        """Calculate relevance score for learning"""
        relevant_keywords = [
            "ai",
            "machine learning",
            "deep learning",
            "technology",
            "programming",
            "python",
            "data science",
            "artificial intelligence",
            "neural network",
            "algorithm",
        ]

        title = content.get("title", "").lower()
        content_text = content.get("content", "").lower()
        combined = f"{title} {content_text}"

        matched_keywords = sum(1 for keyword in relevant_keywords if keyword in combined)

        relevance_score = min(1.0, matched_keywords / 5)

        return relevance_score

    def _calculate_novelty_score(self, content: dict[str, Any]) -> float:
        """Calculate novelty score"""
        content_hash = content.get("content_hash", "")

        if not content_hash:
            return 0.5

        return 0.8

    def _generate_proposal_id(self, content: dict[str, Any]) -> str:
        """Generate unique proposal ID"""
        content_hash = content.get("content_hash", hashlib.sha256(str(time.time()).encode()).hexdigest()[:16])
        timestamp = int(time.time())
        return f"PROP_{timestamp}_{content_hash[:8]}"

    def filter_proposals_for_auto_approval(
        self, 
        proposals: list[ContentProposal] | None = None,
        threshold: float = 0.8
    ) -> tuple[list[ContentProposal], list[ContentProposal]]:
        """
        Filter proposals for auto-approval

        Returns:
            (auto_approved, needs_review)
        """
        if proposals is None:
            proposals = self.proposals

        auto_approved = []
        needs_review = []

        for proposal in proposals:
            if self._should_auto_approve(proposal):
                proposal.status = "approved"
                auto_approved.append(proposal)
            else:
                needs_review.append(proposal)

        logger.info(
            f"📋 Auto-approved: {len(auto_approved)}, Needs review: {len(needs_review)}"
        )

        return auto_approved, needs_review

    def _should_auto_approve(self, proposal: ContentProposal) -> bool:
        """Determine if proposal should be auto-approved"""
        # Use same logic as generate_proposals()
        return proposal.status == "approved"

    def _fetch_from_api_source(self, api_source: PublicAPISource, max_items: int) -> list[dict[str, Any]]:
        """Fetch content from a single Public API source"""
        try:
            items = []
            
            if api_source.name == "Hacker News API":
                items = self._fetch_hacker_news(api_source, max_items)
            elif api_source.name == "GitHub Trending API":
                items = self._fetch_github_trending(api_source, max_items)
            elif api_source.name == "Reddit Machine Learning":
                items = self._fetch_reddit_ml(api_source, max_items)
            elif api_source.name == "ArXiv API":
                items = self._fetch_arxiv(api_source, max_items)
            elif api_source.name == "OpenWeatherMap":
                items = self._fetch_weather(api_source, max_items)
            
            logger.debug(f"📡 Fetched {len(items)} items from {api_source.name}")
            return items
            
        except Exception as e:
            logger.error(f"❌ API fetch error from {api_source.name}: {e}")
            return []

    def _fetch_hacker_news(self, api_source: PublicAPISource, max_items: int) -> list[dict[str, Any]]:
        """Fetch from Hacker News API"""
        try:
            response = requests.get(api_source.api_url, timeout=10)
            response.raise_for_status()
            
            story_ids = response.json()[:max_items]
            items = []
            
            for story_id in story_ids:
                story_url = f"https://hacker-news.firebaseio.com/v0/item/{story_id}.json"
                story_response = requests.get(story_url, timeout=5)
                
                if story_response.status_code == 200:
                    story = story_response.json()
                    if story and story.get("type") == "story":
                        items.append({
                            "title": story.get("title", ""),
                            "content": f"Hacker News story: {story.get('title', '')}",
                            "source_url": story.get("url", ""),
                            "source_name": api_source.name,
                            "category": api_source.category,
                            "published": datetime.now().isoformat(),
                            "trust_score": api_source.trust_score
                        })
            
            return items
            
        except Exception as e:
            logger.error(f"❌ Hacker News fetch error: {e}")
            return []

    def _fetch_github_trending(self, api_source: PublicAPISource, max_items: int) -> list[dict[str, Any]]:
        """Fetch from GitHub Trending API"""
        try:
            params = {
                "q": "stars:>1000 language:python",
                "sort": "stars",
                "order": "desc",
                "per_page": max_items
            }
            
            response = requests.get(api_source.api_url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            items = []
            
            for repo in data.get("items", []):
                items.append({
                    "title": f"GitHub Trending: {repo.get('name', '')}",
                    "content": f"Repository: {repo.get('description', '')} - Stars: {repo.get('stargazers_count', 0)}",
                    "source_url": repo.get("html_url", ""),
                    "source_name": api_source.name,
                    "category": api_source.category,
                    "published": repo.get("updated_at", ""),
                    "trust_score": api_source.trust_score
                })
            
            return items
            
        except Exception as e:
            logger.error(f"❌ GitHub Trending fetch error: {e}")
            return []

    def _fetch_reddit_ml(self, api_source: PublicAPISource, max_items: int) -> list[dict[str, Any]]:
        """Fetch from Reddit Machine Learning"""
        try:
            headers = {"User-Agent": "StillMe-V2-Bot/1.0"}
            response = requests.get(api_source.api_url, headers=headers, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            items = []
            
            for post in data.get("data", {}).get("children", [])[:max_items]:
                post_data = post.get("data", {})
                items.append({
                    "title": post_data.get("title", ""),
                    "content": f"Reddit ML: {post_data.get('selftext', '')[:200]}...",
                    "source_url": f"https://reddit.com{post_data.get('permalink', '')}",
                    "source_name": api_source.name,
                    "category": api_source.category,
                    "published": datetime.fromtimestamp(post_data.get("created_utc", 0)).isoformat(),
                    "trust_score": api_source.trust_score
                })
            
            return items
            
        except Exception as e:
            logger.error(f"❌ Reddit ML fetch error: {e}")
            return []

    def _fetch_arxiv(self, api_source: PublicAPISource, max_items: int) -> list[dict[str, Any]]:
        """Fetch from ArXiv API"""
        try:
            params = {
                "search_query": "cat:cs.AI",
                "start": 0,
                "max_results": max_items,
                "sortBy": "relevance",
                "sortOrder": "descending"
            }
            
            response = requests.get(api_source.api_url, params=params, timeout=15)
            response.raise_for_status()
            
            # Parse XML response (simplified)
            items = []
            # Note: In production, use proper XML parsing
            content = response.text
            
            # Simple extraction (for demo purposes)
            if "entry" in content:
                items.append({
                    "title": "ArXiv AI Research Papers",
                    "content": f"Latest AI research papers from ArXiv: {content[:200]}...",
                    "source_url": "https://arxiv.org/list/cs.AI/recent",
                    "source_name": api_source.name,
                    "category": api_source.category,
                    "published": datetime.now().isoformat(),
                    "trust_score": api_source.trust_score
                })
            
            return items
            
        except Exception as e:
            logger.error(f"❌ ArXiv fetch error: {e}")
            return []

    def _fetch_weather(self, api_source: PublicAPISource, max_items: int) -> list[dict[str, Any]]:
        """Fetch weather data for context"""
        try:
            # This is just for demonstration - weather provides context
            items = []
            
            # Mock weather data (in production, use real API with API key)
            items.append({
                "title": "Weather Context",
                "content": "Current weather conditions for learning context",
                "source_url": "",
                "source_name": api_source.name,
                "category": api_source.category,
                "published": datetime.now().isoformat(),
                "trust_score": api_source.trust_score
            })
            
            return items
            
        except Exception as e:
            logger.error(f"❌ Weather fetch error: {e}")
            return []

    def get_pipeline_stats(self) -> dict[str, Any]:
        """Get pipeline statistics"""
        all_sources = self.rss_sources + self.api_sources
        return {
            "total_rss_sources": len(self.rss_sources),
            "total_api_sources": len(self.api_sources),
            "enabled_sources": sum(1 for s in all_sources if s.enabled),
            "fetched_content_count": len(self.fetched_content),
            "proposals_count": len(self.proposals),
            "seen_hashes_count": len(self.seen_hashes),
            "categories": list(set(s.category for s in all_sources)),
        }

