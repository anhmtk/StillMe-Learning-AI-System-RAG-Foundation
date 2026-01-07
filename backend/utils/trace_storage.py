"""
Trace Storage for StillMe

Stores request traces with TTL for debugging and transparency.
Uses Redis if available, falls back to in-memory storage.
"""

import logging
import threading
from typing import Dict, Optional
from datetime import datetime, timedelta, timezone

from backend.utils.trace_utils import RequestTrace

logger = logging.getLogger(__name__)

# Try to import cache utilities
try:
    from backend.utils.cache_utils import get_from_cache, set_to_cache
    CACHE_AVAILABLE = True
except ImportError:
    CACHE_AVAILABLE = False
    get_from_cache = None
    set_to_cache = None

# In-memory fallback storage
_in_memory_traces: Dict[str, RequestTrace] = {}
_trace_lock = threading.Lock()


class TraceStorage:
    """
    Storage for request traces with TTL
    
    Stores traces in Redis (if available) or in-memory with expiration.
    """
    
    def __init__(self, ttl_hours: int = 24):
        """
        Initialize trace storage
        
        Args:
            ttl_hours: Time to live in hours (default: 24 hours)
        """
        self.ttl_hours = ttl_hours
        self.ttl_seconds = ttl_hours * 3600
        logger.info(f"TraceStorage initialized (TTL: {ttl_hours}h, Cache: {CACHE_AVAILABLE})")
    
    def store(self, trace: RequestTrace) -> None:
        """
        Store a trace
        
        Args:
            trace: RequestTrace to store
        """
        # Try cache first
        if CACHE_AVAILABLE:
            try:
                cache_key = f"trace:{trace.trace_id}"
                set_to_cache(cache_key, trace.to_dict(), ttl=self.ttl_seconds)
                logger.debug(f"Stored trace in cache: {trace.trace_id}")
                return
            except Exception as e:
                logger.debug(f"Cache storage failed, using in-memory: {e}")
        
        # Fallback to in-memory
        with _trace_lock:
            _in_memory_traces[trace.trace_id] = trace
            logger.debug(f"Stored trace in memory: {trace.trace_id}")
    
    def get(self, trace_id: str) -> Optional[RequestTrace]:
        """
        Get a trace by ID
        
        Args:
            trace_id: Trace ID
        
        Returns:
            RequestTrace or None if not found or expired
        """
        # Try cache first
        if CACHE_AVAILABLE:
            try:
                cache_key = f"trace:{trace_id}"
                cached_data = get_from_cache(cache_key)
                if cached_data:
                    # Reconstruct RequestTrace from dict
                    trace = RequestTrace(
                        trace_id=cached_data.get("trace_id", trace_id),
                        timestamp=cached_data.get("timestamp", ""),
                        query=cached_data.get("query", ""),
                        rag_retrieval=cached_data.get("stages", {}).get("rag_retrieval"),
                        llm_generation=cached_data.get("stages", {}).get("llm_generation"),
                        validation=cached_data.get("stages", {}).get("validation"),
                        post_processing=cached_data.get("stages", {}).get("post_processing"),
                        final_response=cached_data.get("stages", {}).get("final_response"),
                        duration_ms=cached_data.get("duration_ms"),
                        error=cached_data.get("error")
                    )
                    logger.debug(f"Retrieved trace from cache: {trace_id}")
                    return trace
            except Exception as e:
                logger.debug(f"Cache retrieval failed, trying memory: {e}")
        
        # Fallback to in-memory
        with _trace_lock:
            trace = _in_memory_traces.get(trace_id)
            if trace:
                logger.debug(f"Retrieved trace from memory: {trace_id}")
                return trace
        
        logger.debug(f"Trace not found: {trace_id}")
        return None
    
    def cleanup_old_traces(self) -> int:
        """
        Clean up expired traces from in-memory storage
        
        Returns:
            Number of traces cleaned up
        """
        if not CACHE_AVAILABLE:
            cutoff = datetime.now(timezone.utc) - timedelta(hours=self.ttl_hours)
            cleaned = 0
            
            with _trace_lock:
                expired_ids = [
                    trace_id for trace_id, trace in _in_memory_traces.items()
                    if datetime.fromisoformat(trace.timestamp.replace('Z', '+00:00')) < cutoff
                ]
                for trace_id in expired_ids:
                    del _in_memory_traces[trace_id]
                    cleaned += 1
            
            if cleaned > 0:
                logger.info(f"Cleaned up {cleaned} expired traces")
            
            return cleaned
        
        return 0  # Cache handles TTL automatically


# Global storage instance
_trace_storage_instance: Optional[TraceStorage] = None


def get_trace_storage() -> TraceStorage:
    """Get global trace storage instance"""
    global _trace_storage_instance
    if _trace_storage_instance is None:
        _trace_storage_instance = TraceStorage(ttl_hours=24)
    return _trace_storage_instance

