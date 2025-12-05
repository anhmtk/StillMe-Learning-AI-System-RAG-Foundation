# StillMe Codebase Assistant

StillMe can now understand and explain its own codebase using RAG-based code retrieval.

## Overview

**Status:** ✅ Phase 1 Complete | 🚧 Phase 2 In Progress

- **Indexed:** 255 files, 377 chunks (backend, stillme_core, frontend)
- **Capabilities:** Code Q&A with file:line citations
- **Safety:** Read-only explanations, no code modifications

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

## Indexing

Codebase is indexed on Railway. To re-index:

```powershell
.\scripts\index_codebase_railway.ps1 -ApiKey "YOUR_API_KEY"
```

Or via API (requires authentication):
```bash
POST /api/codebase/index
```

## Roadmap

- ✅ **Phase 1:** Code Q&A with RAG retrieval
- 🚧 **Phase 2:** Test generation & code review
- 📋 **Phase 3:** Git history integration & onboarding mentor

📚 **Full Implementation Details:** [`CODEBASE_ASSISTANT_IMPLEMENTATION.md`](CODEBASE_ASSISTANT_IMPLEMENTATION.md)

