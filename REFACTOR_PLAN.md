# 🏗️ KẾ HOẠCH TÁI CẤU TRÚC STILLME AI

## 📋 **NGUYÊN TẮC THIẾT KẾ**

### **Separation of Concerns**
- **Core AI Framework**: Logic AI cốt lõi, không phụ thuộc platform
- **AgentDev System**: Hệ thống phát triển và sửa lỗi tự động
- **Desktop App**: Ứng dụng desktop độc lập
- **Mobile App**: Ứng dụng mobile độc lập  
- **API Gateway**: Server và API endpoints
- **Documentation**: Tài liệu tập trung

## 🗂️ **CẤU TRÚC THƯ MỤC MỚI**

```
stillme_ai/
├── stillme-core/                    # Core AI Framework
│   ├── __init__.py
│   ├── framework.py                 # Main framework
│   ├── config/                      # Configuration
│   │   ├── __init__.py
│   │   ├── config.py
│   │   └── defaults.py
│   ├── modules/                     # Core modules
│   │   ├── __init__.py
│   │   ├── emotionsense_v1.py
│   │   ├── market_intel.py
│   │   ├── persona_morph.py
│   │   └── ...
│   ├── adapters/                    # AI provider adapters
│   │   ├── __init__.py
│   │   ├── gpt5_client.py
│   │   └── ollama_client.py
│   ├── common/                      # Common utilities
│   │   ├── __init__.py
│   │   └── ...
│   └── tests/                       # Core tests
│       ├── __init__.py
│       └── ...
│
├── agent-dev/                       # AgentDev System
│   ├── __init__.py
│   ├── core/                        # Core AgentDev
│   │   ├── __init__.py
│   │   ├── agentdev_ultimate.py
│   │   ├── agentdev_honest.py
│   │   ├── agentdev_real_fix.py
│   │   └── agentdev_simple.py
│   ├── validation/                  # Validation system
│   │   ├── __init__.py
│   │   ├── validation_system.py
│   │   └── integration.py
│   ├── tools/                       # AgentDev tools
│   │   ├── __init__.py
│   │   ├── module_tester.py
│   │   └── upgrade.py
│   ├── tests/                       # AgentDev tests
│   │   ├── __init__.py
│   │   ├── test_agentdev_brain.py
│   │   ├── test_agentdev_real.py
│   │   └── test_agentdev_super.py
│   └── docs/                        # AgentDev documentation
│       ├── README.md
│       ├── GUIDE.md
│       └── SYSTEM_REPORT.md
│
├── desktop-app/                     # Desktop Application
│   ├── __init__.py
│   ├── app.py                       # Main desktop app
│   ├── config/                      # Desktop config
│   │   ├── __init__.py
│   │   └── desktop_config.py
│   ├── ui/                          # UI components
│   │   ├── __init__.py
│   │   └── ...
│   ├── build/                       # Build artifacts
│   │   └── ...
│   └── tests/                       # Desktop tests
│       └── ...
│
├── mobile-app/                      # Mobile Application
│   ├── __init__.py
│   ├── platforms/                   # Platform-specific code
│   │   ├── android/
│   │   ├── ios/
│   │   └── shared/
│   ├── src/                         # Source code
│   │   ├── screens/
│   │   ├── services/
│   │   ├── store/
│   │   └── ...
│   ├── config/                      # Mobile config
│   │   ├── app.json
│   │   └── ...
│   └── tests/                       # Mobile tests
│       └── ...
│
├── api-gateway/                     # API Gateway & Server
│   ├── __init__.py
│   ├── server.py                    # Main server
│   ├── api/                         # API endpoints
│   │   ├── __init__.py
│   │   ├── routes/
│   │   └── middleware/
│   ├── gateway/                     # Gateway logic
│   │   ├── __init__.py
│   │   ├── websocket_manager.py
│   │   └── ...
│   ├── config/                      # Server config
│   │   ├── __init__.py
│   │   └── server_config.py
│   └── tests/                       # API tests
│       └── ...
│
├── docs/                            # Documentation
│   ├── README.md                    # Main documentation
│   ├── architecture/                # Architecture docs
│   │   ├── OVERVIEW.md
│   │   ├── ARCHITECTURE_MAP.md
│   │   └── ...
│   ├── guides/                      # User guides
│   │   ├── DEVELOPMENT_GUIDE.md
│   │   ├── MIGRATION_GUIDE.md
│   │   └── ...
│   ├── api/                         # API documentation
│   │   └── ...
│   └── reports/                     # Project reports
│       └── ...
│
├── scripts/                         # Build & deployment scripts
│   ├── build.py
│   ├── deploy.py
│   └── ...
│
├── config/                          # Global configuration
│   ├── requirements.txt
│   ├── pyproject.toml
│   ├── pyrightconfig.json
│   └── ...
│
├── data/                            # Data storage
│   ├── logs/
│   ├── cache/
│   ├── metrics/
│   └── ...
│
└── tests/                           # Integration tests
    ├── __init__.py
    ├── integration_test.py
    ├── comprehensive_system_test.py
    └── ...
```

## 🎯 **CHIẾN LƯỢC THỰC HIỆN**

### **Phase 1: Tách AgentDev System** (Ưu tiên cao)
1. Tạo thư mục `agent-dev/`
2. Di chuyển tất cả file `agentdev_*.py`
3. Di chuyển test files liên quan
4. Sửa import paths
5. Test AgentDev functionality

### **Phase 2: Tách StillMe Core** (Ưu tiên cao)
1. Tạo thư mục `stillme-core/`
2. Di chuyển `stillme_core/` → `stillme-core/`
3. Di chuyển `modules/` → `stillme-core/modules/`
4. Di chuyển `framework.py` → `stillme-core/`
5. Sửa import paths
6. Test core functionality

### **Phase 3: Tách Platform Apps** (Ưu tiên trung bình)
1. Tạo thư mục `desktop-app/`
2. Tạo thư mục `mobile-app/`
3. Di chuyển platform-specific code
4. Sửa import paths
5. Test platform functionality

### **Phase 4: Tách API Gateway** (Ưu tiên trung bình)
1. Tạo thư mục `api-gateway/`
2. Di chuyển server code
3. Di chuyển gateway logic
4. Sửa import paths
5. Test API functionality

### **Phase 5: Tổ chức Documentation** (Ưu tiên thấp)
1. Tạo thư mục `docs/`
2. Di chuyển tài liệu
3. Cập nhật links
4. Tạo index

## ⚠️ **RỦI RO VÀ BIỆN PHÁP**

### **Rủi ro cao:**
- **Import path breaks**: Sửa từng bước, test ngay
- **Circular dependencies**: Phân tích trước khi di chuyển
- **Platform-specific code**: Kiểm tra dependencies

### **Biện pháp:**
- Backup toàn bộ trước khi bắt đầu
- Thực hiện từng phase nhỏ
- Test sau mỗi bước
- Rollback nếu có lỗi

## 📊 **TIMELINE DỰ KIẾN**

- **Phase 1**: 2-3 giờ (AgentDev)
- **Phase 2**: 3-4 giờ (Core)
- **Phase 3**: 2-3 giờ (Platform)
- **Phase 4**: 2-3 giờ (API)
- **Phase 5**: 1-2 giờ (Docs)

**Tổng thời gian**: 10-15 giờ

## ✅ **CRITERIA THÀNH CÔNG**

1. **Functional**: Tất cả chức năng hoạt động bình thường
2. **Clean**: Cấu trúc rõ ràng, dễ hiểu
3. **Maintainable**: Dễ bảo trì và mở rộng
4. **Testable**: Dễ test từng component
5. **Documented**: Tài liệu đầy đủ và cập nhật
