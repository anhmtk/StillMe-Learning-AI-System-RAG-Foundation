# StillMe Structural Manifest - Quick Start

## Problem Solved

StillMe was reporting incorrect validator counts (e.g., "15-layer" or "13+ validators") because it relied on:
- Hardcoded prompts (outdated)
- Static documentation (not synced with code)
- LLM training data (cutoff date issues)

**Solution**: Auto-generated structural manifest that StillMe retrieves from RAG.

## Quick Commands

### Generate Manifest
```bash
python scripts/generate_manifest.py
```
**Output**: `data/stillme_manifest.json`

### Inject to RAG
```bash
python scripts/inject_manifest_to_rag.py
```
**Note**: Auto-generates manifest if missing.

### Both (Recommended)
```bash
python scripts/inject_manifest_to_rag.py
```

## When to Run

**After code changes**:
- Adding/removing validators
- Modifying validator logic
- Changing validator dependencies

**Before deployment**:
- Always regenerate before pushing to production
- Ensures StillMe has latest structure info

**As part of workflow**:
- Add to pre-commit hook (optional)
- Add to CI/CD pipeline (recommended)

## Current Status

✅ **Manifest Generated**: `data/stillme_manifest.json`
✅ **Manifest Injected**: Available in ChromaDB with CRITICAL_FOUNDATION priority
✅ **Total Validators**: 19
✅ **Active Range**: 10-17 validators per response
✅ **Layers**: 7 logical layers

## Verification

Test StillMe's knowledge:
```
"How many validators do you have?"
"What is your validation chain architecture?"
"Explain your 7-layer validation framework"
```

StillMe should now respond with accurate information from the manifest.

## Troubleshooting

**StillMe reports wrong count**:
1. Regenerate: `python scripts/generate_manifest.py`
2. Reinject: `python scripts/inject_manifest_to_rag.py`
3. Test query again

**Manifest not retrieved**:
- Check ChromaDB has CRITICAL_FOUNDATION documents
- Verify query similarity threshold
- Check RAG retrieval logs

## Files

- `scripts/generate_manifest.py` - Manifest generator
- `scripts/inject_manifest_to_rag.py` - RAG injector
- `data/stillme_manifest.json` - Generated manifest (JSON)
- `docs/STRUCTURAL_MANIFEST.md` - Full documentation

