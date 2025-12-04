"""
Self-Tracking Integration for StillMe

Enables StillMe to track its own task execution time, demonstrating
self-awareness while maintaining clear AI identity.

This is the integration layer that connects Time Estimation to StillMe's workflow.
"""

import logging
import time
from typing import Optional, Dict, Any, Callable
from contextlib import contextmanager
from stillme_core.monitoring import get_estimation_engine, get_task_tracker, TimeEstimate

logger = logging.getLogger(__name__)


@contextmanager
def track_task_execution(
    task_description: str,
    task_type: str,
    complexity: str,
    size: int,
    metadata: Optional[Dict[str, Any]] = None,
    communicate_estimate: bool = False
):
    """
    Context manager to track StillMe's own task execution.
    
    Usage:
        with track_task_execution("Migrate validation", "migration", "moderate", 500):
            # StillMe does work here
            migrate_validation_system()
    
    This enables StillMe to:
    - Estimate time before starting
    - Track actual execution time
    - Learn from accuracy
    - Communicate estimates to user (if requested)
    
    Args:
        task_description: Human-readable task description
        task_type: Type of task ("coding", "review", "migration", etc.)
        complexity: Task complexity ("simple", "moderate", "complex", "very_complex")
        size: Task size (lines of code, files changed, etc.)
        metadata: Additional metadata
        communicate_estimate: If True, log estimate for user visibility
    
    Yields:
        TimeEstimate object with estimate information
    """
    estimator = get_estimation_engine()
    tracker = get_task_tracker()
    
    # Step 1: Estimate before starting
    estimate = estimator.estimate(
        task_description=task_description,
        task_type=task_type,
        complexity=complexity,
        size=size,
        metadata=metadata
    )
    
    # Step 2: Start tracking
    task_id = tracker.start_task(
        task_type=task_type,
        complexity=complexity,
        size=size,
        estimated_time_minutes=estimate.estimated_minutes,
        metadata={
            "description": task_description,
            "confidence": estimate.confidence,
            **(metadata or {})
        }
    )
    
    # Step 3: Communicate estimate if requested
    if communicate_estimate:
        estimate_text = estimator.format_estimate(estimate)
        logger.info(f"📊 StillMe self-estimate: {estimate_text}")
        logger.info(f"   I'm an AI system that tracks my own performance to improve estimates over time.")
    else:
        # Still log at debug level for internal tracking visibility
        logger.debug(f"📊 StillMe tracking: {task_description} (estimate: {estimate.estimated_minutes:.2f} min, confidence: {estimate.confidence:.0%})")
    
    try:
        # Yield estimate for use in task
        yield estimate
        
    finally:
        # Step 4: End tracking
        task_record = tracker.end_task(task_id, metadata=metadata)
        
        if task_record:
            accuracy = task_record.accuracy_ratio
            if communicate_estimate:
                if 0.7 <= accuracy <= 1.3:  # Within 30% of estimate
                    logger.info(f"✅ Task completed: {task_record.actual_time_minutes:.2f} min (estimate was accurate)")
                elif accuracy < 0.7:  # Took less time
                    logger.info(f"⚡ Task completed: {task_record.actual_time_minutes:.2f} min (faster than estimated)")
                else:  # Took more time
                    logger.info(f"⏱️ Task completed: {task_record.actual_time_minutes:.2f} min (longer than estimated)")
            
            # Log for learning
            logger.debug(
                f"StillMe self-tracking: task_id={task_id}, "
                f"estimated={task_record.estimated_time_minutes:.2f} min, "
                f"actual={task_record.actual_time_minutes:.2f} min, "
                f"accuracy={accuracy:.2f}"
            )


def estimate_and_track(
    task_description: str,
    task_type: str,
    complexity: str,
    size: int,
    metadata: Optional[Dict[str, Any]] = None
) -> Callable:
    """
    Decorator to estimate and track function execution time.
    
    Usage:
        @estimate_and_track("Refactor learning system", "refactoring", "complex", 1000)
        def refactor_learning_system():
            # StillMe does work
            pass
    """
    def decorator(func: Callable) -> Callable:
        def wrapper(*args, **kwargs):
            with track_task_execution(
                task_description=task_description,
                task_type=task_type,
                complexity=complexity,
                size=size,
                metadata=metadata,
                communicate_estimate=True
            ):
                return func(*args, **kwargs)
        return wrapper
    return decorator


def format_self_aware_response(estimate: TimeEstimate, include_identity: bool = True, language: str = "en") -> str:
    """
    Format time estimate response with clear AI identity.
    
    This ensures StillMe communicates estimates in a way that is:
    - Human-like (natural communication)
    - AI-aware (clear about being AI)
    
    Args:
        estimate: TimeEstimate object
        include_identity: Whether to include AI identity statement
        language: Language code ("en" or "vi")
    
    Returns:
        Formatted response string in specified language
    """
    estimator = get_estimation_engine()
    base_response = estimator.format_estimate(estimate, language=language)
    
    if include_identity:
        if language == "vi":
            identity_statement = (
                " Mình là một hệ thống AI theo dõi thời gian thực thi của chính mình để cải thiện ước tính theo thời gian. "
                "Mình ước tính dựa trên dữ liệu hiệu suất lịch sử, tương tự như cách con người ước tính "
                "dựa trên kinh nghiệm, nhưng mình là một mô hình thống kê học từ các mẫu."
            )
        else:
            identity_statement = (
                " I'm an AI system that tracks my own execution time to improve estimates over time. "
                "I estimate based on my historical performance data, similar to how humans estimate "
                "based on experience, but I'm a statistical model that learns from patterns."
            )
        return base_response + identity_statement
    
    return base_response

