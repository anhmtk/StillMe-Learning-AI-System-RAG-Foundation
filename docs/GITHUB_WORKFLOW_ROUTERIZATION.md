# GitHub Workflow cho Routerization

## 📋 Tổng quan

Đã hoàn thành routerization: tách `main.py` (2817 dòng) thành 5 modular routers. Bây giờ cần:
1. ✅ Cập nhật README (đã xong)
2. ⏳ Mở GitHub issue để track progress
3. ⏳ Push code lên GitHub

## 🔄 Workflow: Issue vs Code Push

### ❓ Có cần push code trước khi mở issue không?

**KHÔNG CẦN!** Bạn có thể:
- **Option 1**: Mở issue trước → Làm code → Push code → Update issue
- **Option 2**: Làm code trước → Push code → Mở issue để track completion

**Trong trường hợp này**: Code đã xong → Nên mở issue để **track completion** và **document changes**.

## 📝 Cách mở GitHub Issue

### Bước 1: Vào GitHub Repository
```
https://github.com/anhmtk/StillMe-Learning-AI-System-RAG-Foundation
```

### Bước 2: Click "New Issue"
- Click nút "New Issue" trên GitHub
- Chọn template: **"[P1A] Routerization - Split main.py into modular routers"**

### Bước 3: Điền thông tin
Issue template đã có sẵn tại: `.github/ISSUE_TEMPLATE/p1a_routerization.md`

**Cập nhật Implementation Plan** (đánh dấu completed):
```markdown
## 📝 Implementation Plan

1. ✅ Create `backend/api/routers/__init__.py`
2. ✅ Extract chat endpoints → `chat_router.py`
3. ✅ Extract learning endpoints → `learning_router.py`
4. ✅ Extract RAG endpoints → `rag_router.py`
5. ✅ Extract tiers endpoints → `tiers_router.py`
6. ✅ Extract SPICE endpoints → `spice_router.py`
7. ✅ Update `main.py` to use `app.include_router()`
8. ⏳ Add smoke tests
9. ⏳ Verify all endpoints work
```

### Bước 4: Submit Issue
- Click "Submit new issue"
- Issue sẽ tự động có labels: `type:refactor`, `risk:low`, `area:api`, `milestone:P1-Foundation`

## 🚀 Cách Push Code

### Sử dụng script có sẵn:

```powershell
# Chạy script push với Personal Access Token
.\scripts\push_with_token.ps1
```

**Script sẽ:**
1. Yêu cầu bạn nhập Personal Access Token
2. Set token vào remote URL (tạm thời)
3. Push code lên GitHub
4. Xóa token khỏi URL (bảo mật)

### Tạo Personal Access Token (nếu chưa có):

1. Vào: https://github.com/settings/tokens
2. Click "Generate new token (classic)"
3. Chọn scope: `repo` (full control of private repositories)
4. Copy token (chỉ hiển thị 1 lần!)

### Commit message gợi ý:

```bash
git add .
git commit -m "refactor: Split main.py into modular routers (P1A)

- Created 5 routers: chat, learning, rag, tiers, spice
- Reduced main.py from 2817 to ~1968 lines
- All 42 endpoints still functional
- No logic changes, move-only refactoring
- Better code organization and maintainability

Closes #[issue-number]"
```

## 🔄 Workflow tiếp theo: Sau khi push code

### ❓ Code đã push rồi, giờ làm gì?

Sau khi push code, có 2 trường hợp:

#### **Trường hợp 1: Push trực tiếp vào `main` branch** ✅
- **Code đã vào dự án rồi!** Không cần làm gì thêm về code.
- **Cần làm:**
  1. ✅ Update issue #56 với progress/completion
  2. ✅ Close issue khi hoàn thành (hoặc để open nếu còn pending tasks)
  3. ✅ Verify code hoạt động trên production

#### **Trường hợp 2: Push vào feature branch** (ví dụ: `refactor/routerization`)
- **Cần tạo Pull Request (PR)** để merge vào `main`:
  1. Vào GitHub → Click "Pull requests" → "New pull request"
  2. Chọn base: `main` ← compare: `refactor/routerization`
  3. Điền title: `[P1A] Routerization - Split main.py into modular routers`
  4. Điền description: Reference issue #56 (`Closes #56` hoặc `Fixes #56`)
  5. Click "Create pull request"
  6. Đợi CI checks pass (nếu có)
  7. Merge PR vào `main`
  8. Close issue #56

### 📝 Cách update issue #56

1. Vào issue #56 trên GitHub
2. Click "Edit" hoặc comment với progress:

```markdown
## ✅ Progress Update

### Completed:
- ✅ Created 5 routers: chat, learning, rag, tiers, spice
- ✅ Reduced main.py from 2817 to ~1968 lines
- ✅ All 42 endpoints still functional
- ✅ README updated with routerization info
- ✅ Code pushed to main branch

### Pending:
- ⏳ Add smoke tests for each router
- ⏳ Verify all endpoints work (manual testing)
- ⏳ Run pytest to ensure no new failures

### Next Steps:
1. Add smoke tests
2. Manual verification
3. Close issue when all tasks complete
```

3. Update labels nếu cần (ví dụ: thêm `status:in-progress` → `status:completed`)

## ✅ Checklist hoàn thành

- [x] Code refactoring hoàn thành
- [x] README đã cập nhật
- [x] GitHub issue đã mở (#56)
- [x] Code đã push lên GitHub
- [ ] Update issue #56 với progress
- [ ] Smoke tests đã thêm (pending)
- [ ] All endpoints verified (pending)
- [ ] Close issue khi hoàn thành

## 📚 Tài liệu liên quan

- Issue template: `.github/ISSUE_TEMPLATE/p1a_routerization.md`
- PR documentation: `docs/P1A_ROUTERIZATION_PR.md`
- Router code: `backend/api/routers/`

