# 🚀 **MIGRATION GUIDE: STILLME_CORE → MODULES CHÍNH**

## ⚠️ **QUAN TRỌNG: stillme_core.py ĐÃ BỊ DEPRECATED!**

Module `stillme_core.py` đã bị deprecated và sẽ bị xóa trong phiên bản tương lai.
Hãy migrate sang sử dụng các modules chuyên biệt thay thế.

## 📋 **MIGRATION MAPPING:**

### **1. SecureMemoryManager → modules/secure_memory_manager.py**

#### **❌ OLD CODE (Deprecated):**
```python
from modules.stillme_core import SecureMemoryManager

sm = SecureMemoryManager()
sm.store("key", "value")
value = sm.retrieve("key")
```

#### **✅ NEW CODE (Recommended):**
```python
from modules.secure_memory_manager import SecureMemoryManager

sm = SecureMemoryManager()
await sm.save("key", "value")
value = await sm.load("key")
```

#### **🚀 NEW FEATURES:**
- **256-bit encryption** với Fernet
- **Automatic key rotation** mỗi 30 ngày
- **Backup & recovery system** tự động
- **Performance metrics** tracking
- **Async support** cho I/O operations

### **2. AuditLogger → framework.py logging + modules/ethical_core_system_v1.py**

#### **❌ OLD CODE (Deprecated):**
```python
from modules.stillme_core import AuditLogger

logger = AuditLogger("audit.log")
logger.log("User action")
logger.log_error("Error occurred")
```

#### **✅ NEW CODE (Recommended):**
```python
import logging
from modules.ethical_core_system_v1 import EthicalCoreSystem

# Framework logging
logger = logging.getLogger(__name__)
logger.info("User action")
logger.error("Error occurred")

# Ethics logging
ethics = EthicalCoreSystem()
violation = ethics.validate_content("content to check")
if violation:
    logger.warning(f"Ethics violation: {violation}")
```

#### **🚀 NEW FEATURES:**
- **Structured logging** với multiple handlers
- **Log rotation** tự động
- **Remote logging** support
- **Performance monitoring**
- **Ethics violation tracking**

### **3. EthicsChecker → modules/ethical_core_system_v1.py**

#### **❌ OLD CODE (Deprecated):**
```python
from modules.stillme_core import EthicsChecker

checker = EthicsChecker()
is_valid = checker.check("content to validate")
```

#### **✅ NEW CODE (Recommended):**
```python
from modules.ethical_core_system_v1 import EthicalCoreSystem

ethics = EthicalCoreSystem()
result = ethics.validate_content("content to validate")

if result.is_valid:
    print("Content is ethical")
else:
    print(f"Violation: {result.violation_type}")
    print(f"Severity: {result.severity}")
```

#### **🚀 NEW FEATURES:**
- **AI-powered content analysis**
- **Multiple violation types** (hate speech, violence, etc.)
- **Severity levels** (low, medium, high, critical)
- **Context-aware checking**
- **Vietnamese language support**

## 🔄 **MIGRATION STEPS:**

### **BƯỚC 1: Update Imports**
```python
# ❌ OLD
from modules.stillme_core import SecureMemoryManager, AuditLogger, EthicsChecker

# ✅ NEW
from modules.secure_memory_manager import SecureMemoryManager
from modules.ethical_core_system_v1 import EthicalCoreSystem
import logging
```

### **BƯỚC 2: Update Class Usage**
```python
# ❌ OLD
sm = SecureMemoryManager()
sm.store("key", "value")

# ✅ NEW
sm = SecureMemoryManager()
await sm.save("key", "value")
```

### **BƯỌC 3: Update Method Calls**
```python
# ❌ OLD
logger = AuditLogger()
logger.log("message")

# ✅ NEW
logger = logging.getLogger(__name__)
logger.info("message")
```

## 🧪 **TESTING MIGRATION:**

### **1. Run Deprecation Tests:**
```bash
python -m pytest tests/test_stillme_core.py -v
```

### **2. Verify New Modules:**
```bash
python -c "from modules.secure_memory_manager import SecureMemoryManager; print('✅ OK')"
python -c "from modules.ethical_core_system_v1 import EthicalCoreSystem; print('✅ OK')"
```

### **3. Check Framework Integration:**
```bash
python -c "import framework; print('✅ Framework OK')"
```

## 📊 **BENEFITS OF MIGRATION:**

### **✅ Performance:**
- **Faster operations** với optimized code
- **Better memory management**
- **Async support** cho I/O operations

### **✅ Features:**
- **Enterprise-grade security** với encryption
- **AI-powered content analysis**
- **Advanced logging** với rotation và monitoring

### **✅ Maintainability:**
- **Modular architecture** dễ mở rộng
- **Comprehensive testing** coverage
- **Clear separation** of concerns

### **✅ Future-proof:**
- **Active development** và updates
- **Community support**
- **Best practices** implementation

## 🚨 **DEPRECATION TIMELINE:**

- **Version 1.0**: Module deprecated với warnings
- **Version 1.1**: Warnings trở nên more aggressive
- **Version 2.0**: Module bị xóa hoàn toàn

## 🔧 **SUPPORT:**

Nếu gặp vấn đề trong quá trình migration:

1. **Check documentation** của modules mới
2. **Run tests** để verify functionality
3. **Check framework integration**
4. **Review error logs** và warnings

---

**🎯 Migrate ngay để tận hưởng features mới và tránh compatibility issues!**
