"""
External Data Layer - Real-time data from public APIs

This module provides access to real-time, structured data from external APIs
(weather, news, finance, etc.) while maintaining StillMe's transparency principles.

⚠️ MIGRATION NOTE: This module is being migrated to stillme_core.external_data.
During migration, imports are forwarded from stillme_core.external_data for backward compatibility.

Key Principles:
- Always show source and timestamp
- Never "package" API data as internal knowledge
- Maintain evidence-over-authority principle
- Intellectual humility when APIs fail
"""

# During migration: Forward imports from stillme_core.external_data
try:
    from stillme_core.external_data import (
        ExternalDataOrchestrator,
        detect_external_data_intent,
        ExternalDataIntent,
        ExternalDataCache,
        ExternalDataProvider,
        ExternalDataResult,
    )
except ImportError:
    # Fallback to local imports if stillme_core is not available yet
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

