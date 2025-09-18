#!/bin/bash

# Security scan for secrets in git history and current codebase
echo "🔍 Scanning for secrets in StillMe Mobile App..."

# Check if trufflehog is installed
if ! command -v trufflehog &> /dev/null; then
    echo "⚠️  trufflehog not found. Installing..."
    # Install trufflehog (adjust for your OS)
    # For Windows: choco install trufflehog
    # For macOS: brew install trufflehog
    # For Linux: go install github.com/trufflesecurity/trufflehog/v3@latest
    echo "Please install trufflehog manually: https://github.com/trufflesecurity/trufflehog"
    exit 1
fi

# Scan git history
echo "🔍 Scanning git history for secrets..."
trufflehog git file://. --no-verification

# Scan current files
echo "🔍 Scanning current files for secrets..."
trufflehog filesystem . --no-verification

# Check for common secret patterns
echo "🔍 Checking for common secret patterns..."
grep -r -i "api[_-]key\|secret\|password\|token" --include="*.dart" --include="*.json" --include="*.yaml" --include="*.yml" lib/ assets/ || echo "✅ No obvious secrets found in source files"

# Check APK for secrets (if exists)
if [ -f "build/app/outputs/flutter-apk/app-debug.apk" ]; then
    echo "🔍 Checking APK for secrets..."
    # Extract APK and scan
    unzip -q build/app/outputs/flutter-apk/app-debug.apk -d /tmp/apk_scan
    grep -r -i "api[_-]key\|secret\|password\|token" /tmp/apk_scan/ || echo "✅ No obvious secrets found in APK"
    rm -rf /tmp/apk_scan
fi

echo "✅ Security scan completed!"
echo "⚠️  If any secrets were found, please:"
echo "   1. Remove them from code"
echo "   2. Rotate the compromised keys"
echo "   3. Use git filter-repo to purge from history"
