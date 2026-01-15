"""
Learning Scheduler Service for StillMe
Automatically runs learning cycles every N hours to fetch content and add to RAG
CRITICAL: This is a core feature - must always be enabled and running

⚠️ MIGRATION NOTE: This module is being migrated to stillme_core.learning.scheduler.
This file now serves as an adapter that forwards to stillme_core.learning.scheduler.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from backend.services.rss_fetcher import RSSFetcher
    from backend.services.source_integration import SourceIntegration
    from backend.vector_db.rag_retrieval import RAGRetrieval
    from backend.services.content_curator import ContentCurator
    from backend.learning.continuum_memory import ContinuumMemory
    from backend.services.rss_fetch_history import RSSFetchHistory

logger = logging.getLogger(__name__)


class LearningScheduler:
    """
    Scheduler that automatically runs learning cycles to fetch content and add to RAG.
    
    CRITICAL: This is a core feature of StillMe - must always be enabled.
    The scheduler runs every N hours (default: 4 hours) to:
    1. Fetch content from RSS feeds and other sources
    2. Pre-filter content for quality
    3. Automatically add to RAG vector database
    4. Track learning history
    """
    
    def __init__(
        self,
        rss_fetcher: Optional["RSSFetcher"] = None,
        source_integration: Optional["SourceIntegration"] = None,
        rag_retrieval: Optional["RAGRetrieval"] = None,
        content_curator: Optional["ContentCurator"] = None,
        rss_fetch_history: Optional["RSSFetchHistory"] = None,
        continuum_memory: Optional["ContinuumMemory"] = None,
        interval_hours: int = 4,
        auto_add_to_rag: bool = True
    ):
        """
        Initialize learning scheduler.
        
        Args:
            rss_fetcher: RSS fetcher instance (optional, will create if None)
            source_integration: Source integration instance (optional, will create if None)
            rag_retrieval: RAG retrieval instance (optional, injected later)
            content_curator: Content curator instance (optional, will create if None)
            rss_fetch_history: RSS fetch history tracker (optional, will create if None)
            continuum_memory: Continuum memory instance (optional)
            interval_hours: Hours between learning cycles (default: 4)
            auto_add_to_rag: Whether to automatically add fetched content to RAG (default: True)
        """
        # Import here to avoid circular imports
        if rss_fetcher is None:
            from backend.services.rss_fetcher import get_rss_fetcher
            rss_fetcher = get_rss_fetcher()  # Use singleton to ensure stats are shared
        
        if source_integration is None:
            from backend.services.source_integration import SourceIntegration
            from stillme_core.learning.curator import ContentCurator
            content_curator = content_curator or ContentCurator()
            source_integration = SourceIntegration(content_curator=content_curator)
        
        if content_curator is None:
            from stillme_core.learning.curator import ContentCurator
            content_curator = ContentCurator()
        
        if rss_fetch_history is None:
            from backend.services.rss_fetch_history import RSSFetchHistory
            rss_fetch_history = RSSFetchHistory()
        
        self.rss_fetcher = rss_fetcher
        self.source_integration = source_integration
        self.rag_retrieval = rag_retrieval  # Will be injected later
        self.content_curator = content_curator
        self.rss_fetch_history = rss_fetch_history
        self.continuum_memory = continuum_memory
        
        self.interval_hours = interval_hours
        self.auto_add_to_rag = auto_add_to_rag
        
        # State tracking
        self.cycle_count = 0
        self.is_running = False
        self._task: Optional[asyncio.Task] = None
        self._proactive_health_task: Optional[asyncio.Task] = None  # Phase 3.2
        self.last_run_time: Optional[datetime] = None
        self.next_run_time: Optional[datetime] = None
        self._stop_event = asyncio.Event()
        
        logger.info(f"LearningScheduler initialized: interval={interval_hours}h, auto_add_to_rag={auto_add_to_rag}")
    
    def set_rag_retrieval(self, rag_retrieval: "RAGRetrieval"):
        """Set RAG retrieval instance (injected after initialization)"""
        self.rag_retrieval = rag_retrieval
        logger.info("RAG retrieval instance set for LearningScheduler")
    
    async def run_learning_cycle(self) -> Dict[str, Any]:
        """
        Run a single learning cycle:
        1. Fetch content from all sources
        2. Pre-filter for quality
        3. Add to RAG (if auto_add_to_rag=True)
        4. Track in history
        
        Returns:
            Dict with cycle results: cycle_number, entries_fetched, entries_added_to_rag, etc.
        """
        start_time = datetime.now()
        cycle_number = self.cycle_count + 1
        
        logger.info(f"🔄 Starting learning cycle #{cycle_number}...")
        
        try:
            # Stage 2 Phase 2: Apply curriculum before learning cycle
            # This ensures we prioritize topics that provide most improvement
            try:
                from backend.learning.curriculum_applier import get_curriculum_applier
                if self.content_curator:
                    applier = get_curriculum_applier(curator=self.content_curator)
                    applier.apply_curriculum(
                        days=30,
                        update_curator=True,
                        update_scheduler=False  # Don't update scheduler during cycle
                    )
                    logger.debug("✅ Applied curriculum to learning cycle")
            except Exception as curriculum_error:
                logger.debug(f"Could not apply curriculum: {curriculum_error}")
            
            # Step 1: Fetch from all sources
            all_entries = self.source_integration.fetch_all_sources(
                max_items_per_source=5,
                use_pre_filter=True,  # Apply pre-filter to reduce costs
                content_curator=self.content_curator,
                min_importance_score=0.3
            )
            
            entries_fetched = len(all_entries)
            logger.info(f"📥 Fetched {entries_fetched} entries from all sources")
            
            # Step 2: Create fetch cycle for tracking
            cycle_id = None
            if self.rss_fetch_history:
                cycle_id = self.rss_fetch_history.create_fetch_cycle(cycle_number=cycle_number)
            
            # Step 3: Pre-filter content (if not already filtered)
            entries_to_add = []
            entries_filtered = 0
            
            if self.content_curator and all_entries:
                filtered_entries, rejected_entries = self.content_curator.pre_filter_content(all_entries)
                entries_to_add = filtered_entries
                entries_filtered = len(rejected_entries)
                
                # Track rejected entries
                for rejected in rejected_entries:
                    if self.rss_fetch_history and cycle_id:
                        self.rss_fetch_history.add_fetch_item(
                            cycle_id=cycle_id,
                            title=rejected.get("title", ""),
                            source_url=rejected.get("source", ""),
                            link=rejected.get("link", ""),
                            summary=rejected.get("summary", ""),
                            status="Filtered: Low Score",
                            status_reason=rejected.get("rejection_reason", "Low quality/Short content")
                        )
            else:
                entries_to_add = all_entries
            
            # Step 4: Add to RAG (if enabled)
            entries_added_to_rag = 0
            if self.auto_add_to_rag and self.rag_retrieval and entries_to_add:
                logger.info(f"📚 Adding {len(entries_to_add)} entries to RAG...")
                
                for entry in entries_to_add:
                    try:
                        # Check for duplicate before adding
                        is_duplicate = False
                        entry_link = entry.get("link", "")
                        if entry_link and self.rag_retrieval:
                            try:
                                is_duplicate = self.rag_retrieval.check_duplicate_by_link(entry_link)
                            except Exception:
                                pass  # If check fails, assume not duplicate
                        
                        # Calculate freshness score (0.0-1.0, higher = newer)
                        freshness_score = 0.0
                        published = entry.get("published", "")
                        if published:
                            try:
                                # Try parsing with dateutil if available, otherwise use simple parsing
                                try:
                                    from dateutil.parser import parse as parse_date
                                    from datetime import timezone, timedelta
                                    tzinfos = {
                                        "UTC": timezone.utc,
                                        "GMT": timezone.utc,
                                        "UT": timezone.utc,
                                        "EST": timezone(timedelta(hours=-5)),
                                        "EDT": timezone(timedelta(hours=-4)),
                                        "CST": timezone(timedelta(hours=-6)),
                                        "CDT": timezone(timedelta(hours=-5)),
                                        "MST": timezone(timedelta(hours=-7)),
                                        "MDT": timezone(timedelta(hours=-6)),
                                        "PST": timezone(timedelta(hours=-8)),
                                        "PDT": timezone(timedelta(hours=-7)),
                                    }
                                    pub_date = parse_date(published, tzinfos=tzinfos)
                                    # Handle timezone-aware dates
                                    if pub_date.tzinfo:
                                        from datetime import timezone
                                        now = datetime.now(timezone.utc)
                                        pub_date_naive = pub_date.astimezone(timezone.utc).replace(tzinfo=None)
                                        now_naive = now.replace(tzinfo=None)
                                        age_days = (now_naive - pub_date_naive).days
                                    else:
                                        age_days = (datetime.now() - pub_date).days
                                except ImportError:
                                    # Fallback: simple ISO format parsing
                                    from datetime import datetime as dt
                                    try:
                                        pub_date = dt.fromisoformat(published.replace('Z', '+00:00'))
                                        if pub_date.tzinfo:
                                            now = datetime.now(pub_date.tzinfo)
                                            age_days = (now.replace(tzinfo=None) - pub_date.replace(tzinfo=None)).days
                                        else:
                                            age_days = (datetime.now() - pub_date).days
                                    except (ValueError, AttributeError):
                                        # Last resort: try basic string parsing
                                        age_days = 999  # Unknown age, use low freshness
                                
                                # Calculate freshness score based on age
                                if age_days < 1:
                                    freshness_score = 1.0
                                elif age_days < 7:
                                    freshness_score = 0.7
                                elif age_days < 30:
                                    freshness_score = 0.3
                                else:
                                    freshness_score = 0.1
                            except Exception as e:
                                logger.debug(f"Failed to parse published date '{published}': {e}")
                                freshness_score = 0.0  # If parsing fails, use 0.0
                        
                        # Track quality metrics for feed
                        feed_url = entry.get("source", "")
                        importance_score = entry.get("importance_score", 0.5)
                        if feed_url:
                            try:
                                from backend.services.feed_health_monitor import get_feed_health_monitor
                                health_monitor = get_feed_health_monitor()
                                health_monitor.track_feed_quality(
                                    feed_url=feed_url,
                                    importance_score=importance_score,
                                    is_duplicate=is_duplicate,
                                    freshness=freshness_score
                                )
                            except Exception as e:
                                logger.debug(f"Failed to track feed quality: {e}")
                        
                        # Skip if duplicate
                        if is_duplicate:
                            if self.rss_fetch_history and cycle_id:
                                self.rss_fetch_history.add_fetch_item(
                                    cycle_id=cycle_id,
                                    title=entry.get("title", ""),
                                    source_url=feed_url,
                                    link=entry_link,
                                    summary=entry.get("summary", ""),
                                    status="Filtered: Duplicate",
                                    status_reason=f"Content already exists in RAG ({duplicate_reason})"
                                )
                            # Track duplicate for quality metrics
                            if feed_url:
                                try:
                                    from backend.services.feed_health_monitor import get_feed_health_monitor
                                    health_monitor = get_feed_health_monitor()
                                    health_monitor.track_feed_quality(
                                        feed_url=feed_url,
                                        importance_score=importance_score,
                                        is_duplicate=True,
                                        freshness=freshness_score
                                    )
                                except Exception:
                                    pass
                            continue
                        
                        # Add to RAG
                        success = self.rag_retrieval.add_learning_content(
                            content=entry.get("summary", ""),
                            source=feed_url,
                            content_type="knowledge",
                            metadata={
                                "title": entry.get("title", ""),
                                "link": entry_link,
                                "published": published,
                                "source_type": entry.get("source_type", "rss"),
                                "importance_score": importance_score
                            }
                        )
                        
                        if success:
                            entries_added_to_rag += 1
                            
                            # Track in history
                            if self.rss_fetch_history and cycle_id:
                                self.rss_fetch_history.add_fetch_item(
                                    cycle_id=cycle_id,
                                    title=entry.get("title", ""),
                                    source_url=feed_url,
                                    link=entry_link,
                                    summary=entry.get("summary", ""),
                                    status="Added to RAG",
                                    vector_id=f"knowledge_{entry_link[:8] if entry_link else 'unknown'}",
                                    added_to_rag_at=datetime.now().isoformat()
                                )
                    except Exception as add_error:
                        logger.error(f"Error adding entry to RAG: {add_error}")
                        # Track error in history
                        if self.rss_fetch_history and cycle_id:
                            self.rss_fetch_history.add_fetch_item(
                                cycle_id=cycle_id,
                                title=entry.get("title", ""),
                                source_url=entry.get("source", ""),
                                link=entry.get("link", ""),
                                summary=entry.get("summary", ""),
                                status="Error: Failed to add",
                                status_reason=str(add_error)
                            )
                
                logger.info(f"✅ Added {entries_added_to_rag} entries to RAG")
            
            # Update cycle count and timestamps
            self.cycle_count = cycle_number
            self.last_run_time = datetime.now()
            self.next_run_time = self.last_run_time + timedelta(hours=self.interval_hours)
            
            processing_time = (datetime.now() - start_time).total_seconds()
            
            result = {
                "cycle_number": cycle_number,
                "entries_fetched": entries_fetched,
                "entries_filtered": entries_filtered,
                "entries_added_to_rag": entries_added_to_rag,
                "processing_time_seconds": processing_time,
                "timestamp": self.last_run_time.isoformat(),
                "next_run": self.next_run_time.isoformat() if self.next_run_time else None,
                "status": "success"
            }
            
            logger.info(f"✅ Learning cycle #{cycle_number} completed: {entries_added_to_rag} entries added to RAG in {processing_time:.2f}s")
            
            # P3: Increment knowledge version after learning cycle (for cache invalidation)
            if entries_added_to_rag > 0:
                try:
                    from backend.services.knowledge_version import increment_knowledge_version
                    new_version = increment_knowledge_version()
                    logger.info(f"📦 P3: Knowledge version incremented to {new_version} after learning cycle (cache will auto-invalidate)")
                except Exception as e:
                    logger.warning(f"Failed to increment knowledge version: {e}")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Error in learning cycle #{cycle_number}: {e}", exc_info=True)
            
            # Record error in unified metrics
            try:
                from stillme_core.monitoring import get_metrics_collector, MetricCategory
                unified_metrics = get_metrics_collector()
                unified_metrics.record_learning_cycle(
                    cycle_number=cycle_number,
                    entries_fetched=0,
                    entries_added=0,
                    entries_filtered=0,
                    sources={},
                    duration_seconds=(datetime.now() - start_time).total_seconds(),
                    error=str(e)
                )
            except Exception as metrics_error:
                logger.debug(f"Failed to record learning error metrics: {metrics_error}")
            
            # Don't increment cycle count on error
            return {
                "cycle_number": 0,  # 0 indicates error
                "entries_fetched": 0,
                "entries_filtered": 0,
                "entries_added_to_rag": 0,
                "processing_time_seconds": (datetime.now() - start_time).total_seconds(),
                "timestamp": datetime.now().isoformat(),
                "next_run": None,
                "status": "error",
                "error": str(e)
            }
    
    async def _scheduler_loop(self):
        """
        Main scheduler loop that runs learning cycles every interval_hours.
        CRITICAL: This is the core learning functionality - must run continuously.
        """
        logger.info(f"🚀 Learning scheduler started - will run every {self.interval_hours} hours")
        
        # Run first cycle immediately
        await self.run_learning_cycle()
        
        while self.is_running:
            try:
                # Wait for next interval
                wait_seconds = self.interval_hours * 3600
                logger.info(f"⏳ Waiting {self.interval_hours} hours until next learning cycle...")
                logger.info(f"🔍 Scheduler loop: is_running={self.is_running}, wait_seconds={wait_seconds}, next_run_time={self.next_run_time.isoformat() if self.next_run_time else 'N/A'}")
                
                # Use stop event to allow immediate cancellation
                try:
                    await asyncio.wait_for(
                        self._stop_event.wait(),
                        timeout=wait_seconds
                    )
                    # Stop event was set - scheduler is stopping
                    logger.info("🛑 Learning scheduler stop event received")
                    break
                except asyncio.TimeoutError:
                    # Timeout means we should run the next cycle
                    logger.info(f"⏰ Wait timeout reached - time to run next learning cycle (waited {wait_seconds}s)")
                    pass
                
                # CRITICAL: Check is_running again after wait (may have changed)
                if not self.is_running:
                    logger.warning("⚠️ Scheduler is_running is False after wait - stopping loop")
                    break
                
                logger.info("🔄 Scheduler loop: About to run next learning cycle...")
                await self.run_learning_cycle()
                logger.info("✅ Scheduler loop: Learning cycle completed, continuing loop...")
                    
            except asyncio.CancelledError:
                logger.info("🛑 Learning scheduler task cancelled")
                break
            except Exception as e:
                logger.error(f"❌ Error in scheduler loop: {e}", exc_info=True)
                # Wait a bit before retrying to avoid tight error loops
                logger.warning(f"⏳ Waiting 60s before retrying scheduler loop after error...")
                await asyncio.sleep(60)
                # Continue loop (don't break) to keep scheduler running
                logger.info("🔄 Scheduler loop: Retrying after error...")
        
        logger.warning(f"⚠️ Scheduler loop exited. is_running={self.is_running}")
    
    async def _proactive_health_check_loop(self):
        """
        Proactive health check loop (Phase 3.2)
        Tests 1-2 feeds every 30 minutes between learning cycles
        """
        logger.info("🔍 Proactive health check loop started - will test feeds every 30 minutes")
        
        while self.is_running:
            try:
                # Wait 30 minutes between checks
                await asyncio.sleep(30 * 60)  # 30 minutes
                
                if not self.is_running:
                    break
                
                # Get list of feeds to test (1-2 random feeds)
                if not self.rss_fetcher or not self.rss_fetcher.feeds:
                    logger.debug("No feeds available for proactive health check")
                    continue
                
                import random
                feeds_to_test = random.sample(
                    self.rss_fetcher.feeds,
                    min(2, len(self.rss_fetcher.feeds))
                )
                
                logger.info(f"🔍 Proactive health check: Testing {len(feeds_to_test)} feed(s)")
                
                # Test each feed
                for feed_url in feeds_to_test:
                    try:
                        # Use RSSFetcher's fetch method directly (simpler approach)
                        from backend.services.feed_health_monitor import get_feed_health_monitor
                        import feedparser
                        import time
                        
                        health_monitor = get_feed_health_monitor()
                        
                        # Simple fetch test (without full circuit breaker complexity)
                        start_time = time.time()
                        try:
                            feed_result = feedparser.parse(feed_url)
                            response_time = time.time() - start_time
                            
                            # Check if fetch was successful
                            if feed_result and not feed_result.bozo:
                                health_monitor.record_success(feed_url, response_time=response_time)
                                logger.debug(f"✅ Proactive check: {feed_url[:50]}... is healthy (response: {response_time:.2f}s)")
                            else:
                                error_msg = feed_result.bozo_exception if feed_result and feed_result.bozo else "Parse error"
                                health_monitor.record_failure(feed_url, f"Proactive check: {error_msg}")
                                logger.debug(f"⚠️ Proactive check: {feed_url[:50]}... failed: {error_msg}")
                        except Exception as fetch_error:
                            response_time = time.time() - start_time
                            health_monitor.record_failure(feed_url, f"Proactive check error: {str(fetch_error)}")
                            logger.debug(f"⚠️ Proactive check: {feed_url[:50]}... error: {fetch_error}")
                    except Exception as e:
                        logger.debug(f"Proactive health check error for {feed_url[:50]}: {e}")
                        from backend.services.feed_health_monitor import get_feed_health_monitor
                        health_monitor = get_feed_health_monitor()
                        health_monitor.record_failure(feed_url, f"Proactive check error: {str(e)}")
                
            except asyncio.CancelledError:
                logger.info("🛑 Proactive health check task cancelled")
                break
            except Exception as e:
                logger.warning(f"Error in proactive health check loop: {e}")
                # Wait a bit before retrying
                await asyncio.sleep(60)
        
        logger.info("🔍 Proactive health check loop exited")
    
    async def start(self):
        """
        Start the learning scheduler.
        CRITICAL: This must be called to enable automatic learning.
        """
        if self.is_running:
            logger.warning("⚠️ Learning scheduler is already running")
            return
        
        if not self.rag_retrieval:
            logger.error("❌ Cannot start scheduler: RAG retrieval not set. Call set_rag_retrieval() first.")
            raise ValueError("RAG retrieval not set")
        
        self.is_running = True
        self._stop_event.clear()
        
        # Cancel old task if it exists (shouldn't happen, but defensive)
        if self._task and not self._task.done():
            logger.warning("⚠️ Cancelling existing scheduler task before starting new one")
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        
        self._task = asyncio.create_task(self._scheduler_loop())
        
        # Add done callback to detect if task dies unexpectedly
        def task_done_callback(task):
            if task.cancelled():
                logger.warning("⚠️ Scheduler task was cancelled")
                # CRITICAL: Reset is_running when task is cancelled (e.g., during shutdown)
                if self.is_running:
                    logger.info("🔄 Resetting is_running=False due to task cancellation (allows watchdog to restart)")
                    self.is_running = False
            elif task.exception():
                logger.error(f"❌ Scheduler task died with exception: {task.exception()}", exc_info=task.exception())
                # Reset is_running on exception so watchdog can restart
                if self.is_running:
                    logger.info("🔄 Resetting is_running=False due to task exception (allows watchdog to restart)")
                    self.is_running = False
            else:
                logger.warning("⚠️ Scheduler task completed unexpectedly (should run forever)")
                # Reset is_running on unexpected completion
                if self.is_running:
                    logger.info("🔄 Resetting is_running=False due to unexpected completion (allows watchdog to restart)")
                    self.is_running = False
        
        self._task.add_done_callback(task_done_callback)
        
        # Start proactive health check task (Phase 3.2)
        self._proactive_health_task = asyncio.create_task(self._proactive_health_check_loop())
        
        logger.info(f"✅ Learning scheduler started - will run every {self.interval_hours} hours")
        logger.info("✅ Proactive health check started - will test feeds every 30 minutes")
    
    async def stop(self):
        """Stop the learning scheduler"""
        if not self.is_running:
            logger.warning("⚠️ Learning scheduler is not running")
            return
        
        self.is_running = False
        self._stop_event.set()
        
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        
        # Stop proactive health check task (Phase 3.2)
        if self._proactive_health_task:
            self._proactive_health_task.cancel()
            try:
                await self._proactive_health_task
            except asyncio.CancelledError:
                pass
        
        self._task = None
        self._proactive_health_task = None
        logger.info("🛑 Learning scheduler stopped")
    
    def get_status(self) -> Dict[str, Any]:
        """Get current scheduler status"""
        return {
            "is_running": self.is_running,
            "cycle_count": self.cycle_count,
            "interval_hours": self.interval_hours,
            "auto_add_to_rag": self.auto_add_to_rag,
            "last_run_time": self.last_run_time.isoformat() if self.last_run_time else None,
            "next_run_time": self.next_run_time.isoformat() if self.next_run_time else None,
            "has_rag_retrieval": self.rag_retrieval is not None,
            "has_source_integration": self.source_integration is not None,
            "has_content_curator": self.content_curator is not None
        }

