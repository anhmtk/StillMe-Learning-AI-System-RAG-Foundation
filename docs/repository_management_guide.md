# 🏗️ StillMe Repository Management Guide

## 📋 Tổng quan

Hệ thống quản lý repository StillMe được thiết kế để:
- **Quét và phân loại** tất cả files trong repository
- **Phát hiện file rác** và candidates để xóa/quarantine
- **Quarantine an toàn** các file có risk thấp
- **Restore** files khi cần thiết
- **CI/CD integration** với shadow testing

## 🛠️ Công cụ chính

### 1. Repository Inventory (`tools/repo_inventory.py`)

**Mục đích**: Quét và phân loại tất cả files trong repository

**Cách sử dụng**:
```bash
# Quét primary files (production code, configs, docs)
python tools/repo_inventory.py --mode primary --with-hash

# Quét excluded files (artifacts, dependencies)
python tools/repo_inventory.py --mode excluded

# Quét tất cả files
python tools/repo_inventory.py --mode all
```

**Output**:
- `reports/primary_inventory.csv` - Danh sách primary files
- `reports/primary_large_files.csv` - Top 1000 files lớn nhất
- `reports/primary_dep_grraph.json` - Dependency graph
- `reports/primary_summary.json` - Tóm tắt thống kê

### 2. Deletion Candidates Finder (`tools/find_candidates.py`)

**Mục đích**: Phát hiện file rác, trùng lặp, và candidates để xóa

**Cách sử dụng**:
```bash
python tools/find_candidates.py
```

**Output**:
- `reports/deletion_candidates.md` - Báo cáo chi tiết
- `reports/deletion_candidates.csv` - Dữ liệu cho quarantine tool

**Phân loại candidates**:
- **LOW risk**: File rác, backup, build artifacts
- **MEDIUM risk**: File không được reference, file cũ
- **HIGH risk**: File có references, file quan trọng

### 3. Quarantine Move Tool (`tools/quarantine_move.py`)

**Mục đích**: Di chuyển file vào graveyard một cách an toàn

**Cách sử dụng**:
```bash
# Liệt kê files đã quarantine
python tools/quarantine_move.py --action list

# Quarantine LOW risk files (dry run)
python tools/quarantine_move.py --action quarantine --risk LOW --dry-run

# Quarantine LOW risk files (thực tế)
python tools/quarantine_move.py --action quarantine --risk LOW

# Quarantine MEDIUM risk files (dry run)
python tools/quarantine_move.py --action quarantine --risk MEDIUM --dry-run

# Quarantine HIGH risk files (dry run)
python tools/quarantine_move.py --action quarantine --risk HIGH --dry-run

# Xóa hoàn toàn graveyard
python tools/quarantine_move.py --action cleanup
```

### 4. Restore Tool (`tools/restore_from_graveyard.py`)

**Mục đích**: Restore files từ graveyard về vị trí cũ

**Cách sử dụng**:
```bash
python tools/restore_from_graveyard.py
```

## 🚀 Workflow khuyến nghị

### 1. Quét repository lần đầu
```bash
# Quét primary files
python tools/repo_inventory.py --mode primary --with-hash

# Tìm deletion candidates
python tools/find_candidates.py
```

### 2. Xem xét candidates
```bash
# Xem báo cáo chi tiết
cat reports/deletion_candidates.md

# Xem danh sách LOW risk files
python tools/quarantine_move.py --action quarantine --risk LOW --dry-run
```

### 3. Quarantine an toàn
```bash
# Quarantine LOW risk files
python tools/quarantine_move.py --action quarantine --risk LOW

# Chạy tests để đảm bảo không có vấn đề
python -m pytest tests/ -v

# Nếu có vấn đề, restore ngay
python tools/restore_from_graveyard.py
```

### 4. Dọn dẹp định kỳ
```bash
# Chạy inventory lại
python tools/repo_inventory.py --mode primary

# Tìm candidates mới
python tools/find_candidates.py

# Quarantine files mới
python tools/quarantine_move.py --action quarantine --risk LOW
```

## 📊 Báo cáo và thống kê

### Primary Inventory Summary
```json
{
  "total_files": 726,
  "total_size_mb": 8.5,
  "unreferenced_files": 726,
  "binary_files": 0,
  "by_type": {
    "code": 406,
    "config": 81,
    "doc": 85,
    "other": 39,
    "test": 115
  },
  "by_size": {
    "small": 160,
    "medium": 566,
    "large": 0,
    "huge": 0
  }
}
```

### Deletion Candidates Summary
```
Total candidates: 562
By risk level:
  - LOW: 171
  - MEDIUM: 391
  - HIGH: 0
By category:
  - node: 4
  - backup: 54
  - unreferenced: 504
```

## 🔒 Bảo mật và an toàn

### Protected Patterns
Các file/directory sau **KHÔNG BAO GIỜ** được quarantine:
- `.env*` files
- `policies/` directory
- `models/`, `weights/`, `checkpoints/` directories
- `data/`, `deploy/` directories
- `.github/`, `sandbox/` directories

### Risk Assessment
- **LOW**: File rác, backup, build artifacts, test files
- **MEDIUM**: File không được reference, file cũ
- **HIGH**: File có references, file quan trọng

### Quarantine Manifest
Mỗi lần quarantine tạo file `reports/quarantine_manifest.json`:
```json
{
  "created_at": "2025-09-23T10:30:00",
  "total_files": 25,
  "total_size": 1024000,
  "files": [
    {
      "original_path": "temp/old_file.py",
      "graveyard_path": "_graveyard/temp/old_file.py",
      "category": "backup",
      "reason": "Matches pattern: temp",
      "size": 1024,
      "moved_at": "2025-09-23T10:30:00"
    }
  ]
}
```

## 🧪 CI/CD Integration

### Shadow CI Workflow
File `ci/shadow_inventory.yml` chạy:
1. **Inventory Scan**: Quét repository
2. **Find Candidates**: Tìm deletion candidates
3. **Pre-quarantine Tests**: Chạy tests trước khi quarantine
4. **Quarantine**: Quarantine LOW risk files
5. **Post-quarantine Tests**: Chạy tests sau khi quarantine
6. **Restore**: Restore files
7. **Final Tests**: Chạy tests cuối cùng

### Local Testing
```bash
# Chạy shadow CI locally
make shadow-ci

# Hoặc dùng npm
npm run shadow:ci
```

## 📝 Best Practices

### 1. Luôn chạy dry-run trước
```bash
python tools/quarantine_move.py --action quarantine --risk LOW --dry-run
```

### 2. Test sau mỗi lần quarantine
```bash
python -m pytest tests/ -v
```

### 3. Backup trước khi cleanup
```bash
# Tạo backup của graveyard
cp -r _graveyard _graveyard_backup_$(date +%Y%m%d)
```

### 4. Review candidates thường xuyên
```bash
# Chạy inventory hàng tuần
python tools/repo_inventory.py --mode primary
python tools/find_candidates.py
```

### 5. Sử dụng Makefile/npm scripts
```bash
# Thay vì chạy lệnh dài
make inventory-primary
make find-candidates
make quarantine-low

# Hoặc
npm run inventory:primary
npm run find:candidates
npm run quarantine:low
```

## 🚨 Troubleshooting

### Lỗi "File not found"
```bash
# Kiểm tra file có tồn tại không
ls -la path/to/file

# Restore từ graveyard
python tools/restore_from_graveyard.py
```

### Lỗi "Permission denied"
```bash
# Kiểm tra quyền
ls -la _graveyard/

# Sửa quyền nếu cần
chmod -R 755 _graveyard/
```

### Lỗi "Tests failing after quarantine"
```bash
# Restore ngay lập tức
python tools/restore_from_graveyard.py

# Chạy tests lại
python -m pytest tests/ -v
```

## 📚 Tài liệu tham khảo

- [Repository Inventory Tool](tools/repo_inventory.py)
- [Deletion Candidates Finder](tools/find_candidates.py)
- [Quarantine Move Tool](tools/quarantine_move.py)
- [Restore Tool](tools/restore_from_graveyard.py)
- [Shadow CI Workflow](ci/shadow_inventory.yml)
- [Makefile](Makefile)
- [Package.json Scripts](package.json)
