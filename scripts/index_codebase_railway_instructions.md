# Railway Codebase Indexing Instructions

## Problem
Railway backend doesn't auto-index codebase on startup. You need to manually trigger indexing.

## Solutions

### Option 1: PowerShell Script (Windows - Recommended)

```powershell
# With API key as parameter
.\scripts\index_codebase_railway.ps1 -BackendUrl "https://stillme-backend-production.up.railway.app" -ApiKey "YOUR_API_KEY"

# With API key from environment variable
$env:STILLME_API_KEY = "YOUR_API_KEY"
.\scripts\index_codebase_railway.ps1

# Force re-index (even if collection has chunks)
.\scripts\index_codebase_railway.ps1 -Force
```

### Option 2: Python Script (If Railway CLI is installed)

First, install Railway CLI:
```powershell
# Via npm (if you have Node.js)
npm install -g @railway/cli

# Or via winget
winget install Railway.CLI
```

Then run:
```bash
railway run python scripts/index_codebase_railway.py
```

### Option 3: Direct API Call (PowerShell)

```powershell
$headers = @{
    "X-API-Key" = "YOUR_STILLME_API_KEY"
    "Content-Type" = "application/json"
}
$body = @{ force = $false } | ConvertTo-Json
$response = Invoke-RestMethod -Uri "https://stillme-backend-production.up.railway.app/api/codebase/index" -Method Post -Headers $headers -Body $body
$response | ConvertTo-Json
```

### Option 4: Direct API Call (curl - if you have Git Bash or WSL)

```bash
curl -X POST https://stillme-backend-production.up.railway.app/api/codebase/index \
  -H "X-API-Key: YOUR_STILLME_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"force": false}'
```

## Getting Your API Key

1. Go to Railway dashboard
2. Select your backend service
3. Go to Variables tab
4. Find `STILLME_API_KEY` or create it if it doesn't exist
5. Copy the value

## Verification

After indexing, verify it worked:

```powershell
# Check stats
Invoke-RestMethod -Uri "https://stillme-backend-production.up.railway.app/api/codebase/stats"
```

You should see `total_chunks > 0` and `status: "ready"`.

## Troubleshooting

### "API key authentication required"
- Make sure `STILLME_API_KEY` is set on Railway
- Make sure you're using the correct API key value

### "No relevant code chunks found"
- Collection is empty - run indexing first
- Check Railway logs for errors during indexing

### "Endpoint not found (404)"
- Backend may not be deployed with latest code
- Redeploy backend to Railway

