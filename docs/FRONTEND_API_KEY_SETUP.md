# Frontend API Key Setup Guide

## Overview
StillMe backend requires API key authentication for sensitive endpoints (scheduler control, database reset, knowledge injection). This guide explains how to configure the frontend to include API keys in requests.

## 🔐 Required Environment Variables

### For Streamlit Dashboard (dashboard.py)

Add to your `.env` file or Railway Variables:

```bash
STILLME_API_KEY=your_actual_api_key_here
STILLME_API_BASE=https://your-backend-url.up.railway.app
```

**Important:**
- `STILLME_API_KEY` must match the backend's `STILLME_API_KEY` environment variable
- `STILLME_API_BASE` should point to your backend URL (not localhost in production)

## 📋 Endpoints Requiring API Key

The following endpoints require `X-API-Key` header:

### Learning Scheduler:
- `POST /api/learning/scheduler/start` - Start scheduler
- `POST /api/learning/scheduler/stop` - Stop scheduler
- `POST /api/learning/curator/update-source-quality` - Update source quality

### RAG Operations:
- `POST /api/rag/add_knowledge` - Add knowledge to vector DB
- `POST /api/rag/reset-database` - Reset vector database
- `GET /api/rag/list-documents` - List documents (requires API key)

### Tiers (Nested Learning):
- `POST /api/v1/tiers/promote/{item_id}` - Promote knowledge item
- `POST /api/v1/tiers/demote/{item_id}` - Demote knowledge item

## 🔧 Implementation Details

### Backend Security Config

The backend uses `require_api_key` dependency for protected endpoints:

```python
from backend.api.auth import require_api_key

@router.post("/scheduler/start", dependencies=[Depends(require_api_key)])
async def start_scheduler():
    ...
```

### Frontend Implementation

The Streamlit dashboard (`dashboard.py`) includes a helper function:

```python
def get_api_headers() -> Dict[str, str]:
    """
    Get headers for API requests, including API key if available.
    """
    headers = {"Content-Type": "application/json"}
    if STILLME_API_KEY:
        headers["X-API-Key"] = STILLME_API_KEY
    return headers
```

All protected requests now use:

```python
r = requests.post(
    f"{API_BASE}/api/learning/scheduler/start",
    headers=get_api_headers(),
    timeout=30
)
```

## 🚀 Setup Instructions

### Local Development:

1. **Create `.env` file in project root:**
```bash
STILLME_API_KEY=your_local_api_key_here
STILLME_API_BASE=http://localhost:8000
```

2. **Generate API key (if not set):**
```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

3. **Set same key in backend `.env`:**
```bash
STILLME_API_KEY=your_local_api_key_here
```

### Production (Railway):

1. **Backend Service → Variables:**
   - `STILLME_API_KEY` = `your_production_api_key`
   - `ENV` = `production`

2. **Dashboard Service → Variables:**
   - `STILLME_API_KEY` = `your_production_api_key` (same as backend)
   - `STILLME_API_BASE` = `https://your-backend-url.up.railway.app`

## ✅ Verification

After setup, test scheduler start:

1. Open dashboard
2. Go to "Learning" page
3. Click "▶️ Start Scheduler"
4. Check backend logs for:
   - `✅ API key verified successfully`
   - `🚀 Starting learning scheduler...`

## ❌ Troubleshooting

### Error: "401 Unauthorized"

**Cause:** API key missing or incorrect

**Fix:**
1. Verify `STILLME_API_KEY` is set in dashboard service variables
2. Verify key matches backend `STILLME_API_KEY`
3. Check logs: `API key missing from request header`

### Error: "403 Forbidden"

**Cause:** API key is incorrect

**Fix:**
1. Regenerate API key
2. Update both backend and dashboard variables
3. Redeploy both services

### Error: "API authentication is not configured"

**Cause:** Backend `STILLME_API_KEY` not set in production

**Fix:**
1. Set `STILLME_API_KEY` in backend service variables
2. Set `ENV=production` in backend service variables
3. Redeploy backend

## 📝 Security Notes

- **Never commit API keys to git** - Use environment variables only
- **Use different keys for dev/prod** - Don't share keys between environments
- **Rotate keys regularly** - Change keys periodically for security
- **Minimum key length:** 32 characters (enforced by backend)

## 🔗 Related Documentation

- `docs/PRODUCTION_FIXES_SUMMARY.md` - Security fixes overview
- `backend/config/security.py` - Security configuration
- `backend/api/auth.py` - Authentication implementation

