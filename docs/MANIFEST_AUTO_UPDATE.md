# Manifest Auto-Update Guide

## Tổng quan

StillMe Structural Manifest cần được cập nhật mỗi khi có thay đổi về validators. Hiện tại có **3 cách** để đảm bảo manifest luôn up-to-date:

## Cách 1: Script Wrapper (Khuyến nghị - Dễ nhất)

Chạy một lệnh duy nhất để generate và inject manifest:

```bash
python scripts/update_manifest.py
```

Script này sẽ:
1. ✅ Generate manifest từ codebase hiện tại
2. ✅ Inject manifest vào ChromaDB với CRITICAL_FOUNDATION priority
3. ✅ Increment knowledge_version (invalidate cache)

**Khi nào dùng**: Sau khi thêm/xóa/sửa validators, hoặc trước khi deploy.

## Cách 2: Pre-commit Hook (Tự động)

Git pre-commit hook sẽ **tự động** phát hiện khi validator files thay đổi và regenerate manifest trước khi commit.

### Setup (chỉ cần làm 1 lần):

```bash
# Hook đã được tạo tại .git/hooks/pre-commit
# Trên Windows, Git Bash sẽ tự động chạy hook này
```

### Cách hoạt động:

1. Khi bạn commit code có thay đổi validator files
2. Hook tự động check xem manifest có cũ hơn không
3. Nếu cũ → tự động regenerate manifest
4. Manifest mới được add vào commit

**Lưu ý**: Hook chỉ regenerate manifest, **KHÔNG** inject vào RAG. Bạn vẫn cần chạy `update_manifest.py` để inject vào RAG sau khi commit.

## Cách 3: Check Script (Kiểm tra thủ công)

Kiểm tra xem manifest có cần update không:

```bash
python scripts/check_manifest.py
```

Script sẽ:
- ✅ Nếu manifest up-to-date: "✅ Manifest is up-to-date"
- ⚠️ Nếu manifest outdated: Liệt kê các files mới hơn và gợi ý chạy `update_manifest.py`

**Khi nào dùng**: Trước khi deploy, hoặc khi nghi ngờ manifest đã cũ.

## Workflow Khuyến nghị

### Development:

1. **Sửa validator code** → Commit (pre-commit hook tự động regenerate manifest)
2. **Trước khi test/deploy** → Chạy `python scripts/update_manifest.py` để inject vào RAG

### Production Deployment:

1. **Trước khi deploy** → Chạy `python scripts/check_manifest.py` để verify
2. **Nếu outdated** → Chạy `python scripts/update_manifest.py`
3. **Deploy** → Manifest đã được inject vào RAG, StillMe sẽ dùng manifest mới

## Tại sao cần inject vào RAG?

- **Generate manifest** → Tạo file JSON `data/stillme_manifest.json`
- **Inject vào RAG** → Convert JSON → Text → Thêm vào ChromaDB → StillMe có thể retrieve

**Quan trọng**: Chỉ generate manifest **KHÔNG ĐỦ**. Phải inject vào RAG thì StillMe mới biết!

## Troubleshooting

### Manifest không được update sau khi sửa validators?

1. Check: `python scripts/check_manifest.py`
2. Nếu outdated: `python scripts/update_manifest.py`

### Pre-commit hook không chạy?

- Trên Windows: Đảm bảo dùng Git Bash hoặc Git GUI
- Check: `.git/hooks/pre-commit` có tồn tại và executable không

### StillMe vẫn trả về số liệu cũ?

1. Verify manifest: `python scripts/check_manifest.py`
2. Update manifest: `python scripts/update_manifest.py`
3. Check cache: Cache đã được invalidate (knowledge_version incremented)
4. Test lại: Hỏi StillMe về validator count

## Tóm tắt Commands

```bash
# Generate + Inject (khuyến nghị)
python scripts/update_manifest.py

# Chỉ check
python scripts/check_manifest.py

# Chỉ generate (không inject)
python scripts/generate_manifest.py

# Chỉ inject (cần manifest đã có)
python scripts/inject_manifest_to_rag.py
```

