# Contributing to StillMe Core Framework

Thank you for your interest in contributing to StillMe Core Framework!

## Philosophy

StillMe Core is built on these principles:

- **Transparency First**: All decisions are logged and explainable
- **Validation Mandatory**: Every response must pass validation
- **Intellectual Humility**: Honest about limitations and uncertainties
- **Modular Design**: Components are independent and extensible

## Getting Started

### Prerequisites

- Python 3.8+
- Git
- Understanding of the framework architecture (see [ARCHITECTURE.md](framework/ARCHITECTURE.md))

### Setup

1. **Clone the repository**:
```bash
git clone <repository-url>
cd StillMe-Learning-AI-System-RAG-Foundation
```

2. **Install dependencies**:
```bash
pip install -r requirements.txt
```

3. **Run tests**:
```bash
pytest tests/
```

## Contribution Areas

### 1. Adding New Validators

Validators ensure response quality. To add a new validator:

1. **Create validator class**:
```python
from stillme_core.validation import Validator, ValidationResult

class MyValidator(Validator):
    def run(self, answer: str, ctx_docs: List[str]) -> ValidationResult:
        # Your validation logic
        if self._check(answer):
            return ValidationResult(passed=True, reasons=[])
        else:
            return ValidationResult(
                passed=False,
                reasons=["My validation failed"]
            )
```

2. **Add to validation module**:
```python
# In stillme_core/validation/__init__.py
from .my_validator import MyValidator

__all__ = [..., "MyValidator"]
```

3. **Write tests**:
```python
def test_my_validator():
    validator = MyValidator()
    result = validator.run("answer", ["doc1", "doc2"])
    assert result.passed == True
```

4. **Update documentation**:
- Add to [VALIDATION.md](framework/VALIDATION.md)
- Update [API.md](framework/API.md)

### 2. Adding New Learning Fetchers

Fetchers retrieve content from external sources:

1. **Create fetcher class**:
```python
from stillme_core.learning import LearningFetcher

class MyFetcher(LearningFetcher):
    def fetch(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        # Fetch logic
        return [{"title": "...", "content": "...", ...}]
    
    def get_source_name(self) -> str:
        return "my_source"
```

2. **Add to learning module**:
```python
# In stillme_core/learning/fetchers/__init__.py
from .my_fetcher import MyFetcher

__all__ = [..., "MyFetcher"]
```

3. **Write tests and documentation**

### 3. Adding New External Data Providers

Providers fetch real-time data:

1. **Create provider class**:
```python
from stillme_core.external_data import ExternalDataProvider, ExternalDataResult

class MyProvider(ExternalDataProvider):
    async def fetch(self, query: str) -> ExternalDataResult:
        # Fetch logic
        return ExternalDataResult(
            success=True,
            data={"key": "value"},
            source="my_provider"
        )
```

2. **Register in orchestrator**:
```python
# In stillme_core/external_data/orchestrator.py
orchestrator.register_provider("my_intent", MyProvider())
```

3. **Write tests and documentation**

### 4. Improving Documentation

Documentation is crucial! Areas to improve:

- Code examples
- API documentation
- Architecture diagrams
- Tutorials
- Best practices

### 5. Bug Fixes

Found a bug? Great! Please:

1. **Create an issue** describing the bug
2. **Write a test** that reproduces the bug
3. **Fix the bug**
4. **Ensure tests pass**
5. **Submit a pull request**

## Development Workflow

### 1. Create a Branch

```bash
git checkout -b feature/my-feature
# or
git checkout -b fix/my-bugfix
```

### 2. Make Changes

- Write code
- Write tests
- Update documentation

### 3. Test Your Changes

```bash
# Run all tests
pytest tests/

# Run specific test
pytest tests/test_my_feature.py

# Run with coverage
pytest --cov=stillme_core tests/
```

### 4. Commit Changes

Follow conventional commits:

```bash
git commit -m "feat: add new validator for X"
git commit -m "fix: resolve issue with Y"
git commit -m "docs: update API documentation"
```

### 5. Submit Pull Request

1. Push your branch
2. Create pull request
3. Describe your changes
4. Link related issues

## Code Style

### Python Style

- Follow PEP 8
- Use type hints
- Write docstrings
- Keep functions focused

### Example

```python
from typing import List, Optional
from stillme_core.validation import Validator, ValidationResult

class MyValidator(Validator):
    """
    Validates something specific.
    
    This validator checks...
    """
    
    def run(self, answer: str, ctx_docs: List[str]) -> ValidationResult:
        """
        Run validation.
        
        Args:
            answer: The answer to validate
            ctx_docs: Context documents from RAG
            
        Returns:
            ValidationResult with passed status and reasons
        """
        # Implementation
        pass
```

## Testing Guidelines

### Unit Tests

- Test each component independently
- Cover edge cases
- Test error handling

### Integration Tests

- Test component interactions
- Test full pipelines
- Test error propagation

### Example Test

```python
import pytest
from stillme_core.validation import MyValidator, ValidationResult

def test_my_validator_passes():
    validator = MyValidator()
    result = validator.run("valid answer", ["doc1"])
    assert result.passed == True
    assert len(result.reasons) == 0

def test_my_validator_fails():
    validator = MyValidator()
    result = validator.run("invalid answer", ["doc1"])
    assert result.passed == False
    assert len(result.reasons) > 0
```

## Documentation Guidelines

### Code Documentation

- Write docstrings for all public APIs
- Include examples in docstrings
- Document parameters and return values

### User Documentation

- Update relevant guides
- Add examples
- Include use cases

## Review Process

1. **Automated Checks**: CI runs tests and linting
2. **Code Review**: Maintainers review code
3. **Feedback**: Address feedback and iterate
4. **Merge**: Once approved, changes are merged

## Questions?

- Check [Architecture Guide](framework/ARCHITECTURE.md)
- Check [API Reference](framework/API.md)
- Open an issue for questions

## Code of Conduct

- Be respectful
- Be constructive
- Be patient
- Be open to feedback

## License

By contributing, you agree that your contributions will be licensed under the same license as the project.

## Thank You!

Your contributions make StillMe Core better for everyone. Thank you for contributing!

