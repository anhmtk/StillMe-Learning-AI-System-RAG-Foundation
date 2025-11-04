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
    chroma_client = ChromaClient()
    logger.info("✓ ChromaDB client initialized")
    
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
except Exception as e:
    _initialization_error = str(e)
    logger.error(f"❌ Failed to initialize RAG components: {e}", exc_info=True)
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
        if context and context["total_context_docs"] > 0:
            # Use context to enhance response
            context_text = rag_retrieval.build_prompt_context(context)
            enhanced_prompt = f"""
            Context: {context_text}
            
            User Question: {request.message}
            
            Please provide a helpful response based on the context above.
            """
            response = await generate_ai_response(enhanced_prompt)
        else:
            # Fallback to regular AI response
            response = await generate_ai_response(request.message)
        
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
        
    except Exception as e:
        logger.error(f"Chat error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

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
        if not learning_scheduler:
            # Provide more detailed error message
            error_msg = "Scheduler not initialized"
            if _initialization_error:
                error_msg = f"Scheduler not initialized: {_initialization_error}"
            return {
                "status": "not_available",
                "message": error_msg,
                "initialization_error": _initialization_error if _initialization_error else None
            }
        
        return {
            "status": "ok",
            **learning_scheduler.get_status()
        }
    except Exception as e:
        logger.error(f"Scheduler status error: {e}")
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
            # Get entries from last fetch and add to RAG
            entries = learning_scheduler.rss_fetcher.fetch_feeds(max_items_per_feed=5)
            
            # Prioritize content if curator available
            if content_curator and self_diagnosis:
                # Get knowledge gaps to prioritize
                recent_gaps = []  # Could be from query history
                prioritized = content_curator.prioritize_learning_content(
                    entries,
                    knowledge_gaps=recent_gaps
                )
                entries = prioritized[:5]  # Take top 5
            
            added_count = 0
            for entry in entries:
                content = f"{entry.get('title', '')}\n{entry.get('summary', '')}"
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
            
            result["entries_added_to_rag"] = added_count
        
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
    # Use the RAG-enhanced chat endpoint as default
    return await chat_with_rag(request)

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
