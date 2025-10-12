# 🔄 Attic Rollback Script
# Restores files from _attic/ back to their original locations

param(
    [switch]$WhatIf,
    [switch]$Force,
    [string]$MovesLog = "artifacts/attic_moves.csv"
)

# Logging function
function Write-Log {
    param([string]$Message, [string]$Level = "INFO")
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $logMessage = "[$timestamp] [$Level] $Message"
    Write-Host $logMessage
    
    # Also write to log file
    $logFile = "artifacts/attic_rollback.log"
    Add-Content -Path $logFile -Value $logMessage -Encoding UTF8
}

# Function to restore a file from attic
function Restore-FromAttic {
    param(
        [string]$SourcePath,
        [string]$DestinationPath,
        [string]$Reason
    )
    
    if (-not (Test-Path $SourcePath)) {
        Write-Log "Source file not found: $SourcePath" "WARN"
        return $false
    }
    
    $destDir = Split-Path $DestinationPath -Parent
    if (-not (Test-Path $destDir)) {
        if ($WhatIf) {
            Write-Log "WOULD CREATE: Directory $destDir" "INFO"
        } else {
            New-Item -ItemType Directory -Path $destDir -Force | Out-Null
            Write-Log "Created directory: $destDir" "INFO"
        }
    }
    
    if ($WhatIf) {
        Write-Log "WOULD RESTORE: $SourcePath -> $DestinationPath (Reason: $Reason)" "INFO"
        return $true
    } else {
        try {
            Move-Item -Path $SourcePath -Destination $DestinationPath -Force
            Write-Log "Restored: $SourcePath -> $DestinationPath" "INFO"
            return $true
        } catch {
            Write-Log "Error restoring $SourcePath: $($_.Exception.Message)" "ERROR"
            return $false
        }
    }
}

# Main execution
Write-Log "Starting attic rollback operation..."
Write-Log "WhatIf mode: $WhatIf"
Write-Log "Force mode: $Force"

# Check if moves log exists
if (-not (Test-Path $MovesLog)) {
    Write-Log "Moves log not found: $MovesLog" "ERROR"
    Write-Log "Cannot proceed without moves log. Exiting." "ERROR"
    exit 1
}

# Check if _attic directory exists
if (-not (Test-Path "_attic")) {
    Write-Log "_attic directory not found. Nothing to restore." "WARN"
    exit 0
}

Write-Log "Reading moves log: $MovesLog"

try {
    $movesData = Import-Csv -Path $MovesLog
    $restoredCount = 0
    $failedCount = 0
    
    foreach ($move in $movesData) {
        $sourcePath = Join-Path "_attic" $move.path_dst
        $destPath = $move.path_src
        $reason = "Rollback from $($move.timestamp)"
        
        if (Restore-FromAttic -SourcePath $sourcePath -DestinationPath $destPath -Reason $reason) {
            $restoredCount++
        } else {
            $failedCount++
        }
    }
    
    Write-Log "Rollback completed: $restoredCount restored, $failedCount failed"
    
    # If not WhatIf and all files restored successfully, clean up _attic
    if (-not $WhatIf -and $failedCount -eq 0 -and $restoredCount -gt 0) {
        Write-Log "All files restored successfully. Cleaning up _attic directory..."
        Remove-Item -Path "_attic" -Recurse -Force
        Write-Log "_attic directory removed"
    }
    
} catch {
    Write-Log "Error reading moves log: $($_.Exception.Message)" "ERROR"
    exit 1
}

Write-Log "Attic rollback operation completed"