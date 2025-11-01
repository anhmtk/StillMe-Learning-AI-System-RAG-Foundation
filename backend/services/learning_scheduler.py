"""
Automated Learning Scheduler for StillMe
Handles periodic RSS fetching and automatic learning cycles
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Optional
from backend.services.rss_fetcher import RSSFetcher

logger = logging.getLogger(__name__)

class LearningScheduler:
    """Automated scheduler for RSS learning cycles"""
    
    def __init__(self, 
                 rss_fetcher: Optional[RSSFetcher] = None,
                 interval_hours: int = 4,
                 auto_add_to_rag: bool = True):
        """Initialize scheduler
        
        Args:
            rss_fetcher: RSSFetcher instance (optional, will create if None)
            interval_hours: Hours between learning cycles (default: 4)
            auto_add_to_rag: Whether to automatically add fetched content to RAG
        """
        self.rss_fetcher = rss_fetcher or RSSFetcher()
        self.interval_hours = interval_hours
        self.auto_add_to_rag = auto_add_to_rag
        self.is_running = False
        self.last_run_time: Optional[datetime] = None
        self.next_run_time: Optional[datetime] = None
        self.cycle_count = 0
        self._task: Optional[asyncio.Task] = None
        
        logger.info(f"LearningScheduler initialized: interval={interval_hours}h, auto_add={auto_add_to_rag}")
    
    async def run_learning_cycle(self):
        """Execute one learning cycle: fetch RSS and optionally add to RAG"""
        try:
            logger.info(f"Starting learning cycle #{self.cycle_count + 1}")
            self.last_run_time = datetime.now()
            
            # Fetch RSS feeds
            entries = self.rss_fetcher.fetch_feeds(max_items_per_feed=5)
            logger.info(f"Fetched {len(entries)} entries from RSS feeds")
            
            # If auto_add_to_rag is enabled, we'll need to call RAG service
            # For now, just log - will integrate with main.py's rag_retrieval
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
        logger.info("Scheduler started successfully")
    
    async def stop(self):
        """Stop the scheduler"""
        if not self.is_running:
            logger.warning("Scheduler is not running")
            return
        
        self.is_running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        
        logger.info("Scheduler stopped")
    
    def get_status(self) -> dict:
        """Get current scheduler status"""
        return {
            "is_running": self.is_running,
            "interval_hours": self.interval_hours,
            "auto_add_to_rag": self.auto_add_to_rag,
            "cycle_count": self.cycle_count,
            "last_run_time": self.last_run_time.isoformat() if self.last_run_time else None,
            "next_run_time": self.next_run_time.isoformat() if self.next_run_time else None,
            "feeds_configured": len(self.rss_fetcher.feeds) if self.rss_fetcher else 0
        }

