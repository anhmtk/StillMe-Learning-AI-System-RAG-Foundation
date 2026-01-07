"""
Trace Router for StillMe

Provides endpoints for retrieving request traces.
"""

import logging
from fastapi import APIRouter, HTTPException, Path
from typing import Dict, Any

from backend.utils.trace_storage import get_trace_storage
from backend.utils.trace_utils import RequestTrace

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/trace", tags=["trace"])


@router.get("/{trace_id}")
async def get_trace(trace_id: str = Path(..., description="Trace ID to retrieve")):
    """
    Get full request trace by trace ID
    
    Returns complete trace including:
    - RAG retrieval details
    - LLM generation details
    - Validation results
    - Post-processing steps
    - Final response metadata
    """
    try:
        trace_storage = get_trace_storage()
        trace = trace_storage.get(trace_id)
        
        if not trace:
            raise HTTPException(
                status_code=404,
                detail=f"Trace not found: {trace_id}. Traces are stored for 24 hours."
            )
        
        return {
            "trace_id": trace.trace_id,
            "timestamp": trace.timestamp,
            "query": trace.query,
            "stages": {
                "rag_retrieval": trace.rag_retrieval,
                "llm_generation": trace.llm_generation,
                "validation": trace.validation,
                "post_processing": trace.post_processing,
                "final_response": trace.final_response
            },
            "duration_ms": trace.duration_ms,
            "error": trace.error
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving trace {trace_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving trace: {str(e)}"
        )

