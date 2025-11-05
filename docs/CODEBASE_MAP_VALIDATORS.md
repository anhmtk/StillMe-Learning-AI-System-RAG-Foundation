# StillMe Codebase Map - Validators Integration Points

## REFLECT: Phân tích hiện trạng

**Giả thuyết:**
- Backend FastAPI có endpoint `/api/chat/rag` và `/api/rag/query` là điểm gắn validator chain
- RAG system đã có sẵn với ChromaDB + EmbeddingService
- Không có ethics guard trong backend hiện tại (có thể ở legacy)
- LLM router đơn giản: fallback theo API key (DeepSeek → OpenAI)
- Dashboard Streamlit có thể hiển thị metrics validation

**Rủi ro:**
- Không có module validators/ hiện tại → phải tạo mới
- Ethics guard có thể ở legacy → cần adapter
- LLM calls nằm trực tiếp trong main.py → cần refactor nhẹ

**Phương án rollback:**
- Tất cả validators có thể tắt bằng `ENABLE_VALIDATORS=false`
- Không sửa code cũ, chỉ thêm wrapper layer

## Bảng tóm tắt thành phần hiện có

| Path | Vai trò | Có test? | Ghi chú |
|------|--------|----------|---------|
| **Backend FastAPI** |
| `backend/api/main.py` | Entry point FastAPI, định nghĩa routes | ✅ `tests/test_backend_api.py` | Endpoint chính: `/api/chat/rag` (line 158), `/api/rag/query` (line 333) |
| `backend/api/routes/` | (Thư mục tồn tại nhưng có thể trống) | ❓ | Có thể dùng để tách routes |
| `backend/api/models/` | (Thư mục tồn tại nhưng có thể trống) | ❓ | Có thể dùng cho Pydantic models |
| **RAG System** |
| `backend/vector_db/__init__.py` | Export ChromaClient, EmbeddingService, RAGRetrieval | ✅ `tests/test_rag_system.py` | Interface chính: `RAGRetrieval.retrieve_context()` |
| `backend/vector_db/chroma_client.py` | ChromaDB client, quản lý collections | ✅ | Methods: `search_knowledge()`, `search_conversations()`, `add_knowledge()` |
| `backend/vector_db/embeddings.py` | EmbeddingService với sentence-transformers | ✅ | Method: `encode_text()` |
| `backend/vector_db/rag_retrieval.py` | RAG service, combine search + context building | ✅ | Methods: `retrieve_context()`, `build_prompt_context()`, `add_learning_content()` |
| **LLM Router** |
| `backend/api/main.py` (line 810-906) | `generate_ai_response()`, `call_deepseek_api()`, `call_openai_api()` | ❌ | Đơn giản: fallback DeepSeek → OpenAI. System prompt hardcoded. |
| **Ethics/Guard** |
| `docs/ETHICS_SECURITY_PRIVACY_REPORT.md` | Documentation về EthicsGuard | ❌ | Đề cập `stillme_core/modules/ethical_core_system_v1.py` nhưng ở legacy/graveyard |
| **Learning System** |
| `backend/learning/knowledge_retention.py` | KnowledgeRetention service | ❓ | Có thể liên quan đến validation metrics |
| `backend/learning/accuracy_scorer.py` | AccuracyScorer service | ❓ | Có thể tích hợp với validator metrics |
| **Services** |
| `backend/services/rss_fetcher.py` | RSS fetcher | ❓ | - |
| `backend/services/learning_scheduler.py` | Learning scheduler | ❓ | - |
| `backend/services/self_diagnosis.py` | Self-diagnosis agent | ❓ | - |
| `backend/services/content_curator.py` | Content curator | ❓ | - |
| **Dashboard** |
| `dashboard.py` | Streamlit dashboard | ✅ `tests/test_frontend_app.py` | Pages: Overview, RAG, Learning, Community. Có thể thêm panel Validation. |
| **Tests** |
| `tests/test_backend_api.py` | Tests cho FastAPI endpoints | ✅ | Test health, chat endpoints |
| `tests/test_rag_system.py` | Tests cho RAG system | ✅ | Test ChromaClient, EmbeddingService, RAGRetrieval |
| `tests/conftest.py` | Pytest fixtures | ✅ | Test data, mocks |

## Điểm tích hợp Validator Chain

### 1. Endpoint chính: `/api/chat/rag` (line 158-228)
**Flow hiện tại:**
```
User request → RAG retrieve_context() → build_prompt_context() → generate_ai_response() → score_response() → return
```

**Điểm gắn validator:**
- **Trước model call:** IdentityInjector vào system prompt (line 175-181)
- **Sau model call:** ValidatorChain (line 182-185)
- **Cuối cùng:** ToneAligner trước return (line 219)

### 2. Endpoint RAG query: `/api/rag/query` (line 333-357)
**Ghi chú:** Endpoint này chỉ trả về context, không generate response. Có thể không cần validator ở đây.

### 3. LLM Router: `generate_ai_response()` (line 810-826)
**Flow hiện tại:**
```
Check API keys → call_deepseek_api() hoặc call_openai_api() → return response
```

**Điểm gắn validator:**
- Wrap `generate_ai_response()` để inject identity và validate output
- Tất cả model paths (DeepSeek, OpenAI) đều đi qua wrapper

## Cấu trúc cần tạo

### Module mới (chưa có):
- `backend/validators/` - Validator chain và các validator cụ thể
- `backend/identity/` - IdentityInjector
- `backend/tone/` - ToneAligner

### Module tái sử dụng:
- `backend/vector_db/rag_retrieval.py` - Đã có, dùng để lấy context docs
- `backend/learning/accuracy_scorer.py` - Có thể tích hợp metrics

## Validation

✅ Bản đồ đã liệt kê đầy đủ các thành phần chính
✅ Đã xác định điểm gắn validator chain
✅ Đã phân tích rủi ro và phương án rollback
✅ Có thể tiến hành B2 (Integration Plan)

