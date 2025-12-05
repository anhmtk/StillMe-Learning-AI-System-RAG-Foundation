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
        from backend.api.utils.chat_helpers import generate_ai_response, detect_language
        from backend.identity.prompt_builder import build_code_explanation_prompt
        import os
        
        # Detect language from question
        detected_lang = detect_language(question)
        
        # Build prompt using prompt_builder (Phase 1.4: Code Explanation Prompt Engineering)
        prompt = build_code_explanation_prompt(
            question=question,
            code_chunks=code_chunks,
            detected_lang=detected_lang
        )
        
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


@router.post("/generate-tests")
async def generate_tests(
    request: Dict[str, Any],
    indexer = Depends(get_codebase_indexer)
):
    """
    Generate unit tests for a code file.
    
    Request body:
    {
        "file_path": "backend/services/validator.py",  # Optional
        "code_content": "...",  # Required if file_path not provided
        "test_framework": "pytest",  # Optional, default: pytest
        "include_edge_cases": true,  # Optional, default: true
        "include_error_handling": true  # Optional, default: true
    }
    
    Returns:
    {
        "test_code": "...",
        "test_file_path": "tests/backend/services/test_validator.py",
        "coverage_estimate": 85,
        "test_cases": ["test_validator_basic", "test_validator_edge_case"],
        "framework": "pytest"
    }
    """
    import os
    from backend.config.security import validate_api_key_config
    from backend.services.test_generator import get_test_generator
    
    # Security: Require API key for this endpoint
    security_status = validate_api_key_config()
    if not security_status["configured"]:
        raise HTTPException(
            status_code=403,
            detail="API key authentication required for test generation endpoint"
        )
    
    try:
        # Get parameters
        file_path = request.get("file_path")
        code_content = request.get("code_content")
        test_framework = request.get("test_framework", "pytest")
        include_edge_cases = request.get("include_edge_cases", True)
        include_error_handling = request.get("include_error_handling", True)
        
        if not file_path and not code_content:
            raise HTTPException(
                status_code=400,
                detail="Either file_path or code_content must be provided"
            )
        
        # Get test generator
        test_generator = get_test_generator(codebase_indexer=indexer)
        
        # Generate tests
        result = await test_generator.generate_tests(
            file_path=file_path,
            code_content=code_content,
            test_framework=test_framework,
            include_edge_cases=include_edge_cases,
            include_error_handling=include_error_handling
        )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error generating tests: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate tests: {str(e)}"
        )


@router.post("/onboarding")
async def generate_onboarding_guide(
    request: Dict[str, Any],
    indexer = Depends(get_codebase_indexer)
):
    """
    Generate personalized onboarding guide for new contributors.
    
    Request body:
    {
        "contributor_profile": "backend developer",  # Optional: "backend", "frontend", "fullstack", "devops"
        "experience_level": "intermediate",  # Optional: "beginner", "intermediate", "advanced"
        "interests": ["validation", "RAG", "testing"],  # Optional: list of topics of interest
        "questions": ["How do I get started?", "What are the most important files?"]  # Optional: specific questions
    }
    
    Returns:
    {
        "guide": {
            "welcome_message": "...",
            "starting_points": [
                {
                    "file_path": "backend/api/routers/chat_router.py",
                    "description": "Main chat endpoint - good starting point",
                    "why_important": "Handles all chat requests"
                }
            ],
            "important_files": [...],
            "first_issues": [
                {
                    "title": "Add unit tests for validator",
                    "description": "...",
                    "difficulty": "beginner",
                    "files_to_read": ["backend/validators/citation_validator.py"]
                }
            ],
            "code_examples": [
                {
                    "file_path": "backend/validators/citation_validator.py",
                    "snippet": "...",
                    "explanation": "This shows how validators work"
                }
            ],
            "next_steps": ["Read README.md", "Set up local environment", "..."]
        }
    }
    """
    try:
        from backend.services.git_history_retriever import get_git_history_retriever
        from backend.identity.prompt_builder import build_code_explanation_prompt
        from backend.api.utils.chat_helpers import generate_ai_response
        from backend.api.utils.chat_helpers import detect_language
        import os
        
        # Get parameters
        contributor_profile = request.get("contributor_profile", "developer")
        experience_level = request.get("experience_level", "intermediate")
        interests = request.get("interests", [])
        questions = request.get("questions", [])
        
        logger.info(f"📚 Generating onboarding guide for {contributor_profile} ({experience_level})")
        
        # Get Git history retriever
        git_retriever = get_git_history_retriever()
        
        # Query codebase for important files based on profile
        profile_queries = {
            "backend": "What are the most important backend files? Main API endpoints, core services",
            "frontend": "What are the main frontend components? UI, chat interface",
            "fullstack": "What are the core components connecting frontend and backend?",
            "devops": "What are the deployment and infrastructure files? Docker, Railway config",
            "developer": "What are the most important files to understand the codebase structure?"
        }
        
        base_query = profile_queries.get(contributor_profile.lower(), profile_queries["developer"])
        
        # Query codebase for important files
        important_files_results = indexer.query_codebase(base_query, n_results=10)
        
        # Query Git history for beginner-friendly commits/issues
        beginner_commits = git_retriever.query_history(
            "beginner friendly tasks, good first issues, easy contributions",
            n_results=5
        )
        
        # Build onboarding guide using LLM
        detected_lang = detect_language(str(questions) if questions else "en")
        
        # Prepare context
        important_files_context = []
        for result in important_files_results[:5]:
            metadata = result.get("metadata", {})
            important_files_context.append({
                "file_path": metadata.get("file_path", ""),
                "description": result.get("document", "")[:200],
                "line_range": f"{metadata.get('line_start', 0)}-{metadata.get('line_end', 0)}"
            })
        
        # Build prompt for onboarding guide
        onboarding_prompt = f"""You are StillMe's Onboarding Mentor. Generate a personalized onboarding guide for a new contributor.

Contributor Profile:
- Role: {contributor_profile}
- Experience Level: {experience_level}
- Interests: {', '.join(interests) if interests else 'General'}
- Questions: {', '.join(questions) if questions else 'None specified'}

Important Files Found:
{chr(10).join([f"- {f['file_path']} ({f['line_range']}): {f['description']}" for f in important_files_context])}

Git History (Recent Beginner-Friendly Commits):
{chr(10).join([f"- {c['subject']} ({c['date']})" for c in beginner_commits[:3]])}

Generate a comprehensive onboarding guide with:
1. Welcome message (personalized)
2. Starting points (3-5 files to read first, with explanations)
3. Important files (5-10 files, organized by category)
4. First issues (suggest 2-3 beginner-friendly tasks based on Git history)
5. Code examples (2-3 code snippets with explanations)
6. Next steps (actionable checklist)

Format the response as a structured guide that helps the contributor understand the codebase and get started quickly.
Be specific, practical, and encouraging.
"""
        
        # Generate guide using LLM
        guide_text = await generate_ai_response(
            prompt=onboarding_prompt,
            detected_lang=detected_lang,
            use_cache=False
        )
        
        # Parse guide into structured format (simple parsing, can be improved)
        guide = {
            "welcome_message": guide_text.split("##")[0].strip() if "##" in guide_text else guide_text[:500],
            "starting_points": important_files_context[:5],
            "important_files": important_files_context,
            "first_issues": [
                {
                    "title": commit.get("subject", ""),
                    "description": commit.get("document", "")[:200],
                    "difficulty": "beginner",
                    "commit_hash": commit.get("commit_hash", ""),
                    "date": commit.get("date", "")
                }
                for commit in beginner_commits[:3]
            ],
            "code_examples": [
                {
                    "file_path": result.get("metadata", {}).get("file_path", ""),
                    "snippet": result.get("document", "")[:300],
                    "explanation": f"Example from {result.get('metadata', {}).get('file_path', '')}"
                }
                for result in important_files_results[:3]
            ],
            "next_steps": [
                "Read README.md for project overview",
                "Set up local development environment",
                "Review starting point files",
                "Pick a first issue from the suggestions",
                "Join the community discussions"
            ],
            "full_guide": guide_text  # Include full LLM-generated guide
        }
        
        return {
            "guide": guide,
            "contributor_profile": contributor_profile,
            "experience_level": experience_level
        }
        
    except Exception as e:
        logger.error(f"❌ Error generating onboarding guide: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate onboarding guide: {str(e)}"
        )


@router.post("/review")
async def review_code(
    request: Dict[str, Any],
    indexer = Depends(get_codebase_indexer)
):
    """
    Review code and return suggestions.
    
    Request body:
    {
        "code_content": "...",  # Required
        "file_path": "backend/services/validator.py",  # Optional
        "check_style": true,  # Optional, default: true
        "check_security": true,  # Optional, default: true
        "check_performance": true  # Optional, default: true
    }
    
    Returns:
    {
        "issues": [
            {
                "severity": "warning",
                "line": 45,
                "type": "missing_error_handling",
                "message": "Missing error handling for open()",
                "suggestion": "Wrap open() in try-except block"
            }
        ],
        "summary": {
            "total": 5,
            "errors": 0,
            "warnings": 3,
            "info": 2
        },
        "score": 85,
        "file_path": "backend/services/validator.py"
    }
    """
    import os
    from backend.config.security import validate_api_key_config
    from backend.services.code_reviewer import get_code_reviewer
    
    # Security: Require API key for this endpoint
    security_status = validate_api_key_config()
    if not security_status["configured"]:
        raise HTTPException(
            status_code=403,
            detail="API key authentication required for code review endpoint"
        )
    
    try:
        # Get parameters
        code_content = request.get("code_content")
        if not code_content:
            raise HTTPException(
                status_code=400,
                detail="code_content is required"
            )
        
        file_path = request.get("file_path")
        check_style = request.get("check_style", True)
        check_security = request.get("check_security", True)
        check_performance = request.get("check_performance", True)
        
        # Get code reviewer
        reviewer = get_code_reviewer(codebase_indexer=indexer)
        
        # Review code
        result = await reviewer.review_code(
            code_content=code_content,
            file_path=file_path,
            check_style=check_style,
            check_security=check_security,
            check_performance=check_performance
        )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error reviewing code: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to review code: {str(e)}"
        )


@router.post("/index")
async def trigger_indexing(
    indexer = Depends(get_codebase_indexer),
    force: bool = False
):
    """
    Trigger codebase indexing (admin endpoint).
    
    This endpoint indexes the entire StillMe codebase into ChromaDB.
    Use with caution - indexing can take several minutes.
    
    Args:
        force: If True, re-index even if collection already has chunks
    
    Returns:
        Dictionary with indexing statistics
    """
    import os
    from backend.config.security import validate_api_key_config
    
    # Security: Require API key for this endpoint
    security_status = validate_api_key_config()
    if not security_status["configured"]:
        raise HTTPException(
            status_code=403,
            detail="API key authentication required for indexing endpoint"
        )
    
    try:
        # Check current status
        current_count = indexer.codebase_collection.count()
        
        if current_count > 0 and not force:
            return {
                "status": "skipped",
                "message": f"Collection already has {current_count} chunks. Use force=true to re-index.",
                "current_count": current_count
            }
        
        logger.info("🚀 Starting codebase indexing via API endpoint...")
        
        # Index entire codebase
        stats = indexer.index_codebase()
        
        # Verify final count
        final_count = indexer.codebase_collection.count()
        
        return {
            "status": "success",
            "message": "Codebase indexing completed successfully",
            "stats": stats,
            "final_count": final_count
        }
        
    except Exception as e:
        logger.error(f"❌ Error indexing codebase: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to index codebase: {str(e)}"
        )

