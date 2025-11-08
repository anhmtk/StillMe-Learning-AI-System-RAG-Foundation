"""
Automated Learning Scheduler for StillMe
Handles periodic RSS fetching and automatic learning cycles
Supports multi-timescale tasks (hourly/daily/weekly/monthly) for Continuum Memory
"""

import asyncio
import logging
import os
from datetime import datetime, timedelta
from typing import Optional, Callable, Dict, Any
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
        try:
            logger.info(f"Starting learning cycle #{self.cycle_count + 1}")
            self.last_run_time = datetime.now()
            
            # Fetch from sources
            if use_multi_source:
                # Try to use SourceIntegration if available (will be injected from main.py)
                # For now, fallback to RSS only
                entries = self.rss_fetcher.fetch_feeds(max_items_per_feed=5)
                logger.info(f"Fetched {len(entries)} entries from RSS feeds (multi-source integration in main.py)")
            else:
                # RSS only
                entries = self.rss_fetcher.fetch_feeds(max_items_per_feed=5)
                logger.info(f"Fetched {len(entries)} entries from RSS feeds")
            
            # If auto_add_to_rag is enabled, we'll need to call RAG service
            # For now, just log - will integrate with main.py's scheduler endpoint
            if self.auto_add_to_rag:
                logger.info(f"Auto-add to RAG enabled - {len(entries)} entries ready for processing")
                # Note: Actual RAG integration will be done in main.py's scheduler endpoint
            
            self.cycle_count += 1
            self.next_run_time = datetime.now() + timedelta(hours=self.interval_hours)
            
            logger.info(f"Learning cycle #{self.cycle_count} completed. Next run: {self.next_run_time}")
            return {
                "cycle_number": self.cycle_count,
                "entries_fetched": len(entries),
                "timestamp": self.last_run_time.isoformat(),
                "next_run": self.next_run_time.isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error in learning cycle: {e}")
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

