# Fix Model Name Issue

## Problem

StillMe is mentioning the incorrect embedding model name (`all-MiniLM-L6-v2`) instead of the correct one (`paraphrase-multilingual-MiniLM-L12-v2`).

## Root Causes

1. **Cached Responses**: LLM response cache contains old responses with incorrect model name
2. **Foundational Knowledge**: Foundational knowledge in RAG database may have old model name

## Solution

### Step 1: Update Foundational Knowledge

Run the script to update foundational knowledge in RAG database:

```bash
python scripts/update_foundational_knowledge_model_name.py
```

This script will:
- Search for foundational knowledge documents with old model name
- Replace `all-MiniLM-L6-v2` with `paraphrase-multilingual-MiniLM-L12-v2`
- Update documents in ChromaDB

### Step 2: Clear LLM Cache

Clear the LLM response cache to force regeneration:

```bash
python scripts/clear_llm_cache.py
```

Or via API (if available):

```bash
curl -X POST http://localhost:8000/api/cache/clear
```

### Step 3: Verify

Test StillMe response to verify correct model name:

1. Ask StillMe: "Bạn đang sử dụng mô hình embedding nào?"
2. Response should mention: `paraphrase-multilingual-MiniLM-L12-v2`
3. Should NOT mention: `all-MiniLM-L6-v2`

## Prevention

To prevent this issue in the future:

1. **Single Source of Truth**: Use `stillme_core/rag/model_info.py` for model information
2. **Update Foundational Knowledge**: When model changes, update foundational knowledge script
3. **Clear Cache**: After updating foundational knowledge, clear cache to force regeneration

## Related Files

- `stillme_core/rag/model_info.py` - Single source of truth for model information
- `scripts/add_foundational_knowledge.py` - Foundational knowledge template
- `backend/identity/prompt_builder.py` - Prompt instructions with model name

