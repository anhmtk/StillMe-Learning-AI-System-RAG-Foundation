"""
Codebase Q&A Router for StillMe Codebase Assistant

Provides API endpoints for querying the StillMe codebase using RAG.
Phase 1.3: Code Q&A API Endpoint
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/codebase", tags=["codebase"])


class CodebaseQueryRequest(BaseModel):
    """Request model for codebase queries"""
    question: str = Field(..., description="Question about the codebase")
    n_results: int = Field(default=5, ge=1, le=20, description="Number of code chunks to retrieve")
    include_code: bool = Field(default=True, description="Include code snippets in response")


class CodeChunkResponse(BaseModel):
    """Response model for a code chunk"""
    file_path: str
    line_start: int
    line_end: int
    code_type: str  # "file", "class", "function"
    function_name: Optional[str] = None
    class_name: Optional[str] = None
    docstring: Optional[str] = None
    code_snippet: Optional[str] = None
    distance: Optional[float] = None  # Similarity distance


class CodebaseQueryResponse(BaseModel):
    """Response model for codebase queries"""
    question: str
    explanation: str
    code_chunks: List[CodeChunkResponse]
    citations: List[str]  # Formatted citations like "file.py:10-20"


def get_codebase_indexer():
    """Dependency: Get CodebaseIndexer instance"""
    try:
        from backend.services.codebase_indexer import get_codebase_indexer
        return get_codebase_indexer()
    except Exception as e:
        logger.error(f"Failed to get CodebaseIndexer: {e}")
        raise HTTPException(status_code=503, detail="Codebase indexer not available")


@router.post("/query", response_model=CodebaseQueryResponse)
async def query_codebase(
    request: CodebaseQueryRequest,
    indexer = Depends(get_codebase_indexer)
):
    """
    Query the StillMe codebase using RAG.
    
    Retrieves relevant code chunks and generates explanations using LLM.
    
    Example questions:
    - "How does the validation chain work?"
    - "What is the RAG retrieval process?"
    - "How does StillMe track task execution time?"
    """
    try:
        logger.info(f"📝 Codebase query: {request.question[:100]}...")
        
        # Retrieve relevant code chunks
        results = indexer.query_codebase(request.question, n_results=request.n_results)
        
        if not results:
            raise HTTPException(
                status_code=404,
                detail="No relevant code chunks found for this question"
            )
        
        logger.info(f"✅ Found {len(results)} relevant code chunks")
        
        # Format code chunks for response
        code_chunks = []
        citations = []
        
        for result in results:
            metadata = result.get("metadata", {})
            chunk_response = CodeChunkResponse(
                file_path=metadata.get("file_path", ""),
                line_start=metadata.get("line_start", 0),
                line_end=metadata.get("line_end", 0),
                code_type=metadata.get("code_type", "unknown"),
                function_name=metadata.get("function_name"),
                class_name=metadata.get("class_name"),
                docstring=metadata.get("docstring"),
                code_snippet=result.get("document", "") if request.include_code else None,
                distance=result.get("distance")
            )
            code_chunks.append(chunk_response)
            
            # Format citation
            file_name = metadata.get("file_path", "").split("/")[-1] if "/" in metadata.get("file_path", "") else metadata.get("file_path", "")
            citation = f"{file_name}:{metadata.get('line_start', '?')}-{metadata.get('line_end', '?')}"
            citations.append(citation)
        
        # Generate explanation using LLM
        explanation = await _generate_code_explanation(
            question=request.question,
            code_chunks=results
        )
        
        return CodebaseQueryResponse(
            question=request.question,
            explanation=explanation,
            code_chunks=code_chunks,
            citations=citations
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error querying codebase: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to query codebase: {str(e)}"
        )


async def _generate_code_explanation(
    question: str,
    code_chunks: List[Dict[str, Any]]
) -> str:
    """
    Generate explanation using LLM with code context.
    
    Args:
        question: User's question about the codebase
        code_chunks: Retrieved code chunks with metadata
        
    Returns:
        Explanation text with code citations
    """
    try:
        from backend.api.utils.chat_helpers import generate_ai_response
        import os
        
        # Build context from code chunks
        context_parts = []
        for i, chunk in enumerate(code_chunks, 1):
            metadata = chunk.get("metadata", {})
            file_path = metadata.get("file_path", "")
            line_range = f"{metadata.get('line_start', '?')}-{metadata.get('line_end', '?')}"
            code_content = chunk.get("document", "")
            
            context_part = f"""
--- Code Chunk {i} ---
File: {file_path}
Lines: {line_range}
Type: {metadata.get('code_type', 'unknown')}
"""
            if metadata.get("class_name"):
                context_part += f"Class: {metadata.get('class_name')}\n"
            if metadata.get("function_name"):
                context_part += f"Function: {metadata.get('function_name')}\n"
            if metadata.get("docstring"):
                context_part += f"Docstring: {metadata.get('docstring')}\n"
            
            context_part += f"\nCode:\n{code_content}\n"
            context_parts.append(context_part)
        
        context = "\n".join(context_parts)
        
        # Build prompt
        prompt = f"""You are StillMe's Codebase Assistant. Answer the user's question about the StillMe codebase based on the provided code chunks.

IMPORTANT SAFETY RULES:
- ONLY explain the code, do NOT suggest modifications
- ONLY describe what the code does, do NOT propose changes
- Cite specific file:line references when mentioning code
- Be accurate and technical

User Question: {question}

Code Context:
{context}

Instructions:
1. Answer the question based on the provided code chunks
2. Cite specific files and line numbers (e.g., "In file.py:10-20, the function does...")
3. Explain the code's purpose and how it works
4. If multiple chunks are relevant, explain how they relate
5. Be concise but thorough
6. Use technical language appropriate for developers

Your explanation:"""
        
        # Call LLM using server keys (internal use for codebase assistant)
        # Use DeepSeek as default provider if available
        deepseek_key = os.getenv("DEEPSEEK_API_KEY")
        if deepseek_key:
            llm_provider = "deepseek"
            llm_api_key = deepseek_key
        else:
            # Fallback to OpenRouter if DeepSeek not available
            openrouter_key = os.getenv("OPENROUTER_API_KEY")
            if openrouter_key:
                llm_provider = "openrouter"
                llm_api_key = openrouter_key
            else:
                # No LLM available, return fallback
                raise ValueError("No LLM API key available (DEEPSEEK_API_KEY or OPENROUTER_API_KEY)")
        
        response = await generate_ai_response(
            prompt=prompt,
            detected_lang="en",  # Code explanations in English
            llm_provider=llm_provider,
            llm_api_key=llm_api_key,
            use_server_keys=True,  # Internal use
            question=question,
            task_type="chat"
        )
        
        return response.strip()
        
    except Exception as e:
        logger.error(f"❌ Error generating explanation: {e}", exc_info=True)
        # Fallback: Return basic explanation
        return f"Found {len(code_chunks)} relevant code chunks. Please check the code_chunks field for details."


@router.get("/stats")
async def get_codebase_stats(
    indexer = Depends(get_codebase_indexer)
):
    """
    Get statistics about the indexed codebase.
    
    Returns:
        Dictionary with collection statistics
    """
    try:
        count = indexer.codebase_collection.count()
        
        return {
            "total_chunks": count,
            "status": "ready" if count > 0 else "empty"
        }
    except Exception as e:
        logger.error(f"❌ Error getting stats: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get codebase stats: {str(e)}"
        )

