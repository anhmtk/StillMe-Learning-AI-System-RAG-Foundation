#!/bin/bash
# Linux/macOS shell script to run NicheRadar v1.5 tests
# Usage: ./run_tests.sh [unit|integration|e2e|all|quick]

echo "🧪 NicheRadar v1.5 Test Runner"
echo "================================"

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed or not in PATH"
    exit 1
fi

# Check if pytest is available
if ! python3 -m pytest --version &> /dev/null; then
    echo "❌ pytest is not installed. Installing..."
    pip3 install -r requirements-test.txt
    if [ $? -ne 0 ]; then
        echo "❌ Failed to install test dependencies"
        exit 1
    fi
fi

# Check if Node.js is available (for Playwright)
if ! command -v node &> /dev/null; then
    echo "❌ Node.js is not installed or not in PATH"
    exit 1
fi

# Check if Playwright is installed
if ! npx playwright --version &> /dev/null; then
    echo "❌ Playwright is not installed. Installing..."
    npm install
    npx playwright install
    if [ $? -ne 0 ]; then
        echo "❌ Failed to install Playwright"
        exit 1
    fi
fi

# Create reports directory
mkdir -p reports logs

# Parse command line arguments
test_type=${1:-all}

# Run tests based on type
case $test_type in
    "unit")
        echo "🚀 Running unit tests..."
        python3 scripts/run_tests.py --unit
        ;;
    "integration")
        echo "🚀 Running integration tests..."
        python3 scripts/run_tests.py --integration
        ;;
    "e2e")
        echo "🚀 Running E2E tests..."
        python3 scripts/run_tests.py --e2e
        ;;
    "quick")
        echo "🚀 Running quick tests (unit + integration)..."
        python3 scripts/run_tests.py --quick
        ;;
    *)
        echo "🚀 Running all tests with reports..."
        python3 scripts/run_tests.py --all
        ;;
esac

if [ $? -ne 0 ]; then
    echo "❌ Tests failed"
    exit 1
else
    echo "✅ Tests completed successfully"
    echo "📊 Reports available in reports/ directory"
    echo "📋 Test summary: reports/test_summary.json"
fi
