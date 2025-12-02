# Clear Cache Guide

## Problem

StillMe responses may contain outdated information (e.g., incorrect model names) due to cached responses.

## Solution: Clear Cache via API

### Option 1: Clear All Cache

**PowerShell (Windows):**
```powershell
Invoke-WebRequest -Uri "https://stillme-backend-production.up.railway.app/api/cache/clear" -Method POST
```

**Bash/Linux/Mac:**
```bash
curl -X POST https://stillme-backend-production.up.railway.app/api/cache/clear
```

### Option 2: Clear Only LLM Response Cache (Recommended)

**PowerShell (Windows):**
```powershell
Invoke-WebRequest -Uri "https://stillme-backend-production.up.railway.app/api/cache/clear?pattern=llm:response:*" -Method POST
```

**Bash/Linux/Mac:**
```bash
curl -X POST "https://stillme-backend-production.up.railway.app/api/cache/clear?pattern=llm:response:*"
```

**Note**: On Windows PowerShell, `curl` is an alias for `Invoke-WebRequest` which doesn't support `-X`. Use `Invoke-WebRequest` directly or `curl.exe` if you have it installed.

This will clear only LLM response cache, keeping RAG and HTTP caches intact.

## Response Format

```json
{
  "status": "success",
  "message": "Cleared 5 cache entries matching pattern: llm:response:*",
  "pattern": "llm:response:*",
  "cleared_count": 5
}
```

## When to Clear Cache

1. **After updating foundational knowledge**: When foundational knowledge in RAG database is updated
2. **After model changes**: When embedding model or LLM model changes
3. **After prompt changes**: When system prompts or instructions are updated
4. **After fixing bugs**: When response generation logic is fixed

## Example Workflow

1. Update foundational knowledge:
   ```bash
   python scripts/update_foundational_knowledge_model_name.py
   ```

2. Clear LLM cache:
   ```bash
   curl -X POST "https://stillme-backend-production.up.railway.app/api/cache/clear?pattern=llm:response:*"
   ```

3. Test StillMe response to verify changes

## Notes

- Cache clearing is **immediate** and **irreversible**
- Clearing cache will force StillMe to regenerate responses (may be slower)
- LLM cache TTL is typically 1 hour (3600 seconds)
- RAG cache TTL is typically 6 hours (21600 seconds)

