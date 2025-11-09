"""
Job Queue System for Non-Blocking Learning Cycles
Tracks background jobs and their status
"""

import asyncio
import uuid
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
from enum import Enum
from threading import Lock

logger = logging.getLogger(__name__)


class JobStatus(str, Enum):
    """Job status enumeration"""
    PENDING = "pending"
    FETCHING = "fetching"
    PREFILTER = "prefilter"
    EMBEDDING = "embedding"
    ADDING_TO_RAG = "adding_to_rag"
    DONE = "done"
    ERROR = "error"


class LearningCycleJob:
    """Represents a learning cycle job"""
    
    def __init__(self, job_id: str):
        self.job_id = job_id
        self.status = JobStatus.PENDING
        self.created_at = datetime.now()
        self.started_at: Optional[datetime] = None
        self.completed_at: Optional[datetime] = None
        self.progress: Dict[str, Any] = {
            "phase": "pending",
            "entries_fetched": 0,
            "entries_filtered": 0,
            "entries_added": 0,
            "current_item": None
        }
        self.result: Optional[Dict[str, Any]] = None
        self.error: Optional[str] = None
        self.logs: List[str] = []
    
    def add_log(self, message: str):
        """Add a log message"""
        timestamp = datetime.now().isoformat()
        self.logs.append(f"[{timestamp}] {message}")
        # Keep only last 100 logs
        if len(self.logs) > 100:
            self.logs = self.logs[-100:]
    
    def update_progress(self, phase: str, **kwargs):
        """Update job progress"""
        self.status = JobStatus[phase.upper()] if phase.upper() in JobStatus.__members__ else JobStatus.PENDING
        self.progress["phase"] = phase
        self.progress.update(kwargs)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert job to dictionary"""
        return {
            "job_id": self.job_id,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "progress": self.progress,
            "result": self.result,
            "error": self.error,
            "logs": self.logs[-20:]  # Return last 20 logs
        }


class JobQueue:
    """Thread-safe job queue for learning cycles"""
    
    def __init__(self):
        self._lock = Lock()
        self._jobs: Dict[str, LearningCycleJob] = {}
        self._max_jobs = 100  # Keep last 100 jobs
    
    def create_job(self) -> str:
        """Create a new job and return job_id"""
        job_id = str(uuid.uuid4())
        job = LearningCycleJob(job_id)
        
        with self._lock:
            self._jobs[job_id] = job
            # Clean up old jobs if we exceed max
            if len(self._jobs) > self._max_jobs:
                # Remove oldest jobs
                sorted_jobs = sorted(self._jobs.items(), key=lambda x: x[1].created_at)
                for old_job_id, _ in sorted_jobs[:-self._max_jobs]:
                    del self._jobs[old_job_id]
        
        logger.info(f"Created learning cycle job: {job_id}")
        return job_id
    
    def get_job(self, job_id: str) -> Optional[LearningCycleJob]:
        """Get job by ID"""
        with self._lock:
            return self._jobs.get(job_id)
    
    def update_job(self, job_id: str, **kwargs):
        """Update job status/progress"""
        with self._lock:
            job = self._jobs.get(job_id)
            if job:
                if "status" in kwargs:
                    job.status = kwargs["status"]
                if "progress" in kwargs:
                    job.progress.update(kwargs["progress"])
                if "result" in kwargs:
                    job.result = kwargs["result"]
                if "error" in kwargs:
                    job.error = kwargs["error"]
                    job.status = JobStatus.ERROR
                if "log" in kwargs:
                    job.add_log(kwargs["log"])
    
    def get_all_jobs(self) -> List[Dict[str, Any]]:
        """Get all jobs (for debugging)"""
        with self._lock:
            return [job.to_dict() for job in self._jobs.values()]


# Global job queue instance
_job_queue = JobQueue()


def get_job_queue() -> JobQueue:
    """Get global job queue instance"""
    return _job_queue

