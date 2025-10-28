#!/usr/bin/env bash
set -euo pipefail

echo "🚀 Starting Optimized StillMe API Server"

# Install required packages if not present
echo "📦 Installing required packages..."
pip install -q orjson httpx uvloop httptools || echo "Some packages may already be installed"

# Navigate to gateway directory
cd gateway_poc/gateway

# Start optimized server
echo "🔥 Starting optimized server with 4 workers, uvloop, httptools..."
python optimized_main.py

echo "✅ Optimized API server started on port 8000"
