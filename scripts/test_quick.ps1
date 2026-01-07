# Quick Test Script for StillMe (PowerShell)
# Usage: .\scripts\test_quick.ps1

# Set your Railway backend URL here (without https://)
$railwayUrl = "stillme-backend-production.up.railway.app"

# Auto-add https:// if not present
if (-not $railwayUrl.StartsWith("http")) {
    $railwayUrl = "https://$railwayUrl"
}

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "StillMe Quick Test Script" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "Testing against: $railwayUrl" -ForegroundColor Yellow
Write-Host ""

# Set environment variable
$env:STILLME_API_BASE = $railwayUrl

# Test 1: Health check
Write-Host "Test 1: Health Check" -ForegroundColor Green
try {
    $health = Invoke-RestMethod -Uri "$railwayUrl/health" -Method GET -TimeoutSec 10
    Write-Host "  [PASS] Backend is healthy: $($health.status)" -ForegroundColor Green
} catch {
    Write-Host "  [FAIL] Backend health check failed: $_" -ForegroundColor Red
    exit 1
}

Write-Host ""

# Test 2: Meta-Learning Dashboard
Write-Host "Test 2: Meta-Learning Dashboard (Task 1)" -ForegroundColor Green
python scripts/test_meta_learning_dashboard.py

Write-Host ""

# Test 3: Request Traceability
Write-Host "Test 3: Request Traceability (Task 3)" -ForegroundColor Green
python scripts/test_request_traceability.py

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "All tests completed!" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan

