# Manual Trace Test Script (PowerShell)
# Tests traceability with longer timeout and better error handling

$apiBase = "https://stillme-backend-production.up.railway.app"

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "Manual Trace Test (Task 3)" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "API Base: $apiBase" -ForegroundColor Yellow
Write-Host ""

# Test 1: Send chat request (with longer timeout)
Write-Host "Step 1: Sending chat request (may take 30-60s)..." -ForegroundColor Green
try {
    $chatResponse = Invoke-RestMethod -Uri "$apiBase/api/chat/rag" `
        -Method POST `
        -ContentType "application/json" `
        -Body '{"message": "Hi", "user_id": "test_user"}' `
        -TimeoutSec 120
    
    $traceId = $chatResponse.trace_id
    
    if ($traceId) {
        Write-Host "  [PASS] Chat response includes trace_id: $traceId" -ForegroundColor Green
        Write-Host ""
        
        # Test 2: Get trace
        Write-Host "Step 2: Getting trace by ID..." -ForegroundColor Green
        try {
            $trace = Invoke-RestMethod -Uri "$apiBase/api/trace/$traceId" -TimeoutSec 30
            
            Write-Host "  [PASS] Trace retrieved successfully" -ForegroundColor Green
            Write-Host "  - Trace ID: $($trace.trace_id)" -ForegroundColor Cyan
            Write-Host "  - Query: $($trace.query)" -ForegroundColor Cyan
            Write-Host "  - Duration: $($trace.duration_ms)ms" -ForegroundColor Cyan
            Write-Host "  - Stages: $($trace.stages.Keys -join ', ')" -ForegroundColor Cyan
            
            # Show final_response if available
            if ($trace.stages.final_response) {
                Write-Host ""
                Write-Host "  Final Response:" -ForegroundColor Yellow
                $trace.stages.final_response | ConvertTo-Json -Depth 3 | Write-Host
            }
            
            Write-Host ""
            Write-Host "[SUCCESS] Traceability is working!" -ForegroundColor Green
        } catch {
            Write-Host "  [FAIL] Could not retrieve trace: $_" -ForegroundColor Red
            Write-Host "  Trace ID was: $traceId" -ForegroundColor Yellow
        }
    } else {
        Write-Host "  [FAIL] Chat response missing trace_id" -ForegroundColor Red
        Write-Host "  Response keys: $($chatResponse.PSObject.Properties.Name -join ', ')" -ForegroundColor Yellow
    }
} catch {
    Write-Host "  [FAIL] Chat request failed: $_" -ForegroundColor Red
    Write-Host "  This may be due to timeout (LLM processing takes 30-60s+)" -ForegroundColor Yellow
    Write-Host "  💡 Try again or check backend logs" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan

