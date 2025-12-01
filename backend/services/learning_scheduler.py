"""
Learning Scheduler Service for StillMe
Automatically runs learning cycles every N hours to fetch content and add to RAG
CRITICAL: This is a core feature - must always be enabled and running
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
            from backend.services.rss_fetcher import RSSFetcher
            rss_fetcher = RSSFetcher()
        
        if source_integration is None:
            from backend.services.source_integration import SourceIntegration
            from backend.services.content_curator import ContentCurator
            content_curator = content_curator or ContentCurator()
            source_integration = SourceIntegration(content_curator=content_curator)
        
        if content_curator is None:
            from backend.services.content_curator import ContentCurator
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
                        # Add to RAG
                        success = self.rag_retrieval.add_learning_content(
                            content=entry.get("summary", ""),
                            source=entry.get("source", "unknown"),
                            content_type="knowledge",
                            metadata={
                                "title": entry.get("title", ""),
                                "link": entry.get("link", ""),
                                "published": entry.get("published", ""),
                                "source_type": entry.get("source_type", "rss")
                            }
                        )
                        
                        if success:
                            entries_added_to_rag += 1
                            
                            # Track in history
                            if self.rss_fetch_history and cycle_id:
                                self.rss_fetch_history.add_fetch_item(
                                    cycle_id=cycle_id,
                                    title=entry.get("title", ""),
                                    source_url=entry.get("source", ""),
                                    link=entry.get("link", ""),
                                    summary=entry.get("summary", ""),
                                    status="Added to RAG",
                                    vector_id=f"knowledge_{entry.get('link', '')[:8]}",
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
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Error in learning cycle #{cycle_number}: {e}", exc_info=True)
            
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
            elif task.exception():
                logger.error(f"❌ Scheduler task died with exception: {task.exception()}", exc_info=task.exception())
            else:
                logger.warning("⚠️ Scheduler task completed unexpectedly (should run forever)")
            # If task died but is_running is still True, that's a bug
            if self.is_running:
                logger.error("❌ CRITICAL: Scheduler task died but is_running=True - scheduler will not continue!")
        
        self._task.add_done_callback(task_done_callback)
        
        logger.info(f"✅ Learning scheduler started - will run every {self.interval_hours} hours")
    
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
        
        self._task = None
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

