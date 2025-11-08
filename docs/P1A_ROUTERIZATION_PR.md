# [P1A] Routerization - Split main.py into Modular Routers

## 🎯 Objective

Split `backend/api/main.py` (currently **2817 lines** with **42 endpoints**) into modular routers for better maintainability and OSS-friendliness.

## 📋 Scope

**Move-only refactoring** - No logic changes, only code organization.

### Target Structure:
```
backend/api/
  main.py (100-200 lines - bootstrap only)
  routers/
    __init__.py
    chat_router.py (4 endpoints: /api/chat/*)
    learning_router.py (19 endpoints: /api/learning/*)
    rag_router.py (4 endpoints: /api/rag/*)
    tiers_router.py (5 endpoints: /api/v1/tiers/*)
    spice_router.py (6 endpoints: /api/spice/*)
```

## 🔍 Evidence & Self-Critique

### Current State:
- **File**: `backend/api/main.py`
- **Lines**: 2817 (verified via `Get-Content backend/api/main.py | Measure-Object -Line`)
- **Endpoints**: 42 (verified via `grep "@app\.(get|post)" backend/api/main.py`)

### Endpoint Distribution:
- **Chat**: 4 endpoints (lines 345, 2263, 2285, 2290)
  - `/api/chat/rag` (POST)
  - `/api/chat/smart_router` (POST)
  - `/api/chat/openai` (POST) - Legacy
  - `/api/chat/deepseek` (POST) - Legacy
- **Learning**: 19 endpoints (lines 828-2034)
- **RAG**: 4 endpoints (lines 986, 1030, 1053, 1067)
- **Tiers**: 5 endpoints (lines 2062-2241)
- **SPICE**: 6 endpoints (lines 2650-2790)
- **Root/Health**: 2 endpoints (lines 291, 309)

### Assumptions:
1. ✅ **Move-only is safe** - No logic changes = minimal risk
2. ✅ **FastAPI routers work** - Standard pattern, well-tested
3. ⚠️ **Global state access** - Routers need access to global services (rag_retrieval, etc.) - will use dependency injection pattern

### Risks & Mitigation:
- **Risk**: Breaking API contracts
  - **Mitigation**: Move-only, no logic changes, smoke tests verify endpoints
- **Risk**: Import errors
  - **Mitigation**: Test imports, verify all dependencies available
- **Rollback**: Single commit revert (move-only = easy rollback)

## 🧪 How to Verify

### Manual Testing:
```bash
# 1. Start server
python -m uvicorn backend.api.main:app --reload

# 2. Check OpenAPI docs
curl http://localhost:8000/docs

# 3. Test each router group
curl -X POST http://localhost:8000/api/chat/rag -H "Content-Type: application/json" -d '{"message":"test"}'
curl -X GET http://localhost:8000/api/learning/metrics
curl -X GET http://localhost:8000/api/rag/stats
curl -X GET http://localhost:8000/api/v1/tiers/stats
curl -X GET http://localhost:8000/api/spice/status
```

### Automated Testing:
```bash
# Run smoke tests
pytest tests/test_router_smoke.py -v

# Run all tests
pytest tests/ -v
```

## 📝 Implementation Plan

1. ✅ Create `backend/api/routers/__init__.py`
2. ⏳ Extract chat endpoints → `chat_router.py`
3. ⏳ Extract learning endpoints → `learning_router.py`
4. ⏳ Extract RAG endpoints → `rag_router.py`
5. ⏳ Extract tiers endpoints → `tiers_router.py`
6. ⏳ Extract SPICE endpoints → `spice_router.py`
7. ⏳ Update `main.py` to use `app.include_router()`
8. ⏳ Add smoke tests
9. ⏳ Verify all endpoints work

## 🔄 Rollback Plan

If issues arise:
```bash
git revert <commit-hash>
# Or manually revert main.py and delete routers/ directory
```

Single commit revert is sufficient (move-only refactoring).

