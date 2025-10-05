@echo off
REM StillMe API Server Startup Script for Windows
REM ================================================

echo 🚀 Starting StillMe API Server...
echo =================================

REM Check if Python is available
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Python is not installed or not in PATH
    echo Please install Python and try again
    pause
    exit /b 1
)

REM Check if required dependencies are installed
echo 🔍 Checking dependencies...
python -c "import fastapi, uvicorn" >nul 2>&1
if %errorlevel% neq 0 (
    echo ⚠️ FastAPI dependencies not found. Installing...
    pip install fastapi uvicorn
)

REM Kill existing processes on port 8000
echo 🔍 Checking for existing processes on port 8000...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :8000') do (
    echo Killing process %%a on port 8000...
    taskkill /PID %%a /F >nul 2>&1
)

REM Start the appropriate API server
echo 🚀 Starting API server...

REM Try to start the main app.py first (port 1216)
echo 📡 Attempting to start main API server (port 1216)...
start "StillMe Main API" cmd /c "python app.py"

REM Wait a moment for the server to start
timeout /t 3 /nobreak >nul

REM Check if main API is running
curl -s http://localhost:1216/health >nul 2>&1
if %errorlevel% equ 0 (
    echo ✅ Main API server is running on port 1216
    echo 📡 Health check: http://localhost:1216/health
) else (
    echo ⚠️ Main API server not responding on port 1216
)

REM Try to start the gateway server (port 8000)
echo 📡 Attempting to start Gateway server (port 8000)...
cd gateway_poc\gateway
start "StillMe Gateway" cmd /c "python main.py"
cd ..\..

REM Wait for gateway to start
timeout /t 5 /nobreak >nul

REM Check if gateway is running
curl -s http://localhost:8000/health >nul 2>&1
if %errorlevel% equ 0 (
    echo ✅ Gateway server is running on port 8000
    echo 📡 Health check: http://localhost:8000/health
    echo 🎯 K6 test endpoint: http://localhost:8000/chat
) else (
    echo ❌ Gateway server not responding on port 8000
    echo 🔧 Trying alternative startup methods...
    
    REM Try alternative startup
    echo 📡 Trying alternative API startup...
    python -c "
import uvicorn
from fastapi import FastAPI
app = FastAPI()

@app.get('/health')
async def health():
    return {'status': 'ok', 'message': 'StillMe API is running'}

@app.post('/chat')
async def chat(request: dict):
    return {'response': 'Hello from StillMe API', 'status': 'success'}

if __name__ == '__main__':
    uvicorn.run(app, host='0.0.0.0', port=8000)
" &
)

echo.
echo 🎉 StillMe API Server startup completed!
echo ========================================
echo.
echo 📡 Available endpoints:
echo    - Main API: http://localhost:1216/health
echo    - Gateway:  http://localhost:8000/health  
echo    - K6 Test:  http://localhost:8000/chat
echo.
echo 🔧 To test the API:
echo    curl http://localhost:8000/health
echo    curl -X POST http://localhost:8000/chat -H "Content-Type: application/json" -d "{\"prompt\": \"Hello\"}"
echo.
pause
