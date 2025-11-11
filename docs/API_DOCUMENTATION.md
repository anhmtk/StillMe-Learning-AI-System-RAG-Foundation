# 📚 StillMe API Documentation

Complete API reference with examples for all endpoints.

## 🔗 Base URL

- **Local Development**: `http://localhost:8000`
- **Production**: `https://stillme-backend-production.up.railway.app`

## 🔐 Authentication

Most endpoints are public. Some endpoints require API key:
- Set `X-API-Key` header: `X-API-Key: your-api-key`
- Or use `api_key` query parameter: `?api_key=your-api-key`

---

## 📋 Table of Contents

- [Chat & RAG APIs](#chat--rag-apis)
- [Learning APIs](#learning-apis)
- [Ethical Safety APIs](#ethical-safety-apis)
- [Self-Diagnosis APIs](#self-diagnosis-apis)
- [Validator Metrics APIs](#validator-metrics-apis)
- [System & Health APIs](#system--health-apis)
- [Debug APIs](#debug-apis)
- [Continuum Memory APIs](#continuum-memory-apis)
- [SPICE Framework APIs](#spice-framework-apis)

---

## 💬 Chat & RAG APIs

### `POST /api/chat/rag`

Chat with StillMe using RAG (Retrieval-Augmented Generation).

**Request:**
```json
{
  "message": "What is StillMe?",
  "use_rag": true,
  "context_limit": 3
}
```

**Response:**
```json
{
  "response": "StillMe is a continuously self-learning AI system...",
  "confidence_score": 0.85,
  "sources": [
    {
      "content": "...",
      "metadata": {"title": "...", "source": "..."}
    }
  ],
  "validation_info": {
    "passed": true,
    "overlap": 0.15
  }
}
```

**Example (cURL):**
```bash
curl -X POST http://localhost:8000/api/chat/rag \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What embedding model do you use?",
    "use_rag": true
  }'
```

**Example (HTTPie):**
```bash
http POST :8000/api/chat/rag \
  message="What is StillMe?" \
  use_rag:=true \
  context_limit:=3
```

**Rate Limit:** 10 requests/minute

---

### `POST /api/rag/add_knowledge`

Add knowledge to RAG vector database.

**Request:**
```json
{
  "content": "StillMe uses ChromaDB as vector database...",
  "source": "documentation",
  "content_type": "knowledge",
  "metadata": {
    "title": "StillMe Architecture",
    "tags": "architecture,vector-db"
  }
}
```

**Response:**
```json
{
  "status": "Knowledge added successfully",
  "content_type": "knowledge"
}
```

**Example:**
```bash
curl -X POST http://localhost:8000/api/rag/add_knowledge \
  -H "Content-Type: application/json" \
  -d '{
    "content": "StillMe uses all-MiniLM-L6-v2 for embeddings",
    "source": "technical-docs",
    "content_type": "knowledge",
    "metadata": {"title": "Embedding Model"}
  }'
```

**Rate Limit:** 20 requests/hour

---

### `POST /api/rag/query`

Query RAG system directly.

**Request:**
```json
{
  "query": "What is RAG?",
  "limit": 5
}
```

**Response:**
```json
{
  "results": [
    {
      "content": "...",
      "metadata": {...},
      "distance": 0.23
    }
  ]
}
```

**Example:**
```bash
http POST :8000/api/rag/query \
  query="What is StillMe?" \
  limit:=5
```

---

### `GET /api/rag/stats`

Get RAG statistics.

**Response:**
```json
{
  "total_documents": 1250,
  "collections": ["stillme_knowledge", "stillme_conversations"],
  "embedding_model": "all-MiniLM-L6-v2",
  "dimensions": 384
}
```

**Example:**
```bash
curl http://localhost:8000/api/rag/stats
```

---

## 📚 Learning APIs

### `POST /api/learning/sources/fetch`

Fetch content from all sources (RSS, arXiv, CrossRef, Wikipedia).

**Request:**
```json
{
  "max_items_per_source": 5,
  "auto_add": false,
  "use_pre_filter": true
}
```

**Response:**
```json
{
  "entries": [
    {
      "title": "...",
      "summary": "...",
      "link": "...",
      "source": "rss"
    }
  ],
  "stats": {
    "rss": 5,
    "arxiv": 3,
    "crossref": 2,
    "wikipedia": 0
  }
}
```

**Example:**
```bash
http POST :8000/api/learning/sources/fetch \
  max_items_per_source:=5 \
  auto_add:=false \
  use_pre_filter:=true
```

**Rate Limit:** 5 requests/hour

---

### `GET /api/learning/scheduler/status`

Get automated scheduler status.

**Response:**
```json
{
  "is_running": true,
  "next_run": "2025-01-10T14:00:00Z",
  "last_run": "2025-01-10T10:00:00Z",
  "cycles_completed": 42,
  "stats": {
    "total_fetched": 1250,
    "total_added": 850,
    "total_filtered": 400
  }
}
```

**Example:**
```bash
curl http://localhost:8000/api/learning/scheduler/status
```

---

### `POST /api/learning/scheduler/run-now`

Manually trigger a learning cycle immediately.

**Request:** (empty body)

**Response:**
```json
{
  "status": "started",
  "job_id": "abc123",
  "message": "Learning cycle started"
}
```

**Example:**
```bash
curl -X POST http://localhost:8000/api/learning/scheduler/run-now
```

**Note:** Requires API key

---

## 🛡️ Ethical Safety APIs

### `GET /api/learning/ethics/violations`

Get ethical violation history.

**Response:**
```json
{
  "violations": [
    {
      "timestamp": "2025-01-10T10:30:00Z",
      "content": "...",
      "reason": "hate_speech",
      "action": "blocked"
    }
  ],
  "total": 15,
  "by_reason": {
    "hate_speech": 5,
    "violence": 3,
    "adult_content": 7
  }
}
```

**Example:**
```bash
curl http://localhost:8000/api/learning/ethics/violations
```

---

### `GET /api/learning/ethics/stats`

Get ethical filter statistics.

**Response:**
```json
{
  "total_checked": 1250,
  "total_blocked": 15,
  "block_rate": 0.012,
  "by_category": {
    "hate_speech": 5,
    "violence": 3,
    "adult_content": 7
  }
}
```

**Example:**
```bash
http GET :8000/api/learning/ethics/stats
```

---

### `POST /api/learning/ethics/check-content`

Test content for ethical compliance.

**Request:**
```json
{
  "content": "Test content to check..."
}
```

**Response:**
```json
{
  "is_safe": true,
  "reasons": [],
  "confidence": 0.95
}
```

**Example:**
```bash
http POST :8000/api/learning/ethics/check-content \
  content="This is a test message"
```

---

## 🔍 Self-Diagnosis APIs

### `POST /api/learning/self-diagnosis/analyze-coverage`

Analyze knowledge coverage across topics.

**Request:**
```json
{
  "topic": "blockchain",
  "depth": 3
}
```

**Response:**
```json
{
  "topic": "blockchain",
  "coverage_score": 0.45,
  "gaps": [
    {
      "subtopic": "smart contracts",
      "coverage": 0.2,
      "priority": "high"
    }
  ],
  "suggestions": [
    "Learn more about smart contracts",
    "Add Ethereum documentation"
  ]
}
```

**Example:**
```bash
curl -X POST http://localhost:8000/api/learning/self-diagnosis/analyze-coverage \
  -H "Content-Type: application/json" \
  -d '{
    "topic": "blockchain",
    "depth": 3
  }'
```

**Use Case:** When user asks "What knowledge is missing about [topic]?", use this endpoint.

---

### `POST /api/learning/self-diagnosis/check-gap`

Check knowledge gap for a specific query.

**Request:**
```json
{
  "query": "How does Ethereum work?"
}
```

**Response:**
```json
{
  "has_gap": true,
  "gap_score": 0.6,
  "suggested_sources": ["ethereum.org", "docs.ethereum.org"]
}
```

**Example:**
```bash
http POST :8000/api/learning/self-diagnosis/check-gap \
  query="How does Ethereum work?"
```

---

### `GET /api/learning/self-diagnosis/suggest-focus`

Suggest learning focus based on gaps.

**Response:**
```json
{
  "suggestions": [
    {
      "topic": "blockchain",
      "priority": "high",
      "reason": "Low coverage (0.2)"
    }
  ]
}
```

**Example:**
```bash
curl http://localhost:8000/api/learning/self-diagnosis/suggest-focus
```

---

## ✅ Validator Metrics APIs

### `GET /api/validators/metrics`

Get validation metrics.

**Response:**
```json
{
  "metrics": {
    "total_validations": 1250,
    "pass_rate": 0.92,
    "passed_count": 1150,
    "failed_count": 100,
    "avg_overlap_score": 0.15,
    "avg_confidence_score": 0.78,
    "hallucination_reduction_rate": 0.08,
    "fallback_usage_count": 25,
    "uncertainty_expressed_count": 150
  }
}
```

**Example:**
```bash
curl http://localhost:8000/api/validators/metrics
```

**Use Case:** Check how well validators are working, hallucination reduction rate.

---

## 🏥 System & Health APIs

### `GET /health`

Health check endpoint.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2025-01-10T12:00:00Z"
}
```

**Example:**
```bash
curl http://localhost:8000/health
```

---

### `GET /ready`

Readiness check (checks dependencies).

**Response:**
```json
{
  "status": "ready",
  "components": {
    "rag": true,
    "chromadb": true,
    "embedding": true
  }
}
```

**Example:**
```bash
curl http://localhost:8000/ready
```

---

### `GET /api/status`

System status with detailed information.

**Response:**
```json
{
  "status": "operational",
  "version": "0.6.2",
  "components": {
    "rag": {"status": "ok"},
    "chromadb": {"status": "ok"},
    "embedding": {"status": "ok"}
  },
  "errors": []
}
```

**Example:**
```bash
curl http://localhost:8000/api/status
```

---

## 🐛 Debug APIs

### `GET /api/debug/cache-status`

Get model cache status.

**Response:**
```json
{
  "status": "success",
  "cache": {
    "exists": true,
    "path": "/app/hf_cache",
    "size_mb": 80.5,
    "model_files_found": true,
    "is_persistent": true,
    "is_writable": true
  }
}
```

**Example:**
```bash
curl http://localhost:8000/api/debug/cache-status
```

---

### `GET /api/debug/model-status`

Get model loading status.

**Response:**
```json
{
  "status": "success",
  "model": {
    "model_name": "all-MiniLM-L6-v2",
    "model_loaded": true,
    "embedding_dimension": 384,
    "cache": {
      "exists": true,
      "path": "/app/hf_cache"
    }
  }
}
```

**Example:**
```bash
http GET :8000/api/debug/model-status
```

---

### `GET /api/debug/environment`

Get environment variables and paths.

**Response:**
```json
{
  "status": "success",
  "environment_variables": {
    "HF_HOME": "/app/hf_cache",
    "TRANSFORMERS_CACHE": "/app/hf_cache",
    "SENTENCE_TRANSFORMERS_HOME": "/app/hf_cache"
  },
  "railway_persistent_volume": {
    "path": "/app/hf_cache",
    "exists": true,
    "is_persistent": true
  }
}
```

**Example:**
```bash
curl http://localhost:8000/api/debug/environment
```

---

## 🧠 Continuum Memory APIs

### `GET /api/v1/tiers/stats`

Get tier statistics (L0-L3).

**Response:**
```json
{
  "tiers": {
    "L0": {"count": 100, "size_mb": 5.2},
    "L1": {"count": 50, "size_mb": 2.5},
    "L2": {"count": 20, "size_mb": 1.0},
    "L3": {"count": 10, "size_mb": 0.5}
  }
}
```

**Example:**
```bash
curl http://localhost:8000/api/v1/tiers/stats
```

---

### `POST /api/v1/tiers/promote/{item_id}`

Promote item to higher tier.

**Example:**
```bash
curl -X POST http://localhost:8000/api/v1/tiers/promote/abc123 \
  -H "X-API-Key: your-key"
```

**Note:** Requires API key

---

## 🔬 SPICE Framework APIs

### `POST /api/spice/run-cycle`

Run SPICE evaluation cycle.

**Request:**
```json
{
  "challenger_type": "ethical",
  "topics": ["AI ethics", "transparency"]
}
```

**Response:**
```json
{
  "status": "completed",
  "results": {
    "challenges_generated": 10,
    "answers_validated": 8,
    "score": 0.85
  }
}
```

**Example:**
```bash
http POST :8000/api/spice/run-cycle \
  challenger_type="ethical" \
  topics:='["AI ethics"]'
```

---

## 📊 Common Response Fields

### Chat Response
- `response`: Generated text response
- `confidence_score`: 0.0-1.0 confidence level
- `sources`: Array of retrieved context documents
- `validation_info`: Validation results
  - `passed`: Boolean
  - `overlap`: Evidence overlap score
  - `used_fallback`: Boolean

### Error Response
```json
{
  "error": "Error message",
  "detail": "Detailed error information"
}
```

---

## ⚠️ Common Errors

### 503 Service Unavailable
- **Cause**: RAG system not initialized
- **Solution**: Wait for startup to complete, check `/ready` endpoint

### 429 Too Many Requests
- **Cause**: Rate limit exceeded
- **Solution**: Wait and retry, check rate limits

### 401 Unauthorized
- **Cause**: API key required but not provided
- **Solution**: Add `X-API-Key` header or `api_key` query parameter

---

## 🔗 Interactive API Documentation

StillMe provides interactive API documentation via Swagger UI:

- **Local**: http://localhost:8000/docs
- **Production**: https://stillme-backend-production.up.railway.app/docs

You can test all endpoints directly in the browser!

---

## 📝 Notes

- All timestamps are in ISO 8601 format (UTC)
- All endpoints return JSON
- Rate limits are per IP address
- Some endpoints require API key (see Authentication section)

---

**Last Updated**: 2025-01-10  
**API Version**: v0.6.2

