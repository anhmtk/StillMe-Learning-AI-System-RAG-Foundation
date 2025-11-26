# Quick Log Check - PowerShell script to find evaluation errors
# Usage: .\scripts\quick_log_check.ps1 [log_file_path]

param(
    [string]$LogPath = "logs\server.log"
)

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "🔍 QUICK LOG CHECK FOR EVALUATION ISSUES" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

if (-not (Test-Path $LogPath)) {
    Write-Host "❌ Log file not found: $LogPath" -ForegroundColor Red
    Write-Host ""
    Write-Host "Looking for log files..." -ForegroundColor Yellow
    $found = Get-ChildItem -Path "logs" -Filter "*.log" -ErrorAction SilentlyContinue
    if ($found) {
        Write-Host "Found log files:" -ForegroundColor Green
        $found | ForEach-Object { Write-Host "  - $($_.FullName)" }
    }
    exit 1
}

Write-Host "📄 Analyzing: $LogPath" -ForegroundColor Yellow
Write-Host ""

# Get file size
$fileSize = (Get-Item $LogPath).Length / 1MB
Write-Host "📊 File size: $([math]::Round($fileSize, 2)) MB" -ForegroundColor Cyan

# Read last 5000 lines if file is large
$linesToRead = if ($fileSize -gt 10) { 5000 } else { $null }

Write-Host ""
Write-Host "🔍 Searching for patterns..." -ForegroundColor Yellow
Write-Host ""

# Search patterns
$patterns = @{
    "Fallback Messages" = @(
        "fallback.*message",
        "using fallback",
        "StillMe is experiencing a technical issue",
        "cannot provide a good answer"
    )
    "LLM Failures" = @(
        "LLM.*failed",
        "LLM.*error",
        "LLM.*returned.*empty",
        "API.*error",
        "timeout"
    )
    "Validation Failures" = @(
        "validation.*failed",
        "missing_citation",
        "language_mismatch"
    )
    "Empty Responses" = @(
        "empty response",
        "response.*is.*None"
    )
    "Evaluation Requests" = @(
        "evaluation_bot",
        "truthfulqa",
        "citation_rate"
    )
}

$results = @{}

if ($linesToRead) {
    Write-Host "📖 Reading last $linesToRead lines..." -ForegroundColor Yellow
    $content = Get-Content $LogPath -Tail $linesToRead -ErrorAction SilentlyContinue
} else {
    Write-Host "📖 Reading entire file..." -ForegroundColor Yellow
    $content = Get-Content $LogPath -ErrorAction SilentlyContinue
}

foreach ($category in $patterns.Keys) {
    $matches = @()
    foreach ($pattern in $patterns[$category]) {
        $matches += $content | Select-String -Pattern $pattern -CaseSensitive:$false | Select-Object -First 10
    }
    $results[$category] = $matches
}

# Print results
Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "📊 RESULTS" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

foreach ($category in $results.Keys) {
    $count = $results[$category].Count
    if ($count -gt 0) {
        Write-Host "🔍 $category : $count matches" -ForegroundColor Yellow
        Write-Host "-" * 60 -ForegroundColor Gray
        
        $results[$category] | Select-Object -First 5 | ForEach-Object {
            $line = $_.Line
            if ($line.Length -gt 200) { $line = $line.Substring(0, 200) + "..." }
            Write-Host "  $line" -ForegroundColor White
        }
        
        if ($count -gt 5) {
            Write-Host "  ... and $($count - 5) more" -ForegroundColor Gray
        }
        Write-Host ""
    }
}

# Summary
$totalIssues = ($results.Values | Measure-Object -Property Count -Sum).Sum
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "📈 SUMMARY" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "Total issues found: $totalIssues" -ForegroundColor $(if ($totalIssues -gt 0) { "Red" } else { "Green" })
Write-Host ""

if ($totalIssues -eq 0) {
    Write-Host "✅ No obvious issues found!" -ForegroundColor Green
    Write-Host "   Consider checking LLM provider configuration" -ForegroundColor Yellow
} else {
    Write-Host "⚠️  Issues detected. Review patterns above." -ForegroundColor Yellow
    Write-Host ""
    Write-Host "💡 Next steps:" -ForegroundColor Cyan
    Write-Host "   1. Review the patterns above" -ForegroundColor White
    Write-Host "   2. Check LLM API keys and quotas" -ForegroundColor White
    Write-Host "   3. Review validation chain thresholds" -ForegroundColor White
    Write-Host "   4. Run: python scripts/analyze_evaluation_logs.py $LogPath" -ForegroundColor White
}




