"""
Dependency Injection for StillMe API
Provides FastAPI Depends() functions for service injection
"""

from fastapi import Depends
from typing import Optional
import logging

logger = logging.getLogger(__name__)

# Global service instances (initialized in main.py)
_rag_retrieval: Optional[object] = None
_chroma_client: Optional[object] = None
_embedding_service: Optional[object] = None
_knowledge_retention: Optional[object] = None
_accuracy_scorer: Optional[object] = None
_learning_scheduler: Optional[object] = None
_rss_fetcher: Optional[object] = None
_content_curator: Optional[object] = None
_self_diagnosis: Optional[object] = None
_continuum_memory: Optional[object] = None
_source_integration: Optional[object] = None
_rss_fetch_history: Optional[object] = None


def set_services(
    rag_retrieval=None,
    chroma_client=None,
    embedding_service=None,
    knowledge_retention=None,
    accuracy_scorer=None,
    learning_scheduler=None,
    rss_fetcher=None,
    content_curator=None,
    self_diagnosis=None,
    continuum_memory=None,
    source_integration=None,
    rss_fetch_history=None
):
    """Set global service instances (called from main.py during startup)"""
    global _rag_retrieval, _chroma_client, _embedding_service
    global _knowledge_retention, _accuracy_scorer, _learning_scheduler
    global _rss_fetcher, _content_curator, _self_diagnosis
    global _continuum_memory, _source_integration, _rss_fetch_history
    
    if rag_retrieval is not None:
        _rag_retrieval = rag_retrieval
    if chroma_client is not None:
        _chroma_client = chroma_client
    if embedding_service is not None:
        _embedding_service = embedding_service
    if knowledge_retention is not None:
        _knowledge_retention = knowledge_retention
    if accuracy_scorer is not None:
        _accuracy_scorer = accuracy_scorer
    if learning_scheduler is not None:
        _learning_scheduler = learning_scheduler
    if rss_fetcher is not None:
        _rss_fetcher = rss_fetcher
    if content_curator is not None:
        _content_curator = content_curator
    if self_diagnosis is not None:
        _self_diagnosis = self_diagnosis
    if continuum_memory is not None:
        _continuum_memory = continuum_memory
    if source_integration is not None:
        _source_integration = source_integration
    if rss_fetch_history is not None:
        _rss_fetch_history = rss_fetch_history


# Dependency functions for FastAPI Depends()
def get_rag_retrieval_dep() -> object:
    """Dependency: Get RAG retrieval service"""
    if _rag_retrieval is None:
        # Fallback to main module if not set
        import backend.api.main as main_module
        return main_module.rag_retrieval
    return _rag_retrieval


def get_chroma_client_dep() -> object:
    """Dependency: Get ChromaDB client"""
    if _chroma_client is None:
        import backend.api.main as main_module
        return main_module.chroma_client
    return _chroma_client


def get_embedding_service_dep() -> object:
    """Dependency: Get embedding service"""
    if _embedding_service is None:
        import backend.api.main as main_module
        return main_module.embedding_service
    return _embedding_service


def get_knowledge_retention_dep() -> object:
    """Dependency: Get knowledge retention service"""
    if _knowledge_retention is None:
        import backend.api.main as main_module
        return main_module.knowledge_retention
    return _knowledge_retention


def get_accuracy_scorer_dep() -> object:
    """Dependency: Get accuracy scorer service"""
    if _accuracy_scorer is None:
        import backend.api.main as main_module
        return main_module.accuracy_scorer
    return _accuracy_scorer


def get_learning_scheduler_dep() -> object:
    """Dependency: Get learning scheduler service"""
    if _learning_scheduler is None:
        import backend.api.main as main_module
        return main_module.learning_scheduler
    return _learning_scheduler


def get_rss_fetcher_dep() -> object:
    """Dependency: Get RSS fetcher service"""
    if _rss_fetcher is None:
        import backend.api.main as main_module
        return main_module.rss_fetcher
    return _rss_fetcher


def get_content_curator_dep() -> object:
    """Dependency: Get content curator service"""
    if _content_curator is None:
        import backend.api.main as main_module
        return main_module.content_curator
    return _content_curator


def get_self_diagnosis_dep() -> object:
    """Dependency: Get self diagnosis service"""
    if _self_diagnosis is None:
        import backend.api.main as main_module
        return getattr(main_module, 'self_diagnosis', None)
    return _self_diagnosis


def get_continuum_memory_dep() -> object:
    """Dependency: Get continuum memory service"""
    if _continuum_memory is None:
        import backend.api.main as main_module
        return main_module.continuum_memory
    return _continuum_memory


def get_source_integration_dep() -> object:
    """Dependency: Get source integration service"""
    if _source_integration is None:
        import backend.api.main as main_module
        return main_module.source_integration
    return _source_integration


def get_rss_fetch_history_dep() -> object:
    """Dependency: Get RSS fetch history service"""
    if _rss_fetch_history is None:
        import backend.api.main as main_module
        return main_module.rss_fetch_history
    return _rss_fetch_history


# Type aliases for cleaner code
RAGRetrievalDep = Depends(get_rag_retrieval_dep)
ChromaClientDep = Depends(get_chroma_client_dep)
EmbeddingServiceDep = Depends(get_embedding_service_dep)
KnowledgeRetentionDep = Depends(get_knowledge_retention_dep)
AccuracyScorerDep = Depends(get_accuracy_scorer_dep)
LearningSchedulerDep = Depends(get_learning_scheduler_dep)
RSSFetcherDep = Depends(get_rss_fetcher_dep)
ContentCuratorDep = Depends(get_content_curator_dep)
SelfDiagnosisDep = Depends(get_self_diagnosis_dep)
ContinuumMemoryDep = Depends(get_continuum_memory_dep)
SourceIntegrationDep = Depends(get_source_integration_dep)
RSSFetchHistoryDep = Depends(get_rss_fetch_history_dep)

