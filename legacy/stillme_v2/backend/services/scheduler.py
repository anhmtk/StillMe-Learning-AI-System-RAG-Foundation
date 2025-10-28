# Learning Scheduler Service
"""
Learning Scheduler Service
Automatically triggers learning sessions at scheduled intervals
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Any, Dict
from sqlalchemy.orm import Session

from ..database.schema import get_direct_db_session
from .evolution_manager import EvolutionManager

logger = logging.getLogger(__name__)


class LearningScheduler:
    """
    Learning Scheduler
    Manages automatic learning session execution
    """
    
    def __init__(self):
        """Initialize Learning Scheduler"""
        self.is_running = False
        self.task = None
        self.interval_minutes = 60  # Run every hour
        self.last_run = None
        
    async def start_scheduler(self):
        """Start the learning scheduler"""
        if self.is_running:
            logger.warning("Scheduler is already running")
            return
            
        self.is_running = True
        logger.info(f"🚀 Starting Learning Scheduler (interval: {self.interval_minutes} minutes)")
        
        # Start background task
        self.task = asyncio.create_task(self._scheduler_loop())
        
    async def stop_scheduler(self):
        """Stop the learning scheduler"""
        if not self.is_running:
            return
            
        self.is_running = False
        if self.task:
            self.task.cancel()
            try:
                await self.task
            except asyncio.CancelledError:
                pass
                
        logger.info("🛑 Learning Scheduler stopped")
        
    async def _scheduler_loop(self):
        """Main scheduler loop"""
        while self.is_running:
            try:
                # Check if it's time to run
                if self._should_run_now():
                    await self._run_learning_session()
                    self.last_run = datetime.now()
                    
                # Wait before next check
                await asyncio.sleep(60)  # Check every minute
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Scheduler loop error: {e}")
                await asyncio.sleep(60)  # Wait before retry
                
    def _should_run_now(self) -> bool:
        """Check if learning session should run now"""
        if not self.last_run:
            return True  # First run
            
        time_since_last = datetime.now() - self.last_run
        return time_since_last >= timedelta(minutes=self.interval_minutes)
        
    async def _run_learning_session(self):
        """Run a learning session"""
        try:
            logger.info("🧠 Triggering automatic learning session...")
            
            # Get database session
            db = get_direct_db_session()
            evolution_manager = EvolutionManager(db)
            
            # Run learning session
            result = evolution_manager.run_daily_learning_session()
            
            logger.info(f"✅ Learning session completed: {result}")
            
        except Exception as e:
            logger.error(f"❌ Learning session failed: {e}")
        finally:
            if 'db' in locals():
                try:
                    db.close()
                except:
                    pass
                
    def get_scheduler_status(self) -> Dict[str, Any]:
        """Get scheduler status"""
        return {
            "is_running": self.is_running,
            "interval_minutes": self.interval_minutes,
            "last_run": self.last_run.isoformat() if self.last_run else None,
            "next_run": self._get_next_run_time(),
            "status": "active" if self.is_running else "stopped"
        }
        
    def _get_next_run_time(self) -> str:
        """Get next scheduled run time"""
        if not self.last_run:
            return "immediately"
            
        next_run = self.last_run + timedelta(minutes=self.interval_minutes)
        return next_run.isoformat()
        
    def set_interval(self, minutes: int):
        """Set scheduler interval"""
        if minutes < 1:
            raise ValueError("Interval must be at least 1 minute")
            
        self.interval_minutes = minutes
        logger.info(f"⏰ Scheduler interval updated to {minutes} minutes")


# Global scheduler instance
learning_scheduler = LearningScheduler()