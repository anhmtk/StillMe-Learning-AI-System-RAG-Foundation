---
name: "[P1C] Fix Failing Tests & Stabilize CI"
about: Fix test failures and ensure CI pipeline is green
title: "[P1C] Fix Failing Tests & Stabilize CI"
labels: type:test, risk:low, area:ci, milestone:P1-Foundation
assignees: ''
---

## 🎯 Objective

Ensure all tests pass in CI pipeline and stabilize test execution.

## 📋 Scope

### Current State:
- **Test files**: 15 files (verified)
- **Test functions**: 167 functions (verified)
- **CI status**: [UNVERIFIED - need to check GitHub Actions]

### Tasks:
1. Identify failing tests
2. Fix legitimate failures
3. Skip flaky tests (with reason) if needed
4. Ensure CI workflow passes

## ✅ Acceptance Criteria

1. **All tests pass** - No errors, only expected skips
2. **CI workflow green** - GitHub Actions Tests workflow passes
3. **No new warnings** - Security scans (gitleaks) pass
4. **Test stability** - No flaky tests in CI

## 🔍 Evidence & Self-Critique

### Current Test Status:
```bash
# Command: pytest tests/ -q --tb=no
# Result: "=================== 1 skipped, 1 warning, 1 error in 9.13s ===================="
```

### Assumptions:
1. ⚠️ **Some tests may be flaky** - Need to identify and fix or skip
2. ✅ **Test infrastructure works** - pytest, fixtures, mocks are set up
3. ⚠️ **CI environment differences** - May need to adjust for CI vs local

### Risks & Mitigation:
- **Risk**: Fixing tests breaks functionality
  - **Mitigation**: Review test failures carefully, ensure fixes don't hide real bugs
- **Risk**: Skipping too many tests
  - **Mitigation**: Only skip truly flaky tests, document reason, create follow-up issue
- **Rollback**: Revert test changes individually

## 🧪 How to Verify

### Local Testing:
```bash
# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/test_rss_fetcher.py -v

# Run with coverage
pytest tests/ --cov=backend --cov-report=term
```

### CI Verification:
- Check GitHub Actions: https://github.com/anhmtk/StillMe-Learning-AI-System-RAG-Foundation/actions
- Verify Tests workflow is green
- Verify no new security warnings

## 📝 Implementation Plan

1. Run full test suite locally
2. Identify failing tests
3. Categorize failures (legitimate bugs vs flaky tests)
4. Fix legitimate failures
5. Skip flaky tests with `@pytest.mark.skip(reason="...")`
6. Verify CI passes
7. Document skipped tests in test file comments

## 🔄 Rollback Plan

```bash
# Revert specific test file
git checkout HEAD -- tests/test_<file>.py

# Or revert all test changes
git revert <commit-hash>
```

