"""
Learning Router for StillMe API
Handles all learning-related endpoints (knowledge retention, RSS, scheduler, self-diagnosis, curator)
"""

from fastapi import APIRouter, Request, HTTPException, Depends, Query, status
from backend.api.models import LearningRequest, LearningResponse
from backend.api.rate_limiter import limiter, get_rate_limit_key_func
from backend.api.auth import require_api_key
from backend.api.job_queue import get_job_queue
from typing import Optional, Dict, Any, List
import asyncio
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

router = APIRouter()

# Import global services from main (temporary - will refactor to dependency injection later)
# These are initialized in main.py before routers are included
def get_knowledge_retention():
    """Get knowledge retention service from main module"""
    import backend.api.main as main_module
    return main_module.knowledge_retention

def get_rag_retrieval():
    """Get RAG retrieval service from main module"""
    import backend.api.main as main_module
    return main_module.rag_retrieval

def get_chroma_client():
    """Get ChromaDB client from main module"""
    import backend.api.main as main_module
    return main_module.chroma_client

def get_accuracy_scorer():
    """Get accuracy scorer service from main module"""
    import backend.api.main as main_module
    return main_module.accuracy_scorer

def get_content_curator():
    """Get content curator service from main module"""
    import backend.api.main as main_module
    return main_module.content_curator

def get_rss_fetcher():
    """Get RSS fetcher service from main module"""
    import backend.api.main as main_module
    return main_module.rss_fetcher

def get_learning_scheduler():
    """Get learning scheduler service from main module"""
    import backend.api.main as main_module
    return main_module.learning_scheduler

def get_self_diagnosis():
    """Get self-diagnosis agent service from main module"""
    import backend.api.main as main_module
    return main_module.self_diagnosis

def _get_rss_fetch_history_service():
    """Get RSS fetch history service from main module"""
    import backend.api.main as main_module
    return main_module.rss_fetch_history

def get_source_integration():
    """Get source integration service from main module"""
    import backend.api.main as main_module
    return main_module.source_integration

def get_initialization_error():
    """Get initialization error from main module"""
    import backend.api.main as main_module
    return getattr(main_module, '_initialization_error', None)

# ============================================================================
# Basic Learning Endpoints
# ============================================================================

@router.post("/add", response_model=LearningResponse)
async def add_learning_content(request: LearningRequest):
    """Add learning content to the system"""
    try:
        knowledge_retention = get_knowledge_retention()
        rag_retrieval = get_rag_retrieval()
        content_curator = get_content_curator()
        
        # Add to knowledge retention system
        knowledge_id = None
        if knowledge_retention:
            knowledge_id = knowledge_retention.add_knowledge(
                content=request.content,
                source=request.source,
                knowledge_type=request.content_type,
                metadata=request.metadata
            )
        
        # Add to vector database
        if rag_retrieval:
            # Calculate importance score for knowledge alert system
            importance_score = 0.5
            if content_curator:
                content_dict = {
                    "title": request.metadata.get("title", "") if request.metadata else "",
                    "summary": request.content[:500] if len(request.content) > 500 else request.content,
                    "source": request.source
                }
                importance_score = content_curator.calculate_importance_score(content_dict)
            
            # Merge importance_score into metadata
            enhanced_metadata = request.metadata or {}
            enhanced_metadata["importance_score"] = importance_score
            if not enhanced_metadata.get("title"):
                content_lines = request.content.split("\n")
                if content_lines:
                    enhanced_metadata["title"] = content_lines[0][:200]
            
            success = rag_retrieval.add_learning_content(
                content=request.content,
                source=request.source,
                content_type=request.content_type,
                metadata=enhanced_metadata
            )
            if not success:
                return LearningResponse(
                    success=False,
                    message="Failed to add to vector database"
                )
        
        return LearningResponse(
            success=True,
            knowledge_id=knowledge_id,
            message="Learning content added successfully"
        )
        
    except Exception as e:
        logger.error(f"Learning error: {e}")
        return LearningResponse(
            success=False,
            message=f"Error: {str(e)}"
        )

@router.get("/metrics")
async def get_learning_metrics():
    """Get learning and accuracy metrics"""
    try:
        knowledge_retention = get_knowledge_retention()
        accuracy_scorer = get_accuracy_scorer()
        chroma_client = get_chroma_client()
        
        metrics = {}
        
        # Get retention metrics
        if knowledge_retention:
            metrics["retention"] = knowledge_retention.calculate_retention_metrics()
        
        # Get accuracy metrics
        if accuracy_scorer:
            metrics["accuracy"] = accuracy_scorer.get_accuracy_metrics()
        
        # Get vector DB stats
        if chroma_client:
            metrics["vector_db"] = chroma_client.get_collection_stats()
        
        return metrics
        
    except Exception as e:
        logger.error(f"Metrics error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/retained")
async def get_retained_knowledge(
    limit: int = Query(default=100, ge=1, le=1000, description="Maximum number of items to return"),
    min_score: Optional[float] = Query(default=None, ge=0.0, le=1.0, description="Minimum retention score")
):
    """Get retained knowledge items with full details for audit log
    
    Returns:
        List of retained knowledge items with:
        - Timestamp Added
        - Source URL (Link)
        - Retained Content Snippet (5-10 sentences)
        - Vector ID (Debug)
    """
    try:
        knowledge_retention = get_knowledge_retention()
        rag_retrieval = get_rag_retrieval()
        chroma_client = get_chroma_client()
        
        if not knowledge_retention:
            raise HTTPException(status_code=503, detail="Knowledge retention not available")
        
        # Apply min_score filter if provided
        knowledge = knowledge_retention.get_retained_knowledge(limit=limit)
        
        # Filter by min_score if provided
        if min_score is not None:
            knowledge = [item for item in knowledge if item.get("retention_score", 0.0) >= min_score]
        
        # Enhance with vector IDs and content snippets from RAG
        enhanced_items = []
        for item in knowledge:
            source = item.get("source", "")
            metadata = item.get("metadata", {})
            link = metadata.get("link", source)
            
            # Get content snippet (5-10 sentences)
            content = item.get("content", "")
            sentences = content.split(". ")
            snippet = ". ".join(sentences[:10])  # First 10 sentences
            if len(sentences) > 10:
                snippet += "..."
            
            # Try to get vector ID from RAG if available
            vector_id = None
            if rag_retrieval and chroma_client:
                try:
                    # Try to find the document in ChromaDB by source/link
                    # This is approximate - we'll use metadata to match
                    vector_id = metadata.get("id") or metadata.get("doc_id")
                    if not vector_id and link:
                        # Try to construct ID from link
                        vector_id = f"knowledge_{link[:20].replace('/', '_').replace(':', '_')}"
                except Exception:
                    pass
            
            enhanced_item = {
                "id": item.get("id"),
                "timestamp_added": item.get("created_at") or item.get("last_accessed"),
                "source_url": link,
                "retained_content_snippet": snippet,
                "vector_id": vector_id or f"knowledge_{item.get('id', 'unknown')}",
                "full_content": content,  # Include full content for reference
                "retention_score": item.get("retention_score", 0.0),
                "access_count": item.get("access_count", 0),
                "metadata": metadata
            }
            enhanced_items.append(enhanced_item)
        
        return {
            "knowledge_items": enhanced_items,
            "total": len(enhanced_items)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Retained knowledge error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/accuracy_metrics")
async def get_accuracy_metrics():
    """Get accuracy metrics"""
    try:
        accuracy_scorer = get_accuracy_scorer()
        
        if not accuracy_scorer:
            return {"metrics": {
                "total_responses": 0,
                "average_accuracy": 0.0,
                "trend": "N/A"
            }}
        
        metrics = accuracy_scorer.get_accuracy_metrics()
        return {"metrics": metrics}
        
    except Exception as e:
        logger.error(f"Accuracy metrics error: {e}")
        return {"metrics": {
            "total_responses": 0,
            "average_accuracy": 0.0,
            "trend": "N/A"
        }}

# ============================================================================
# Multi-Source Learning Pipeline Endpoints
# ============================================================================

@router.post("/sources/fetch")
@limiter.limit("5/hour", key_func=get_rate_limit_key_func)  # Multi-source fetch: 5 requests per hour
async def fetch_all_sources(
    request: Request,
    max_items_per_source: int = Query(default=5, ge=1, le=20, description="Maximum items per source"),
    auto_add: bool = Query(default=False, description="Automatically add to RAG"),
    use_pre_filter: bool = Query(default=True, description="Apply pre-filter before adding to RAG")
):
    """Fetch content from all enabled sources (RSS, arXiv, CrossRef, Wikipedia) with detailed status tracking
    
    Args:
        max_items_per_source: Maximum items per source
        auto_add: If True, automatically add to RAG vector DB
        use_pre_filter: If True, apply pre-filter before adding
    """
    try:
        source_integration = get_source_integration()
        rss_fetch_history = _get_rss_fetch_history_service()
        rag_retrieval = get_rag_retrieval()
        
        if not source_integration:
            raise HTTPException(status_code=503, detail="Source integration not available")
        
        # Create fetch cycle for tracking
        cycle_id = None
        if rss_fetch_history:
            cycle_id = rss_fetch_history.create_fetch_cycle(cycle_number=0)  # Manual fetch = cycle 0
        
        # Fetch from all sources
        entries = source_integration.fetch_all_sources(
            max_items_per_source=max_items_per_source,
            use_pre_filter=use_pre_filter
        )
        
        # Track each entry with status (similar to RSS fetch)
        tracked_entries = []
        added_count = 0
        
        if auto_add and rag_retrieval:
            # Process entries (pre-filter already applied if use_pre_filter=True)
            for entry in entries:
                content = f"{entry.get('title', '')}\n{entry.get('summary', entry.get('content', ''))}"
                
                # Check for duplicates
                is_duplicate = False
                if rag_retrieval:
                    try:
                        existing = rag_retrieval.retrieve_context(
                            query=entry.get('title', ''),
                            knowledge_limit=1,
                            conversation_limit=0
                        )
                        if existing.get("knowledge_docs"):
                            existing_doc = existing["knowledge_docs"][0]
                            existing_metadata = existing_doc.get("metadata", {})
                            existing_link = existing_metadata.get("link", "")
                            if existing_link == entry.get("link", "") or existing_link == entry.get("source_url", ""):
                                is_duplicate = True
                    except Exception:
                        pass
                
                if is_duplicate:
                    status = "Filtered: Duplicate"
                    reason = "Content already exists in RAG"
                    if rss_fetch_history and cycle_id:
                        rss_fetch_history.add_fetch_item(
                            cycle_id=cycle_id,
                            title=entry.get("title", ""),
                            source_url=entry.get("source_url", entry.get("source", "")),
                            link=entry.get("link", ""),
                            summary=entry.get("summary", ""),
                            status=status,
                            status_reason=reason
                        )
                    tracked_entries.append({**entry, "status": status, "status_reason": reason})
                    continue
                
                # Try to add to RAG
                vector_id = None
                try:
                    success = rag_retrieval.add_learning_content(
                        content=content,
                        source=entry.get("source", "unknown"),
                        content_type="knowledge",
                        metadata={
                            "link": entry.get("link", ""),
                            "source_url": entry.get("source_url", ""),
                            "published": entry.get("published", datetime.now().isoformat()),
                            "type": entry.get("metadata", {}).get("source_type", "unknown"),
                            "title": entry.get("title", "")[:200],
                            "license": entry.get("metadata", {}).get("license", "Unknown")
                        }
                    )
                    
                    if success:
                        added_count += 1
                        status = "Added to RAG"
                        vector_id = f"knowledge_{entry.get('link', entry.get('source_url', ''))[:8]}"
                        if rss_fetch_history and cycle_id:
                            rss_fetch_history.add_fetch_item(
                                cycle_id=cycle_id,
                                title=entry.get("title", ""),
                                source_url=entry.get("source_url", entry.get("source", "")),
                                link=entry.get("link", ""),
                                summary=entry.get("summary", ""),
                                status=status,
                                vector_id=vector_id,
                                added_to_rag_at=datetime.now().isoformat()
                            )
                        tracked_entries.append({**entry, "status": status, "vector_id": vector_id})
                    else:
                        status = "Filtered: Low Score"
                        reason = "Failed to add to RAG"
                        if rss_fetch_history and cycle_id:
                            rss_fetch_history.add_fetch_item(
                                cycle_id=cycle_id,
                                title=entry.get("title", ""),
                                source_url=entry.get("source_url", entry.get("source", "")),
                                link=entry.get("link", ""),
                                summary=entry.get("summary", ""),
                                status=status,
                                status_reason=reason
                            )
                        tracked_entries.append({**entry, "status": status, "status_reason": reason})
                except Exception as add_error:
                    status = "Filtered: Low Score"
                    reason = f"Error adding to RAG: {str(add_error)[:100]}"
                    if rss_fetch_history and cycle_id:
                        rss_fetch_history.add_fetch_item(
                            cycle_id=cycle_id,
                            title=entry.get("title", ""),
                            source_url=entry.get("source_url", entry.get("source", "")),
                            link=entry.get("link", ""),
                            summary=entry.get("summary", ""),
                            status=status,
                            status_reason=reason
                        )
                    tracked_entries.append({**entry, "status": status, "status_reason": reason})
        else:
            # If not auto_add, just track as fetched
            for entry in entries:
                status = "Fetched (not added)"
                if rss_fetch_history and cycle_id:
                    rss_fetch_history.add_fetch_item(
                        cycle_id=cycle_id,
                        title=entry.get("title", ""),
                        source_url=entry.get("source_url", entry.get("source", "")),
                        link=entry.get("link", ""),
                        summary=entry.get("summary", ""),
                        status=status
                    )
                tracked_entries.append({**entry, "status": status})
        
        # Complete cycle
        if rss_fetch_history and cycle_id:
            rss_fetch_history.complete_fetch_cycle(cycle_id)
        
        return {
            "status": "success",
            "entries_fetched": len(entries),
            "entries_added": added_count,
            "entries_filtered": len(tracked_entries) - added_count,
            "entries": tracked_entries[:50],  # Limit response size
            "cycle_id": cycle_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Multi-source fetch error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/sources/stats")
async def get_source_stats():
    """Get statistics for all enabled sources"""
    try:
        source_integration = get_source_integration()
        
        if not source_integration:
            return {"status": "not_available"}
        
        stats = source_integration.get_source_stats()
        return {
            "status": "ok",
            **stats
        }
    except Exception as e:
        logger.error(f"Source stats error: {e}")
        return {"status": "error", "message": str(e)}

# ============================================================================
# RSS Learning Pipeline Endpoints (kept for backward compatibility)
# ============================================================================

@router.post("/rss/fetch")
@limiter.limit("5/hour", key_func=get_rate_limit_key_func)  # RSS fetch: 5 requests per hour (can be expensive)
async def fetch_rss_content(
    request: Request,
    max_items: int = Query(default=5, ge=1, le=50, description="Maximum items per feed"),
    auto_add: bool = Query(default=False, description="Automatically add to RAG")
):
    """Fetch content from RSS feeds with detailed status tracking
    
    Args:
        max_items: Maximum items per feed
        auto_add: If True, automatically add to RAG vector DB
    """
    try:
        rss_fetcher = get_rss_fetcher()
        rss_fetch_history = _get_rss_fetch_history_service()
        rag_retrieval = get_rag_retrieval()
        content_curator = get_content_curator()
        
        if not rss_fetcher:
            raise HTTPException(status_code=503, detail="RSS fetcher not available")
        
        # Create fetch cycle for tracking
        cycle_id = None
        if rss_fetch_history:
            cycle_id = rss_fetch_history.create_fetch_cycle(cycle_number=0)  # Manual fetch = cycle 0
        
        entries = rss_fetcher.fetch_feeds(max_items_per_feed=max_items)
        
        # Track each entry with status
        tracked_entries = []
        added_count = 0
        
        if auto_add and rag_retrieval:
            # Pre-filter if content curator available
            if content_curator:
                filtered_entries, rejected_entries = content_curator.pre_filter_content(entries)
                
                # Track rejected entries (Low Score)
                for rejected in rejected_entries:
                    status = "Filtered: Low Score"
                    reason = rejected.get("rejection_reason", "Low quality/Short content")
                    if rss_fetch_history and cycle_id:
                        rss_fetch_history.add_fetch_item(
                            cycle_id=cycle_id,
                            title=rejected.get("title", ""),
                            source_url=rejected.get("source", ""),
                            link=rejected.get("link", ""),
                            summary=rejected.get("summary", ""),
                            status=status,
                            status_reason=reason
                        )
                    tracked_entries.append({
                        **rejected,
                        "status": status,
                        "status_reason": reason
                    })
                
                entries = filtered_entries
            
            # Process filtered entries
            for entry in entries:
                content = f"{entry['title']}\n{entry['summary']}"
                
                # Check for duplicates (simple check - could be enhanced with semantic similarity)
                is_duplicate = False
                if rag_retrieval:
                    try:
                        # Try to find similar content in RAG
                        existing = rag_retrieval.retrieve_context(
                            query=entry['title'],
                            knowledge_limit=1,
                            conversation_limit=0
                        )
                        if existing.get("knowledge_docs"):
                            # Check if title matches closely
                            existing_doc = existing["knowledge_docs"][0]
                            existing_metadata = existing_doc.get("metadata", {})
                            existing_link = existing_metadata.get("link", "")
                            if existing_link == entry.get("link", ""):
                                is_duplicate = True
                    except Exception:
                        pass  # If check fails, assume not duplicate
                
                if is_duplicate:
                    status = "Filtered: Duplicate"
                    reason = "Content already exists in RAG"
                    if rss_fetch_history and cycle_id:
                        rss_fetch_history.add_fetch_item(
                            cycle_id=cycle_id,
                            title=entry.get("title", ""),
                            source_url=entry.get("source", ""),
                            link=entry.get("link", ""),
                            summary=entry.get("summary", ""),
                            status=status,
                            status_reason=reason
                        )
                    tracked_entries.append({
                        **entry,
                        "status": status,
                        "status_reason": reason
                    })
                    continue
                
                # Try to add to RAG
                vector_id = None
                try:
                    success = rag_retrieval.add_learning_content(
                        content=content,
                        source=entry['source'],
                        content_type="knowledge",
                        metadata={
                            "link": entry['link'],
                            "published": entry['published'],
                            "type": "rss_feed",
                            "title": entry.get('title', '')[:200]
                        }
                    )
                    
                    if success:
                        added_count += 1
                        status = "Added to RAG"
                        # Try to get vector ID (may not be available immediately)
                        vector_id = f"knowledge_{entry.get('link', '')[:8]}"
                        if rss_fetch_history and cycle_id:
                            rss_fetch_history.add_fetch_item(
                                cycle_id=cycle_id,
                                title=entry.get("title", ""),
                                source_url=entry.get("source", ""),
                                link=entry.get("link", ""),
                                summary=entry.get("summary", ""),
                                status=status,
                                vector_id=vector_id,
                                added_to_rag_at=datetime.now().isoformat()
                            )
                        tracked_entries.append({
                            **entry,
                            "status": status,
                            "vector_id": vector_id
                        })
                    else:
                        status = "Filtered: Low Score"
                        reason = "Failed to add to RAG"
                        if rss_fetch_history and cycle_id:
                            rss_fetch_history.add_fetch_item(
                                cycle_id=cycle_id,
                                title=entry.get("title", ""),
                                source_url=entry.get("source", ""),
                                link=entry.get("link", ""),
                                summary=entry.get("summary", ""),
                                status=status,
                                status_reason=reason
                            )
                        tracked_entries.append({
                            **entry,
                            "status": status,
                            "status_reason": reason
                        })
                except Exception as add_error:
                    status = "Filtered: Low Score"
                    reason = f"Error adding to RAG: {str(add_error)[:100]}"
                    if rss_fetch_history and cycle_id:
                        rss_fetch_history.add_fetch_item(
                            cycle_id=cycle_id,
                            title=entry.get("title", ""),
                            source_url=entry.get("source", ""),
                            link=entry.get("link", ""),
                            summary=entry.get("summary", ""),
                            status=status,
                            status_reason=reason
                        )
                    tracked_entries.append({
                        **entry,
                        "status": status,
                        "status_reason": reason
                    })
        else:
            # If not auto_add, just track as fetched
            for entry in entries:
                status = "Fetched (not added)"
                if rss_fetch_history and cycle_id:
                    rss_fetch_history.add_fetch_item(
                        cycle_id=cycle_id,
                        title=entry.get("title", ""),
                        source_url=entry.get("source", ""),
                        link=entry.get("link", ""),
                        summary=entry.get("summary", ""),
                        status=status
                    )
                tracked_entries.append({
                    **entry,
                    "status": status
                })
        
        # Complete cycle
        if rss_fetch_history and cycle_id:
            rss_fetch_history.complete_fetch_cycle(cycle_id)
        
        return {
            "status": "success",
            "entries_fetched": len(entries),
            "entries_added": added_count if auto_add else 0,
            "entries": tracked_entries[:10]  # Return first 10 for preview
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"RSS fetch error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/rss/fetch-history")
async def get_rss_fetch_history(limit: int = 100):
    """Get latest RSS fetch items with detailed status from the most recent cycle
    
    Args:
        limit: Maximum number of items to return
        
    Returns:
        List of fetch items with status (Source URL, Title, Fetch Timestamp, STATUS)
    """
    try:
        rss_fetch_history = _get_rss_fetch_history_service()
        
        if not rss_fetch_history:
            raise HTTPException(status_code=503, detail="RSS fetch history not available")
        
        items = rss_fetch_history.get_latest_fetch_items(limit=limit)
        return {
            "items": items,
            "total": len(items)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"RSS fetch history error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/rss/stats")
async def get_rss_stats():
    """Get RSS pipeline statistics"""
    try:
        rss_fetcher = get_rss_fetcher()
        
        if not rss_fetcher:
            return {"feeds_configured": 0, "status": "not_available"}
        
        return {
            "feeds_configured": len(rss_fetcher.feeds),
            "status": "ready",
            "feeds": rss_fetcher.feeds
        }
    except Exception as e:
        logger.error(f"RSS stats error: {e}")
        return {"feeds_configured": 0, "status": "error"}

# ============================================================================
# Automated Scheduler Endpoints
# ============================================================================

@router.post("/scheduler/start", dependencies=[Depends(require_api_key)])
async def start_scheduler():
    """
    Start automated learning scheduler
    
    Security: This endpoint requires API key authentication via X-API-Key header.
    """
    try:
        learning_scheduler = get_learning_scheduler()
        
        if not learning_scheduler:
            raise HTTPException(status_code=503, detail="Scheduler not available")
        
        if learning_scheduler.is_running:
            return {"status": "already_running", "message": "Scheduler is already running"}
        
        await learning_scheduler.start()
        return {
            "status": "started",
            "message": "Scheduler started successfully",
            "interval_hours": learning_scheduler.interval_hours,
            "next_run": learning_scheduler.next_run_time.isoformat() if learning_scheduler.next_run_time else None
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Start scheduler error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/scheduler/stop", dependencies=[Depends(require_api_key)])
async def stop_scheduler():
    """
    Stop automated learning scheduler
    
    Security: This endpoint requires API key authentication via X-API-Key header.
    """
    try:
        learning_scheduler = get_learning_scheduler()
        
        if not learning_scheduler:
            raise HTTPException(status_code=503, detail="Scheduler not available")
        
        if not learning_scheduler.is_running:
            return {"status": "not_running", "message": "Scheduler is not running"}
        
        await learning_scheduler.stop()
        return {
            "status": "stopped",
            "message": "Scheduler stopped successfully"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Stop scheduler error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/scheduler/status")
async def get_scheduler_status():
    """Get scheduler status"""
    try:
        learning_scheduler = get_learning_scheduler()
        _initialization_error = get_initialization_error()
        
        # Debug logging
        logger.info(f"get_scheduler_status called. learning_scheduler is None: {learning_scheduler is None}")
        logger.info(f"_initialization_error: {_initialization_error}")
        
        if not learning_scheduler:
            # Provide more detailed error message
            error_msg = "Scheduler not initialized"
            if _initialization_error:
                error_msg = f"Scheduler not initialized: {_initialization_error}"
            logger.warning(f"Returning not_available status: {error_msg}")
            # Return proper JSON response, not empty
            return {
                "status": "not_available",
                "message": error_msg,
                "initialization_error": _initialization_error if _initialization_error else None,
                "is_running": False,
                "interval_hours": 4,
                "auto_add_to_rag": False,
                "cycle_count": 0,
                "last_run_time": None,
                "next_run_time": None,
                "feeds_configured": 0
            }
        
        # Get status from scheduler
        status = learning_scheduler.get_status()
        logger.info(f"Scheduler status retrieved successfully: {status}")
        
        return {
            "status": "ok",
            **status
        }
    except Exception as e:
        logger.error(f"Scheduler status error: {e}", exc_info=True)
        # Return proper JSON response even on error, not empty
        return {
            "status": "error",
            "message": str(e),
            "is_running": False,
            "interval_hours": 4,
            "auto_add_to_rag": False,
            "cycle_count": 0,
            "last_run_time": None,
            "next_run_time": None,
            "feeds_configured": 0
        }

@router.post("/scheduler/run-now")
async def run_scheduler_now(request: Request, sync: bool = Query(False, description="Run synchronously (for tests)")):
    """
    Manually trigger a learning cycle immediately with detailed status tracking.
    
    By default, returns 202 Accepted immediately and runs in background.
    Use ?sync=true for synchronous execution (for tests).
    """
    try:
        learning_scheduler = get_learning_scheduler()
        
        if not learning_scheduler:
            raise HTTPException(status_code=503, detail="Scheduler not available")
        
        # For sync mode (tests), run synchronously
        if sync:
            return await _run_learning_cycle_sync()
        
        # Non-blocking mode: create job and return immediately
        job_queue = get_job_queue()
        job_id = job_queue.create_job()
        
        # Start background task
        from backend.api.routers.learning_router_background import run_learning_cycle_background
        asyncio.create_task(run_learning_cycle_background(job_id))
        
        from fastapi import Response
        import json
        return Response(
            content=json.dumps({
                "status": "accepted",
                "job_id": job_id,
                "message": "Learning cycle started in background. Use GET /api/learning/scheduler/job-status/{job_id} to check progress."
            }),
            media_type="application/json",
            status_code=status.HTTP_202_ACCEPTED
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Run scheduler now error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


async def _run_learning_cycle_sync():
    """Synchronous learning cycle execution (for tests)"""
    learning_scheduler = get_learning_scheduler()
    rss_fetch_history = _get_rss_fetch_history_service()
    rag_retrieval = get_rag_retrieval()
    source_integration = get_source_integration()
    content_curator = get_content_curator()
    self_diagnosis = get_self_diagnosis()
    
    result = await learning_scheduler.run_learning_cycle()
    cycle_number = result.get("cycle_number", 0)
    cycle_id_str = f"cycle_{cycle_number}"
    
    # Create fetch cycle for tracking
    cycle_id = None
    if rss_fetch_history:
        cycle_id = rss_fetch_history.create_fetch_cycle(cycle_number=cycle_number)
    
    # ============================================================================
    # 70/30 LEARNING ALLOCATION SYSTEM
    # ============================================================================
    # Total learning capacity per cycle
    LEARNING_CAPACITY_PER_CYCLE = 10  # Total items StillMe can learn per cycle
    
    # Allocation split: 70% automatic, 30% community
    AUTOMATIC_LEARNING_QUOTA = int(LEARNING_CAPACITY_PER_CYCLE * 0.7)  # 7 items
    COMMUNITY_LEARNING_QUOTA = int(LEARNING_CAPACITY_PER_CYCLE * 0.3)  # 3 items
    
    all_entries_to_add = []
    community_items_added = 0
    automatic_items_added = 0
    
    # STEP 1: Process Community Proposals (30% quota - PRIORITY)
    try:
        from backend.services.community_proposals import get_community_proposals
        from backend.services.url_fetcher import get_url_fetcher
        
        community = get_community_proposals()
        url_fetcher = get_url_fetcher()
        
        approved_proposals = community.get_approved_proposals_not_learned(limit=COMMUNITY_LEARNING_QUOTA)
        
        logger.info(f"Found {len(approved_proposals)} approved community proposals to learn")
        
        for proposal in approved_proposals[:COMMUNITY_LEARNING_QUOTA]:
            try:
                # Fetch content from proposal URL
                content_data = url_fetcher.fetch_content(
                    url=proposal["source_url"],
                    proposal_type=proposal["proposal_type"]
                )
                
                if not content_data or not content_data.get("success"):
                    logger.warning(f"Failed to fetch content for proposal {proposal['proposal_id']}")
                    continue
                
                # Prepare entry for RAG
                entry = {
                    "title": content_data.get("title", proposal.get("description", "Community Proposal")),
                    "summary": content_data.get("summary", ""),
                    "link": content_data.get("link", proposal["source_url"]),
                    "published": content_data.get("published", datetime.now().isoformat()),
                    "source": f"community_proposal:{proposal['proposal_id']}",
                    "content_type": "community_proposal",
                    "proposal_id": proposal["proposal_id"],
                    "proposal_type": proposal["proposal_type"],
                    "description": proposal.get("description", "")
                }
                
                # Add full content if available
                if content_data.get("full_content"):
                    entry["full_content"] = content_data["full_content"]
                
                all_entries_to_add.append(entry)
                community_items_added += 1
                
                logger.info(f"Community proposal {proposal['proposal_id']} prepared for learning")
            except Exception as e:
                logger.error(f"Error processing community proposal {proposal.get('proposal_id', 'unknown')}: {e}")
                continue
    except Exception as e:
        logger.error(f"Error processing community proposals: {e}")
    
    # Calculate remaining quota for automatic learning
    remaining_quota = LEARNING_CAPACITY_PER_CYCLE - community_items_added
    automatic_quota = min(AUTOMATIC_LEARNING_QUOTA, remaining_quota)
    
    logger.info(f"Learning allocation: {community_items_added} community items, {automatic_quota} automatic items (quota: {COMMUNITY_LEARNING_QUOTA}/{AUTOMATIC_LEARNING_QUOTA})")
    
    # STEP 2: Process Automatic Sources (70% quota, or remaining if community used less)
    if learning_scheduler.auto_add_to_rag and rag_retrieval:
        # Use entries from the learning cycle result (already fetched)
        # Don't fetch again - use the entries that were already fetched in run_learning_cycle
        entries_to_add = []
        filtered_count = 0
        
        # Fetch from all sources using SourceIntegration
        try:
            # Use SourceIntegration to fetch from all enabled sources
            if source_integration:
                all_entries = source_integration.fetch_all_sources(
                    max_items_per_source=5,
                    use_pre_filter=False  # We'll apply pre-filter manually to track rejected items
                )
                logger.info(f"Fetched {len(all_entries)} entries from all sources (RSS + arXiv + CrossRef + Wikipedia)")
            else:
                # Fallback to RSS only
                all_entries = learning_scheduler.rss_fetcher.fetch_feeds(max_items_per_feed=5)
                logger.info(f"Fetched {len(all_entries)} entries from RSS (SourceIntegration not available)")
            
            # STEP 1: Pre-Filter (BEFORE embedding) to reduce costs
            if content_curator:
                filtered_entries, rejected_entries = content_curator.pre_filter_content(all_entries)
                filtered_count = len(rejected_entries)
                logger.info(
                    f"Pre-Filter: {len(filtered_entries)}/{len(all_entries)} passed. "
                    f"Rejected {filtered_count} items (saving embedding costs)"
                )
                
                # Track rejected entries (Low Score)
                for rejected in rejected_entries:
                    status = "Filtered: Low Score"
                    reason = rejected.get("rejection_reason", "Low quality/Short content")
                    if rss_fetch_history and cycle_id:
                        rss_fetch_history.add_fetch_item(
                            cycle_id=cycle_id,
                            title=rejected.get("title", ""),
                            source_url=rejected.get("source", ""),
                            link=rejected.get("link", ""),
                            summary=rejected.get("summary", ""),
                            status=status,
                            status_reason=reason
                        )
                
                # Use filtered entries for further processing
                all_entries = filtered_entries
            else:
                logger.warning("Content curator not available, skipping pre-filter (may increase costs)")
            
            # STEP 2: Prioritize content if curator and self_diagnosis available
            if content_curator and self_diagnosis:
                # Get knowledge gaps to prioritize
                recent_gaps = []  # Could be from query history
                prioritized = content_curator.prioritize_learning_content(
                    all_entries,
                    knowledge_gaps=recent_gaps
                )
                # Take top entries up to automatic quota
                entries_to_add = prioritized[:min(automatic_quota, len(prioritized))]
                logger.info(f"Content curator prioritized {len(entries_to_add)} entries from {len(all_entries)} total (quota: {automatic_quota})")
            else:
                # If no curator, add entries up to automatic quota
                entries_to_add = all_entries[:min(automatic_quota, len(all_entries))]
                logger.info(f"No content curator, adding {len(entries_to_add)} entries directly (quota: {automatic_quota})")
            
            # Add automatic entries to the list
            all_entries_to_add.extend(entries_to_add)
            automatic_items_added = len(entries_to_add)
            
        except Exception as e:
            logger.error(f"Error preparing entries for RAG: {e}")
            entries_to_add = []
        
        # STEP 3: Add all entries (community + automatic) to RAG
        added_count = 0
        for entry in all_entries_to_add:
            try:
                content = f"{entry.get('title', '')}\n{entry.get('summary', '')}"
                if not content.strip():
                    logger.warning(f"Skipping empty entry: {entry.get('title', 'No title')}")
                    continue
                
                # Check for duplicates
                is_duplicate = False
                try:
                    existing = rag_retrieval.retrieve_context(
                        query=entry.get('title', ''),
                        knowledge_limit=1,
                        conversation_limit=0
                    )
                    if existing.get("knowledge_docs"):
                        existing_doc = existing["knowledge_docs"][0]
                        existing_metadata = existing_doc.get("metadata", {})
                        existing_link = existing_metadata.get("link", "")
                        if existing_link == entry.get("link", ""):
                            is_duplicate = True
                except Exception:
                    pass
                
                if is_duplicate:
                    status = "Filtered: Duplicate"
                    reason = "Content already exists in RAG"
                    if rss_fetch_history and cycle_id:
                        rss_fetch_history.add_fetch_item(
                            cycle_id=cycle_id,
                            title=entry.get("title", ""),
                            source_url=entry.get("source", ""),
                            link=entry.get("link", ""),
                            summary=entry.get("summary", ""),
                            status=status,
                            status_reason=reason
                        )
                    continue
                
                # Calculate importance score for knowledge alert system
                importance_score = 0.5
                if content_curator:
                    importance_score = content_curator.calculate_importance_score(entry)
                
                vector_id = None
                success = rag_retrieval.add_learning_content(
                    content=content,
                    source=entry.get('source', 'rss'),
                    content_type="knowledge",
                    metadata={
                        "link": entry.get('link', ''),
                        "published": entry.get('published', ''),
                        "type": "rss_feed",
                        "scheduler_cycle": result.get("cycle_number", 0),
                        "priority_score": entry.get("priority_score", 0.5),
                        "importance_score": importance_score,
                        "title": entry.get('title', '')[:200]  # Store title for knowledge alert
                    }
                )
                if success:
                    added_count += 1
                    status = "Added to RAG"
                    vector_id = f"knowledge_{entry.get('link', '')[:8]}"
                    
                    # If this is a community proposal, mark it as learned
                    if entry.get("proposal_id"):
                        try:
                            from backend.services.community_proposals import get_community_proposals
                            community = get_community_proposals()
                            community.mark_proposal_as_learned(
                                proposal_id=entry["proposal_id"],
                                cycle_id=cycle_id_str
                            )
                            logger.info(f"Marked community proposal {entry['proposal_id']} as learned")
                        except Exception as e:
                            logger.error(f"Error marking proposal as learned: {e}")
                    
                    if rss_fetch_history and cycle_id:
                        rss_fetch_history.add_fetch_item(
                            cycle_id=cycle_id,
                            title=entry.get("title", ""),
                            source_url=entry.get("source", ""),
                            link=entry.get("link", ""),
                            summary=entry.get("summary", ""),
                            status=status,
                            vector_id=vector_id,
                            added_to_rag_at=datetime.now().isoformat()
                        )
                    logger.info(f"Added entry to RAG: {entry.get('title', 'No title')[:50]}")
                else:
                    status = "Filtered: Low Score"
                    reason = "Failed to add to RAG"
                    if rss_fetch_history and cycle_id:
                        rss_fetch_history.add_fetch_item(
                            cycle_id=cycle_id,
                            title=entry.get("title", ""),
                            source_url=entry.get("source", ""),
                            link=entry.get("link", ""),
                            summary=entry.get("summary", ""),
                            status=status,
                            status_reason=reason
                        )
                    logger.warning(f"Failed to add entry to RAG: {entry.get('title', 'No title')[:50]}")
            except Exception as e:
                status = "Filtered: Low Score"
                reason = f"Error adding to RAG: {str(e)[:100]}"
                if rss_fetch_history and cycle_id:
                    rss_fetch_history.add_fetch_item(
                        cycle_id=cycle_id,
                        title=entry.get("title", ""),
                        source_url=entry.get("source", ""),
                        link=entry.get("link", ""),
                        summary=entry.get("summary", ""),
                        status=status,
                        status_reason=reason
                    )
                logger.error(f"Error adding entry to RAG: {e}")
                continue
        
        result["entries_added_to_rag"] = added_count
        result["entries_filtered"] = filtered_count
        result["community_items_added"] = community_items_added
        result["automatic_items_added"] = automatic_items_added
        result["learning_allocation"] = {
            "total_capacity": LEARNING_CAPACITY_PER_CYCLE,
            "community_quota": COMMUNITY_LEARNING_QUOTA,
            "automatic_quota": AUTOMATIC_LEARNING_QUOTA,
            "community_used": community_items_added,
            "automatic_used": automatic_items_added,
            "allocation_percentage": {
                "community": round((community_items_added / LEARNING_CAPACITY_PER_CYCLE) * 100, 1) if LEARNING_CAPACITY_PER_CYCLE > 0 else 0,
                "automatic": round((automatic_items_added / LEARNING_CAPACITY_PER_CYCLE) * 100, 1) if LEARNING_CAPACITY_PER_CYCLE > 0 else 0
            }
        }
        
        # Complete cycle
        if rss_fetch_history and cycle_id:
            rss_fetch_history.complete_fetch_cycle(cycle_id)
        
        logger.info(
            f"Learning cycle: Fetched {result.get('entries_fetched', 0)} entries, "
            f"Filtered {filtered_count} (Low quality/Short), "
            f"Added {added_count} to RAG "
            f"(Community: {community_items_added}/{COMMUNITY_LEARNING_QUOTA}, "
            f"Automatic: {automatic_items_added}/{AUTOMATIC_LEARNING_QUOTA})"
        )
    
    return result


@router.get("/scheduler/job-status/{job_id}")
async def get_job_status(job_id: str):
    """
    Get status of a learning cycle job.
    
    Returns job status, progress, and result (when completed).
    """
    try:
        job_queue = get_job_queue()
        job = job_queue.get_job(job_id)
        
        if not job:
            raise HTTPException(status_code=404, detail=f"Job {job_id} not found")
        
        return job.to_dict()
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get job status error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/scheduler/job-logs/{job_id}")
async def get_job_logs(job_id: str):
    """
    Get logs for a learning cycle job.
    
    Returns all log messages for the job.
    """
    try:
        job_queue = get_job_queue()
        job = job_queue.get_job(job_id)
        
        if not job:
            raise HTTPException(status_code=404, detail=f"Job {job_id} not found")
        
        return {
            "job_id": job_id,
            "logs": job.logs
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get job logs error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# Self-Diagnosis & Content Curation Endpoints
# ============================================================================

@router.post("/self-diagnosis/check-gap")
async def check_knowledge_gap(query: str, threshold: float = 0.5):
    """Check if there's a knowledge gap for a query"""
    try:
        self_diagnosis = get_self_diagnosis()
        
        if not self_diagnosis:
            raise HTTPException(status_code=503, detail="Self-diagnosis not available")
        
        result = self_diagnosis.identify_knowledge_gaps(query, threshold)
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Knowledge gap check error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/self-diagnosis/analyze-coverage")
async def analyze_coverage(topics: List[str]):
    """Analyze knowledge coverage across multiple topics"""
    try:
        self_diagnosis = get_self_diagnosis()
        
        if not self_diagnosis:
            raise HTTPException(status_code=503, detail="Self-diagnosis not available")
        
        result = self_diagnosis.analyze_knowledge_coverage(topics)
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Coverage analysis error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/self-diagnosis/suggest-focus")
async def suggest_learning_focus(recent_queries: Optional[List[str]] = None, limit: int = 5):
    """Suggest learning focus based on knowledge gaps"""
    try:
        self_diagnosis = get_self_diagnosis()
        
        if not self_diagnosis:
            return {"suggestions": [], "reason": "Self-diagnosis not available"}
        
        # If no queries provided, return empty
        if not recent_queries:
            recent_queries = []
        
        suggestions = self_diagnosis.suggest_learning_focus(recent_queries, limit)
        return {
            "suggestions": suggestions,
            "count": len(suggestions)
        }
    except Exception as e:
        logger.error(f"Learning focus suggestion error: {e}")
        return {"suggestions": [], "error": str(e)}

@router.post("/curator/prioritize")
async def prioritize_content(content_list: List[Dict[str, Any]]):
    """Prioritize learning content"""
    try:
        content_curator = get_content_curator()
        self_diagnosis = get_self_diagnosis()
        
        if not content_curator:
            raise HTTPException(status_code=503, detail="Content curator not available")
        
        # Get knowledge gaps from self-diagnosis
        knowledge_gaps = []
        if self_diagnosis and content_list:
            # Extract topics from content
            topics = [item.get("title", "")[:50] for item in content_list[:10]]
            coverage = self_diagnosis.analyze_knowledge_coverage(topics)
            knowledge_gaps = coverage.get("gap_topics", [])
        
        prioritized = content_curator.prioritize_learning_content(
            content_list,
            knowledge_gaps=knowledge_gaps
        )
        return {
            "prioritized_content": prioritized,
            "total_items": len(prioritized)
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Content prioritization error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/nested-learning/metrics")
async def get_nested_learning_metrics():
    """
    Get Nested Learning metrics (tier distribution, update frequency, cost reduction)
    Requires ENABLE_CONTINUUM_MEMORY=true
    """
    import os
    ENABLE_CONTINUUM_MEMORY = os.getenv("ENABLE_CONTINUUM_MEMORY", "false").lower() == "true"
    
    if not ENABLE_CONTINUUM_MEMORY:
        return {
            "enabled": False,
            "message": "Nested Learning is disabled. Set ENABLE_CONTINUUM_MEMORY=true to enable."
        }
    
    try:
        from backend.api.metrics_collector import get_metrics_collector
        
        # CRITICAL: Force reload module to avoid Python cache issues
        # If code was updated but module was cached, this ensures we get the latest version
        import sys
        import importlib
        if 'backend.learning.continuum_memory' in sys.modules:
            importlib.reload(sys.modules['backend.learning.continuum_memory'])
        
        # Import after reload to ensure we get the latest version
        from backend.learning.continuum_memory import ContinuumMemory, TIER_UPDATE_FREQUENCY
        
        metrics = get_metrics_collector()
        all_metrics = metrics.get_metrics()
        nested_metrics = all_metrics.get("nested_learning", {})
        
        # Get tier distribution from database
        
        continuum_memory = ContinuumMemory()
        
        # Try to get tier stats - handle both old and new method names for compatibility
        try:
            tier_stats = continuum_memory.get_tier_stats()
        except AttributeError as e:
            # Check if it's the old method name issue
            if 'get_tier_statistics' in str(e) or 'get_tier_stats' in str(e):
                logger.error(f"❌ CRITICAL: ContinuumMemory class is outdated. Method not found: {e}")
                logger.error("   This usually means Python module cache needs to be cleared.")
                logger.error("   Solution: Restart the backend service to clear Python cache.")
                # Return error response instead of empty stats
                raise HTTPException(
                    status_code=500,
                    detail=f"ContinuumMemory class is outdated. Please restart the backend service to clear Python module cache. Error: {str(e)}"
                )
            # Other AttributeError - use fallback
            logger.warning(f"get_tier_stats() not available, using fallback: {e}")
            tier_stats = {"L0": 0, "L1": 0, "L2": 0, "L3": 0, "total": 0, "promoted_7d": 0, "demoted_7d": 0}
        
        # Update metrics collector with tier distribution
        # get_tier_stats() returns {"L0": count, "L1": count, ...}
        tier_counts = {k: v for k, v in tier_stats.items() if k in ["L0", "L1", "L2", "L3"]}
        for tier, count in tier_counts.items():
            metrics.update_tier_distribution(tier, count)
        
        # Calculate cost reduction estimate
        total_operations = nested_metrics.get("embedding_operations_total", 0)
        skipped_operations = sum(nested_metrics.get("tier_skipped_counts", {}).values())
        cost_reduction_pct = 0.0
        if total_operations > 0:
            cost_reduction_pct = (skipped_operations / (total_operations + skipped_operations)) * 100
        
        return {
            "enabled": True,
            "cycle_count": nested_metrics.get("cycle_count", 0),
            "tier_distribution": tier_counts,
            "tier_update_frequency": TIER_UPDATE_FREQUENCY,
            "tier_update_counts": nested_metrics.get("tier_update_counts", {}),
            "tier_skipped_counts": nested_metrics.get("tier_skipped_counts", {}),
            "embedding_operations": {
                "total": nested_metrics.get("embedding_operations_total", 0),
                "by_tier": nested_metrics.get("embedding_operations_by_tier", {})
            },
            "cost_reduction": {
                "skipped_operations": skipped_operations,
                "total_operations": total_operations + skipped_operations,
                "reduction_percentage": round(cost_reduction_pct, 2)
            },
            "surprise_score_stats": nested_metrics.get("surprise_score_stats", {})
        }
    except Exception as e:
        logger.error(f"Error getting Nested Learning metrics: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting metrics: {str(e)}")

@router.get("/curator/stats")
async def get_curation_stats():
    """Get content curation statistics"""
    try:
        content_curator = get_content_curator()
        
        if not content_curator:
            return {"status": "not_available"}
        
        stats = content_curator.get_curation_stats()
        return {
            "status": "ok",
            **stats
        }
    except Exception as e:
        logger.error(f"Curation stats error: {e}")
        return {"status": "error", "message": str(e)}

@router.post("/curator/update-source-quality", dependencies=[Depends(require_api_key)])
async def update_source_quality(source: str, quality_score: float):
    """
    Update quality score for a source
    
    Security: This endpoint requires API key authentication via X-API-Key header.
    """
    try:
        content_curator = get_content_curator()
        
        if not content_curator:
            raise HTTPException(status_code=503, detail="Content curator not available")
        
        if not 0.0 <= quality_score <= 1.0:
            raise HTTPException(status_code=400, detail="Quality score must be between 0.0 and 1.0")
        
        content_curator.update_source_quality(source, quality_score)
        return {
            "status": "updated",
            "source": source,
            "quality_score": quality_score
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Update source quality error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

