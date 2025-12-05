# StillMe Codebase Assistant

StillMe can now understand and explain its own codebase using RAG-based code retrieval, generate tests, and review code.

## Overview

**Status:** ✅ Phase 3 Complete

- **Indexed:** 255 files, 377 chunks (backend, stillme_core, frontend)
- **Git History:** 50+ commits indexed (design decisions, implementation history)
- **Capabilities:** 
  - Code Q&A with file:line citations
  - Test generation (pytest format)
  - Code review (static + LLM analysis)
  - Git history queries ("Why did we choose X?")
  - Onboarding mentor (personalized guides for new contributors)
- **Safety:** Read-only explanations, review-only suggestions, no auto-fix

## Usage

### API Endpoint

**POST** `/api/codebase/query`

Query the codebase and get explanations with code citations.

**Request:**
```json
{
  "question": "How does the validation chain work?",
  "n_results": 5,
  "include_code": true
}
```

**Response:**
```json
{
  "question": "How does the validation chain work?",
  "explanation": "The validation chain orchestrates...",
  "code_chunks": [...],
  "citations": ["chain.py:45-78"]
}
```

**Example Questions:**
- "How does the validation chain work?"
- "What is the RAG retrieval process?"
- "How does StillMe track task execution time?"
- "StillMe sử dụng mô hình embedding nào?" (Vietnamese supported)

**Stats:** `GET /api/codebase/stats` - Returns collection statistics

### Test Generation

**POST** `/api/codebase/generate-tests`

Generate unit tests for code snippets or files.

**Request:**
```json
{
  "code_content": "def add(a, b): return a + b",
  "test_framework": "pytest",
  "include_edge_cases": true,
  "include_error_handling": true
}
```

**Response:**
```json
{
  "test_code": "import pytest\ndef test_add():\n    ...",
  "test_file_path": "tests/test_generated.py",
  "coverage_estimate": 100,
  "test_cases": ["test_add_positive", "test_add_negative", ...]
}
```

**Features:**
- Generates pytest-formatted tests
- Includes happy path, edge cases, error handling
- Uses codebase context for better test quality
- Returns test code (user must review before using)

### Code Review

**POST** `/api/codebase/review`

Review code for issues and suggest improvements.

**Request:**
```json
{
  "code_content": "import os\n\ndef badName():\n    file = open('test.txt')\n    return file.read()",
  "check_style": true,
  "check_security": true,
  "check_performance": true
}
```

**Response:**
```json
{
  "issues": [
    {
      "severity": "warning",
      "type": "unused_import",
      "message": "Import 'os' is unused",
      "suggestion": "Remove unused import"
    },
    {
      "severity": "error",
      "type": "missing_error_handling",
      "message": "File operations should use try-except",
      "suggestion": "Use context manager: with open('test.txt') as f:"
    }
  ],
  "summary": {
    "total": 2,
    "errors": 1,
    "warnings": 1,
    "info": 0
  },
  "score": 75
}
```

**Features:**
- Static analysis: unused imports, unreachable code, naming issues
- LLM analysis: style, security, performance
- Code quality score (0-100)
- Safety: Review only, no auto-fix

## Indexing

Codebase is indexed on Railway. To re-index:

```powershell
.\scripts\index_codebase_railway.ps1 -ApiKey "YOUR_API_KEY"
```

Or via API (requires authentication):
```bash
POST /api/codebase/index
```

## Safety Boundaries

- **Read-only**: Code explanations only, no modifications
- **Review-only**: Code review suggests fixes, never auto-applies
- **User review required**: Generated tests must be reviewed before use
- **No auto-fix**: All suggestions require manual approval

## Roadmap

- ✅ **Phase 1:** Code Q&A with RAG retrieval
- ✅ **Phase 2:** Test generation & code review
- 📋 **Phase 3:** Git history integration & onboarding mentor

📚 **Full Implementation Details:** [`CODEBASE_ASSISTANT_IMPLEMENTATION.md`](CODEBASE_ASSISTANT_IMPLEMENTATION.md)

