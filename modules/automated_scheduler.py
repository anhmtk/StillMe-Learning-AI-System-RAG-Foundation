#!/usr/bin/env python3
"""
Automated Scheduler - Tự động chạy daily learning sessions với APScheduler

Author: StillMe AI Framework
Version: 1.0.0
"""

import asyncio
import logging
import signal
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.date import DateTrigger
from apscheduler.jobstores.memory import MemoryJobStore
from apscheduler.executors.asyncio import AsyncIOExecutor
from apscheduler.events import EVENT_JOB_EXECUTED, EVENT_JOB_ERROR, EVENT_JOB_MISSED

@dataclass
class SchedulerConfig:
    """Configuration for automated scheduler"""
    # Daily learning schedule
    daily_learning_time: str = "09:00"  # 9:00 AM daily
    daily_learning_timezone: str = "Asia/Ho_Chi_Minh"
    
    # Weekly analysis schedule
    weekly_analysis_day: int = 0  # Monday (0=Monday, 1=Tuesday, etc.)
    weekly_analysis_time: str = "10:00"  # 10:00 AM
    
    # Monthly improvement schedule
    monthly_improvement_day: int = 1  # 1st of month
    monthly_improvement_time: str = "11:00"  # 11:00 AM
    
    # Health check interval
    health_check_interval: int = 30  # 30 minutes
    
    # Max retry attempts
    max_retry_attempts: int = 3
    
    # Job timeout (seconds)
    job_timeout: int = 3600  # 1 hour

class AutomatedScheduler:
    """Automated scheduler for StillMe learning system"""
    
    def __init__(self, config: Optional[SchedulerConfig] = None):
        self.config = config or SchedulerConfig()
        self.logger = logging.getLogger(__name__)
        self.scheduler = None
        self.framework = None
        self.learning_manager = None
        self.is_running = False
        
        # Job statistics
        self.job_stats = {
            "daily_learning": {"executed": 0, "failed": 0, "last_run": None},
            "weekly_analysis": {"executed": 0, "failed": 0, "last_run": None},
            "monthly_improvement": {"executed": 0, "failed": 0, "last_run": None},
            "health_check": {"executed": 0, "failed": 0, "last_run": None}
        }
        
        # Setup signal handlers
        self._setup_signal_handlers()
        
    def _setup_signal_handlers(self):
        """Setup signal handlers for graceful shutdown"""
        def signal_handler(signum, frame):
            self.logger.info(f"Received signal {signum}, shutting down gracefully...")
            self.stop()
            sys.exit(0)
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
    
    async def initialize(self, framework=None):
        """Initialize scheduler with framework"""
        try:
            self.framework = framework
            
            # Initialize scheduler
            jobstores = {
                'default': MemoryJobStore()
            }
            executors = {
                'default': AsyncIOExecutor()
            }
            job_defaults = {
                'coalesce': True,
                'max_instances': 1,
                'misfire_grace_time': 300  # 5 minutes
            }
            
            self.scheduler = AsyncIOScheduler(
                jobstores=jobstores,
                executors=executors,
                job_defaults=job_defaults,
                timezone=self.config.daily_learning_timezone
            )
            
            # Setup event listeners
            self.scheduler.add_listener(self._job_executed, EVENT_JOB_EXECUTED)
            self.scheduler.add_listener(self._job_error, EVENT_JOB_ERROR)
            self.scheduler.add_listener(self._job_missed, EVENT_JOB_MISSED)
            
            # Initialize learning manager if framework available
            if self.framework:
                await self._initialize_learning_manager()
            
            self.logger.info("✅ AutomatedScheduler initialized successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Failed to initialize scheduler: {e}")
            return False
    
    async def _initialize_learning_manager(self):
        """Initialize learning manager with framework integration"""
        try:
            from modules.daily_learning_manager import DailyLearningManager
            
            # Get managers from framework
            memory_manager = getattr(self.framework, 'layered_memory', None)
            improvement_manager = getattr(self.framework, 'self_improvement_manager', None)
            
            self.learning_manager = DailyLearningManager(
                memory_manager=memory_manager,
                improvement_manager=improvement_manager
            )
            
            self.logger.info("✅ Learning manager initialized with framework integration")
            
        except Exception as e:
            self.logger.error(f"❌ Failed to initialize learning manager: {e}")
            self.learning_manager = None
    
    def _job_executed(self, event):
        """Handle job executed event"""
        job_id = event.job_id
        if job_id in self.job_stats:
            self.job_stats[job_id]["executed"] += 1
            self.job_stats[job_id]["last_run"] = datetime.now().isoformat()
        
        self.logger.info(f"✅ Job executed: {job_id}")
    
    def _job_error(self, event):
        """Handle job error event"""
        job_id = event.job_id
        if job_id in self.job_stats:
            self.job_stats[job_id]["failed"] += 1
        
        self.logger.error(f"❌ Job failed: {job_id} - {event.exception}")
    
    def _job_missed(self, event):
        """Handle job missed event"""
        job_id = event.job_id
        self.logger.warning(f"⚠️ Job missed: {job_id}")
    
    async def start(self):
        """Start the scheduler"""
        if not self.scheduler:
            self.logger.error("❌ Scheduler not initialized")
            return False
        
        try:
            # Add scheduled jobs
            await self._add_scheduled_jobs()
            
            # Start scheduler
            self.scheduler.start()
            self.is_running = True
            
            self.logger.info("🚀 AutomatedScheduler started successfully")
            self.logger.info(f"📅 Daily learning scheduled at: {self.config.daily_learning_time}")
            self.logger.info(f"📊 Weekly analysis scheduled: {self.config.weekly_analysis_day} at {self.config.weekly_analysis_time}")
            self.logger.info(f"🔧 Monthly improvement scheduled: {self.config.monthly_improvement_day} at {self.config.monthly_improvement_time}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Failed to start scheduler: {e}")
            return False
    
    async def _add_scheduled_jobs(self):
        """Add all scheduled jobs"""
        try:
            if not self.scheduler:
                self.logger.warning("Scheduler not initialized")
                return
                
            # Daily learning session
            self.scheduler.add_job(
                func=self._run_daily_learning_session,
                trigger=CronTrigger(
                    hour=int(self.config.daily_learning_time.split(':')[0]),
                    minute=int(self.config.daily_learning_time.split(':')[1]),
                    timezone=self.config.daily_learning_timezone
                ),
                id='daily_learning',
                name='Daily Learning Session',
                replace_existing=True,
                max_instances=1
            )
            
            # Weekly analysis
            if self.scheduler:
                self.scheduler.add_job(
                func=self._run_weekly_analysis,
                trigger=CronTrigger(
                    day_of_week=0,  # Monday (0=Monday, 1=Tuesday, etc.)
                    hour=int(self.config.weekly_analysis_time.split(':')[0]),
                    minute=int(self.config.weekly_analysis_time.split(':')[1]),
                    timezone=self.config.daily_learning_timezone
                ),
                id='weekly_analysis',
                name='Weekly Learning Analysis',
                replace_existing=True,
                max_instances=1
            )
            
            # Monthly improvement
            if self.scheduler:
                self.scheduler.add_job(
                func=self._run_monthly_improvement,
                trigger=CronTrigger(
                    day=self.config.monthly_improvement_day,
                    hour=int(self.config.monthly_improvement_time.split(':')[0]),
                    minute=int(self.config.monthly_improvement_time.split(':')[1]),
                    timezone=self.config.daily_learning_timezone
                ),
                id='monthly_improvement',
                name='Monthly Improvement Analysis',
                replace_existing=True,
                max_instances=1
            )
            
            # Health check
            if self.scheduler:
                self.scheduler.add_job(
                func=self._run_health_check,
                trigger=IntervalTrigger(minutes=self.config.health_check_interval),
                id='health_check',
                name='System Health Check',
                replace_existing=True,
                max_instances=1
            )
            
            self.logger.info("✅ All scheduled jobs added successfully")
            
        except Exception as e:
            self.logger.error(f"❌ Failed to add scheduled jobs: {e}")
            raise
    
    async def _run_daily_learning_session(self):
        """Run daily learning session"""
        try:
            self.logger.info("🧠 Starting scheduled daily learning session...")
            
            if not self.learning_manager:
                self.logger.warning("⚠️ Learning manager not available, skipping session")
                return
            
            # Select today's cases
            today_cases = self.learning_manager.select_today_cases(max_cases=3)
            
            if not today_cases:
                self.logger.info("ℹ️ No learning cases available for today")
                return
            
            # Run learning session
            total_score = 0
            session_results = []
            
            for case in today_cases:
                # Mock response for automated session
                response = f"Automated response for: {case.question}. This includes keywords: {', '.join(case.expected_keywords[:2])}."
                score = 7.0  # Mock score
                
                # Record response
                self.learning_manager.record_response(
                    case_id=case.id,
                    response=response,
                    score=score,
                    feedback="Automated learning session"
                )
                
                total_score += score
                session_results.append({
                    "case_id": case.id,
                    "question": case.question,
                    "score": score
                })
            
            avg_score = total_score / len(today_cases)
            
            # Run improvement analysis
            improvement_result = self.learning_manager.run_learning_improvement_cycle()
            
            self.logger.info(f"✅ Daily learning session completed - Avg score: {avg_score:.1f}/10")
            self.logger.info(f"📈 Improvement suggestions: {improvement_result.get('suggestions_count', 0)}")
            
        except Exception as e:
            self.logger.error(f"❌ Daily learning session failed: {e}")
            raise
    
    async def _run_weekly_analysis(self):
        """Run weekly learning analysis"""
        try:
            self.logger.info("📊 Starting weekly learning analysis...")
            
            if not self.learning_manager:
                self.logger.warning("⚠️ Learning manager not available, skipping analysis")
                return
            
            # Get learning stats
            stats = self.learning_manager.get_learning_stats()
            
            # Run comprehensive analysis
            analysis = self.learning_manager.analyze_learning_performance()
            
            # Generate weekly report
            report = self.learning_manager.generate_learning_report()
            
            self.logger.info("✅ Weekly analysis completed")
            self.logger.info(f"📊 Total cases: {stats.get('total_cases', 0)}")
            self.logger.info(f"📈 Recent avg score: {stats.get('recent_avg_score', 0)}")
            self.logger.info(f"🔍 Performance trend: {analysis.get('performance_analysis', {}).get('overall_score_trend', 'unknown')}")
            
        except Exception as e:
            self.logger.error(f"❌ Weekly analysis failed: {e}")
            raise
    
    async def _run_monthly_improvement(self):
        """Run monthly improvement analysis"""
        try:
            self.logger.info("🔧 Starting monthly improvement analysis...")
            
            if not self.learning_manager:
                self.logger.warning("⚠️ Learning manager not available, skipping improvement")
                return
            
            # Run comprehensive improvement analysis
            improvement_result = self.learning_manager.run_learning_improvement_cycle()
            
            # Get detailed analysis
            analysis = improvement_result.get("analysis", {})
            suggestions = improvement_result.get("improvement_suggestions", [])
            
            self.logger.info("✅ Monthly improvement analysis completed")
            self.logger.info(f"📈 Suggestions generated: {len(suggestions)}")
            self.logger.info(f"📤 Suggestions submitted: {improvement_result.get('suggestions_submitted', False)}")
            
            # Log improvement suggestions
            for i, suggestion in enumerate(suggestions, 1):
                self.logger.info(f"💡 Suggestion {i}: {suggestion.get('description', 'N/A')}")
            
        except Exception as e:
            self.logger.error(f"❌ Monthly improvement failed: {e}")
            raise
    
    async def _run_health_check(self):
        """Run system health check"""
        try:
            # Check scheduler health
            if self.scheduler:
                jobs = self.scheduler.get_jobs()
                active_jobs = len([job for job in jobs if job.next_run_time])
            else:
                active_jobs = 0
            
            # Check learning manager health
            learning_health = "healthy" if self.learning_manager else "unavailable"
            
            # Check framework health
            framework_health = "healthy" if self.framework else "unavailable"
            
            self.logger.info(f"💚 Health check - Jobs: {active_jobs}, Learning: {learning_health}, Framework: {framework_health}")
            
        except Exception as e:
            self.logger.error(f"❌ Health check failed: {e}")
    
    def stop(self):
        """Stop the scheduler"""
        if self.scheduler and self.is_running:
            self.scheduler.shutdown(wait=True)
            self.is_running = False
            self.logger.info("🛑 AutomatedScheduler stopped")
    
    def get_status(self) -> Dict[str, Any]:
        """Get scheduler status"""
        if not self.scheduler:
            return {"status": "not_initialized"}
        
        jobs = self.scheduler.get_jobs()
        job_info = []
        
        for job in jobs:
            job_info.append({
                "id": job.id,
                "name": job.name,
                "next_run": job.next_run_time.isoformat() if job.next_run_time else None,
                "trigger": str(job.trigger)
            })
        
        return {
            "status": "running" if self.is_running else "stopped",
            "jobs": job_info,
            "job_stats": self.job_stats,
            "config": {
                "daily_learning_time": self.config.daily_learning_time,
                "weekly_analysis_day": self.config.weekly_analysis_day,
                "monthly_improvement_day": self.config.monthly_improvement_day,
                "health_check_interval": self.config.health_check_interval
            }
        }
    
    async def run_manual_job(self, job_id: str) -> Dict[str, Any]:
        """Run a job manually"""
        try:
            if not self.scheduler:
                return {"status": "error", "error": "Scheduler not initialized"}
            
            # Run the job directly without checking scheduler jobs
            if job_id == "daily_learning":
                await self._run_daily_learning_session()
            elif job_id == "weekly_analysis":
                await self._run_weekly_analysis()
            elif job_id == "monthly_improvement":
                await self._run_monthly_improvement()
            elif job_id == "health_check":
                await self._run_health_check()
            else:
                return {"status": "error", "error": f"Unknown job: {job_id}"}
            
            return {"status": "success", "job_id": job_id}
            
        except Exception as e:
            self.logger.error(f"❌ Manual job execution failed: {e}")
            return {"status": "error", "error": str(e)}

# Factory function
def create_automated_scheduler(config: Optional[SchedulerConfig] = None) -> AutomatedScheduler:
    """Create and return an AutomatedScheduler instance"""
    return AutomatedScheduler(config)

# Test function
async def test_automated_scheduler():
    """Test the automated scheduler"""
    print("🚀 Testing Automated Scheduler")
    print("=" * 50)
    
    # Create scheduler
    scheduler = create_automated_scheduler()
    
    # Initialize
    success = await scheduler.initialize()
    if not success:
        print("❌ Failed to initialize scheduler")
        return
    
    print("✅ Scheduler initialized")
    
    # Start scheduler
    success = await scheduler.start()
    if not success:
        print("❌ Failed to start scheduler")
        return
    
    print("✅ Scheduler started")
    
    # Get status
    status = scheduler.get_status()
    print(f"📊 Status: {status['status']}")
    print(f"📅 Jobs: {len(status['jobs'])}")
    
    # Run manual health check
    result = await scheduler.run_manual_job("health_check")
    print(f"💚 Health check: {result['status']}")
    
    # Stop scheduler
    scheduler.stop()
    print("🛑 Scheduler stopped")

if __name__ == "__main__":
    asyncio.run(test_automated_scheduler())
