"""
StillMe Backend API
FastAPI backend with RAG (Retrieval-Augmented Generation) capabilities
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
import os
import logging
import asyncio
import httpx
from datetime import datetime

# Import RAG components
from backend.vector_db import ChromaClient, EmbeddingService, RAGRetrieval
from backend.learning import KnowledgeRetention, AccuracyScorer
from backend.services.rss_fetcher import RSSFetcher
from backend.services.learning_scheduler import LearningScheduler
from backend.services.self_diagnosis import SelfDiagnosisAgent
from backend.services.content_curator import ContentCurator

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="StillMe API",
    description="Self-Evolving AI System with RAG capabilities",
    version="0.4.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize RAG components
# Track initialization errors for better diagnostics
_initialization_error = None
chroma_client = None
embedding_service = None
rag_retrieval = None
knowledge_retention = None
accuracy_scorer = None
rss_fetcher = None
learning_scheduler = None
self_diagnosis = None
content_curator = None

try:
    logger.info("Initializing RAG components...")
    # Try with reset_on_error=False first (preserve data)
    # If schema error, will try with reset_on_error=True (which deletes directory first)
    chroma_client_ref = None
    try:
        chroma_client = ChromaClient(reset_on_error=False)
        logger.info("✓ ChromaDB client initialized")
    except (RuntimeError, Exception) as e:
        error_str = str(e).lower()
        if "schema mismatch" in error_str or "no such column" in error_str or "topic" in error_str:
            logger.warning("⚠️ Schema mismatch detected!")
            logger.warning("Attempting to reset database by deleting directory...")
            
            # Store reference to old client if exists (for cleanup)
            if chroma_client_ref:
                try:
                    # Try to close/disconnect old client
                    if hasattr(chroma_client_ref, 'client'):
                        logger.info("Closing old ChromaDB client connection...")
                        # ChromaDB PersistentClient doesn't have explicit close, but we can try to delete reference
                        del chroma_client_ref
                except:
                    pass
            
            # Force garbage collection to ensure old client is freed
            import gc
            gc.collect()
            logger.info("Garbage collected old client references")
            
            # Try resetting database - this will delete the directory before creating client
            chroma_client = ChromaClient(reset_on_error=True)
            logger.info("✓ ChromaDB client initialized (after directory reset)")
            logger.warning("⚠️ IMPORTANT: If errors persist, please RESTART the backend service on Railway to clear process cache.")
        else:
            raise
    
    embedding_service = EmbeddingService()
    logger.info("✓ Embedding service initialized")
    
    rag_retrieval = RAGRetrieval(chroma_client, embedding_service)
    logger.info("✓ RAG retrieval initialized")
    
    knowledge_retention = KnowledgeRetention()
    logger.info("✓ Knowledge retention initialized")
    
    accuracy_scorer = AccuracyScorer()
    logger.info("✓ Accuracy scorer initialized")
    
    rss_fetcher = RSSFetcher()
    logger.info("✓ RSS fetcher initialized")
    
    learning_scheduler = LearningScheduler(
        rss_fetcher=rss_fetcher,
        interval_hours=4,
        auto_add_to_rag=True
    )
    logger.info("✓ Learning scheduler initialized")
    
    self_diagnosis = SelfDiagnosisAgent(rag_retrieval=rag_retrieval)
    logger.info("✓ Self-diagnosis agent initialized")
    
    content_curator = ContentCurator()
    logger.info("✓ Content curator initialized")
    
    logger.info("✅ All RAG components initialized successfully")
    logger.info("🎉 StillMe backend is ready!")
except Exception as e:
    _initialization_error = str(e)
    logger.error(f"❌ Failed to initialize RAG components: {e}", exc_info=True)
    if "schema mismatch" in str(e).lower() or "no such column" in str(e).lower() or "topic" in str(e).lower():
        logger.error("⚠️ CRITICAL: Schema mismatch persists after reset attempt.")
        logger.error("⚠️ ACTION REQUIRED: Please RESTART the backend service on Railway to clear process cache.")
        logger.error("⚠️ The file deletion worked, but the process may be caching the old schema.")
    # Fallback to None for graceful degradation
    # Components already set to None above

# Pydantic models
class ChatRequest(BaseModel):
    message: str
    user_id: Optional[str] = "default"
    use_rag: bool = True
    context_limit: int = 3

class ChatResponse(BaseModel):
    response: str
    context_used: Optional[Dict[str, Any]] = None
    accuracy_score: Optional[float] = None
    learning_session_id: Optional[int] = None

class LearningRequest(BaseModel):
    content: str
    source: str
    content_type: str = "knowledge"
    metadata: Optional[Dict[str, Any]] = None

class LearningResponse(BaseModel):
    success: bool
    knowledge_id: Optional[int] = None
    message: str

class RAGQueryRequest(BaseModel):
    query: str
    knowledge_limit: int = 3
    conversation_limit: int = 2

# API Routes
@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "StillMe API v0.4.0",
        "status": "running",
        "rag_enabled": rag_retrieval is not None,
        "timestamp": datetime.now().isoformat()
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    rag_status = "enabled" if rag_retrieval else "disabled"
    return {
        "status": "healthy",
        "rag_status": rag_status,
        "timestamp": datetime.now().isoformat()
    }

@app.post("/api/chat/rag", response_model=ChatResponse)
async def chat_with_rag(request: ChatRequest):
    """Chat with RAG-enhanced responses"""
    try:
        # Get RAG context if enabled
        context = None
        if rag_retrieval and request.use_rag:
            context = rag_retrieval.retrieve_context(
                query=request.message,
                knowledge_limit=request.context_limit,
                conversation_limit=2
            )
        
        # Generate response using AI (simplified for demo)
        enable_validators = os.getenv("ENABLE_VALIDATORS", "false").lower() == "true"
        enable_tone_align = os.getenv("ENABLE_TONE_ALIGN", "true").lower() == "true"
        
        if context and context["total_context_docs"] > 0:
            # Use context to enhance response
            context_text = rag_retrieval.build_prompt_context(context)
            
            # Build base prompt with citation instructions
            citation_instruction = ""
            if enable_validators:
                # Count knowledge docs for citation numbering
                num_knowledge = len(context.get("knowledge_docs", []))
                if num_knowledge > 0:
                    citation_instruction = f"\n\nIMPORTANT: When referencing information from the context above, include citations in the format [1], [2], etc. where the number corresponds to the context item number. For example, if you reference the first context item, use [1]."
            
            base_prompt = f"""
            Context: {context_text}
            {citation_instruction}
            
            User Question: {request.message}
            
            Please provide a helpful response based on the context above.
            """
            
            # Inject StillMe identity if validators enabled
            if enable_validators:
                from backend.identity.injector import inject_identity
                enhanced_prompt = inject_identity(base_prompt)
            else:
                enhanced_prompt = base_prompt
            
            raw_response = await generate_ai_response(enhanced_prompt)
            
            # Validate response if enabled
            if enable_validators:
                try:
                    from backend.validators.chain import ValidatorChain
                    from backend.validators.citation import CitationRequired
                    from backend.validators.evidence_overlap import EvidenceOverlap
                    from backend.validators.numeric import NumericUnitsBasic
                    from backend.validators.ethics_adapter import EthicsAdapter
                    
                    # Build context docs list for validation
                    ctx_docs = [
                        doc["content"] for doc in context["knowledge_docs"]
                    ] + [
                        doc["content"] for doc in context["conversation_docs"]
                    ]
                    
                    # Create validator chain
                    chain = ValidatorChain([
                        CitationRequired(),
                        EvidenceOverlap(threshold=0.08),
                        NumericUnitsBasic(),
                        EthicsAdapter(guard_callable=None)  # TODO: wire existing ethics guard if available
                    ])
                    
                    # Run validation
                    validation_result = chain.run(raw_response, ctx_docs)
                    
                    # Record metrics
                    try:
                        from backend.validators.metrics import get_metrics
                        metrics = get_metrics()
                        # Extract overlap score from reasons if available
                        overlap_score = 0.0
                        for reason in validation_result.reasons:
                            if reason.startswith("low_overlap:"):
                                try:
                                    overlap_score = float(reason.split(":")[1])
                                except (ValueError, IndexError):
                                    pass
                        metrics.record_validation(
                            passed=validation_result.passed,
                            reasons=validation_result.reasons,
                            overlap_score=overlap_score
                        )
                    except Exception as metrics_error:
                        logger.warning(f"Failed to record metrics: {metrics_error}")
                    
                    if not validation_result.passed:
                        # Use patched answer if available, otherwise return 422
                        if validation_result.patched_answer:
                            response = validation_result.patched_answer
                            logger.info(f"Validation failed but using patched answer. Reasons: {validation_result.reasons}")
                        else:
                            logger.warning(f"Validation failed: {validation_result.reasons}")
                            raise HTTPException(
                                status_code=422,
                                detail={
                                    "error": "validation_failed",
                                    "reasons": validation_result.reasons,
                                    "original_response_preview": raw_response[:200] if raw_response else ""
                                }
                            )
                    else:
                        response = validation_result.patched_answer or raw_response
                        logger.debug(f"Validation passed. Reasons: {validation_result.reasons}")
                except HTTPException:
                    raise
                except Exception as validation_error:
                    logger.error(f"Validation error: {validation_error}, falling back to raw response")
                    response = raw_response
            else:
                response = raw_response
        else:
            # Fallback to regular AI response
            base_prompt = request.message
            if enable_validators:
                from backend.identity.injector import inject_identity
                enhanced_prompt = inject_identity(base_prompt)
            else:
                enhanced_prompt = base_prompt
            
            response = await generate_ai_response(enhanced_prompt)
        
        # Score the response
        accuracy_score = None
        if accuracy_scorer:
            accuracy_score = accuracy_scorer.score_response(
                question=request.message,
                actual_answer=response,
                scoring_method="semantic_similarity"
            )
        
        # Record learning session
        learning_session_id = None
        if knowledge_retention:
            learning_session_id = knowledge_retention.record_learning_session(
                session_type="chat",
                content_learned=f"Q: {request.message}\nA: {response}",
                accuracy_score=accuracy_score or 0.5,
                metadata={"user_id": request.user_id}
            )
        
        # Align tone if enabled
        if enable_tone_align:
            try:
                from backend.tone.aligner import align_tone
                response = align_tone(response)
            except Exception as tone_error:
                logger.error(f"Tone alignment error: {tone_error}, using original response")
                # Continue with original response on error
        
        # Store conversation in vector DB
        if rag_retrieval:
            rag_retrieval.add_learning_content(
                content=f"Q: {request.message}\nA: {response}",
                source="user_chat",
                content_type="conversation",
                metadata={
                    "user_id": request.user_id,
                    "timestamp": datetime.now().isoformat(),
                    "accuracy_score": accuracy_score
                }
            )
        
        return ChatResponse(
            response=response,
            context_used=context,
            accuracy_score=accuracy_score,
            learning_session_id=learning_session_id
        )
        
    except HTTPException:
        # Re-raise HTTP exceptions (they have proper status codes)
        raise
    except Exception as e:
        # Log detailed error with context
        logger.error(f"Chat error: {e}", exc_info=True)
        logger.error(f"Request details: message={request.message[:100]}, user_id={request.user_id}, use_rag={request.use_rag}")
        
        # Check if it's a specific error we can handle
        error_str = str(e).lower()
        if "rag" in error_str and "not available" in error_str:
            raise HTTPException(status_code=503, detail="RAG system is not available. Please check backend initialization.")
        elif "embedding" in error_str or "model" in error_str:
            raise HTTPException(status_code=503, detail="Embedding service is not available. Please check backend logs.")
        else:
            raise HTTPException(
                status_code=500,
                detail=f"Chat error: {str(e)}. Please check backend logs for details."
            )

@app.post("/api/learning/add", response_model=LearningResponse)
async def add_learning_content(request: LearningRequest):
    """Add learning content to the system"""
    try:
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
            success = rag_retrieval.add_learning_content(
                content=request.content,
                source=request.source,
                content_type=request.content_type,
                metadata=request.metadata
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

@app.get("/api/learning/metrics")
async def get_learning_metrics():
    """Get learning and accuracy metrics"""
    try:
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

@app.get("/api/learning/retained")
async def get_retained_knowledge(limit: int = 10):
    """Get retained knowledge items"""
    try:
        if not knowledge_retention:
            raise HTTPException(status_code=503, detail="Knowledge retention not available")
        
        knowledge = knowledge_retention.get_retained_knowledge(limit=limit)
        return {"knowledge_items": knowledge}
        
    except Exception as e:
        logger.error(f"Retained knowledge error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# RAG-specific endpoints
@app.post("/api/rag/add_knowledge")
async def add_knowledge_rag(request: LearningRequest):
    """Add knowledge to RAG vector database"""
    try:
        if not rag_retrieval:
            raise HTTPException(status_code=503, detail="RAG system not available")
        
        success = rag_retrieval.add_learning_content(
            content=request.content,
            source=request.source,
            content_type=request.content_type,
            metadata=request.metadata
        )
        
        if success:
            return {"status": "Knowledge added successfully", "content_type": request.content_type}
        else:
            raise HTTPException(status_code=500, detail="Failed to add knowledge to vector DB")
            
    except Exception as e:
        logger.error(f"RAG add knowledge error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/rag/query")
async def query_rag(request: RAGQueryRequest):
    """Query RAG system for relevant context"""
    try:
        if not rag_retrieval:
            raise HTTPException(status_code=503, detail="RAG system not available")
        
        context = rag_retrieval.retrieve_context(
            query=request.query,
            knowledge_limit=request.knowledge_limit,
            conversation_limit=request.conversation_limit
        )
        
        context_text = rag_retrieval.build_prompt_context(context)
        
        return {
            "status": "Context retrieved",
            "context": context_text,
            "raw_results": context,
            "total_context_docs": context.get("total_context_docs", 0)
        }
        
    except Exception as e:
        logger.error(f"RAG query error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/rag/stats")
async def get_rag_stats():
    """Get RAG system statistics"""
    try:
        if not chroma_client:
            raise HTTPException(status_code=503, detail="Vector DB not available")
        
        stats = chroma_client.get_collection_stats()
        return {"stats": stats}
        
    except Exception as e:
        logger.error(f"RAG stats error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/rag/reset-database")
async def reset_rag_database():
    """Reset ChromaDB database (deletes all data and recreates collections)"""
    import shutil
    import os
    
    try:
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
                    raise HTTPException(status_code=500, detail=f"Failed to reset: {dir_error}")
            else:
                raise
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Database reset error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/status")
async def get_status():
    """Get system status"""
    try:
        status = {
            "stage": "Infant",
            "sessions_completed": 0,
            "milestone_sessions": 100,
            "system_age_days": 0
        }
        
        # Try to get from database if available
        # For now, return default status
        
        return status
        
    except Exception as e:
        logger.error(f"Status error: {e}")
        return {
            "stage": "Unknown",
            "sessions_completed": 0,
            "milestone_sessions": 100,
            "system_age_days": 0
        }

@app.get("/api/validators/metrics")
async def get_validation_metrics():
    """Get validation metrics"""
    try:
        from backend.validators.metrics import get_metrics
        metrics = get_metrics()
        return {"metrics": metrics.get_metrics()}
    except Exception as e:
        logger.error(f"Validation metrics error: {e}")
        return {
            "metrics": {
                "total_validations": 0,
                "pass_rate": 0.0,
                "passed_count": 0,
                "failed_count": 0,
                "avg_overlap_score": 0.0,
                "reasons_histogram": {},
                "recent_logs": []
            }
        }

@app.get("/api/learning/accuracy_metrics")
async def get_accuracy_metrics():
    """Get accuracy metrics"""
    try:
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

# RSS Learning Pipeline endpoints
@app.post("/api/learning/rss/fetch")
async def fetch_rss_content(max_items: int = 5, auto_add: bool = False):
    """Fetch content from RSS feeds
    
    Args:
        max_items: Maximum items per feed
        auto_add: If True, automatically add to RAG vector DB
    """
    try:
        if not rss_fetcher:
            raise HTTPException(status_code=503, detail="RSS fetcher not available")
        
        entries = rss_fetcher.fetch_feeds(max_items_per_feed=max_items)
        
        # Auto-add to RAG if requested
        added_count = 0
        if auto_add and rag_retrieval:
            for entry in entries:
                content = f"{entry['title']}\n{entry['summary']}"
                success = rag_retrieval.add_learning_content(
                    content=content,
                    source=entry['source'],
                    content_type="knowledge",
                    metadata={
                        "link": entry['link'],
                        "published": entry['published'],
                        "type": "rss_feed"
                    }
                )
                if success:
                    added_count += 1
        
        return {
            "status": "success",
            "entries_fetched": len(entries),
            "entries_added": added_count if auto_add else 0,
            "entries": entries[:10]  # Return first 10 for preview
        }
        
    except Exception as e:
        logger.error(f"RSS fetch error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/learning/rss/stats")
async def get_rss_stats():
    """Get RSS pipeline statistics"""
    try:
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

# Automated Scheduler endpoints
@app.post("/api/learning/scheduler/start")
async def start_scheduler():
    """Start automated learning scheduler"""
    try:
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
    except Exception as e:
        logger.error(f"Start scheduler error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/learning/scheduler/stop")
async def stop_scheduler():
    """Stop automated learning scheduler"""
    try:
        if not learning_scheduler:
            raise HTTPException(status_code=503, detail="Scheduler not available")
        
        if not learning_scheduler.is_running:
            return {"status": "not_running", "message": "Scheduler is not running"}
        
        await learning_scheduler.stop()
        return {
            "status": "stopped",
            "message": "Scheduler stopped successfully"
        }
    except Exception as e:
        logger.error(f"Stop scheduler error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/learning/scheduler/status")
async def get_scheduler_status():
    """Get scheduler status"""
    try:
        # Debug logging
        logger.info(f"get_scheduler_status called. learning_scheduler is None: {learning_scheduler is None}")
        logger.info(f"_initialization_error: {_initialization_error}")
        
        if not learning_scheduler:
            # Provide more detailed error message
            error_msg = "Scheduler not initialized"
            if _initialization_error:
                error_msg = f"Scheduler not initialized: {_initialization_error}"
            logger.warning(f"Returning not_available status: {error_msg}")
            return {
                "status": "not_available",
                "message": error_msg,
                "initialization_error": _initialization_error if _initialization_error else None
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
        return {"status": "error", "message": str(e)}

@app.post("/api/learning/scheduler/run-now")
async def run_scheduler_now():
    """Manually trigger a learning cycle immediately"""
    try:
        if not learning_scheduler:
            raise HTTPException(status_code=503, detail="Scheduler not available")
        
        result = await learning_scheduler.run_learning_cycle()
        
        # If auto_add_to_rag is enabled, add to RAG
        if learning_scheduler.auto_add_to_rag and rag_retrieval:
            # Use entries from the learning cycle result (already fetched)
            # Don't fetch again - use the entries that were already fetched in run_learning_cycle
            entries_to_add = []
            
            # Try to get entries from the RSS fetcher's last fetch
            # If that's not available, fetch again (but this should be rare)
            try:
                # Get entries that were fetched in this cycle
                # The run_learning_cycle already fetched entries, but we need to access them
                # For now, we'll fetch again but this should be optimized later
                all_entries = learning_scheduler.rss_fetcher.fetch_feeds(max_items_per_feed=5)
                logger.info(f"Fetched {len(all_entries)} entries for RAG addition")
                
                # Prioritize content if curator available
                if content_curator and self_diagnosis:
                    # Get knowledge gaps to prioritize
                    recent_gaps = []  # Could be from query history
                    prioritized = content_curator.prioritize_learning_content(
                        all_entries,
                        knowledge_gaps=recent_gaps
                    )
                    # Take top entries (up to 5, but can be fewer if prioritized list is shorter)
                    entries_to_add = prioritized[:min(5, len(prioritized))]
                    logger.info(f"Content curator prioritized {len(entries_to_add)} entries from {len(all_entries)} total")
                else:
                    # If no curator, add all entries (or limit to reasonable number)
                    entries_to_add = all_entries[:min(10, len(all_entries))]
                    logger.info(f"No content curator, adding {len(entries_to_add)} entries directly")
                
            except Exception as e:
                logger.error(f"Error preparing entries for RAG: {e}")
                entries_to_add = []
            
            added_count = 0
            for entry in entries_to_add:
                try:
                    content = f"{entry.get('title', '')}\n{entry.get('summary', '')}"
                    if not content.strip():
                        logger.warning(f"Skipping empty entry: {entry.get('title', 'No title')}")
                        continue
                    
                    success = rag_retrieval.add_learning_content(
                        content=content,
                        source=entry.get('source', 'rss'),
                        content_type="knowledge",
                        metadata={
                            "link": entry.get('link', ''),
                            "published": entry.get('published', ''),
                            "type": "rss_feed",
                            "scheduler_cycle": result.get("cycle_number", 0),
                            "priority_score": entry.get("priority_score", 0.5)
                        }
                    )
                    if success:
                        added_count += 1
                        logger.info(f"Added entry to RAG: {entry.get('title', 'No title')[:50]}")
                    else:
                        logger.warning(f"Failed to add entry to RAG: {entry.get('title', 'No title')[:50]}")
                except Exception as e:
                    logger.error(f"Error adding entry to RAG: {e}")
                    continue
            
            result["entries_added_to_rag"] = added_count
            logger.info(f"Learning cycle: Fetched {result.get('entries_fetched', 0)} entries, added {added_count} to RAG")
        
        return result
        
    except Exception as e:
        logger.error(f"Run scheduler now error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Self-Diagnosis & Content Curation endpoints
@app.post("/api/learning/self-diagnosis/check-gap")
async def check_knowledge_gap(query: str, threshold: float = 0.5):
    """Check if there's a knowledge gap for a query"""
    try:
        if not self_diagnosis:
            raise HTTPException(status_code=503, detail="Self-diagnosis not available")
        
        result = self_diagnosis.identify_knowledge_gaps(query, threshold)
        return result
    except Exception as e:
        logger.error(f"Knowledge gap check error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/learning/self-diagnosis/analyze-coverage")
async def analyze_coverage(topics: List[str]):
    """Analyze knowledge coverage across multiple topics"""
    try:
        if not self_diagnosis:
            raise HTTPException(status_code=503, detail="Self-diagnosis not available")
        
        result = self_diagnosis.analyze_knowledge_coverage(topics)
        return result
    except Exception as e:
        logger.error(f"Coverage analysis error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/learning/self-diagnosis/suggest-focus")
async def suggest_learning_focus(recent_queries: Optional[List[str]] = None, limit: int = 5):
    """Suggest learning focus based on knowledge gaps"""
    try:
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

@app.post("/api/learning/curator/prioritize")
async def prioritize_content(content_list: List[Dict[str, Any]]):
    """Prioritize learning content"""
    try:
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
    except Exception as e:
        logger.error(f"Content prioritization error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/learning/curator/stats")
async def get_curation_stats():
    """Get content curation statistics"""
    try:
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

@app.post("/api/learning/curator/update-source-quality")
async def update_source_quality(source: str, quality_score: float):
    """Update quality score for a source"""
    try:
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
    except Exception as e:
        logger.error(f"Update source quality error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Smart router endpoint - automatically selects best model
@app.post("/api/chat/smart_router", response_model=ChatResponse)
async def chat_smart_router(request: ChatRequest):
    """
    Smart router that automatically selects the best chat endpoint.
    This is the main endpoint used by the dashboard.
    """
    try:
        # Use the RAG-enhanced chat endpoint as default
        return await chat_with_rag(request)
    except HTTPException:
        # Re-raise HTTP exceptions (they have proper status codes)
        raise
    except Exception as e:
        # Log detailed error for debugging
        logger.error(f"Smart router error: {e}", exc_info=True)
        # Return a more helpful error message
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}. Please check backend logs for details."
        )

# Legacy endpoints for backward compatibility
@app.post("/api/chat/openai")
async def chat_openai(request: ChatRequest):
    """Legacy OpenAI chat endpoint"""
    return await chat_with_rag(request)

@app.post("/api/chat/deepseek")
async def chat_deepseek(request: ChatRequest):
    """Legacy DeepSeek chat endpoint"""
    return await chat_with_rag(request)

# Helper functions
async def generate_ai_response(prompt: str) -> str:
    """Generate AI response (simplified for demo)"""
    try:
        # Check for API keys
        openai_key = os.getenv("OPENAI_API_KEY")
        deepseek_key = os.getenv("DEEPSEEK_API_KEY")
        
        if deepseek_key:
            return await call_deepseek_api(prompt, deepseek_key)
        elif openai_key:
            return await call_openai_api(prompt, openai_key)
        else:
            return "I'm StillMe, but I need API keys to provide real responses. Please configure OPENAI_API_KEY or DEEPSEEK_API_KEY in your environment."
            
    except Exception as e:
        logger.error(f"AI response error: {e}")
        return f"I encountered an error: {str(e)}"

async def call_deepseek_api(prompt: str, api_key: str) -> str:
    """Call DeepSeek API"""
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                "https://api.deepseek.com/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "deepseek-chat",
                    "messages": [
                        {
                            "role": "system",
                            "content": "You are StillMe, a self-evolving AI system. Provide helpful, accurate responses in Vietnamese when appropriate."
                        },
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    "max_tokens": 2000,
                    "temperature": 0.7
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                if "choices" in data and len(data["choices"]) > 0:
                    return data["choices"][0]["message"]["content"]
                else:
                    return "DeepSeek API returned unexpected response format"
            else:
                return f"DeepSeek API error: {response.status_code}"
                
    except Exception as e:
        logger.error(f"DeepSeek API error: {e}")
        return f"DeepSeek API error: {str(e)}"

async def call_openai_api(prompt: str, api_key: str) -> str:
    """Call OpenAI API"""
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                "https://api.openai.com/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "gpt-3.5-turbo",
                    "messages": [
                        {
                            "role": "system",
                            "content": "You are StillMe, a self-evolving AI system. Provide helpful, accurate responses in Vietnamese when appropriate."
                        },
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    "max_tokens": 2000,
                    "temperature": 0.7
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                if "choices" in data and len(data["choices"]) > 0:
                    return data["choices"][0]["message"]["content"]
                else:
                    return "OpenAI API returned unexpected response format"
            else:
                return f"OpenAI API error: {response.status_code}"
                
    except Exception as e:
        logger.error(f"OpenAI API error: {e}")
        return f"OpenAI API error: {str(e)}"

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
