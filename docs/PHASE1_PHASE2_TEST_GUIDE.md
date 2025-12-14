# Phase 1 & 2 Test Guide - Dashboard Testing

## Test Questions cho Phase 1 (Citation Quality)

### Test 1: High Similarity với Metadata đầy đủ
**Question**: "Giải thích quantum computing cho người mới bắt đầu"

**Expected**:
- Citation format: `[Document Title, Source, Date]` hoặc `[Document Title, Source]`
- Không phải `[general knowledge]`
- Log sẽ show: `max_similarity=0.XX` (should be > 0.8)

**Log cần check**:
```
Auto-added human-readable citation '[...]' to response (context docs: X, max_similarity=0.XX)
```

### Test 2: Medium Similarity
**Question**: "Liệt kê 5 ưu điểm của AI so với con người"

**Expected**:
- Citation format: `[Information from {Source} documents]` (e.g., `[Information from Wikipedia documents]`)
- Similarity should be 0.5-0.8
- Không phải `[general knowledge]`

**Log cần check**:
```
max_similarity=0.XX (should be between 0.5 and 0.8)
```

### Test 3: Low Similarity nhưng có Context
**Question**: "AI có ý thức không?"

**Expected**:
- Citation format: `[Background knowledge informed by {Source} context]` hoặc `[Background knowledge informed by retrieved context]`
- Similarity should be 0.3-0.5
- Acknowledge context nhưng low relevance

**Log cần check**:
```
max_similarity=0.XX (should be between 0.3 and 0.5)
```

### Test 4: No Context / Very Low Similarity
**Question**: "2+2 bằng mấy?"

**Expected**:
- Citation format: `[general knowledge] (I don't have specific sources for this information)`
- Similarity should be < 0.3 hoặc no context
- Intellectual humility: Acknowledge no specific sources

**Log cần check**:
```
max_similarity=0.XX (should be < 0.3) hoặc "No context"
```

## Test Questions cho Phase 2 (Batch Validation)

### Test 5: Multi-step Response (5+ steps)
**Question**: "Liệt kê 5 ưu điểm của AI so với con người, kèm giải thích ngắn"

**Expected**:
- Response có 5+ numbered steps
- Batch validation should succeed (không timeout)
- Log sẽ show: `P1.1.b: Batch validation completed in X.XXs for 5 steps (1 LLM call)`

**Log cần check**:
```
✅ P1.1.b: Using batch validation (1 LLM call) for 5 steps
✅ P1.1.b: Batch validation completed in X.XXs for 5 steps (1 LLM call)
```

**Nếu fail**:
```
⚠️ Batch validation failed: ..., falling back to lightweight chain
```

### Test 6: Multi-step với nhiều steps (7+)
**Question**: "Liệt kê 7 bước để học machine learning từ đầu"

**Expected**:
- Batch validation should handle 7+ steps
- Optimized prompt should prevent timeout
- Check log for completion time

**Log cần check**:
```
P1.1.b: Batch validation completed in X.XXs for 7 steps (1 LLM call)
```

## Cách Đọc Log - Key Indicators

### Phase 1 (Citation Quality) - Log Patterns:

#### ✅ SUCCESS Indicators:
```
Auto-added human-readable citation '[Document Title, Source, Date]' to response (context docs: 3, max_similarity=0.85)
```
- `max_similarity=0.XX` → Shows similarity score
- Citation format không phải `[general knowledge]` khi có context

#### ❌ FAIL Indicators:
```
Auto-added human-readable citation '[general knowledge]' to response (context docs: 3, max_similarity=0.85)
```
- Có context (3 docs) và high similarity (0.85) nhưng vẫn `[general knowledge]` → BUG!

#### Hierarchy Level Detection:
- **Level 1** (>0.8): `[Title, Source, Date]` hoặc `[Title, Source]`
- **Level 2** (0.5-0.8): `[Information from {Source} documents]`
- **Level 3** (0.3-0.5): `[Background knowledge informed by {Source} context]`
- **Level 4** (<0.3): `[general knowledge] (I don't have specific sources...)`

### Phase 2 (Batch Validation) - Log Patterns:

#### ✅ SUCCESS Indicators:
```
P1.1.b: Using batch validation (1 LLM call) for 5 steps
P1.1.b: Batch validation completed in 2.34s for 5 steps (1 LLM call)
```
- Shows batch validation used (1 LLM call)
- Completion time < 5s (timeout threshold)
- No fallback message

#### ❌ FAIL Indicators:
```
P1.1.b: Using batch validation (1 LLM call) for 5 steps
⚠️ Batch validation failed: The read operation timed out, falling back to lightweight chain
```
- Timeout sau khi optimize → Cần check prompt hoặc increase timeout

#### Fallback Indicators:
```
⚠️ Batch validation failed: ..., falling back to lightweight chain
```
- Nếu thấy message này → Batch validation failed, using lightweight chain
- Lightweight chain vẫn validate, nhưng không batch (chậm hơn)

## Checklist khi Test

### Phase 1 Checklist:
- [ ] Citation format matches similarity level
- [ ] High similarity (>0.8) → Specific citation with title/source
- [ ] Medium similarity (0.5-0.8) → Source type citation
- [ ] Low similarity (0.3-0.5) → Background knowledge citation
- [ ] No context → `[general knowledge]` with transparency message
- [ ] Log shows `max_similarity=0.XX` correctly

### Phase 2 Checklist:
- [ ] Multi-step responses trigger batch validation
- [ ] Batch validation completes without timeout
- [ ] Log shows "Batch validation completed in X.XXs"
- [ ] No fallback to lightweight chain (unless timeout)
- [ ] Validation quality maintained (all steps validated)

## Common Issues & Solutions

### Issue 1: Citation vẫn là `[general knowledge]` khi có context
**Check**:
- Log có show `max_similarity=0.XX`?
- Context docs có similarity scores?
- CitationRequired có extract similarity scores?

**Solution**: Check `backend/validators/citation.py` - `_add_citation()` method

### Issue 2: Batch validation vẫn timeout
**Check**:
- Log shows timeout after 5s?
- Prompt length trong log?
- API response time?

**Solution**: 
- Check optimized prompt length
- May need to increase timeout further
- Or implement local model (Phase 2 future work)

### Issue 3: Similarity scores không được extract
**Check**:
- Log shows `max_similarity=0.0`?
- Context docs có `similarity` field?
- RAG retrieval có return similarity?

**Solution**: Check `backend/vector_db/rag_retrieval.py` - similarity extraction

## Test Results Template

```
Test Date: YYYY-MM-DD
Test Questions: [List questions tested]

Phase 1 Results:
- Test 1 (High Similarity): ✅/❌ - Citation: [...]
- Test 2 (Medium Similarity): ✅/❌ - Citation: [...]
- Test 3 (Low Similarity): ✅/❌ - Citation: [...]
- Test 4 (No Context): ✅/❌ - Citation: [...]

Phase 2 Results:
- Test 5 (5 steps): ✅/❌ - Batch validation: Success/Timeout
- Test 6 (7+ steps): ✅/❌ - Batch validation: Success/Timeout

Issues Found:
- [List any issues]

Next Steps:
- [List follow-up actions]
```

