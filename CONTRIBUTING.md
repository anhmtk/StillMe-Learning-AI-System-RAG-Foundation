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

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=. --cov-report=html

# Run specific test file
pytest tests/test_router_fallback.py
```

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
