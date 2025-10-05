param(
  [int]$Port = 8000,
  [string]$App = "app:app",
  [switch]$Reload = $true
)

# Kill existing process on port if any
Write-Host "Checking for existing processes on port $Port..."
$existing = netstat -ano | findstr ":$Port"
if ($existing) {
    Write-Host "Found existing process on port $Port, killing..."
    $pids = ($existing -split "\s+")[-1] | Sort-Object -Unique
    foreach ($processId in $pids) { 
        taskkill /PID $processId /F 2>$null | Out-Null 
    }
    Start-Sleep -Seconds 2
}

# Start API server in background
Write-Host "Starting API server on port $Port..."
$cmd = "uvicorn $App --port $Port --host 127.0.0.1"
if ($Reload) {
    $cmd += " --reload"
}
Start-Process -FilePath "cmd" -ArgumentList "/c", "$cmd" -WindowStyle Minimized

# Probe /health/ai until READY (max 20s)
Write-Host "Waiting for API to become ready..."
$max=20; $ok=$false
for ($i=0; $i -lt $max; $i++) {
  try {
    $res = Invoke-WebRequest -Uri "http://127.0.0.1:$Port/health/ai" -TimeoutSec 2 -ErrorAction Stop
    if ($res.StatusCode -eq 200) { 
        $ok=$true
        Write-Host "API READY on :$Port"
        break 
    }
  } catch {
    Write-Host "Attempt $($i+1)/$max - waiting for API..."
  }
  Start-Sleep -Seconds 1
}

if (-not $ok) { 
    Write-Error "API failed to become healthy on :$Port after $max seconds"
    Write-Host "Troubleshooting tips:"
    Write-Host "   - Check if port $Port is already in use: netstat -an | findstr :$Port"
    Write-Host "   - Check if FastAPI dependencies are installed: pip install fastapi uvicorn"
    Write-Host "   - Check if app.py exists and has /health/ai endpoint"
    exit 1 
}

Write-Host "API server is running and healthy!"