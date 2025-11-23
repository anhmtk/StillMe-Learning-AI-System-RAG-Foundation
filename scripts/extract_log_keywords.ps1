<#
.SYNOPSIS
    Extract important log lines from Railway backend logs for analysis
    
.DESCRIPTION
    This script reads Railway backend logs and extracts only the important lines
    related to errors, filtering, citations, rewrite, validation, etc.
    This reduces log size from thousands of lines to ~200 important lines.
    
.PARAMETER LogFile
    Path to the log file (if you saved log from Railway to a file)
    
.PARAMETER FromClipboard
    Read log from clipboard instead of file
    
.PARAMETER OutputFile
    Output file path (default: extracted_log_YYYYMMDD_HHMMSS.txt)
    
.EXAMPLE
    .\scripts\extract_log_keywords.ps1 -LogFile "railway_log.txt"
    
.EXAMPLE
    .\scripts\extract_log_keywords.ps1 -FromClipboard
#>

param(
    [string]$LogFile = "",
    [switch]$FromClipboard = $false,
    [string]$OutputFile = ""
)

# Keywords to search for (case-insensitive)
$keywords = @(
    # Errors
    "ERROR",
    "error",
    "Exception",
    "exception",
    "failed",
    "Failed",
    "FAILED",
    
    # Forbidden terms filter
    "Filtered forbidden",
    "Filtering",
    "Keeping.*trải nghiệm",
    "Keeping.*có trải nghiệm",
    
    # Citations
    "citation",
    "Citation",
    "Removed citation",
    "Re-added citations",
    "Auto-added citation",
    "Missing citation",
    "citation relevance",
    
    # Rewrite process
    "rewrite",
    "rewritten",
    "Rewritten",
    "ALWAYS rewriting",
    "Quality evaluator flagged",
    "Post-processing took",
    
    # Validation
    "Validation failed",
    "identity_violation",
    "anthropomorphic_language",
    "missing_humility",
    
    # Quality evaluation
    "QualityEvaluator",
    "quality_result",
    
    # Entities
    "entities",
    "detected_entities",
    "cannot access local variable.*entities",
    
    # Timeout
    "timeout",
    "timed out",
    "Read timed out",
    
    # Other important
    "Successfully rewrote",
    "Filtered forbidden terms",
    "Citation relevance issues detected"
)

# Read log content
$logContent = @()

if ($FromClipboard) {
    Write-Host "📋 Reading log from clipboard..." -ForegroundColor Cyan
    $logContent = Get-Clipboard -Raw
    if (-not $logContent) {
        Write-Host "❌ Clipboard is empty. Please copy log from Railway first." -ForegroundColor Red
        exit 1
    }
    $logContent = $logContent -split "`r?`n"
} elseif ($LogFile -and (Test-Path $LogFile)) {
    Write-Host "📄 Reading log from file: $LogFile" -ForegroundColor Cyan
    $logContent = Get-Content $LogFile -Encoding UTF8
} else {
    Write-Host "❌ No log file specified or file not found." -ForegroundColor Red
    Write-Host "Usage:" -ForegroundColor Yellow
    Write-Host "  .\scripts\extract_log_keywords.ps1 -LogFile `"railway_log.txt`"" -ForegroundColor Yellow
    Write-Host "  .\scripts\extract_log_keywords.ps1 -FromClipboard" -ForegroundColor Yellow
    exit 1
}

Write-Host "📊 Total log lines: $($logContent.Count)" -ForegroundColor Cyan

# Extract important lines
$extractedLines = @()
$lineCount = 0

foreach ($line in $logContent) {
    $lineCount++
    
    # Check if line contains any keyword
    $matched = $false
    foreach ($keyword in $keywords) {
        if ($line -match $keyword) {
            $matched = $true
            break
        }
    }
    
    if ($matched) {
        $extractedLines += $line
    }
    
    # Progress indicator (suppress output to avoid terminal noise)
    # Only show progress every 5000 lines to reduce terminal output
    if ($lineCount % 5000 -eq 0) {
        Write-Host "  Processed $lineCount lines, found $($extractedLines.Count) important lines..." -ForegroundColor Gray
    }
}

Write-Host "✅ Extracted $($extractedLines.Count) important lines from $($logContent.Count) total lines" -ForegroundColor Green

# Generate output filename if not provided
if (-not $OutputFile) {
    $timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
    $OutputFile = "extracted_log_$timestamp.txt"
}

# Write to output file
$extractedLines | Out-File -FilePath $OutputFile -Encoding UTF8

Write-Host "📝 Saved extracted log to: $OutputFile" -ForegroundColor Green
Write-Host "📋 File size: $([math]::Round((Get-Item $OutputFile).Length / 1KB, 2)) KB" -ForegroundColor Cyan

# Also copy to clipboard for easy sharing
$extractedLines -join "`r`n" | Set-Clipboard
Write-Host "✅ Copied extracted log to clipboard (ready to paste)" -ForegroundColor Green

Write-Host "`n💡 You can now send this file to the AI assistant for analysis!" -ForegroundColor Yellow

