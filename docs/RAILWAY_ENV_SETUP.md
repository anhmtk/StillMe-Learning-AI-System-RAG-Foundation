# Railway Environment Variables Setup Guide

## Backend Service Environment Variables

### Required for Nested Learning

**`ENABLE_CONTINUUM_MEMORY`** = `true`
- **Location**: Backend service → Variables tab
- **Purpose**: Enables Nested Learning tiered update frequency system
- **Default**: `false` (disabled)
- **Note**: Must be set to `true` to enable Nested Learning features

### Required for Model Caching (CRITICAL - Prevents Re-downloading)

**`PERSISTENT_CACHE_PATH`** = `/app/hf_cache`
- **Location**: Backend service → Variables tab
- **Purpose**: Points to Railway persistent volume for model cache
- **Why**: Prevents re-downloading `all-MiniLM-L6-v2` model (79MB) on every deploy
- **Note**: This MUST be set to match the persistent volume mount path in `railway-backend.json`

### How to Set in Railway

1. Go to Railway Dashboard
2. Select your **Backend** service
3. Click **Variables** tab
4. Click **+ New Variable**
5. Add:
   - **Name**: `ENABLE_CONTINUUM_MEMORY`
   - **Value**: `true`
6. Add:
   - **Name**: `PERSISTENT_CACHE_PATH`
   - **Value**: `/app/hf_cache`
7. Click **Save**

### Verification

After setting variables, check backend logs:
- Look for: `✅ Using Railway persistent volume cache: /app/hf_cache`
- Look for: `✅ Model cached at: /app/hf_cache`
- Look for: `✅ Model files found in cache: /app/hf_cache/sentence_transformers/all-MiniLM-L6-v2`

If you see these messages, model caching is working correctly.

## Persistent Volume Setup

The persistent volume is already configured in `railway-backend.json`:
```json
{
  "volumes": [
    {
      "name": "stillme-hf-cache",
      "mountPath": "/app/hf_cache",
      "sizeGB": 1
    }
  ]
}
```

**Important**: Railway manages volumes through **Config-as-Code** (not a separate "Volumes" tab).

### How to Verify Volume:

1. **Check Config-as-Code**:
   - Go to Backend service → **Settings** → **Config-as-code** tab
   - Verify `railway-backend.json` is selected
   - Check that volumes configuration is present

2. **Verify via Backend Logs** (After deploy):
   - Look for: `✅ Using Railway persistent volume cache: /app/hf_cache`
   - If you see this, volume is mounted correctly

3. **Check if volume exists** (via logs):
   - After first deploy, check if `/app/hf_cache` directory exists
   - Model will be cached there after first download

### If Volume Not Working:

Railway should **auto-create** the volume from `railway-backend.json` on first deploy. If it doesn't:
1. Check **Config-as-code** tab → verify `railway-backend.json` path is correct
2. Redeploy the service (Railway will read config and create volume)
3. Check logs for volume mount messages

## Troubleshooting

### Model Still Re-downloading?

1. **Check persistent volume exists**: Backend → Volumes → `stillme-hf-cache`
2. **Check environment variable**: Backend → Variables → `PERSISTENT_CACHE_PATH=/app/hf_cache`
3. **Check logs**: Look for cache path messages during startup
4. **Verify cache directory**: After first download, model should be in `/app/hf_cache/sentence_transformers/all-MiniLM-L6-v2`

### Nested Learning Not Working?

1. **Check environment variable**: Backend → Variables → `ENABLE_CONTINUUM_MEMORY=true`
2. **Check logs**: Look for "Nested Learning: Update isolation enabled"
3. **Verify feature flag**: Dashboard → Nested Learning page should show metrics (not "disabled" message)

