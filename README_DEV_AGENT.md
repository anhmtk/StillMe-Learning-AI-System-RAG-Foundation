# STILLME AI Framework - Development Guide

## 🚀 Quick Start

### Prerequisites
- Python 3.12+
- VS Code with Python extension
- All dependencies installed (see requirements.txt)

### Installation
```bash
# Install dependencies
pip install -r requirements.txt

# Install package in development mode
pip install -e .

# Run framework
python framework.py --once
```

## 🔧 VS Code Import Issues Fix

### Problem
VS Code shows import errors for packages that are already installed:
- `Import "cryptography.fernet" could not be resolved`
- `Import "ollama" could not be resolved`
- `Import "sentence_transformers" could not be resolved`
- `Import "pytest_asyncio" could not be resolved`

### Solution 1: Reload VS Code Window
1. Press `Ctrl+Shift+P`
2. Type "Developer: Reload Window"
3. Press Enter

### Solution 2: Select Python Interpreter
1. Press `Ctrl+Shift+P`
2. Type "Python: Select Interpreter"
3. Choose: `C:\Users\LENOVO\AppData\Local\Programs\Python\Python312\python.exe`

### Solution 3: Restart Python Language Server
1. Press `Ctrl+Shift+P`
2. Type "Python: Restart Language Server"
3. Press Enter

### Solution 4: Clear VS Code Cache
1. Close VS Code
2. Delete `.vscode` folder
3. Reopen VS Code
4. Re-select Python interpreter

## 📁 Project Structure

```
stillme_ai/
├── framework.py              # Main framework entry point
├── modules/                  # Core AI modules
│   ├── __init__.py          # Package initialization
│   ├── smart_gpt_api_manager_v1.py
│   ├── conversational_core_v1.py
│   ├── layered_memory_v1.py
│   ├── token_optimizer_v1.py
│   ├── secure_memory_manager.py
│   ├── persona_morph.py
│   └── content_integrity_filter.py
├── tests/                    # Test suite
├── config/                   # Configuration files
├── data/                     # Data storage
├── requirements.txt          # Dependencies
├── setup.py                  # Package setup
├── pyrightconfig.json        # Pyright configuration
└── .vscode/settings.json     # VS Code settings
```

## 🧪 Testing

### Run All Tests
```bash
python -m pytest tests/ -v
```

### Run Specific Module Tests
```bash
python -m pytest tests/test_secure_memory_manager.py -v
python -m pytest tests/test_persona_morph.py -v
```

### Run Framework
```bash
# Development mode (run once)
python framework.py --once

# Service mode
python framework.py

# Fast boot mode
python framework.py --fast
```

## 🔍 Troubleshooting

### Import Errors
- Verify packages are installed: `pip list`
- Check Python interpreter path
- Restart VS Code Python extension

### Framework Issues
- Check all dependencies: `pip install -r requirements.txt`
- Verify Python version: `python --version`
- Check environment variables

### Test Failures
- Set `OPENROUTER_API_KEY` for PersonaMorph tests
- Check mock configurations in conftest.py
- Verify test data files exist

## 📚 Dependencies

### Core Dependencies
- **cryptography**: Encryption and security
- **pytest-asyncio**: Async testing support
- **httpx**: HTTP client for API calls
- **sentence-transformers**: AI text processing
- **torch**: PyTorch for machine learning

### Optional Dependencies
- **ollama**: Local AI model support
- **fastapi**: Web framework
- **uvicorn**: ASGI server

## 🎯 Development Workflow

1. **Setup Environment**
   - Install Python 3.12+
   - Install dependencies
   - Configure VS Code

2. **Development**
   - Make changes to modules
   - Run tests to verify
   - Test framework integration

3. **Testing**
   - Run unit tests
   - Run integration tests
   - Test framework startup

4. **Deployment**
   - Verify all tests pass
   - Check framework startup
   - Deploy to production

## 🆘 Support

If you encounter issues:
1. Check this guide first
2. Verify all dependencies are installed
3. Check Python interpreter selection
4. Restart VS Code and Python extension
5. Check project configuration files

## 📝 Notes

- Framework startup time: ~7 seconds
- All 7 core modules are integrated
- Production ready with comprehensive testing
- Fast boot mode available for development
- Once mode available for testing
