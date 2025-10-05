param([Parameter(Mandatory=$true)][int]$Port)

Write-Host "Looking for processes on port $Port..."
$lines = netstat -ano | findstr ":$Port"
if (-not $lines) { 
    Write-Host "No process found on port $Port"
    exit 0 
}

Write-Host "Found processes on port ${Port}:"
$lines | ForEach-Object { Write-Host "   $_" }

$pids = ($lines -split "\s+")[-1] | Sort-Object -Unique
Write-Host "Killing processes: $($pids -join ', ')"

foreach ($processId in $pids) { 
    try {
        taskkill /PID $processId /F 2>$null | Out-Null
        Write-Host "Killed process $processId"
    } catch {
        Write-Host "Failed to kill process $processId (may already be dead)"
    }
}

Write-Host "All processes on port $Port have been terminated"