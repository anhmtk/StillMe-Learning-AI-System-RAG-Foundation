# Changelog - Validator Chain Integration

## v0.6.4 - Validator Chain & Identity Injection (2025-01-27)

### Added

#### Validators Module (`backend/validators/`)
- **ValidatorChain**: Orchestrates multiple validators sequentially
- **CitationRequired**: Ensures answers include citations `[1]`, `[2]`, etc.
- **EvidenceOverlap**: Checks answer overlaps with RAG context (ngram-based, threshold: 8%)
- **NumericUnitsBasic**: Detects numbers and suggests citations
- **SchemaFormat**: Validates answer format/sections (optional, endpoint-specific)
- **EthicsAdapter**: Wraps existing ethics guard (if available)
- **ValidationMetrics**: Collects metrics (pass rate, overlap scores, reasons histogram)

#### Identity Module (`backend/identity/`)
- **IdentityInjector**: Injects StillMe identity into prompts
- **STILLME_IDENTITY**: System prompt ensuring brand consistency

#### Tone Module (`backend/tone/`)
- **ToneAligner**: Normalizes response tone to StillMe style

#### API Changes
- **New endpoint**: `GET /api/validators/metrics` - Returns validation metrics
- **Enhanced endpoint**: `POST /api/chat/rag` - Now supports validation chain (if enabled)
- **Error response**: Returns 422 with validation reasons if validation fails

#### Dashboard Changes
- **New page**: "Validation" - Shows validation metrics, pass rate, overlap scores, failure reasons histogram, and recent logs

#### Environment Variables
- `ENABLE_VALIDATORS=true|false` - Enable/disable validators globally (default: false)
- `ENABLE_TONE_ALIGN=true|false` - Enable/disable tone alignment (default: true)
- `VALIDATOR_EVIDENCE_THRESHOLD=0.08` - Minimum overlap threshold (default: 0.08)
- `VALIDATOR_CITATION_REQUIRED=true|false` - Require citations (default: true)
- `STILLME_TONE_STYLE=neutral|friendly|scholarly` - Tone style (default: neutral, future)

#### Tests
- `tests/test_validators_chain.py` - Tests for ValidatorChain (5 tests)
- `tests/test_identity_injector.py` - Tests for IdentityInjector (4 tests)
- `tests/test_evidence_overlap.py` - Tests for EvidenceOverlap (9 tests)
- All tests passing ✅

#### Documentation
- `docs/CODEBASE_MAP_VALIDATORS.md` - Codebase map for validators integration
- `docs/INTEGRATION_VALIDATORS.md` - Integration plan and pipeline flow
- Updated `README.md` with validator chain section

### Changed

- **`backend/api/main.py`**: 
  - Enhanced `/api/chat/rag` endpoint with validation chain
  - Added identity injection before model calls
  - Added tone alignment after validation
  - Added metrics recording

### Technical Details

**Pipeline Flow:**
```
User Request → RAG Retrieval → Identity Injection → Model Call → 
Validator Chain → Tone Alignment → Metrics → Response
```

**Validator Chain Order:**
1. CitationRequired
2. EvidenceOverlap
3. NumericUnitsBasic
4. SchemaFormat (optional)
5. EthicsAdapter

**Rollback Strategy:**
- Set `ENABLE_VALIDATORS=false` to disable all validators
- All validators are wrapped in try-catch with fallback to raw response
- No breaking changes to existing API (backward compatible)

### Breaking Changes

None. All changes are backward compatible and can be disabled via environment variables.

### Migration Guide

1. **Enable validators** (optional):
   ```bash
   export ENABLE_VALIDATORS=true
   export ENABLE_TONE_ALIGN=true
   ```

2. **Monitor metrics**:
   - Visit dashboard → "Validation" page
   - Or call `GET /api/validators/metrics`

3. **Rollback if needed**:
   ```bash
   export ENABLE_VALIDATORS=false
   ```

### Known Issues

- EthicsAdapter currently has no-op guard (TODO: wire existing ethics guard if available)
- Validation adds ~100-200ms latency (acceptable for quality improvement)
- Some validators may have false positives (can be tuned via thresholds)

### Future Improvements

- [ ] Wire existing ethics guard into EthicsAdapter
- [ ] Add RetrievalCoverage validator (check if entities exist in RAG docs)
- [ ] Async validation for better performance
- [ ] Caching validation results
- [ ] More sophisticated tone alignment rules
- [ ] Per-endpoint validator configuration

