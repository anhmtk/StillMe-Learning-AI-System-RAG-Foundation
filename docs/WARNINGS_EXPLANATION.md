# StillMe Backend Warnings Explanation

## 1. CORS_ALLOWED_ORIGINS Warning

```
[WARNING] ⚠️ CORS_ALLOWED_ORIGINS not set. Using default localhost origins only.
```

**Meaning:**
- CORS (Cross-Origin Resource Sharing) is not configured for production
- Backend only allows requests from `localhost` origins
- Dashboard on Railway may not be able to connect to backend

**Impact:**
- ⚠️ **Production Issue**: Dashboard may fail to connect to backend if they're on different domains

**Fix:**
Set environment variable in Railway Backend service:
```
CORS_ALLOWED_ORIGINS=https://your-dashboard-url.up.railway.app,https://your-frontend-domain.com
```

**Note:** This is a **production security warning**. For development, it's OK to ignore.

---

## 2. HTTPS Enforcement Warning

```
[INFO] ⚠️ HTTPS enforcement disabled - set ENFORCE_HTTPS=true to enable
```

**Meaning:**
- Backend is not forcing HTTPS redirects
- HTTP requests are allowed (security risk in production)

**Impact:**
- ⚠️ **Production Security Risk**: Sensitive data may be sent over HTTP

**Fix:**
Set environment variable in Railway Backend service:
```
ENFORCE_HTTPS=true
```

**Note:** Railway automatically provides HTTPS, but this ensures HTTP requests are redirected to HTTPS.

---

## 3. Pydantic Schema Warning

```
[err] * 'schema_extra' has been renamed to 'json_schema_extra'
```

**Meaning:**
- Code is using Pydantic V1 syntax (`schema_extra`) but Pydantic V2 is installed
- This is a deprecation warning, not an error

**Impact:**
- ✅ **No Impact**: Code still works, but should be updated for future compatibility

**Fix:**
Update Pydantic models to use `json_schema_extra` instead of `schema_extra` (low priority).

---

## 4. ChromaDB Telemetry Error

```
[ERROR] Failed to send telemetry event ClientCreateCollectionEvent: capture() takes 1 positional argument but 3 were given
```

**Meaning:**
- ChromaDB library is trying to send telemetry but the handler signature is wrong
- This is a **ChromaDB library bug**, not our code

**Impact:**
- ✅ **No Impact**: Telemetry is disabled anyway (`anonymized_telemetry=False`)
- Error is logged but doesn't affect functionality

**Fix:**
Already fixed - telemetry is disabled in `chroma_client.py`. This error can be ignored.

---

## 5. Model Cache Warning

```
[WARNING] ⚠️ Model files not found in cache. Will download on first use.
```

**Meaning:**
- Model cache directory exists but model files are not found
- Model will be downloaded when first used

**Impact:**
- ⚠️ **Performance**: First request will be slow (2-3 minutes to download 79MB model)
- ⚠️ **Cost**: Model is re-downloaded if not cached properly

**Root Cause:**
- Persistent volume may not be mounted correctly
- Model may be cached in a different location than expected
- Cache verification logic may not check the correct path

**Fix:**
See `docs/RAILWAY_ENV_SETUP.md` for persistent volume setup instructions.

---

## Summary

| Warning | Severity | Action Required |
|---------|----------|----------------|
| CORS_ALLOWED_ORIGINS | ⚠️ Production | Set in Railway variables |
| ENFORCE_HTTPS | ⚠️ Production | Set `ENFORCE_HTTPS=true` |
| Pydantic schema_extra | ✅ Low | Update to `json_schema_extra` (future) |
| ChromaDB telemetry | ✅ None | Already disabled, can ignore |
| Model cache | ⚠️ Performance | Fix persistent volume setup |

