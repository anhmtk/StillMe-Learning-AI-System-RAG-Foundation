# Capture Backend Logs from Running Process
# This script captures logs from the backend process and saves to file

param(
    [string]$OutputFile = "logs\backend_capture.log",
    [int]$Duration = 30,  # seconds
    [int]$ProcessId = 0
)

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "📝 CAPTURING BACKEND LOGS" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

# Find backend process
if ($ProcessId -eq 0) {
    Write-Host "🔍 Finding backend process..." -ForegroundColor Yellow
    $processes = Get-Process | Where-Object {
        $_.ProcessName -like "*python*" -and 
        $_.CommandLine -like "*start_backend*" -or
        $_.CommandLine -like "*uvicorn*" -or
        $_.CommandLine -like "*fastapi*"
    } -ErrorAction SilentlyContinue
    
    if (-not $processes) {
        # Try to find by port 8000
        $netstat = netstat -ano | Select-String ":8000" | Select-String "LISTENING"
        if ($netstat) {
            $pid = ($netstat -split '\s+')[-1]
            $processes = Get-Process -Id $pid -ErrorAction SilentlyContinue
        }
    }
    
    if ($processes) {
        $ProcessId = $processes[0].Id
        Write-Host "✅ Found backend process: PID $ProcessId" -ForegroundColor Green
    } else {
        Write-Host "❌ Backend process not found!" -ForegroundColor Red
        Write-Host ""
        Write-Host "Please provide Process ID manually:" -ForegroundColor Yellow
        Write-Host "  .\scripts\capture_backend_logs.ps1 -ProcessId <PID>" -ForegroundColor White
        Write-Host ""
        Write-Host "Or find it with:" -ForegroundColor Yellow
        Write-Host "  Get-Process | Where-Object {`$_.ProcessName -like '*python*'}" -ForegroundColor White
        exit 1
    }
}

# Create logs directory
$logDir = Split-Path $OutputFile -Parent
if (-not (Test-Path $logDir)) {
    New-Item -ItemType Directory -Path $logDir -Force | Out-Null
    Write-Host "✅ Created logs directory: $logDir" -ForegroundColor Green
}

Write-Host ""
Write-Host "📊 Capturing logs for $Duration seconds..." -ForegroundColor Yellow
Write-Host "   Output: $OutputFile" -ForegroundColor Cyan
Write-Host "   Process ID: $ProcessId" -ForegroundColor Cyan
Write-Host ""
Write-Host "Press Ctrl+C to stop early" -ForegroundColor Gray
Write-Host ""

# Note: PowerShell can't directly capture stdout from another process
# We'll use a different approach - check if there's a way to redirect
# For now, provide instructions

Write-Host "⚠️  Note: PowerShell cannot directly capture stdout from running process." -ForegroundColor Yellow
Write-Host ""
Write-Host "Alternative methods:" -ForegroundColor Cyan
Write-Host ""
Write-Host "Method 1: Restart backend with logging to file" -ForegroundColor White
Write-Host "  python start_backend.py > logs\backend.log 2>&1" -ForegroundColor Gray
Write-Host ""
Write-Host "Method 2: Use Process Monitor (ProcMon) to capture" -ForegroundColor White
Write-Host ""
Write-Host "Method 3: Check console window where backend is running" -ForegroundColor White
Write-Host ""

# Try to get recent events from Event Log (if available)
Write-Host "Checking Windows Event Log for Python errors..." -ForegroundColor Yellow
$events = Get-WinEvent -FilterHashtable @{LogName='Application'; ProviderName='Python'} -MaxEvents 10 -ErrorAction SilentlyContinue
if ($events) {
    Write-Host "Found $($events.Count) Python events:" -ForegroundColor Green
    $events | ForEach-Object {
        Write-Host "  [$($_.TimeCreated)] $($_.Message.Substring(0, [Math]::Min(100, $_.Message.Length)))" -ForegroundColor Gray
    }
} else {
    Write-Host "No Python events found in Event Log" -ForegroundColor Gray
}

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "💡 RECOMMENDED: Restart backend with file logging" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan




