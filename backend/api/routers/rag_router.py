"""
RAG Router for StillMe API
Handles all RAG-related endpoints
"""

from fastapi import APIRouter, Request, HTTPException, Depends
from backend.api.models import LearningRequest, RAGQueryRequest, RAGQueryResponse
from backend.api.rate_limiter import limiter, get_rate_limit_key_func
from backend.api.auth import require_api_key
from backend.validators.ethics_adapter import EthicsAdapter
from typing import Optional
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
async def add_knowledge_rag(
    request: Request, 
    learning_request: LearningRequest,
    api_key: Optional[str] = Depends(require_api_key)
):
    """
    Add knowledge to RAG vector database
    
    Security: Requires API key authentication (X-API-Key header) to prevent unauthorized content injection.
    For self-hosted deployments, users can set STILLME_API_KEY in environment.
    For shared deployments, only approved users should have API keys.
    
    Content is validated for:
    - Ethics compliance (EthicsAdapter)
    - Quality (ContentCurator pre-filter)
    - Format (LearningRequest validation)
    """
    try:
        rag_retrieval = get_rag_retrieval()
        content_curator = get_content_curator()
        
        if not rag_retrieval:
            raise HTTPException(status_code=503, detail="RAG system not available")
        
        # Ethics validation - CRITICAL for preventing malicious content
        try:
            from backend.validators.ethics_adapter import EthicsAdapter
            from backend.services.ethics_guard import check_content_ethics
            
            ethics_adapter = EthicsAdapter(guard_callable=check_content_ethics)
            from backend.validators.base import ValidationResult
            ethics_result = ethics_adapter.run(learning_request.content, [])
            
            if not ethics_result.passed:
                logger.warning(f"Ethics validation failed for content from source: {learning_request.source}")
                raise HTTPException(
                    status_code=400,
                    detail=f"Content failed ethics validation: {', '.join(ethics_result.reasons)}"
                )
        except HTTPException:
            raise
        except Exception as ethics_error:
            # If ethics check fails due to error, log but don't block (fail-open for now)
            # In production, you may want to fail-closed
            logger.error(f"Ethics validation error: {ethics_error}")
            # For now, we'll allow content through if ethics check errors
            # TODO: Consider making this fail-closed in production
        
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
        enhanced_metadata["added_by"] = "api"  # Track that this was added via API
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
            logger.info(f"Knowledge added successfully from source: {learning_request.source}")
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

@router.get("/list-documents", dependencies=[Depends(require_api_key)])
async def list_documents(
    collection: str = "all",
    limit: int = 100,
    offset: int = 0
):
    """
    List all documents in ChromaDB collections (requires API key)
    
    Args:
        collection: "knowledge", "conversation", or "all" (default: "all")
        limit: Maximum number of documents to return (default: 100, max: 1000)
        offset: Number of documents to skip (default: 0)
    
    Returns:
        List of documents with content and metadata
    """
    try:
        chroma_client = get_chroma_client()
        
        if not chroma_client:
            raise HTTPException(status_code=503, detail="Vector DB not available")
        
        limit = min(limit, 1000)  # Cap at 1000
        
        results = {
            "knowledge_documents": [],
            "conversation_documents": [],
            "total_knowledge": 0,
            "total_conversation": 0
        }
        
        # Get knowledge documents
        if collection in ["all", "knowledge"]:
            try:
                # ChromaDB doesn't have direct "get all" - we use query with empty embedding or peek
                # For now, we'll use a workaround: query with a dummy embedding to get all
                # Actually, ChromaDB has .get() method to retrieve all documents
                knowledge_data = chroma_client.knowledge_collection.get(
                    limit=limit,
                    offset=offset
                )
                
                if knowledge_data and "documents" in knowledge_data:
                    for i, doc in enumerate(knowledge_data.get("documents", [])):
                        doc_id = knowledge_data.get("ids", [])[i] if i < len(knowledge_data.get("ids", [])) else f"doc_{i}"
                        metadata = knowledge_data.get("metadatas", [{}])[i] if i < len(knowledge_data.get("metadatas", [])) else {}
                        
                        results["knowledge_documents"].append({
                            "id": doc_id,
                            "content": doc[:500] + "..." if len(doc) > 500 else doc,  # Truncate for display
                            "content_length": len(doc),
                            "metadata": {k: v for k, v in metadata.items() if v is not None}
                        })
                
                results["total_knowledge"] = chroma_client.knowledge_collection.count()
            except Exception as e:
                logger.error(f"Error getting knowledge documents: {e}")
                results["knowledge_documents"] = []
        
        # Get conversation documents
        if collection in ["all", "conversation"]:
            try:
                conversation_data = chroma_client.conversation_collection.get(
                    limit=limit,
                    offset=offset
                )
                
                if conversation_data and "documents" in conversation_data:
                    for i, doc in enumerate(conversation_data.get("documents", [])):
                        doc_id = conversation_data.get("ids", [])[i] if i < len(conversation_data.get("ids", [])) else f"conv_{i}"
                        metadata = conversation_data.get("metadatas", [{}])[i] if i < len(conversation_data.get("metadatas", [])) else {}
                        
                        results["conversation_documents"].append({
                            "id": doc_id,
                            "content": doc[:500] + "..." if len(doc) > 500 else doc,  # Truncate for display
                            "content_length": len(doc),
                            "metadata": {k: v for k, v in metadata.items() if v is not None}
                        })
                
                results["total_conversation"] = chroma_client.conversation_collection.count()
            except Exception as e:
                logger.error(f"Error getting conversation documents: {e}")
                results["conversation_documents"] = []
        
        return results
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"List documents error: {e}")
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

