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
- [Why StillMe?](#-why-stillme)
- [About the Founder](#-about-the-founder)
- [StillMe in Numbers](#-stillme-in-numbers)
- [Use Cases](#-use-cases)
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

### 🎯 Core Identity & Constitution

StillMe's foundational principle: **"I don't build an AI that knows everything. I build an AI that KNOWS IT DOESN'T KNOW — and has the courage to admit it. That's not a weakness. That's a SUPER POWER."**

**Key Principles:**
- **Intellectual Humility**: Knowing when we don't know is our core strength
- **Transparency**: Every decision, every learning source, every limitation is visible
- **Ethical Boundaries**: We know what NOT to do — we don't simulate emotions, claim consciousness, or replace human agency
- **Anti-Anthropomorphism**: StillMe explicitly states it is an AI system, not a human. All responses clarify StillMe's nature as a statistical model without subjective experience
- **Cultural Respect**: Built to serve a global community with diverse cultural and philosophical backgrounds
- **Scientific Honesty**: We distinguish between aspirational goals and measured results

**📜 Full Constitution:** See [`docs/CONSTITUTION.md`](docs/CONSTITUTION.md) for complete operating principles, ethical guidelines, and philosophical foundations.

**Tech Stack:**
- **Backend**: FastAPI, Python 3.12+
- **Vector DB**: ChromaDB with sentence-transformers embeddings
- **Frontend**: Streamlit dashboard
- **LLM**: DeepSeek, OpenAI GPT (configurable)

## 🤔 Why StillMe?

**The Problem:**
- **ChatGPT/Claude are black boxes** — You can't verify their sources or understand their decision-making
- **They hallucinate confidently** — No way to catch errors or verify claims
- **They're frozen in time** — Can't learn from new information published after their training cutoff
- **No transparency** — Hidden algorithms, hidden data sources, hidden decision-making processes

**StillMe's Solution:**
- ✅ **100% Transparent** — Every source is cited, every decision is visible, every line of code is public
- ✅ **Validated Responses** — Multi-layer validation chain reduces hallucinations through citation, evidence overlap, and confidence scoring
- ✅ **Continuously Learning** — Updates knowledge every 4 hours from trusted sources (RSS, arXiv, CrossRef, Wikipedia)
- ✅ **Open Source** — You can inspect, modify, and improve everything
- ✅ **Intellectual Humility** — StillMe knows when it doesn't know and has the courage to admit it

**Perfect for:**
- 🔬 **Researchers** who need verifiable sources and audit trails
- 💼 **Developers** building transparent AI applications
- 🏢 **Organizations** requiring accountability and compliance
- 🎓 **Educators** teaching students about AI transparency
- 🌍 **Anyone** who values honesty over false confidence

## 👤 About the Founder

StillMe was initiated by **Anh Nguyễn**, a Vietnamese founder passionate about transparent and responsible AI.

**What makes this story unique:** The founder doesn't have a formal IT background — demonstrating that with passion, vision, and modern AI tools, anyone can meaningfully contribute to the future of AI. This reflects an environment where innovation is not only possible but encouraged, where individuals can pursue ambitious AI projects that contribute to the global open-source community.

**However, StillMe is now a community-driven open-source project.** All knowledge is guided by intellectual humility and evidence-based principles, not personal authority. StillMe adheres to the **"evidence-over-authority"** principle: evidence and citations always take precedence over personal opinions.

> *"I don't build an AI that knows everything. I build an AI that KNOWS IT DOESN'T KNOW — and has the courage to admit it. That's not a weakness. That's a SUPER POWER."*

## 📊 StillMe in Numbers

- **634 questions** evaluated on TruthfulQA benchmark
- **99.7% citation rate** — Every response cites sources
- **70.9% transparency score** — Highest among evaluated systems
- **100% open source** — Every line of code is public
- **6 learning cycles/day** — Continuously updated knowledge base
- **30-50% cost reduction** — Pre-filter system reduces embedding costs
- **56% accuracy** — Competitive with GPT-4 (52%) on 50-question subset
- **0% ungrounded responses** — All answers are either cited or express uncertainty

## 💼 Use Cases

### Research & Academia
- Verifiable sources for academic work
- Audit trails for research assistance
- Transparent methodology for peer review

### Healthcare
- Transparent AI for medical information (with proper disclaimers)
- Source citations for medical claims
- Confidence scoring for critical decisions

### Legal
- Audit trail for legal research assistance
- Citation verification for legal claims
- Transparent decision-making processes

### Education
- Teaching students about AI transparency
- Demonstrating responsible AI development
- Learning tool with verifiable sources

### Enterprise
- Building transparent AI applications
- Compliance and accountability requirements
- Customizable validation chains

### Open Source Community
- Inspectable AI systems
- Community-driven learning
- Transparent governance

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
- ✅ Validator Chain - Reduces hallucinations through multiple validation checks
  - Citation validation (CitationRequired, CitationRelevance)
  - Evidence overlap checking (EvidenceOverlap)
  - Confidence scoring (0.0-1.0) with uncertainty detection
  - Language mismatch detection (LanguageValidator)
  - Ethics validation (EthicsAdapter)
  - Identity check (IdentityCheckValidator) - Prevents anthropomorphism
  - Ego neutrality (EgoNeutralityValidator) - Detects "Hallucination of Experience"
  - Source consensus (SourceConsensusValidator) - Detects contradictions between RAG sources
  - Factual hallucination detection (FactualHallucinationValidator)
  - Step-level validation (StepValidator) - Validates multi-step reasoning
  - Consistency checking (ConsistencyChecker) - Cross-validates claims
  - Fallback handling (FallbackHandler)
- ✅ Post-Processing System - Quality enhancement and variation
  - Quality evaluator - Rule-based quality assessment (0 token cost)
  - Rewrite engine - LLM-based answer refinement with retry mechanism
  - Style sanitizer - Removes anthropomorphic language
  - Honesty handler - Specialized processing for transparency questions
- ✅ Philosophical Question Processor - 3-layer system for consciousness/emotion questions
  - Intent classification (consciousness, emotion, understanding, mixed)
  - Sub-type detection (paradox, epistemic, meta, definitional, direct)
  - Varied answer templates (5 guard statements, 4 deep answer variations)
  - Anti-anthropomorphism enforcement - Explicitly states StillMe is AI system

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
External Sources → Learning Pipeline → Vector DB → RAG → Validator Chain → Post-Processing → Response
```

**Components:**
- **External Sources**: RSS, arXiv, CrossRef, Wikipedia, Stanford Encyclopedia
- **Learning Pipeline**: Scheduler → Source Integration → Pre-Filter → Content Curator → Embedding → ChromaDB
- **RAG System**: ChromaDB (vector search) + LLM (response generation)
- **Validator Chain**: Multi-layer validation (11 validators) ensuring quality and reducing hallucinations
- **Post-Processing**: Quality evaluation → Rewrite engine (with retry) → Style sanitization
- **Philosophical Processor**: Specialized 3-layer system for consciousness/emotion questions
- **Dashboard**: Streamlit UI for monitoring and interaction

**Data Flow:**
1. Scheduler triggers learning cycle every 4 hours
2. Source Integration fetches from enabled sources
3. Pre-Filter removes low-quality content (saves embedding costs by 30-50%)
4. Content Curator prioritizes based on knowledge gaps
5. Embedding Service converts text to vectors (all-MiniLM-L6-v2, 384 dims)
6. ChromaDB stores vectors for semantic search
7. User query → Intent detection (philosophical/factual) → RAG retrieval → LLM generation
8. Response → Validator Chain (11 validators) → Post-processing (quality eval + rewrite) → Final response

**Anti-Anthropomorphism Mechanisms:**
- **Identity Check Validator**: Detects and prevents anthropomorphic language
- **Ego Neutrality Validator**: Catches "Hallucination of Experience" (claims of personal experience)
- **Philosophical Processor**: Explicitly states StillMe is AI system, not human
- **Style Sanitizer**: Removes emotional language and personal experience claims
- **Guard Statements**: Every philosophical answer includes clear statement that StillMe is AI

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
- [`docs/CONSTITUTION.md`](docs/CONSTITUTION.md) - **Core Identity & Operating Principles** (Constitutional Framework)
- [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) - System architecture details
- [`docs/PHILOSOPHY.md`](docs/PHILOSOPHY.md) - Philosophy and vision
- [`docs/API_DOCUMENTATION.md`](docs/API_DOCUMENTATION.md) - Complete API reference
- [`docs/DEPLOYMENT_GUIDE.md`](docs/DEPLOYMENT_GUIDE.md) - Deployment instructions
- [`docs/PAPER.md`](docs/PAPER.md) - **Research Paper: StillMe Framework for Transparent, Validated RAG Systems**
- [`docs/PAPER_TABLES_FIGURES.md`](docs/PAPER_TABLES_FIGURES.md) - Tables and figures for the paper

**User Guides:**
- [`docs/GETTING_STARTED.md`](docs/GETTING_STARTED.md) - Quick start guide (5 minutes)
- [`docs/USER_GUIDE.md`](docs/USER_GUIDE.md) - Complete user guide
- [`docs/FAQ.md`](docs/FAQ.md) - Frequently asked questions

**Development:**
- [`CONTRIBUTING.md`](CONTRIBUTING.md) - Contributing guidelines
- [`docs/PLATFORM_ENGINEERING_ROADMAP.md`](docs/PLATFORM_ENGINEERING_ROADMAP.md) - Technical roadmap

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
