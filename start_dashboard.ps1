# StillMe Dashboard Auto-Start Script
Write-Host "🚀 Starting StillMe Dashboard..." -ForegroundColor Green
Write-Host "================================" -ForegroundColor Green

# Check if dashboard is already running
$portCheck = Get-NetTCPConnection -LocalPort 8529 -ErrorAction SilentlyContinue
if ($portCheck) {
    Write-Host "✅ Dashboard already running on port 8529" -ForegroundColor Yellow
    Write-Host "🌐 Open: http://localhost:8529" -ForegroundColor Cyan
    Read-Host "Press Enter to continue"
    exit 0
}

Write-Host "🔄 Starting dashboard..." -ForegroundColor Blue
try {
    streamlit run dashboards/streamlit/integrated_dashboard.py --server.port 8529 --server.headless true
} catch {
    Write-Host "❌ Error starting dashboard: $_" -ForegroundColor Red
    Read-Host "Press Enter to continue"
}
