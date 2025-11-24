"""
RSS Feed Fetcher for StillMe
Enhanced RSS fetching service with retry mechanism, XML validation, and fallback feeds
"""

import feedparser
import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from backend.services.content_curator import ContentCurator

from backend.services.rss_fetcher_enhanced import (
    fetch_feed_with_fallback,
    fetch_feed_with_retry
)
from backend.services.circuit_breaker import CircuitBreakerManager, CircuitBreakerConfig
from backend.services.feed_health_monitor import get_feed_health_monitor

logger = logging.getLogger(__name__)

class RSSFetcher:
    """Simple RSS feed fetcher"""
    
    def __init__(self):
        # Initialize circuit breaker manager for RSS feeds
        self.circuit_breaker_manager = CircuitBreakerManager()
        # Circuit breaker config: Open after 5 failures, close after 2 successes, 60s timeout
        self.circuit_config = CircuitBreakerConfig(
            failure_threshold=5,
            success_threshold=2,
            timeout_seconds=60,
            timeout_window=300  # 5 minute window
        )
        # Default trusted RSS feeds
        self.feeds = [
            # Existing feeds
            "https://news.ycombinator.com/rss",
            "https://rss.nytimes.com/services/xml/rss/nyt/Technology.xml",
            
            # Statistics
            "https://www.r-bloggers.com/feed/",
            "https://feeds.feedburner.com/StatisticalModelingCausalInferenceAndSocialScience",
            
            # Psychology
            # Note: psychologicalscience.org feed has parse errors - removed temporarily
            # "https://www.psychologicalscience.org/feed",
            
            # Biology & Science
            "https://www.nature.com/nature.rss",
            "https://www.nature.com/natmachintell.rss",  # Nature Machine Intelligence - AI research & ethics
            "https://www.pnas.org/action/showFeed?type=etoc&feed=rss&jc=PNAS",  # PNAS - Working feed (alternative to /rss/current.xml)
            # Removed: "https://www.scientificamerican.com/rss/" - 404 Not Found
            # Removed: "https://www.science.org/rss/news_current.xml" - XML validation errors
            # Removed: "https://www.pnas.org/rss/current.xml" - XML validation errors (using action/showFeed instead)
            # Removed: "https://www.sciencedaily.com/rss/matter_energy.xml" - XML parse errors (all variants failed)
            
            # Physics
            # Removed: "https://www.aps.org/publications/apsnews/rss.xml" - 403 Forbidden (bot protection)
            # Removed: "https://www.iop.org/rss" - 403 Forbidden (bot protection)
            # Removed: "https://physicsworld.com/feed/" - XML parse errors (all variants failed)
            "https://phys.org/rss-feed/",  # Phys.org main feed (reliable)
            
            # Chemistry
            # Note: Some chemistry feeds may be empty - will be monitored and replaced if needed
            
            # History & Historical Events
            "https://feeds.bbci.co.uk/news/world/rss.xml",  # BBC World News - Fixed URL (redirects from bbc.com)
            "https://www.theguardian.com/world/rss",  # The Guardian World - Historical context & analysis
            "https://www.historytoday.com/rss.xml",  # History Today - Academic history magazine
            # Removed: "https://www.history.com/.rss/topics/news" - 404 Not Found
            # Note: Historical sources help StillMe answer questions about events like Geneva 1954, Bretton Woods 1944
            
            # Ethics & Applied Philosophy
            "http://bioethicstoday.org/feed/",  # Bioethics Today - Working redirect from bioethics.net
            # Removed: "https://www.ethics.org.au/feed/" - XML validation errors
            # Removed: "https://www.bioethics.net/feed/" - Redirects to bioethicstoday.org (using direct URL)
            # Note: Ethics sources complement philosophy sources for practical ethical reasoning
            
            # Social Sciences
            "https://www.apa.org/rss/topics/psychology",  # American Psychological Association - Psychology news
            # Removed: "https://www.psychologytoday.com/us/rss" - 404 Not Found
            # Removed: "https://www.scientificamerican.com/psychology/feed/" - 404 Not Found
            # Note: Social sciences provide context for understanding human behavior, religion, philosophy
            
            # Religious Studies & Philosophy
            "https://www.philosophynow.org/rss",  # Philosophy Now - Philosophy magazine (reliable)
            "https://www.theguardian.com/world/religion/rss",  # The Guardian - Religion
            "https://tricycle.org/feed/",  # Tricycle - Buddhist Magazine (reliable)
            "https://iep.utm.edu/feed/",  # Internet Encyclopedia of Philosophy - Academic philosophy reference
            "https://www.firstthings.com/rss",  # First Things - Religion, culture, philosophy
            # Removed: "https://philpapers.org/rss/recent.xml" - 403 Forbidden (bot protection)
            # Removed: "https://www.patheos.com/feed/" - 403 Forbidden (bot protection)
            # Removed: "https://www.religionnews.com/feed/" - 403 Forbidden (bot protection)
            # Removed: "https://aeon.co/feed.rss" - XML parse errors (all variants failed)
            # Removed: "https://www.lionsroar.com/feed/" - XML parse errors (all variants failed)
            
            # NEW: Academic & Research Sources (as suggested by StillMe in user conversation)
            # Added based on StillMe's analysis of reliable, peer-reviewed, and up-to-date sources
            # Removed: "https://www.science.org/action/showFeed?type=etoc&feed=rss&jc=science" - XML parsing error (not well-formed)
            # Note: "https://www.nature.com/nature.rss" already listed above in Biology & Science section
            # Removed: Reuters feeds (businessNews, technologyNews) - Permanent DNS errors ([Errno -2] Name or service not known)
            "https://feeds.bloomberg.com/markets/news.rss",  # Bloomberg Markets - Economic & financial analysis
            
            # Tech Policy & AI Governance Blogs
            "https://www.eff.org/rss/updates.xml",  # Electronic Frontier Foundation - Tech policy
            "https://www.wired.com/feed/rss",  # Wired - Technology & AI news
            # Removed: "https://www.acm.org/feed" - 403 Forbidden (bot protection)
            # Removed: "https://www.technologyreview.com/feed/" - XML validation errors
            # Removed: "https://www.brookings.edu/feed/" - XML parsing error (syntax error: line 2, column 0)
            # Removed: "https://www.cato.org/feed/" - Failed to fetch (403/404)
            # Removed: "https://www.aei.org/technology/feed/" - 403 Forbidden, no reliable alternative
            
            # AI Ethics & Technology
            # Removed: "https://www.technologyreview.com/topic/artificial-intelligence/feed/" - Failed to fetch
            # Removed: "https://aiethicslab.com/feed/" - Failed to fetch
            
            # Academic Blogs & AI Alignment
            "https://www.overcomingbias.com/feed",  # Overcoming Bias - Rationality (reliable)
            # Removed: "https://www.gwern.net/feed.xml" - XML validation errors
            # Removed: "https://www.alignmentforum.org/feed.xml" - XML parse errors (all variants failed)
            # Removed: "https://www.lesswrong.com/feed.xml" - XML parse errors
            # Removed: "https://distill.pub/rss.xml" - Failed to fetch
            # Removed: "https://lilianweng.github.io/feed.xml" - 404 + XML error, no reliable alternative
            # Removed: "https://www.scottaaronson.com/blog/?feed=rss2" - Failed to fetch
            
            # Note: Google Scholar, PubMed, IEEE Xplore don't have public RSS feeds
            # These would require API integration (future enhancement):
            # - Google Scholar: Would need scraping or unofficial API (rate-limited)
            # - PubMed: Has API but requires API key and structured queries
            # - IEEE Xplore: Requires institutional access and API key
        ]
        # Track error states for self-diagnosis
        self.last_error: Optional[str] = None
        self.error_count = 0
        self.last_success_time: Optional[datetime] = None
        self.successful_feeds = 0
        self.failed_feeds = 0
    
    async def fetch_feeds_async(self, max_items_per_feed: Optional[int] = None, 
                                content_curator=None, 
                                min_importance_score: float = 0.3) -> List[Dict[str, Any]]:
        """Fetch entries from all RSS feeds with value-based prioritization
        
        Args:
            max_items_per_feed: Maximum items to fetch per feed (None = fetch all, then filter by value)
            content_curator: ContentCurator instance for importance scoring (optional)
            min_importance_score: Minimum importance score to include (0.0-1.0)
            
        Returns:
            List of feed entries, prioritized by value/importance
        """
        all_entries = []
        self.successful_feeds = 0
        self.failed_feeds = 0
        errors = []
        
        # Fetch all feeds concurrently with retry and fallback
        # Wrap each fetch with circuit breaker
        async def fetch_with_circuit_breaker(feed_url: str):
            """Fetch feed with circuit breaker protection"""
            breaker = self.circuit_breaker_manager.get_breaker(
                f"rss_feed_{feed_url[:50]}",  # Use first 50 chars as name
                self.circuit_config
            )
            
            # Check if circuit is open
            if breaker.state.value == "open":
                logger.warning(f"Circuit breaker OPEN for {feed_url} - skipping (too many failures)")
                return None
            
            try:
                # Execute fetch with circuit breaker
                result = await fetch_feed_with_fallback(feed_url)
                breaker._on_success()
                # Record success in health monitor
                health_monitor = get_feed_health_monitor()
                health_monitor.record_success(feed_url)
                health_monitor.update_circuit_breaker_state(feed_url, breaker.state.value)
                return result
            except Exception as e:
                breaker._on_failure()
                # Record failure in health monitor
                health_monitor = get_feed_health_monitor()
                health_monitor.record_failure(feed_url, str(e))
                health_monitor.update_circuit_breaker_state(feed_url, breaker.state.value)
                raise
        
        tasks = [fetch_with_circuit_breaker(feed_url) for feed_url in self.feeds]
        feeds = await asyncio.gather(*tasks, return_exceptions=True)
        
        for feed_url, feed_result in zip(self.feeds, feeds):
            try:
                if isinstance(feed_result, Exception):
                    error_msg = f"Failed to fetch {feed_url}: {feed_result}"
                    errors.append(error_msg)
                    self.failed_feeds += 1
                    self.error_count += 1
                    logger.error(error_msg)
                    # Record failure in health monitor
                    health_monitor = get_feed_health_monitor()
                    health_monitor.record_failure(feed_url, str(feed_result))
                    breaker = self.circuit_breaker_manager.get_breaker(
                        f"rss_feed_{feed_url[:50]}",
                        self.circuit_config
                    )
                    health_monitor.update_circuit_breaker_state(feed_url, breaker.state.value)
                    continue
                
                if feed_result is None:
                    error_msg = f"Failed to fetch {feed_url}: All retries and fallbacks exhausted or circuit breaker OPEN"
                    errors.append(error_msg)
                    self.failed_feeds += 1
                    logger.warning(error_msg)
                    # Record failure in health monitor
                    health_monitor = get_feed_health_monitor()
                    health_monitor.record_failure(feed_url, "All retries exhausted or circuit breaker OPEN")
                    breaker = self.circuit_breaker_manager.get_breaker(
                        f"rss_feed_{feed_url[:50]}",
                        self.circuit_config
                    )
                    health_monitor.update_circuit_breaker_state(feed_url, breaker.state.value)
                    continue
                
                feed = feed_result
                
                # Check if feed parsing was successful
                if feed.bozo and feed.bozo_exception:
                    error_msg = f"RSS feed parse error for {feed_url}: {feed.bozo_exception}"
                    errors.append(error_msg)
                    self.failed_feeds += 1
                    logger.warning(error_msg)
                    continue
                
                # Extract ALL entries (no limit if max_items_per_feed is None)
                feed_entries = feed.entries
                if max_items_per_feed is not None:
                    feed_entries = feed.entries[:max_items_per_feed]
                
                # Process each entry and calculate importance score
                scored_entries = []
                for entry in feed_entries:
                    entry_data = {
                        "title": entry.get("title", ""),
                        "summary": entry.get("summary", entry.get("description", "")),
                        "link": entry.get("link", ""),
                        "published": entry.get("published", datetime.now().isoformat()),
                        "source": feed_url,
                        "content_type": "knowledge"
                    }
                    
                    # Calculate importance score if curator available
                    if content_curator:
                        importance_score = content_curator.calculate_importance_score(entry_data)
                        entry_data["importance_score"] = importance_score
                        # Only include if meets minimum threshold
                        if importance_score >= min_importance_score:
                            scored_entries.append(entry_data)
                    else:
                        # No curator: include all entries (backward compatibility)
                        scored_entries.append(entry_data)
                
                # Sort by importance score (highest first) if curator available
                if content_curator and scored_entries:
                    scored_entries.sort(key=lambda x: x.get("importance_score", 0.0), reverse=True)
                
                all_entries.extend(scored_entries)
                self.successful_feeds += 1
                
                if content_curator:
                    logger.info(f"✅ Fetched {len(scored_entries)}/{len(feed.entries)} items from {feed_url} (value-based: importance >= {min_importance_score})")
                else:
                    logger.info(f"✅ Fetched {len(scored_entries)} items from {feed_url}")
                
            except Exception as e:
                error_msg = f"Failed to process {feed_url}: {e}"
                errors.append(error_msg)
                self.failed_feeds += 1
                self.error_count += 1
                logger.error(error_msg)
        
        # Update error state
        if errors:
            self.last_error = "; ".join(errors[:3])  # Keep first 3 errors
        else:
            self.last_error = None
            self.last_success_time = datetime.now()
        
        # Calculate failure rate
        total_feeds = len(self.feeds)
        failure_rate = (self.failed_feeds / total_feeds * 100) if total_feeds > 0 else 0
        
        logger.info(f"📊 RSS Feed Summary: {len(all_entries)} entries (successful: {self.successful_feeds}/{total_feeds}, failed: {self.failed_feeds}/{total_feeds}, failure rate: {failure_rate:.1f}%)")
        
        # Alert if failure rate is high
        if failure_rate > 10:
            logger.warning(f"⚠️ HIGH RSS FEED FAILURE RATE: {failure_rate:.1f}% ({self.failed_feeds}/{total_feeds} feeds failed)")
        
        return all_entries
    
    def fetch_feeds(self, max_items_per_feed: Optional[int] = None, 
                    content_curator=None,
                    min_importance_score: float = 0.3) -> List[Dict[str, Any]]:
        """Fetch entries from all RSS feeds with value-based prioritization (synchronous wrapper)
        
        Args:
            max_items_per_feed: Maximum items to fetch per feed (None = fetch all, filter by value)
            content_curator: ContentCurator instance for importance scoring (optional)
            min_importance_score: Minimum importance score to include (0.0-1.0)
            
        Returns:
            List of feed entries, prioritized by value/importance
        """
        # Run async version in event loop
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # If loop is already running, create a new task
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(
                        asyncio.run, 
                        self.fetch_feeds_async(max_items_per_feed, content_curator, min_importance_score)
                    )
                    return future.result()
            else:
                return loop.run_until_complete(
                    self.fetch_feeds_async(max_items_per_feed, content_curator, min_importance_score)
                )
        except RuntimeError:
            # No event loop, create one
            return asyncio.run(self.fetch_feeds_async(max_items_per_feed, content_curator, min_importance_score))
    
    def fetch_single_feed(self, feed_url: str, max_items: int = 5) -> List[Dict[str, Any]]:
        """Fetch entries from a single RSS feed"""
        try:
            feed = feedparser.parse(feed_url)
            entries = []
            
            for entry in feed.entries[:max_items]:
                entry_data = {
                    "title": entry.get("title", ""),
                    "summary": entry.get("summary", entry.get("description", "")),
                    "link": entry.get("link", ""),
                    "published": entry.get("published", datetime.now().isoformat()),
                    "source": feed_url,
                    "content_type": "knowledge"
                }
                entries.append(entry_data)
            
            return entries
            
        except Exception as e:
            error_msg = f"Failed to fetch {feed_url}: {e}"
            self.last_error = error_msg
            self.error_count += 1
            logger.error(error_msg)
            return []
    
    def get_stats(self) -> Dict[str, Any]:
        """Get fetcher statistics"""
        total_feeds = len(self.feeds)
        failure_rate = (self.failed_feeds / total_feeds * 100) if total_feeds > 0 else 0
        
        return {
            "source": "rss",
            "feeds_count": total_feeds,
            "successful_feeds": self.successful_feeds,
            "failed_feeds": self.failed_feeds,
            "failure_rate": round(failure_rate, 2),
            "error_count": self.error_count,
            "last_error": self.last_error,
            "last_success_time": self.last_success_time.isoformat() if self.last_success_time else None,
            "status": "error" if self.last_error and (not self.last_success_time or self.failed_feeds > 0) else "ok",
            "alert_threshold_exceeded": failure_rate > 10
        }

