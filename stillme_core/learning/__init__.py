"""
StillMe Learning Module
Safe daily smart-learning pipeline for AI systems.
"""

__version__ = "1.0.0"
__author__ = "StillMe AI Framework"

# Import main pipeline
from .pipeline import LearningPipeline

# Import unified learning manager
from .unified_learning_manager import (
    UnifiedLearningManager,
    LearningSystemMode,
    LearningConfig,
    get_unified_learning_manager,
    initialize_learning_systems
)

# Import convenience functions
from .fetcher.rss_fetch import fetch_content_from_sources
from .parser.normalize import normalize_content_batch
from .gates.license_gate import validate_content_licenses
from .risk.injection_scan import assess_content_risks
from .score.quality import score_content_quality_batch
from .dedupe.novelty import check_content_novelty
from .approve.queue import get_approval_queue
from .ingest.vector_store import get_vector_store
from .ingest.claims_store import get_claims_store
from .reports.digest import get_digest_generator

__all__ = [
    'LearningPipeline',
    'UnifiedLearningManager',
    'LearningSystemMode',
    'LearningConfig',
    'get_unified_learning_manager',
    'initialize_learning_systems',
    'fetch_content_from_sources',
    'normalize_content_batch',
    'validate_content_licenses',
    'assess_content_risks',
    'score_content_quality_batch',
    'check_content_novelty',
    'get_approval_queue',
    'get_vector_store',
    'get_claims_store',
    'get_digest_generator'
]
