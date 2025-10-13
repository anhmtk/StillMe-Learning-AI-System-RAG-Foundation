# 🗑️ DANH SÁCH FILE DƯ THỪA CỤ THỂ

## 📋 **BACKUP/LEGACY FILES (140 files - XÓA NGAY):**

### **1. _attic/ Directory (~100 files):**
```
_attic/
├── _graveyard/20251010/          # Graveyard files
├── agent_dev/                    # Old agent dev files
├── agentdev_tests/               # Old test files
├── cache/                        # Cache files
├── chaos/                        # Chaos test files
├── dashboards/                   # Old dashboard files
├── examples/                     # Example files
├── fixtures/                     # Test fixtures
├── plugins/                      # Old plugin files
├── scripts/                      # Old script files
├── security/                     # Old security files
├── security_basics/              # Basic security files
├── stillme_api/                  # Old API files
├── stillme_community/            # Community files
├── stillme_core/                 # Old core files
├── tests/                        # Old test files
├── tools/                        # Old tool files
└── unit/                         # Unit test files
```

### **2. backups/ Directory (~20 files):**
```
backups/
└── self_improvement/             # Self improvement backups
```

### **3. agentdev_backups/ Directory (~10 files):**
```
agentdev_backups/                 # Empty directory
```

### **4. framework_backups/ Directory (~10 files):**
```
framework_backups/                # Framework backups
```

## 🧪 **TEST FILES DƯ THỪA (50 files - XÓA HOẶC CONSOLIDATE):**

### **1. Root Level Test Files (~50 files):**
```
test_agentdev_core_comprehensive.py
test_dashboard_real_data.py
test_generated.py
test_*.py                         # All test_*.py files at root
```

### **2. tests_harness/ Directory (~30 files):**
```
tests_harness/
├── simple_html_report.py
├── simple_demo.py
├── seed_generator.py
├── scale_dataset.py
├── runners/
├── optimization/
├── evaluators/
├── benchmarking/
├── augmentor/
└── demo_*.py
```

### **3. tests_agentdev_scan/ Directory (~10 files):**
```
tests_agentdev_scan/
├── test_zero_guard_when_sources_fail.py
├── test_unicode_log_parsing.py
├── test_scan_matches_ruff.py
└── other test files
```

## 🛠️ **SCRIPT FILES DƯ THỪA (30 files - XÓA HOẶC CONSOLIDATE):**

### **1. scripts/ Directory (~30 files cần xóa):**
```
scripts/
├── validate_*.py                 # Validation scripts
├── test_*.py                     # Test scripts
├── run_*.py                      # Run scripts
├── generate_*.py                 # Generate scripts
├── analyze_*.py                  # Analysis scripts
├── check_*.py                    # Check scripts
├── fix_*.py                      # Fix scripts
├── debug_*.py                    # Debug scripts
├── monitor_*.py                  # Monitor scripts
├── router_*.py                   # Router scripts
├── quality_*.py                  # Quality scripts
├── security_*.py                 # Security scripts
├── performance_*.py              # Performance scripts
├── deploy_*.py                   # Deploy scripts
├── install_*.py                  # Install scripts
├── configure_*.py                # Configure scripts
├── export_*.py                   # Export scripts
├── import_*.py                   # Import scripts
├── backup_*.py                   # Backup scripts
├── restore_*.py                  # Restore scripts
├── cleanup_*.py                  # Cleanup scripts
├── optimize_*.py                 # Optimization scripts
├── calibrate_*.py                # Calibration scripts
├── extract_*.py                  # Extract scripts
├── apply_*.py                    # Apply scripts
├── plan_*.py                     # Planning scripts
├── create_*.py                   # Creation scripts
├── setup_*.py                    # Setup scripts
├── start_*.py                    # Start scripts
└── other utility scripts
```

### **2. tools/ Directory (~10 files cần xóa):**
```
tools/
├── semantic_search.py
├── scan_null_bytes.py
├── run_redteam.py
├── restore_from_graveyard.py
├── repo_inventory.py
├── quarantine_move.py
├── pytest_bisect.py
├── normalize_encoding.py
├── monitor_resources.py
├── generate_k6_report.py
├── find_candidates.py
├── check_null_bytes_precommit.py
├── check_crlf_precommit.py
├── baseline_scan.py
├── audit_type_ignores.py
├── ast_impact.py
└── analyze_car_results.py
```

## 🔧 **CORE MODULES DƯ THỪA (20 files - XÓA HOẶC REFACTOR):**

### **1. stillme_core/modules/ Directory (~20 files):**
```
stillme_core/modules/
├── layered_memory_v1_old.py
├── content_integrity_filter_old.py
├── api_provider_manager_old.py
└── other old modules
```

### **2. stillme_core/core/ Directory (~10 files):**
```
stillme_core/core/
├── advanced_security/            # Old security files
├── build/                        # Build files
├── cli/                          # CLI files
├── deployment/                   # Deployment files
├── monitoring/                   # Monitoring files
├── predictive/                   # Predictive files
├── team_coordination/            # Team coordination files
└── validation/                   # Validation files
```

## 📊 **TỔNG KẾT:**

| **Loại** | **Số files** | **Hành động** | **Ưu tiên** |
|----------|--------------|---------------|-------------|
| **Backup/Legacy** | **140** | **XÓA NGAY** | **🔴 CAO** |
| **Test dư thừa** | **50** | **XÓA/CONSOLIDATE** | **🟡 TRUNG BÌNH** |
| **Script dư thừa** | **30** | **XÓA/CONSOLIDATE** | **🟡 TRUNG BÌNH** |
| **Core dư thừa** | **20** | **XÓA/REFACTOR** | **🟢 THẤP** |
| **TỔNG CỘNG** | **240** | **CÓ THỂ XÓA** | **🎯 30%** |

## 🚀 **KẾ HOẠCH THỰC HIỆN:**

### **Phase 1: Xóa Backup/Legacy (140 files)**
- Xóa `_attic/` directory
- Xóa `backups/` directory
- Xóa `agentdev_backups/` directory
- Xóa `framework_backups/` directory

### **Phase 2: Consolidate Test Files (50 files)**
- Di chuyển test files vào `tests/` directory
- Xóa duplicate test files
- Consolidate test harness

### **Phase 3: Clean Scripts (30 files)**
- Xóa one-time use scripts
- Consolidate utility scripts
- Keep only essential scripts

### **Phase 4: Refactor Core (20 files)**
- Review core modules
- Remove unused modules
- Refactor if necessary

## ⚠️ **LƯU Ý QUAN TRỌNG:**
- **Backup trước khi xóa**
- **Test kỹ sau khi xóa**
- **Review từng file trước khi xóa**
- **Không xóa file đang được sử dụng**
