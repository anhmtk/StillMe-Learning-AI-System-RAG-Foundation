"""
Trace Utilities for StillMe

Provides utilities for request tracing and correlation IDs.
"""

import logging
import uuid
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from dataclasses import dataclass, field, asdict

logger = logging.getLogger(__name__)


def generate_correlation_id() -> str:
    """
    Generate unique correlation ID for request tracing
    
    Format: trace_{timestamp}_{random}
    
    Returns:
        Correlation ID string
    """
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    random_part = str(uuid.uuid4())[:8]
    return f"trace_{timestamp}_{random_part}"


@dataclass
class RequestTrace:
    """
    Full trace of a request through StillMe
    
    Tracks all stages: API → RAG → LLM → Validation → Response
    """
    trace_id: str
    timestamp: str
    query: str
    
    # Stages
    rag_retrieval: Optional[Dict[str, Any]] = None
    llm_generation: Optional[Dict[str, Any]] = None
    validation: Optional[Dict[str, Any]] = None
    post_processing: Optional[Dict[str, Any]] = None
    final_response: Optional[Dict[str, Any]] = None
    
    # Metadata
    duration_ms: Optional[float] = None
    error: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert trace to dictionary"""
        return {
            "trace_id": self.trace_id,
            "timestamp": self.timestamp,
            "query": self.query[:200] + "..." if len(self.query) > 200 else self.query,
            "stages": {
                "rag_retrieval": self.rag_retrieval,
                "llm_generation": self.llm_generation,
                "validation": self.validation,
                "post_processing": self.post_processing,
                "final_response": self.final_response
            },
            "duration_ms": self.duration_ms,
            "error": self.error
        }

