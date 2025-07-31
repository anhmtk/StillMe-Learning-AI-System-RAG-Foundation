@echo off
echo [INFO] Checking Docker Daemon...
docker info >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Docker daemon is not running. Please start Docker Desktop.
    pause
    exit /b
)

echo [INFO] Starting StillMe container...
docker run --rm -v D:\stillme_ai:/app -w /app stillme_ai python framework.py


pause

