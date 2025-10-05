@echo off
echo ========================================
echo StillMe Mobile App - APK Builder
echo ========================================
echo.

REM Check if Flutter is installed
flutter --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Flutter is not installed or not in PATH
    echo Please install Flutter SDK 3.10.0+ and add it to PATH
    pause
    exit /b 1
)

echo ✅ Flutter found
echo.

REM Navigate to mobile_app directory
cd /d "%~dp0"

echo 📦 Installing dependencies...
flutter pub get
if %errorlevel% neq 0 (
    echo ❌ Failed to install dependencies
    pause
    exit /b 1
)

echo ✅ Dependencies installed
echo.

REM Clean previous builds
echo 🧹 Cleaning previous builds...
flutter clean
flutter pub get

echo ✅ Clean completed
echo.

REM Build APK
echo 🔨 Building APK...
echo.
echo Building with VPS endpoint: http://160.191.89.99:21568
echo Founder mode: Enabled
echo Passcode: 0000
echo.

flutter build apk --debug ^
    --dart-define=BASE_URL=http://160.191.89.99:21568 ^
    --dart-define=FOUNDER_MODE=true ^
    --dart-define=FOUNDER_PASSCODE=0000

if %errorlevel% neq 0 (
    echo ❌ APK build failed
    pause
    exit /b 1
)

echo.
echo ✅ APK build completed successfully!
echo.

REM Check if APK file exists
if exist "build\app\outputs\flutter-apk\app-debug.apk" (
    echo 📱 APK Location: build\app\outputs\flutter-apk\app-debug.apk
    
    REM Get file size
    for %%A in ("build\app\outputs\flutter-apk\app-debug.apk") do (
        echo 📊 File Size: %%~zA bytes
    )
    
    echo.
    echo 🚀 Ready to install on Android device!
    echo.
    echo Installation commands:
    echo   adb install build\app\outputs\flutter-apk\app-debug.apk
    echo.
    echo Or use: make install-apk
    echo.
) else (
    echo ❌ APK file not found
    pause
    exit /b 1
)

echo ========================================
echo Build completed successfully!
echo ========================================
pause
