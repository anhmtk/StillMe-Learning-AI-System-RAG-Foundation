# PowerShell script for moving files to _attic/ directory
# Supports CSV input and filtering parameters

param(
    [string]$FromCsv = "",
    [int]$ScoreMin = 80,
    [int]$TopN = 200,
    [int]$RelaxedMin = 60,
    [switch]$WhatIf = $false
)

# Create _attic directory if it doesn't exist
if (-not (Test-Path "_attic")) {
    New-Item -ItemType Directory -Path "_attic" -Force
    New-Item -ItemType File -Path "_attic/.gitkeep" -Force
}

# Initialize move log
$moveLog = @()
$timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"

Write-Host "Starting attic move operation..." -ForegroundColor Green
Write-Host "  - Score minimum: $ScoreMin" -ForegroundColor Yellow
Write-Host "  - Relaxed minimum: $RelaxedMin" -ForegroundColor Yellow
Write-Host "  - Top N: $TopN" -ForegroundColor Yellow
Write-Host "  - WhatIf: $WhatIf" -ForegroundColor Yellow

if ($FromCsv -and (Test-Path $FromCsv)) {
    Write-Host "Reading candidates from CSV: $FromCsv" -ForegroundColor Cyan
    
    $candidates = Import-Csv $FromCsv
    $movedCount = 0
    $processedCount = 0
    
    foreach ($candidate in $candidates) {
        if ($processedCount -ge $TopN) {
            break
        }
        
        $filePath = $candidate.path
        $score = [int]$candidate.redundant_score
        $isNearDupe = $candidate.is_near_dupe -eq "True"
        $looksBackup = $candidate.looks_backup -eq "True"
        $inboundImports = [int]$candidate.inbound_imports
        $executedLines = [int]$candidate.executed_lines
        $gitTouches = [int]$candidate.git_touches
        $daysSinceLastChange = [int]$candidate.days_since_last_change
        $isWhitelisted = $candidate.is_whitelisted -eq "True"
        $inRegistry = $candidate.in_registry -eq "True"
        
        # Apply decision rules
        $meetsGeneralCriteria = $score -ge $ScoreMin
        $meetsRelaxedCriteria = $score -ge $RelaxedMin -and ($isNearDupe -or $looksBackup)
        
        # 3-KHÔNG rule
        $threeKhong = ($inboundImports -eq 0 -and $executedLines -eq 0 -and $gitTouches -le 1 -and $daysSinceLastChange -gt 180)
        
        # 2-KHÓA rule (protection)
        $twoKhoa = -not $isWhitelisted -and -not $inRegistry -and -not $filePath.EndsWith("__init__.py")
        
        if (($meetsGeneralCriteria -or $meetsRelaxedCriteria) -and $threeKhong -and $twoKhoa) {
            if (Test-Path $filePath) {
                $destPath = "_attic/$filePath"
                $destDir = Split-Path $destPath -Parent
                
                if (-not (Test-Path $destDir)) {
                    New-Item -ItemType Directory -Path $destDir -Force | Out-Null
                }
                
                if ($WhatIf) {
                    Write-Host "  [WHATIF] Would move: $filePath -> $destPath (score: $score)" -ForegroundColor Yellow
                } else {
                    try {
                        Move-Item -Path $filePath -Destination $destPath -Force
                        Write-Host "  Moved: $filePath (score: $score)" -ForegroundColor Green
                        
                        $moveLog += [PSCustomObject]@{
                            src = $filePath
                            dst = $destPath
                            timestamp = $timestamp
                            score = $score
                            reason = if ($meetsRelaxedCriteria) { "relaxed" } else { "general" }
                        }
                        
                        $movedCount++
                    } catch {
                        Write-Host "  Failed to move: $filePath - $($_.Exception.Message)" -ForegroundColor Red
                    }
                }
                
                $processedCount++
            } else {
                Write-Host "  File not found: $filePath" -ForegroundColor Yellow
            }
        }
    }
    
    Write-Host "Move operation complete:" -ForegroundColor Green
    Write-Host "  - Files processed: $processedCount" -ForegroundColor White
    Write-Host "  - Files moved: $movedCount" -ForegroundColor White
    
    # Save move log
    if ($moveLog.Count -gt 0) {
        $logFile = "artifacts/attic_moves.csv"
        $logDir = Split-Path $logFile -Parent
        if (-not (Test-Path $logDir)) {
            New-Item -ItemType Directory -Path $logDir -Force | Out-Null
        }
        
        $moveLog | Export-Csv -Path $logFile -NoTypeInformation -Append
        Write-Host "  - Move log saved to: $logFile" -ForegroundColor White
    }
    
} else {
    Write-Host "CSV file not found: $FromCsv" -ForegroundColor Red
    Write-Host "Usage: .\attic_move.ps1 -FromCsv path -ScoreMin int -TopN int [-RelaxedMin int] [-WhatIf]" -ForegroundColor Yellow
}

Write-Host "Attic move operation completed!" -ForegroundColor Green
