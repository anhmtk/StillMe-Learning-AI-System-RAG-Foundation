---
name: "[P1B] Health & Readiness Endpoints"
about: Add /health (liveness) and /ready (readiness) endpoints for deployment health checks
title: "[P1B] Health & Readiness Endpoints"
labels: type:infra, risk:low, area:api, milestone:P1-Foundation
assignees: ''
---

## 🎯 Objective

Add production-ready health check endpoints for Kubernetes/Docker health probes and monitoring.

## 📋 Scope

### Endpoints to Add:
1. **GET /health** - Liveness probe (service is running)
2. **GET /ready** - Readiness probe (service is ready to accept traffic)

### Readiness Checks:
- ✅ SQLite database connectivity (SELECT 1)
- ✅ ChromaDB heartbeat (PersistentClient.heartbeat())
- ✅ Embedding service (encode_text("test"))

## ✅ Acceptance Criteria

1. **/health** returns `{"status": "ok"}` with 200 status
2. **/ready** returns 200 when all checks pass, 503 if any check fails
3. **/ready** includes check details in JSON response
4. **Feature flag**: `ENABLE_HEALTH_READY=true` (default: true)
5. **No breaking changes** - Existing endpoints unaffected

## 🔍 Evidence & Self-Critique

### Current State:
- **File**: `backend/api/main.py`
- **Existing**: `/health` endpoint exists (line 309) but only checks RAG status
- **Missing**: `/ready` endpoint with comprehensive checks

### Assumptions:
1. ✅ **ChromaDB has heartbeat** - `PersistentClient` supports health checks
2. ✅ **SQLite connection test** - Simple `SELECT 1` is sufficient
3. ⚠️ **Embedding service test** - May be slow, consider timeout

### Risks & Mitigation:
- **Risk**: Readiness checks too slow
  - **Mitigation**: Add timeouts (1-2s per check), fail fast
- **Risk**: False negatives (service works but check fails)
  - **Mitigation**: Test checks independently, log failures
- **Rollback**: Feature flag `ENABLE_HEALTH_READY=false` disables new endpoints

## 🧪 How to Verify

### Manual Testing:
```bash
# Liveness check
curl http://localhost:8000/health
# Expected: {"status": "ok"}

# Readiness check (all passing)
curl http://localhost:8000/ready
# Expected: {"status": "ready", "checks": {"database": true, "vector_db": true, "embeddings": true}}

# Readiness check (simulate failure - stop ChromaDB)
# Expected: {"status": "not_ready", "checks": {"database": true, "vector_db": false, "embeddings": true}}
```

### Kubernetes/Docker:
```yaml
# docker-compose.yml or k8s deployment
livenessProbe:
  httpGet:
    path: /health
    port: 8000
  initialDelaySeconds: 10
  periodSeconds: 30

readinessProbe:
  httpGet:
    path: /ready
    port: 8000
  initialDelaySeconds: 5
  periodSeconds: 10
```

## 📝 Implementation Plan

1. Add `/ready` endpoint to `main.py` (or router if P1A merged)
2. Implement 3 checks (SQLite, ChromaDB, Embeddings)
3. Add feature flag `ENABLE_HEALTH_READY`
4. Add timeouts for checks
5. Update `/health` to be simpler (just status)
6. Add tests for both endpoints
7. Update documentation

## 🔄 Rollback Plan

```bash
# Option 1: Feature flag
export ENABLE_HEALTH_READY=false

# Option 2: Revert commit
git revert <commit-hash>
```

