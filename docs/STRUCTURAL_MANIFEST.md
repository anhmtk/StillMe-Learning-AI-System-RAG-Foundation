# StillMe Structural Manifest System

## Overview

The Structural Manifest system ensures StillMe always knows the **exact current state** of its own validation framework. This solves the "knowledge gap" problem where StillMe reports outdated information. StillMe must read numbers from the manifest, not from hardcoded documentation.

## Problem Statement

**Before**: StillMe's knowledge about its own structure came from:
- Hardcoded prompts (often outdated)
- Static documentation files
- LLM training data (cutoff date issues)

**Result**: StillMe would report incorrect validator counts, outdated architecture information, or generic descriptions.

**After**: StillMe has a **self-generated, always-up-to-date manifest** that:
- Scans the actual codebase
- Extracts validator information automatically
- Injects into RAG with CRITICAL_FOUNDATION priority
- Updates whenever validators change

## Architecture

### 1. Manifest Generation (`scripts/generate_manifest.py`)

**Purpose**: Scan `stillme_core/validation/` and extract:
- All validator classes
- Docstrings and purposes
- Execution modes (sequential/parallel)
- Criticality levels
- File paths
- Layer organization

**Output**: `data/stillme_manifest.json`

**When to run**:
- After adding/removing validators
- After modifying validator logic
- Before deploying to production
- As part of CI/CD pipeline

### 2. Manifest Injection (`scripts/inject_manifest_to_rag.py`)

**Purpose**: Convert JSON manifest to human-readable text and inject into ChromaDB

**Process**:
1. Load `data/stillme_manifest.json`
2. Convert to markdown-formatted text
3. Add to ChromaDB with `CRITICAL_FOUNDATION` source tag
4. Set `importance_score: 1.0` for priority retrieval

**Result**: StillMe retrieves this manifest when answering about validation chain

### 3. Manifest Structure

```json
{
  "system_name": "StillMe",
  "version": "1.2.0",
  "last_sync": "2025-12-20T12:17:45Z",
  "validation_framework": {
    "total_validators": 19,
    "min_active_validators": 10,
    "max_active_validators": 17,
    "always_active": [...],
    "conditional": [...],
    "layers": [...],
    "registry": {...}
  }
}
```

## Usage

### Generate Manifest

```bash
python scripts/generate_manifest.py
```

**Output**: `data/stillme_manifest.json`

### Inject to RAG

```bash
python scripts/inject_manifest_to_rag.py
```

**Note**: This script will auto-generate manifest if it doesn't exist.

### Combined Workflow

```bash
# Generate and inject in one command
python scripts/inject_manifest_to_rag.py
```

## Integration Points

### 1. RAG Retrieval Priority

The manifest is injected with:
- `source: "CRITICAL_FOUNDATION"` - Highest priority tag
- `importance_score: 1.0` - Maximum importance
- `tags: "foundational:stillme,CRITICAL_FOUNDATION,validation,validators"`

This ensures StillMe retrieves it when answering about:
- "How many validators do you have?"
- "What is your validation chain?"
- "Explain your validation architecture"

### 2. Prompt Integration

The manifest text is formatted to be:
- **Human-readable**: Markdown format for LLM consumption
- **Structured**: Clear sections (layers, registry, counts)
- **Actionable**: Explicit instructions like "DO NOT say '15-layer'"

### 3. Auto-Sync Strategy

**Option A: Manual (Current)**
- Run `generate_manifest.py` after code changes
- Run `inject_manifest_to_rag.py` to update RAG

**Option B: Git Hook (Recommended)**
- Pre-commit hook: Regenerate manifest if validation files changed
- Pre-push hook: Inject to RAG before deployment

**Option C: CI/CD Integration**
- Generate manifest in CI pipeline
- Inject to RAG in deployment step
- Verify manifest is up-to-date

## Current Validator Count

**Total Validators**: 19

**Always Active**: 10
- LanguageValidator
- CitationRequired
- CitationRelevance
- NumericUnitsBasic
- ConfidenceValidator
- FactualHallucinationValidator
- ReligiousChoiceValidator
- HallucinationExplanationValidator
- VerbosityValidator
- EthicsAdapter

**Conditional**: 7
- EvidenceOverlap (when has context)
- SourceConsensusValidator (when has ≥2 sources)
- EgoNeutralityValidator (when has context)
- IdentityCheckValidator (when enabled)
- PhilosophicalDepthValidator (for philosophical questions)
- ReviewAdapter (may not always be used)
- AISelfModelValidator (for AI_SELF_MODEL domain)

**Active Range**: 10-17 validators per response

## Validation Layers

1. **Language & Format**: LanguageValidator, SchemaFormat
2. **Citation & Evidence**: CitationRequired, CitationRelevance, EvidenceOverlap
3. **Content Quality**: ConfidenceValidator, FactualHallucinationValidator, NumericUnitsBasic
4. **Identity & Ethics**: IdentityCheckValidator, EgoNeutralityValidator, EthicsAdapter, ReligiousChoiceValidator
5. **Source Consensus**: SourceConsensusValidator
6. **Specialized Validation**: PhilosophicalDepthValidator, HallucinationExplanationValidator, VerbosityValidator, AISelfModelValidator
7. **Fallback & Review**: FallbackHandler, ReviewAdapter

## Benefits

### 1. Self-Awareness
StillMe can accurately describe its own architecture:
- "I have 19 validators total"
- "I use 10-17 validators per response depending on context"
- "My validation framework has 7 logical layers"

### 2. Technical Credibility
When StillMe says "I checked this through 17 validation layers", it's **factually accurate**, not a hallucination.

### 3. Maintainability
- No manual prompt updates needed
- Manifest auto-updates from codebase
- Single source of truth

### 4. Transparency
- Users can verify StillMe's claims
- Manifest is publicly accessible
- Architecture is self-documenting

## Troubleshooting

### Manifest Out of Sync

**Symptoms**: StillMe reports wrong validator count

**Solution**:
```bash
python scripts/generate_manifest.py
python scripts/inject_manifest_to_rag.py
```

### Manifest Not Retrieved

**Symptoms**: StillMe doesn't mention manifest information

**Check**:
1. Manifest exists in `data/stillme_manifest.json`
2. Manifest injected to ChromaDB (check logs)
3. RAG retrieval includes `CRITICAL_FOUNDATION` source
4. Query similarity is high enough

**Debug**:
```python
from backend.vector_db.rag_retrieval import get_rag_retrieval
rag = get_rag_retrieval()
results = rag.search("StillMe validation chain validators", n_results=5)
# Check if manifest appears in results
```

## Future Enhancements

1. **Auto-regeneration on file changes**: Watch `stillme_core/validation/` for changes
2. **Version tracking**: Track manifest versions and changes over time
3. **Dependency graph**: Visualize validator dependencies
4. **Performance metrics**: Include validator execution times in manifest
5. **Test coverage**: Include test coverage information per validator

## Related Files

- `scripts/generate_manifest.py` - Manifest generator
- `scripts/inject_manifest_to_rag.py` - RAG injector
- `data/stillme_manifest.json` - Generated manifest
- `stillme_core/validation/` - Validator source code
- `docs/framework/VALIDATION.md` - Validation framework documentation

