# StillMe Architecture - Tier 3.5 Optimization Plan

## 📋 Current Architecture Summary

### 1. RAG Retrieval (`backend/vector_db/rag_retrieval.py`)

**Current Implementation:**
- **Embedding Model**: all-MiniLM-L6-v2 (384 dimensions)
- **Search Strategy**: 
  - Parallel search for knowledge + conversation (ThreadPoolExecutor)
  - Knowledge search: `knowledge_limit` (default: 3)
  - Conversation search: `conversation_limit` (default: 1)
- **No Score Threshold**: All retrieved documents are used regardless of similarity score
- **No MMR/Diversity**: Documents may be redundant
- **No Pre-filtering**: All results from ChromaDB are included

**Key Methods:**
- `retrieve_context()`: Main retrieval method
- `_search_knowledge()`: Knowledge document search
- `_search_conversations()`: Conversation history search

**Current Flow:**
1. Generate query embedding (384 dims)
2. Parallel search: knowledge + conversation
3. Merge results (avoid duplicates by ID)
4. Return top `knowledge_limit` + `conversation_limit`

**Issues:**
- ❌ No similarity score threshold → low-quality context included
- ❌ No diversity filtering → redundant documents
- ❌ Fixed limits → not adaptive to query complexity

---

### 2. Context Building (`backend/api/routers/chat_router.py`)

**Current Implementation:**
- **Conversation History**: 
  - Hard-coded: Last 5 messages
  - Max tokens: 1000 (total)
  - Per message: Max 500 tokens
  - Function: `_format_conversation_history()`
- **Token Estimation**: ~4 chars per token (simple heuristic)
- **Truncation**: Simple character-based truncation

**Current Flow:**
1. Take last 5 messages from history
2. Allocate tokens per message (distribute remaining)
3. Truncate each message if needed
4. Format as "User: ... / Assistant: ..."

**Issues:**
- ❌ Fixed 5 messages → not adaptive to query type
- ❌ No prioritization → recent messages may not be most relevant
- ❌ Simple truncation → may cut important context

---

### 3. Validation Chain (`backend/validators/chain.py`)

**Current Validators (8-9 total):**
1. `LanguageValidator` - Must run first
2. `CitationRequired` - Must run before CitationRelevance
3. `CitationRelevance` - Checks keyword overlap (min: 0.1 = 10%)
4. `EvidenceOverlap` - Checks answer vs context overlap
5. `ConfidenceValidator` - Checks confidence score
6. `IdentityCheckValidator` - Checks StillMe identity violations
7. `EgoNeutralityValidator` - Checks anthropomorphic language
8. `EthicsAdapter` - Ethics filtering
9. `NumericUnitsBasic` - Numeric validation

**Current Behavior:**
- **CitationRelevance**: Only logs warning if overlap < 10%, doesn't remove citation
- **ConfidenceValidator**: Checks confidence but doesn't force "I don't know" template
- **Parallel Execution**: Some validators run in parallel (CitationRelevance, EvidenceOverlap, etc.)

**Issues:**
- ❌ CitationRelevance only warns → irrelevant citations remain
- ❌ ConfidenceValidator doesn't force uncertainty when context is weak
- ❌ No action on low-quality context → LLM may still hallucinate

---

### 4. Metrics & Logging

**Current Metrics:**
- `RAG_Retrieval_Latency`: Time from ChromaDB query to result
- `LLM_Inference_Latency`: Time from API call to response
- `Total_Response_Latency`: End-to-end latency
- `Timing breakdown`: Detailed timing per component

**Missing Metrics:**
- ❌ Average similarity score of retrieved context
- ❌ Number of documents filtered out (if any)
- ❌ Context quality score

---

## 🎯 Tier 3.5 Optimization Plan

### Goal: Improve RAG quality & reduce hallucination WITHOUT increasing cost

**Constraints:**
- ✅ NO additional LLM calls
- ✅ NO paid external APIs
- ✅ NO heavy compute (cross-encoder re-ranker)
- ✅ Latency: Keep RAG retrieval ~0.3-0.8s, Validation ~0.1-0.2s

---

## 📝 Implementation Steps

### Step 1: RAG Retrieval Optimization

**1.1. Add Similarity Score Threshold**
- **File**: `backend/vector_db/rag_retrieval.py`
- **Change**: Filter documents with similarity score < threshold (e.g., 0.3-0.4)
- **Logic**: 
  - If all scores < threshold → return empty context + flag "no_reliable_context"
  - If some scores < threshold → filter them out
- **Benefit**: Only high-quality context → less hallucination

**1.2. Add MMR (Max Marginal Relevance) for Diversity**
- **File**: `backend/vector_db/rag_retrieval.py`
- **Change**: After getting top_k (e.g., 20), apply MMR to select diverse subset
- **Logic**:
  - Start with highest-scoring document
  - For each next document: score = λ * similarity - (1-λ) * max_similarity_to_selected
  - λ = 0.7 (balance relevance vs diversity)
- **Benefit**: Less redundant context → more informative

**1.3. Adaptive Knowledge Limit**
- **File**: `backend/vector_db/rag_retrieval.py`
- **Change**: Adjust `knowledge_limit` based on query complexity
- **Logic**:
  - Short query (< 20 words) → knowledge_limit = 2
  - Medium query (20-50 words) → knowledge_limit = 3
  - Long query (> 50 words) → knowledge_limit = 5
- **Benefit**: Better context allocation

---

### Step 2: Dynamic Conversation Context Window

**2.1. Adaptive Message Window**
- **File**: `backend/api/routers/chat_router.py` (function: `_format_conversation_history`)
- **Change**: Replace hard-coded 5 messages with dynamic window
- **Logic**:
  - If query is follow-up (contains "đó", "nó", "vậy", "như vậy") → include 3-5 recent messages
  - If query is new topic → include 0-2 recent messages (just for context)
  - If query is long/complex → prioritize RAG knowledge over conversation
- **Benefit**: Better context allocation, less token waste

**2.2. Semantic Relevance for Conversation History**
- **File**: `backend/api/routers/chat_router.py`
- **Change**: Use embedding similarity to select most relevant conversation messages
- **Logic**:
  - Embed query + all recent messages (last 10)
  - Select top 3-5 by similarity score
  - Only include if similarity > threshold (e.g., 0.4)
- **Benefit**: Only relevant conversation context → less noise

---

### Step 3: Validation Chain Fine-tuning

**3.1. CitationRelevance Action**
- **File**: `backend/validators/citation_relevance.py`
- **Change**: Remove citation if overlap < threshold (instead of just warning)
- **Logic**:
  - If overlap < 10% → remove citation from answer
  - Add note: "Some citations were removed due to low relevance"
- **Benefit**: Only relevant citations → more accurate answers

**3.2. ConfidenceValidator Enhancement**
- **File**: `backend/validators/confidence.py`
- **Change**: Force "I don't know" template when context is weak
- **Logic**:
  - If `context_docs_count == 0` OR `avg_similarity_score < 0.3`:
    - Force template: "I don't have sufficient information to answer this accurately"
    - Don't let LLM guess
- **Benefit**: Less hallucination when context is poor

**3.3. Context Quality Check**
- **File**: `backend/validators/chain.py` (new validator or enhance existing)
- **Change**: Add context quality check before LLM call
- **Logic**:
  - Calculate average similarity score of retrieved context
  - If avg < 0.3 → inject instruction: "The retrieved context has low relevance. You MUST acknowledge uncertainty."
- **Benefit**: LLM knows when context is weak → more honest answers

---

### Step 4: Metrics & Logging Enhancement

**4.1. Add Context Quality Metrics**
- **File**: `backend/vector_db/rag_retrieval.py`
- **Change**: Log average similarity score, number of filtered documents
- **Metrics**:
  - `avg_similarity_score`: Average similarity of retrieved context
  - `filtered_docs_count`: Number of documents filtered by threshold
  - `context_quality`: "high" (>0.6), "medium" (0.4-0.6), "low" (<0.4)

**4.2. Add Validation Metrics**
- **File**: `backend/validators/chain.py`
- **Change**: Log validation decisions (citations removed, confidence forced, etc.)
- **Metrics**:
  - `citations_removed`: Number of citations removed by CitationRelevance
  - `confidence_forced`: Whether ConfidenceValidator forced uncertainty
  - `context_quality_warning`: Whether context quality was flagged

---

## 🚀 Implementation Priority

**Phase 1 (High Impact, Low Risk):**
1. ✅ Add similarity score threshold (Step 1.1)
2. ✅ CitationRelevance action (Step 3.1)
3. ✅ ConfidenceValidator enhancement (Step 3.2)

**Phase 2 (Medium Impact, Medium Risk):**
4. ✅ MMR for diversity (Step 1.2)
5. ✅ Adaptive conversation window (Step 2.1)

**Phase 3 (Nice to Have):**
6. ✅ Semantic relevance for conversation (Step 2.2)
7. ✅ Adaptive knowledge limit (Step 1.3)
8. ✅ Metrics enhancement (Step 4)

---

## 📊 Expected Results

**Before (Current):**
- RAG retrieval: ~0.3-0.8s
- Validation: ~0.1-0.2s
- Context quality: Variable (may include low-relevance docs)
- Hallucination: Moderate (LLM may guess when context is weak)

**After (Tier 3.5):**
- RAG retrieval: ~0.3-0.8s (same, MMR adds ~0.05s)
- Validation: ~0.1-0.2s (same)
- Context quality: High (only relevant, diverse docs)
- Hallucination: Reduced (LLM forced to acknowledge uncertainty when context is weak)

**Cost Impact:**
- ✅ Zero additional cost (no new LLM calls, no paid APIs)
- ✅ Token usage: Same or slightly lower (better filtering)

---

## 🔍 Testing Strategy

**Test Cases:**
1. **High-quality context query**: Should retrieve relevant docs, good citations
2. **Low-quality context query**: Should acknowledge uncertainty, no hallucination
3. **Follow-up query**: Should use relevant conversation history
4. **New topic query**: Should prioritize RAG knowledge over conversation
5. **Redundant context**: Should use MMR to diversify

**Success Criteria:**
- ✅ Context quality metrics show improvement
- ✅ Hallucination rate decreases (manual evaluation)
- ✅ Latency stays within bounds
- ✅ No cost increase

---

## 📝 Notes

- All optimizations use existing infrastructure (embedding model, ChromaDB)
- No breaking changes to API or data structures
- Backward compatible (can be enabled/disabled via env vars)
- Incremental implementation (each step can be tested independently)

