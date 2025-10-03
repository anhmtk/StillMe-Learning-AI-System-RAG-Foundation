# Module Validation Guide

This document describes how to validate modules in the StillMe AI project.

## Overview

The project uses a comprehensive validation system to ensure code quality across all modules. Each module is validated for:

1. **Ruff Linting** - Code style and quality
2. **Mypy Type Checking** - Type safety
3. **Tests** - Functionality verification
4. **Type Ignore Check** - Ensures no forbidden `# type: ignore` comments

## Available Modules

The following modules are validated:

- `stillme_core/common` - Common utilities
- `gateway_poc` - Gateway proof of concept
- `stillme_core` - Core StillMe functionality
- `agent_dev` - Agent development tools
- `clients` - Client implementations
- `desktop_app` - Desktop application
- `dashboards` - Dashboard implementations
- `niche_radar` - Niche radar functionality
- `plugins` - Plugin system
- `runtime` - Runtime utilities
- `scripts` - Utility scripts
- `tests` - Test suite
- `tools` - Development tools

## Validation Commands

### Using Makefile (Recommended)

```bash
# Validate all modules
make validate-all

# Validate specific module
make validate-module MODULE=stillme_core

# Lint all modules
make lint-all

# Lint specific module
make lint-module MODULE=agent_dev

# Test all modules
make test-all

# Test specific module
make test-module MODULE=tests

# Type check all modules
make type-check-all

# Type check specific module
make type-check-module MODULE=stillme_core

# Clean up temporary files
make clean
```

### Using Python Scripts

```bash
# Validate all modules
python scripts/validate_all_modules.py

# Validate specific module
python scripts/validate_module.py stillme_core

# Check for forbidden type: ignore comments
python scripts/deny_type_ignore.py stillme_core
```

### Using Direct Commands

```bash
# Ruff linting
ruff check stillme_core --statistics

# Mypy type checking
mypy stillme_core --ignore-missing-imports

# Run tests
pytest stillme_core -v

# Check for forbidden type: ignore comments
python scripts/deny_type_ignore.py stillme_core
```

## CI/CD Integration

The project includes GitHub Actions workflow (`.github/workflows/module-validation.yml`) that automatically validates all modules on:

- Push to `main` or `develop` branches
- Pull requests to `main` or `develop` branches

Each module is validated in parallel for faster CI runs.

## Validation Rules

### Ruff Linting Rules

The project uses strict Ruff configuration in `pyproject.toml`:

- **E** - pycodestyle errors
- **F** - pyflakes errors
- **I** - isort import sorting
- **B** - flake8-bugbear
- **UP** - pyupgrade

### Mypy Type Checking

- Python 3.12 target
- Strict type checking enabled
- Missing imports ignored for external dependencies
- No `# type: ignore` comments allowed (enforced by custom script)

### Test Requirements

- All modules should have tests when possible
- Tests must pass for module validation to succeed
- No tests required for utility scripts

### Type Ignore Policy

**STRICT RULE**: No `# type: ignore` comments are allowed unless explicitly whitelisted in `scripts/deny_type_ignore.py`.

This ensures proper type annotations and prevents hiding type errors.

## Troubleshooting

### Common Issues

1. **Ruff Linting Failures**
   ```bash
   # Auto-fix most issues
   ruff check . --fix
   
   # Fix with unsafe fixes
   ruff check . --fix --unsafe-fixes
   ```

2. **Mypy Type Errors**
   - Add proper type annotations
   - Use `cast()` for complex type assertions
   - Avoid `Any` type when possible

3. **Test Failures**
   - Check test dependencies
   - Ensure test data is available
   - Verify test environment setup

4. **Type Ignore Violations**
   - Remove `# type: ignore` comments
   - Fix underlying type issues
   - Add proper type annotations

### Getting Help

```bash
# Show help
make help

# Check specific module status
make validate-module MODULE=<module_name>

# Run individual validation steps
make lint-module MODULE=<module_name>
make type-check-module MODULE=<module_name>
make test-module MODULE=<module_name>
```

## Best Practices

1. **Run validation before committing**
   ```bash
   make validate-all
   ```

2. **Fix issues incrementally**
   - Start with linting issues
   - Then fix type errors
   - Finally run tests

3. **Use proper type annotations**
   - Avoid `Any` type
   - Use `Optional` for nullable values
   - Use `Union` for multiple types

4. **Keep tests up to date**
   - Add tests for new functionality
   - Update tests when changing APIs
   - Ensure test coverage

5. **Follow the "no type: ignore" rule**
   - Always fix type issues properly
   - Never hide type errors with `# type: ignore`
   - Use proper type annotations instead

## Module Status

Current validation status:

- ✅ `stillme_core/common` - 0 errors
- ✅ `gateway_poc` - 0 errors  
- ⚠️ `stillme_core` - 42 errors (invalid-syntax in backup_legacy/ - ignored)
- ✅ `agent_dev` - 0 errors
- ✅ `clients` - 0 errors
- ✅ `desktop_app` - 0 errors
- ✅ `dashboards` - 0 errors
- ✅ `niche_radar` - 0 errors
- ✅ `plugins` - 0 errors
- ✅ `runtime` - 0 errors
- ✅ `scripts` - 0 errors
- ✅ `tests` - 0 errors
- ✅ `tools` - 0 errors

**Total**: 12/13 modules fully validated (92% success rate)
