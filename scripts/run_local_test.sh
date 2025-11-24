#!/bin/bash
# Quick script to run tests against local backend
# Usage: ./scripts/run_local_test.sh

# Set port (default: 8000, can be overridden)
PORT=${STILLME_PORT:-8000}
export STILLME_API_BASE="http://localhost:$PORT"
export STILLME_PORT="$PORT"

echo "🔧 Testing against local backend on port $PORT"
echo "   Make sure backend is running: python start_backend.py"
echo ""

python scripts/test_transparency_and_evidence.py

