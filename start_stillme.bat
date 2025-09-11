@echo off
echo 🚀 Starting StillMe AI System...
echo ========================================

cd /d "%~dp0"

echo 🚀 Starting StillMe AI Server...
start "StillMe AI Server" python stable_ai_server.py

timeout /t 5 /nobreak >nul

echo 🌐 Starting Gateway Server...
cd stillme_platform\gateway
start "Gateway Server" python simple_main.py

timeout /t 3 /nobreak >nul

echo ✅ StillMe System is running!
echo.
echo 📱 Mobile App: npx react-native run-android
echo 💻 Desktop App: npm start
echo 🌐 Gateway: http://localhost:8000
echo 🤖 AI Server: http://localhost:8769
echo.
echo Press any key to stop all services...
pause >nul

echo 🛑 Stopping services...
taskkill /f /im python.exe >nul 2>&1
echo ✅ Shutdown complete
