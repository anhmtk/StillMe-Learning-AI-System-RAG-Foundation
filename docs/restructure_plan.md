# 🏗️ StillMe Repository Restructure Plan

**Ngày**: 2025-09-22  
**Mục tiêu**: Dọn dẹp và tái cấu trúc repository để gọn gàng, sạch sẽ  
**Nguyên tắc**: TUYỆT ĐỐI KHÔNG xóa các file quan trọng cho dự án

## 📊 **PHÂN TÍCH HIỆN TRẠNG**

### **Cấu trúc hiện tại:**
- **Root level**: 100+ files (quá nhiều)
- **Mobile apps**: 3 versions (simple, new, platform)
- **Test files**: 18 files ở root + tests/ directory
- **Debug files**: 6 files ở root
- **Backup files**: Nhiều file backup cũ
- **Documentation**: Phân tán, trùng lặp

## 🎯 **KẾ HOẠCH TÁI CẤU TRÚC**

### **PHASE 1: DỌN DẸP AN TOÀN (LOW RISK)**

#### **1.1 Xóa Backup & Development Files**
```bash
# Backup files (có thể tái tạo)
backup_agentdev_1757736199/
stable_ai_server_backup.py
stable_ai_server_clean.py
stable_ai_server_complex.py
stable_ai_server_simple.py
```

#### **1.2 Xóa Test Files ở Root**
```bash
# Test files tạm thời (có trong tests/ directory)
test_*.py (18 files)
debug_*.py (6 files)
```

#### **1.3 Xóa Mobile App Duplicates**
```bash
# Mobile app versions cũ
mobile_app_simple/
mobile_app_new/
# Giữ lại: stillme_platform/mobile/ (current)
```

### **PHASE 2: TỔ CHỨC LẠI CẤU TRÚC**

#### **2.1 Tạo thư mục organized**
```
stillme_ai/
├── 📱 apps/                    # Application entry points
│   ├── desktop/               # Desktop app
│   ├── mobile/                # Current mobile app
│   └── web/                   # Web app (future)
├── 🧠 core/                   # Core framework
│   ├── runtime/               # Runtime modules
│   ├── policies/              # Policy files
│   └── config/                # Configuration
├── 🛠️ tools/                  # Development tools
├── 🧪 tests/                  # All test files
├── 📚 docs/                   # Documentation
└── 📊 reports/                # Reports and analytics
```

#### **2.2 Di chuyển files**
```bash
# Di chuyển desktop app
stillme_desktop_app.py → apps/desktop/

# Di chuyển mobile app
stillme_platform/mobile/ → apps/mobile/

# Di chuyển tools
tools/ → tools/ (giữ nguyên)

# Di chuyển docs
*.md → docs/ (trừ README.md)
```

### **PHASE 3: CONSOLIDATE DOCUMENTATION**

#### **3.1 Merge documentation files**
- Gộp các `*_COMPLETION_REPORT.md` thành `docs/completion_reports.md`
- Gộp các `*_README.md` thành `docs/development_guides.md`
- Tạo `docs/architecture.md` từ các file architecture

## ⚠️ **CÁC FILE TUYỆT ĐỐI KHÔNG ĐƯỢC XÓA**

### **Core Application Files:**
- `app.py` - Main backend server
- `stillme_desktop_app.py` - Main desktop app
- `stillme_platform/` - Current platform
- `policies/` - Policy files
- `runtime/` - Runtime modules
- `config/` - Configuration files
- `.env*` - Environment files
- `requirements.txt` - Dependencies

### **Important Directories:**
- `stillme_core/` - Core framework
- `niche_radar/` - NicheRadar module
- `cache/` - Cache system
- `metrics/` - Metrics system
- `security/` - Security modules
- `tests/` - Test suite
- `tools/` - Development tools

## 🚀 **EXECUTION PLAN**

### **Step 1: Backup Current State**
```bash
git add .
git commit -m "Backup before restructure"
```

### **Step 2: Phase 1 - Safe Cleanup**
- Xóa backup files
- Xóa test files ở root
- Xóa mobile app duplicates

### **Step 3: Phase 2 - Restructure**
- Tạo thư mục mới
- Di chuyển files
- Cập nhật imports

### **Step 4: Phase 3 - Documentation**
- Consolidate docs
- Update README.md
- Create architecture docs

### **Step 5: Verification**
- Test core functionality
- Verify imports
- Check CI/CD

## 📈 **EXPECTED BENEFITS**

1. **Cleaner Structure**: Dễ navigate và maintain
2. **Reduced Confusion**: Ít duplicate files
3. **Better Organization**: Logical grouping
4. **Easier Onboarding**: Clear structure cho new developers
5. **Maintainability**: Dễ dàng tìm và sửa files

## 🔒 **SAFETY MEASURES**

1. **Git Backup**: Commit trước khi thay đổi
2. **Incremental Changes**: Từng bước nhỏ
3. **Verification**: Test sau mỗi phase
4. **Rollback Plan**: Có thể revert nếu cần
5. **Documentation**: Ghi lại mọi thay đổi

## 📋 **CHECKLIST**

- [ ] Backup current state
- [ ] Phase 1: Safe cleanup
- [ ] Phase 2: Restructure
- [ ] Phase 3: Documentation
- [ ] Verification & testing
- [ ] Update CI/CD
- [ ] Update documentation
- [ ] Final commit
