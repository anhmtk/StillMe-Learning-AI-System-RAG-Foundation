# 🧹 Integration Tracker: Cleanup Branches Merge

## 📊 PR Merge Checklist

| PR | Link | Status | Conflicts? | tools/inventory | .github/workflows | whitelist.yml | scripts/windows/attic_* |
|----|------|--------|------------|-----------------|-------------------|---------------|------------------------|
| wave-1d | [ ] | □ | □ | □ | □ | □ | □ |
| wave-1e | [ ] | □ | □ | □ | □ | □ | □ |
| wave-1f | [ ] | □ | □ | □ | □ | □ | □ |
| wave-2a | [ ] | □ | □ | □ | □ | □ | □ |

**Legend:** □ = Pending, ■ = Done

## 🔍 Post-Merge Verification

### File Structure Check
- [ ] `_attic/` visible in main branch (Code tab)
- [ ] `.gitignore` contains `!_attic/**` line
- [ ] `tools/inventory/` contains all analysis tools
- [ ] `.github/workflows/` contains cleanup-audit.yml + attic-dryrun.yml
- [ ] `docs/cleanup/` contains wave-1d.md through wave-2a.md
- [ ] `artifacts/baseline/` contains baseline files

### CI Workflows Check
- [ ] Actions: Cleanup Audit run OK (green ✅)
- [ ] Actions: Attic Dry-Run run OK (green ✅)
- [ ] Artifacts downloaded and verified

## 🎯 Kết Quả Mong Đợi
- Tất cả 4 PRs merged thành công vào main
- `_attic/` directory hiển thị và được track
- CI workflows chạy thành công và tạo artifacts
- Baseline files được lưu trong `artifacts/baseline/`

## 🚨 Nếu Lỗi Thì Làm Gì
- **Conflicts**: Dùng "Resolve conflicts" → Giữ phiên bản cleanup cho tools/inventory, .github/workflows, whitelist.yml, scripts/windows/attic_*
- **CI Failed**: Check Actions tab → Re-run workflow → Check error logs
- **_attic/ Missing**: Edit .gitignore → Add `!_attic/**` → Commit changes

---

## 📝 PR Body Templates

### PR 1: Wave-1d Merge
```markdown
## cleanup-wave-1d (initial quarantine + tools)

### Changes
- ✅ Initial file quarantine to _attic/
- ✅ Created analysis tools: import_graph.py, redundant_score.py
- ✅ Added PowerShell scripts for safe file moves
- ✅ Established CI gates for backup file detection

### Review Checklist
- [ ] _attic/ directory created
- [ ] tools/inventory/ contains analysis scripts
- [ ] scripts/windows/ contains attic_move.ps1
- [ ] CI workflow runs successfully

### How to Resolve Conflicts (Web)
1. Click "Resolve conflicts" button
2. For conflicts in tools/inventory/**: Keep version from wave-1d
3. For conflicts in .github/workflows/**: Keep version from wave-1d
4. Click "Mark as resolved" → "Commit merge"
```

### PR 2: Wave-1e Merge
```markdown
## cleanup-wave-1e (enhanced analysis + coverage)

### Changes
- ✅ Enhanced import graph analysis
- ✅ Added coverage generation with smoke tests
- ✅ Improved redundant scoring algorithm
- ✅ Added near-duplicate detection

### Review Checklist
- [ ] artifacts/import_inbound.json generated
- [ ] artifacts/coverage.json generated
- [ ] artifacts/redundancy_report.csv generated
- [ ] Enhanced CI gates working

### How to Resolve Conflicts (Web)
1. Click "Resolve conflicts" button
2. For tools/inventory/**: Keep version from wave-1e
3. For .github/workflows/**: Keep version from wave-1e
4. For config/cleanup/whitelist.yml: Keep version from wave-1e
5. Click "Mark as resolved" → "Commit merge"
```

### PR 3: Wave-1f Merge
```markdown
## cleanup-wave-1f (near-dupe consolidation + CI hardening)

### Changes
- ✅ Near-duplicate detection and pilot selection
- ✅ Compatibility shims in stillme_compat/
- ✅ Enhanced CI gates with strict backup detection
- ✅ Weekly attic dry-run workflow

### Review Checklist
- [ ] stillme_compat/ package created
- [ ] artifacts/near_dupes.json generated
- [ ] CI workflows enhanced
- [ ] Weekly dry-run scheduled

### How to Resolve Conflicts (Web)
1. Click "Resolve conflicts" button
2. For tools/inventory/**: Keep version from wave-1f
3. For .github/workflows/**: Keep version from wave-1f
4. For scripts/windows/attic_*: Keep version from wave-1f
5. Click "Mark as resolved" → "Commit merge"
```

### PR 4: Wave-2a Merge
```markdown
## cleanup-wave-2a (attic eviction planning + baseline)

### Changes
- ✅ Attic sweeper tool for eviction candidates
- ✅ Baseline snapshots after Wave-1f
- ✅ Enhanced CI gates with strict backup detection
- ✅ Weekly attic dry-run with artifact upload

### Review Checklist
- [ ] tools/inventory/attic_sweeper.py created
- [ ] artifacts/baseline/ contains snapshots
- [ ] Weekly dry-run workflow active
- [ ] Enhanced CI gates working

### How to Resolve Conflicts (Web)
1. Click "Resolve conflicts" button
2. For tools/inventory/**: Keep version from wave-2a
3. For .github/workflows/**: Keep version from wave-2a
4. For config/cleanup/whitelist.yml: Keep version from wave-2a
5. Click "Mark as resolved" → "Commit merge"
```

---

## 🚀 Sau Khi Merge Xong Hết

### 1. Xác Thực _attic/ Có File .py
1. ➡️ Vào main branch → **Code** tab
2. ➡️ Tìm folder `_attic/` trong file tree
3. ➡️ Click vào `_attic/` → Kiểm tra có file `.py` không
4. ➡️ Nếu không thấy: Edit `.gitignore` → Thêm `!_attic/**` → Commit

### 2. Kiểm Tra Artifacts
1. ➡️ Vào **Actions** tab
2. ➡️ Tìm latest run của "Cleanup Audit"
3. ➡️ Download artifact `cleanup-audit-artifacts`
4. ➡️ Tìm latest run của "Attic Dry-Run"
5. ➡️ Download artifact `attic-dryrun-artifacts`

### 3. Ghi Chú Quan Trọng
- 📅 **Sau ≥30 ngày**: Chuyển sang Wave-2c (controlled delete)
- 🔍 **Monitor**: Theo dõi weekly attic dry-run results
- 🗑️ **Review**: Xem xét eviction candidates trong artifacts

---

## 📈 Quick Actions (Click Only)

1. 🔍 **Find PRs**: GitHub → Pull requests → Search "cleanup/wave-"
2. ➡️ **Merge 1d**: wave-1d-safe → main (Create merge commit)
3. ➡️ **Merge 1e**: wave-1e-safe → main (Resolve conflicts if needed)
4. ➡️ **Merge 1f**: wave-1f-safe → main (Resolve conflicts if needed)
5. ➡️ **Merge 2a**: wave-2a-safe → main (Resolve conflicts if needed)
6. 🔍 **Check _attic/**: Code tab → Look for _attic/ folder
7. ⚙️ **Fix .gitignore**: If _attic/ missing → Edit .gitignore → Add `!_attic/**`
8. 🚀 **Run CI**: Actions → Run "Cleanup Audit" workflow
9. 🗂️ **Run Dry-Run**: Actions → Run "Attic Dry-Run" workflow
10. ✅ **Verify**: Check artifacts and baseline files exist
