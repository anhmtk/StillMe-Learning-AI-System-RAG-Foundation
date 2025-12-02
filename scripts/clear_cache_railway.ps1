# PowerShell script to clear LLM cache on Railway
# Usage: .\scripts\clear_cache_railway.ps1

param(
    [string]$BackendUrl = "https://stillme-backend-production.up.railway.app",
    [string]$Pattern = "llm:response:*",
    [switch]$ClearAll
)

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "Clearing Cache on Railway" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

if ($ClearAll) {
    $url = "$BackendUrl/api/cache/clear"
    Write-Host "Clearing ALL cache..." -ForegroundColor Yellow
} else {
    $url = "$BackendUrl/api/cache/clear?pattern=$Pattern"
    Write-Host "Clearing LLM cache (pattern: $Pattern)..." -ForegroundColor Yellow
}

Write-Host "URL: $url" -ForegroundColor Gray
Write-Host ""

try {
    $response = Invoke-WebRequest -Uri $url -Method POST -UseBasicParsing
    
    if ($response.StatusCode -eq 200) {
        $result = $response.Content | ConvertFrom-Json
        Write-Host "✅ Success!" -ForegroundColor Green
        Write-Host "   Status: $($result.status)" -ForegroundColor Green
        Write-Host "   Message: $($result.message)" -ForegroundColor Green
        if ($result.cleared_count) {
            Write-Host "   Cleared: $($result.cleared_count) entries" -ForegroundColor Green
        }
    } else {
        Write-Host "⚠️ Unexpected status code: $($response.StatusCode)" -ForegroundColor Yellow
    }
} catch {
    Write-Host "❌ Error: $($_.Exception.Message)" -ForegroundColor Red
    if ($_.Exception.Response) {
        $reader = New-Object System.IO.StreamReader($_.Exception.Response.GetResponseStream())
        $responseBody = $reader.ReadToEnd()
        Write-Host "   Response: $responseBody" -ForegroundColor Red
    }
    exit 1
}

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "Next steps:" -ForegroundColor Cyan
Write-Host "1. Test StillMe response to verify correct model name" -ForegroundColor Cyan
Write-Host "2. Response should now be regenerated with updated knowledge" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan

