# 🔧 GitHub Actions Stabilization - UI Guide

## 📋 Summary of Changes Made

### ✅ Files Created
- `.github/workflows/cleanup-audit.yml` - New cleanup audit workflow (v4 artifacts)
- `.github/workflows/attic-dryrun.yml` - New weekly attic dry-run workflow

### ✅ Files Modified (Disabled to Manual Only)
- `.github/workflows/agentdev-ci.yml` - Changed to workflow_dispatch only
- `.github/workflows/ci_tier1.yml` - Changed to workflow_dispatch only
- `.github/workflows/ci-tests.yml` - Changed to workflow_dispatch only
- `.github/workflows/ci-unit.yml` - Changed to workflow_dispatch only
- `.github/workflows/continuous-testing.yml` - Changed to workflow_dispatch only
- `.github/workflows/test.yml` - Changed to workflow_dispatch only

### 🔒 Files Kept Active (Security & Cleanup)
- `.github/workflows/gitleaks.yml` - Security scanning (active)
- `.github/workflows/security.yml` - Security & Ethics Tests (active)
- `.github/workflows/security-ci.yml` - Security CI (active)
- `.github/workflows/cleanup-audit.yml` - Cleanup audit (active)
- `.github/workflows/attic-dryrun.yml` - Weekly attic dry-run (active)

## 🚀 Next Steps (UI Actions)

### 1. Create Branch
1. ➡️ Go to GitHub → Code tab
2. ➡️ Click "main" branch dropdown
3. ➡️ Type "ops/disable-legacy-ci" in "Find or create a branch"
4. ➡️ Click "Create branch: ops/disable-legacy-ci from main"

### 2. Commit Changes
1. ➡️ Go to "Changes" tab (should show modified files)
2. ➡️ Add commit message: "ci: disable legacy workflows (manual only) + fix artifact v4 for cleanup-audit"
3. ➡️ Click "Commit changes"

### 3. Create Pull Request
1. ➡️ Click "Compare & pull request" button
2. ➡️ Set base: `main`, compare: `ops/disable-legacy-ci`
3. ➡️ Title: "ci: disable legacy workflows (manual only) + fix artifact v4 for cleanup-audit"
4. ➡️ Description:
```markdown
## 🔧 GitHub Actions Stabilization

### Changes Made
- ✅ **Created 2 new cleanup workflows** with v4 artifacts:
  - `cleanup-audit.yml` - Cleanup audit with strict backup file detection
  - `attic-dryrun.yml` - Weekly attic dry-run with artifact upload

- ✅ **Disabled 6 legacy workflows** to manual trigger only:
  - `agentdev-ci.yml`, `ci_tier1.yml`, `ci-tests.yml`
  - `ci-unit.yml`, `continuous-testing.yml`, `test.yml`

- 🔒 **Kept 3 security workflows active**:
  - `gitleaks.yml`, `security.yml`, `security-ci.yml`

### Impact
- 🎯 **Reduced CI noise** - Only essential workflows run automatically
- 🔒 **Enhanced security** - Security workflows remain active
- 🧹 **Added cleanup monitoring** - New cleanup audit and attic dry-run
- ⚡ **Fixed deprecation** - Upgraded upload-artifact from v3 to v4

### Verification
- [ ] Security workflows still active
- [ ] Cleanup workflows created and functional
- [ ] Legacy workflows available via manual trigger
- [ ] No deprecation warnings in Actions
```

5. ➡️ Click "Create pull request"

## 🎯 Expected Results

### After PR Merge
- **Active workflows**: 5 (3 security + 2 cleanup)
- **Manual-only workflows**: 6+ (legacy workflows)
- **CI resource usage**: Significantly reduced
- **Security coverage**: Maintained
- **Cleanup monitoring**: Enhanced

### Verification Checklist
- [ ] `gitleaks.yml` runs on push/PR
- [ ] `security.yml` runs on push/PR  
- [ ] `cleanup-audit.yml` runs on push/PR
- [ ] `attic-dryrun.yml` runs weekly
- [ ] Legacy workflows available via "Run workflow" button
- [ ] No deprecation warnings in Actions logs

## 🚨 Troubleshooting

### If PR Fails
- Check Actions tab for error details
- Verify YAML syntax in modified workflows
- Ensure all required files are included

### If Workflows Don't Run
- Check workflow triggers in Actions tab
- Verify branch protection rules
- Check workflow permissions

### If Security Workflows Disabled
- Immediately re-enable by reverting changes
- Check `.github/workflows/security*.yml` files
- Verify `gitleaks.yml` is still active
