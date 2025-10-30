# 🔒 Branch Protection Guide - Solo Project Configuration

## Mục đích

Hướng dẫn cấu hình **Branch Protection Rules** cho GitHub repository solo project, cân bằng giữa:
- ✅ **Bảo mật** (không push trực tiếp lên main, có status checks)
- ✅ **Hiệu quả** (không cản trở workflow của solo developer)
- ✅ **Chất lượng code** (giữ được checks và reviews khi cần)

---

## 🎯 Cấu hình khuyến nghị cho Solo Project

### Bước 1: Vào Branch Protection Settings

1. Vào repository: `https://github.com/anhmtk/StillMe---Self-Evolving-AI-System`
2. Click **Settings** (cài đặt)
3. Chọn **Branches** trong menu bên trái
4. Tìm section **Branch protection rules**
5. Click **Add rule** hoặc **Edit** rule cho branch `main`

---

## ⚙️ Cấu hình chi tiết

### ✅ Nên bật (Recommended)

| Tùy chọn | Giá trị | Lý do |
|---------|---------|-------|
| **Require a pull request before merging** | ✅ **ON** | Đảm bảo mọi thay đổi đều qua PR, có history rõ ràng |
| **Require approvals** | ❌ **OFF** | Solo project không cần approval từ người khác |
| **Dismiss stale pull request approvals when new commits are pushed** | ✅ **ON** | Đảm bảo code mới nhất đã được review |
| **Require status checks to pass before merging** | ✅ **ON** | Bắt buộc Gitleaks, Cleanup Audit phải pass |
| **Require branches to be up to date before merging** | ✅ **ON** | Tránh conflict, đảm bảo code sync |
| **Require conversation resolution before merging** | ✅ **ON** (Optional) | Đảm bảo mọi comment/issue được giải quyết |
| **Require signed commits** | ❌ **OFF** | Solo project không cần GPG signing |
| **Require linear history** | ❌ **OFF** | Cho phép merge commits (flexible hơn) |
| **Do not allow bypassing the above settings** | ❌ **OFF** | Cho phép bypass khi cần (emergency fixes) |

### ❌ Nên tắt (Not Recommended)

| Tùy chọn | Giá trị | Lý do |
|---------|---------|-------|
| **Allow force pushes** | ❌ **OFF** | Bảo mật: không cho phép rewrite history |
| **Allow deletions** | ❌ **OFF** | Bảo mật: không cho phép xóa branch main |

---

## 🔍 Status Checks (Quan trọng!)

Trong section **"Require status checks to pass before merging"**:

### Bước 1: Chọn status checks bắt buộc

✅ Tick vào các checks sau:
- `Security – Gitleaks / gitleaks`
- `Cleanup Audit / cleanup-audit` (nếu có)

### Bước 2: Cấu hình "Require branches to be up to date"

✅ Tick vào: **"Require branches to be up to date before merging"**

**Lý do:** Đảm bảo PR luôn merge vào code mới nhất, tránh conflict và đảm bảo checks chạy trên code base mới nhất.

---

## 📝 Tóm tắt cấu hình

```
┌─────────────────────────────────────────────────┐
│ Branch Protection Rule: main                   │
├─────────────────────────────────────────────────┤
│ ✅ Require pull request                          │
│    └─ ❌ Require approvals (OFF)                │
│    └─ ✅ Dismiss stale approvals (ON)           │
│                                                 │
│ ✅ Require status checks                        │
│    └─ ✅ Security – Gitleaks                    │
│    └─ ✅ Cleanup Audit                          │
│    └─ ✅ Require up-to-date (ON)                │
│                                                 │
│ ✅ Require conversation resolution (Optional)   │
│                                                 │
│ ❌ Require signed commits                       │
│ ❌ Require linear history                       │
│ ❌ Allow force pushes                           │
│ ❌ Allow deletions                              │
│                                                 │
│ ❌ Do not allow bypassing (OFF - flexible)      │
└─────────────────────────────────────────────────┘
```

---

## 🚀 Workflow sau khi cấu hình

### Workflow bình thường:

```bash
# 1. Tạo feature branch
git checkout -b feature/new-feature

# 2. Code, commit, push
git add .
git commit -m "feat: Add new feature"
git push origin feature/new-feature

# 3. Tạo PR trên GitHub
# 4. Đợi checks pass (Gitleaks, Cleanup Audit)
# 5. Merge PR (không cần approval từ người khác)
```

### Emergency fixes (có thể bypass nếu cần):

Nếu tắt **"Do not allow bypassing"**, bạn có thể:
- Dùng GitHub CLI: `gh pr create --base main --head fix/emergency --fill`
- Hoặc tạm thời disable protection rule trong settings

---

## ⚠️ Lưu ý quan trọng

### 1. Không push trực tiếp lên `main`

Sau khi cấu hình, bạn **KHÔNG THỂ** push trực tiếp:
```bash
# ❌ Sẽ bị reject
git checkout main
git push origin main
```

**Phải** tạo branch và PR:
```bash
# ✅ Đúng
git checkout -b fix/bug
git push origin fix/bug
# → Tạo PR trên GitHub → Merge
```

### 2. Status checks phải pass

Mọi PR phải pass:
- ✅ Gitleaks (security scan)
- ✅ Cleanup Audit (nếu có)

Nếu check fail, phải fix xong mới merge được.

### 3. Code phải up-to-date

Trước khi merge, PR phải rebase hoặc merge với `main` mới nhất:
```bash
# Trên branch của bạn
git checkout feature/xyz
git fetch origin
git rebase origin/main
git push origin feature/xyz --force-with-lease
```

---

## 🔧 Troubleshooting

### Issue: "Merging is blocked - checks not running"

**Nguyên nhân:** Workflow trong `main` branch cũ, không có `GITHUB_TOKEN` hoặc permissions.

**Giải pháp:** 
1. Tạo PR fix workflow trước
2. Merge vào `main`
3. Checks sẽ chạy cho PR tiếp theo

### Issue: "Can't merge - branch is out of date"

**Giải pháp:**
```bash
git checkout your-branch
git fetch origin
git rebase origin/main
git push origin your-branch --force-with-lease
```

### Issue: "Require signed commits" error

**Nguyên nhân:** Branch protection yêu cầu GPG signed commits.

**Giải pháp:** 
1. Tắt "Require signed commits" trong settings (không cần cho solo project)
2. Hoặc setup GPG signing (phức tạp, không cần thiết)

---

## 📚 Tài liệu tham khảo

- [GitHub: About protected branches](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches/about-protected-branches)
- [GitHub: Requiring status checks](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches/managing-a-branch-protection-rule#require-status-checks-before-merging)

---

## ✅ Checklist sau khi cấu hình

- [ ] Branch protection rule đã được tạo cho `main`
- [ ] Require pull request: **ON**
- [ ] Require approvals: **OFF** (cho solo project)
- [ ] Require status checks: **ON** với Gitleaks và Cleanup Audit
- [ ] Require up-to-date: **ON**
- [ ] Allow force pushes: **OFF**
- [ ] Allow deletions: **OFF**
- [ ] Test workflow: tạo branch mới → PR → merge thành công

---

**Lưu ý:** Cấu hình này phù hợp cho **solo project** và **small team**. Nếu sau này có nhiều contributors, có thể bật lại "Require approvals" với số lượng approval tối thiểu = 1.
