# StillMe Architecture Overview - For AI Assistants

> **Purpose**: This document provides a comprehensive technical overview of StillMe's architecture for AI assistants (like Gemini, Claude, etc.) to understand the system and provide informed advice.

## 🎯 Quick Summary

StillMe is a **RAG-based Learning AI System** that:
- **Learns automatically every 4 hours** (6 cycles/day) from RSS feeds, arXiv, CrossRef, Wikipedia
- Uses **ChromaDB with PersistentClient** for vector storage
- Implements **19 validators organized into 7 layers** for response validation
- Has **self-improvement mechanisms** that learn from validation patterns
- Prevents **duplicate content** through deduplication checks

---

## 📋 Table of Contents

1. [Learning System Architecture](#1-learning-system-architecture)
2. [RAG & Vector Database](#2-rag--vector-database)
3. [Validation Framework](#3-validation-framework)
4. [Self-Improvement System](#4-self-improvement-system)
5. [Technical Decisions & Trade-offs](#5-technical-decisions--trade-offs)

---

## 1. Learning System Architecture

### 1.1 Scheduling Mechanism

**Question from Gemini**: "Bạn đang dùng Cron Job hay Celery/Redis để quản lý việc này?"

**Answer**: StillMe uses **asyncio background tasks**, NOT Cron Job or Celery/Redis.

**Implementation**:
- Location: `backend/services/learning_scheduler.py`
- Mechanism: `asyncio.Task` running in background
- Interval: 4 hours (configurable via `interval_hours` parameter)
- Lifecycle: Started on FastAPI startup, runs continuously until shutdown

**Code Reference**:
```python
# backend/services/learning_scheduler.py
class LearningScheduler:
    def __init__(self, interval_hours: int = 4):
        self.interval_hours = interval_hours
        self._task: Optional[asyncio.Task] = None
    
    async def _run_continuously(self):
        """Background task that runs learning cycles every N hours"""
        while not self._stop_event.is_set():
            await self.run_learning_cycle()
            await asyncio.sleep(self.interval_hours * 3600)
```

**Why asyncio instead of Cron/Celery?**:
- Simpler deployment (no external dependencies)
- Better integration with FastAPI async architecture
- Easier error handling and logging
- Sufficient for single-instance deployment

### 1.2 Duplicate Prevention

**Question from Gemini**: "Bạn xử lý thế nào để tránh việc Overlapping/Duplicate dữ liệu nếu một nguồn (như arXiv) chưa có bài mới?"

**Answer**: StillMe implements **multi-layer deduplication**:

1. **Pre-check before adding to RAG**:
   - Location: `backend/api/routers/learning_router.py` (lines 389-403)
   - Mechanism: Checks if content already exists in ChromaDB by `source_url` or `title`
   - If duplicate found: Status = "Filtered: Duplicate", skip adding

2. **Deduplication during retrieval**:
   - Location: `backend/vector_db/rag_retrieval.py` (lines 425-447)
   - Mechanism: Removes duplicate documents based on `source_url`, `url`, or `title`
   - Prevents same article from appearing multiple times due to chunking

3. **EvidenceOverlap validator**:
   - Location: `backend/validators/evidence_overlap.py`
   - Purpose: Detects overlapping evidence in responses (not for learning deduplication, but for response quality)

**Code Reference**:
```python
# Check for duplicates before adding
is_duplicate = False
if rag_retrieval:
    try:
        # Check if content already exists
        existing = rag_retrieval.check_content_exists(
            source_url=entry.get("source_url"),
            title=entry.get("title")
        )
        is_duplicate = existing is not None
    except Exception:
        pass

if is_duplicate:
    status = "Filtered: Duplicate"
    continue  # Skip adding
```

**Result**: StillMe effectively prevents duplicate content even if the same article appears in multiple RSS feeds or if arXiv hasn't published new papers.

---

## 2. RAG & Vector Database

### 2.1 ChromaDB Configuration

**Question from Gemini**: "Bạn có đang dùng Persistent Client để lưu trữ lâu dài không?"

**Answer**: ✅ **YES**, StillMe uses `PersistentClient` for long-term storage.

**Implementation**:
- Location: `backend/vector_db/chroma_client.py` (line 222)
- Client Type: `chromadb.PersistentClient`
- Persistence Path: `/app/data/vector_db` (or env var `CHROMA_PERSIST_DIR`)
- Settings: `anonymized_telemetry=False`, `allow_reset=True`

**Code Reference**:
```python
# backend/vector_db/chroma_client.py
self.client = chromadb.PersistentClient(
    path=persist_directory,  # /app/data/vector_db
    settings=Settings(
        anonymized_telemetry=False,
        allow_reset=True
    )
)
```

**Why PersistentClient?**:
- Data persists across restarts
- No need to re-embed content on every startup
- Essential for production deployment (Railway, etc.)

### 2.2 Re-ranking Mechanism

**Question from Gemini**: "Bạn có cơ chế Re-ranking (Xếp hạng lại) sau khi lấy kết quả từ ChromaDB không?"

**Answer**: StillMe uses **MMR (Maximal Marginal Relevance)** for diversity, but **NO explicit re-ranking** after similarity search.

**Current Implementation**:
- Location: `backend/vector_db/rag_retrieval.py` (line 117)
- Mechanism: `use_mmr=True`, `mmr_lambda=0.7`
- Purpose: Balances similarity and diversity in retrieved documents

**What StillMe DOES**:
- ✅ MMR for diversity (reduces redundant results)
- ✅ Deduplication (removes duplicate documents)
- ✅ Priority filtering (CRITICAL_FOUNDATION documents prioritized)
- ✅ Similarity threshold filtering (default: 0.1)

**What StillMe DOES NOT have**:
- ❌ Cross-encoder re-ranking (e.g., using a separate model to re-rank results)
- ❌ LLM-based re-ranking (e.g., using LLM to score relevance)

**Potential Improvement** (for Gemini's consideration):
- Could add cross-encoder re-ranking for better relevance
- Could use LLM to re-rank top-K results for critical queries
- Trade-off: Additional latency vs. better relevance

---

## 3. Validation Framework

### 3.1 Validator Architecture

**Structure**:
- **19 validators total** organized into **7 layers**
- Dynamic validator selection (10-17 validators per response, depending on context)
- Sequential and parallel execution modes

**Layers**:
1. **Language & Format**: LanguageValidator, SchemaFormat
2. **Citation & Evidence**: CitationRequired, CitationRelevance, EvidenceOverlap
3. **Content Quality**: ConfidenceValidator, FactualHallucinationValidator, NumericUnitsBasic
4. **Identity & Ethics**: IdentityCheckValidator, EgoNeutralityValidator, EthicsAdapter, ReligiousChoiceValidator
5. **Source Consensus**: SourceConsensusValidator
6. **Specialized Validation**: PhilosophicalDepthValidator, HallucinationExplanationValidator, VerbosityValidator, AISelfModelValidator
7. **Fallback & Review**: FallbackHandler, ReviewAdapter

**Key Validators**:
- **FactualHallucinationValidator**: Detects explicit fake entities, non-existent concepts
- **EvidenceOverlap**: Checks if response evidence overlaps with retrieved context
- **ConfidenceValidator**: Ensures appropriate uncertainty expression when confidence is low

---

## 4. Self-Improvement System

### 4.1 What "Self-Evolving" Means

**Question from Gemini**: "Hệ thống 'tiến hóa' theo nghĩa là nạp thêm dữ liệu hay là tự điều chỉnh tham số/prompt?"

**Answer**: StillMe's "self-evolving" means **learning from validation patterns and suggesting learning content**, NOT automatic parameter/prompt adjustment.

**Current Implementation**:
- Location: `backend/validators/self_improvement.py`
- Component: `SelfImprovementAnalyzer`
- Mechanism:
  1. Analyzes validation failures over time (last 7 days)
  2. Detects knowledge gaps (questions with no RAG context)
  3. Suggests learning content based on gaps
  4. Updates learning priorities

**What StillMe DOES**:
- ✅ Analyzes validation patterns
- ✅ Detects knowledge gaps from validation failures
- ✅ Suggests topics to learn (e.g., "Geneva Conference 1954", "Bretton Woods 1944")
- ✅ Tracks learning proposals for future cycles

**What StillMe DOES NOT do**:
- ❌ Automatic parameter adjustment (e.g., Top-K, similarity threshold)
- ❌ Automatic prompt modification
- ❌ Self-modifying code

**Philosophy**: StillMe evolves through **learning new content**, not through **changing its architecture**. The architecture is fixed, but knowledge grows.

**Code Reference**:
```python
# backend/validators/self_improvement.py
class SelfImprovementAnalyzer:
    def get_knowledge_gaps_from_failures(self, days: int = 7):
        """Extract knowledge gaps from validation failures"""
        recent_failures = [
            r for r in self.tracker._records
            if datetime.fromisoformat(r.timestamp) >= cutoff_time
            and not r.passed
            and r.context_docs_count == 0  # No context = knowledge gap
        ]
        # Extract topics and suggest learning content
```

---

## 5. Technical Decisions & Trade-offs

### 5.1 Why asyncio instead of Cron/Celery?

**Decision**: Use asyncio background tasks

**Pros**:
- ✅ No external dependencies (Redis, Celery worker)
- ✅ Simpler deployment (single process)
- ✅ Better integration with FastAPI
- ✅ Easier error handling

**Cons**:
- ❌ Single point of failure (if FastAPI crashes, scheduler stops)
- ❌ No distributed scheduling (can't scale horizontally easily)

**Trade-off**: Simplicity vs. scalability. For single-instance deployment, asyncio is sufficient.

### 5.2 Why ChromaDB instead of Pinecone/Weaviate?

**Decision**: Use ChromaDB with PersistentClient

**Pros**:
- ✅ Open-source, self-hosted
- ✅ Simple API
- ✅ Good for small to medium scale (< 100K vectors)
- ✅ Persistent storage built-in

**Cons**:
- ❌ No built-in re-ranking
- ❌ Limited advanced features (compared to Pinecone/Weaviate)
- ❌ Performance may degrade at very large scale (> 1M vectors)

**Trade-off**: Simplicity and cost vs. advanced features. ChromaDB is sufficient for StillMe's current scale.

### 5.3 Why No Automatic Parameter Adjustment?

**Decision**: Fixed architecture, evolving knowledge

**Philosophy**: StillMe's "evolution" is through **learning new content**, not **changing its structure**.

**Rationale**:
- Predictability: Fixed architecture ensures consistent behavior
- Transparency: Users know what to expect
- Safety: Prevents unintended behavior changes
- Simplicity: Easier to debug and maintain

**Alternative Considered**: Could add automatic parameter tuning, but decided against it for now.

---

## 📊 Key Metrics

- **Learning Frequency**: 6 cycles/day (every 4 hours)
- **Validators**: 19 total, 7 layers
- **Vector Database**: ChromaDB PersistentClient
- **Deduplication**: Multi-layer (pre-check + retrieval deduplication)
- **Self-Improvement**: Pattern analysis + learning suggestions (NOT parameter adjustment)

---

## 🔍 Key Files for Understanding

1. **Learning Scheduler**: `backend/services/learning_scheduler.py`
2. **RAG Retrieval**: `backend/vector_db/rag_retrieval.py`
3. **ChromaDB Client**: `backend/vector_db/chroma_client.py`
4. **Validation Chain**: `backend/validators/chain.py`
5. **Self-Improvement**: `backend/validators/self_improvement.py`
6. **Main Entry**: `backend/api/main.py`

---

## 💡 Recommendations for AI Assistants

When providing advice to StillMe developers:

1. **Understand the architecture**: StillMe uses asyncio, not Cron/Celery
2. **Know the scale**: Currently handles ~18K documents, ChromaDB is sufficient
3. **Respect the philosophy**: "Self-evolving" means learning content, not changing architecture
4. **Consider trade-offs**: Simplicity vs. advanced features (ChromaDB vs. Pinecone)
5. **Focus on improvements**: Re-ranking, better deduplication, etc.

---

## 📝 Notes for Gemini/Claude

This document is designed to help you understand StillMe's architecture quickly. If you need more details:

- Check `docs/framework/ARCHITECTURE.md` for detailed architecture
- Check `README.md` for project overview
- Check `backend/api/routers/chat_router.py` for main chat logic
- Check `backend/services/learning_scheduler.py` for learning mechanism

**Key Takeaway**: StillMe is a **RAG-based Learning AI** that evolves through **learning new content**, not through **changing its architecture**. The architecture is fixed, but knowledge grows continuously.

