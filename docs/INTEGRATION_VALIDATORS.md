StillMe Validators Integration Plan
REFLECT: Target Pipeline

Hypothesis:

The Validator Chain will reduce hallucination by ~80% through citation checking, evidence overlap, and ethical compliance.

The IdentityInjector ensures StillMe’s identity remains consistent across all models.

The ToneAligner normalizes tone and ensures coherent communication style.

Risks:

Validation may increase response latency (by 100–200 ms).

A failed validator could reject valid responses (false positives).

The EthicsGuard may be overly strict depending on content.

Rollback Plan:

Disable the entire chain via ENABLE_VALIDATORS=false.

Disable individual validators through configuration flags.

Fallback to the legacy (pre-validator) flow if a validator crashes.

Pipeline Flow
┌─────────────────────────────────────────────────────────────────┐
│ 1. User Request → /api/chat/rag                                 │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 2. RAG Retrieval (backend/vector_db/rag_retrieval.py)           │
│    - retrieve_context(query)                                    │
│    - Returns: knowledge_docs, conversation_docs                 │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 3. IdentityInjector (backend/identity/injector.py)              │
│    - inject_identity(user_prompt)                               │
│    - Adds STILLME_IDENTITY system prompt                        │
│    - Returns: enhanced_prompt with StillMe identity             │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 4. Model Router (backend/api/main.py::generate_ai_response)     │
│    - Check ENABLE_VALIDATORS flag                               │
│    - Route to: DeepSeek / OpenAI / Gemini / Local               │
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
│    │     - Threshold: 0.08 (8% minimum overlap)               │ │
│    │     - Fail if overlap < threshold                        │ │
│    └─────────────────────────────────────────────────────────┘ │
│    ┌─────────────────────────────────────────────────────────┐ │
│    │ 5.3 NumericUnitsBasic                                    │ │
│    │     - Detect numeric values in the answer                │ │
│    │     - Warn if numbers lack citation (optional)           │ │
│    └─────────────────────────────────────────────────────────┘ │
│    ┌─────────────────────────────────────────────────────────┐ │
│    │ 5.4 SchemaFormat (optional, endpoint-specific)           │ │
│    │     - Check required sections                            │ │
│    │     - Fail if sections are missing                       │ │
│    └─────────────────────────────────────────────────────────┘ │
│    ┌─────────────────────────────────────────────────────────┐ │
│    │ 5.5 EthicsAdapter                                        │ │
│    │     - Wraps existing EthicsGuard (if available)          │ │
│    │     - Fail if ethics violation detected                  │ │
│    └─────────────────────────────────────────────────────────┘ │
│    ┌─────────────────────────────────────────────────────────┐ │
│    │ 5.6 RetrievalCoverage (optional, future)                 │ │
│    │     - Check if entities in the answer exist in RAG docs  │ │
│    │     - Suggest expanding RAG if missing                   │ │
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
              │  Use      │       │  Use patched │
              │  patched  │       │  answer OR   │
              │  answer   │       │  return 422  │
              └─────┬─────┘       └──────┬───────┘
                    └──────────┬──────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 6. ToneAligner (backend/tone/aligner.py)                        │
│    - align_tone(answer)                                         │
│    - Normalize tone; ensure polite or neutral closure           │
│    - Returns: aligned_answer                                   │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 7. Metrics & Logging                                            │
│    - Record: validation_pass_rate, reasons_histogram            │
│    - Log: validation results (INFO level)                       │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 8. Return Response (ChatResponse)                               │
│    - response: aligned_answer                                   │
│    - context_used: RAG context                                  │
│    - validation_metrics: (if ENABLE_VALIDATORS=true)            │
└─────────────────────────────────────────────────────────────────┘

FastAPI Integration Points
Service Layer Integration (Recommended)

File: backend/api/main.py
Endpoint: /api/chat/rag (line 158)

Modification Example:

# Before model call (line 175–181)
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
            if validation_result.patched_answer:
                response = validation_result.patched_answer
            else:
                raise HTTPException(
                    status_code=422,
                    detail={
                        "error": "validation_failed",
                        "reasons": validation_result.reasons,
                        "original_response": raw_response[:200]
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

Compatibility Risks

1.API Response Schema
    - Risk: Adding validation_metrics might break existing clients.
    - Solution: Wrap under ENABLE_VALIDATORS; only include when enabled.
    - Fallback: If disabled, response remains identical to old schema.

2.Latency
    - Risk: Validation chain adds 100–200 ms latency.
    - Solution: Cache results or use asynchronous validation (future).
    - Fallback: Disable validators for real-time endpoints.

3.False Positives
    - Risk: Validators may reject valid answers (e.g., non-standard citation formats).
    - Solution: Use patched_answer auto-fix or return 422 with details.
    - Fallback: Client may retry with ENABLE_VALIDATORS=false.

Fallback Strategy
async def generate_validated_response(
    prompt: str,
    ctx_docs: list[str],
    enable_validators: bool = True
) -> str:
    """Generate response with optional validation."""
    try:
        raw = await generate_ai_response(prompt)
        
        if enable_validators and os.getenv("ENABLE_VALIDATORS", "false").lower() == "true":
            result = validator_chain.run(raw, ctx_docs)
            return result.patched_answer or raw
        else:
            return raw
    except Exception as e:
        logger.error(f"Validation error: {e}, falling back to raw response")
        return raw

Environment Variables
# Enable/disable validators globally
ENABLE_VALIDATORS=true|false          # Default: false (safe rollout)

# Enable/disable tone alignment
ENABLE_TONE_ALIGN=true|false          # Default: true

# Tone style (future option)
STILLME_TONE_STYLE=neutral|friendly|scholarly  # Default: neutral

# Validator thresholds
VALIDATOR_EVIDENCE_THRESHOLD=0.08      # Default: 0.08 (8% overlap)
VALIDATOR_CITATION_REQUIRED=true       # Default: true

Validation Summary

✅ Pipeline flow fully mapped
✅ FastAPI integration point identified (service layer)
✅ Risks and fallback strategy clearly defined
✅ Environment variables configured
✅ Ready for Phase 3: Module Implementation

Reference Links
    Codebase Map: docs/CODEBASE_MAP_VALIDATORS.md
    FastAPI Endpoint: backend/api/main.py:158 (/api/chat/rag)
    RAG Retrieval: backend/vector_db/rag_retrieval.py:27 (retrieve_context())
    LLM Router: backend/api/main.py:810 (generate_ai_response())