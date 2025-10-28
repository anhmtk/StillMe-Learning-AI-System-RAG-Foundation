# 🔗 StillMe Communication Channel Architecture

## 📋 Tổng quan

Hệ thống kênh giao tiếp giữa StillMe Native App và Android APK đã được thiết kế và implement hoàn chỉnh với kiến trúc microservices, real-time communication và cross-platform compatibility.

## 🏗️ Kiến trúc tổng thể

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Desktop App   │    │   Mobile App    │    │   Web Client    │
│   (Electron)    │    │  (React Native) │    │   (Browser)     │
└─────────┬───────┘    └─────────┬───────┘    └─────────┬───────┘
          │                      │                      │
          │ WebSocket            │ WebSocket            │ WebSocket
          │ /ws/{client_id}      │ /ws/{client_id}      │ /ws/{client_id}
          │                      │                      │
          └──────────────────────┼──────────────────────┘
                                 │
                    ┌─────────────┴─────────────┐
                    │     StillMe Gateway       │
                    │   (FastAPI + WebSocket)   │
                    └─────────────┬─────────────┘
                                  │
                    ┌─────────────┴─────────────┐
                    │     StillMe Core          │
                    │   (Python Backend)        │
                    └───────────────────────────┘
```

## 🔧 Các thành phần chính

### 1. **StillMe Gateway** (`stillme_platform/gateway/`)
- **FastAPI Server** với WebSocket support
- **Message Protocol** chuẩn hóa cho tất cả communication
- **WebSocket Manager** quản lý connections và routing
- **Authentication & Authorization** với JWT tokens
- **Rate Limiting & Circuit Breakers** cho stability

#### Key Files:
- `main.py` - FastAPI application với WebSocket endpoints
- `core/message_protocol.py` - Message types và validation
- `core/websocket_manager.py` - Connection management
- `core/config.py` - Configuration management

### 2. **Shared Types** (`stillme_platform/shared/types.ts`)
- **Message Types**: COMMAND, RESPONSE, STATUS, NOTIFICATION, HEARTBEAT
- **Device Types**: Desktop, Mobile, Web, Server
- **Connection Types**: WebSocket, HTTP, gRPC
- **User & Preferences**: Cross-platform user management

### 3. **Desktop App** (`stillme_platform/desktop/`)
- **Electron + React** với TypeScript
- **WebSocketService** cho real-time communication
- **Redux Store** cho state management
- **Notification System** với native OS integration

#### Key Features:
- Real-time chat với StillMe AI
- File upload/download
- System notifications
- Auto-update mechanism

### 4. **Mobile App** (`stillme_platform/mobile/`)
- **React Native** với TypeScript
- **Cross-platform services**:
  - WebSocketService - Real-time communication
  - NotificationService - Push notifications (Firebase)
  - BiometricService - Touch ID/Face ID authentication
  - StorageService - Local data persistence

#### Key Features:
- Biometric authentication
- Push notifications
- Offline support
- Cross-platform UI (iOS/Android)

### 5. **Integration Bridge** (`stillme_core/integration_bridge.py`)
- **Internal communication** giữa các components
- **Authentication Manager** với multiple auth levels
- **Message Queue** cho async processing
- **Circuit Breakers** cho fault tolerance

## 📡 Message Protocol

### Message Types:
```typescript
enum MessageType {
  COMMAND = 'command',      // Execute command on StillMe Core
  RESPONSE = 'response',    // Command execution result
  STATUS = 'status',        // System/component status updates
  NOTIFICATION = 'notification', // Push notifications
  SYNC = 'sync',           // Data synchronization
  HEARTBEAT = 'heartbeat', // Connection health check
  ERROR = 'error'          // Error messages
}
```

### Message Structure:
```typescript
interface BaseMessage {
  id: string;              // Unique message ID
  type: MessageType;       // Message type
  timestamp: number;       // Unix timestamp
  source: string;          // Source client/device ID
  target?: string;         // Target client/device ID
  metadata?: Record<string, any>; // Additional data
}
```

## 🔐 Security Features

### 1. **Authentication**
- JWT tokens với expiration
- Biometric authentication (mobile)
- Device fingerprinting
- Session management

### 2. **Authorization**
- Role-based access control
- Permission levels
- API key management
- Rate limiting

### 3. **Data Protection**
- Message encryption (optional)
- Secure WebSocket connections (WSS)
- Local storage encryption
- Privacy controls

## 🚀 Communication Flow

### 1. **Connection Establishment**
```
Client → Gateway: WebSocket connection request
Gateway → Client: Connection accepted + client_id
Client → Gateway: Authentication message
Gateway → Client: Authentication success/failure
Client → Gateway: Heartbeat messages (every 30s)
```

### 2. **Command Execution**
```
Client → Gateway: Command message
Gateway → StillMe Core: Process command
StillMe Core → Gateway: Command result
Gateway → Client: Response message
```

### 3. **Real-time Updates**
```
StillMe Core → Gateway: Status/notification
Gateway → All Clients: Broadcast message
Clients: Update UI/notifications
```

## 📱 Platform-Specific Features

### Desktop App:
- Native OS integration
- System tray support
- File system access
- Auto-updater
- Keyboard shortcuts

### Mobile App:
- Push notifications (Firebase)
- Biometric authentication
- Camera/microphone access
- Offline mode
- Background sync

### Web Client:
- Progressive Web App (PWA)
- Service workers
- Local storage
- Responsive design

## 🔧 Configuration

### Gateway Configuration:
```python
class Settings(BaseSettings):
    gateway_url: str = "ws://localhost:8000/ws"
    stillme_core_url: str = "http://localhost:8001"
    redis_url: str = "redis://localhost:6379"
    jwt_secret: str
    debug: bool = False
```

### Client Configuration:
```typescript
interface AppConfig {
  gateway_url: string;
  stillme_core_url: string;
  api_key?: string;
  debug: boolean;
  auto_update: boolean;
  analytics: boolean;
}
```

## 🧪 Testing & Monitoring

### 1. **Health Checks**
- Gateway health endpoint
- StillMe Core health check
- Database connectivity
- Redis connectivity

### 2. **Metrics & Logging**
- Connection metrics
- Message throughput
- Error rates
- Performance monitoring

### 3. **Testing**
- Unit tests cho tất cả services
- Integration tests cho communication flow
- End-to-end tests cho user scenarios
- Load testing cho scalability

## 🚀 Deployment

### Development:
```bash
# Start Gateway
cd stillme_platform/gateway
uvicorn main:app --reload --port 8000

# Start StillMe Core
cd stillme_core
python main.py

# Start Desktop App
cd stillme_platform/desktop
npm start

# Start Mobile App
cd stillme_platform/mobile
npx react-native run-android
```

### Production:
- Docker containers cho tất cả services
- Kubernetes orchestration
- Load balancers
- SSL/TLS certificates
- Monitoring & logging

## 📈 Scalability

### Horizontal Scaling:
- Multiple Gateway instances
- Load balancer distribution
- Redis clustering
- Database sharding

### Performance Optimization:
- Message compression
- Connection pooling
- Caching strategies
- Async processing

## 🔮 Future Enhancements

1. **gRPC Support** - High-performance binary protocol
2. **GraphQL Integration** - Flexible data querying
3. **WebRTC** - Direct peer-to-peer communication
4. **Edge Computing** - Distributed processing
5. **AI/ML Integration** - Smart routing và optimization

## 📚 Documentation

- API Documentation: `/docs` endpoint
- WebSocket Protocol: `PROTOCOL.md`
- Deployment Guide: `DEPLOYMENT.md`
- Troubleshooting: `TROUBLESHOOTING.md`

---

**Tác giả**: StillMe Development Team  
**Phiên bản**: 1.0.0  
**Cập nhật cuối**: 2024-01-XX
