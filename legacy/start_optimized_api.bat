@echo off
setlocal enabledelayedexpansion

echo 🚀 Starting Optimized StillMe API Server

REM Install required packages if not present
echo 📦 Installing required packages...
pip install -q orjson httpx uvloop httptools || echo Some packages may already be installed

REM Navigate to gateway directory
cd gateway_poc\gateway

REM Start optimized server
echo 🔥 Starting optimized server with 4 workers, uvloop, httptools...
python optimized_main.py

echo ✅ Optimized API server started on port 8000
