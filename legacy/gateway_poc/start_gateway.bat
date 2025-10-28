@echo off
echo 🚀 Starting StillMe Optimized Gateway
echo =====================================

echo.
echo 📋 Prerequisites Check:
echo.

REM Check if Python is available
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Python not found. Please install Python 3.11+
    pause
    exit /b 1
)
echo ✅ Python found

REM Check if Redis is running
curl -s http://localhost:6379 >nul 2>&1
if %errorlevel% neq 0 (
    echo ⚠️  Redis not running. Starting Redis...
    echo    Please install Redis or use Docker: docker run -d -p 6379:6379 redis:alpine
    echo    Continuing without Redis (caching will be disabled)...
) else (
    echo ✅ Redis is running
)

echo.
echo 🚀 Starting FastAPI Gateway...
echo.

REM Change to gateway directory
cd /d "%~dp0"

REM Install dependencies if needed
if not exist "venv" (
    echo 📦 Creating virtual environment...
    python -m venv venv
)

echo 📦 Activating virtual environment...
call venv\Scripts\activate.bat

echo 📦 Installing dependencies...
pip install -r requirements.txt

echo.
echo 🚀 Starting Gateway on http://localhost:8080
echo    Health Check: http://localhost:8080/health
echo    Metrics: http://localhost:8080/api/metrics
echo.
echo Press Ctrl+C to stop
echo.

REM Start the gateway
python fastapi_gateway.py

pause
