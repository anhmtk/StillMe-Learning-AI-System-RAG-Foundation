# Contributing to StillMe

Thank you for your interest in contributing to StillMe! This guide will help you get started.

## 🚀 Development Setup

### Prerequisites
- Python 3.11 or 3.12
- Git
- (Optional) Docker for containerized development

### Step 1: Fork and Clone
```bash
# Fork the repository on GitHub, then:
git clone https://github.com/YOUR_USERNAME/StillMe-Learning-AI-System-RAG-Foundation.git
cd StillMe-Learning-AI-System-RAG-Foundation
```

### Step 2: Create Virtual Environment
```bash
# Create virtual environment
python -m venv venv

# Activate (Windows)
venv\Scripts\activate

# Activate (Linux/Mac)
source venv/bin/activate
```

### Step 3: Install Dependencies
```bash
# Install project dependencies
pip install -r requirements.txt

# Install development tools (optional but recommended)
pip install ruff mypy pytest pytest-cov pytest-asyncio
```

### Step 4: Setup Environment Variables
```bash
# Copy example env file
cp env.example .env

# Edit .env and add your API keys (at minimum, one of):
# DEEPSEEK_API_KEY=your_key_here
# OPENAI_API_KEY=your_key_here
```

### Step 5: Run Tests Locally
```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=backend --cov-report=html

# Run specific test file
pytest tests/test_router_smoke.py -v
```

### Step 6: Run Linting Locally
```bash
# Check code style with Ruff
ruff check .

# Auto-fix issues
ruff check . --fix

# Check formatting
ruff format --check .

# Auto-format
ruff format .
```

### Step 7: Start Development Server
```bash
# Start backend API
python start_backend.py

# Or with uvicorn directly
uvicorn backend.api.main:app --reload --port 8000

# Start dashboard (in another terminal)
streamlit run dashboard.py
```

## 🤝 How to Contribute

### Reporting Bugs
- Open an issue on GitHub with a clear description
- Include steps to reproduce
- Provide error logs if available
- Use the bug report template if available

### Suggesting Features
- Open a discussion or issue
- Explain the use case and benefits
- Be open to feedback and iteration
- Check existing issues/discussions first

### Code Contributions

1. **Fork the repository** on GitHub
2. **Create a feature branch** from `main`:
   ```bash
   git checkout -b feature/your-feature-name
   ```
3. **Make your changes** following code style guidelines
4. **Run tests and linting** before committing:
   ```bash
   pytest tests/ -v
   ruff check .
   ```
5. **Commit with clear messages**:
   ```bash
   git commit -m "feat: Add new feature description"
   ```
6. **Push to your fork**:
   ```bash
   git push origin feature/your-feature-name
   ```
7. **Submit a pull request** to `main` branch
8. **Ensure CI checks pass** (tests, linting)

### Good First Issues

Looking for a place to start? Check issues labeled:
- `good-first-issue` - Great for newcomers
- `help-wanted` - Community contributions welcome
- `documentation` - Improve docs

Common contribution areas:
- Add type hints to functions
- Refactor to dependency injection
- Complete SPICE implementation
- Add integration tests
- Improve documentation

## 🚀 Adding Support for New AI Models

StillMe supports multiple AI providers (DeepSeek, OpenAI, etc.). To add support for a new model:

### Step 1: Create the API Function

Create a new function in `backend/api/main.py`:

```python
async def call_[model]_api(prompt: str, api_key: str, detected_lang: str = 'en') -> str:
    """
    Call [Model Name] API
    
    IMPORTANT: Use build_system_prompt_with_language() to ensure
    output language matches input language.
    
    Args:
        prompt: User prompt
        api_key: API key or endpoint URL
        detected_lang: Detected language code
        
    Returns:
        AI-generated response string
    """
    try:
        # ✅ Use centralized system prompt builder
        system_content = build_system_prompt_with_language(detected_lang)
        
        # Make API call with your model's specific format
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                "[YOUR_API_ENDPOINT]",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "[model-name]",
                    "system": system_content,  # ✅ Use system prompt
                    "messages": [
                        {"role": "user", "content": prompt}
                    ],
                    "max_tokens": 2000,
                    "temperature": 0.7
                }
            )
            data = response.json()
            # Parse response according to your API's format
            return data["choices"][0]["message"]["content"]
    except Exception as e:
        logger.error(f"[Model] API error: {e}")
        return f"[Model] API error: {str(e)}"
```

### Step 2: Add to Model Router

In `generate_ai_response()` function, add your model check:

```python
# Check for API keys (priority order)
[model]_key = os.getenv("[MODEL]_API_KEY")
if [model]_key:
    return await call_[model]_api(prompt, [model]_key, detected_lang=detected_lang)
```

### Step 3: Update Documentation

- Add your model to `README.md` under supported models
- Update `env.example` with your API key variable
- Add any model-specific configuration notes

### Step 4: Test

- Test with different languages (English, Vietnamese, etc.)
- Verify language matching works correctly
- Test error handling

### Example: Adding Claude (Anthropic)

```python
# 1. Create function
async def call_claude_api(prompt: str, api_key: str, detected_lang: str = 'en') -> str:
    system_content = build_system_prompt_with_language(detected_lang)
    
    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": api_key,
                "anthropic-version": "2023-06-01",
                "Content-Type": "application/json"
            },
            json={
                "model": "claude-3-opus-20240229",
                "max_tokens": 2000,
                "system": system_content,
                "messages": [{"role": "user", "content": prompt}]
            }
        )
        data = response.json()
        return data["content"][0]["text"]

# 2. Add to router
anthropic_key = os.getenv("ANTHROPIC_API_KEY")
if anthropic_key:
    return await call_claude_api(prompt, anthropic_key, detected_lang=detected_lang)
```

## ✅ Why This Approach?

- **Consistency**: All models use the same language matching logic
- **Maintainability**: One place to update language instructions
- **Community-Friendly**: Clear, simple steps for contributors
- **Future-Proof**: Easy to extend without breaking existing code

## 📝 Code Style

- **Follow PEP 8** Python style guide
- **Use type hints** for function parameters and return types
- **Add docstrings** to all public functions and classes
- **Write clear, descriptive variable names**
- **Run Ruff** before committing: `ruff check . --fix`

### Type Hints Example
```python
from typing import Optional, List, Dict, Any

async def process_data(
    items: List[str],
    config: Optional[Dict[str, Any]] = None
) -> Dict[str, int]:
    """Process items and return statistics."""
    # Implementation
    return {"count": len(items)}
```

## 🧪 Testing

- **Add unit tests** for new features in `tests/` directory
- **Test error handling** and edge cases
- **Verify language matching** works correctly
- **Test with different input languages** (English, Vietnamese, etc.)
- **Aim for 80%+ coverage** for new code

### Test Structure
```python
# tests/test_your_feature.py
import pytest
from backend.your_module import your_function

def test_your_function_success():
    """Test successful case."""
    result = your_function("input")
    assert result == "expected_output"

def test_your_function_error():
    """Test error handling."""
    with pytest.raises(ValueError):
        your_function("invalid_input")
```

## ✅ Pre-Commit Checklist

Before submitting a PR, ensure:
- [ ] All tests pass: `pytest tests/ -v`
- [ ] Linting passes: `ruff check .`
- [ ] Code is formatted: `ruff format .`
- [ ] Type hints added (where applicable)
- [ ] Docstrings added for public functions
- [ ] README/docs updated if needed
- [ ] No `# type: ignore` comments (unless absolutely necessary)

## 📚 Questions?

- Open a discussion on GitHub
- Check existing issues
- Review the codebase

Thank you for contributing to StillMe! 🎉

