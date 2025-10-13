# 🔧 GitHub Actions Stabilization Plan

## 📋 Current Workflow Analysis

### ✅ Keep Active (3 workflows)
- `gitleaks.yml` - Security scanning
- `security.yml` - Security & Ethics Tests  
- `security-ci.yml` - Security CI (if exists)

### 🔄 Disable to Manual Only (workflow_dispatch)
- `agentdev-ci.yml`
- `cd-prod.yml`
- `cd-staging.yml`
- `ci_tier1.yml`
- `ci_tier2_nightly.yml`
- `ci-agentdev-monitor.yml`
- `ci-autofix.yml`
- `ci-dast.yml`
- `ci-integration.yml`
- `ci-tests.yml`
- `ci-unit.yml`
- `continuous-testing.yml`
- `load-chaos.yml`
- `load-smoke.yml`
- `module-validation.yml`
- `no-ignore-gate.yml`
- `performance-test.yml`
- `security-scan.yml`
- `test_harness.yml`
- `test.yml`

### 📝 Missing Files to Create
- `cleanup-audit.yml` - Need to create (was referenced but missing)
- `attic-dryrun.yml` - Need to create (was referenced but missing)

## 🎯 Changes Required

### 1. Create Missing Cleanup Workflows
- Create `cleanup-audit.yml` with proper triggers and v4 artifacts
- Create `attic-dryrun.yml` with weekly schedule

### 2. Disable Legacy Workflows
- Change all non-security workflows to `workflow_dispatch` only
- Preserve YAML structure and comments

### 3. Branch & PR
- Create `ops/disable-legacy-ci` branch
- Commit with message: "ci: disable legacy workflows (manual only) + fix artifact v4 for cleanup-audit"
- Open PR to main

## 🚀 Implementation Steps

1. Create branch `ops/disable-legacy-ci`
2. Create missing cleanup workflows
3. Disable legacy workflows (change triggers)
4. Commit changes
5. Push branch and create PR
