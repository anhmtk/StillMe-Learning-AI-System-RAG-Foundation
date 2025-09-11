# 🚀 StillMe Communication Channel - Setup Guide

## 📋 Tổng quan

Hướng dẫn setup và chạy hệ thống kênh giao tiếp giữa StillMe Native App và Android APK.

## 🏗️ Kiến trúc đã implement

### ✅ **Hoàn thành:**
1. **StillMe Gateway** - Trung tâm giao tiếp
2. **Mobile App Services** - WebSocket, Notifications, Biometric, Storage
3. **Desktop App Integration** - WebSocket client
4. **Shared Types** - Protocol chuẩn
5. **Integration Bridge** - Cầu nối nội bộ

## 🛠️ Setup Instructions

### 1. **StillMe Gateway Setup**

```bash
# Navigate to gateway directory
cd stillme_platform/gateway

# Install dependencies
pip install -r requirements.txt

# Set environment variables
export SECRET_KEY="your-secret-key-here"
export DATABASE_URL="postgresql+asyncpg://user:password@localhost/stillme_gateway"
export REDIS_URL="redis://localhost:6379"
export STILLME_CORE_URL="http://localhost:8000"

# Start Gateway
uvicorn main:app --host 0.0.0.0 --port 8001 --reload
```

### 2. **Mobile App Setup**

```bash
# Navigate to mobile directory
cd stillme_platform/mobile

# Install dependencies
npm install

# iOS Setup
cd ios && pod install && cd ..

# Android Setup
# Ensure Android SDK is installed and configured

# Start Metro bundler
npm start

# Run on Android
npm run android

# Run on iOS
npm run ios
```

### 3. **Desktop App Setup**

```bash
# Navigate to desktop directory
cd stillme_platform/desktop

# Install dependencies
npm install

# Start development server
npm start

# Build for production
npm run build
```

## 🔧 Configuration

### Gateway Configuration (`stillme_platform/gateway/core/config.py`)

```python
class Settings(BaseSettings):
    # Application
    APP_NAME: str = "StillMe Gateway"
    VERSION: str = "1.0.0"
    DEBUG: bool = False
    HOST: str = "0.0.0.0"
    PORT: int = 8001
    
    # Security
    SECRET_KEY: str  # Required
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # Database
    DATABASE_URL: str  # Required
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379"
    
    # StillMe Integration
    STILLME_CORE_URL: str = "http://localhost:8000"
    STILLME_API_KEY: Optional[str] = None
```

### Mobile App Configuration

```typescript
// stillme_platform/mobile/src/services/websocket.ts
const config = {
  url: 'ws://localhost:8001/ws', // Gateway WebSocket URL
  reconnectInterval: 5000,
  maxReconnectAttempts: 10,
  heartbeatInterval: 30000,
};
```

## 📡 Communication Flow

### 1. **Connection Establishment**
```
Mobile App → Gateway: WebSocket connection
Gateway → Mobile App: Connection accepted + client_id
Mobile App → Gateway: Authentication
Gateway → Mobile App: Auth success
```

### 2. **Command Execution**
```
Mobile App → Gateway: Command message
Gateway → StillMe Core: Process command
StillMe Core → Gateway: Command result
Gateway → Mobile App: Response message
```

### 3. **Real-time Updates**
```
StillMe Core → Gateway: Status/notification
Gateway → All Clients: Broadcast message
Mobile App: Update UI/notifications
```

## 🧪 Testing

### 1. **Test Gateway Health**
```bash
curl http://localhost:8001/api/health/
```

### 2. **Test WebSocket Connection**
```javascript
const ws = new WebSocket('ws://localhost:8001/ws/test-client');
ws.onopen = () => console.log('Connected');
ws.onmessage = (event) => console.log('Message:', event.data);
```

### 3. **Test Mobile App**
- Launch mobile app
- Check WebSocket connection status
- Send test message
- Verify response

## 🔐 Security Features

### 1. **Authentication**
- JWT tokens với expiration
- Biometric authentication (mobile)
- Device fingerprinting

### 2. **Authorization**
- Role-based access control
- API key management
- Rate limiting

### 3. **Data Protection**
- Message encryption (optional)
- Secure WebSocket connections (WSS)
- Local storage encryption

## 📱 Platform Features

### Mobile App:
- ✅ WebSocket real-time communication
- ✅ Push notifications (Firebase)
- ✅ Biometric authentication
- ✅ Offline support
- ✅ Local storage
- ✅ Cross-platform UI (iOS/Android)

### Desktop App:
- ✅ WebSocket client
- ✅ System notifications
- ✅ File handling
- ✅ Auto-updater

### Gateway:
- ✅ WebSocket server
- ✅ Message routing
- ✅ Authentication
- ✅ Rate limiting
- ✅ Health checks

## 🚀 Deployment

### Development:
```bash
# Start all services
./scripts/start-dev.sh
```

### Production:
```bash
# Docker deployment
docker-compose up -d

# Kubernetes deployment
kubectl apply -f k8s/
```

## 🔍 Monitoring

### Health Checks:
- Gateway: `http://localhost:8001/api/health/`
- StillMe Core: `http://localhost:8000/api/health/`

### Logs:
- Gateway: `stillme_platform/gateway/gateway.log`
- Mobile: React Native debugger
- Desktop: Electron dev tools

## 🐛 Troubleshooting

### Common Issues:

1. **WebSocket Connection Failed**
   - Check Gateway is running
   - Verify firewall settings
   - Check network connectivity

2. **Authentication Failed**
   - Verify SECRET_KEY is set
   - Check token expiration
   - Validate credentials

3. **Mobile App Not Connecting**
   - Check Metro bundler is running
   - Verify device/emulator network
   - Check WebSocket URL configuration

4. **StillMe Core Integration Failed**
   - Verify STILLME_CORE_URL
   - Check StillMe Core is running
   - Validate API key

## 📚 API Documentation

### Gateway API:
- Swagger UI: `http://localhost:8001/docs`
- ReDoc: `http://localhost:8001/redoc`

### WebSocket Protocol:
- Endpoint: `ws://localhost:8001/ws/{client_id}`
- Message format: JSON
- Heartbeat: Every 30 seconds

## 🔮 Next Steps

1. **Testing**: Comprehensive end-to-end testing
2. **Performance**: Load testing và optimization
3. **Security**: Penetration testing
4. **Monitoring**: Advanced metrics và alerting
5. **Documentation**: User guides và API docs

---

**Tác giả**: StillMe Development Team  
**Phiên bản**: 1.0.0  
**Cập nhật cuối**: 2024-01-XX
