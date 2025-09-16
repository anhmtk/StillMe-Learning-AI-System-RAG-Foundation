@echo off
echo 🚀 Building StillMe AI Mobile App...

echo 📋 Checking Flutter installation...
flutter --version
if %errorlevel% neq 0 (
    echo ❌ Flutter not found! Please install Flutter first.
    echo 📥 Download from: https://flutter.dev/docs/get-started/install
    pause
    exit /b 1
)

cd mobile_app

echo 📦 Getting Flutter dependencies...
flutter pub get
if %errorlevel% neq 0 (
    echo ❌ Failed to get dependencies!
    pause
    exit /b 1
)

echo 🔨 Building APK...
flutter build apk --release
if %errorlevel% neq 0 (
    echo ❌ Failed to build APK!
    pause
    exit /b 1
)

echo ✅ APK built successfully!
echo 📱 APK location: mobile_app\build\app\outputs\flutter-apk\app-release.apk

echo.
echo 📋 Next steps:
echo 1. Connect your phone via USB
echo 2. Enable USB Debugging on your phone
echo 3. Run: flutter install
echo 4. Or copy APK to your phone and install manually

echo.
echo 🎉 Build completed successfully!
pause
