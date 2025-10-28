# StillMe Mobile App

**StillMe Mobile** - Personal AI Assistant với giao diện hiện đại, telemetry chi tiết và Founder Console.

## 🚀 Tính năng chính

### 💬 Chat Interface
- **Bubble chat hiện đại** với avatar, markdown support, code highlighting
- **Quick Actions** với các lệnh nhanh: `/persona`, `/translate`, `/dev route`, `/clear`, `/export`
- **Telemetry strip** hiển thị model, tokens, latency, cost real-time
- **Typing indicator** và smooth animations

### 👑 Founder Console
- **AgentDev Commands**: `/agentdev run <task>`, `/agentdev status`, `/agentdev model <name>`
- **System Switches**: Auto-translate, Safety level, Token cap, Max latency
- **Live Metrics**: Model status, token usage, performance, cost tracking
- **Command Terminal** với history và auto-complete

### 📊 Telemetry & Analytics
- **Real-time metrics**: Model, tokens, latency, cost estimate
- **Session tracking**: Tổng hợp thống kê theo session
- **Performance monitoring**: P50/P95 latency, error rate
- **Cost estimation**: Tracking chi phí theo thời gian thực

### ⚙️ Settings & Configuration
- **Server settings**: Base URL, timeout, retry policy
- **Feature toggles**: Telemetry, auto-translate, founder mode
- **Privacy controls**: Local logging only
- **About information**: Version, build, license

## 🏗️ Kiến trúc

### Clean Architecture
```
lib/
├── core/                 # Core functionality
│   ├── theme/           # App theme & styling
│   ├── models/          # Data models (Freezed)
│   ├── navigation/      # App routing (GoRouter)
│   └── config/          # Configuration management
├── data/                # Data layer
│   ├── repositories/    # Chat repository
│   └── services/        # API service
├── ui/                  # UI layer
│   ├── screens/         # App screens
│   └── widgets/         # Reusable widgets
└── main.dart           # App entry point
```

### State Management
- **Riverpod** cho state management
- **Freezed** cho immutable data models
- **JsonSerializable** cho JSON serialization

### Dependencies
- **Flutter 3.x** với Material 3
- **Dio** cho HTTP requests
- **GoRouter** cho navigation
- **Hive** cho local storage
- **Flutter Markdown** cho message rendering

## 🛠️ Build & Development

### Prerequisites
```bash
# Flutter SDK 3.10.0+
flutter --version

# Android SDK (for APK build)
flutter doctor
```

### Quick Start
```bash
# Clone và setup
cd mobile_app
make install

# Chạy trên device/emulator
make run

# Build APK
make apk
```

### Build Commands

#### Basic Build
```bash
make apk              # Debug APK
make release          # Release APK (unsigned)
make build-install    # Build + Install
```

#### Custom Configuration
```bash
# Build với custom base URL
make build-with-url

# Build với founder mode
make build-founder

# Build với custom passcode
make build-passcode

# Build với tất cả custom settings
make build-full
```

#### Development Workflow
```bash
make dev              # Clean + Install + Generate + Run
make prod             # Clean + Install + Generate + Build
make full-test        # Test + Analyze + Format
```

### Environment Variables

#### Build-time Configuration
```bash
# Custom base URL
--dart-define=BASE_URL=http://your-server:port

# Enable founder mode
--dart-define=FOUNDER_MODE=true

# Custom founder passcode
--dart-define=FOUNDER_PASSCODE=1234
```

#### Runtime Configuration
File: `assets/config/app_config.json`
```json
{
  "api": {
    "baseUrl": "http://160.191.89.99:21568",
    "timeout": 30000,
    "retryAttempts": 3
  },
  "features": {
    "founderMode": false,
    "telemetry": true,
    "autoTranslate": false
  },
  "security": {
    "founderPasscode": "0000"
  }
}
```

## 📱 APK Build & Installation

### Debug APK
```bash
make apk
# Output: build/app/outputs/flutter-apk/app-debug.apk
```

### Release APK (Unsigned)
```bash
make release
# Output: build/app/outputs/flutter-apk/app-release.apk
```

### Installation
```bash
# Install on connected device
make install-apk

# Or manually
adb install build/app/outputs/flutter-apk/app-debug.apk
```

### APK Signing (Production)
```bash
# Generate keystore
keytool -genkey -v -keystore stillme-key.jks -keyalg RSA -keysize 2048 -validity 10000 -alias stillme

# Build signed APK
flutter build apk --release --split-per-abi
```

## 🔧 Configuration

### Server Endpoints
- **Health**: `GET /health` → `{"status": "healthy"}`
- **Chat**: `POST /chat` với body:
  ```json
  {
    "message": "user message",
    "session_id": "uuid",
    "metadata": {
      "persona": "assistant",
      "language": "vi",
      "founder_command": "optional",
      "debug": true
    }
  }
  ```

### Response Format
```json
{
  "text": "AI response",
  "model": "gemma2:2b",
  "usage": {
    "prompt_tokens": 42,
    "completion_tokens": 128,
    "total_tokens": 170
  },
  "latency_ms": 840,
  "cost_estimate_usd": 0.0008,
  "routing": {
    "selected": "gemma2:2b",
    "candidates": ["gemma2:2b", "deepseek-coder-6.7b"]
  },
  "safety": {
    "filtered": false,
    "flags": []
  }
}
```

### Founder Console Commands
- `/agentdev run <task>` - Execute AgentDev task
- `/agentdev status` - Check AgentDev status  
- `/agentdev model <name>` - Set model routing hint
- `:founder` - Open founder console (requires passcode)

## 🎨 UI/UX Features

### Theme
- **Dark mode** mặc định với Material 3
- **Color palette**: Primary #0F172A, Secondary #1E293B, Accent #3B82F6
- **Typography**: Inter font family
- **Animations**: Smooth 60fps transitions

### Chat Interface
- **Message bubbles** với rounded corners và shadows
- **Markdown support** với code highlighting
- **Copy/retry actions** cho từng message
- **Typing indicator** với animated dots
- **Telemetry strip** có thể expand/collapse

### Quick Actions
- **Action sheet** với grid layout
- **Visual icons** cho từng action
- **Command shortcuts** cho power users
- **Context-aware** suggestions

## 🔒 Security & Privacy

### Founder Mode
- **Passcode protection** (default: 0000)
- **Secure storage** cho sensitive data
- **Session timeout** (configurable)
- **Biometric support** (optional)

### Privacy
- **Local logging only** option
- **No data collection** by default
- **Secure API communication**
- **Configurable telemetry**

## 🐛 Troubleshooting

### Common Issues

#### Build Errors
```bash
# Clean và rebuild
make clean
make install
make build
```

#### Connection Issues
```bash
# Test server connection
curl http://160.191.89.99:21568/health

# Check network connectivity
flutter doctor
```

#### APK Installation
```bash
# Enable USB debugging
# Check connected devices
make devices

# Install manually
adb install -r build/app/outputs/flutter-apk/app-debug.apk
```

### Debug Mode
```bash
# Run with verbose logging
flutter run --debug --verbose

# Check logs
flutter logs
```

## 📋 Testing

### Unit Tests
```bash
make test
```

### Integration Tests
```bash
flutter test integration_test/
```

### Manual Testing
1. **Chat functionality**: Gửi tin nhắn, nhận response
2. **Telemetry**: Kiểm tra metrics hiển thị
3. **Founder console**: Test passcode, commands
4. **Settings**: Đổi server URL, test connection
5. **Quick actions**: Test các lệnh nhanh

## 🚀 Deployment

### Development
```bash
make dev              # Local development
make apk              # Debug APK for testing
```

### Production
```bash
make prod             # Production build
make release          # Signed release APK
```

### CI/CD Integration
```yaml
# GitHub Actions example
- name: Build APK
  run: |
    cd mobile_app
    make install
    make release
```

## 📞 Support

### Issues
- **GitHub Issues**: Báo cáo bugs và feature requests
- **Documentation**: Xem README và code comments
- **Community**: Tham gia discussion

### Development
- **Code style**: Flutter/Dart conventions
- **Architecture**: Clean Architecture principles
- **Testing**: Unit + Integration tests
- **Documentation**: Inline comments + README

---

**StillMe Mobile** - Personal AI Assistant với giao diện hiện đại và tính năng mạnh mẽ! 🚀
