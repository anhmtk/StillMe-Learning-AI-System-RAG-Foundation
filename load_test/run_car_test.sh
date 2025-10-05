#!/usr/bin/env bash
set -euo pipefail

echo "🚀 Starting K6 CAR Throughput Test"

# Set environment variables
export CLARIFICATION_API_URL="${CLARIFICATION_API_URL:-http://localhost:8000/chat}"

# Create output directory
mkdir -p reports/k6_car_test

# Run K6 CAR test
echo "📊 Running K6 CAR test with 200/300/400 RPS scenarios..."
k6 run \
  --summary-export="reports/k6_car_test/summary.json" \
  --out json="reports/k6_car_test/results.json" \
  load_test/clarification_car_test.js

echo "✅ K6 CAR test completed"
echo "📁 Results saved to:"
echo "   - reports/k6_car_test/summary.json"
echo "   - reports/k6_car_test/results.json"
