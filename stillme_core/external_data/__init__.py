"""
StillMe Core External Data System

Provides external data providers (weather, news, time, etc.) with
orchestration, caching, and rate limiting.

This module has been migrated from backend/external_data/ to stillme_core/external_data/
"""

from .orchestrator import ExternalDataOrchestrator
from .intent_detector import detect_external_data_intent, ExternalDataIntent
from .cache import ExternalDataCache
from .providers.base import ExternalDataProvider, ExternalDataResult

__all__ = [
    "ExternalDataOrchestrator",
    "detect_external_data_intent",
    "ExternalDataIntent",
    "ExternalDataCache",
    "ExternalDataProvider",
    "ExternalDataResult",
]
