# 🔧 StillMe AI Maintenance Guide

This guide provides comprehensive instructions for maintaining the StillMe AI codebase, focusing on code quality, testing, and system reliability.

## 📋 Table of Contents

- [Code Quality Maintenance](#code-quality-maintenance)
- [Testing & Validation](#testing--validation)
- [Import Optimization](#import-optimization)
- [System Health Checks](#system-health-checks)
- [Performance Monitoring](#performance-monitoring)
- [Troubleshooting](#troubleshooting)

## 🎯 Code Quality Maintenance

### Regular Maintenance Tasks

#### 1. Import Optimization
Run import optimization tools regularly to maintain code quality:

```bash
# Optimize imports across all modules
python tools/simple_import_optimizer.py stillme_core,agent_dev,tests

# Analyze code complexity
python tools/code_quality_analyzer.py

# Check for circular dependencies
python tools/import_cycle_scan.py stillme_core,agent_dev
```

#### 2. Code Quality Metrics
Monitor these key metrics:

- **Import Density**: Should be < 15% per file
- **Cyclomatic Complexity**: Should be < 20 per function
- **Code Coverage**: Should be > 95%
- **Test Pass Rate**: Should be 100%

#### 3. Pre-commit Hooks
Ensure all pre-commit hooks are working:

```bash
# Install pre-commit hooks
pre-commit install

# Run all hooks
pre-commit run --all-files

# Update hooks
pre-commit autoupdate
```

## 🧪 Testing & Validation

### System Validation Tests

Run comprehensive system validation after any major changes:

```bash
# Run all system validation tests
python -m pytest tests/test_system_validation.py -v

# Run specific test categories
python -m pytest tests/test_system_validation.py::TestSystemValidation::test_framework_import -v
python -m pytest tests/test_system_validation.py::TestSystemValidation::test_learning_system_import -v
python -m pytest tests/test_system_validation.py::TestSystemValidation::test_agentdev_import -v
```

### Test Coverage Requirements

- **Framework Tests**: 100% pass rate required
- **Learning System Tests**: 100% pass rate required
- **AgentDev Tests**: 100% pass rate required
- **Config Bootstrap Tests**: 100% pass rate required

### Smoke Tests

Run smoke tests to validate basic functionality:

```bash
# AgentDev canary test
python -m pytest tests/test_agentdev_canary.py -v

# Config bootstrap test
python -m pytest tests/test_config_bootstrap.py -v

# Connectivity test
python -m pytest tests/test_connectivity.py -v
```

## 🔄 Import Optimization

### When to Run Import Optimization

Run import optimization in these scenarios:

1. **After adding new modules**
2. **Before major releases**
3. **When import density > 15%**
4. **When circular dependencies detected**
5. **Monthly maintenance cycle**

### Import Optimization Process

#### Step 1: Analyze Current State
```bash
# Check import density
python tools/code_quality_analyzer.py

# Scan for circular dependencies
python tools/import_cycle_scan.py stillme_core,agent_dev,tests
```

#### Step 2: Optimize Imports
```bash
# Run optimization (safe mode)
python tools/simple_import_optimizer.py stillme_core,agent_dev,tests

# Verify no syntax errors
python -m pyright stillme_core/ agent_dev/ --ignoreexternal
```

#### Step 3: Validate Changes
```bash
# Run system validation tests
python -m pytest tests/test_system_validation.py -v

# Run smoke tests
python -m pytest tests/test_agentdev_canary.py tests/test_config_bootstrap.py -v
```

### Import Optimization Best Practices

1. **Always backup before optimization**
2. **Run tests after each optimization**
3. **Commit changes incrementally**
4. **Document any manual fixes needed**
5. **Monitor build times for improvements**

## 🏥 System Health Checks

### Daily Health Checks

Run these checks daily to ensure system stability:

```bash
# Framework initialization
python -c "from stillme_core.framework import StillMeFramework; fw = StillMeFramework(); print('Framework OK')"

# Learning system import
python -c "import stillme_core.learning; print('Learning System OK')"

# AgentDev import
python -c "import agent_dev.core.agentdev; print('AgentDev OK')"

# Config bootstrap
python -c "import stillme_core.config_bootstrap; print('Config Bootstrap OK')"
```

### Weekly Health Checks

Run comprehensive health checks weekly:

```bash
# Full system validation
python -m pytest tests/test_system_validation.py -v

# Import optimization check
python tools/import_cycle_scan.py stillme_core,agent_dev,tests

# Code quality analysis
python tools/code_quality_analyzer.py
```

### Monthly Health Checks

Perform deep maintenance monthly:

```bash
# Full import optimization
python tools/simple_import_optimizer.py stillme_core,agent_dev,tests

# Comprehensive testing
python -m pytest tests/ -v --tb=short

# Security scan
make security

# Performance analysis
python tools/code_quality_analyzer.py
```

## 📊 Performance Monitoring

### Key Performance Indicators

Monitor these metrics regularly:

#### Code Quality Metrics
- **Import Density**: Target < 15%
- **Cyclomatic Complexity**: Target < 20
- **Test Coverage**: Target > 95%
- **Build Time**: Monitor for regressions

#### System Performance Metrics
- **Import Time**: Should be < 2 seconds
- **Test Execution Time**: Should be < 30 seconds
- **Memory Usage**: Should be stable
- **CPU Usage**: Should be minimal during idle

### Performance Monitoring Tools

```bash
# Monitor import performance
time python -c "import stillme_core.framework"

# Monitor test performance
time python -m pytest tests/test_system_validation.py

# Monitor memory usage
python -m memory_profiler tools/code_quality_analyzer.py
```

## 🚨 Troubleshooting

### Common Issues and Solutions

#### 1. Import Errors After Optimization

**Symptoms**: ModuleNotFoundError, ImportError
**Solution**:
```bash
# Check for missing __init__.py files
find . -name "*.py" -exec dirname {} \; | sort -u | xargs -I {} touch {}/__init__.py

# Verify Python path
python -c "import sys; print(sys.path)"

# Re-run optimization with verbose output
python tools/simple_import_optimizer.py stillme_core,agent_dev,tests --verbose
```

#### 2. Circular Dependency Issues

**Symptoms**: ImportError: cannot import name
**Solution**:
```bash
# Detect circular dependencies
python tools/import_cycle_scan.py stillme_core,agent_dev,tests

# Fix using dependency resolver
python tools/fix_import_dependencies.py stillme_core,agent_dev,tests

# Use lazy imports where needed
# Example: from typing import TYPE_CHECKING
```

#### 3. Test Failures After Changes

**Symptoms**: Test failures in system validation
**Solution**:
```bash
# Run tests with verbose output
python -m pytest tests/test_system_validation.py -v -s

# Check specific failing tests
python -m pytest tests/test_system_validation.py::TestSystemValidation::test_framework_import -v

# Verify environment variables
python -c "import os; print('STILLME_DRY_RUN:', os.getenv('STILLME_DRY_RUN', '0'))"
```

#### 4. Performance Degradation

**Symptoms**: Slow imports, slow tests
**Solution**:
```bash
# Profile import performance
python -m cProfile -s cumtime -c "import stillme_core.framework"

# Check for unnecessary imports
python tools/code_quality_analyzer.py

# Optimize imports
python tools/simple_import_optimizer.py stillme_core,agent_dev,tests
```

### Emergency Procedures

#### System Recovery
If the system becomes unstable:

1. **Restore from backup**
2. **Run system validation tests**
3. **Check import optimization status**
4. **Verify all dependencies**
5. **Run smoke tests**

#### Rollback Procedure
```bash
# Rollback to previous working state
git log --oneline -10
git checkout <previous-working-commit>

# Verify system health
python -m pytest tests/test_system_validation.py -v

# Re-apply changes incrementally
```

## 📚 Additional Resources

### Documentation
- [README.md](../README.md) - Main project documentation
- [CONTRIBUTING.md](../CONTRIBUTING.md) - Contribution guidelines
- [SECURITY.md](../SECURITY.md) - Security policies

### Tools Reference
- `tools/simple_import_optimizer.py` - Import optimization
- `tools/code_quality_analyzer.py` - Code quality analysis
- `tools/import_cycle_scan.py` - Circular dependency detection
- `tools/fix_import_dependencies.py` - Dependency fixes

### Test Suites
- `tests/test_system_validation.py` - System validation tests
- `tests/test_agentdev_canary.py` - AgentDev canary tests
- `tests/test_config_bootstrap.py` - Config bootstrap tests
- `tests/test_connectivity.py` - Connectivity tests

## 🤝 Contributing

When contributing to StillMe AI:

1. **Follow the maintenance procedures**
2. **Run all validation tests**
3. **Ensure import optimization compliance**
4. **Document any changes**
5. **Update this guide if needed**

For questions or issues, please open a GitHub issue or contact the maintainers.

---

**Last Updated**: Wave-06 Documentation & Maintenance Phase
**Version**: 2.1.0
**Maintainer**: StillMe AI Team
