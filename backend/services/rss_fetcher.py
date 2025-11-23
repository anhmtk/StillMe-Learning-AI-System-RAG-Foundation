"""
RSS Feed Fetcher for StillMe
Enhanced RSS fetching service with retry mechanism, XML validation, and fallback feeds
"""

import feedparser
import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging

from backend.services.rss_fetcher_enhanced import (
    fetch_feed_with_fallback,
    fetch_feed_with_retry
)

logger = logging.getLogger(__name__)

class RSSFetcher:
    """Simple RSS feed fetcher"""
    
    def __init__(self):
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
            "https://www.scientificamerican.com/rss/",  # Scientific American - Science news & analysis
            "https://www.science.org/rss/news_current.xml",  # Science Magazine - Latest research news
            "https://www.pnas.org/rss/current.xml",  # PNAS (Proceedings of the National Academy of Sciences) - Top research
            # Removed: "https://www.sciencedaily.com/rss/matter_energy.xml" - XML parse errors (all variants failed)
            
            # Physics
            "https://www.aps.org/publications/apsnews/rss.xml",  # American Physical Society News
            "https://www.iop.org/rss",  # Institute of Physics RSS
            # Removed: "https://physicsworld.com/feed/" - XML parse errors (all variants failed)
            "https://phys.org/rss-feed/",  # Phys.org main feed (reliable)
            
            # Chemistry
            # Note: Some chemistry feeds may be empty - will be monitored and replaced if needed
            
            # History & Historical Events
            "https://www.history.com/.rss/topics/news",  # History.com - Historical events & analysis
            "https://www.bbc.com/news/world/rss.xml",  # BBC World News - International history & current events
            "https://www.theguardian.com/world/rss",  # The Guardian World - Historical context & analysis
            # Note: Historical sources help StillMe answer questions about events like Geneva 1954, Bretton Woods 1944
            
            # Ethics & Applied Philosophy
            "https://www.ethics.org.au/feed/",  # The Ethics Centre - Applied ethics & moral philosophy
            "https://www.bioethics.net/feed/",  # Bioethics.net - Bioethics & medical ethics
            # Note: Ethics sources complement philosophy sources for practical ethical reasoning
            
            # Social Sciences
            "https://www.psychologytoday.com/us/rss",  # Psychology Today - Psychology & social sciences
            "https://www.scientificamerican.com/psychology/feed/",  # Scientific American Psychology
            # Note: Social sciences provide context for understanding human behavior, religion, philosophy
            
            # Religious Studies & Philosophy
            "https://philpapers.org/rss/recent.xml",  # PhilPapers - Recent philosophy papers
            "https://www.philosophynow.org/rss",  # Philosophy Now - Philosophy magazine
            "https://www.theguardian.com/world/religion/rss",  # The Guardian - Religion
            "https://tricycle.org/feed/",  # Tricycle - Buddhist Magazine (reliable)
            "https://iep.utm.edu/feed/",  # Internet Encyclopedia of Philosophy - Academic philosophy reference
            "https://www.patheos.com/feed/",  # Patheos - Multi-religious perspectives & interfaith dialogue
            "https://www.religionnews.com/feed/",  # Religion News Service - Religion news & analysis
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
            "https://www.acm.org/feed",  # ACM (Association for Computing Machinery) - Tech policy & research
            "https://www.technologyreview.com/feed/",  # MIT Technology Review - AI & technology (main feed)
            # Removed: "https://www.brookings.edu/feed/" - XML parsing error (syntax error: line 2, column 0)
            # Removed: "https://www.cato.org/feed/" - Failed to fetch (403/404)
            # Removed: "https://www.aei.org/technology/feed/" - 403 Forbidden, no reliable alternative
            
            # AI Ethics & Technology
            # Removed: "https://www.technologyreview.com/topic/artificial-intelligence/feed/" - Failed to fetch
            # Removed: "https://aiethicslab.com/feed/" - Failed to fetch
            
            # Academic Blogs & AI Alignment
            "https://www.overcomingbias.com/feed",  # Overcoming Bias - Rationality (reliable)
            "https://www.gwern.net/feed.xml",  # Gwern's Blog - AI, rationality, research
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
    
    async def fetch_feeds_async(self, max_items_per_feed: int = 5) -> List[Dict[str, Any]]:
        """Fetch entries from all RSS feeds (async version with retry and fallback)
        
        Args:
            max_items_per_feed: Maximum items to fetch per feed
            
        Returns:
            List of feed entries
        """
        all_entries = []
        self.successful_feeds = 0
        self.failed_feeds = 0
        errors = []
        
        # Fetch all feeds concurrently with retry and fallback
        tasks = [fetch_feed_with_fallback(feed_url) for feed_url in self.feeds]
        feeds = await asyncio.gather(*tasks, return_exceptions=True)
        
        for feed_url, feed_result in zip(self.feeds, feeds):
            try:
                if isinstance(feed_result, Exception):
                    error_msg = f"Failed to fetch {feed_url}: {feed_result}"
                    errors.append(error_msg)
                    self.failed_feeds += 1
                    self.error_count += 1
                    logger.error(error_msg)
                    continue
                
                if feed_result is None:
                    error_msg = f"Failed to fetch {feed_url}: All retries and fallbacks exhausted"
                    errors.append(error_msg)
                    self.failed_feeds += 1
                    logger.warning(error_msg)
                    continue
                
                feed = feed_result
                
                # Check if feed parsing was successful
                if feed.bozo and feed.bozo_exception:
                    error_msg = f"RSS feed parse error for {feed_url}: {feed.bozo_exception}"
                    errors.append(error_msg)
                    self.failed_feeds += 1
                    logger.warning(error_msg)
                    continue
                
                # Extract entries
                for entry in feed.entries[:max_items_per_feed]:
                    entry_data = {
                        "title": entry.get("title", ""),
                        "summary": entry.get("summary", entry.get("description", "")),
                        "link": entry.get("link", ""),
                        "published": entry.get("published", datetime.now().isoformat()),
                        "source": feed_url,
                        "content_type": "knowledge"
                    }
                    all_entries.append(entry_data)
                
                self.successful_feeds += 1
                logger.info(f"✅ Fetched {len(feed.entries[:max_items_per_feed])} items from {feed_url}")
                
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
    
    def fetch_feeds(self, max_items_per_feed: int = 5) -> List[Dict[str, Any]]:
        """Fetch entries from all RSS feeds (synchronous wrapper)
        
        Args:
            max_items_per_feed: Maximum items to fetch per feed
            
        Returns:
            List of feed entries
        """
        # Run async version in event loop
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # If loop is already running, create a new task
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(asyncio.run, self.fetch_feeds_async(max_items_per_feed))
                    return future.result()
            else:
                return loop.run_until_complete(self.fetch_feeds_async(max_items_per_feed))
        except RuntimeError:
            # No event loop, create one
            return asyncio.run(self.fetch_feeds_async(max_items_per_feed))
    
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

