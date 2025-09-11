# 🏗️ StillMe Gateway Architecture

## 📋 Tổng quan

StillMe Gateway là trung tâm giao tiếp chính cho hệ thống StillMe multi-platform, cung cấp WebSocket, REST API và message routing.

## 🗂️ File Structure

### **Entry Points:**

#### 1. **`main.py`** - Production Gateway (PRIMARY)
- **Mục đích**: Gateway chính thức cho production
- **Tính năng**: 
  - Full authentication & authorization
  - Database integration (PostgreSQL/SQLite)
  - Redis caching
  - WebSocket manager
  - Message protocol
  - Health checks
  - Rate limiting
- **Port**: 8001 (configurable)
- **Security**: High (CORS restricted, JWT auth)

#### 2. **`dev_gateway.py`** - Development Gateway (SECONDARY)
- **Mục đích**: Gateway đơn giản cho development và testing
- **Tính năng**:
  - Basic WebSocket support
  - Simple message forwarding
  - StillMe AI integration
  - Health checks
- **Port**: 8000 (configurable)
- **Security**: Development mode (CORS permissive)

## 🔧 Configuration

### **Environment Variables:**
```bash
# Production (main.py)
SECRET_KEY=your-secret-key
DATABASE_URL=postgresql://user:pass@localhost/stillme
REDIS_URL=redis://localhost:6379
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:8080

# Development (dev_gateway.py)
STILLME_AI_URL=http://127.0.0.1:2377
DEBUG=true
```

### **CORS Configuration:**
- **Production**: Restricted origins từ environment
- **Development**: Permissive for local development

## 🚀 Usage

### **Production:**
```bash
cd stillme_platform/gateway
uvicorn main:app --host 0.0.0.0 --port 8001
```

### **Development:**
```bash
cd stillme_platform/gateway
uvicorn dev_gateway:app --host 0.0.0.0 --port 8000 --reload
```

## 🔒 Security Considerations

1. **Production Gateway**: Sử dụng `main.py` với full security
2. **Development Gateway**: Chỉ sử dụng `dev_gateway.py` cho local development
3. **CORS**: Production có restricted origins, development có permissive CORS
4. **Authentication**: Production có JWT, development có basic auth

## 📊 Monitoring

- **Health Endpoints**: `/health` và `/api/health`
- **WebSocket Status**: Real-time connection monitoring
- **Logging**: Structured logging với different levels

## 🔄 Migration Notes

- **Từ `simple_main.py`**: File đã được rename thành `dev_gateway.py`
- **Backward Compatibility**: Update scripts để sử dụng `dev_gateway.py`
- **Documentation**: Cập nhật tất cả references
