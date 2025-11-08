---
name: "[P1A] Routerization Complete - Final 4 Endpoints"
about: Complete routerization by moving remaining 4 endpoints to system_router
title: "[P1A] Routerization Complete - System Router (4 endpoints)"
labels: type:refactor, risk:low, area:api, milestone:P1-Foundation
assignees: ''
---

## 🎯 Objective

Complete routerization by moving the final 4 endpoints from `main.py` to `system_router.py`:
- `/` - Root endpoint
- `/health` - Health check
- `/api/status` - System status
- `/api/validators/metrics` - Validation metrics

## 📋 Scope

**Move-only refactoring** - No logic changes, only code organization.

### Target:
- Create `backend/api/routers/system_router.py` with 4 endpoints
- Update `main.py` to include system_router
- Update `backend/api/routers/__init__.py`
- Update README.md

## ✅ Acceptance Criteria

1. **All 42 endpoints still work** - No breaking changes
2. **OpenAPI docs unchanged** - All routes visible at `/docs`
3. **Pytest passes** - No new test failures introduced
4. **Code organization** - `main.py` reduced to ~1900 lines (from 2817)
5. **No linter errors** - Clean code, no `# type: ignore`

## 🔍 Evidence & Self-Critique

### Current State:
- **File**: `backend/api/main.py`
- **Lines**: ~1899 (after previous routerization)
- **Remaining endpoints**: 4 (root, health, status, validators/metrics)

### Endpoint Distribution:
- ✅ Chat: 4 endpoints → `chat_router.py`
- ✅ Learning: 19 endpoints → `learning_router.py`
- ✅ RAG: 4 endpoints → `rag_router.py`
- ✅ Tiers: 5 endpoints → `tiers_router.py`
- ✅ SPICE: 6 endpoints → `spice_router.py`
- ⏳ System: 4 endpoints → `system_router.py` (NEW)

### Assumptions:
1. ✅ **Move-only is safe** - No logic changes = minimal risk
2. ✅ **FastAPI routers work** - Standard pattern, well-tested
3. ⚠️ **Global state access** - Routers need access to global services (rag_retrieval, etc.) - using dependency injection pattern

### Risks & Mitigation:
- **Risk**: Breaking API contracts
  - **Mitigation**: Move-only, no logic changes, verify endpoints work
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

# 3. Test system endpoints
curl http://localhost:8000/
curl http://localhost:8000/health
curl http://localhost:8000/api/status
curl http://localhost:8000/api/validators/metrics
```

### Automated Testing:
```bash
# Run all tests
pytest tests/ -v

# Check for linter errors
# (No # type: ignore allowed)
```

## 📝 Implementation Plan

1. ✅ Create `backend/api/routers/system_router.py` with 4 endpoints
2. ✅ Update `main.py` to include system_router
3. ✅ Update `backend/api/routers/__init__.py`
4. ✅ Update README.md
5. ⏳ Verify all endpoints work
6. ⏳ Run pytest
7. ⏳ Check linter errors

## 🔄 Rollback Plan

If issues arise:
```bash
git revert <commit-hash>
# Or manually revert main.py and delete system_router.py
```

Single commit revert is sufficient (move-only refactoring).

## 📊 Expected Results

- **main.py**: Reduced from ~1899 to ~1850 lines
- **Total routers**: 6 (chat, learning, rag, tiers, spice, system)
- **All 42 endpoints**: Fully routerized
- **Code quality**: No linter errors, no `# type: ignore`

