# 🧹 Integration Playbook: Wave-2x Cleanup Branches

## 📋 Overview
Hướng dẫn hợp nhất các nhánh cleanup (1d/1e/1f/2a) hoàn toàn qua GitHub UI, không cần chạy lệnh terminal.

## 🎯 Objectives
- ✅ Merge tuần tự: wave-1d → wave-1e → wave-1f → wave-2a
- ✅ Xử lý conflicts trên web
- ✅ Bật tracking `_attic/` 
- ✅ Chốt baseline sau merge
- ✅ Xác thực CI workflows hoạt động

---

## 🚀 PHASE 1: Sequential PR Merging

### Step 1: Merge wave-1d-safe → main
1. ➡️ Vào GitHub → Pull requests
2. ➡️ Tìm PR `cleanup/wave-1d-safe → main`
3. ➡️ Click **"Merge pull request"**
4. ➡️ Chọn **"Create a merge commit"** (không dùng squash)
5. ➡️ Click **"Confirm merge"**

### Step 2: Merge wave-1e-safe → main  
1. ➡️ Tìm PR `cleanup/wave-1e-safe → main`
2. ➡️ Nếu có conflicts: Click **"Resolve conflicts"**
3. ➡️ **Conflict Resolution Rules:**
   - `tools/inventory/**` → Giữ phiên bản từ wave-1e
   - `.github/workflows/**` → Giữ phiên bản từ wave-1e  
   - `config/cleanup/whitelist.yml` → Giữ phiên bản từ wave-1e
   - `scripts/windows/attic_*` → Giữ phiên bản từ wave-1e
4. ➡️ Click **"Mark as resolved"** → **"Commit merge"**
5. ➡️ Click **"Merge pull request"**

### Step 3: Merge wave-1f-safe → main
1. ➡️ Tìm PR `cleanup/wave-1f-safe → main`
2. ➡️ Nếu có conflicts: Áp dụng **Conflict Resolution Rules** (như Step 2)
3. ➡️ Click **"Merge pull request"**

### Step 4: Merge wave-2a-safe → main
1. ➡️ Tìm PR `cleanup/wave-2a-safe → main`
2. ➡️ Nếu có conflicts: Áp dụng **Conflict Resolution Rules**
3. ➡️ Click **"Merge pull request"**

---

## 🔧 PHASE 2: Enable _attic/ Tracking

### Check Current Status
1. ➡️ Vào main branch → **Code** tab
2. ➡️ Tìm folder `_attic/` trong file tree
3. ➡️ Nếu **KHÔNG thấy** `_attic/` → Cần enable tracking

### Enable _attic/ Tracking (if needed)
1. ➡️ Tìm file `.gitignore` trong root
2. ➡️ Click **"Edit"** (pencil icon)
3. ➡️ Tìm dòng có `_attic/` hoặc `_attic`
4. ➡️ Thêm dòng mới: `!_attic/**` (ngay sau dòng ignore)
5. ➡️ Click **"Commit changes"**
6. ➡️ Title: `ci(cleanup): unignore _attic/**`
7. ➡️ Description: `Enable tracking of _attic/ directory for cleanup monitoring`

---

## 📊 PHASE 3: Post-Merge Verification

### ✅ Checklist 1: File Structure
- [ ] `_attic/` folder visible in main branch
- [ ] `tools/inventory/` contains all analysis tools
- [ ] `.github/workflows/` contains cleanup-audit.yml + attic-dryrun.yml
- [ ] `docs/cleanup/` contains wave-1d.md through wave-2a.md
- [ ] `artifacts/baseline/` contains baseline files

### ✅ Checklist 2: CI Workflows
1. ➡️ Vào **Actions** tab
2. ➡️ Tìm workflow **"🧹 Cleanup Audit"**
3. ➡️ Click **"Run workflow"** → **"Run workflow"**
4. ➡️ Đợi workflow hoàn thành (should be ✅ green)
5. ➡️ Tìm workflow **"🗂️ Attic Dry-Run"** 
6. ➡️ Click **"Run workflow"** → **"Run workflow"**

### ✅ Checklist 3: Artifacts Generation
1. ➡️ Vào **Actions** → Click vào latest run
2. ➡️ Scroll xuống **"Artifacts"** section
3. ➡️ Download và kiểm tra:
   - `cleanup-audit-artifacts`
   - `attic-dryrun-artifacts`

---

## 📝 PR Templates

### Template 1: Wave-1d Merge
```
Title: cleanup-wave-1d (initial quarantine + tools)

Description:
- ✅ Initial file quarantine to _attic/
- ✅ Created analysis tools: import_graph.py, redundant_score.py
- ✅ Added PowerShell scripts for safe file moves
- ✅ Established CI gates for backup file detection

Review Checklist:
- [ ] _attic/ directory created
- [ ] tools/inventory/ contains analysis scripts
- [ ] scripts/windows/ contains attic_move.ps1
- [ ] CI workflow runs successfully
```

### Template 2: Wave-1e Merge
```
Title: cleanup-wave-1e (enhanced analysis + coverage)

Description:
- ✅ Enhanced import graph analysis
- ✅ Added coverage generation with smoke tests
- ✅ Improved redundant scoring algorithm
- ✅ Added near-duplicate detection

Review Checklist:
- [ ] artifacts/import_inbound.json generated
- [ ] artifacts/coverage.json generated
- [ ] artifacts/redundancy_report.csv generated
- [ ] Enhanced CI gates working
```

### Template 3: Wave-1f Merge
```
Title: cleanup-wave-1f (near-dupe consolidation + CI hardening)

Description:
- ✅ Near-duplicate detection and pilot selection
- ✅ Compatibility shims in stillme_compat/
- ✅ Enhanced CI gates with strict backup detection
- ✅ Weekly attic dry-run workflow

Review Checklist:
- [ ] stillme_compat/ package created
- [ ] artifacts/near_dupes.json generated
- [ ] CI workflows enhanced
- [ ] Weekly dry-run scheduled
```

### Template 4: Wave-2a Merge
```
Title: cleanup-wave-2a (attic eviction planning + baseline)

Description:
- ✅ Attic sweeper tool for eviction candidates
- ✅ Baseline snapshots after Wave-1f
- ✅ Enhanced CI gates with strict backup detection
- ✅ Weekly attic dry-run with artifact upload

Review Checklist:
- [ ] tools/inventory/attic_sweeper.py created
- [ ] artifacts/baseline/ contains snapshots
- [ ] Weekly dry-run workflow active
- [ ] Enhanced CI gates working
```

---

## 🚨 Troubleshooting

### Issue: _attic/ Not Visible After Merge
**Solution:**
1. ➡️ Check `.gitignore` for `_attic/` entries
2. ➡️ Add `!_attic/**` line
3. ➡️ Commit changes
4. ➡️ Wait for CI to run

### Issue: CI Workflows Failing
**Solution:**
1. ➡️ Check **Actions** tab for error details
2. ➡️ Look for missing dependencies
3. ➡️ Check file paths in workflows
4. ➡️ Re-run failed workflows

### Issue: Conflicts During Merge
**Solution:**
1. ➡️ Use **"Resolve conflicts"** button
2. ➡️ Apply **Conflict Resolution Rules**
3. ➡️ Keep cleanup-related files from newer branch
4. ➡️ Mark as resolved and commit

---

## 📈 Quick Reference (10 Steps)

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

---

## 🎯 Success Criteria

**Integration Complete When:**
- ✅ All 4 PRs merged to main
- ✅ `_attic/` directory visible and tracked
- ✅ CI workflows running successfully
- ✅ Artifacts being generated
- ✅ Baseline files in `artifacts/baseline/`
- ✅ Weekly dry-run scheduled and working

**Next Steps After Integration:**
- 📊 Monitor weekly attic dry-run results
- 🗑️ Review eviction candidates after 30 days
- 🚀 Plan Wave-2c: Controlled deletion of safe files
