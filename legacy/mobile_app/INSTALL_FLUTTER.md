# Flutter Installation Guide

## 🚀 Cài đặt Flutter SDK

### Bước 1: Download Flutter SDK
1. Truy cập: https://docs.flutter.dev/get-started/install/windows
2. Download Flutter SDK (Windows)
3. Giải nén vào thư mục: `C:\flutter`

### Bước 2: Thêm Flutter vào PATH
1. Mở **System Properties** → **Environment Variables**
2. Trong **System Variables**, tìm và chọn **Path** → **Edit**
3. Thêm: `C:\flutter\bin`
4. Click **OK** để lưu

### Bước 3: Cài đặt Android Studio
1. Download Android Studio: https://developer.android.com/studio
2. Cài đặt với **Android SDK**, **Android SDK Platform-Tools**, **Android SDK Build-Tools**
3. Mở Android Studio → **More Actions** → **SDK Manager**
4. Cài đặt **Android SDK Platform 33** (hoặc mới hơn)

### Bước 4: Cài đặt Android SDK Command-line Tools
1. Trong Android Studio → **SDK Manager** → **SDK Tools**
2. Check **Android SDK Command-line Tools (latest)**
3. Click **Apply** để cài đặt

### Bước 5: Cấu hình Android SDK
1. Tạo biến môi trường **ANDROID_HOME** = `C:\Users\[username]\AppData\Local\Android\Sdk`
2. Thêm vào **Path**:
   - `%ANDROID_HOME%\platform-tools`
   - `%ANDROID_HOME%\tools`
   - `%ANDROID_HOME%\tools\bin`

### Bước 6: Kiểm tra cài đặt
```bash
# Mở Command Prompt mới và chạy:
flutter doctor
```

### Bước 7: Chấp nhận Android licenses
```bash
flutter doctor --android-licenses
```

## 📱 Cài đặt APK Builder

### Option 1: Sử dụng build script
```bash
# Sau khi cài Flutter, chạy:
build_apk.bat
```

### Option 2: Build thủ công
```bash
# Cài dependencies
flutter pub get

# Build APK
flutter build apk --debug --dart-define=BASE_URL=http://160.191.89.99:21568 --dart-define=FOUNDER_MODE=true --dart-define=FOUNDER_PASSCODE=0000
```

## 🔧 Troubleshooting

### Flutter không được nhận diện
- Restart Command Prompt/PowerShell
- Kiểm tra PATH có chứa `C:\flutter\bin`
- Chạy `flutter doctor` để kiểm tra

### Android SDK issues
- Đảm bảo Android Studio đã cài đặt
- Kiểm tra ANDROID_HOME environment variable
- Chạy `flutter doctor --android-licenses`

### Build errors
- Chạy `flutter clean`
- Chạy `flutter pub get`
- Kiểm tra internet connection

## 📋 Requirements

- **Windows 10/11**
- **Flutter SDK 3.10.0+**
- **Android Studio** với Android SDK
- **Java JDK 11+**
- **Internet connection** để download dependencies

## 🎯 Quick Start

1. Cài đặt Flutter theo hướng dẫn trên
2. Chạy `flutter doctor` để kiểm tra
3. Chạy `build_apk.bat` để build APK
4. APK sẽ được tạo tại: `build/app/outputs/flutter-apk/app-debug.apk`

---

**Lưu ý**: Cần cài đặt Flutter SDK trước khi có thể build APK. Hướng dẫn chi tiết tại: https://docs.flutter.dev/get-started/install/windows
