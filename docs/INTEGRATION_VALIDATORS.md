# StillMe Validators Integration Plan

## REFLECT: Pipeline mục tiêu

**Giả thuyết:**
- Validator chain sẽ giảm 80% halu bằng cách kiểm tra citation, evidence overlap, và ethics
- IdentityInjector đảm bảo bản sắc StillMe độc lập với model
- ToneAligner chuẩn hóa giọng điệu

**Rủi ro:**
- Validation có thể làm chậm response (latency tăng 100-200ms)
- Validator fail có thể reject valid responses (false positive)
- Ethics guard có thể quá strict

**Phương án rollback:**
- Tắt bằng `ENABLE_VALIDATORS=false` → bỏ qua toàn bộ chain
- Tắt từng validator riêng lẻ qua config
- Fallback về flow cũ nếu validator crash

## Pipeline Flow

```
┌─────────────────────────────────────────────────────────────────┐
│ 1. User Request → /api/chat/rag                                 │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 2. RAG Retrieval (backend/vector_db/rag_retrieval.py)          │
│    - retrieve_context(query)                                    │
│    - Returns: knowledge_docs, conversation_docs                │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 3. IdentityInjector (backend/identity/injector.py)              │
│    - inject_identity(user_prompt)                              │
│    - Adds STILLME_IDENTITY system prompt                        │
│    - Returns: enhanced_prompt với bản sắc StillMe              │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 4. Model Router (backend/api/main.py::generate_ai_response)    │
│    - Check ENABLE_VALIDATORS flag                               │
│    - Route to: DeepSeek / OpenAI / Gemini / Local                │
│    - Returns: raw_response                                      │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 5. ValidatorChain (backend/validators/chain.py)                 │
│    ┌─────────────────────────────────────────────────────────┐ │
│    │ 5.1 CitationRequired                                     │ │
│    │     - Check for [1], [2]... citations                    │ │
│    │     - Fail if missing                                    │ │
│    └─────────────────────────────────────────────────────────┘ │
│    ┌─────────────────────────────────────────────────────────┐ │
│    │ 5.2 EvidenceOverlap                                      │ │
│    │     - ngram_overlap(answer, ctx_docs)                    │ │
│    │     - Threshold: 0.08 (8% overlap tối thiểu)            │ │
│    │     - Fail if overlap < threshold                        │ │
│    └─────────────────────────────────────────────────────────┘ │
│    ┌─────────────────────────────────────────────────────────┐ │
│    │ 5.3 NumericUnitsBasic                                    │ │
│    │     - Detect numbers in answer                           │ │
│     │     - Warning if numbers without citation (optional)    │ │
│    └─────────────────────────────────────────────────────────┘ │
│    ┌─────────────────────────────────────────────────────────┐ │
│    │ 5.4 SchemaFormat (optional, tuỳ endpoint)                │ │
│    │     - Check required sections                            │ │
│    │     - Fail if missing sections                           │ │
│    └─────────────────────────────────────────────────────────┘ │
│    ┌─────────────────────────────────────────────────────────┐ │
│    │ 5.5 EthicsAdapter                                       │ │
│    │     - Wrap existing EthicsGuard (nếu có)                  │ │
│    │     - Fail if ethics violation                           │ │
│    └─────────────────────────────────────────────────────────┘ │
│    ┌─────────────────────────────────────────────────────────┐ │
│    │ 5.6 RetrievalCoverage (optional, future)                │ │
│    │     - Check if entities in answer exist in RAG docs       │ │
│    │     - Suggest expand RAG if missing                      │ │
│    └─────────────────────────────────────────────────────────┘ │
│    Returns: ValidationResult(passed, reasons, patched_answer)  │
└─────────────────────────────────────────────────────────────────┘
                              ↓
                    ┌──────────┴──────────┐
                    │  passed?            │
                    └──────────┬──────────┘
                    ┌──────────┴──────────┐
                    │                     │
              ┌─────▼─────┐       ┌──────▼──────┐
              │  YES      │       │  NO          │
              │           │       │              │
              │  Use      │       │  Use         │
              │  patched  │       │  patched OR  │
              │  answer   │       │  return 422  │
              └─────┬─────┘       └──────┬───────┘
                    └──────────┬──────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 6. ToneAligner (backend/tone/aligner.py)                        │
│    - align_tone(answer)                                        │
│    - Normalize tone, ensure polite ending                       │
│    - Returns: aligned_answer                                   │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 7. Metrics & Logging                                           │
│    - Record: validation_pass_rate, reasons_histogram            │
│    - Log: validation results (INFO level)                      │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 8. Return Response (ChatResponse)                             │
│    - response: aligned_answer                                  │
│    - context_used: RAG context                                │
│    - validation_metrics: (nếu ENABLE_VALIDATORS=true)          │
└─────────────────────────────────────────────────────────────────┘
```

## Điểm gắn vào FastAPI

### Service Layer Integration (Recommended)

**File:** `backend/api/main.py`

**Endpoint:** `/api/chat/rag` (line 158)

**Modification:**

```python
# Before model call (line 175-181)
if context and context["total_context_docs"] > 0:
    context_text = rag_retrieval.build_prompt_context(context)
    
    # NEW: Inject StillMe identity
    from backend.identity.injector import inject_identity
    enhanced_prompt = inject_identity(
        f"""Context: {context_text}\n\nUser Question: {request.message}"""
    )
    
    # Generate response
    raw_response = await generate_ai_response(enhanced_prompt)
    
    # NEW: Validate response
    if os.getenv("ENABLE_VALIDATORS", "false").lower() == "true":
        from backend.validators.chain import ValidatorChain
        from backend.validators.citation import CitationRequired
        from backend.validators.evidence_overlap import EvidenceOverlap
        from backend.validators.numeric import NumericUnitsBasic
        from backend.validators.ethics_adapter import EthicsAdapter
        
        # Build context docs list
        ctx_docs = [
            doc["content"] for doc in context["knowledge_docs"]
        ] + [
            doc["content"] for doc in context["conversation_docs"]
        ]
        
        # Create validator chain
        chain = ValidatorChain([
            CitationRequired(),
            EvidenceOverlap(threshold=0.08),
            NumericUnitsBasic(),
            EthicsAdapter(guard_callable=None)  # TODO: wire existing guard
        ])
        
        # Run validation
        validation_result = chain.run(raw_response, ctx_docs)
        
        if not validation_result.passed:
            # Use patched answer if available, otherwise return 422
            if validation_result.patched_answer:
                response = validation_result.patched_answer
            else:
                raise HTTPException(
                    status_code=422,
                    detail={
                        "error": "validation_failed",
                        "reasons": validation_result.reasons,
                        "original_response": raw_response[:200]  # Preview
                    }
                )
        else:
            response = validation_result.patched_answer or raw_response
    else:
        response = raw_response
    
    # NEW: Align tone
    if os.getenv("ENABLE_TONE_ALIGN", "true").lower() == "true":
        from backend.tone.aligner import align_tone
        response = align_tone(response)
```

### Rủi ro tương thích

1. **API Response Schema:**
   - **Rủi ro:** Thêm field `validation_metrics` có thể break clients
   - **Giải pháp:** Wrap trong flag `ENABLE_VALIDATORS`, chỉ thêm field khi enabled
   - **Fallback:** Nếu `ENABLE_VALIDATORS=false`, response giống hệt cũ

2. **Latency:**
   - **Rủi ro:** Validation chain tăng 100-200ms latency
   - **Giải pháp:** Cache validation results, async validation (future)
   - **Fallback:** Có thể tắt validators cho real-time endpoints

3. **False Positives:**
   - **Rủi ro:** Validator reject valid responses (ví dụ: citation format khác)
   - **Giải pháp:** `patched_answer` để auto-fix, hoặc return 422 với details
   - **Fallback:** Client có thể retry với `ENABLE_VALIDATORS=false`

### Fallback Strategy

```python
# Wrapper function với fallback
async def generate_validated_response(
    prompt: str,
    ctx_docs: list[str],
    enable_validators: bool = True
) -> str:
    """Generate response with optional validation"""
    try:
        raw = await generate_ai_response(prompt)
        
        if enable_validators and os.getenv("ENABLE_VALIDATORS", "false").lower() == "true":
            # Run validation
            result = validator_chain.run(raw, ctx_docs)
            return result.patched_answer or raw
        else:
            return raw
    except Exception as e:
        logger.error(f"Validation error: {e}, falling back to raw response")
        return raw  # Fallback to unvalidated response
```

## Environment Variables

```bash
# Enable/disable validators globally
ENABLE_VALIDATORS=true|false          # Default: false (safe rollout)

# Enable/disable tone alignment
ENABLE_TONE_ALIGN=true|false          # Default: true

# Tone style (future)
STILLME_TONE_STYLE=neutral|friendly|scholarly  # Default: neutral

# Validator-specific thresholds
VALIDATOR_EVIDENCE_THRESHOLD=0.08      # Default: 0.08 (8% overlap)
VALIDATOR_CITATION_REQUIRED=true      # Default: true
```

## Validation

✅ Pipeline flow đã được vẽ chi tiết
✅ Điểm gắn vào FastAPI đã được xác định (service layer)
✅ Rủi ro và fallback strategy đã được nêu rõ
✅ Environment variables đã được định nghĩa
✅ Có thể tiến hành B3 (Tạo module)

## Links

- Codebase Map: [docs/CODEBASE_MAP_VALIDATORS.md](./CODEBASE_MAP_VALIDATORS.md)
- FastAPI endpoint: `backend/api/main.py:158` (`/api/chat/rag`)
- RAG retrieval: `backend/vector_db/rag_retrieval.py:27` (`retrieve_context()`)
- LLM router: `backend/api/main.py:810` (`generate_ai_response()`)

