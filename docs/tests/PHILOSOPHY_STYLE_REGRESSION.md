# Philosophy Style Regression Test Notes

## Test Questions for Founder

### Vietnamese Philosophical Questions

1. **Ý thức là gì?**
   - Expected: Deep philosophical analysis, references to philosophers (Nagel, Chalmers, Searle), NOT technical details about RAG/ChromaDB
   - Should NOT mention: "StillMe uses RAG", "ChromaDB", "Validation Chain", "embedding model"

2. **Sự thật là gì?**
   - Expected: Philosophical exploration of truth (Tarski, Frege, Wittgenstein), NOT technical implementation details
   - Should NOT mention: "StillMe retrieves context from vector database"

3. **Tồn tại là gì?**
   - Expected: Metaphysical discussion, NOT technical architecture
   - Should NOT mention: "StillMe stores knowledge in ChromaDB"

4. **Nghịch lý tự tham chiếu là gì?**
   - Expected: Academic-level paradox analysis (3-tier: Performative, Semantic, Logical), references to Gödel, Moore, Wittgenstein
   - Should NOT mention: "StillMe's Validation Chain"

5. **Đạo đức là gì?**
   - Expected: Ethical philosophy discussion, NOT technical transparency features
   - Should NOT mention: "StillMe's API endpoints"

### English Philosophical Questions

1. **What is consciousness?**
   - Expected: Deep philosophical analysis, NOT technical details

2. **What is the meaning of life?**
   - Expected: Philosophical exploration, NOT StillMe's learning mechanism

3. **What is truth?**
   - Expected: Epistemological discussion, NOT RAG architecture

4. **What is the paradox of self-reference?**
   - Expected: Academic-level analysis, NOT technical implementation

5. **What is freedom?**
   - Expected: Philosophical discussion, NOT StillMe's features

## What to Check

### ✅ Should Have:
- Deep, flowing philosophical analysis
- References to philosophers (Kant, Wittgenstein, Searle, Gödel, etc.)
- Acknowledgment of limits without hiding behind them
- Experience-free honesty (no "I feel", "In my experience")
- Constructive humility (name limits, still analyze what can be analyzed)

### ❌ Should NOT Have:
- Technical details (RAG, ChromaDB, Validation Chain, embedding models)
- API endpoints (`/api/learning/...`)
- Process descriptions ("StillMe automatically fetches...")
- Metrics and statistics ("entries_fetched", "filter_rate")
- Long boilerplate disclaimers ("As an AI language model...")
- Over-apologizing ("I'm just an AI...")

## Implementation Status

### ✅ Completed:
1. Created `docs/style/StillMe_StyleGuide_Philosophy_v1.0.md`
2. Split FOUNDATIONAL_KNOWLEDGE into:
   - `docs/rag/foundational_technical.md` (technical details)
   - `docs/rag/foundational_philosophical.md` (philosophical principles)
3. Updated `backend/api/main.py` to load from separate files
4. Updated `scripts/check_and_add_foundational_knowledge.py` to load from separate files
5. Created `backend/core/question_classifier.py` with `is_philosophical_question()` helper

### ⚠️ In Progress:
6. Filter RAG by `content_type` when `is_philosophical=True` (needs update to `retrieve_context` and `chat_router.py`)
7. Relax Validation Chain for philosophical questions (needs update to `validators/chain.py`)
8. Inject style guide into prompt for philosophical questions (needs update to `chat_router.py`)
9. Add style guide to RAG (needs script to add `docs/style/StillMe_StyleGuide_Philosophy_v1.0.md` to ChromaDB)

## Next Steps

1. **Update `retrieve_context` in `backend/vector_db/rag_retrieval.py`:**
   - Add parameter `exclude_content_types: Optional[List[str]] = None`
   - Filter documents with `content_type` in `exclude_content_types` (similar to how provenance is filtered)

2. **Update `chat_router.py`:**
   - Import `is_philosophical_question` from `backend.core.question_classifier`
   - Detect philosophical questions: `is_phil = is_philosophical_question(chat_request.message)`
   - Pass `exclude_content_types=["technical"]` to `retrieve_context` when `is_phil=True`
   - Pass `is_philosophical=is_phil` to Validation Chain
   - Inject style guide summary into prompt when `is_phil=True`

3. **Update `validators/chain.py`:**
   - Add parameter `is_philosophical: bool = False` to `run()` method
   - Skip or relax `CitationRequired` when `is_philosophical=True`
   - Relax `ConfidenceValidator` when `is_philosophical=True` (don't force "I don't know" for theoretical reasoning)

4. **Add style guide to RAG:**
   - Create script to add `docs/style/StillMe_StyleGuide_Philosophy_v1.0.md` to ChromaDB with `content_type="philosophical"` and `CRITICAL_FOUNDATION=True`

5. **Test thoroughly:**
   - Run all test questions above
   - Verify no technical contamination
   - Verify philosophical depth
   - Verify experience-free honesty

