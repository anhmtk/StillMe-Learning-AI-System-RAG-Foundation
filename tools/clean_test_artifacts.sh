#!/bin/bash
# Clean test artifacts and cache files

echo "🧹 Cleaning test artifacts..."

# Remove pytest cache
rm -rf .pytest_cache || true

# Remove Python cache
find . -type d -name "__pycache__" -exec rm -rf {} + || true
find . -name "*.pyc" -delete || true

# Remove coverage reports
rm -rf reports/coverage || true
rm -rf coverage || true
rm -rf htmlcov || true

# Remove test reports
rm -rf reports/test_report.html || true
rm -rf reports/junit.xml || true

echo "✅ Test artifacts cleaned!"
