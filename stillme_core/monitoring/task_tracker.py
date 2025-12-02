"""
Task Tracking for Time Estimation

Tracks task execution time and metadata for self-aware time estimation.
"""

import logging
import time
import uuid
from typing import Dict, Optional, Any, List
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from stillme_core.monitoring import get_metrics_collector, MetricCategory

logger = logging.getLogger(__name__)


@dataclass
class TaskRecord:
    """Record of a task execution"""
    task_id: str
    task_type: str  # "coding", "review", "migration", "analysis", "refactoring"
    complexity: str  # "simple", "moderate", "complex", "very_complex"
    size: int  # lines_of_code, files_changed, components_affected
    estimated_time_minutes: Optional[float]
    actual_time_minutes: float
    accuracy_ratio: float  # actual / estimated (if estimated)
    confidence: float  # 0.0-1.0
    timestamp: str  # ISO format
    metadata: Dict[str, Any]


class TaskTracker:
    """
    Tracks task execution for time estimation learning.
    
    Records:
    - Task start: task_type, complexity, size, estimated_time
    - Task end: actual_time, accuracy_ratio
    """
    
    def __init__(self):
        self.metrics = get_metrics_collector()
        self._active_tasks: Dict[str, Dict[str, Any]] = {}
    
    def start_task(
        self,
        task_type: str,
        complexity: str,
        size: int,
        estimated_time_minutes: Optional[float] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Record task start.
        
        Args:
            task_type: Type of task ("coding", "review", "migration", etc.)
            complexity: Task complexity ("simple", "moderate", "complex", "very_complex")
            size: Task size (lines of code, files changed, etc.)
            estimated_time_minutes: Estimated time (optional)
            metadata: Additional metadata
            
        Returns:
            task_id: Unique task identifier
        """
        task_id = str(uuid.uuid4())
        start_time = time.time()
        
        self._active_tasks[task_id] = {
            "task_type": task_type,
            "complexity": complexity,
            "size": size,
            "estimated_time_minutes": estimated_time_minutes,
            "start_time": start_time,
            "metadata": metadata or {}
        }
        
        # Record to metrics
        self.metrics.record(
            MetricCategory.SYSTEM,
            "task_start",
            {
                "task_id": task_id,
                "task_type": task_type,
                "complexity": complexity,
                "size": size,
                "estimated_time_minutes": estimated_time_minutes
            },
            metadata=metadata
        )
        
        logger.debug(f"Task started: {task_id} ({task_type}, {complexity}, size={size})")
        return task_id
    
    def end_task(
        self,
        task_id: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[TaskRecord]:
        """
        Record task end and calculate accuracy.
        
        Args:
            task_id: Task identifier from start_task()
            metadata: Additional metadata
            
        Returns:
            TaskRecord if task was found, None otherwise
        """
        if task_id not in self._active_tasks:
            logger.warning(f"Task {task_id} not found in active tasks")
            return None
        
        task_info = self._active_tasks.pop(task_id)
        actual_time_minutes = (time.time() - task_info["start_time"]) / 60
        
        estimated = task_info.get("estimated_time_minutes")
        accuracy_ratio = 0.0
        if estimated and estimated > 0:
            accuracy_ratio = actual_time_minutes / estimated
        
        # Create task record
        task_record = TaskRecord(
            task_id=task_id,
            task_type=task_info["task_type"],
            complexity=task_info["complexity"],
            size=task_info["size"],
            estimated_time_minutes=estimated,
            actual_time_minutes=actual_time_minutes,
            accuracy_ratio=accuracy_ratio,
            confidence=task_info.get("confidence", 0.5),
            timestamp=datetime.now(timezone.utc).isoformat(),
            metadata={**(task_info.get("metadata", {})), **(metadata or {})}
        )
        
        # Record to metrics
        self.metrics.record(
            MetricCategory.SYSTEM,
            "task_end",
            {
                "task_id": task_id,
                "actual_time_minutes": actual_time_minutes,
                "estimated_time_minutes": estimated,
                "accuracy_ratio": accuracy_ratio
            },
            metadata=metadata
        )
        
        logger.debug(f"Task completed: {task_id} (actual: {actual_time_minutes:.2f} min, accuracy: {accuracy_ratio:.2f})")
        return task_record
    
    def get_historical_tasks(
        self,
        task_type: Optional[str] = None,
        complexity: Optional[str] = None,
        days: int = 30
    ) -> List[TaskRecord]:
        """
        Get historical task records.
        
        Args:
            task_type: Filter by task type (optional)
            complexity: Filter by complexity (optional)
            days: Number of days to look back
            
        Returns:
            List of TaskRecord objects
        """
        # Get from metrics system
        metrics = self.metrics.get_metrics(MetricCategory.SYSTEM, days=days)
        
        # Extract task_end records
        task_records = []
        for record in self.metrics._records:
            if record.category == MetricCategory.SYSTEM.value and record.metric_name == "task_end":
                value = record.value
                if isinstance(value, dict):
                    # Reconstruct TaskRecord from metrics
                    task_records.append(TaskRecord(
                        task_id=value.get("task_id", ""),
                        task_type="",  # Will be filled from task_start
                        complexity="",
                        size=0,
                        estimated_time_minutes=value.get("estimated_time_minutes"),
                        actual_time_minutes=value.get("actual_time_minutes", 0),
                        accuracy_ratio=value.get("accuracy_ratio", 0),
                        confidence=0.5,
                        timestamp=record.timestamp,
                        metadata=record.metadata or {}
                    ))
        
        # Filter
        if task_type:
            task_records = [t for t in task_records if t.task_type == task_type]
        if complexity:
            task_records = [t for t in task_records if t.complexity == complexity]
        
        return task_records


# Global instance
_task_tracker: Optional[TaskTracker] = None


def get_task_tracker() -> TaskTracker:
    """Get global task tracker instance"""
    global _task_tracker
    if _task_tracker is None:
        _task_tracker = TaskTracker()
    return _task_tracker

