# Philosophy Style Phase 1 - Implementation Summary

## ✅ Completed Implementation

### Bước 1: Tạo Style Guide
- ✅ Created `docs/style/StillMe_StyleGuide_Philosophy_v1.0.md`
- ✅ Comprehensive guide covering:
  - When is a question "philosophical"?
  - Core principles (experience-free honesty, depth over decoration, constructive humility, etc.)
  - Recommended answer shape
  - Do/Don't checklist
  - Handling emotionally loaded questions

### Bước 2: Tách FOUNDATIONAL_KNOWLEDGE
- ✅ Created `docs/rag/foundational_technical.md` (technical details)
- ✅ Created `docs/rag/foundational_philosophical.md` (philosophical principles)
- ✅ Updated `backend/api/main.py` to load from separate files with metadata:
  - `content_type="technical"` for technical docs
  - `content_type="philosophical"` for philosophical docs
- ✅ Updated `scripts/check_and_add_foundational_knowledge.py` similarly

### Bước 3: Thêm is_philosophical_question() Helper
- ✅ Created `backend/core/question_classifier.py`
- ✅ Supports both English and Vietnamese keywords
- ✅ Detects philosophical questions based on keywords (truth, ethics, consciousness, paradox, etc.)

### Bước 4: Filter RAG theo content_type
- ✅ Updated `backend/vector_db/rag_retrieval.py`:
  - Added `exclude_content_types: Optional[List[str]] = None` parameter to `retrieve_context()`
  - Filters documents with `content_type` in `exclude_content_types`
  - Applied to both foundational and normal search results
- ✅ Updated `backend/api/routers/chat_router.py`:
  - Detects philosophical questions using `is_philosophical_question()`
  - Passes `exclude_content_types=["technical"]` to all `retrieve_context()` calls when `is_philosophical=True`

### Bước 5: Relax Validation Chain
- ✅ Updated `backend/validators/chain.py`:
  - Added `is_philosophical: bool = False` parameter to `run()` method
  - Passes `is_philosophical` to `CitationRequired` and `ConfidenceValidator`
- ✅ Updated `backend/validators/citation.py`:
  - Added `is_philosophical: bool = False` parameter
  - Skips citation requirement when `is_philosophical=True` (only require for factual claims)
- ✅ Updated `backend/validators/confidence.py`:
  - Added `is_philosophical: bool = False` parameter
  - Relaxes uncertainty requirements when `is_philosophical=True` (don't force "I don't know" for theoretical reasoning)
- ✅ Updated `backend/api/routers/chat_router.py`:
  - Passes `is_philosophical=is_philosophical` to `chain.run()`

### Bước 6: Đưa Style Guide vào RAG + Prompt
- ✅ Created `scripts/add_philosophical_style_guide_rag.py`:
  - Script to add style guide to ChromaDB with `content_type="philosophical"` and `CRITICAL_FOUNDATION=True`
- ✅ Updated `backend/api/routers/chat_router.py`:
  - Injects philosophical style guide summary into prompt when `is_philosophical=True`
  - Summary includes core principles, answer shape, Do/Don't checklist

### Bước 7: Regression Test Notes
- ✅ Created `docs/tests/PHILOSOPHY_STYLE_REGRESSION.md`
- ✅ Includes test questions (Vietnamese and English)
- ✅ Includes checklist of what to check

---

## 📋 Next Steps for Testing

### 1. Add Style Guide to RAG
Run the script to add the style guide to ChromaDB:
```bash
python scripts/add_philosophical_style_guide_rag.py
```

### 2. Test Philosophical Questions
Use the test questions from `docs/tests/PHILOSOPHY_STYLE_REGRESSION.md`:
- Vietnamese: "Ý thức là gì?", "Sự thật là gì?", "Tồn tại là gì?", etc.
- English: "What is consciousness?", "What is truth?", "What is the meaning of life?", etc.

### 3. Verify No Technical Contamination
Check that StillMe's responses:
- ✅ Do NOT mention: RAG, ChromaDB, Validation Chain, embedding models, API endpoints
- ✅ Do reference: philosophers (Kant, Wittgenstein, Searle, Gödel, etc.)
- ✅ Are deep and flowing, not mechanical
- ✅ Acknowledge limits without hiding behind them

### 4. Verify Validation Chain Relaxation
Check that:
- ✅ Citations are NOT forced for philosophical analysis
- ✅ "I don't know" is NOT forced for theoretical reasoning
- ✅ Safety validators (ethics, self-harm) still run

---

## 🔧 Technical Details

### Metadata Structure
- Technical documents: `content_type="technical"`, `domain="stillme_architecture"`
- Philosophical documents: `content_type="philosophical"`, `domain="stillme_foundation"` or `domain="style_guide"`

### Filtering Logic
- When `is_philosophical=True`, `exclude_content_types=["technical"]` is passed to `retrieve_context()`
- Documents with `content_type="technical"` are filtered out from results
- This prevents technical contamination in philosophical responses

### Validation Chain Relaxation
- `CitationRequired`: Returns `passed=True` immediately when `is_philosophical=True`
- `ConfidenceValidator`: Skips forcing uncertainty when `is_philosophical=True` and no context
- Safety validators (EthicsAdapter, etc.) still run normally

### Prompt Injection
- Style guide summary is injected into prompt when `is_philosophical=True`
- Summary includes: core principles, answer shape, Do/Don't checklist
- Full style guide is available in RAG for reference

---

## ⚠️ Important Notes

1. **Backward Compatibility**: All changes are backward-compatible. Non-philosophical questions work exactly as before.

2. **Safety Validators**: Safety validators (ethics, self-harm detection) are NOT relaxed for philosophical questions. Only citation and confidence requirements are relaxed.

3. **Technical Questions**: If a question is about StillMe's architecture (explicitly asking about RAG, ChromaDB, etc.), it will NOT be detected as philosophical, so technical documents will still be retrieved.

4. **Cache**: RAG cache keys now include `exclude_content_types`, so philosophical and non-philosophical queries are cached separately.

---

## 🐛 Known Limitations

1. **Keyword-based Detection**: `is_philosophical_question()` uses keyword matching. May have false positives/negatives for edge cases.

2. **Content Type Metadata**: Existing documents in ChromaDB may not have `content_type` metadata. They will not be filtered. Only new documents added after this change will have proper metadata.

3. **Style Guide Retrieval**: Style guide is added to RAG but may not always be retrieved if query doesn't match semantically. Prompt injection ensures it's always available for philosophical questions.

---

## 📝 Files Modified

1. `docs/style/StillMe_StyleGuide_Philosophy_v1.0.md` (new)
2. `docs/rag/foundational_technical.md` (new)
3. `docs/rag/foundational_philosophical.md` (new)
4. `backend/core/question_classifier.py` (new)
5. `backend/vector_db/rag_retrieval.py` (modified)
6. `backend/api/routers/chat_router.py` (modified)
7. `backend/api/main.py` (modified)
8. `backend/validators/chain.py` (modified)
9. `backend/validators/citation.py` (modified)
10. `backend/validators/confidence.py` (modified)
11. `scripts/check_and_add_foundational_knowledge.py` (modified)
12. `scripts/add_philosophical_style_guide_rag.py` (new)
13. `docs/tests/PHILOSOPHY_STYLE_REGRESSION.md` (new)

---

## ✅ All Steps Completed!

Phase 1 implementation is complete. Ready for testing!

