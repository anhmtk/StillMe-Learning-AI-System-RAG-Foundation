"""
RAG Router for StillMe API
Handles all RAG-related endpoints
"""

from fastapi import APIRouter, Request, HTTPException, Depends
from backend.api.models import LearningRequest, RAGQueryRequest, RAGQueryResponse
from backend.api.rate_limiter import limiter, get_rate_limit_key_func
from backend.api.auth import require_api_key
import logging
import os
import shutil

logger = logging.getLogger(__name__)

router = APIRouter()

# Import global services from main (temporary - will refactor to dependency injection later)
# These are initialized in main.py before routers are included
def get_rag_retrieval():
    """Get RAG retrieval service from main module"""
    import backend.api.main as main_module
    return main_module.rag_retrieval

def get_chroma_client():
    """Get ChromaDB client from main module"""
    import backend.api.main as main_module
    return main_module.chroma_client

def get_content_curator():
    """Get content curator service from main module"""
    import backend.api.main as main_module
    return main_module.content_curator

@router.post("/add_knowledge")
@limiter.limit("20/hour", key_func=get_rate_limit_key_func)  # RAG add: 20 requests per hour (expensive)
async def add_knowledge_rag(request: Request, learning_request: LearningRequest):
    """Add knowledge to RAG vector database"""
    try:
        rag_retrieval = get_rag_retrieval()
        content_curator = get_content_curator()
        
        if not rag_retrieval:
            raise HTTPException(status_code=503, detail="RAG system not available")
        
        # Calculate importance score for knowledge alert system
        importance_score = 0.5
        if content_curator:
            # Create a content dict for importance calculation
            content_dict = {
                "title": learning_request.metadata.get("title", "") if learning_request.metadata else "",
                "summary": learning_request.content[:500] if len(learning_request.content) > 500 else learning_request.content,
                "source": learning_request.source
            }
            importance_score = content_curator.calculate_importance_score(content_dict)
        
        # Merge importance_score into metadata
        enhanced_metadata = learning_request.metadata or {}
        enhanced_metadata["importance_score"] = importance_score
        if not enhanced_metadata.get("title"):
            # Extract title from content if not provided
            content_lines = learning_request.content.split("\n")
            if content_lines:
                enhanced_metadata["title"] = content_lines[0][:200]
        
        success = rag_retrieval.add_learning_content(
            content=learning_request.content,
            source=learning_request.source,
            content_type=learning_request.content_type,
            metadata=enhanced_metadata
        )
        
        if success:
            return {"status": "Knowledge added successfully", "content_type": learning_request.content_type}
        else:
            raise HTTPException(status_code=500, detail="Failed to add knowledge to vector DB")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"RAG add knowledge error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/query", response_model=RAGQueryResponse)
async def query_rag(request: RAGQueryRequest):
    """Query RAG system for relevant context"""
    try:
        rag_retrieval = get_rag_retrieval()
        
        if not rag_retrieval:
            raise HTTPException(status_code=503, detail="RAG system not available")
        
        context = rag_retrieval.retrieve_context(
            query=request.query,
            knowledge_limit=request.knowledge_limit,
            conversation_limit=request.conversation_limit
        )
        
        return RAGQueryResponse(
            knowledge_docs=context.get("knowledge_docs", []),
            conversation_docs=context.get("conversation_docs", []),
            total_context_docs=context.get("total_context_docs", 0)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"RAG query error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/stats")
async def get_rag_stats():
    """Get RAG system statistics"""
    try:
        chroma_client = get_chroma_client()
        
        if not chroma_client:
            raise HTTPException(status_code=503, detail="Vector DB not available")
        
        stats = chroma_client.get_collection_stats()
        return {"stats": stats}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"RAG stats error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/reset-database", dependencies=[Depends(require_api_key)])
async def reset_rag_database():
    """
    Reset ChromaDB database (deletes all data and recreates collections)
    
    Security: This endpoint requires API key authentication via X-API-Key header.
    """
    try:
        chroma_client = get_chroma_client()
        persist_dir = "data/vector_db"
        
        # If chroma_client is None, we need to delete the directory directly
        if not chroma_client:
            logger.warning("ChromaClient not initialized, attempting to delete vector_db directory...")
            if os.path.exists(persist_dir):
                try:
                    shutil.rmtree(persist_dir)
                    logger.info(f"Deleted {persist_dir} directory")
                    os.makedirs(persist_dir, exist_ok=True)
                    logger.info(f"Recreated {persist_dir} directory")
                except Exception as dir_error:
                    logger.error(f"Failed to delete directory: {dir_error}")
                    raise HTTPException(
                        status_code=500, 
                        detail=f"Cannot delete vector_db directory: {dir_error}. You may need to restart backend service."
                    )
            else:
                logger.info(f"Directory {persist_dir} does not exist, creating it...")
                os.makedirs(persist_dir, exist_ok=True)
            
            return {
                "status": "success",
                "message": "Vector database directory deleted. Please restart the backend service to reinitialize."
            }
        
        # If chroma_client exists, try to reset via client
        try:
            # Delete existing collections
            try:
                chroma_client.client.delete_collection("stillme_knowledge")
            except Exception:
                pass
            
            try:
                chroma_client.client.delete_collection("stillme_conversations")
            except Exception:
                pass
            
            # Recreate collections
            chroma_client.knowledge_collection = chroma_client.client.create_collection(
                name="stillme_knowledge",
                metadata={"description": "Knowledge base for StillMe learning"}
            )
            chroma_client.conversation_collection = chroma_client.client.create_collection(
                name="stillme_conversations",
                metadata={"description": "Conversation history for context"}
            )
            
            logger.info("✅ ChromaDB database reset successfully via API")
            return {
                "status": "success",
                "message": "Database reset successfully. All collections recreated."
            }
        except Exception as client_error:
            # If client reset fails, try deleting directory
            logger.warning(f"Client reset failed: {client_error}, trying directory deletion...")
            if os.path.exists(persist_dir):
                try:
                    shutil.rmtree(persist_dir)
                    os.makedirs(persist_dir, exist_ok=True)
                    logger.info("Deleted and recreated vector_db directory")
                    return {
                        "status": "success",
                        "message": "Vector database directory deleted. Please restart the backend service to reinitialize."
                    }
                except Exception as dir_error:
                    logger.error(f"Failed to delete directory: {dir_error}")
                    raise HTTPException(
                        status_code=500,
                        detail=f"Cannot delete vector_db directory: {dir_error}. You may need to restart backend service."
                    )
            else:
                raise HTTPException(
                    status_code=500,
                    detail=f"Cannot reset database: {client_error}. Please check backend logs."
                )
                
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"RAG reset database error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

