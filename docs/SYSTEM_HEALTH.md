# System Health Report

**Generated:** 2025-09-27T15:39:44.493397  
**Overall Status:** FAIL

## Summary

- **Total Checks:** 6
- **Passed:** 3 ✅
- **Failed:** 2 ❌
- **Warnings:** 1 ⚠️

### Critical Gates

- **Critical Checks:** ❌ FAIL
- **Security (High=0):** ❌ FAIL (13 high severity)
- **Coverage (≥85%):** ❌ FAIL (0.0%)

## Detailed Results

### Unit Tests ❌

**Status:** FAIL

- Tests: 0
- Passed: 0
- Failed: 0
- Coverage: 0.0%

### Security Scan ❌

**Status:** FAIL

- Bandit: 13H/27M/163L
- Semgrep: 0H/0M/0L
- Total High Severity: 13

### Ethics Tests ✅

**Status:** PASS

- Tests: 0
- Passed: 0
- Failed: 0

### Open Ports ✅

**Status:** PASS

- No dangerous ports open

### Library Versions ⚠️

**Status:** WARN

- Missing Libraries: scikit-learn

### Core Functionality ✅

**Status:** PASS

- Router Loaded: True
- Core Imports: True
- Model Selected: llama3:8b

## Artifacts

- **Detailed Results:** `reports/health_check.json`
- **Coverage Report:** `artifacts/coverage/index.html`
- **Security Reports:** `artifacts/bandit-report.json`, `artifacts/semgrep-report.json`

## Next Steps

- ❌ **System health check failed** - address critical issues before proceeding
- Fix critical check failures
- Resolve 13 high severity security issues
- Increase test coverage to ≥85% (currently 0.0%)
