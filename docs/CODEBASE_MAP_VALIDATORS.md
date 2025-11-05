# StillMe Codebase Map - Validators Integration Points

## REFLECT: Current State Analysis

**Hypothesis:**
- Backend FastAPI has endpoints `/api/chat/rag` and `/api/rag/query` as validator chain integration points
- RAG system already exists with ChromaDB + EmbeddingService
- No ethics guard in current backend (may be in legacy)
- LLM router is simple: fallback by API key (DeepSeek → OpenAI)
- Streamlit dashboard can display validation metrics

**Risks:**
- No validators/ module currently → must create new
- Ethics guard may be in legacy → needs adapter
- LLM calls are directly in main.py → needs light refactor

**Rollback Plan:**
- All validators can be disabled via `ENABLE_VALIDATORS=false`
- Don't modify old code, only add wrapper layer

## Summary Table of Existing Components

| Path | Role | Has Tests? | Notes |
|------|------|------------|-------|
| **Backend FastAPI** |
| `backend/api/main.py` | FastAPI entry point, defines routes | ✅ `tests/test_backend_api.py` | Main endpoint: `/api/chat/rag` (line 158), `/api/rag/query` (line 333) |
| `backend/api/routes/` | (Directory exists but may be empty) | ❓ | Can be used to split routes |
| `backend/api/models/` | (Directory exists but may be empty) | ❓ | Can be used for Pydantic models |
| **RAG System** |
| `backend/vector_db/__init__.py` | Exports ChromaClient, EmbeddingService, RAGRetrieval | ✅ `tests/test_rag_system.py` | Main interface: `RAGRetrieval.retrieve_context()` |
| `backend/vector_db/chroma_client.py` | ChromaDB client, manages collections | ✅ | Methods: `search_knowledge()`, `search_conversations()`, `add_knowledge()` |
| `backend/vector_db/embeddings.py` | EmbeddingService with sentence-transformers | ✅ | Method: `encode_text()` |
| `backend/vector_db/rag_retrieval.py` | RAG service, combines search + context building | ✅ | Methods: `retrieve_context()`, `build_prompt_context()`, `add_learning_content()` |
| **LLM Router** |
| `backend/api/main.py` (line 810-906) | `generate_ai_response()`, `call_deepseek_api()`, `call_openai_api()` | ❌ | Simple: fallback DeepSeek → OpenAI. System prompt hardcoded. |
| **Ethics/Guard** |
| `docs/ETHICS_SECURITY_PRIVACY_REPORT.md` | Documentation about EthicsGuard | ❌ | Mentions `stillme_core/modules/ethical_core_system_v1.py` but in legacy/graveyard |
| **Learning System** |
| `backend/learning/knowledge_retention.py` | KnowledgeRetention service | ❓ | May relate to validation metrics |
| `backend/learning/accuracy_scorer.py` | AccuracyScorer service | ❓ | Can integrate with validator metrics |
| **Services** |
| `backend/services/rss_fetcher.py` | RSS fetcher | ❓ | - |
| `backend/services/learning_scheduler.py` | Learning scheduler | ❓ | - |
| `backend/services/self_diagnosis.py` | Self-diagnosis agent | ❓ | - |
| `backend/services/content_curator.py` | Content curator | ❓ | - |
| **Dashboard** |
| `dashboard.py` | Streamlit dashboard | ✅ `tests/test_frontend_app.py` | Pages: Overview, RAG, Learning, Community. Can add Validation panel. |
| **Tests** |
| `tests/test_backend_api.py` | Tests for FastAPI endpoints | ✅ | Test health, chat endpoints |
| `tests/test_rag_system.py` | Tests for RAG system | ✅ | Test ChromaClient, EmbeddingService, RAGRetrieval |
| `tests/conftest.py` | Pytest fixtures | ✅ | Test data, mocks |

## Validator Chain Integration Points

### 1. Main Endpoint: `/api/chat/rag` (line 158-228)
**Current Flow:**
```
User request → RAG retrieve_context() → build_prompt_context() → generate_ai_response() → score_response() → return
```

**Validator Integration Points:**
- **Before model call:** IdentityInjector into system prompt (line 175-181)
- **After model call:** ValidatorChain (line 182-185)
- **Finally:** ToneAligner before return (line 219)

### 2. RAG Query Endpoint: `/api/rag/query` (line 333-357)
**Note:** This endpoint only returns context, doesn't generate response. May not need validator here.

### 3. LLM Router: `generate_ai_response()` (line 810-826)
**Current Flow:**
```
Check API keys → call_deepseek_api() or call_openai_api() → return response
```

**Validator Integration Points:**
- Wrap `generate_ai_response()` to inject identity and validate output
- All model paths (DeepSeek, OpenAI) go through wrapper

## Structure to Create

### New Modules (not yet existing):
- `backend/validators/` - Validator chain and specific validators
- `backend/identity/` - IdentityInjector
- `backend/tone/` - ToneAligner

### Reusable Modules:
- `backend/vector_db/rag_retrieval.py` - Already exists, used to get context docs
- `backend/learning/accuracy_scorer.py` - Can integrate metrics

## Validation

✅ Map has listed all main components
✅ Validator chain integration points identified
✅ Risks and rollback plan analyzed
✅ Can proceed to B2 (Integration Plan)
