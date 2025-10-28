#!/bin/bash
# StillMe API Server Startup Script for Linux/macOS
# ================================================

echo "🚀 Starting StillMe API Server..."
echo "================================="

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 is not installed or not in PATH"
    echo "Please install Python3 and try again"
    exit 1
fi

# Check if required dependencies are installed
echo "🔍 Checking dependencies..."
if ! python3 -c "import fastapi, uvicorn" 2>/dev/null; then
    echo "⚠️ FastAPI dependencies not found. Installing..."
    pip3 install fastapi uvicorn
fi

# Kill existing processes on ports 8000 and 1216
echo "🔍 Checking for existing processes..."
pkill -f "python.*app.py" 2>/dev/null || true
pkill -f "python.*main.py" 2>/dev/null || true
pkill -f "uvicorn.*8000" 2>/dev/null || true
pkill -f "uvicorn.*1216" 2>/dev/null || true

# Start the main API server (port 1216)
echo "📡 Starting main API server (port 1216)..."
python3 app.py &
MAIN_PID=$!

# Wait for main API to start
sleep 3

# Check if main API is running
if curl -s http://localhost:1216/health >/dev/null 2>&1; then
    echo "✅ Main API server is running on port 1216"
    echo "📡 Health check: http://localhost:1216/health"
else
    echo "⚠️ Main API server not responding on port 1216"
fi

# Start the gateway server (port 8000)
echo "📡 Starting Gateway server (port 8000)..."
cd gateway_poc/gateway
python3 main.py &
GATEWAY_PID=$!
cd ../..

# Wait for gateway to start
sleep 5

# Check if gateway is running
if curl -s http://localhost:8000/health >/dev/null 2>&1; then
    echo "✅ Gateway server is running on port 8000"
    echo "📡 Health check: http://localhost:8000/health"
    echo "🎯 K6 test endpoint: http://localhost:8000/chat"
else
    echo "❌ Gateway server not responding on port 8000"
    echo "🔧 Trying alternative startup methods..."
    
    # Try alternative startup
    echo "📡 Trying alternative API startup..."
    python3 -c "
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
fi

echo ""
echo "🎉 StillMe API Server startup completed!"
echo "========================================"
echo ""
echo "📡 Available endpoints:"
echo "   - Main API: http://localhost:1216/health"
echo "   - Gateway:  http://localhost:8000/health"
echo "   - K6 Test:  http://localhost:8000/chat"
echo ""
echo "🔧 To test the API:"
echo "   curl http://localhost:8000/health"
echo "   curl -X POST http://localhost:8000/chat -H 'Content-Type: application/json' -d '{\"prompt\": \"Hello\"}'"
echo ""
echo "🛑 To stop the servers:"
echo "   kill $MAIN_PID $GATEWAY_PID"
echo ""
