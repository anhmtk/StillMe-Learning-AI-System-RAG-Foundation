---
name: "[P1D] Cleanup Legacy Code (Archive, Don't Delete)"
about: Archive legacy code to separate branch, keep repo clean
title: "[P1D] Archive Legacy Code"
labels: type:maintenance, risk:low, area:docs, milestone:P1-Foundation
assignees: ''
---

## 🎯 Objective

Clean up repository by archiving legacy code to separate branch, improving maintainability without losing history.

## 📋 Scope

### Directories to Archive:
- `_graveyard/2025-01-27/` - 300+ legacy files
- `legacy/` - Legacy code and configurations

### Approach:
1. Create branch `archive/20250127`
2. Move legacy code to archive branch
3. Remove from main branch
4. Update README with "Archived Code" section

## ✅ Acceptance Criteria

1. **Main branch cleaner** - Legacy directories removed
2. **History preserved** - Archive branch contains all legacy code
3. **README updated** - Links to archive branch for reference
4. **No breaking changes** - Active code unaffected

## 🔍 Evidence & Self-Critique

### Current State:
- **Directory**: `_graveyard/2025-01-27/` - Contains 300+ files
- **Directory**: `legacy/` - Contains legacy code
- **Impact**: Makes repo harder to navigate, but code may be referenced

### Assumptions:
1. ✅ **Legacy code not used** - Verified no imports from legacy/
2. ⚠️ **May need reference** - Archive branch preserves access
3. ✅ **Git history preserved** - Archive branch maintains full history

### Risks & Mitigation:
- **Risk**: Accidentally delete needed code
  - **Mitigation**: Archive to branch first, verify no active imports, then remove
- **Risk**: Breaking references
  - **Mitigation**: Check for imports/references before removal
- **Rollback**: Merge archive branch back to main if needed

## 🧪 How to Verify

### Before Archive:
```bash
# Check for imports from legacy/
grep -r "from legacy" backend/
grep -r "import legacy" backend/

# Verify archive branch created
git branch | grep archive
```

### After Archive:
```bash
# Verify legacy/ removed from main
ls legacy/  # Should not exist

# Verify archive branch has code
git checkout archive/20250127
ls legacy/  # Should exist
```

## 📝 Implementation Plan

1. Create archive branch: `git checkout -b archive/20250127`
2. Verify no active imports from legacy/
3. Commit current state to archive branch
4. Switch back to main
5. Remove legacy directories
6. Update README with archive section
7. Commit cleanup
8. Push both branches

## 🔄 Rollback Plan

```bash
# Restore from archive branch
git checkout main
git merge archive/20250127 --no-ff

# Or cherry-pick specific files
git checkout archive/20250127 -- legacy/specific_file.py
```

