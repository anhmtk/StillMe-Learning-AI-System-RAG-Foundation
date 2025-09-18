# Quick APK Build Guide

## 🚀 Build APK nhanh (sau khi cài Flutter)

### 1. Cài đặt Flutter
```bash
# Download từ: https://docs.flutter.dev/get-started/install/windows
# Giải nén vào C:\flutter
# Thêm C:\flutter\bin vào PATH
# Restart terminal
```

### 2. Kiểm tra Flutter
```bash
flutter doctor
```

### 3. Build APK
```bash
# Trong thư mục mobile_app:
flutter pub get
flutter build apk --debug --dart-define=BASE_URL=http://160.191.89.99:21568 --dart-define=FOUNDER_MODE=true --dart-define=FOUNDER_PASSCODE=0000
```

### 4. APK Location
```
build/app/outputs/flutter-apk/app-debug.apk
```

## 📱 Install APK
```bash
# Kết nối Android device qua USB
# Enable USB Debugging
adb install build/app/outputs/flutter-apk/app-debug.apk
```

## 🔧 Alternative: Use build script
```bash
# Chạy file build_apk.bat
build_apk.bat
```

---

**APK sẽ có tất cả tính năng:**
- ✅ Chat interface với VPS server
- ✅ Founder Console (passcode: 0000)
- ✅ Telemetry & metrics
- ✅ Quick actions
- ✅ Settings & configuration
