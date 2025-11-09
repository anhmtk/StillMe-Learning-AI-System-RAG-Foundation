# Confidence Validation & Fallback Handler

## Overview

StillMe implements a comprehensive confidence validation system that prevents hallucinations by:
1. **Detecting when AI should express uncertainty** (ConfidenceValidator)
2. **Providing safe fallback answers** when validation fails (FallbackHandler)
3. **Calculating confidence scores** based on context quality and validation results
4. **Tracking metrics** for A/B testing and hallucination reduction measurement

## Components

### 1. ConfidenceValidator

**Location:** `backend/validators/confidence.py`

**Purpose:** Detects when AI should express uncertainty, especially when no context is available.

**Key Features:**
- Requires uncertainty expressions when no context is found
- Detects overconfidence patterns
- Supports multiple languages (English, Vietnamese, Chinese)
- Case-insensitive pattern matching

**Configuration:**
```python
ConfidenceValidator(require_uncertainty_when_no_context=True)
```

**Validation Rules:**
- ✅ **PASS**: AI expresses uncertainty when no context (`"I don't know"`, `"Không biết"`, etc.)
- ❌ **FAIL**: AI is overconfident without context (`"Definitely X"`, `"Chắc chắn 100%"`, etc.)
- ✅ **PASS**: AI is confident when context exists (uncertainty optional)

**Uncertainty Patterns Detected:**
- English: "I don't know", "I'm not certain", "I cannot answer", etc.
- Vietnamese: "Không biết", "Không có đủ thông tin", "Không thể trả lời", etc.
- Chinese: "不知道", "不确定", etc.

### 2. FallbackHandler

**Location:** `backend/validators/fallback_handler.py`

**Purpose:** Provides safe, informative fallback answers when validation fails critically.

**Key Features:**
- Multi-language support (English, Vietnamese, Chinese)
- Context-aware fallback generation
- Prevents hallucinated content from reaching users
- Explains StillMe's learning mechanism

**Usage:**
```python
fallback_handler = FallbackHandler()
safe_answer = fallback_handler.get_fallback_answer(
    original_answer=hallucinated_response,
    validation_result=failed_validation,
    ctx_docs=[],
    user_question="User's question",
    detected_lang="en"
)
```

**Fallback Triggers:**
- `missing_uncertainty_no_context` - AI didn't express uncertainty when no context
- `missing_citation` + no context - Missing citation when no context available
- `low_overlap` + no context - Low overlap when no context available

**Fallback Content:**
- Acknowledges lack of information
- Explains StillMe's continuous learning (every 4 hours)
- Offers alternatives (reformulate, wait, related topics)
- Does NOT contain original hallucinated content

### 3. Confidence Score Calculation

**Location:** `backend/api/routers/chat_router.py::_calculate_confidence_score()`

**Purpose:** Calculates AI confidence in the answer based on multiple factors.

**Calculation Logic:**
```python
Base Confidence:
- 0 context docs: 0.2 (very low)
- 1 context doc: 0.5 (medium)
- 2+ context docs: 0.8 (high)

Adjustments:
- Validation passed: +0.1 (max 1.0)
- Missing uncertainty (no context): 0.1 (very low)
- Missing citation (with context): -0.2
- Low overlap: -0.15
- Other failures: -0.1
```

**Score Ranges:**
- **0.0 - 0.3**: Very uncertain (red indicator)
- **0.4 - 0.6**: Medium confidence (orange indicator)
- **0.7 - 1.0**: High confidence (green indicator)

### 4. Integration with ValidatorChain

**Location:** `backend/api/routers/chat_router.py`

**Integration:**
```python
chain = ValidatorChain([
    CitationRequired(),
    EvidenceOverlap(threshold=0.01),
    NumericUnitsBasic(),
    ConfidenceValidator(require_uncertainty_when_no_context=True),  # NEW
    EthicsAdapter(guard_callable=None)
])
```

**Flow:**
1. ValidatorChain runs all validators sequentially
2. If ConfidenceValidator fails → triggers FallbackHandler
3. FallbackHandler generates safe answer
4. Confidence score calculated based on results
5. Metrics recorded for A/B testing

### 5. Metrics Tracking

**Location:** `backend/validators/metrics.py`

**New Metrics:**
- `avg_confidence_score`: Average confidence across all responses
- `fallback_usage_count`: Number of times fallback was used
- `fallback_usage_rate`: Percentage of responses using fallback
- `hallucination_prevented_count`: Number of hallucinations prevented
- `hallucination_reduction_rate`: Percentage of prevented hallucinations
- `uncertainty_expressed_count`: Number of times AI expressed uncertainty
- `uncertainty_expression_rate`: Percentage of uncertainty expressions

**A/B Testing:**
These metrics enable measurement of:
- Hallucination reduction effectiveness
- Confidence score distribution
- Fallback usage patterns
- Uncertainty expression patterns

## API Response Changes

### ChatResponse Model

**New Fields:**
```python
class ChatResponse(BaseModel):
    response: str
    confidence_score: Optional[float]  # 0.0 - 1.0
    validation_info: Optional[Dict[str, Any]]  # Validation details
    learning_suggestions: Optional[List[str]]  # Knowledge gap suggestions
    # ... existing fields
```

**validation_info Structure:**
```python
{
    "passed": bool,
    "reasons": List[str],
    "used_fallback": bool,
    "confidence_score": float,
    "context_docs_count": int
}
```

## Dashboard Display

**Location:** `dashboard.py`

**Features:**
- Expandable "Response Metadata" section for each assistant message
- Color-coded confidence score (🟢 green / 🟡 orange / 🔴 red)
- Validation status display
- Fallback usage indicator
- Learning suggestions display

**UI Elements:**
- Confidence Score: Visual indicator with percentage
- Validation Status: Pass/Fail with reasons
- Fallback Indicator: Shows when safe fallback was used
- Learning Suggestions: Topics to learn based on knowledge gaps

## Testing

**Test Files:**
- `tests/test_confidence_validator.py` - ConfidenceValidator tests
- `tests/test_fallback_handler.py` - FallbackHandler tests
- `tests/test_confidence_integration.py` - Integration tests

**Test Philosophy:**
- **Strict and honest** - No cheating with type ignores or comments
- **Edge case coverage** - Empty strings, special characters, long inputs
- **Multi-language support** - English, Vietnamese, Chinese
- **Integration testing** - Full ValidatorChain integration

## Configuration

**Environment Variables:**
```bash
ENABLE_VALIDATORS=true  # Enable validator chain (includes ConfidenceValidator)
VALIDATOR_EVIDENCE_THRESHOLD=0.01  # Evidence overlap threshold
```

**Code Configuration:**
```python
# In chat_router.py
ConfidenceValidator(require_uncertainty_when_no_context=True)
```

## Best Practices

1. **Always enable validators in production** - `ENABLE_VALIDATORS=true`
2. **Monitor metrics** - Track hallucination reduction rate
3. **Review fallback usage** - High fallback rate may indicate knowledge gaps
4. **Adjust confidence thresholds** - Based on your use case requirements
5. **Test edge cases** - Empty context, special characters, long inputs

## Troubleshooting

**Issue: High fallback usage rate**
- **Cause**: Knowledge gaps in RAG system
- **Solution**: Improve knowledge base coverage, adjust learning sources

**Issue: Low confidence scores**
- **Cause**: Insufficient context or validation failures
- **Solution**: Improve RAG retrieval, check validation reasons

**Issue: False positives (valid answers rejected)**
- **Cause**: Overly strict validation
- **Solution**: Adjust thresholds, review validation reasons

## Future Enhancements

- [ ] Confidence score calibration based on user feedback
- [ ] Adaptive thresholds based on question type
- [ ] Multi-level fallback strategies
- [ ] Confidence score explanation to users
- [ ] A/B testing framework for threshold optimization

