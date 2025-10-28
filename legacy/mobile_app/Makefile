# StillMe Mobile App Makefile

.PHONY: help install clean build run test apk release

# Default target
help:
	@echo "StillMe Mobile App - Available commands:"
	@echo ""
	@echo "  install     - Install Flutter dependencies"
	@echo "  clean       - Clean build artifacts"
	@echo "  build       - Build the app"
	@echo "  run         - Run on connected device/emulator"
	@echo "  test        - Run tests"
	@echo "  apk         - Build APK (debug)"
	@echo "  release     - Build release APK (unsigned)"
	@echo "  doctor      - Run Flutter doctor"
	@echo "  format      - Format code"
	@echo "  analyze     - Analyze code"
	@echo ""

# Install dependencies
install:
	@echo "📦 Installing Flutter dependencies..."
	flutter pub get
	@echo "✅ Dependencies installed!"

# Clean build artifacts
clean:
	@echo "🧹 Cleaning build artifacts..."
	flutter clean
	flutter pub get
	@echo "✅ Clean completed!"

# Build the app
build:
	@echo "🔨 Building StillMe Mobile App..."
	flutter build apk --debug
	@echo "✅ Build completed!"

# Run on device/emulator
run:
	@echo "🚀 Running StillMe Mobile App..."
	flutter run --debug
	@echo "✅ App running!"

# Run tests
test:
	@echo "🧪 Running tests..."
	flutter test
	@echo "✅ Tests completed!"

# Build debug APK
apk:
	@echo "📱 Building debug APK..."
	flutter build apk --debug
	@echo "✅ APK built: build/app/outputs/flutter-apk/app-debug.apk"

# Build release APK (unsigned)
release:
	@echo "📱 Building release APK (unsigned)..."
	flutter build apk --release
	@echo "✅ Release APK built: build/app/outputs/flutter-apk/app-release.apk"

# Run Flutter doctor
doctor:
	@echo "🩺 Running Flutter doctor..."
	flutter doctor
	@echo "✅ Flutter doctor completed!"

# Format code
format:
	@echo "🎨 Formatting code..."
	flutter format .
	@echo "✅ Code formatted!"

# Analyze code
analyze:
	@echo "🔍 Analyzing code..."
	flutter analyze
	@echo "✅ Code analysis completed!"

# Generate code (for freezed, json_serializable, etc.)
generate:
	@echo "⚡ Generating code..."
	flutter packages pub run build_runner build --delete-conflicting-outputs
	@echo "✅ Code generation completed!"

# Build with custom base URL
build-with-url:
	@echo "🔨 Building with custom base URL..."
	flutter build apk --debug --dart-define=BASE_URL=http://160.191.89.99:21568
	@echo "✅ Build with custom URL completed!"

# Build with founder mode enabled
build-founder:
	@echo "🔨 Building with founder mode enabled..."
	flutter build apk --debug --dart-define=FOUNDER_MODE=true
	@echo "✅ Build with founder mode completed!"

# Build with custom passcode
build-passcode:
	@echo "🔨 Building with custom passcode..."
	flutter build apk --debug --dart-define=FOUNDER_PASSCODE=1234
	@echo "✅ Build with custom passcode completed!"

# Full build with all custom settings
build-full:
	@echo "🔨 Building with all custom settings..."
	flutter build apk --debug \
		--dart-define=BASE_URL=http://160.191.89.99:21568 \
		--dart-define=FOUNDER_MODE=true \
		--dart-define=FOUNDER_PASSCODE=0000
	@echo "✅ Full build completed!"

# Install APK on connected device
install-apk:
	@echo "📱 Installing APK on connected device..."
	adb install build/app/outputs/flutter-apk/app-debug.apk
	@echo "✅ APK installed!"

# Check connected devices
devices:
	@echo "📱 Checking connected devices..."
	flutter devices
	@echo "✅ Device check completed!"

# Run on specific device
run-device:
	@echo "🚀 Running on specific device..."
	flutter run --device-id=$(DEVICE_ID)
	@echo "✅ App running on device!"

# Build and install in one command
build-install:
	@echo "🔨 Building and installing APK..."
	$(MAKE) apk
	$(MAKE) install-apk
	@echo "✅ Build and install completed!"

# Development workflow
dev: clean install generate run

# Production workflow
prod: clean install generate build-full

# Quick test
quick-test:
	@echo "⚡ Quick test..."
	flutter test test/
	@echo "✅ Quick test completed!"

# Full test suite
full-test:
	@echo "🧪 Full test suite..."
	flutter test
	flutter analyze
	flutter format --set-exit-if-changed .
	@echo "✅ Full test suite completed!"
