# Web dev server (Vite/Next/React...)
Write-Host "🚀 Starting Web development server..."

# Kill existing process on port 3000 if any
$existing = netstat -ano | findstr ":3000"
if ($existing) {
    Write-Host "⚠️  Found existing process on port 3000, killing..."
    $pids = ($existing -split "\s+")[-1] | Sort-Object -Unique
    foreach ($processId in $pids) { 
        taskkill /PID $processId /F 2>$null | Out-Null 
    }
    Start-Sleep -Seconds 2
}

# Start web server in background
Start-Process -FilePath "cmd" -ArgumentList "/c", "npm run dev" -WindowStyle Minimized

# Probe http://localhost:3000
Write-Host "⏳ Waiting for Web server to become ready..."
$max=30; $ok=$false
for ($i=0; $i -lt $max; $i++) {
  try {
    $res = Invoke-WebRequest -Uri "http://127.0.0.1:3000" -TimeoutSec 2 -ErrorAction Stop
    if ($res.StatusCode -ge 200 -and $res.StatusCode -lt 500) { 
        $ok=$true
        Write-Host "✅ WEB READY on :3000"
        break 
    }
  } catch {
    Write-Host "⏳ Attempt $($i+1)/$max - waiting for Web server..."
  }
  Start-Sleep -Seconds 1
}

if (-not $ok) { 
    Write-Error "❌ WEB failed to become healthy on :3000 after $max seconds"
    Write-Host "💡 Troubleshooting tips:"
    Write-Host "   - Check if port 3000 is already in use: netstat -an | findstr :3000"
    Write-Host "   - Check if npm dependencies are installed: npm install"
    Write-Host "   - Check if package.json has 'dev' script"
    exit 1 
}

Write-Host "🎉 Web server is running and healthy!"
