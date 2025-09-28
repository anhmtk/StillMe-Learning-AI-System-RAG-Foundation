"""
🕐 StillMe Learning Scheduler
============================

APScheduler wrapper cho tự động hóa học tập của StillMe.
Hỗ trợ cron jobs, interval scheduling, và resource-aware scheduling.

Tính năng:
- Cron-based scheduling với timezone support
- Resource monitoring trước khi chạy
- Jitter để tránh dồn tải
- Graceful shutdown và error handling
- Session tracking và logging

Author: StillMe AI Framework
Version: 2.0.0
Date: 2025-09-28
"""

import asyncio
import logging
import signal
import sys
import time
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, Callable, List
from dataclasses import dataclass
from pathlib import Path
import json

try:
    from apscheduler.schedulers.asyncio import AsyncIOScheduler
    from apscheduler.triggers.cron import CronTrigger
    from apscheduler.triggers.interval import IntervalTrigger
    from apscheduler.events import EVENT_JOB_EXECUTED, EVENT_JOB_ERROR, EVENT_JOB_MISSED
    from apscheduler.jobstores.memory import MemoryJobStore
    from apscheduler.executors.asyncio import AsyncIOExecutor
    APSCHEDULER_AVAILABLE = True
except ImportError:
    APSCHEDULER_AVAILABLE = False
    logging.warning("APScheduler not available. Install with: pip install apscheduler")

logger = logging.getLogger(__name__)

@dataclass
class SchedulerConfig:
    """Cấu hình scheduler"""
    enabled: bool = False
    cron_expression: str = "30 2 * * *"  # 02:30 hàng ngày
    timezone: str = "Asia/Ho_Chi_Minh"
    jitter_seconds: int = 300  # ±5 phút
    max_concurrent_sessions: int = 1
    skip_if_cpu_high: bool = True
    cpu_threshold: float = 70.0
    skip_if_memory_high: bool = True
    memory_threshold_mb: int = 1024
    skip_if_tokens_low: bool = True
    min_tokens_required: int = 1000
    enable_graceful_shutdown: bool = True
    shutdown_timeout: int = 30  # seconds

@dataclass
class ScheduledJob:
    """Thông tin job đã lên lịch"""
    job_id: str
    name: str
    trigger: str
    next_run: Optional[datetime]
    last_run: Optional[datetime]
    status: str  # pending, running, completed, failed, skipped

class LearningScheduler:
    """
    Scheduler cho hệ thống học tập tự động của StillMe
    """
    
    def __init__(self, config: SchedulerConfig = None):
        self.config = config or SchedulerConfig()
        self.logger = logging.getLogger(__name__)
        
        if not APSCHEDULER_AVAILABLE:
            raise ImportError("APScheduler is required but not installed. Run: pip install apscheduler")
        
        # Initialize scheduler
        self.scheduler = None
        self.is_running = False
        self.scheduled_jobs: Dict[str, ScheduledJob] = {}
        self.session_lock = asyncio.Lock()
        
        # Statistics
        self.stats = {
            'total_jobs': 0,
            'successful_jobs': 0,
            'failed_jobs': 0,
            'skipped_jobs': 0,
            'last_run': None,
            'next_run': None
        }
        
        # Setup signal handlers for graceful shutdown
        if self.config.enable_graceful_shutdown:
            self._setup_signal_handlers()
    
    def _setup_signal_handlers(self):
        """Setup signal handlers cho graceful shutdown"""
        def signal_handler(signum, frame):
            self.logger.info(f"Received signal {signum}, initiating graceful shutdown...")
            asyncio.create_task(self.shutdown())
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
    
    async def initialize(self):
        """Khởi tạo scheduler"""
        try:
            # Configure job stores and executors
            jobstores = {
                'default': MemoryJobStore()
            }
            executors = {
                'default': AsyncIOExecutor()
            }
            job_defaults = {
                'coalesce': True,
                'max_instances': self.config.max_concurrent_sessions,
                'misfire_grace_time': 300  # 5 minutes
            }
            
            # Create scheduler
            self.scheduler = AsyncIOScheduler(
                jobstores=jobstores,
                executors=executors,
                job_defaults=job_defaults,
                timezone=self.config.timezone
            )
            
            # Add event listeners
            self.scheduler.add_listener(self._job_executed, EVENT_JOB_EXECUTED)
            self.scheduler.add_listener(self._job_error, EVENT_JOB_ERROR)
            self.scheduler.add_listener(self._job_missed, EVENT_JOB_MISSED)
            
            self.logger.info("Learning scheduler initialized successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize scheduler: {e}")
            return False
    
    async def start(self):
        """Bắt đầu scheduler"""
        if not self.scheduler:
            await self.initialize()
        
        if not self.scheduler:
            raise RuntimeError("Scheduler not initialized")
        
        try:
            self.scheduler.start()
            self.is_running = True
            self.logger.info(f"Scheduler started with timezone: {self.config.timezone}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to start scheduler: {e}")
            return False
    
    async def stop(self):
        """Dừng scheduler"""
        if self.scheduler and self.is_running:
            try:
                self.scheduler.shutdown(wait=True)
                self.is_running = False
                self.logger.info("Scheduler stopped")
                return True
            except Exception as e:
                self.logger.error(f"Failed to stop scheduler: {e}")
                return False
        return True
    
    async def shutdown(self):
        """Graceful shutdown"""
        self.logger.info("Initiating graceful shutdown...")
        
        # Stop accepting new jobs
        if self.scheduler:
            self.scheduler.shutdown(wait=False)
        
        # Wait for current jobs to complete
        timeout = self.config.shutdown_timeout
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            running_jobs = [job for job in self.scheduled_jobs.values() if job.status == 'running']
            if not running_jobs:
                break
            await asyncio.sleep(1)
        
        self.is_running = False
        self.logger.info("Graceful shutdown completed")
    
    async def schedule_daily_training(self, training_function: Callable, **kwargs) -> bool:
        """
        Lên lịch daily training session
        
        Args:
            training_function: Function để chạy training
            **kwargs: Additional arguments cho training function
        
        Returns:
            bool: True nếu lên lịch thành công
        """
        if not self.config.enabled:
            self.logger.warning("Scheduler is disabled")
            return False
        
        try:
            # Parse cron expression
            cron_parts = self.config.cron_expression.split()
            if len(cron_parts) != 5:
                raise ValueError(f"Invalid cron expression: {self.config.cron_expression}")
            
            minute, hour, day, month, day_of_week = cron_parts
            
            # Create cron trigger
            trigger = CronTrigger(
                minute=minute,
                hour=hour,
                day=day,
                month=month,
                day_of_week=day_of_week,
                timezone=self.config.timezone,
                jitter=self.config.jitter_seconds
            )
            
            # Add job
            job = self.scheduler.add_job(
                func=self._wrapped_training_function,
                trigger=trigger,
                args=[training_function, kwargs],
                id='daily_training',
                name='Daily Learning Training',
                replace_existing=True
            )
            
            # Track job
            next_run_time = getattr(job, 'next_run_time', None)
            self.scheduled_jobs['daily_training'] = ScheduledJob(
                job_id='daily_training',
                name='Daily Learning Training',
                trigger=self.config.cron_expression,
                next_run=next_run_time,
                last_run=None,
                status='pending'
            )
            
            self.stats['total_jobs'] += 1
            self.stats['next_run'] = next_run_time
            
            self.logger.info(f"Daily training scheduled: {self.config.cron_expression} ({self.config.timezone})")
            self.logger.info(f"Next run: {next_run_time}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to schedule daily training: {e}")
            return False
    
    async def _wrapped_training_function(self, training_function: Callable, kwargs: Dict[str, Any]):
        """
        Wrapper function cho training với resource checks và error handling
        """
        job_id = 'daily_training'
        start_time = time.time()
        
        try:
            # Update job status
            if job_id in self.scheduled_jobs:
                self.scheduled_jobs[job_id].status = 'running'
                self.scheduled_jobs[job_id].last_run = datetime.now()
            
            self.logger.info(f"Starting scheduled training session: {job_id}")
            
            # Resource checks
            if not await self._check_resources():
                self.logger.warning("Resource checks failed, skipping training session")
                if job_id in self.scheduled_jobs:
                    self.scheduled_jobs[job_id].status = 'skipped'
                self.stats['skipped_jobs'] += 1
                return
            
            # Check for concurrent sessions
            async with self.session_lock:
                # Run training function
                result = await training_function(**kwargs)
                
                # Update statistics
                duration = time.time() - start_time
                self.logger.info(f"Training session completed in {duration:.2f} seconds")
                
                if job_id in self.scheduled_jobs:
                    self.scheduled_jobs[job_id].status = 'completed'
                
                self.stats['successful_jobs'] += 1
                self.stats['last_run'] = datetime.now()
                
                return result
                
        except Exception as e:
            self.logger.error(f"Training session failed: {e}")
            
            if job_id in self.scheduled_jobs:
                self.scheduled_jobs[job_id].status = 'failed'
            
            self.stats['failed_jobs'] += 1
            raise
    
    async def _check_resources(self) -> bool:
        """
        Kiểm tra tài nguyên hệ thống trước khi chạy training
        
        Returns:
            bool: True nếu đủ tài nguyên, False nếu cần skip
        """
        try:
            import psutil
            
            # Check CPU usage
            if self.config.skip_if_cpu_high:
                cpu_percent = psutil.cpu_percent(interval=1)
                if cpu_percent > self.config.cpu_threshold:
                    self.logger.warning(f"CPU usage too high: {cpu_percent:.1f}% > {self.config.cpu_threshold}%")
                    return False
            
            # Check memory usage
            if self.config.skip_if_memory_high:
                memory = psutil.virtual_memory()
                memory_mb = memory.used / (1024 * 1024)
                if memory_mb > self.config.memory_threshold_mb:
                    self.logger.warning(f"Memory usage too high: {memory_mb:.1f}MB > {self.config.memory_threshold_mb}MB")
                    return False
            
            # Check token budget (placeholder - cần implement token tracking)
            if self.config.skip_if_tokens_low:
                # TODO: Implement token budget checking
                pass
            
            return True
            
        except ImportError:
            self.logger.warning("psutil not available, skipping resource checks")
            return True
        except Exception as e:
            self.logger.error(f"Resource check failed: {e}")
            return False
    
    def _job_executed(self, event):
        """Event handler khi job được thực thi thành công"""
        job_id = event.job_id
        self.logger.info(f"Job executed successfully: {job_id}")
    
    def _job_error(self, event):
        """Event handler khi job gặp lỗi"""
        job_id = event.job_id
        exception = event.exception
        self.logger.error(f"Job failed: {job_id}, error: {exception}")
    
    def _job_missed(self, event):
        """Event handler khi job bị miss"""
        job_id = event.job_id
        self.logger.warning(f"Job missed: {job_id}")
    
    def get_status(self) -> Dict[str, Any]:
        """Lấy trạng thái scheduler"""
        return {
            'enabled': self.config.enabled,
            'running': self.is_running,
            'timezone': self.config.timezone,
            'cron_expression': self.config.cron_expression,
            'scheduled_jobs': {job_id: {
                'name': job.name,
                'trigger': job.trigger,
                'next_run': job.next_run.isoformat() if job.next_run else None,
                'last_run': job.last_run.isoformat() if job.last_run else None,
                'status': job.status
            } for job_id, job in self.scheduled_jobs.items()},
            'statistics': self.stats,
            'apscheduler_available': APSCHEDULER_AVAILABLE
        }
    
    def get_next_run_time(self) -> Optional[datetime]:
        """Lấy thời gian chạy tiếp theo"""
        if 'daily_training' in self.scheduled_jobs:
            return self.scheduled_jobs['daily_training'].next_run
        return None
    
    def get_last_run_time(self) -> Optional[datetime]:
        """Lấy thời gian chạy cuối cùng"""
        if 'daily_training' in self.scheduled_jobs:
            return self.scheduled_jobs['daily_training'].last_run
        return None

# Global scheduler instance
_scheduler_instance: Optional[LearningScheduler] = None

def get_learning_scheduler(config: SchedulerConfig = None) -> LearningScheduler:
    """Get global scheduler instance"""
    global _scheduler_instance
    if _scheduler_instance is None:
        _scheduler_instance = LearningScheduler(config)
    return _scheduler_instance

async def initialize_scheduler(config: SchedulerConfig = None) -> LearningScheduler:
    """Initialize và start scheduler"""
    scheduler = get_learning_scheduler(config)
    await scheduler.initialize()
    if config and config.enabled:
        await scheduler.start()
    return scheduler
