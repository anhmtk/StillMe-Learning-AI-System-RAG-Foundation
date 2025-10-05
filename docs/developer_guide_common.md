# 🔧 DEVELOPER GUIDE - COMMON LAYER
# 🔧 HƯỚNG DẪN NHÀ PHÁT TRIỂN - LỚP CHUNG

## 📖 OVERVIEW - TỔNG QUAN

The Common Layer provides shared utilities and functionality across all StillMe modules, reducing code duplication and improving maintainability.

Lớp Chung cung cấp các tiện ích và chức năng dùng chung cho tất cả các modules StillMe, giảm trùng lặp code và cải thiện khả năng bảo trì.

## 🏗️ ARCHITECTURE - KIẾN TRÚC

```
common/
├── __init__.py          # Main exports
├── config.py            # Configuration management
├── logging.py           # Structured logging
├── errors.py            # Error handling
├── retry.py             # Retry mechanisms
├── http.py              # HTTP utilities (planned)
├── io.py                # File I/O helpers (planned)
├── templates.py         # Response templates (planned)
├── metrics.py           # Performance metrics (planned)
└── cache.py             # Caching utilities (planned)
```

## ⚙️ CONFIGURATION MANAGEMENT - QUẢN LÝ CẤU HÌNH

### **Basic Usage - Sử dụng Cơ bản**

```python
from common.config import ConfigManager, load_module_config

# Load module-specific configuration
config = load_module_config("my_module", "config/my_module.json")

# Get configuration values
api_url = config.get("api.url", "http://localhost:8000")
timeout = config.get("api.timeout", 30)

# Set configuration values
config.set("api.timeout", 60)
config.save()
```

### **Advanced Usage - Sử dụng Nâng cao**

```python
from common.config import ConfigManager, StillMeConfig

# Create custom configuration
default_config = {
    "database": {
        "host": "localhost",
        "port": 5432,
        "name": "stillme"
    },
    "features": {
        "enabled": True,
        "max_retries": 3
    }
}

config_manager = ConfigManager("config/custom.json", default_config, "MYAPP_")

# Environment variable override
# MYAPP_DATABASE_HOST=production.db.com
# MYAPP_FEATURES_ENABLED=false

# Get nested values with dot notation
db_host = config_manager.get("database.host")
feature_enabled = config_manager.get("features.enabled")

# Validate required keys
config_manager.validate_required([
    "database.host",
    "database.port",
    "database.name"
])

# Type-safe configuration
max_retries = config_manager.get_with_type("features.max_retries", int, 3)
```

## 📝 STRUCTURED LOGGING - LOGGING CÓ CẤU TRÚC

### **Basic Usage - Sử dụng Cơ bản**

```python
from common.logging import get_module_logger, get_framework_logger

# Get module logger
logger = get_module_logger("my_module")

# Basic logging
logger.info("Module initialized successfully")
logger.warning("Configuration file not found, using defaults")
logger.error("Failed to connect to database")

# Log with context
logger.info("User login successful", user_id="12345", ip="192.168.1.100")
```

### **Advanced Usage - Sử dụng Nâng cao**

```python
from common.logging import StructuredLogger, get_logger

# Create custom logger
logger = get_logger("MyApp.Custom", 
                   log_file="logs/custom.log", 
                   json_format=True,
                   console_output=True)

# Performance logging
logger.log_performance("database_query", 0.245, query="SELECT * FROM users")

# API logging
logger.log_api_call("POST", "/api/users", 201, 0.156, 
                   request_size=1024, response_size=512)

# Security logging
logger.log_security_event("AUTH_FAILURE", "Invalid credentials", 
                         user_id="12345", ip="192.168.1.100")

# Correlation ID for request tracing
with logger.with_correlation_id("req-12345"):
    logger.info("Processing request")
    # All logs in this context will include correlation_id
```

### **JSON vs Standard Format - Định dạng JSON vs Chuẩn**

```python
# JSON format (production)
logger = get_logger("MyApp", json_format=True)
# Output: {"timestamp": "2025-09-11 21:00:00", "level": "INFO", "message": "Hello"}

# Standard format (development)
logger = get_logger("MyApp", json_format=False)
# Output: 2025-09-11 21:00:00 - MyApp - INFO - Hello
```

## ⚠️ ERROR HANDLING - XỬ LÝ LỖI

### **Basic Usage - Sử dụng Cơ bản**

```python
from common.errors import (
    StillMeException, ConfigurationError, ModuleError, 
    APIError, SecurityError, ErrorHandler
)

# Create custom exception
class MyModuleError(StillMeException):
    def __init__(self, message: str, module_name: str = None):
        super().__init__(message, error_code="MY_MODULE_ERROR", 
                        context={"module_name": module_name})

# Raise exception
raise MyModuleError("Module initialization failed", "my_module")

# Handle errors
try:
    risky_operation()
except MyModuleError as e:
    logger.error(f"Module error: {e.message}", error_code=e.error_code)
    return {"error": e.to_dict()}
```

### **Advanced Usage - Sử dụng Nâng cao**

```python
from common.errors import ErrorHandler, ErrorRecovery

# Centralized error handling
error_handler = ErrorHandler(logger)

try:
    result = some_operation()
except Exception as e:
    response = error_handler.handle_error(e, {"operation": "user_login"})
    return response

# Error recovery strategies
def unreliable_api_call():
    # This might fail
    return requests.get("https://unreliable-api.com/data")

# Retry with backoff
result = ErrorRecovery.retry_with_backoff(
    unreliable_api_call, 
    max_retries=3, 
    base_delay=1.0
)

# Fallback response
try:
    data = get_primary_data()
except APIError as e:
    fallback_response = ErrorRecovery.fallback_response(
        e, 
        fallback_data={"message": "Service temporarily unavailable"}
    )
    return fallback_response
```

### **Specific Exception Types - Các Loại Exception Cụ thể**

```python
# Configuration errors
raise ConfigurationError("Invalid API key", config_key="api.key")

# Module errors
raise ModuleError("Module failed to initialize", module_name="database")

# API errors
raise APIError("Service unavailable", status_code=503, endpoint="/api/users")

# Security errors
raise SecurityError("Unauthorized access", security_level="high")

# Validation errors
raise ValidationError("Invalid email format", field="email", value="invalid-email")

# Network errors
raise NetworkError("Connection timeout", url="https://api.example.com", timeout=30)
```

## 🔄 RETRY MECHANISMS - CƠ CHẾ RETRY

### **Basic Usage - Sử dụng Cơ bản**

```python
from common.retry import retry_with_backoff, RetryManager

# Decorator approach
@retry_with_backoff(max_attempts=3, base_delay=1.0)
def unreliable_function():
    # This might fail
    return requests.get("https://api.example.com/data")

# Manual approach
retry_manager = RetryManager()
result = retry_manager.retry_sync(unreliable_function)
```

### **Advanced Usage - Sử dụng Nâng cao**

```python
from common.retry import (
    RetryConfig, CircuitBreaker, CircuitBreakerConfig,
    circuit_breaker, retry_api_call
)

# Custom retry configuration
config = RetryConfig(
    max_attempts=5,
    base_delay=0.5,
    max_delay=30.0,
    exponential_base=2.0,
    jitter=True,
    exceptions=(ConnectionError, TimeoutError)
)

retry_manager = RetryManager(config)

# Circuit breaker pattern
@circuit_breaker(failure_threshold=5, recovery_timeout=60.0)
def external_api_call():
    return requests.get("https://external-api.com/data")

# API-specific retry
@retry_api_call(max_attempts=3, base_delay=1.0)
def call_user_service():
    return requests.get("https://user-service.com/api/users")
```

### **Async Retry - Retry Bất đồng bộ**

```python
import asyncio
from common.retry import RetryManager

async def async_api_call():
    async with aiohttp.ClientSession() as session:
        async with session.get("https://api.example.com/data") as response:
            return await response.json()

# Async retry
retry_manager = RetryManager()
result = await retry_manager.retry_async(async_api_call)
```

## 🧪 TESTING - KIỂM THỬ

### **Testing Common Modules - Kiểm thử Common Modules**

```python
import pytest
from common.config import ConfigManager
from common.logging import StructuredLogger
from common.errors import StillMeException

def test_config_manager():
    config = ConfigManager("test.json", {"key": "value"})
    assert config.get("key") == "value"

def test_logger():
    logger = StructuredLogger("test")
    # Logger should not raise exceptions
    logger.info("test message")

def test_exception():
    error = StillMeException("test error", error_code="TEST_ERROR")
    assert error.error_code == "TEST_ERROR"
    assert "error_id" in error.to_dict()
```

### **Integration Testing - Kiểm thử Tích hợp**

```python
def test_config_and_logging_integration():
    # Load config
    config = ConfigManager("test.json", {"logging": {"level": "DEBUG"}})
    
    # Create logger with config
    log_level = config.get("logging.level", "INFO")
    logger = StructuredLogger("integration_test")
    
    # Should work without errors
    logger.info("Integration test successful")
```

## 📊 PERFORMANCE CONSIDERATIONS - XEM XÉT HIỆU SUẤT

### **Logging Performance - Hiệu suất Logging**

```python
# Good: Use appropriate log levels
logger.debug("Detailed debug info")  # Only in development
logger.info("Important information")  # Production logging
logger.warning("Potential issues")    # Production logging
logger.error("Errors that need attention")  # Production logging

# Good: Batch log operations
logger.info("Processing started", batch_size=1000)
# ... process items ...
logger.info("Processing completed", processed=1000, errors=0)

# Avoid: Excessive logging in loops
for item in items:
    logger.debug(f"Processing item {item.id}")  # Too verbose
```

### **Configuration Performance - Hiệu suất Cấu hình**

```python
# Good: Cache configuration values
class MyModule:
    def __init__(self):
        self.config = load_module_config("my_module")
        self.api_url = self.config.get("api.url")  # Cache once
        self.timeout = self.config.get("api.timeout", 30)  # Cache once
    
    def make_request(self):
        # Use cached values
        return requests.get(self.api_url, timeout=self.timeout)

# Avoid: Loading config repeatedly
def make_request():
    config = load_module_config("my_module")  # Expensive!
    return requests.get(config.get("api.url"))
```

## 🔒 SECURITY CONSIDERATIONS - XEM XÉT BẢO MẬT

### **Logging Security - Bảo mật Logging**

```python
# Good: Sanitize sensitive data
logger.info("User login", user_id="12345")  # OK
logger.info("User login", password="secret")  # BAD!

# Good: Use security logger for sensitive events
from common.logging import get_security_logger
security_logger = get_security_logger()
security_logger.log_security_event("AUTH_FAILURE", "Invalid credentials", 
                                  user_id="12345", ip="192.168.1.100")
```

### **Configuration Security - Bảo mật Cấu hình**

```python
# Good: Use environment variables for secrets
config = ConfigManager("config.json", defaults, "MYAPP_")
# MYAPP_DATABASE_PASSWORD=secret123

# Good: Validate configuration
config.validate_required(["database.host", "database.port"])

# Avoid: Hardcoded secrets
config = {"database": {"password": "hardcoded_secret"}}  # BAD!
```

## 🚀 MIGRATION GUIDE - HƯỚNG DẪN DI CHUYỂN

### **From Old Logging - Từ Logging Cũ**

```python
# Old way
import logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
handler = logging.StreamHandler()
handler.setFormatter(formatter)
logger.addHandler(handler)

# New way
from common.logging import get_module_logger
logger = get_module_logger("my_module")
```

### **From Old Configuration - Từ Cấu hình Cũ**

```python
# Old way
import json
import os

def load_config():
    with open("config.json", "r") as f:
        config = json.load(f)
    # Override with environment variables
    config["api_url"] = os.getenv("API_URL", config["api_url"])
    return config

# New way
from common.config import load_module_config
config = load_module_config("my_module", "config.json")
```

## 📚 BEST PRACTICES - THỰC HÀNH TỐT NHẤT

### **1. Use Appropriate Log Levels - Sử dụng Mức Log Phù hợp**
- `DEBUG`: Detailed information for debugging
- `INFO`: General information about program execution
- `WARNING`: Something unexpected happened, but the program is still working
- `ERROR`: A serious problem occurred
- `CRITICAL`: A very serious error occurred

### **2. Include Context in Logs - Bao gồm Context trong Logs**
```python
# Good
logger.info("User action completed", 
           user_id=user.id, 
           action="login", 
           duration=0.5)

# Bad
logger.info("Action completed")
```

### **3. Use Structured Exceptions - Sử dụng Exception có Cấu trúc**
```python
# Good
raise APIError("Service unavailable", 
              status_code=503, 
              endpoint="/api/users",
              suggested_action="Retry in 5 minutes")

# Bad
raise Exception("API failed")
```

### **4. Implement Proper Retry Logic - Triển khai Logic Retry Phù hợp**
```python
# Good: Specific exceptions and reasonable delays
@retry_with_backoff(
    max_attempts=3, 
    base_delay=1.0,
    exceptions=(ConnectionError, TimeoutError)
)
def api_call():
    return requests.get("https://api.example.com")

# Bad: Retry everything with no delay
@retry_with_backoff(max_attempts=10, base_delay=0)
def api_call():
    return requests.get("https://api.example.com")
```

### **5. Validate Configuration Early - Xác thực Cấu hình Sớm**
```python
# Good: Validate on startup
def initialize_module():
    config = load_module_config("my_module")
    config.validate_required(["api.url", "api.key"])
    # Continue initialization...

# Bad: Validate on every request
def handle_request():
    config = load_module_config("my_module")
    if not config.get("api.url"):
        raise ConfigurationError("Missing API URL")
    # Handle request...
```

## 🔧 TROUBLESHOOTING - KHẮC PHỤC SỰ CỐ

### **Common Issues - Vấn đề Thường gặp**

1. **Import Errors - Lỗi Import**
   ```python
   # Make sure common module is in Python path
   from common.logging import get_module_logger  # Should work
   ```

2. **Configuration Not Loading - Cấu hình Không Tải**
   ```python
   # Check file path and permissions
   config = ConfigManager("config/my_module.json", defaults)
   print(config.to_dict())  # Debug configuration
   ```

3. **Logging Not Working - Logging Không Hoạt động**
   ```python
   # Check log file permissions and directory
   logger = get_module_logger("my_module", log_file="logs/my_module.log")
   logger.info("Test message")
   ```

4. **Retry Not Working - Retry Không Hoạt động**
   ```python
   # Check exception types and retry configuration
   @retry_with_backoff(exceptions=(ValueError,))  # Only retry ValueError
   def my_function():
       raise TypeError("This won't be retried")
   ```

## 📞 SUPPORT - HỖ TRỢ

For questions or issues with the Common Layer, please:

1. Check this documentation first
2. Look at the test files for examples
3. Check the existing module implementations
4. Create an issue with detailed information

Để được hỗ trợ về Common Layer, vui lòng:

1. Kiểm tra tài liệu này trước
2. Xem các file test để có ví dụ
3. Kiểm tra các triển khai module hiện có
4. Tạo issue với thông tin chi tiết

---

**Happy Coding! - Chúc bạn lập trình vui vẻ! 🚀**
