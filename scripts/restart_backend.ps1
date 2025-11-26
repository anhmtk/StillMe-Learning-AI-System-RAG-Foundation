# Restart Backend - Stop and start backend with logging

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "🔄 RESTARTING BACKEND" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

# Stop existing backend
Write-Host "🛑 Stopping existing backend..." -ForegroundColor Yellow
$processes = Get-Process | Where-Object {
    $_.ProcessName -like "*python*"
} | Where-Object {
    try {
        $cmdline = (Get-CimInstance Win32_Process -Filter "ProcessId = $($_.Id)").CommandLine
        $cmdline -like "*start_backend*" -or $cmdline -like "*uvicorn*" -or $cmdline -like "*fastapi*"
    } catch {
        $false
    }
}

if ($processes) {
    $processes | Stop-Process -Force -ErrorAction SilentlyContinue
    Write-Host "✅ Stopped $($processes.Count) backend process(es)" -ForegroundColor Green
    Start-Sleep -Seconds 2
} else {
    Write-Host "ℹ️  No backend process found" -ForegroundColor Gray
}

Write-Host ""
Write-Host "🚀 Starting backend with logging..." -ForegroundColor Yellow
Write-Host ""

# Start with logging
& "$PSScriptRoot\start_backend_with_logging.ps1"

Write-Host ""
Write-Host "✅ Backend restarted!" -ForegroundColor Green
Write-Host ""
Write-Host "💡 Wait 5-10 seconds for backend to fully start, then test:" -ForegroundColor Yellow
Write-Host "   python -c `"import requests; r = requests.post('http://localhost:8000/api/chat/rag', json={'message': 'What is 2+2?', 'use_rag': True}, timeout=30); print(r.json().get('response', '')[:200])`"" -ForegroundColor Gray




