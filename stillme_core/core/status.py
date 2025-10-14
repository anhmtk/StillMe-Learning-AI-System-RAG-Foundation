#!/usr/bin/env python3
"""
Status Enums - MINIMAL CONTRACT derived from tests/usages
"""

from enum import Enum


class JobStatus(Enum):
    """Job status enum - MINIMAL CONTRACT derived from tests/usages"""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class StepStatus(Enum):
    """Step status enum - MINIMAL CONTRACT derived from tests/usages"""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


__all__ = ["JobStatus", "StepStatus"]