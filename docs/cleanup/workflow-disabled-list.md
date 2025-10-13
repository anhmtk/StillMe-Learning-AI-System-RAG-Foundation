# 🔧 Workflows Disabled to Manual Only

## ✅ Successfully Disabled (workflow_dispatch only)

### Legacy CI/CD Workflows
- `agentdev-ci.yml` - AgentDev CI
- `cd-prod.yml` - Production deployment
- `cd-staging.yml` - Staging deployment
- `ci_tier1.yml` - Tier 1 CI
- `ci_tier2_nightly.yml` - Tier 2 nightly CI
- `ci-agentdev-monitor.yml` - AgentDev monitoring
- `ci-autofix.yml` - Auto-fix CI
- `ci-dast.yml` - DAST testing
- `ci-integration.yml` - Integration testing
- `ci-tests.yml` - General CI tests
- `ci-unit.yml` - Unit testing
- `continuous-testing.yml` - Continuous testing
- `load-chaos.yml` - Chaos testing
- `load-smoke.yml` - Smoke testing
- `module-validation.yml` - Module validation
- `no-ignore-gate.yml` - No-ignore gate
- `performance-test.yml` - Performance testing
- `security-scan.yml` - Security scanning
- `test_harness.yml` - Test harness
- `test.yml` - General testing

## 🔒 Kept Active (Security & Cleanup)

### Security Workflows
- `gitleaks.yml` - Security scanning (active)
- `security.yml` - Security & Ethics Tests (active)
- `security-ci.yml` - Security CI (active)

### Cleanup Workflows (Newly Created)
- `cleanup-audit.yml` - Cleanup audit (active, v4 artifacts)
- `attic-dryrun.yml` - Weekly attic dry-run (active)

## 📊 Summary
- **Total workflows**: 24
- **Disabled to manual**: 20
- **Kept active**: 4 (3 security + 1 cleanup)
- **Newly created**: 2 (cleanup workflows)

## 🎯 Impact
- Reduced CI noise and resource usage
- Focused on essential security and cleanup workflows
- Legacy workflows still available via manual trigger
- Fixed deprecation warnings (upload-artifact v3 → v4)
