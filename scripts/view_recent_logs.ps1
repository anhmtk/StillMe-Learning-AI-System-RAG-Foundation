# View Recent Backend Logs
# This script shows recent logs from backend log files

param(
    [string]$LogFile = "logs\backend.log",
    [int]$Lines = 100,
    [string]$Filter = ""
)

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "📄 VIEWING RECENT BACKEND LOGS" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

# Check if log file exists
if (-not (Test-Path $LogFile)) {
    Write-Host "❌ Log file not found: $LogFile" -ForegroundColor Red
    Write-Host ""
    Write-Host "Looking for log files..." -ForegroundColor Yellow
    
    $logFiles = Get-ChildItem -Path "logs" -Filter "*.log" -ErrorAction SilentlyContinue
    if ($logFiles) {
        Write-Host "Found log files:" -ForegroundColor Green
        $logFiles | ForEach-Object {
            Write-Host "  - $($_.FullName) ($([math]::Round($_.Length / 1KB, 2)) KB)" -ForegroundColor White
        }
        Write-Host ""
        Write-Host "Usage: .\scripts\view_recent_logs.ps1 -LogFile <path>" -ForegroundColor Yellow
    } else {
        Write-Host "❌ No log files found!" -ForegroundColor Red
        Write-Host ""
        Write-Host "💡 Start backend with logging:" -ForegroundColor Yellow
        Write-Host "   .\scripts\start_backend_with_logging.ps1" -ForegroundColor White
    }
    exit 1
}

# Get file info
$fileInfo = Get-Item $LogFile
$fileSize = [math]::Round($fileInfo.Length / 1MB, 2)
Write-Host "📊 File: $LogFile" -ForegroundColor Cyan
Write-Host "   Size: $fileSize MB" -ForegroundColor Cyan
Write-Host "   Last modified: $($fileInfo.LastWriteTime)" -ForegroundColor Cyan
Write-Host ""

# Read logs
Write-Host "📖 Reading last $Lines lines..." -ForegroundColor Yellow
Write-Host ""

if ($Filter) {
    Write-Host "🔍 Filtering for: $Filter" -ForegroundColor Yellow
    Write-Host ""
    Get-Content $LogFile -Tail $Lines | Select-String -Pattern $Filter | Select-Object -Last 50
} else {
    # Show last N lines
    $content = Get-Content $LogFile -Tail $Lines
    
    # Highlight important patterns
    foreach ($line in $content) {
        if ($line -match "ERROR|CRITICAL") {
            Write-Host $line -ForegroundColor Red
        } elseif ($line -match "WARNING|fallback") {
            Write-Host $line -ForegroundColor Yellow
        } elseif ($line -match "validation.*failed|missing_citation") {
            Write-Host $line -ForegroundColor Magenta
        } elseif ($line -match "LLM.*error|LLM.*failed|API.*error") {
            Write-Host $line -ForegroundColor Red
        } else {
            Write-Host $line -ForegroundColor White
        }
    }
}

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "💡 TIPS" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Filter for specific patterns:" -ForegroundColor Yellow
Write-Host "  .\scripts\view_recent_logs.ps1 -Filter `"fallback|error`"" -ForegroundColor Gray
Write-Host ""
Write-Host "View more lines:" -ForegroundColor Yellow
Write-Host "  .\scripts\view_recent_logs.ps1 -Lines 500" -ForegroundColor Gray
Write-Host ""
Write-Host "Watch logs in real-time:" -ForegroundColor Yellow
Write-Host "  Get-Content $LogFile -Wait -Tail 50" -ForegroundColor Gray

