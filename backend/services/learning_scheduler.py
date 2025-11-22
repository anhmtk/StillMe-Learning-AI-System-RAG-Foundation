"""
Automated Learning Scheduler for StillMe
Handles periodic RSS fetching and automatic learning cycles
Supports multi-timescale tasks (hourly/daily/weekly/monthly) for Continuum Memory
"""

import asyncio
import logging
import os
from datetime import datetime, timedelta
from typing import Optional
from backend.services.rss_fetcher import RSSFetcher

logger = logging.getLogger(__name__)

# Feature flag check
ENABLE_CONTINUUM_MEMORY = os.getenv("ENABLE_CONTINUUM_MEMORY", "false").lower() == "true"

class LearningScheduler:
    """Automated scheduler for RSS learning cycles with multi-timescale support"""
    
    def __init__(self, 
                 rss_fetcher: Optional[RSSFetcher] = None,
                 interval_hours: int = 4,
                 auto_add_to_rag: bool = True,
                 continuum_memory=None):
        """Initialize scheduler
        
        Args:
            rss_fetcher: RSSFetcher instance (optional, will create if None)
            interval_hours: Hours between learning cycles (default: 4)
            auto_add_to_rag: Whether to automatically add fetched content to RAG
            continuum_memory: ContinuumMemory instance (optional, for tier management)
        """
        self.rss_fetcher = rss_fetcher or RSSFetcher()
        self.interval_hours = interval_hours
        self.auto_add_to_rag = auto_add_to_rag
        self.continuum_memory = continuum_memory
        self.is_running = False
        self.last_run_time: Optional[datetime] = None
        self.next_run_time: Optional[datetime] = None
        self.cycle_count = 0
        self._task: Optional[asyncio.Task] = None
        self._multi_timescale_task: Optional[asyncio.Task] = None
        
        # Multi-timescale task tracking
        self._last_hourly_run: Optional[datetime] = None
        self._last_daily_run: Optional[datetime] = None
        self._last_weekly_run: Optional[datetime] = None
        self._last_monthly_run: Optional[datetime] = None
        
        logger.info(f"LearningScheduler initialized: interval={interval_hours}h, auto_add={auto_add_to_rag}")
    
    async def run_learning_cycle(self, use_multi_source: bool = True):
        """Execute one learning cycle: fetch from all sources and optionally add to RAG
        
        Args:
            use_multi_source: If True, use SourceIntegration (RSS + arXiv + CrossRef + Wikipedia)
                             If False, use only RSS (backward compatibility)
        """
        import time
        start_time = time.time()
        
        try:
            logger.info(f"🚀 Starting learning cycle #{self.cycle_count + 1}")
            self.last_run_time = datetime.now()
            
            # Fetch from sources
            if use_multi_source:
                # Try to use SourceIntegration if available (will be injected from main.py)
                # For now, fallback to RSS only
                entries = self.rss_fetcher.fetch_feeds(max_items_per_feed=5)
                logger.info(f"✅ Fetched {len(entries)} entries from RSS feeds (multi-source integration in main.py)")
            else:
                # RSS only
                entries = self.rss_fetcher.fetch_feeds(max_items_per_feed=5)
                logger.info(f"✅ Fetched {len(entries)} entries from RSS feeds")
            
            # If auto_add_to_rag is enabled, actually process entries and add to RAG
            entries_added = 0
            entries_filtered = 0
            if self.auto_add_to_rag:
                logger.info(f"📦 Auto-add to RAG enabled - {len(entries)} entries ready for processing")
                
                # Import services from main module (avoid circular imports)
                try:
                    import backend.api.main as main_module
                    rag_retrieval = main_module.rag_retrieval
                    source_integration = main_module.source_integration
                    content_curator = main_module.content_curator
                    rss_fetch_history = main_module.rss_fetch_history
                    
                    if not rag_retrieval:
                        logger.warning("⚠️ RAG retrieval not available, skipping RAG processing")
                    else:
                        # Create fetch cycle for tracking
                        cycle_id = None
                        if rss_fetch_history:
                            cycle_id = rss_fetch_history.create_fetch_cycle(cycle_number=self.cycle_count + 1)
                        
                        # Fetch from all sources if available
                        all_entries = []
                        if source_integration:
                            logger.info("📡 Fetching from all sources (RSS + arXiv + CrossRef + Wikipedia)...")
                            all_entries = source_integration.fetch_all_sources(
                                max_items_per_source=5,
                                use_pre_filter=False  # We'll apply pre-filter manually to track rejected items
                            )
                            logger.info(f"✅ Fetched {len(all_entries)} entries from all sources")
                        else:
                            all_entries = entries
                            logger.info(f"📡 Using {len(all_entries)} entries from RSS (SourceIntegration not available)")
                        
                        # STEP 1: Pre-Filter (BEFORE embedding) to reduce costs
                        filtered_entries = all_entries
                        if content_curator:
                            logger.info("🔍 Applying pre-filter to reduce embedding costs...")
                            filtered_entries, rejected_entries = content_curator.pre_filter_content(all_entries)
                            entries_filtered = len(rejected_entries)
                            logger.info(
                                f"✅ Pre-Filter: {len(filtered_entries)}/{len(all_entries)} passed. "
                                f"Rejected {entries_filtered} items (saving embedding costs)"
                            )
                        else:
                            logger.warning("⚠️ Content curator not available, skipping pre-filter (may increase costs)")
                        
                        # STEP 2: Process entries and add to RAG with detailed progress tracking
                        total_to_process = len(filtered_entries)
                        logger.info(f"🔄 Starting RAG processing for {total_to_process} entries...")
                        
                        batch_size = 20  # Increased batch size for better performance (was 10)
                        for batch_idx in range(0, total_to_process, batch_size):
                            batch = filtered_entries[batch_idx:batch_idx + batch_size]
                            batch_num = (batch_idx // batch_size) + 1
                            total_batches = (total_to_process + batch_size - 1) // batch_size
                            
                            logger.info(
                                f"📊 Processing batch {batch_num}/{total_batches}: "
                                f"{len(batch)} items ({batch_idx + 1}-{min(batch_idx + batch_size, total_to_process)}/{total_to_process})"
                            )
                            
                            for entry_idx, entry in enumerate(batch):
                                try:
                                    content = f"{entry.get('title', '')}\n{entry.get('summary', '')}"
                                    if not content.strip():
                                        logger.warning(f"⚠️ Skipping empty entry: {entry.get('title', 'No title')}")
                                        continue
                                    
                                    # Check for duplicates
                                    is_duplicate = False
                                    try:
                                        existing = rag_retrieval.retrieve_context(
                                            query=entry.get('title', ''),
                                            knowledge_limit=1,
                                            conversation_limit=0
                                        )
                                        if existing.get("knowledge_docs"):
                                            existing_doc = existing["knowledge_docs"][0]
                                            existing_metadata = existing_doc.get("metadata", {})
                                            if existing_metadata.get("link", "") == entry.get("link", ""):
                                                is_duplicate = True
                                    except Exception:
                                        pass
                                    
                                    if is_duplicate:
                                        logger.debug(f"⏭️ Skipping duplicate: {entry.get('title', '')[:50]}")
                                        continue
                                    
                                    # Calculate importance score
                                    importance_score = 0.5
                                    if content_curator:
                                        importance_score = content_curator.calculate_importance_score(entry)
                                    
                                    # Add to RAG (this triggers embedding generation and ChromaDB insertion)
                                    logger.debug(
                                        f"🔧 Generating embedding and adding to ChromaDB: "
                                        f"{entry.get('title', 'No title')[:50]}"
                                    )
                                    
                                    success = rag_retrieval.add_learning_content(
                                        content=content,
                                        source=entry.get('source', 'rss'),
                                        content_type="knowledge",
                                        metadata={
                                            "link": entry.get('link', ''),
                                            "published": entry.get('published', ''),
                                            "type": "rss_feed",
                                            "scheduler_cycle": self.cycle_count + 1,
                                            "priority_score": entry.get("priority_score", 0.5),
                                            "importance_score": importance_score,
                                            "title": entry.get('title', '')[:200]
                                        }
                                    )
                                    
                                    if success:
                                        entries_added += 1
                                        logger.info(
                                            f"✅ ChromaDB: Inserted document {entries_added}/{total_to_process} "
                                            f"({entries_added * 100 // total_to_process if total_to_process > 0 else 0}% complete) - "
                                            f"{entry.get('title', 'No title')[:50]}"
                                        )
                                        
                                        # Track in fetch history
                                        # Note: vector_id here is a temporary tracking ID, not the actual ChromaDB vector ID
                                        # The actual ChromaDB ID is generated in add_learning_content() with format: knowledge_<uuid>
                                        if rss_fetch_history and cycle_id:
                                            # Generate a proper tracking ID (not the actual ChromaDB vector ID)
                                            import uuid
                                            tracking_id = f"knowledge_{uuid.uuid4().hex[:8]}"
                                            rss_fetch_history.add_fetch_item(
                                                cycle_id=cycle_id,
                                                title=entry.get("title", ""),
                                                source_url=entry.get("source", ""),
                                                link=entry.get("link", ""),
                                                summary=entry.get("summary", ""),
                                                status="Added to RAG",
                                                vector_id=tracking_id,  # Temporary tracking ID, actual ChromaDB ID is different
                                                added_to_rag_at=datetime.now().isoformat()
                                            )
                                    else:
                                        logger.warning(f"❌ Failed to add entry to RAG: {entry.get('title', 'No title')[:50]}")
                                        
                                except Exception as e:
                                    logger.error(f"❌ Error processing entry: {e}")
                                    continue
                            
                            # Log batch completion
                            logger.info(
                                f"✅ Batch {batch_num}/{total_batches} completed: "
                                f"{entries_added} entries added so far (running total: {entries_added}/{total_to_process})"
                            )
                        
                        # Complete fetch cycle
                        if rss_fetch_history and cycle_id:
                            rss_fetch_history.complete_fetch_cycle(cycle_id)
                        
                        processing_time = time.time() - start_time
                        logger.info(
                            f"✅ RAG processing completed: {entries_added}/{total_to_process} entries processed successfully "
                            f"({entries_filtered} filtered, {total_to_process - entries_added - entries_filtered} failed/skipped) "
                            f"in {processing_time:.2f}s"
                        )
                        
                except Exception as e:
                    logger.error(f"❌ Error in RAG processing: {e}", exc_info=True)
                    # Continue with cycle completion even if RAG processing fails
            
            self.cycle_count += 1
            self.next_run_time = datetime.now() + timedelta(hours=self.interval_hours)
            
            total_time = time.time() - start_time
            logger.info(
                f"✅ Learning cycle #{self.cycle_count} completed in {total_time:.2f}s. "
                f"Next run: {self.next_run_time}"
            )
            
            # CRITICAL: Record learning metrics for dashboard/statistics
            try:
                from backend.services.learning_metrics_tracker import get_learning_metrics_tracker
                
                # Aggregate filter reasons (simplified - can be enhanced)
                filter_reasons = {
                    "Low quality/Short content": entries_filtered,
                    "Duplicate": 0  # Can be enhanced to track actual duplicates
                }
                
                # Aggregate sources (use source_integration if available)
                sources = {}
                try:
                    import backend.api.main as main_module
                    source_integration = main_module.source_integration
                    if source_integration:
                        # Try to get source breakdown from source_integration
                        sources = {
                            "rss": len(entries),
                            "arxiv": 0,  # Can be enhanced to track actual source breakdown
                            "crossref": 0,
                            "wikipedia": 0
                        }
                    else:
                        sources = {"rss": len(entries)}
                except Exception:
                    sources = {"rss": len(entries)}
                
                tracker = get_learning_metrics_tracker()
                tracker.record_learning_cycle(
                    cycle_number=self.cycle_count,
                    entries_fetched=len(entries),
                    entries_added=entries_added if self.auto_add_to_rag else 0,
                    entries_filtered=entries_filtered if self.auto_add_to_rag else 0,
                    filter_reasons=filter_reasons,
                    sources=sources,
                    duration_seconds=total_time
                )
                logger.info(f"📊 Learning metrics recorded for cycle #{self.cycle_count}")
            except Exception as metrics_error:
                logger.warning(f"⚠️ Failed to record learning metrics: {metrics_error}")
            
            return {
                "cycle_number": self.cycle_count,
                "entries_fetched": len(entries),
                "entries_added_to_rag": entries_added if self.auto_add_to_rag else 0,
                "entries_filtered": entries_filtered if self.auto_add_to_rag else 0,
                "timestamp": self.last_run_time.isoformat(),
                "next_run": self.next_run_time.isoformat(),
                "processing_time_seconds": total_time
            }
            
        except Exception as e:
            logger.error(f"❌ Error in learning cycle: {e}", exc_info=True)
            return {
                "cycle_number": self.cycle_count,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    async def _scheduler_loop(self):
        """Main scheduler loop - runs continuously"""
        logger.info(f"Scheduler started. Interval: {self.interval_hours} hours")
        
        while self.is_running:
            try:
                # Run learning cycle
                await self.run_learning_cycle()
                
                # Wait for next interval
                wait_seconds = self.interval_hours * 3600
                logger.info(f"Waiting {self.interval_hours} hours until next cycle...")
                await asyncio.sleep(wait_seconds)
                
            except asyncio.CancelledError:
                logger.info("Scheduler loop cancelled")
                break
            except Exception as e:
                logger.error(f"Error in scheduler loop: {e}")
                # Wait a bit before retrying
                await asyncio.sleep(60)
    
    async def start(self):
        """Start the scheduler"""
        if self.is_running:
            logger.warning("Scheduler is already running")
            return
        
        self.is_running = True
        self._task = asyncio.create_task(self._scheduler_loop())
        
        # Start multi-timescale scheduler if Continuum Memory is enabled
        if ENABLE_CONTINUUM_MEMORY and self.continuum_memory:
            self._multi_timescale_task = asyncio.create_task(self._multi_timescale_loop())
            logger.info("Multi-timescale scheduler started")
        
        logger.info("Scheduler started successfully")
    
    async def stop(self):
        """Stop the scheduler"""
        if not self.is_running:
            logger.warning("Scheduler is not running")
            return
        
        self.is_running = False
        
        # Stop main scheduler loop
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        
        # Stop multi-timescale scheduler
        if self._multi_timescale_task:
            self._multi_timescale_task.cancel()
            try:
                await self._multi_timescale_task
            except asyncio.CancelledError:
                pass
        
        logger.info("Scheduler stopped")
    
    async def _multi_timescale_loop(self):
        """Multi-timescale scheduler loop for Continuum Memory tasks"""
        logger.info("Multi-timescale scheduler loop started")
        
        while self.is_running:
            try:
                now = datetime.now()
                
                # Hourly: Update L0 metrics + rebuild mini-index
                if (self._last_hourly_run is None or 
                    (now - self._last_hourly_run).total_seconds() >= 3600):
                    await self._run_hourly_tasks()
                    self._last_hourly_run = now
                
                # Daily: Recompute surprise + promotion/demotion L0↔L1
                if (self._last_daily_run is None or 
                    (now - self._last_daily_run).total_seconds() >= 86400):
                    await self._run_daily_tasks()
                    self._last_daily_run = now
                
                # Weekly: Compact/re-embed L1, check demote
                if (self._last_weekly_run is None or 
                    (now - self._last_weekly_run).total_seconds() >= 604800):
                    await self._run_weekly_tasks()
                    self._last_weekly_run = now
                
                # Monthly: Snapshot L2, rebuild full index, report forgetting
                if (self._last_monthly_run is None or 
                    (now - self._last_monthly_run).total_seconds() >= 2592000):  # ~30 days
                    await self._run_monthly_tasks()
                    self._last_monthly_run = now
                
                # Check every minute
                await asyncio.sleep(60)
                
            except asyncio.CancelledError:
                logger.info("Multi-timescale scheduler loop cancelled")
                break
            except Exception as e:
                logger.error(f"Error in multi-timescale scheduler loop: {e}")
                await asyncio.sleep(60)
    
    async def _run_hourly_tasks(self):
        """Hourly tasks: Update L0 metrics + rebuild mini-index"""
        if not ENABLE_CONTINUUM_MEMORY or not self.continuum_memory:
            return
        
        try:
            logger.info("Running hourly tasks: Update L0 metrics")
            # TODO: Update retrieval_count_7d for L0 items
            # TODO: Rebuild mini-index for L0 tier
            logger.info("Hourly tasks completed")
        except Exception as e:
            logger.error(f"Error in hourly tasks: {e}")
    
    async def _run_daily_tasks(self):
        """Daily tasks: Recompute surprise + promotion/demotion L0↔L1"""
        if not ENABLE_CONTINUUM_MEMORY or not self.continuum_memory:
            return
        
        try:
            logger.info("Running daily tasks: Recompute surprise + promotion/demotion")
            
            # Import PromotionManager
            from backend.learning.promotion_manager import PromotionManager
            promotion_manager = PromotionManager()
            
            # Get all L0 and L1 items
            import sqlite3
            conn = sqlite3.connect(self.continuum_memory.db_path)
            cursor = conn.cursor()
            
            # Get L0 items
            cursor.execute("SELECT item_id FROM tier_metrics WHERE tier = 'L0'")
            l0_items = [row[0] for row in cursor.fetchall()]
            
            # Get L1 items
            cursor.execute("SELECT item_id FROM tier_metrics WHERE tier = 'L1'")
            l1_items = [row[0] for row in cursor.fetchall()]
            
            conn.close()
            
            # Evaluate and promote L0 items
            promoted_count = 0
            for item_id in l0_items:
                result = promotion_manager.evaluate_and_promote(item_id)
                if result:
                    promoted_count += 1
            
            # Evaluate and demote L1 items
            demoted_count = 0
            for item_id in l1_items:
                result = promotion_manager.evaluate_and_demote(item_id)
                if result:
                    demoted_count += 1
            
            logger.info(f"Daily tasks completed: {promoted_count} promoted, {demoted_count} demoted")
        except Exception as e:
            logger.error(f"Error in daily tasks: {e}")
    
    async def _run_weekly_tasks(self):
        """Weekly tasks: Compact/re-embed L1, check demote"""
        if not ENABLE_CONTINUUM_MEMORY or not self.continuum_memory:
            return
        
        try:
            logger.info("Running weekly tasks: Compact/re-embed L1, check demote")
            # TODO: Compact L1 tier (remove expired items)
            # TODO: Re-embed L1 items if needed
            # TODO: Check for L2→L1 demotions
            logger.info("Weekly tasks completed")
        except Exception as e:
            logger.error(f"Error in weekly tasks: {e}")
    
    async def _run_monthly_tasks(self):
        """Monthly tasks: Snapshot L2, rebuild full index, report forgetting"""
        if not ENABLE_CONTINUUM_MEMORY or not self.continuum_memory:
            return
        
        try:
            logger.info("Running monthly tasks: Snapshot L2, rebuild index, report forgetting")
            # TODO: Create snapshot of L2 tier
            # TODO: Rebuild full index
            # TODO: Generate forgetting report
            logger.info("Monthly tasks completed")
        except Exception as e:
            logger.error(f"Error in monthly tasks: {e}")
    
    def get_status(self) -> dict:
        """Get current scheduler status"""
        status = {
            "is_running": self.is_running,
            "interval_hours": self.interval_hours,
            "auto_add_to_rag": self.auto_add_to_rag,
            "cycle_count": self.cycle_count,
            "last_run_time": self.last_run_time.isoformat() if self.last_run_time else None,
            "next_run_time": self.next_run_time.isoformat() if self.next_run_time else None,
            "feeds_configured": len(self.rss_fetcher.feeds) if self.rss_fetcher else 0
        }
        
        # Add multi-timescale status if enabled
        if ENABLE_CONTINUUM_MEMORY:
            status["multi_timescale_enabled"] = True
            status["last_hourly_run"] = self._last_hourly_run.isoformat() if self._last_hourly_run else None
            status["last_daily_run"] = self._last_daily_run.isoformat() if self._last_daily_run else None
            status["last_weekly_run"] = self._last_weekly_run.isoformat() if self._last_weekly_run else None
            status["last_monthly_run"] = self._last_monthly_run.isoformat() if self._last_monthly_run else None
        else:
            status["multi_timescale_enabled"] = False
        
        return status

