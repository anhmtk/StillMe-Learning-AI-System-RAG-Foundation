#!/bin/bash

# Build development APK with security features
echo "🔨 Building StillMe Mobile App - Development Flavor"

# Clean previous builds
flutter clean
flutter pub get

# Build development APK
flutter build apk \
  --debug \
  --flavor dev \
  --dart-define=BASE_URL=http://160.191.89.99:21568 \
  --dart-define=FOUNDER_MODE=true \
  --dart-define=FOUNDER_PASSCODE=0000

echo "✅ Development APK built successfully!"
echo "📱 APK location: build/app/outputs/flutter-apk/app-dev-debug.apk"
echo "🔍 Features: HTTP allowed, logging enabled, debug mode"
