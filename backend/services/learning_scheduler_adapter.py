"""
Adapter for LearningScheduler - Backward Compatibility

⚠️ MIGRATION NOTE: LearningScheduler has been migrated to stillme_core.learning.scheduler.
This adapter forwards imports for backward compatibility.
"""

# Forward import from stillme_core
try:
    from stillme_core.learning.scheduler import LearningScheduler
except ImportError:
    # Fallback to local import if stillme_core is not available
    from backend.services.learning_scheduler import LearningScheduler

__all__ = ["LearningScheduler"]

