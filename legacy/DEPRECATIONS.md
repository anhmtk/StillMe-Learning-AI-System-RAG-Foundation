# 🗑️ Deprecations and Removal Plan

## Overview
This document tracks deprecated functionality and provides a timeline for their removal from the StillMe IPC system.

## Deprecation Policy
- **Notice Period**: 4 weeks minimum
- **Warning Period**: 2 weeks with runtime warnings
- **Removal**: After stability period
- **Documentation**: All deprecations documented with migration guides

## Current Deprecations

### None Currently
No functionality is currently marked for deprecation.

## Planned Deprecations

### 1. Legacy Dashboard Components
**Status**: Planned  
**Deprecation Date**: 2025-10-27  
**Removal Date**: 2025-11-24  
**Reason**: Replaced by unified dashboard system  

**Affected Files**:
- `dashboards/legacy/` (entire directory)
- `scripts/legacy_dashboard.py`
- `tests/test_legacy_dashboard.py`

**Migration Path**:
- Use `dashboards/streamlit/simple_app.py` for interactive dashboard
- Use `docs/dashboard/index.html` for static dashboard
- Update documentation references

**Action Required**:
- [ ] Add deprecation warnings to legacy components
- [ ] Update documentation with migration guide
- [ ] Notify all users of deprecation
- [ ] Create migration scripts if needed

### 2. Old Metrics System
**Status**: Planned  
**Deprecation Date**: 2025-11-03  
**Removal Date**: 2025-12-01  
**Reason**: Replaced by unified metrics system  

**Affected Files**:
- `stillme_core/legacy_metrics/` (entire directory)
- `scripts/old_metrics_aggregator.py`
- `tests/test_legacy_metrics.py`

**Migration Path**:
- Use `stillme_core/metrics/emitter.py` for metrics collection
- Use `scripts/aggregate_metrics.py` for aggregation
- Update configuration files

**Action Required**:
- [ ] Add deprecation warnings to legacy metrics
- [ ] Create migration guide
- [ ] Update configuration documentation
- [ ] Test migration process

## Deprecation Process

### 1. Announcement Phase (Week 1)
- [ ] Add deprecation notice to documentation
- [ ] Create migration guide
- [ ] Notify all developers and users
- [ ] Add deprecation warnings to code

### 2. Warning Phase (Weeks 2-3)
- [ ] Add runtime warnings for deprecated functionality
- [ ] Update error messages with migration information
- [ ] Monitor usage and provide support
- [ ] Collect feedback and adjust timeline if needed

### 3. Final Notice (Week 4)
- [ ] Send final removal notice
- [ ] Update all documentation
- [ ] Provide final migration support
- [ ] Prepare removal commit

### 4. Removal Phase (Week 5+)
- [ ] Remove deprecated code
- [ ] Update tests
- [ ] Update documentation
- [ ] Verify no breaking changes

## Migration Guides

### Legacy Dashboard Migration
```python
# Old way (deprecated)
from dashboards.legacy import LegacyDashboard
dashboard = LegacyDashboard()

# New way
from dashboards.streamlit.simple_app import SimpleDashboard
dashboard = SimpleDashboard()
```

### Legacy Metrics Migration
```python
# Old way (deprecated)
from stillme_core.legacy_metrics import LegacyMetrics
metrics = LegacyMetrics()

# New way
from stillme_core.metrics.emitter import get_metrics_emitter
metrics = get_metrics_emitter()
```

## Monitoring and Metrics

### Deprecation Tracking
- **Usage Metrics**: Track usage of deprecated functionality
- **Migration Progress**: Monitor migration completion
- **Support Requests**: Track support requests related to deprecations
- **Error Rates**: Monitor error rates during deprecation period

### Success Criteria
- **Zero Usage**: No usage of deprecated functionality after removal
- **Smooth Migration**: <5% of users need support during migration
- **No Breaking Changes**: No unexpected breaking changes
- **Clean Removal**: All deprecated code removed without issues

## Communication Plan

### Internal Communication
- **Developer Notifications**: Email and Slack notifications
- **Documentation Updates**: All relevant docs updated
- **Code Reviews**: Deprecation warnings in code reviews
- **Team Meetings**: Regular updates in team meetings

### External Communication
- **Release Notes**: Deprecation notices in release notes
- **Documentation**: Clear migration guides
- **Support**: Dedicated support for migration issues
- **Community**: Forum and GitHub issue updates

## Rollback Plan

### Emergency Rollback
If critical issues arise during deprecation:
1. **Immediate**: Revert deprecation warnings
2. **Short-term**: Extend deprecation timeline
3. **Long-term**: Re-evaluate deprecation decision

### Rollback Triggers
- **Critical Bugs**: Deprecation causes critical system issues
- **High Support Load**: >20% of users need migration support
- **Performance Issues**: Significant performance degradation
- **Security Issues**: Deprecation introduces security vulnerabilities

## Timeline Summary

| Phase | Duration | Key Activities |
|-------|----------|----------------|
| Announcement | 1 week | Documentation, notifications, warnings |
| Warning | 2 weeks | Runtime warnings, support, monitoring |
| Final Notice | 1 week | Final notifications, migration support |
| Removal | Ongoing | Code removal, cleanup, verification |

## Contact Information

**Deprecation Manager**: StillMe IPC Development Team  
**Email**: dev-team@stillme.ai  
**Slack**: #stillme-deprecations  
**GitHub**: https://github.com/stillme-ai/stillme/issues  

## Changelog

| Date | Change | Author |
|------|--------|--------|
| 2025-09-29 | Initial deprecation plan created | StillMe IPC Team |
| 2025-09-29 | Added legacy dashboard deprecation | StillMe IPC Team |
| 2025-09-29 | Added legacy metrics deprecation | StillMe IPC Team |
