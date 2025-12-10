# NPR-Inspired Validator Dependencies Analysis

## Validator Execution Order (Current)

### Sequential Validators (Must run in order)

1. **LanguageValidator** (Priority: HIGHEST)
   - Must run FIRST
   - Detects language mismatch
   - Can patch answer if mismatch detected
   - **Dependencies**: None (independent)

2. **CitationRequired** (Priority: CRITICAL)
   - Must run before CitationRelevance
   - Provides citations to answer
   - Can patch answer (adds citations)
   - **Dependencies**: None (but provides data for CitationRelevance)

3. **ConfidenceValidator** (Priority: CRITICAL)
   - May depend on other validators' results
   - Reads `previous_reasons` to detect source_contradiction
   - **Dependencies**: 
     - SourceConsensusValidator (if enabled) - detects contradictions
     - EvidenceOverlap (if enabled) - checks overlap
   - **Note**: Can run after parallel validators complete

4. **FactualHallucinationValidator** (Priority: CRITICAL)
   - Detects factual errors
   - **Dependencies**: None (reads answer and ctx_docs only)

5. **ReligiousChoiceValidator** (Priority: CRITICAL)
   - Rejects religion choice in responses
   - **Dependencies**: None (reads answer only)

### Parallel Validators (Can run concurrently)

1. **CitationRelevance** (Priority: MEDIUM)
   - Checks citation quality
   - **Dependencies**: CitationRequired (must run first to provide citations)
   - **Note**: Currently marked as parallel, but depends on CitationRequired
   - **Recommendation**: Keep sequential after CitationRequired

2. **EvidenceOverlap** (Priority: MEDIUM)
   - Checks content matches context
   - **Dependencies**: None (reads answer and ctx_docs only)
   - **Can run in parallel**: ✅ YES

3. **NumericUnitsBasic** (Priority: LOW)
   - Validates numeric/units claims
   - **Dependencies**: None (reads answer only)
   - **Can run in parallel**: ✅ YES

4. **EgoNeutralityValidator** (Priority: MEDIUM)
   - Catches "Hallucination of Experience"
   - **Dependencies**: None (reads answer and ctx_docs only)
   - **Can run in parallel**: ✅ YES

5. **SourceConsensusValidator** (Priority: MEDIUM)
   - Detects contradictions between sources
   - **Dependencies**: 
     - EvidenceOverlap (should run after to check overlap first)
     - ConfidenceValidator (uses results to express uncertainty)
   - **Note**: Currently marked as both parallel and sequential (contradiction!)
   - **Recommendation**: Run after EvidenceOverlap, before ConfidenceValidator (sequential)

6. **IdentityCheckValidator** (Priority: MEDIUM)
   - Prevents anthropomorphism
   - **Dependencies**: None (reads answer only)
   - **Can run in parallel**: ✅ YES

7. **PhilosophicalDepthValidator** (Priority: LOW, Conditional)
   - Validates philosophical depth
   - **Dependencies**: None (reads answer only)
   - **Can run in parallel**: ✅ YES

8. **EthicsAdapter** (Priority: CRITICAL)
   - Ethical content filtering
   - **Dependencies**: None (reads answer only)
   - **Can run in parallel**: ✅ YES (but should run last for safety)

## Optimal Parallel Execution Groups

### Group 1: Sequential (Must run first)
```
LanguageValidator → CitationRequired → [Parallel Group 2] → ConfidenceValidator
```

### Group 2: Parallel (Can run concurrently after CitationRequired)
```
- CitationRelevance (after CitationRequired)
- EvidenceOverlap
- NumericUnitsBasic
- EgoNeutralityValidator
- IdentityCheckValidator
- PhilosophicalDepthValidator (if philosophical)
- EthicsAdapter (should run last, but can be parallel)
```

### Group 3: Sequential (After parallel group)
```
SourceConsensusValidator (after EvidenceOverlap) → ConfidenceValidator
```

### Group 4: Sequential (Critical validators)
```
FactualHallucinationValidator → ReligiousChoiceValidator
```

## Current Issues

1. **CitationRelevance** marked as parallel but depends on CitationRequired
   - **Fix**: Run sequentially after CitationRequired

2. **SourceConsensusValidator** marked as both parallel and sequential
   - **Fix**: Run sequentially after EvidenceOverlap, before ConfidenceValidator

3. **ConfidenceValidator** depends on SourceConsensusValidator results
   - **Fix**: Run sequentially after SourceConsensusValidator

4. **EthicsAdapter** should run last for safety
   - **Fix**: Keep as last validator, but can still run in parallel with others

## NPR-Inspired Optimization

### Shared KV Cache Concept
- Validators that read the same data (answer, ctx_docs) can share a cache
- Embeddings for ctx_docs can be computed once and shared
- Similarity scores can be cached

### Parallel Execution Strategy
1. **Phase 1**: Run sequential validators (LanguageValidator, CitationRequired)
2. **Phase 2**: Run parallel validators in batches:
   - Batch 1: CitationRelevance (depends on CitationRequired)
   - Batch 2: EvidenceOverlap, NumericUnitsBasic, EgoNeutralityValidator, IdentityCheckValidator, PhilosophicalDepthValidator
   - Batch 3: EthicsAdapter (last for safety)
3. **Phase 3**: Run sequential validators (SourceConsensusValidator, ConfidenceValidator)
4. **Phase 4**: Run critical validators (FactualHallucinationValidator, ReligiousChoiceValidator)

## Expected Speedup

- **Current**: ~2-3s for full validation chain
- **With NPR optimization**: ~0.5-1s (2-3x speedup)
- **Parallel validators**: 6-8 validators can run concurrently
- **Sequential validators**: 4-5 validators must run in order

## Implementation Plan

1. ✅ Analyze dependencies (this document)
2. ⏳ Optimize `_can_run_parallel()` logic
3. ⏳ Implement batch-based parallel execution
4. ⏳ Add shared KV cache for embeddings
5. ⏳ Add performance metrics
6. ⏳ Test and measure speedup

