# Start Backend with File Logging
# Simple version without emoji to avoid encoding issues

param(
    [string]$LogDir = "logs"
)

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "STARTING BACKEND WITH FILE LOGGING" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

# Create logs directory
if (-not (Test-Path $LogDir)) {
    New-Item -ItemType Directory -Path $LogDir -Force | Out-Null
    Write-Host "[OK] Created logs directory: $LogDir" -ForegroundColor Green
}

# Stop existing backend if running
Write-Host "Stopping existing backend..." -ForegroundColor Yellow
Get-Process | Where-Object {
    $_.ProcessName -like "*python*"
} | Where-Object {
    try {
        $cmdline = (Get-CimInstance Win32_Process -Filter "ProcessId = $($_.Id)").CommandLine
        if ($cmdline) {
            $cmdline -like "*start_backend*" -or $cmdline -like "*uvicorn*"
        } else {
            $false
        }
    } catch {
        $false
    }
} | Stop-Process -Force -ErrorAction SilentlyContinue

Start-Sleep -Seconds 2

# Start backend with logging
$logFile = Join-Path $LogDir "backend.log"
$errorLogFile = Join-Path $LogDir "backend_error.log"

Write-Host ""
Write-Host "Starting backend..." -ForegroundColor Yellow
Write-Host "Log file: $logFile" -ForegroundColor Cyan
Write-Host "Error log: $errorLogFile" -ForegroundColor Cyan
Write-Host ""

# Start process with output redirection
$process = Start-Process -FilePath "python.exe" `
    -ArgumentList "start_backend.py" `
    -RedirectStandardOutput $logFile `
    -RedirectStandardError $errorLogFile `
    -NoNewWindow `
    -PassThru

if ($process) {
    Write-Host "[OK] Backend started with PID: $($process.Id)" -ForegroundColor Green
    Write-Host ""
    Write-Host "Logs are being written to:" -ForegroundColor Cyan
    Write-Host "  - $logFile" -ForegroundColor White
    Write-Host "  - $errorLogFile" -ForegroundColor White
    Write-Host ""
    Write-Host "To view logs in real-time:" -ForegroundColor Yellow
    Write-Host "  Get-Content $logFile -Wait -Tail 50" -ForegroundColor Gray
    Write-Host ""
    Write-Host "To filter for errors:" -ForegroundColor Yellow
    $filterCmd = "Get-Content $logFile -Wait -Tail 50 | Where-Object { `$_ -match 'error|fallback|validation' }"
    Write-Host "  $filterCmd" -ForegroundColor Gray
    Write-Host ""
    
    # Save PID
    $process.Id | Out-File -FilePath (Join-Path $LogDir "backend.pid") -Encoding UTF8 -NoNewline
    Write-Host "[OK] Process ID saved to: $LogDir\backend.pid" -ForegroundColor Green
} else {
    Write-Host "ERROR: Failed to start backend" -ForegroundColor Red
    exit 1
}
