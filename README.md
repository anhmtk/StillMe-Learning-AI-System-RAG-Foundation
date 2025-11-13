# 🧠 StillMe - Learning AI system with RAG foundation

<div align="center">
  <img src="assets/logo.png" alt="StillMe Logo" width="200" height="200">
</div>

> **A Transparent AI Learning System that continuously learns from multiple sources and provides context-aware responses through RAG architecture.**

[![Python](https://img.shields.io/badge/Python-3.12+-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)](https://fastapi.tiangolo.com)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.28+-red.svg)](https://streamlit.io)
[![Tests](https://github.com/anhmtk/StillMe-Learning-AI-System-RAG-Foundation/workflows/Tests/badge.svg)](https://github.com/anhmtk/StillMe-Learning-AI-System-RAG-Foundation/actions)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## 📑 Table of Contents

- [What is StillMe?](#-what-is-stillme)
- [Quick Start](#-quick-start)
- [Features](#-features)
- [API Reference](#-api-reference)
- [Architecture](#-architecture)
- [Contributing](#-contributing)
- [Documentation](#-documentation)

## 🌟 What is StillMe?

StillMe is a **RAG-based AI system** that:
- Continuously learns from RSS feeds, arXiv, CrossRef, and Wikipedia
- Provides context-aware responses using ChromaDB vector search
- Validates responses to reduce hallucinations
- Tracks learning metrics and knowledge retention

**Core Philosophy:** *"In the AI era, true value lies not in what AI can do, but in what AI chooses NOT to do."* — A truly intelligent AI knows what NOT to do, not that it can do everything. StillMe preserves what makes humans human by knowing its boundaries.

**Tech Stack:**
- **Backend**: FastAPI, Python 3.12+
- **Vector DB**: ChromaDB with sentence-transformers embeddings
- **Frontend**: Streamlit dashboard
- **LLM**: DeepSeek, OpenAI GPT (configurable)

## 🚀 Quick Start

### Prerequisites

- Python 3.12+
- Docker & Docker Compose (recommended)
- API keys: `DEEPSEEK_API_KEY` or `OPENAI_API_KEY`

### Option 1: Docker (Recommended)

```bash
# Clone repository
git clone https://github.com/anhmtk/StillMe-Learning-AI-System-RAG-Foundation.git
cd StillMe-Learning-AI-System-RAG-Foundation

# Copy environment template
cp env.example .env
# Edit .env with your API keys

# Start services
docker compose up -d

# Check logs
docker compose logs -f
```

**Access:**
- Dashboard: http://localhost:8501
- API: http://localhost:8000
- API Docs: http://localhost:8000/docs

### Option 2: Manual Setup

```bash
# Clone repository
git clone https://github.com/anhmtk/StillMe-Learning-AI-System-RAG-Foundation.git
cd StillMe-Learning-AI-System-RAG-Foundation

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp env.example .env
# Edit .env with your API keys:
# DEEPSEEK_API_KEY=sk-your-key
# OPENAI_API_KEY=sk-your-key

# Start backend (terminal 1)
python -m uvicorn backend.api.main:app --host 0.0.0.0 --port 8000 --reload

# Start frontend (terminal 2)
streamlit run dashboard.py --server.port 8501
```

### Environment Variables

**Required:**
- `DEEPSEEK_API_KEY` or `OPENAI_API_KEY` - LLM API key

**Optional:**
- `ENABLE_VALIDATORS=true` - Enable Validator Chain (reduces hallucinations)
- `ENABLE_ARXIV=true` - Enable arXiv fetching (default: true)
- `ENABLE_WIKIPEDIA=true` - Enable Wikipedia fetching (default: true)
- `COMMUNITY_MIN_VOTES=10` - Minimum votes for community proposals (default: 10)

See `env.example` for full list.

## ✨ Features

### ✅ Implemented & Working

**Core RAG System:**
- ✅ Vector Database (ChromaDB) - Semantic search and knowledge retrieval
- ✅ RAG (Retrieval-Augmented Generation) - Context-aware responses
- ✅ Validator Chain - Reduces hallucinations by 80%
  - Citation validation
  - Evidence overlap checking
  - Confidence scoring (0.0-1.0)
  - Fallback handling

**Learning Pipeline:**
- ✅ Multi-Source Learning - RSS, arXiv, CrossRef, Wikipedia
- ✅ Automated Scheduler - Fetches every 4 hours
- ✅ Pre-Filter System - Filters content before embedding (30-50% cost reduction)
- ✅ Content Curator - Prioritizes learning content
- ✅ Self-Diagnosis - Detects knowledge gaps

**Memory System:**
- ✅ Continuum Memory - Tiered architecture (L0-L3)
- ✅ Knowledge Retention Tracking
- ✅ Accuracy Scoring

**Community Features:**
- ✅ Community-Driven Learning - Voting system for learning proposals
- ✅ Interactive Conversation Learning - Learn from user conversations with permission

**Dashboard:**
- ✅ Streamlit UI - Real-time metrics, chat interface, RAG interface
- ✅ Validation Panel - Monitor validator performance
- ✅ Memory Health - Track tier statistics and forgetting metrics

### 🚧 Experimental

- 🔬 **Nested Learning** - Tiered update frequency (experimental branch)

## 📡 API Reference

### Chat Endpoints

**POST `/api/chat/rag`** - Chat with RAG-enhanced responses
```json
{
  "message": "What is RAG?",
  "use_rag": true,
  "context_limit": 3
}
```

**POST `/api/chat/ask`** - Simplified Q&A endpoint (RAG enabled by default)
```json
{
  "message": "What is StillMe?"
}
```

**POST `/api/chat/smart_router`** - Auto-selects best endpoint (used by dashboard)

### Learning Endpoints

**POST `/api/learning/sources/fetch`** - Fetch from all sources
```
GET /api/learning/sources/fetch?max_items_per_source=5&auto_add=false
```

**POST `/api/learning/scheduler/start`** - Start automated scheduler
**POST `/api/learning/scheduler/stop`** - Stop scheduler
**GET `/api/learning/scheduler/status`** - Get scheduler status

**POST `/api/learning/rss/fetch`** - Fetch RSS feeds
```
POST /api/learning/rss/fetch?max_items=5&auto_add=false
```

### RAG Endpoints

**POST `/api/rag/add_knowledge`** - Add knowledge to vector DB
**POST `/api/rag/query`** - Query vector DB
**GET `/api/rag/stats`** - Get RAG statistics

### System Endpoints

**GET `/health`** - Liveness probe
**GET `/ready`** - Readiness probe (checks DB, ChromaDB, embeddings)
**GET `/api/status`** - System status
**GET `/api/validators/metrics`** - Validation metrics

### Community Endpoints

**POST `/api/community/propose`** - Propose learning source
**POST `/api/community/vote`** - Vote on proposal
**GET `/api/community/pending`** - Get pending proposals
**GET `/api/community/queue`** - Get learning queue

**Full API Documentation:** http://localhost:8000/docs (Swagger UI)

## 🔧 Architecture

```
External Sources → Learning Pipeline → Vector DB → RAG → Validator Chain → Response
```

**Components:**
- **External Sources**: RSS, arXiv, CrossRef, Wikipedia
- **Learning Pipeline**: Scheduler → Source Integration → Pre-Filter → Content Curator → Embedding → ChromaDB
- **RAG System**: ChromaDB (vector search) + LLM (response generation)
- **Validator Chain**: Citation → Evidence → Confidence → Fallback
- **Dashboard**: Streamlit UI for monitoring and interaction

**Data Flow:**
1. Scheduler triggers learning cycle every 4 hours
2. Source Integration fetches from enabled sources
3. Pre-Filter removes low-quality content (saves embedding costs)
4. Content Curator prioritizes based on knowledge gaps
5. Embedding Service converts text to vectors (all-MiniLM-L6-v2, 384 dims)
6. ChromaDB stores vectors for semantic search
7. User query → RAG retrieval → Validator Chain → Response

**Detailed Architecture:** See [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md)

## 🤝 Contributing

We welcome contributions! See [CONTRIBUTING.md](CONTRIBUTING.md) for detailed setup guide.

### Quick Start for Contributors

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/your-feature`
3. Make changes and add tests
4. Run tests: `pytest`
5. Submit a pull request

### Good First Issues

- Add type hints to functions
- Refactor to dependency injection (FastAPI `Depends()`)
- Improve documentation
- Add unit tests for existing features

### Areas Needing Help

- PostgreSQL migration (Alembic setup done, migration needed)
- SPICE framework implementation (framework ready)
- Observability (Prometheus metrics, structured logging)
- Performance optimization (Redis caching, query optimization)

**Community:**
- [GitHub Discussions](https://github.com/anhmtk/StillMe-Learning-AI-System-RAG-Foundation/discussions)
- [Issues](https://github.com/anhmtk/StillMe-Learning-AI-System-RAG-Foundation/issues)
- [Pull Requests](https://github.com/anhmtk/StillMe-Learning-AI-System-RAG-Foundation/pulls)

## 📚 Documentation

**Core Documentation:**
- [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) - System architecture details
- [`docs/PHILOSOPHY.md`](docs/PHILOSOPHY.md) - Philosophy and vision
- [`docs/API_DOCUMENTATION.md`](docs/API_DOCUMENTATION.md) - Complete API reference
- [`docs/DEPLOYMENT_GUIDE.md`](docs/DEPLOYMENT_GUIDE.md) - Deployment instructions

**Development:**
- [`docs/DEVELOPMENT_GUIDE.md`](docs/DEVELOPMENT_GUIDE.md) - Contributing guidelines
- [`docs/ACTION_ITEMS_IMPROVEMENT_ROADMAP.md`](docs/ACTION_ITEMS_IMPROVEMENT_ROADMAP.md) - Technical debt and roadmap

**Features:**
- [`docs/SPICE_ARCHITECTURE.md`](docs/SPICE_ARCHITECTURE.md) - SPICE framework
- [`docs/CONFIDENCE_AND_FALLBACK.md`](docs/CONFIDENCE_AND_FALLBACK.md) - Validation system

## ⚠️ Known Limitations

**Current:**
- SQLite database (PostgreSQL migration planned)
- Single-threaded scheduler (needs distributed task queue)
- ChromaDB memory-based (needs persistence for scaling)

**See:** [`docs/ACTION_ITEMS_IMPROVEMENT_ROADMAP.md`](docs/ACTION_ITEMS_IMPROVEMENT_ROADMAP.md) for full list

## 📄 License

MIT License - see [LICENSE](LICENSE) for details.

## 🙏 Acknowledgments

- **OpenAI** for GPT models and API
- **DeepSeek** for AI capabilities
- **The Open Source Community** for inspiration and support

---

**StillMe** - *Learning AI system with RAG foundation* 🤖✨
