#!/bin/bash

# Build production APK with security hardening
echo "🔨 Building StillMe Mobile App - Production Flavor"

# Clean previous builds
flutter clean
flutter pub get

# Build production APK with obfuscation
flutter build apk \
  --release \
  --flavor prod \
  --obfuscate \
  --split-debug-info=build/symbols/prod

echo "✅ Production APK built successfully!"
echo "📱 APK location: build/app/outputs/flutter-apk/app-prod-release.apk"
echo "🔒 Features: HTTPS only, no logging, obfuscated, minified"
echo "⚠️  Remember to configure proper release signing!"
