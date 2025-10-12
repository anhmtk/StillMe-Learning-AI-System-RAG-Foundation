# PowerShell script to move files to _attic/ (quarantine)
# Usage: .\attic_move.ps1 [-WhatIf] [-Force]

param(
    [switch]$WhatIf,
    [switch]$Force,
    [string]$RedundancyReport = "artifacts/redundancy_report.csv",
    [string]$FromCsv = "",
    [int]$ScoreMin = 80,
    [int]$TopN = 200
)

# Set error action preference
$ErrorActionPreference = "Stop"

# Function to log messages
function Write-Log {
    param([string]$Message, [string]$Level = "INFO")
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    Write-Host "[$timestamp] [$Level] $Message"
}

# Function to create _attic directory structure
function New-AtticDirectory {
    param([string]$SourcePath)
    
    $relativePath = $SourcePath -replace [regex]::Escape($PWD.Path + "\"), ""
    $atticPath = Join-Path "_attic" $relativePath
    $atticDir = Split-Path $atticPath -Parent
    
    if (-not (Test-Path $atticDir)) {
        New-Item -ItemType Directory -Path $atticDir -Force | Out-Null
        Write-Log "Created directory: $atticDir"
    }
    
    return $atticPath
}

# Function to move file to attic
function Move-ToAttic {
    param(
        [string]$SourcePath,
        [string]$Reason,
        [int]$Score
    )
    
    try {
        if (-not (Test-Path $SourcePath)) {
            Write-Log "File not found: $SourcePath" "WARN"
            return $false
        }
        
        $atticPath = New-AtticDirectory -SourcePath $SourcePath
        
        if ($WhatIf) {
            Write-Log "WOULD MOVE: $SourcePath -> $atticPath (Score: $Score, Reason: $Reason)" "INFO"
            return $true
        }
        
        # Create parent directory in attic
        $atticParent = Split-Path $atticPath -Parent
        if (-not (Test-Path $atticParent)) {
            New-Item -ItemType Directory -Path $atticParent -Force | Out-Null
        }
        
        # Move file
        Move-Item -Path $SourcePath -Destination $atticPath -Force
        Write-Log "MOVED: $SourcePath -> $atticPath (Score: $Score, Reason: $Reason)" "INFO"
        
        # Log to CSV
        $moveRecord = [PSCustomObject]@{
            Timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
            SourcePath = $SourcePath
            AtticPath = $atticPath
            Reason = $Reason
            Score = $Score
            Action = "MOVE"
        }
        
        $csvPath = "artifacts/attic_moves.csv"
        $csvDir = Split-Path $csvPath -Parent
        if (-not (Test-Path $csvDir)) {
            New-Item -ItemType Directory -Path $csvDir -Force | Out-Null
        }
        
        if (-not (Test-Path $csvPath)) {
            $moveRecord | Export-Csv -Path $csvPath -NoTypeInformation
        } else {
            $moveRecord | Export-Csv -Path $csvPath -NoTypeInformation -Append
        }
        
        return $true
        
    } catch {
        Write-Log "Error moving $SourcePath : $($_.Exception.Message)" "ERROR"
        return $false
    }
}

# Function to process backup files
function Process-BackupFiles {
    Write-Log "Processing backup files..."
    
    $backupPatterns = @(
        "*_backup.py",
        "*backup*.py", 
        "*.bak.py",
        "*_old.py",
        "*_copy.py",
        "*_tmp.py",
        "*.py.save",
        "*.py~"
    )
    
    $movedCount = 0
    foreach ($pattern in $backupPatterns) {
        $files = Get-ChildItem -Path . -Recurse -Filter $pattern -File
        foreach ($file in $files) {
            if (Move-ToAttic -SourcePath $file.FullName -Reason "Backup pattern: $pattern" -Score 100) {
                $movedCount++
            }
        }
    }
    
    Write-Log "Moved $movedCount backup files"
}

# Function to process backup directories
function Process-BackupDirectories {
    Write-Log "Processing backup directories..."
    
    $backupDirs = @(
        "backup",
        "backup_legacy", 
        "old",
        ".ipynb_checkpoints",
        "__pycache__"
    )
    
    $movedCount = 0
    foreach ($dirPattern in $backupDirs) {
        $dirs = Get-ChildItem -Path . -Recurse -Directory -Name $dirPattern
        foreach ($dir in $dirs) {
            $fullPath = Join-Path $PWD $dir
            if (Test-Path $fullPath) {
                $atticPath = New-AtticDirectory -SourcePath $fullPath
                
                if ($WhatIf) {
                    Write-Log "WOULD MOVE DIRECTORY: $fullPath -> $atticPath" "INFO"
                } else {
                    try {
                        $atticParent = Split-Path $atticPath -Parent
                        if (-not (Test-Path $atticParent)) {
                            New-Item -ItemType Directory -Path $atticParent -Force | Out-Null
                        }
                        
                        Move-Item -Path $fullPath -Destination $atticPath -Force
                        Write-Log "MOVED DIRECTORY: $fullPath -> $atticPath" "INFO"
                        $movedCount++
                    } catch {
                        Write-Log "Error moving directory $fullPath : $($_.Exception.Message)" "ERROR"
                    }
                }
            }
        }
    }
    
    Write-Log "Moved $movedCount backup directories"
}

# Function to process high-score files from CSV
function Process-HighScoreFiles {
    param([string]$CsvPath, [int]$MinScore = 70, [int]$MaxFiles = 200)
    
    if (-not (Test-Path $CsvPath)) {
        Write-Log "Redundancy report not found: $CsvPath" "WARN"
        return
    }
    
    Write-Log "Processing high-score files from $CsvPath (min score: $MinScore, max files: $MaxFiles)..."
    
    try {
        $csvData = Import-Csv -Path $CsvPath
        $movedCount = 0
        $processedCount = 0
        
        foreach ($row in $csvData) {
            if ($processedCount -ge $MaxFiles) {
                break
            }
            
            $score = [int]$row.redundant_score
            if ($score -ge $MinScore -and $row.is_whitelisted -eq "False") {
                $sourcePath = Join-Path $PWD $row.path
                $reason = "High redundant score: $score"
                
                if (Move-ToAttic -SourcePath $sourcePath -Reason $reason -Score $score) {
                    $movedCount++
                }
                $processedCount++
            }
        }
        
        Write-Log "Processed $processedCount files, moved $movedCount high-score files"
        
    } catch {
        Write-Log "Error processing CSV: $($_.Exception.Message)" "ERROR"
    }
}

# Main execution
Write-Log "Starting attic move operation..."
Write-Log "WhatIf mode: $WhatIf"
Write-Log "Force mode: $Force"

# Create _attic directory
if (-not (Test-Path "_attic")) {
    New-Item -ItemType Directory -Path "_attic" -Force | Out-Null
    Write-Log "Created _attic directory"
}

# Create .gitkeep in _attic
$gitkeepPath = Join-Path "_attic" ".gitkeep"
if (-not (Test-Path $gitkeepPath)) {
    New-Item -ItemType File -Path $gitkeepPath -Force | Out-Null
    Write-Log "Created .gitkeep in _attic"
}

# Process different types of files
if ($FromCsv -ne "") {
    # Use CSV-based processing
    Write-Log "Using CSV-based processing: $FromCsv"
    Process-HighScoreFiles -CsvPath $FromCsv -MinScore $ScoreMin -MaxFiles $TopN
} else {
    # Use legacy processing
    Write-Log "Using legacy processing"
    Process-BackupFiles
    Process-BackupDirectories
    Process-HighScoreFiles -CsvPath $RedundancyReport -MinScore 70
}

Write-Log "Attic move operation completed"

# Summary
if (Test-Path "artifacts/attic_moves.csv") {
    $moves = Import-Csv -Path "artifacts/attic_moves.csv"
    Write-Log "Total files moved: $($moves.Count)"
    
    if ($moves.Count -gt 0) {
        Write-Log "Move log saved to: artifacts/attic_moves.csv"
    }
}
