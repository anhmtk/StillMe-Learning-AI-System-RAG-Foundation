# Epistemic State Classification

## Overview

StillMe classifies each response into one of three **epistemic states** to indicate the system's level of certainty about the information provided:

- **KNOWN**: Clear evidence, good citations, validators pass
- **UNCERTAIN**: Some information but thin, or validators warn
- **UNKNOWN**: System truly doesn't know / insufficient data

This classification helps users understand the reliability of StillMe's responses and aligns with StillMe's philosophy of transparency and anti-hallucination.

## Classification Rules

### KNOWN State

A response is classified as **KNOWN** when:

- ✅ Validation passed (`validation_passed = True`)
- ✅ Has valid citations (e.g., `[1]`, `[2]`, `[general knowledge]`)
- ✅ Has RAG context (`context_docs_count > 0`)
- ✅ High confidence (`confidence_score >= 0.7`)
- ✅ No critical warnings from validators

**Example:**
```
Response: "According to [1] and [2], the capital of France is Paris."
- Citations: [1], [2]
- Context docs: 3
- Confidence: 0.85
- Validation: Passed
→ State: KNOWN
```

### UNCERTAIN State

A response is classified as **UNCERTAIN** when:

- Has some information (citations or context) but:
  - Medium confidence (`0.4 <= confidence_score < 0.7`), or
  - Has warnings from validators (non-critical), or
  - Has citations but no RAG context (general knowledge only)

**Example:**
```
Response: "Based on [1], the answer might be X. However, there is some uncertainty."
- Citations: [1]
- Context docs: 1
- Confidence: 0.55
- Validation: Passed with warnings
→ State: UNCERTAIN
```

### UNKNOWN State

A response is classified as **UNKNOWN** when:

- ❌ Fallback triggered (`used_fallback = True`), or
- ❌ No context and low confidence (`context_docs_count = 0` and `confidence_score < 0.5`), or
- ❌ Critical validation failures (e.g., `factual_hallucination`, `missing_citation`, `explicit_fake_entity`)

**Example:**
```
Response: "I don't have sufficient information to answer this question accurately."
- Citations: None
- Context docs: 0
- Confidence: 0.2
- Fallback: True
→ State: UNKNOWN
```

## Implementation

### Location

- **Module**: `backend/core/epistemic_state.py`
- **Function**: `calculate_epistemic_state()`
- **Integration**: Calculated after validation, before returning `ChatResponse`

### API Response

The `epistemic_state` field is included in the `ChatResponse` JSON:

```json
{
  "response": "...",
  "confidence_score": 0.85,
  "validation_info": {...},
  "epistemic_state": "KNOWN"
}
```

### Configuration

Thresholds can be adjusted in `calculate_epistemic_state()`:

- **KNOWN threshold**: `confidence_score >= 0.7` (line ~100)
- **UNCERTAIN range**: `0.4 <= confidence_score < 0.7` (line ~120)
- **Citation patterns**: Regex patterns for detecting citations (line ~60)
- **Critical failures**: List of critical validation failure patterns (line ~75)

## Use Cases

1. **User Transparency**: Users can see at a glance how confident StillMe is about each response
2. **Quality Monitoring**: Track the distribution of epistemic states across responses
3. **Fallback Detection**: Identify when StillMe is using fallback responses
4. **Citation Quality**: Distinguish between responses with RAG context vs. general knowledge

## Future Enhancements

- **ML-based Classification**: Upgrade from rule-based to ML-based classifier for more nuanced classification
- **Citation Quality Scoring**: Consider citation relevance and source quality, not just presence
- **Confidence Calibration**: Fine-tune confidence thresholds based on evaluation results
- **Dashboard Integration**: Display epistemic state badges in the dashboard UI

## Related Features

- **Validation Chain**: Epistemic state relies on validation results from the validator chain
- **Confidence Scoring**: Uses `confidence_score` calculated from context quality and validation results
- **Fallback Mechanism**: UNKNOWN state is triggered when fallback responses are used
- **Citation System**: KNOWN state requires valid citations from RAG context

## See Also

- [Validation Chain Documentation](VALIDATION_CHAIN.md)
- [Cost-Benefit Logic for RewriteLLM](COST_BENEFIT_REWRITE.md)
- [StillMe Architecture](../README.md)

