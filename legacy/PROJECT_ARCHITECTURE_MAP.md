# 🗺️ STILLME PROJECT ARCHITECTURE MAP
# 🗺️ BẢN ĐỒ KIẾN TRÚC DỰ ÁN STILLME

## 📋 OVERVIEW / TỔNG QUAN
This document shows the relationships and dependencies between all StillMe project files and modules.
Tài liệu này hiển thị mối quan hệ và phụ thuộc giữa tất cả files và modules của dự án StillMe.

## 🏗️ CORE ARCHITECTURE / KIẾN TRÚC CORE

```
┌─────────────────────────────────────────────────────────────┐
│                    STILLME AI FRAMEWORK                     │
│                 FRAMEWORK AI STILLME                        │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    framework.py                             │
│              Main Framework Entry Point                     │
│              Điểm vào chính của Framework                   │
└─────────────────────────────────────────────────────────────┘
                              │
                    ┌─────────┼─────────┐
                    ▼         ▼         ▼
        ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐
        │   modules/      │ │   config/       │ │   tests/        │
        │   Core Modules  │ │   Configuration │ │   Test Suites   │
        │   Modules Core  │ │   Cấu hình      │ │   Bộ Test       │
        └─────────────────┘ └─────────────────┘ └─────────────────┘
```

## 🔗 FILE RELATIONSHIPS / MỐI QUAN HỆ FILES

### **1. CORE FRAMEWORK / FRAMEWORK CORE**

#### `framework.py` (Main Entry Point)
**Connects to / Kết nối với:**
- `modules/` - All core modules
- `config/framework_config.json` - Configuration
- `stable_ai_server.py` - AI server
- `tests/` - Test suites

**Dependencies / Phụ thuộc:**
- All modules in `modules/` directory
- Configuration files in `config/`
- Logging system

---

### **2. AI SERVER / SERVER AI**

#### `stable_ai_server.py` (AI Server)
**Connects to / Kết nối với:**
- `framework.py` - Core framework integration
- `modules/conversational_core_v1.py` - Conversation handling
- `modules/identity_handler.py` - Identity management
- `modules/ethical_core_system_v1.py` - Ethics validation
- `stillme_platform/gateway/` - Gateway communication

**Dependencies / Phụ thuộc:**
- FastAPI framework
- CircuitBreaker and RetryManager classes
- All AI modules

---

### **3. GATEWAY SYSTEM / HỆ THỐNG GATEWAY**

#### `stillme_platform/gateway/main.py` (Production Gateway)
**Connects to / Kết nối với:**
- `dev_gateway.py` - Development version
- `cors_config.py` - CORS configuration
- `core/` - Core gateway modules
- `api/` - API route handlers
- `services/` - Business logic

#### `stillme_platform/gateway/dev_gateway.py` (Development Gateway)
**Connects to / Kết nối với:**
- `cors_config.py` - CORS configuration
- `stable_ai_server.py` - AI server communication
- `main.py` - Production version reference

#### `stillme_platform/gateway/cors_config.py` (CORS Configuration)
**Connects to / Kết nối với:**
- `main.py` - Production gateway
- `dev_gateway.py` - Development gateway
- `env.example` - Environment template

---

### **4. CORE MODULES / MODULES CORE**

#### `modules/ethical_core_system_v1.py` (Ethics System)
**Connects to / Kết nối với:**
- `config/ethical_rules.json` - Rules configuration
- `framework.py` - Framework integration
- `stable_ai_server.py` - Server integration
- `logs/ethical_violations.log` - Violation logs

#### `modules/identity_handler.py` (Identity Management)
**Connects to / Kết nối với:**
- `config/framework_config.json` - Identity configuration
- `modules/conversational_core_v1.py` - Integration point
- `stable_ai_server.py` - Server integration
- `tests/test_identity_handler.py` - Unit tests

#### `modules/conversational_core_v1.py` (Conversation Core)
**Connects to / Kết nối với:**
- `modules/identity_handler.py` - Identity integration
- `modules/ethical_core_system_v1.py` - Ethics validation
- `framework.py` - Framework integration
- `stable_ai_server.py` - Server integration

---

### **5. CONFIGURATION / CẤU HÌNH**

#### `config/framework_config.json` (Main Configuration)
**Connects to / Kết nối với:**
- `framework.py` - Framework loading
- `modules/identity_handler.py` - Identity settings
- All modules requiring configuration

#### `config/ethical_rules.json` (Ethics Rules)
**Connects to / Kết nối với:**
- `modules/ethical_core_system_v1.py` - Ethics system
- `framework.py` - Framework integration

---

### **6. TESTING / KIỂM THỬ**

#### `tests/test_gateway_architecture.py` (Gateway Tests)
**Connects to / Kết nối với:**
- `stillme_platform/gateway/` - Gateway implementation
- `cors_config.py` - CORS configuration
- `stable_ai_server.py` - AI server

#### `tests/test_identity_handler.py` (Identity Tests)
**Connects to / Kết nối với:**
- `modules/identity_handler.py` - Identity handler
- `config/framework_config.json` - Configuration

---

## 🔄 DATA FLOW / LUỒNG DỮ LIỆU

### **Request Flow / Luồng Yêu cầu:**
```
Client Request → Gateway → AI Server → Framework → Modules → Response
Yêu cầu Client → Gateway → AI Server → Framework → Modules → Phản hồi
```

### **Configuration Flow / Luồng Cấu hình:**
```
framework_config.json → Framework → Modules → Runtime Configuration
Cấu hình Framework → Framework → Modules → Cấu hình Runtime
```

### **Error Handling Flow / Luồng Xử lý Lỗi:**
```
Error → CircuitBreaker → RetryManager → Fallback → Response
Lỗi → CircuitBreaker → RetryManager → Fallback → Phản hồi
```

---

## 📊 DEPENDENCY MATRIX / MA TRẬN PHỤ THUỘC

| File | Depends On | Used By |
|------|------------|---------|
| `framework.py` | `modules/`, `config/` | `stable_ai_server.py` |
| `stable_ai_server.py` | `framework.py`, `modules/` | `gateway/`, `tests/` |
| `gateway/main.py` | `cors_config.py`, `core/` | `dev_gateway.py` |
| `gateway/dev_gateway.py` | `cors_config.py` | `main.py` |
| `modules/identity_handler.py` | `config/framework_config.json` | `conversational_core_v1.py` |
| `modules/ethical_core_system_v1.py` | `config/ethical_rules.json` | `framework.py` |

---

## 🎯 KEY INTEGRATION POINTS / ĐIỂM TÍCH HỢP CHÍNH

1. **Framework ↔ Modules**: Core framework loads and manages all modules
2. **Gateway ↔ AI Server**: Communication between gateway and AI server
3. **Identity ↔ Conversational**: Identity handler integrated into conversation flow
4. **Ethics ↔ All Modules**: Ethics validation across all AI operations
5. **Config ↔ All Components**: Centralized configuration management

---

## 🔧 MAINTENANCE NOTES / GHI CHÚ BẢO TRÌ

- **Gateway**: Use `main.py` for production, `dev_gateway.py` for development
- **Configuration**: Update `framework_config.json` for global changes
- **Testing**: Run `tests/test_gateway_architecture.py` for integration tests
- **Security**: CORS configuration in `cors_config.py` is environment-based
- **Error Handling**: CircuitBreaker and RetryManager in `stable_ai_server.py`
