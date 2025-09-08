# 📚 PHASE 0 - API DOCUMENTATION

## 🔗 **INTERNAL INTEGRATION BRIDGE API**

### **Base URL**: `http://localhost:8765`

---

## 🔐 **AUTHENTICATION**

### **JWT Token Authentication**
All protected endpoints require a valid JWT token in the Authorization header:

```http
Authorization: Bearer <your_jwt_token>
```

### **Token Generation**
Tokens are generated through the `/auth/login` endpoint and expire after 24 hours.

---

## 📋 **API ENDPOINTS**

### **1. Health Check**

#### **GET /health**
Check the health status of the integration bridge.

**Authentication**: Public  
**Rate Limit**: 100 requests/minute  

**Request:**
```http
GET /health
```

**Response:**
```json
{
  "status": "success",
  "data": {
    "status": "healthy",
    "timestamp": "2025-09-08T10:46:02.035337",
    "active_connections": 5,
    "queue_size": 0
  },
  "timestamp": "2025-09-08T10:46:02.035337",
  "request_time_ms": 12.5
}
```

**Status Codes:**
- `200 OK`: Service is healthy
- `500 Internal Server Error`: Service is unhealthy

---

### **2. Authentication**

#### **POST /auth/login**
Authenticate user and receive JWT token.

**Authentication**: Public  
**Rate Limit**: 10 requests/minute  

**Request:**
```http
POST /auth/login
Content-Type: application/json

{
  "username": "your_username",
  "password": "your_password"
}
```

**Response:**
```json
{
  "status": "success",
  "data": {
    "token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
    "expires": "2025-09-09T10:46:02.035337"
  },
  "timestamp": "2025-09-08T10:46:02.035337",
  "request_time_ms": 45.2
}
```

**Error Response:**
```json
{
  "status": "error",
  "error": "Invalid credentials",
  "timestamp": "2025-09-08T10:46:02.035337"
}
```

**Status Codes:**
- `200 OK`: Authentication successful
- `401 Unauthorized`: Invalid credentials
- `429 Too Many Requests`: Rate limit exceeded

---

### **3. System Metrics**

#### **GET /metrics**
Get system performance metrics and statistics.

**Authentication**: Authenticated  
**Rate Limit**: 60 requests/minute  

**Request:**
```http
GET /metrics
Authorization: Bearer <your_jwt_token>
```

**Response:**
```json
{
  "status": "success",
  "data": {
    "metrics": {
      "request_times": [12.5, 15.2, 8.9, 11.3],
      "error_counts": {
        "RateLimitExceeded": 2,
        "AuthenticationError": 1
      },
      "active_connections": 5,
      "queue_size": 0,
      "endpoints": 3
    }
  },
  "timestamp": "2025-09-08T10:46:02.035337",
  "request_time_ms": 8.7
}
```

**Status Codes:**
- `200 OK`: Metrics retrieved successfully
- `401 Unauthorized`: Authentication required
- `429 Too Many Requests`: Rate limit exceeded

---

## 🔌 **WEBSOCKET API**

### **Connection**
```javascript
const ws = new WebSocket('ws://localhost:8765');
```

### **Message Types**

#### **1. Ping/Pong**
```json
// Client -> Server
{
  "type": "ping"
}

// Server -> Client
{
  "type": "pong",
  "timestamp": "2025-09-08T10:46:02.035337"
}
```

#### **2. Subscribe to Message Types**
```json
// Client -> Server
{
  "type": "subscribe",
  "message_types": ["request", "response", "notification"]
}

// Server -> Client
{
  "type": "subscribed",
  "message_types": ["request", "response", "notification"]
}
```

#### **3. API Request via WebSocket**
```json
// Client -> Server
{
  "type": "request",
  "method": "GET",
  "path": "/health",
  "headers": {
    "Authorization": "Bearer <token>"
  },
  "body": {}
}

// Server -> Client
{
  "type": "response",
  "status": "success",
  "data": {
    "status": "healthy",
    "timestamp": "2025-09-08T10:46:02.035337"
  }
}
```

---

## 📊 **MESSAGE QUEUE API**

### **Message Structure**
```python
{
  "id": "uuid4",
  "type": "request|response|notification|error|heartbeat|authentication|authorization",
  "source": "agentdev",
  "target": "target_module",
  "payload": {
    "data": "any"
  },
  "timestamp": "2025-09-08T10:46:02.035337",
  "auth_level": "public|authenticated|authorized|admin",
  "correlation_id": "optional_correlation_id",
  "retry_count": 0,
  "max_retries": 3,
  "ttl": "optional_ttl"
}
```

### **Publishing Messages**
```python
# Python example
message_id = await bridge.send_message(
    target="stillme_core",
    message_type=MessageType.REQUEST,
    payload={"action": "health_check"},
    auth_level=AuthLevel.AUTHENTICATED
)
```

### **Subscribing to Messages**
```python
# Python example
async def handle_request(message):
    print(f"Received request: {message.payload}")

await bridge.message_queue.subscribe(MessageType.REQUEST, handle_request)
```

---

## 🛡️ **SECURITY**

### **Authentication Levels**
- **PUBLIC**: No authentication required
- **AUTHENTICATED**: Valid JWT token required
- **AUTHORIZED**: Valid JWT token with specific permissions
- **ADMIN**: Valid JWT token with admin permissions

### **Rate Limiting**
Each endpoint has configurable rate limits:
- **Health Check**: 100 requests/minute
- **Login**: 10 requests/minute
- **Metrics**: 60 requests/minute

### **Security Headers**
```http
X-Forwarded-For: client_ip_address
Authorization: Bearer <jwt_token>
Content-Type: application/json
```

---

## ⚠️ **ERROR HANDLING**

### **Error Response Format**
```json
{
  "status": "error",
  "error": "Error message description",
  "timestamp": "2025-09-08T10:46:02.035337"
}
```

### **Common Error Codes**
- **400 Bad Request**: Invalid request format
- **401 Unauthorized**: Authentication required or invalid
- **403 Forbidden**: Insufficient permissions
- **404 Not Found**: Endpoint not found
- **429 Too Many Requests**: Rate limit exceeded
- **500 Internal Server Error**: Server error

---

## 🔄 **CIRCUIT BREAKER**

### **Circuit Breaker States**
- **CLOSED**: Normal operation
- **OPEN**: Circuit is open, requests are blocked
- **HALF_OPEN**: Testing if service is back online

### **Configuration**
```python
circuit_breaker_config = {
    "threshold": 5,  # Number of failures before opening
    "timeout": "1 minute",  # Time before attempting reset
    "monitoring_window": "5 minutes"  # Time window for failure counting
}
```

---

## 📈 **MONITORING & METRICS**

### **Available Metrics**
- **Request Times**: Response time distribution
- **Error Counts**: Error type and frequency
- **Active Connections**: Current WebSocket connections
- **Queue Size**: Message queue depth
- **Endpoint Count**: Number of registered endpoints
- **Circuit Breakers**: Circuit breaker states

### **Performance Targets**
- **API Response Time**: <50ms (P95)
- **WebSocket Latency**: <10ms
- **Authentication Time**: <5ms
- **Rate Limit Check**: <1ms

---

## 🧪 **TESTING**

### **Test Endpoints**
```bash
# Health check
curl -X GET http://localhost:8765/health

# Login
curl -X POST http://localhost:8765/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "test", "password": "test"}'

# Metrics (with token)
curl -X GET http://localhost:8765/metrics \
  -H "Authorization: Bearer <your_token>"
```

### **WebSocket Testing**
```javascript
// Browser console
const ws = new WebSocket('ws://localhost:8765');
ws.onopen = () => {
  ws.send(JSON.stringify({type: 'ping'}));
};
ws.onmessage = (event) => {
  console.log('Received:', JSON.parse(event.data));
};
```

---

## 📚 **SDK EXAMPLES**

### **Python SDK**
```python
from stillme_core.integration_bridge import IntegrationBridge

# Initialize bridge
bridge = IntegrationBridge()
await bridge.start()

# Make API request
response = await bridge.handle_request(
    method="GET",
    path="/health",
    headers={}
)

# Send message
message_id = await bridge.send_message(
    target="stillme_core",
    message_type=MessageType.REQUEST,
    payload={"action": "test"}
)

# Stop bridge
await bridge.stop()
```

### **JavaScript SDK**
```javascript
// WebSocket connection
const ws = new WebSocket('ws://localhost:8765');

// Send ping
ws.send(JSON.stringify({type: 'ping'}));

// Subscribe to messages
ws.send(JSON.stringify({
  type: 'subscribe',
  message_types: ['request', 'response']
}));

// Make API request
ws.send(JSON.stringify({
  type: 'request',
  method: 'GET',
  path: '/health',
  headers: {}
}));
```

---

## 🔧 **CONFIGURATION**

### **Environment Variables**
```bash
# Bridge configuration
INTEGRATION_BRIDGE_HOST=localhost
INTEGRATION_BRIDGE_PORT=8765
INTEGRATION_BRIDGE_SECRET_KEY=your_secret_key

# Rate limiting
DEFAULT_RATE_LIMIT=100
LOGIN_RATE_LIMIT=10
METRICS_RATE_LIMIT=60

# Circuit breaker
CIRCUIT_BREAKER_THRESHOLD=5
CIRCUIT_BREAKER_TIMEOUT=60

# Monitoring
METRICS_COLLECTION_INTERVAL=30
CLEANUP_INTERVAL=300
```

### **Configuration File**
```json
{
  "bridge": {
    "host": "localhost",
    "port": 8765,
    "secret_key": "auto_generated"
  },
  "rate_limiting": {
    "default": 100,
    "login": 10,
    "metrics": 60
  },
  "circuit_breaker": {
    "threshold": 5,
    "timeout": 60
  },
  "monitoring": {
    "metrics_interval": 30,
    "cleanup_interval": 300
  }
}
```

---

## 📝 **CHANGELOG**

### **Version 1.0.0** (2025-09-08)
- ✅ Initial release
- ✅ RESTful API endpoints
- ✅ WebSocket support
- ✅ JWT authentication
- ✅ Rate limiting
- ✅ Circuit breaker pattern
- ✅ Message queue system
- ✅ Comprehensive testing
- ✅ Complete documentation

---

## 🆘 **SUPPORT**

### **Documentation**
- **API Reference**: This document
- **Architecture Guide**: `PHASE0_INTEGRATION_FOUNDATION_REPORT.md`
- **Testing Guide**: `test_integration_bridge_fixed.py`

### **Troubleshooting**
1. **Connection Issues**: Check host/port configuration
2. **Authentication Errors**: Verify JWT token validity
3. **Rate Limit Errors**: Implement exponential backoff
4. **Circuit Breaker Open**: Wait for timeout period

### **Contact**
- **Technical Issues**: Check logs in `logs/` directory
- **Performance Issues**: Monitor metrics endpoint
- **Security Issues**: Review security assessment report

---

**Documentation Version**: 1.0.0  
**Last Updated**: 2025-09-08  
**Generated By**: AgentDev System  
**Phase**: 0 - Internal Integration Foundation
