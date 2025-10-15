# Contributing to StillMe AI Framework

Thank you for your interest in contributing to StillMe! This document provides guidelines for contributing to the project.

## Getting Started

1. Fork the repository
2. Clone your fork: `git clone https://github.com/YOUR_USERNAME/stillme_ai.git`
3. Create a feature branch: `git checkout -b feature/your-feature-name`
4. Install dependencies: `pip install -r requirements.txt`
5. Install pre-commit hooks: `pre-commit install`

## Development Setup

### Running Tests

#### System Validation Tests (Required)
Before submitting any changes, run the comprehensive system validation tests:

```bash
# Run all system validation tests (REQUIRED)
python -m pytest tests/test_system_validation.py -v

# Run specific validation tests
python -m pytest tests/test_system_validation.py::TestSystemValidation::test_framework_import -v
python -m pytest tests/test_system_validation.py::TestSystemValidation::test_learning_system_import -v
python -m pytest tests/test_system_validation.py::TestSystemValidation::test_agentdev_import -v
```

#### Standard Test Suite
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=. --cov-report=html

# Run specific test file
pytest tests/test_router_fallback.py

# Run smoke tests
python -m pytest tests/test_agentdev_canary.py tests/test_config_bootstrap.py -v
```

#### Test Requirements
- **System validation tests**: Must pass 100%
- **Framework tests**: Must pass 100%
- **Learning system tests**: Must pass 100%
- **AgentDev tests**: Must pass 100%
- **Config bootstrap tests**: Must pass 100%

### Import Optimization (Required)

StillMe AI maintains strict import optimization standards. All contributions must comply with these requirements:

#### Import Optimization Tools
```bash
# Check import density and complexity
python tools/code_quality_analyzer.py

# Scan for circular dependencies
python tools/import_cycle_scan.py stillme_core,agent_dev,tests

# Optimize imports (if needed)
python tools/simple_import_optimizer.py stillme_core,agent_dev,tests
```

#### Import Requirements
- **Import density**: Must be < 15% per file
- **No circular dependencies**: All imports must be acyclic
- **Standardized import order**: Follow PEP 8 import ordering
- **No duplicate imports**: Each import should appear only once
- **Lazy imports**: Use `TYPE_CHECKING` for type-only imports

#### Before Submitting
1. Run import optimization tools
2. Verify no circular dependencies
3. Check import density is acceptable
4. Run system validation tests
5. Ensure all imports work correctly

### Code Style

We use the following tools for code quality:

- **Black**: Code formatting
- **Ruff**: Linting and import sorting
- **detect-secrets**: Secret detection

Run these before committing:

```bash
black .
ruff check --fix .
detect-secrets scan
```

## Pull Request Process

1. Ensure all tests pass: `pytest`
2. Run code quality checks: `pre-commit run --all-files`
3. Update documentation if needed
4. Submit a pull request with a clear description

## Documentation

- **README.md**: Main project documentation (English, AI-assisted translation)
- **API Documentation**: In `docs/` directory
- **Code Comments**: Please add clear comments for complex logic

## Language Note

The maintainer is not fluent in English. Documentation is written with AI assistance. If you find unclear language or grammar issues, please:

1. Open an issue with the specific text
2. Suggest improvements
3. Help improve the documentation

## Code of Conduct

Please be respectful and constructive in all interactions. We welcome contributors from all backgrounds and experience levels.

## Security

- **DO NOT** open public issues for security vulnerabilities
- Report security issues privately via SECURITY.md
- **DO NOT** commit secrets, API keys, or sensitive data

## Questions?

Feel free to open an issue for questions or clarifications. We appreciate your help in making StillMe better!
