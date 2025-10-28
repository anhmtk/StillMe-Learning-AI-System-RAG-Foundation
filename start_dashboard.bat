@echo off
echo 🚀 Starting StillMe Dashboard...
echo ================================

cd /d "%~dp0"

echo 📋 Checking if dashboard is already running...
netstat -an | findstr :8529 >nul
if %errorlevel% == 0 (
    echo ✅ Dashboard already running on port 8529
    echo 🌐 Open: http://localhost:8529
    pause
    exit /b 0
)

echo 🔄 Starting dashboard...
streamlit run dashboards/streamlit/integrated_dashboard.py --server.port 8529 --server.headless true

echo ❌ Dashboard stopped
pause