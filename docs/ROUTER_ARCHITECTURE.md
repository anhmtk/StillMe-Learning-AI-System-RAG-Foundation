# StillMe Router Architecture
## Kiến trúc Router Hệ thống

### **🎯 TỔNG QUAN**
StillMe sử dụng kiến trúc router thống nhất để điều hướng requests đến các AI providers phù hợp.

### **🏗️ KIẾN TRÚC CHÍNH**

#### **1. ProviderRouter (Chính)**
- **File**: `stillme_core/core/provider_router.py`
- **Mục đích**: Router chính cho AI providers
- **Chức năng**: 
  - Gọi Dev Agent Bridge
  - Xử lý HTTP requests
  - Quản lý timeout và retry
  - Hỗ trợ async/sync

#### **2. Router (Wrapper)**
- **File**: `stillme_core/router/__init__.py`
- **Mục đích**: Interface đơn giản cho tests
- **Chức năng**:
  - Wrap IntelligentRouter
  - Validation cơ bản
  - Fallback logic

#### **3. IntelligentRouter (Thông minh)**
- **File**: `stillme_core/core/router/intelligent_router.py`
- **Mục đích**: Router với context awareness
- **Chức năng**:
  - Phân tích request complexity
  - Context-aware routing
  - Learning từ patterns

### **🔄 FLOW ROUTING**

```
User Input → Router → ProviderRouter → AI Provider
     ↓           ↓           ↓
  Validation  Context    HTTP Call
              Analysis
```

### **📋 ROUTING MODES**

#### **Fast Mode (Local AI)**
- **Điều kiện**: Simple greetings, basic questions
- **Provider**: Local AI (Ollama, etc.)
- **Ưu điểm**: Nhanh, không tốn cost

#### **Safe Mode (Cloud AI)**
- **Điều kiện**: Complex questions, technical topics
- **Provider**: Cloud AI (OpenAI, etc.)
- **Ưu điểm**: Chính xác, powerful

### **🧪 TESTING**

#### **Test Files**
- `tests/test_router.py` - Main router tests
- `tests/test_unit_router.py` - Unit tests
- `tests/test_integration_system.py` - Integration tests

#### **Test Router Classes**
- Chỉ dùng trong test environment
- Không được import vào production code

### **❌ ROUTER ĐÃ XÓA (Legacy)**

#### **Đã dọn dẹp:**
- `_attic/app.py.SmartRouter` - Legacy implementation
- `_attic/scripts/*router*` - Development tools
- `_attic/modules/intelligent_router.py` - Old version
- `tests/test_router_fallback.py` - Duplicate test
- `tests/test_router_v9.py` - Old version
- `scripts/benchmark_router.py` - Development tool

### **🚀 SỬ DỤNG**

#### **Trong Dashboard:**
```python
from stillme_core.provider_router import ask_sync

response = ask_sync(
    prompt="Hello",
    mode="fast",  # hoặc "safe"
    system_prompt="You are StillMe AI"
)
```

#### **Trong Tests:**
```python
from stillme_core.router import Router

router = Router(config)
result = router.route({"prompt": "test"})
```

### **🔧 CONFIGURATION**

#### **Environment Variables:**
- `STILLME_DRY_RUN` - Test mode
- `OPENAI_API_KEY` - OpenAI access
- `OLLAMA_BASE_URL` - Local AI endpoint

#### **Router Config:**
```python
config = {
    "models": {
        "local": "llama3.1:8b",
        "cloud": "gpt-4"
    },
    "fallback_enabled": True,
    "timeout": 30.0
}
```

### **📈 MONITORING**

#### **Metrics:**
- Response time
- Success rate
- Fallback usage
- Cost tracking

#### **Logs:**
- Routing decisions
- Provider selection
- Error handling

### **🔄 MAINTENANCE**

#### **Thêm Provider mới:**
1. Update `ProviderRouter`
2. Add config
3. Update tests
4. Update documentation

#### **Thay đổi Logic:**
1. Update `IntelligentRouter`
2. Test thoroughly
3. Update dashboard integration
4. Monitor performance

---

**Lưu ý**: Chỉ sử dụng 3 router chính được liệt kê ở trên. Tất cả router khác đã được dọn dẹp.
