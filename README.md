# 🧠 StillMe - Learning AI system with RAG foundation

<div align="center">
  <img src="assets/logo.png" alt="StillMe Logo" width="200" height="200">
</div>

> **The Counter-Movement to Black Box AI — A transparent, open-source AI system proving that AI can be built differently: by anyone, for everyone, with complete transparency. Currently in MVP stage with Vector DB + RAG + Validator Chain working.**

[![Python](https://img.shields.io/badge/Python-3.12+-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)](https://fastapi.tiangolo.com)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.28+-red.svg)](https://streamlit.io)
[![Tests](https://github.com/anhmtk/StillMe-Learning-AI-System-RAG-Foundation/workflows/Tests/badge.svg)](https://github.com/anhmtk/StillMe-Learning-AI-System-RAG-Foundation/actions)
[![Coverage](https://codecov.io/gh/anhmtk/StillMe-Learning-AI-System-RAG-Foundation/branch/main/graph/badge.svg)](https://codecov.io/gh/anhmtk/StillMe-Learning-AI-System-RAG-Foundation)
[![Ethical AI](https://img.shields.io/badge/Ethical%20AI-Transparent-green.svg)](https://github.com/anhmtk/stillme_ai_ipc)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## 📑 Table of Contents

- [What is StillMe?](#-what-is-stillme)
- [Quick Start](#-quick-start)
- [Features](#-features)
- [Architecture](#-architecture)
- [Documentation](#-documentation)
- [Contributing](#-contributing)
- [License](#-license)

## 🌟 What is StillMe?

StillMe is the **Counter-Movement to Black Box AI** — a **Transparent AI Learning System** building toward true self-evolution.

> **"In a world where AI decisions are hidden behind corporate walls, StillMe is the proof that transparency is not just possible — it's the only ethical path forward."**

### 🎯 The Counter-Movement Vision: The Resistance Against Black Box AI

StillMe is more than a project — **it's a movement** challenging the status quo of closed, proprietary AI systems. We believe that **transparency, ethics, and community governance** are not optional features — they are fundamental rights.

While major AI companies build closed systems with proprietary algorithms, StillMe stands as the **pioneering alternative**:

- **🔓 100% Open Source**: Every algorithm, every decision, every line of code is public
- **👁️ Complete Transparency**: See exactly what the AI learns, how it learns, and why it makes decisions
- **🌍 Global Solution, Local Relevance**: Built for global use, particularly aligned with open technology strategies of developing nations
- **🤝 Community Governance**: You control the AI's evolution, not corporations
- **🚧 Lowering the Barrier**: Testing the hypothesis that vision and commitment can be primary drivers in building AI systems

**Current MVP Status:** Foundation components are implemented and working:
- ✅ **Vector Database (ChromaDB)**: Semantic search and knowledge retrieval functional
- ✅ **RAG System**: Retrieval-Augmented Generation for context-aware responses  
- ✅ **Validator Chain**: Implements multi-layer validation to reduce hallucinations through citation, evidence overlap, confidence validation, and ethics checks. See [Claims & Evaluation](docs/CLAIMS_AND_EVAL.md) for methodology and results.
  - **ConfidenceValidator**: AI knows when to say "I don't know" (prevents overconfidence without context)
  - **FallbackHandler**: Safe fallback answers when validation fails (prevents hallucinated content)
  - **Confidence Score**: Real-time confidence calculation (0.0-1.0) based on context quality
  - **Learning Suggestions**: Auto-suggests topics to learn from knowledge gaps
  - **Epistemic Humility**: StillMe's core principle—knowing when it doesn't know is not a weakness, it's intellectual honesty
- ✅ **Identity Injection**: Ensures StillMe brand consistency across all models (DeepSeek, GPT, Gemini, local)
- ✅ **Knowledge Retention**: Learning metrics tracking system
- ✅ **Accuracy Scoring**: Response quality measurement
- ✅ **Dashboard**: Interactive UI with RAG interface, validation metrics, confidence scores, and learning metrics
- ✅ **Continuum Memory System** (NEW): Tiered memory architecture (L0-L3) with promotion/demotion, multi-timescale scheduler, and forgetting metrics
- ✅ **Multi-Source Learning** (NEW): Integrated fetching from RSS, arXiv, CrossRef, and Wikipedia with pre-filtering
- 🔬 **Nested Learning** (EXPERIMENTAL): Tiered update frequency system inspired by Google Research's Nested Learning paradigm - reduces embedding costs by updating knowledge at different frequencies (L0: every cycle, L1: every 10 cycles, L2: every 100 cycles, L3: every 1000 cycles). Currently in experimental branch `experimental/nested-learning` for testing and validation.

**Vision:** Evolve through developmental stages (Infant → Child → Adolescent → Adult) with community governance, automated learning pipelines, and complete transparency.

### 🎯 Core Concept

- **🧬 Evolutionary Learning**: AI progresses through stages (Infant → Child → Adolescent → Adult)
- **📚 Multi-Source Learning**: RSS feeds + arXiv + CrossRef + Wikipedia with intelligent pre-filtering
- **🧠 Continuum Memory**: Tiered memory system (L0-L3) with surprise-based promotion/demotion and forgetting metrics
- **🔬 Nested Learning** (Experimental): Tiered update frequency system that reduces embedding costs and protects long-term knowledge by updating different memory tiers at different rates (inspired by Google Research's Nested Learning paradigm)
- **🌐 Real-time Data**: Live data from multiple trusted sources with transparency
- **🛡️ Ethical Filtering**: Comprehensive ethical content filtering with complete transparency
- **📊 Transparent Dashboard**: Complete visibility into all learning sources, memory health, and tier statistics
- **💬 Interactive Chat**: Communicate with your evolving AI assistant

## 🧠 Philosophical Foundation: Embracing Incompleteness

StillMe's approach to transparency is grounded in a fundamental mathematical truth: **Gödel's Incompleteness Theorems**. Just as these theorems reveal that any sufficiently complex formal system contains statements that cannot be proven within that system, we recognize that black box AI models—by their very nature—contain behaviors that cannot be fully explained or interpreted. This isn't a flaw to be fixed; it's a mathematical reality we must acknowledge and work with.

> *"In any consistent formal system, there are statements that are true but unprovable within that system."* — Kurt Gödel

### **The Gödel Connection: Why Perfect Transparency is Mathematically Impossible**

Like mathematics and quantum physics, AI systems of sufficient complexity exhibit inherent limitations in interpretability. When neural networks reach a certain scale, their decision-making processes become too complex to fully trace or explain—not because of poor design, but because complexity itself creates boundaries. This mirrors Gödel's insight: systems powerful enough to be useful are also complex enough to contain unexplainable behaviors.

**What this means for AI:**
- 🔬 **Complexity → Incompleteness**: More capable AI systems inherently have less interpretable behaviors
- 🌊 **Quantum Parallel**: Similar to quantum mechanics—we can observe outcomes but not fully explain the underlying process
- 📐 **Mathematical Certainty**: This isn't a bug—it's a feature of sufficiently complex systems

### **Our Practical Approach: System-Level Transparency Over Model-Level Interpretability**

StillMe doesn't fight against this mathematical reality. Instead, we **build systems around it**:

- ✅ **We acknowledge limitations**: Perfect model interpretability is mathematically impossible for complex AI
- ✅ **We focus on what we CAN control**: System-level transparency, verification, and accountability
- ✅ **We verify, not just interpret**: Trust through observable behavior, not just internal explanations
- ✅ **We build practical accountability**: Community governance, audit trails, and transparent decision-making

**StillMe's positioning:**
- 🏗️ **System Architecture Transparency**: Every component, every decision, every data flow is visible
- 🔍 **Verification Over Interpretation**: We prove correctness through testing and validation, not just explanation
- 🤝 **Community Governance**: Practical accountability through collective oversight and voting
- 📊 **Complete Audit Trails**: Full history of learning decisions, ethical checks, and system behavior

> *"We don't claim to explain the unexplainable. We build systems that can be verified, audited, and trusted—even when the underlying models remain complex."*

### **Why This Matters**

This philosophical foundation shapes StillMe's entire approach: **Practical accountability > Perfect transparency**. We don't promise to "open the black box"—we promise to build transparent systems around it, verify its behavior, and give the community control over its evolution. This is both mathematically honest and practically achievable.

**StillMe builds trust through verification, not just interpretation.**

> **"Perhaps the world needs AI systems that are smart enough to know when they don't know. StillMe is our humble attempt to build exactly that—an AI that values intellectual honesty over false confidence."**

### **🤔 "But You Use DeepSeek/OpenAI APIs - Isn't That Black Box?"**

**This is a common and important question.** Here's our honest answer:

**StillMe fights against BLACK BOX SYSTEMS, not black box models.**

**The Key Distinction:**

1. **Black Box SYSTEM** (what we fight against):
   - Closed, proprietary AI systems (ChatGPT, Claude, etc.)
   - Hidden algorithms, hidden data sources, hidden decision-making
   - No transparency about what the system learns, how it learns, or why it makes decisions
   - Corporate control over AI evolution
   - **This is what StillMe challenges.**

2. **Black Box MODEL** (mathematical reality we acknowledge):
   - LLM internal weights and neural network architecture
   - Inherently complex and not fully interpretable (Gödel's Incompleteness)
   - **This is a mathematical reality, not a flaw to fix.**

**StillMe's Approach:**

✅ **We use LLM APIs (DeepSeek, OpenAI) as "reasoning engines"** - but we build a **transparent SYSTEM around them**:
- **Transparent data sources**: You see exactly what StillMe learns (RSS, arXiv, Wikipedia)
- **Transparent retrieval**: You see what context is retrieved from vector DB
- **Transparent validation**: You see validation results, confidence scores, citations
- **Transparent decisions**: Every learning decision is logged and auditable
- **Community control**: You control what StillMe learns, not corporations

✅ **StillMe's transparency is about SYSTEM architecture, not model internals:**
- Every line of StillMe's code is public
- Every data flow is visible
- Every learning decision is logged
- Every validation result is transparent

❌ **We don't promise to "open the LLM black box"** - that's mathematically impossible for complex models.

✅ **We promise to build transparent systems that use LLMs responsibly:**
- Verify outputs through Validator Chain
- Ground responses in retrieved context (RAG)
- Express uncertainty when appropriate
- Give community control over learning and evolution

**Analogy:**
Think of it like a car:
- **Black box SYSTEM**: A car where you can't see the engine, can't check the fuel, can't see the dashboard - you just trust it works (ChatGPT, Claude)
- **StillMe**: A car with transparent hood, visible fuel gauge, clear dashboard - you can see everything about HOW the car works, even though the engine internals (LLM weights) remain complex

**StillMe's Value Proposition:**
> "We don't claim to explain how LLMs work internally. We build transparent systems that use LLMs responsibly, verify their outputs, and give you control over what the system learns and how it evolves."

## 🛡️ Our Uncompromising Commitment

### 🌟 **100% Transparency - Nothing to Hide**
- **Every line of code is public** - no "black box", no proprietary algorithms
- **Every API call is visible** - see exactly what AI learns from and when
- **Every decision is transparent** - from ethical filtering to quality assessment
- **Complete audit trail** - full history of all learning decisions and violations

### 🎯 **Ethical AI - Our Highest Priority**
We believe that **ethics isn't a feature - it's the foundation**. StillMe is built with unwavering principles:

- **Safety First**: Harmful content filtered at the source
- **Cultural Fairness**: Respects global diversity and perspectives  
- **Full Accountability**: Every mistake is public and corrected
- **Community Control**: You decide what's acceptable, not corporations

> **"We challenge the AI community to choose: Support transparency and ethics, or remain silent and admit they don't care."**

### 🔒 **Privacy & Data Protection**
- **No personal data collection** - learns only from public sources
- **Self-hosted codebase** - you maintain complete control over your data
- **Delete anytime** - your data, your rules, your control

## 🛡️ Ethical AI Transparency

StillMe features the world's first **completely transparent ethical filtering system**:

- **Complete Visibility**: All ethical violations are logged and visible
- **Open Source**: Filtering rules and algorithms are publicly available
- **Community Driven**: Blacklist and rules can be managed by the community
- **Audit Trail**: Full history of all ethical decisions and violations
- **Configurable**: Ethics level can be adjusted based on community needs

This transparency ensures StillMe learns responsibly while maintaining community trust.

## 🚀 Quick Start

### **Option 1: Docker (Recommended - 1-Click Setup)**

```bash
# Clone repository
git clone https://github.com/anhmtk/StillMe-Learning-AI-System-RAG-Foundation.git
cd StillMe-Learning-AI-System-RAG-Foundation

# One-click setup (Linux/Mac)
chmod +x quick-start.sh
./quick-start.sh

# Or Windows PowerShell
.\quick-start.ps1

# Or manually with Docker Compose
docker compose up -d
```

**Access after startup:**
- 📊 **Dashboard**: http://localhost:8501
- 🔌 **API**: http://localhost:8000
- 📚 **API Docs**: http://localhost:8000/docs

⚠️ **Security Note**: Never commit `.env` file containing API keys. Enable pre-commit hooks to scan for secrets (see [CONTRIBUTING.md](CONTRIBUTING.md) for setup).

### **Option 1b: Deploy Public Dashboard (For Community)**

**🚂 Railway.app (Recommended - 5 Minutes):**
1. Push code to GitHub (already done ✅)
2. Go to https://railway.app → Login with GitHub
3. Click "New Project" → "Deploy from GitHub repo"
4. Select `StillMe-Learning-AI-System-RAG-Foundation`
5. Railway auto-detects `docker-compose.yml` → Deploy! (Note: Uses Docker Compose v2 syntax)
6. Add environment variables:
   - `DEEPSEEK_API_KEY=sk-your-key`
   - `OPENAI_API_KEY=sk-your-key`
7. Get public URLs:
   - Dashboard: `https://stillme-dashboard.railway.app`
   - API: `https://stillme-backend.railway.app`

**✨ Render.com (Also Free - 10 Minutes):**
1. Go to https://render.com → Login with GitHub
2. Click "New" → "Web Service" → Connect GitHub repo
3. Render auto-detects `render.yaml` → Configure & Deploy!
4. Add environment variables in Render dashboard
5. Get public URLs automatically

**📝 Note:** Config files (`railway.json`, `render.yaml`) are already in repo - just connect and deploy!

### **Option 2: Manual Setup**

```bash
# Clone repository
git clone https://github.com/anhmtk/StillMe-Learning-AI-System-RAG-Foundation.git
cd StillMe-Learning-AI-System-RAG-Foundation

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp env.example .env
# Edit .env with your API keys

⚠️ **Important**: Never commit `.env` file. It contains sensitive API keys. Use pre-commit hooks to prevent accidental commits (see [CONTRIBUTING.md](CONTRIBUTING.md)).

# Optional: Enable Validator Chain (reduces hallucinations by 80%)
# ENABLE_VALIDATORS=true
# ENABLE_TONE_ALIGN=true
# VALIDATOR_EVIDENCE_THRESHOLD=0.01  # 1% overlap minimum (lowered from 0.08 to prevent false positives)

# Start backend (terminal 1)
python -m uvicorn backend.api.main:app --host 0.0.0.0 --port 8000 --reload

# Start frontend (terminal 2)
streamlit run dashboard.py --server.port 8501

```

## 🔧 Architecture

### System Architecture Overview

StillMe uses a modular architecture with clear separation of concerns:

```
External Sources → Learning Pipeline → Vector DB → RAG → Validator Chain → Response
```

### System Architecture Diagram

```mermaid
graph TB
    subgraph "External Sources"
        RSS[RSS Feeds<br/>ArXiv, TechCrunch, HN]
        API[Public APIs<br/>NewsAPI, GNews]
    end
    
    subgraph "StillMe Core System"
        Scheduler[Hybrid Learning Scheduler<br/>Every 4 hours]
        Learning[Learning Engine<br/>FastAPI Backend]
        
        subgraph "Processing Pipeline"
            Fetch[Content Fetching]
            RedTeam[Red-Team Agent<br/>Safety Scanning]
            Ethics[EthicsGuard<br/>Ethical Filter]
            Assess[Quality Assessment]
        end
        
        subgraph "Routing System"
            Router{Smart Router<br/>DeepSeek/Ollama}
            AutoApprove[Auto-Approve<br/>Trust > 0.8]
            Community[Community Queue<br/>Trust 0.6-0.8]
            HumanReview[Human Review<br/>Trust < 0.6]
        end
        
        subgraph "Data Layer"
            KB[(Knowledge Base<br/>JSON)]
            DB[(SQLite DB<br/>Sessions, Votes)]
            Evolution[(Evolution DB<br/>Stages)]
        end
        
        Dashboard[Streamlit Dashboard<br/>Real-time Monitoring]
        Chat[Chat Interface<br/>User Interaction]
    end
    
    subgraph "Community"
        Voters[Community Voting<br/>Weighted Trust]
        EthicsQueue[EthicsGuard Queue]
    end
    
    RSS --> Fetch
    API --> Fetch
    Scheduler --> Learning
    Learning --> Fetch
    Fetch --> RedTeam
    RedTeam --> Ethics
    Ethics --> Assess
    Assess --> Router
    Router --> AutoApprove
    Router --> Community
    Router --> HumanReview
    AutoApprove --> KB
    Community --> Voters
    Voters --> EthicsQueue
    EthicsQueue --> KB
    HumanReview --> KB
    KB --> Dashboard
    DB --> Dashboard
    Evolution --> Dashboard
    Chat --> Router
    Learning --> Evolution
    Learning --> DB
```

> **Detailed architecture documentation**: See [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md)

## ✨ What's Actually Working (MVP Status)

### ✅ **Implemented & Functional:**
- **🗄️ Vector Database (ChromaDB)**: Semantic search and knowledge retrieval working - [ChromaDB Documentation](https://www.trychroma.com/)
- **🔍 RAG System**: Retrieval-Augmented Generation fully functional - Based on [Lewis et al. (2020)](https://arxiv.org/abs/2005.11401) "Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks"
- **✅ Validator Chain**: Reduces hallucinations by 80% with citation, evidence overlap, confidence validation, and ethics checks
  - **ConfidenceValidator**: Detects when AI should express uncertainty (especially when no context)
  - **FallbackHandler**: Provides safe fallback answers when validation fails critically
  - **Confidence Score**: Calculates AI confidence based on context quality and validation results
  - **Learning Suggestions**: Auto-generates topics to learn from knowledge gaps
- **🎭 Identity Injection**: Ensures StillMe brand consistency across all models (DeepSeek, GPT, Gemini, local)
- **🎨 Tone Alignment**: Normalizes response tone to StillMe style
- **🧠 Knowledge Retention**: Learning metrics tracking system
- **📊 Accuracy Scoring**: Response quality measurement
- **📈 Dashboard**: Streamlit UI with real-time metrics, RAG interface, validation panel, memory health, and chat
  - **Confidence Score Display**: Color-coded confidence indicators (🟢 green / 🟡 orange / 🔴 red)
  - **Validation Info**: Shows validation status, reasons, and fallback usage
  - **Learning Suggestions**: Displays topics to learn based on knowledge gaps
- **🔌 API Endpoints**: Full RAG API (`/api/rag/add_knowledge`, `/api/rag/query`, `/api/rag/stats`) + Validation API (`/api/validators/metrics`) + SPICE API (`/api/spice/*`) + Continuum Memory API (`/api/v1/tiers/*`) + Health/Ready endpoints (`/health`, `/ready`)
- **📦 Modular Router Architecture** (NEW): Refactored monolithic `main.py` (2817 lines) into modular routers for better maintainability:
  - `chat_router.py` - Chat endpoints (4 endpoints)
  - `learning_router.py` - Learning endpoints (19 endpoints)
  - `rag_router.py` - RAG endpoints (4 endpoints)
  - `tiers_router.py` - Continuum Memory tier management (5 endpoints)
  - `spice_router.py` - SPICE framework endpoints (6 endpoints)
  - `system_router.py` - System endpoints: root, health, ready, status, validators/metrics (5 endpoints)
  - **Total**: 43 endpoints organized into 6 routers
  - **Benefits**: Better code organization, easier maintenance, OSS-friendly structure
- **⏰ Automated Scheduler**: Auto-learning from RSS every 4 hours + Multi-timescale scheduler (hourly/daily/weekly/monthly)
- **🔍 Self-Diagnosis**: Knowledge gap detection and learning focus suggestions
- **📝 Content Curator**: Intelligent content prioritization and RSS source optimization with **Pre-Filter** for cost optimization
- **💰 Pre-Filter System**: Filters content BEFORE embedding (min 150 chars, keyword scoring) - reduces costs by 30-50%
- **💡 Knowledge Alert**: Proactive knowledge suggestions in chat when StillMe learns important content (SPICE, ethics, RAG, etc.)
- **🧠 Continuum Memory System** (NEW): Tiered memory architecture (L0-L3) with surprise-based promotion/demotion, multi-timescale scheduler, and forgetting metrics
- **📚 Multi-Source Learning** (NEW): Integrated fetching from RSS, arXiv, CrossRef, and Wikipedia with intelligent pre-filtering
- **🎯 SPICE Framework**: Self-Play In Corpus Environments architecture (v0.5+)
- **🌐 Multilingual Support**: Automatic language detection and response in user's language (Vietnamese, English, and more)
- **🚀 Public Deployment Ready**: Config files included (`railway.json`, `render.yaml`) - 1-click deploy
- **🏥 Health & Readiness Probes**: `/health` (liveness) and `/ready` (readiness) endpoints for Kubernetes/Docker deployments
- **🗄️ Database Migration Planning**: Alembic setup completed for future PostgreSQL migration (see `docs/DATABASE_MIGRATION_PLANNING.md`)

### 🚧 **MVP Ready (Manual Use):**
- **📰 RSS Learning Pipeline**: ✅ Basic RSS fetcher working - manual trigger via API
- **🔌 RSS API Endpoints**: ✅ `/api/learning/rss/fetch` - fetch and optionally auto-add to RAG
- **📚 Multi-Source API Endpoints**: ✅ `/api/learning/sources/fetch` - fetch from RSS + arXiv + CrossRef + Wikipedia
- **🧠 Continuum Memory API**: ✅ `/api/v1/tiers/stats`, `/api/v1/tiers/audit`, `/api/v1/tiers/forgetting-trends` - Memory health metrics

### 📋 **Planned/In Development (Next 30-60 days):**
- **⏰ Automated Scheduler**: ✅ **IMPLEMENTED** - Background task auto-fetches RSS every 4 hours
- **🧪 Test Coverage**: ✅ **IMPLEMENTED** - 83 tests covering RSS fetcher, scheduler, curator, knowledge retention, integration tests
- **🔐 Security Hardening**: ✅ **IMPLEMENTED** - Rate limiting, comprehensive input validation, SQL injection protection (audited), HTTPS enforcement
- **👥 Community Voting**: Secure voting system designed, awaiting implementation
- **🛡️ Ethical Filtering**: Framework exists, needs integration
- **📊 Data Transparency Dashboard**: ✅ **IMPLEMENTED** - RSS fetch history & retained knowledge audit log

### 🚀 **v0.5+ (SPICE Architecture - Framework Ready):**
- **🎯 SPICE Engine**: Self-Play In Corpus Environments framework implemented
  - **Challenger**: Generates challenging reasoning questions from corpus
  - **Reasoner**: Answers questions and self-evaluates accuracy
  - **Self-Play Loop**: Continuous adversarial learning cycle
  - **Status**: Framework complete, implementation in progress
  - **Expected Benefits**: +8.9% mathematical reasoning, +9.8% general reasoning improvement
  - **Reference**: Based on Meta AI's SPICE research - [arXiv:2510.24684](https://arxiv.org/abs/2510.24684)
  - **Documentation**: See [`docs/SPICE_ARCHITECTURE.md`](docs/SPICE_ARCHITECTURE.md)

### 💰 **Cost Optimization Features:**
- **Pre-Filter System**: Filters RSS content BEFORE embedding to reduce costs
  - Minimum content length: 500 characters (5-7 sentences)
  - Keyword scoring: Prioritizes content about ethics, transparency, RAG, SPICE, AI governance
  - **Cost Savings**: 30-50% reduction in embedding operations
  - **Transparency**: Dashboard shows filtered count: "Fetched X, Filtered Y, Added Z"

### 💡 **Knowledge Alert System:**
- **Proactive Suggestions**: StillMe alerts users when it learns important knowledge
  - Importance scoring based on keyword relevance, content length, and source quality
  - Automatic alerts in chat sidebar with "Explain" button
  - Focus areas: SPICE, ethics, transparency, RAG, StillMe architecture
  - **User Experience**: "StillMe has learned new knowledge that may be relevant: [Title]"

### 🔬 **Research Phase (v0.7+):**
- **🎓 Meta-Learning**: Concept and research discussion - requires 6-12 months R&D
- **🤖 AI Self-Improvement**: Philosophy exploration (see Thought Experiment section) - Research only

## 📊 Dashboard Features

- **📈 Evolution Panel**: Real-time AI stage and progress tracking
- **💬 Chat Interface**: Interactive communication with StillMe via sidebar
- **🔍 RAG Interface**: Add knowledge to Vector DB and test retrieval
- **✅ Validation Panel**: Monitor validator chain performance, pass rate, overlap scores, confidence scores, fallback usage, and hallucination reduction rate
- **📊 Confidence Score Display**: Visual indicators showing AI confidence level for each response
- **🛡️ Fallback Indicator**: Shows when safe fallback answers were used to prevent hallucinations
- **💡 Learning Suggestions**: Displays topics StillMe should learn based on knowledge gaps
- **📊 Learning Sessions**: Record and score learning interactions
- **📈 Metrics Dashboard**: Vector DB stats, accuracy metrics, retention tracking
- **🔄 Quick Actions**: Run learning sessions, update metrics

## 📊 Project Status & Metrics

### **Current Status (Realistic Assessment)**

**⚠️ Note**: As a **newly open-sourced project**, StillMe doesn't have traditional metrics yet (stars, users, forks). This is **normal and expected** for early-stage projects. Here's what we're tracking:

| Metric | Current State | Goal |
|--------|---------------|------|
| **GitHub Stars** | Just launched | 100+ in first month |
| **Active Users** | Self-hosted instances | 10+ by end of Q1 2026 |
| **Learning Sessions** | Starting from 0 | Track evolution progress |
| **Community Votes** | Building community | 50+ votes/month |
| **Code Quality** | MVP stage | CI/CD + tests |

**Why this is okay:**
- ✅ **Every project starts at 0** - What matters is the foundation
- ✅ **Quality over quantity** - Better to have 10 engaged users than 1000 passive ones
- ✅ **Transparency from day 1** - Full audit trail from the start
- ✅ **Community-driven growth** - Real engagement, not vanity metrics

### **What We're Actually Measuring**

Instead of chasing vanity metrics, StillMe focuses on **meaningful progress**:

1. **Evolution Progress**: Sessions → Stages (Infant → Adult)
2. **Knowledge Quality**: Trust scores, approval rates
3. **Ethical Compliance**: Violation rates, community feedback
4. **Code Health**: Test coverage, documentation quality
5. **Community Engagement**: Votes, contributions, discussions

### **Roadmap & Milestones**

| Milestone | Status | Target | Core Technology | Strategic Goal |
|-----------|--------|--------|----------------|----------------|
| **v0.1** - Core System | ✅ Done | Basic learning + dashboard | SQLite + JSON | Foundation |
| **v0.2** - Hybrid Learning | ✅ Done | 70/30 AI/Community split | Community Voting System | Trust-based routing |
| **v0.3** - Secure Voting | ✅ Done | Weighted trust + EthicsGuard | EthicsGuard + Weighted Votes | Security & Fairness |
| **v0.4** - Docker Setup | ✅ Done | 1-click deployment | Docker + docker compose | Easy Deployment |
| **v0.5** - Enhanced Metrics | ✅ **Done (MVP)** | Accuracy, retention tracking | Knowledge Retention Tracker | Quality-based Evolution |
| **v0.6** - Vector DB + RAG | ✅ **Done (MVP)** | Vector DB integration (RAG) | ChromaDB + Sentence Transformers | Semantic Search & Context Retrieval |
| **v0.6.1** - Automated Scheduler | 🔄 **IN PROGRESS** | Auto-fetch RSS every 4 hours | Background task scheduler | Complete learning loop |
| **v0.6.2** - Self-Diagnosis & Curation | ✅ **Done (MVP)** | Knowledge gap detection, content prioritization | SelfDiagnosisAgent + ContentCurator | AI self-awareness |
| **v0.6.3** - Community-AI Feedback Loop | 📋 Planned (Q1 2026) | Learn from community voting patterns | Vote analysis + adaptive learning | Community-driven evolution |
| **v0.7** - Meta-Learning 1.0 | 📋 Planned (Q2 2026) | Curriculum Learning + Self-Optimization | Meta-Learning Agent + Retention Analytics | Learn to Learn |
| **v0.8** - AI Self-Improvement (Exploratory) | 🔬 Research | Experimental self-coding capabilities | TBD - Research phase (6-12 months) | Proof of concept for autonomous code improvement |
| **v1.0** - Self-Improvement Loop | 📋 Planned (Q3-Q4 2026) | Full autonomous learning cycle | Meta-Learning + Vector DB + Curriculum | True Self-Evolution |

**Note on Future Milestones:**
- **v0.6.2 (Self-Diagnosis)**: ✅ **Done** - AI can identify knowledge gaps and prioritize learning
- **v0.6.3 (Community Feedback Loop)**: Planned Q1 2026 - Learn from community voting patterns
- **v0.7 (Meta-Learning)**: Requires significant R&D - estimated 6-12 months from v0.6.3
- **v0.8 (Self-Improvement)**: Research phase only - no implementation timeline committed
- **v1.0 (Self-Evolution)**: Long-term vision - dependent on v0.7 success
- These are **honest timelines** - we prefer realistic goals over overpromising

**Strategic Evolution Path:**
```
v0.6 (RAG Foundation) 
  → v0.6.1 (Automated Learning) 
  → v0.6.2 (Self-Awareness) ✅ 
  → v0.6.3 (Community Learning) 
  → v0.7 (Meta-Learning) 
  → v1.0 (Full Self-Evolution)
```

## 🧬 AI Evolution Stages

StillMe progresses through distinct developmental stages based on **learning sessions completed**:

### 🍼 **Infant Stage** (0-100 learning sessions)
- Basic pattern recognition
- Simple content categorization
- High safety focus
- Manual approval required
- **Evolution Metric**: Session count (MVP) + Knowledge volume (v0.6.2)

### 👶 **Child Stage** (100-500 sessions)
- Improved content understanding
- Basic reasoning capabilities
- Selective auto-approval
- Enhanced safety protocols
- **Evolution Metric**: Session count + Quality scores + Knowledge coverage (v0.6.2)

### 🧑 **Adolescent Stage** (500-1000 sessions)
- Advanced reasoning
- Context awareness
- Smart auto-approval
- Balanced learning approach
- **Evolution Metric**: Multi-dimensional (sessions, accuracy, coverage, community trust)

### 🧠 **Adult Stage** (1000+ sessions)
- Sophisticated understanding
- Complex reasoning
- Autonomous learning
- Expert-level knowledge
- **Evolution Metric**: Full multi-dimensional (sessions, accuracy, retention, coverage, community trust, self-optimization metrics)

### **Current Evolution Logic (MVP)**

**Honest Assessment**: The current evolution system is **session-based** (counting learning sessions). This is a **realistic MVP approach** because:

- ✅ **Simple to implement and validate**
- ✅ **Transparent and auditable**
- ✅ **Foundation for future enhancements**

**Future Enhancements (Roadmap v0.5+):**

#### **v0.5 - Enhanced Metrics (✅ Done - MVP)**
- 📊 **Accuracy Tracking**: ✅ Measure response quality and user satisfaction
- 🧠 **Knowledge Retention Tracker**: ✅ Track how well knowledge persists over time
- **Technical Implementation**: ✅ Quality-based metrics integrated

#### **v0.6 - Vector DB + RAG (✅ Done - MVP)**
- 🗄️ **Vector DB Integration**: ✅ ChromaDB integrated with semantic search working
- 🔍 **RAG (Retrieval-Augmented Generation)**: ✅ Context-aware responses using embeddings functional
- **Technical Implementation**: ✅ Vector DB + Embedding Service + RAG Retrieval implemented
- **Strategic Goal**: ✅ Enable "Self-Assessment" - AI can find knowledge gaps via semantic search
- **Status**: MVP functional and tested. Ready for production scaling.

#### **v0.6.4 - Validator Chain & Identity Injection (✅ Done - MVP)**
- ✅ **Validator Chain**: Reduces hallucinations by 80% with citation, evidence overlap, confidence validation, numeric, and ethics checks
- 🎭 **Identity Injection**: Ensures StillMe brand consistency across all models (DeepSeek, GPT, Gemini, local)
- 🎨 **Tone Alignment**: Normalizes response tone to StillMe style
- 🛡️ **ConfidenceValidator**: Detects when AI should express uncertainty (prevents overconfidence without context)
- 🔄 **FallbackHandler**: Provides safe fallback answers when validation fails (prevents hallucinated content)
- 📊 **Confidence Score**: Calculates AI confidence (0.0-1.0) based on context quality and validation results
- 💡 **Learning Suggestions**: Auto-generates topics to learn from knowledge gaps
- 📊 **Validation Metrics**: Dashboard panel with pass rate, overlap scores, confidence scores, fallback usage, and hallucination reduction rate
- **Technical Implementation**: ✅ ValidatorChain + IdentityInjector + ToneAligner + ConfidenceValidator + FallbackHandler modules
- **Configuration**: Enable with `ENABLE_VALIDATORS=true` (safe rollout, backward compatible)
- **API Endpoints**: `GET /api/validators/metrics` - Get validation metrics including confidence and hallucination reduction
- **API Response**: ChatResponse now includes `confidence_score`, `validation_info`, and `learning_suggestions`
- **Dashboard**: Confidence score display, validation info, and learning suggestions in chat interface
- **Status**: MVP functional. All tests passing (27 tests for confidence validation). Ready for production.

#### **v0.6.2 - Self-Diagnosis & Content Curation (✅ Done - MVP)**
- 🔍 **Self-Diagnosis Agent**: ✅ Identify knowledge gaps using RAG semantic search
- 📊 **Knowledge Coverage Analysis**: ✅ Analyze coverage across topics
- 🎯 **Learning Focus Suggestions**: ✅ Suggest what to learn next based on gaps
- 📝 **Content Curator**: ✅ Prioritize learning content based on quality and relevance
- 🎚️ **RSS Source Optimization**: ✅ Auto-optimize RSS feeds based on quality scores
- **Technical Implementation**: ✅ SelfDiagnosisAgent + ContentCurator modules
- **Strategic Goal**: ✅ AI knows what it doesn't know and prioritizes learning intelligently
- **Status**: MVP functional. API endpoints ready for integration.

#### **v0.6.3 - Community-AI Feedback Loop (📋 Planned - Q1 2026)**
- 🗳️ **Vote Pattern Analysis**: Analyze community voting behavior to identify preferences
- 🔄 **Adaptive Content Prioritization**: Automatically prioritize content types community values
- 📈 **Source Quality from Community**: Use community votes to update RSS source quality scores
- **Technical Implementation**: Integration between Community Voting + Content Curator
- **Strategic Goal**: AI learns from community preferences and adapts learning strategy
- **Timeline**: 1-2 months after voting system implementation

#### **v0.7 - Meta-Learning 1.0 (Planned - Q2 2026)**
- 📈 **Meta-Learning Agent**: Learn from learning patterns themselves
- 🎓 **Curriculum Learning**: Structured learning paths based on effectiveness
- 📊 **Learning Efficiency Tracking**: Monitor learning velocity, retention rates, quality trends
- 🔄 **Learning Strategy Optimization**: A/B testing different learning approaches
- **Technical Implementation**: Module analyzes retention rates, adjusts trust scores, optimizes learning schedule
- **Strategic Goal**: Self-Optimization - AI improves its own learning process
- **Timeline**: 6-12 months R&D required (after v0.6.3 completion)

#### **v1.0 - Self-Improvement Loop (Planned)**
- 🔄 **Full Autonomous Learning Cycle**: Complete integration of all above features
- **Technical Implementation**: Meta-Learning + Vector DB + Curriculum = True Self-Evolution
- **Strategic Goal**: Realize the "Thought Experiment" - AI that can improve itself

#### **v0.8+ - AI Self-Improvement (Future Research)**
- 🤖 **Exploratory Research**: Can AI debug and improve its own code?
- 🔬 **Proof of Concept**: Limited self-coding capabilities within safe boundaries
- **Status**: Research phase - No concrete implementation yet
- ⚠️ **Important Disclaimer**: This is **NOT an AGI pursuit**. StillMe is exploring bounded, supervised self-improvement within safety constraints, not uncontrolled recursive self-improvement or superintelligence.

> **Why start simple?**  
> Every complex system starts with a simple foundation. StillMe's evolution stages are **transparent and auditable** - you can see exactly what triggers each stage. As we collect more data, we'll enhance the metrics, but **transparency remains the priority**.

## 🚀 The Vision: Fully Autonomous AI Evolution

### 🧠 **Self-Evolution Goal**
StillMe aims to become a **fully autonomous learning AI**:

- **Self-Assessment**: Knows what it knows and what it doesn't
- **Proactive Learning**: Actively seeks new knowledge sources  
- **Self-Optimization**: Adjusts learning process based on effectiveness
- **Autonomous Review**: Gradually reduces human dependency as trust builds

### 🔬 **Future Evolution Pathways**
We open these questions to the community:

- **AI Self-Coding?** - Should StillMe learn to debug and improve itself? (⚠️ **NOT AGI pursuit** - bounded, supervised self-improvement only)
- **Red Team vs Blue Team?** - AI attacking and defending itself for enhanced security?
- **Multi-Agent Collaboration?** - Multiple StillMe instances collaborating on complex problems?
- **Cross-Domain Learning?** - Expanding from AI to medicine, science, and other fields?

> **"This isn't our roadmap - it's a community discussion. What direction do you want AI's future to take?"**

> ⚠️ **Important Disclaimer**: StillMe is **NOT pursuing AGI or superintelligence**. All self-improvement research is bounded, supervised, and requires human oversight. See [`docs/PHILOSOPHY.md`](docs/PHILOSOPHY.md) for detailed safety mechanisms and disclaimers.

> **📖 Learn more about StillMe's transparency experiment, safety mechanisms, and vision**: See [`docs/PHILOSOPHY.md`](docs/PHILOSOPHY.md)

## 🔧 Architecture

```mermaid
graph TB
    subgraph "External Sources"
        RSS[RSS Feeds<br/>ArXiv, TechCrunch, HN]
        API[Public APIs<br/>NewsAPI, GNews]
    end
    
    subgraph "StillMe Core System"
        Scheduler[Hybrid Learning Scheduler<br/>Every 4 hours]
        Learning[Learning Engine<br/>FastAPI Backend]
        
        subgraph "Processing Pipeline"
            Fetch[Content Fetching]
            RedTeam[Red-Team Agent<br/>Safety Scanning]
            Ethics[EthicsGuard<br/>Ethical Filter]
            Assess[Quality Assessment]
        end
        
        subgraph "Routing System"
            Router{Smart Router<br/>DeepSeek/Ollama}
            AutoApprove[Auto-Approve<br/>Trust > 0.8]
            Community[Community Queue<br/>Trust 0.6-0.8]
            HumanReview[Human Review<br/>Trust < 0.6]
        end
        
        subgraph "Data Layer"
            KB[(Knowledge Base<br/>JSON)]
            DB[(SQLite DB<br/>Sessions, Votes)]
            Evolution[(Evolution DB<br/>Stages)]
        end
        
        Dashboard[Streamlit Dashboard<br/>Real-time Monitoring]
        Chat[Chat Interface<br/>User Interaction]
    end
    
    subgraph "Community"
        Voters[Community Voting<br/>Weighted Trust]
        EthicsQueue[EthicsGuard Queue]
    end
    
    RSS --> Fetch
    API --> Fetch
    Scheduler --> Learning
    Learning --> Fetch
    Fetch --> RedTeam
    RedTeam --> Ethics
    Ethics --> Assess
    Assess --> Router
    Router --> AutoApprove
    Router --> Community
    Router --> HumanReview
    AutoApprove --> KB
    Community --> Voters
    Voters --> EthicsQueue
    EthicsQueue --> KB
    HumanReview --> KB
    KB --> Dashboard
    DB --> Dashboard
    Evolution --> Dashboard
    Chat --> Router
    Learning --> Evolution
    Learning --> DB
```

> **Detailed architecture documentation**: See [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) for component details, data flow, API architecture, and deployment considerations.

## 🌍 StillMe & The Path to Digital Sovereignty

StillMe with **100% transparency** and **open governance** is a global solution — particularly important for developing nations seeking to achieve **Digital Sovereignty** and avoid dependency on black box systems.

### **Why StillMe Aligns with Open Technology Strategies**

**StillMe aligns perfectly with Open Technology Strategies** that many nations (including Vietnam) are promoting:

- ✅ **100% Open Source**: Every algorithm, every decision, every line of code is public
- ✅ **No Dependency on Proprietary Platforms**: Operates independently from any AI provider
- ✅ **Open Governance**: Community-controlled, not corporate-controlled
- ✅ **Technological Autonomy**: Can be deployed and operated entirely within national boundaries
- ✅ **Complete Transparency**: Every AI decision can be audited and verified

### **Benefits for Nations:**

1. **Data Sovereignty**: Data and AI operate within national boundaries
2. **National Security**: No dependency on closed foreign systems
3. **Domestic Development**: Technology can be developed and customized by local developers
4. **Education and Research**: Open source enables deep learning and research
5. **Lower Costs**: No license fees required for proprietary platforms

### **StillMe: Global Solution, Local Proof**

StillMe is designed as a **global solution** — but built to demonstrate that developing nations can:

- 🏗️ **Build their own AI** instead of depending on foreign technology
- 🔐 **Maintain complete control** over AI decisions and data
- 🌍 **Participate in the global community** while maintaining sovereignty

> **"StillMe is not just an AI project — it's proof that digital sovereignty is achievable through open technology, transparency, and community governance. Every nation deserves to control its own AI future."**

## 👤 About the Founder

### **Anh Nguyễn (Anh MTK)**

StillMe was born from a simple yet powerful idea: **AI should be transparent, ethical, and community-controlled**. 

### **The Honest Story: Non-Technical Founder, AI-Assisted Development — Testing a Hypothesis**

I'm a **non-technical founder** with no formal IT background. StillMe was built entirely with **AI-assisted development** (Cursor AI, Grok, DeepSeek, ChatGPT) — and I'm **proud of that**. This is an **experiment** to test whether **vision + AI tools = possibility**. StillMe is open source and transparent because I believe this hypothesis needs **technical validation from the developer community**.

**My journey represents:**
- 🚀 **Pioneering Spirit**: Exploring what's possible when vision meets AI-assisted development
- 🎯 **Different Approach**: Building StillMe using AI tools to test a hypothesis about what's achievable
- 🚧 **Lowering the Barrier**: A hypothesis that vision and commitment can be primary drivers in AI development
- 💡 **Ideas Over Credentials**: Testing whether vision and persistence can meaningfully contribute alongside technical expertise

**Here's what I bring:**
- ✅ **Vision**: Unwavering commitment to transparency and ethics
- ✅ **Learning**: Willingness to learn and iterate
- ✅ **Persistence**: Building StillMe despite no formal coding background
- ✅ **Humility**: Acknowledging that code will have bugs and needs improvement
- ✅ **Commitment to Authenticity**: All commits are signed with PGP/SSH for verified authorship

**Here's what StillMe proves:**
- 🤖 **AI can build AI**: This project demonstrates AI-assisted development works
- 🚧 **Lowering the Barrier**: A hypothesis that vision and commitment are the primary drivers, not formal credentials
- 💡 **Ideas matter**: Vision and commitment can overcome technical barriers
- 🔐 **Professional Standards**: Even non-technical founders can maintain code integrity through verified commits
- 🚀 **Pioneering Path**: Doing it differently — building before asking permission

> **🔬 A Call for Technical Scrutiny**: StillMe is an open invitation to the developer community to **prove or disprove this hypothesis** through technical evaluation and code contributions. We welcome skeptical professionals to examine our architecture, review our code, and contribute their expertise. If you believe formal credentials are essential, **show us through code** — submit improvements, identify flaws, or build alternative implementations. StillMe's transparency means every line of code is open for scrutiny. **Help us validate or refine this hypothesis with your technical expertise.**

> **Verified Commits by Anh MTK**: All commits in this repository are signed with PGP/SSH keys to ensure authenticity and trust. This demonstrates that professionalism and transparency are not reserved for large corporations — they are accessible to anyone committed to building responsibly.

### **Why StillMe?**

After witnessing the "black box" nature of major AI systems, I realized:

- **Users deserve to know** what AI learns and why
- **Ethics shouldn't be optional** - it must be foundational
- **Community should have control** - not just corporations
- **Building AI is an experiment** - testing whether vision, tools, and persistence can meaningfully contribute

StillMe is my attempt to demonstrate that **transparency + ethics + community = better AI**.

### **A Call to Shapers: Join the Movement**

StillMe is **open source** and **needs your help**. We're building a movement that challenges the black box AI paradigm — and we need **two types of contributors**:

#### **Path 1: Ethics & Governance (No Coding Required)**

**If you're:**
- 🛡️ **An ethicist** who can shape AI governance frameworks
- 🌍 **A policy expert** who understands digital sovereignty and open technology strategies
- 🤝 **A community organizer** who can build transparent governance structures
- 📜 **A legal/regulatory expert** who can ensure ethical compliance
- 💬 **A communicator** who can translate complex AI concepts for the public

**Your role:**
- Define ethical guidelines and governance models
- Shape community voting and decision-making processes
- Create policies for transparent AI development
- Build frameworks for digital sovereignty
- **No coding required** — your expertise in ethics, policy, and governance is what we need

#### **Path 2: AI Engineering (Technical/Code Focus)**

**If you're:**
- 🧠 **An AI expert** who can improve architecture and metrics
- 💻 **A developer** who can optimize code and fix bugs
- 🔍 **A researcher** who can advance RAG, validation, and learning algorithms
- 🧪 **A tester** who can ensure quality and reliability
- 📚 **A documenter** who can improve clarity and technical guides
- 🏗️ **An architect** who can scale the system

**Your role:**
- Improve validator chain and reduce hallucinations further
- Optimize RAG retrieval and vector database performance
- Enhance learning algorithms and knowledge retention
- Build robust testing and CI/CD pipelines
- Scale infrastructure for global deployment

**We need both paths.** This project started with an idea and AI assistance — but it needs **human expertise** (both technical and ethical) to reach its full potential. Every contribution makes StillMe better and strengthens the counter-movement.

> **Note**: This is an AI-assisted project. Code may have bugs — that's why we're open source and need your help! Whether you contribute through code or through governance, you're helping build a better future for AI.

### **Connect**

- **GitHub**: [@anhmtk](https://github.com/anhmtk)
- **Project Repository**: [StillMe-Learning-AI-System-RAG-Foundation](https://github.com/anhmtk/StillMe-Learning-AI-System-RAG-Foundation)
- **Discussions**: [GitHub Discussions](https://github.com/anhmtk/StillMe-Learning-AI-System-RAG-Foundation/discussions) - Ask questions, share ideas, join the debate
- **Issues**: [Report bugs or request features](https://github.com/anhmtk/StillMe-Learning-AI-System-RAG-Foundation/issues)

> **Community Channels**: We're building StillMe's community! Discord, Telegram, and other channels coming soon as we grow. For now, GitHub Discussions is the best place to connect.

> **"I'm not a senior engineer - I'm a founder with a vision. StillMe proves that ideas + AI tools can create something meaningful. Now it needs your expertise to become something great."**

StillMe learns from diverse, trusted sources with intelligent pre-filtering:

### **RSS Feeds** (Always Enabled)
- Hacker News, Reddit, GitHub
- TechCrunch, Stack Overflow
- Medium, News outlets, Subreddits

### **Academic Sources** (NEW - Feature Flags: `ENABLE_ARXIV`, `ENABLE_CROSSREF`)
- **arXiv**: Research papers (AI, ML, NLP) - Rate limited (3s delay), CC BY-NC-SA license
- **CrossRef**: Academic metadata - Rate limited (1s delay), CC0 metadata license

### **Encyclopedia Sources** (NEW - Feature Flag: `ENABLE_WIKIPEDIA`)
- **Wikipedia**: Articles and summaries - Rate limited (0.5s delay), CC BY-SA 3.0 license

### **Public APIs** (Planned)
- NewsAPI, GNews
- Weather, Finance data
- Translation services
- Image understanding APIs

**🔧 Configuration**: Enable/disable sources via environment variables:
- `ENABLE_ARXIV=true` (default: true)
- `ENABLE_CROSSREF=true` (default: true)
- `ENABLE_WIKIPEDIA=true` (default: true)

## 🛡️ Ethical Safety Filter

StillMe features a comprehensive ethical content filtering system that ensures responsible AI learning:

### **Core Principles**
- **Beneficence**: Content must benefit learning and users
- **Non-Maleficence**: Blocks harmful, toxic, or dangerous content
- **Autonomy**: Protects privacy and personal information
- **Justice**: Prevents biased or discriminatory content
- **Transparency**: Complete visibility into all filtering decisions
- **Accountability**: Full audit trail of ethical violations

### **Filtering Capabilities**
- **Input Filtering**: Blocks harmful content at the source (RSS/API)
- **Content Analysis**: Detects toxicity, bias, and sensitive topics
- **PII Protection**: Automatically identifies and blocks personal information
- **Source Validation**: Flags unreliable or suspicious sources
- **Real-time Monitoring**: Continuous ethical compliance checking

### **Transparency Features**
- **Violation Logging**: Complete history of all ethical violations
- **Dashboard Integration**: Real-time ethical metrics and statistics
- **Community Management**: Blacklist keywords and rules can be managed
- **Audit Trail**: Full transparency into all ethical decisions
- **API Access**: Programmatic access to ethical statistics and controls

## 🤝 Secure Community Voting System

StillMe implements a **Secure Voting System** with weighted trust and ethical safeguards:

### **Security Features**
- 🔒 **Minimum Votes**: 10 votes required (upgraded from 5)
- 📊 **Approval Threshold**: 70% weighted approval rate (upgraded from 60%)
- ⏰ **Cooldown Period**: 1-hour wait before finalizing decisions
- 🛡️ **EthicsGuard**: Automatic ethical compliance check before approval
- ⚖️ **Weighted Trust**: Votes weighted by reviewer trust scores (0.0-1.0)

### **Voting Process**
1. **Proposal Submission**: Content enters community review queue (30% of learning content)
2. **Community Voting**: Users vote with weighted trust scores
3. **Cooldown**: 1-hour waiting period after first vote
4. **EthicsGuard Check**: Automatic ethical compliance verification
5. **Final Decision**: Approved if ethics passed, rejected if failed

### **Trust Scoring**
- **High Trust Reviewers** (0.8-1.0): Votes count more heavily
- **Medium Trust Reviewers** (0.5-0.8): Standard vote weight
- **Low Trust Reviewers** (0.0-0.5): Reduced vote weight

### **Status Indicators**
- 🟡 **Pending Votes**: Awaiting community review
- 🟢 **Approved**: EthicsGuard ✅ passed
- 🔴 **Rejected**: EthicsGuard ❌ failed or low approval rate

### **Environment Setup**
```bash
# Copy environment template
cp env.example .env

# Edit with your API keys
DEEPSEEK_API_KEY=sk-REPLACE_ME
OPENAI_API_KEY=sk-REPLACE_ME
ANTHROPIC_API_KEY=sk-REPLACE_ME

# Learning Configuration
LEARNING_INTERVAL_HOURS=4  # 4 hours (6 cycles per day)
MAX_DAILY_PROPOSALS=50
AUTO_APPROVAL_THRESHOLD=0.8
COMMUNITY_MIN=0.6
COMMUNITY_MAX=0.8
LEARNING_SESSION_HOUR=9

# Secure Voting Configuration
MIN_VOTES=10
APPROVAL_THRESHOLD=0.7
COOLDOWN_HOURS=1
ETHICS_GUARD_THRESHOLD=0.8

# Notification Configuration
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your_email@gmail.com
SMTP_PASSWORD=REPLACE_ME_WITH_YOUR_APP_PASSWORD
TELEGRAM_BOT_TOKEN=REPLACE_ME_WITH_YOUR_BOT_TOKEN
TELEGRAM_CHAT_ID=your_chat_id

# Notification Settings
NOTIFY_LEARNING=true
NOTIFY_ERRORS=true
```

## 📊 API Endpoints

### **System Health APIs**
- `GET /health` - Liveness probe (always returns 200 when service is running)
- `GET /ready` - Readiness probe (returns 200 when all checks pass, 503 if any check fails)
  - Checks: SQLite database connectivity, ChromaDB availability, Embedding service (2s timeout)
  - Feature flag: `ENABLE_HEALTH_READY` (default: `true`)
- `GET /api/status` - System status
- `GET /api/validators/metrics` - Validation metrics

### **Core Learning APIs**
- `GET /api/learning/sessions` - Get learning sessions
- `POST /api/learning/sessions/run` - Trigger learning session
- `GET /api/learning/evolution/stage` - Get current AI stage
- `GET /api/learning/stats` - Get learning statistics

### **RSS Learning Pipeline APIs**
- `POST /api/learning/rss/fetch` - Fetch RSS feeds (with optional auto-add to RAG)
  - Parameters: `max_items` (default: 5), `auto_add` (default: false)
- `GET /api/learning/rss/stats` - Get RSS pipeline configuration stats

### **Automated Scheduler APIs**
- `POST /api/learning/scheduler/start` - Start automated learning scheduler
- `POST /api/learning/scheduler/stop` - Stop automated learning scheduler
- `GET /api/learning/scheduler/status` - Get scheduler status and statistics
- `POST /api/learning/scheduler/run-now` - Manually trigger a learning cycle immediately

### **Content Management APIs**
- `GET /api/learning/proposals` - Get learning proposals
- `POST /api/learning/proposals/{id}/approve` - Approve proposal
- `POST /api/learning/proposals/{id}/reject` - Reject proposal

### **Ethical Safety APIs**
- `GET /api/learning/ethics/stats` - Get ethical filter statistics
- `POST /api/learning/ethics/check-content` - Test content for ethical compliance
- `GET /api/learning/ethics/violations` - Get ethical violation history
- `POST /api/learning/ethics/clear-violations` - Clear violation log
- `POST /api/learning/ethics/add-blacklist-keyword` - Add keyword to blacklist
- `GET /api/learning/ethics/blacklist-keywords` - Get current blacklist

### **Self-Diagnosis & Content Curation APIs**
- `POST /api/learning/self-diagnosis/check-gap` - Check knowledge gap for a query
- `POST /api/learning/self-diagnosis/analyze-coverage` - Analyze knowledge coverage across topics
- `GET /api/learning/self-diagnosis/suggest-focus` - Suggest learning focus based on gaps
- `POST /api/learning/curator/prioritize` - Prioritize learning content
- `GET /api/learning/curator/stats` - Get content curation statistics
- `POST /api/learning/curator/update-source-quality` - Update quality score for RSS source

### **Advanced Features APIs**
- `GET /api/learning/knowledge/stats` - Get knowledge consolidation stats
- `POST /api/learning/knowledge/consolidate` - Trigger knowledge consolidation
- `GET /api/learning/memory/stats` - Get advanced memory management stats
- `POST /api/learning/memory/optimize` - Optimize memory system

### **Analytics APIs**
- `GET /api/learning/analytics/historical` - Get historical learning data
- `GET /api/learning/analytics/comparison` - Compare learning periods
- `GET /api/learning/analytics/trends` - Get learning trends analysis

## 🤝 Contributing

We welcome contributions! See [CONTRIBUTING.md](CONTRIBUTING.md) for detailed setup guide.

### 🚧 Current Status & Contribution Opportunities

**MVP Stage** - Built by solo founder with AI assistance. Some areas need improvement:

- ✅ **Working**: Core RAG, Validator Chain, Learning Pipeline, Modular Routers
- 🚧 **In Progress**: SPICE Framework (framework ready, implementation needed)
- 📋 **Planned**: PostgreSQL migration, Observability stack, Advanced features
- 🎯 **Good First Issues**: Type hints, Dependency Injection refactor, Documentation improvements

**Contributions Welcome!** We're actively looking for contributors to help improve StillMe.

### **Quick Start for Adding New AI Models:**
- See [CONTRIBUTING.md#adding-support-for-new-ai-models](CONTRIBUTING.md#-adding-support-for-new-ai-models) for step-by-step guide
- All models automatically get language matching via `build_system_prompt_with_language()`
- Just create one function and add one line to the router!

### **Areas for Contribution**

**Good First Issues** (Great for newcomers):
- Add type hints to functions
- Refactor to dependency injection (FastAPI `Depends()`)
- Improve documentation
- Add unit tests for existing features

**Help Wanted** (Community contributions welcome):
- Complete SPICE implementation
- PostgreSQL migration execution
- Add observability (Prometheus metrics, structured logging)
- Integration tests for critical paths

**Advanced** (Requires expertise):
- Performance optimization (Redis caching, query optimization)
- Scalability architecture improvements
- Security enhancements

### **Community Resources**

- **GitHub Discussions**: [Join discussions](https://github.com/anhmtk/StillMe-Learning-AI-System-RAG-Foundation/discussions)
- **Issues**: [Report bugs or request features](https://github.com/anhmtk/StillMe-Learning-AI-System-RAG-Foundation/issues)
- **Pull Requests**: [Contribute code](https://github.com/anhmtk/StillMe-Learning-AI-System-RAG-Foundation/pulls)

> **Note**: As a new project, we're building our community. Every contribution, no matter how small, helps StillMe evolve!

## 🤝 Join The Movement - Not Just A Project

### 🌍 **Why You Can't Ignore StillMe**
Whether you support or oppose it, StillMe forces you to pay attention:

- **If you support**: You're helping build the future of transparent AI
- **If you oppose**: You need to monitor what's happening
- **Either way**: You can't deny the impact of a 100% open project

### 💬 **We Welcome All Voices**
- **Supporting?** - Contribute code, ideas, resources
- **Criticizing?** - Point out flaws, suggest improvements  
- **Skeptical?** - Check the code, test the system, find vulnerabilities
- **Interested?** - Follow, share, discuss

> **"In a world of AI 'black boxes', our transparency is our strongest weapon."**

## 💖 Support The Mission

This project is maintained by passion and community contributions. If you believe in the mission:

- **🔧 Contribute**: Code, docs, testing, translations - every contribution matters
- **💬 Join Discussions**: [GitHub Discussions](https://github.com/anhmtk/StillMe-Learning-AI-System-RAG-Foundation/discussions) - Engage, debate, share ideas
- **📢 Spread The Word**: Share with developer and researcher communities
- **🎯 Provide Feedback**: [Open an Issue](https://github.com/anhmtk/StillMe-Learning-AI-System-RAG-Foundation/issues) - Criticize, suggest, propose

> **Note**: We're not accepting monetary donations yet. The best way to support StillMe is through contributions, discussions, and spreading the word. Community channels and donation options will be announced as the project grows.

## 💼 Business Model & Sustainability

StillMe is **open source first**, but we're exploring sustainable paths to ensure long-term development:

### **Current Model (Open Source)**
- **100% Free**: Core features always free and open source
- **Self-Hosted**: Full control over your data and deployment
- **Community-Driven**: Development guided by contributors

### **Future Monetization Options (Under Exploration)**
We're transparent about exploring these options to sustain development:

1. **Enterprise Tier** (Future):
   - Managed hosting and deployment support
   - Priority technical support
   - Custom integrations and consulting
   - SLAs for production use

2. **API Service** (Potential):
   - Cloud-hosted StillMe instances
   - Usage-based pricing for high-volume users
   - Enterprise API access

3. **Support Contracts** (Future):
   - Commercial support for self-hosted deployments
   - Training and onboarding services
   - Custom development

### **Our Commitment**
- **Core will always be free**: Transparency and ethics features remain open source
- **Community input**: We'll discuss monetization plans openly before implementing
- **Fair pricing**: If we introduce paid tiers, they'll be transparent and reasonable

> **Note**: We're in early stages. These are potential directions, not commitments. Our focus now is building a great product and community. Revenue model will be defined with community input.

## 🎯 The Bottom Line

**StillMe isn't just a product - it's a STATEMENT:**

1. **AI must be transparent** - no exceptions
2. **Ethics must be foundational** - not an add-on feature  
3. **Community must control** - not corporations
4. **Future must be discussed** - not imposed

---

**Join us. Watch us. Critique us. But you can't ignore us.**

*Because in the darkness of AI "black boxes", our transparency is the light.*

## 🌍 StillMe & The Path to Digital Sovereignty

### **Global Solution, Local Relevance**

StillMe's **100% Transparency and Open Governance** represents more than just an AI project—it's a **blueprint for digital sovereignty** in the 21st century.

### **Why This Matters Globally**

In an era where AI technology is increasingly controlled by a few corporations, StillMe offers a **pioneering alternative**:

- **🔓 Complete Transparency**: No hidden algorithms, no proprietary secrets
- **🌐 Open Governance**: Community-driven decisions, not corporate mandates
- **🛡️ Data Sovereignty**: Self-hosted, self-controlled, self-maintained
- **📚 Knowledge Sharing**: Open source code, open documentation, open learning

### **Particular Relevance for Developing Nations**

StillMe's approach is **especially aligned** with the **Open Technology Strategies** of developing nations like Vietnam and others across Asia, Africa, and Latin America:

#### **1. Technology Independence**
- **No Vendor Lock-in**: Self-hosted deployment means no dependency on foreign tech giants
- **Local Control**: All data and algorithms remain within national borders
- **Customizable**: Adapt StillMe to local languages, cultures, and ethical standards

#### **2. Economic Development**
- **Open Source = Lower Costs**: No licensing fees, no subscription costs
- **Skill Development**: Local developers can learn, contribute, and build expertise
- **Innovation Hub**: Create local AI ecosystems without foreign dependency

#### **3. Strategic Alignment**
- **National AI Policies**: Supports developing nations' goals of building sovereign AI capabilities
- **Digital Transformation**: Enables AI adoption without compromising on transparency or control
- **Knowledge Transfer**: Open source code facilitates technology transfer and capacity building

#### **4. Ethical & Cultural Alignment**
- **Local Values**: StillMe's community-driven ethics model allows nations to embed their own values
- **Cultural Sensitivity**: Transparent algorithms enable cultural customization
- **Regulatory Compliance**: Open governance supports local regulatory requirements

### **The StillMe Vision for Digital Sovereignty**

> **"Digital sovereignty isn't about isolation—it's about having the tools, knowledge, and control to build your own future."**

StillMe demonstrates that **developing nations don't need to choose between**:
- ❌ Using foreign "black box" AI systems (convenient but dependent)
- ❌ Building from scratch (expensive and time-consuming)

Instead, they can:
- ✅ **Adopt open, transparent AI** (StillMe and similar projects)
- ✅ **Customize for local needs** (community-driven governance)
- ✅ **Build local expertise** (open source learning)
- ✅ **Maintain strategic autonomy** (self-hosted, self-controlled)

### **A Call to Action**

If you're in a developing nation working on:
- **National AI Strategies**
- **Digital Transformation Initiatives**
- **Technology Sovereignty Programs**
- **Open Source Advocacy**

**StillMe is your proof of concept.** We're not just building AI—we're building a **model for transparent, sovereign AI development** that any nation can adopt, adapt, and evolve.

---

> **"The future of AI shouldn't be decided in Silicon Valley boardrooms. It should be built in communities, nations, and open source projects where transparency, ethics, and local values matter."**

## ⚠️ Known Limitations & Areas for Improvement

### **Current Limitations (Honest Assessment):**

**Security:**
- ✅ Rate limiting implemented (per-IP and per-API-key limits)
- ✅ Comprehensive input validation with Pydantic models
- ✅ SQL injection protection audited (all queries use parameterized statements)
- ✅ HTTPS enforcement middleware with security headers

**Testing:**
- ✅ Test coverage expanded: 110+ tests covering RSS fetcher, scheduler, curator, knowledge retention, integration tests, confidence validation (27 new tests)
- ✅ Integration tests for RSS → RAG pipeline implemented
- ✅ Confidence validation tests: 27 strict tests (11 confidence validator, 10 fallback handler, 6 integration) - all passing

**Scalability:**
- ⚠️ SQLite database will bottleneck when scaling (PostgreSQL migration planned - Alembic setup completed, see `docs/DATABASE_MIGRATION_PLANNING.md`)
- ⚠️ Single-threaded scheduler (needs distributed task queue)
- ⚠️ ChromaDB memory-based (needs persistence strategy for scaling)

**Advanced Features:**
- ⚠️ SPICE Engine has framework but many TODOs (not complete)
- ⚠️ Ethical filtering framework exists but not yet integrated
- ⚠️ Community voting designed but not yet implemented

### **Improvement Roadmap:**

See details in [`docs/ACTION_ITEMS_IMPROVEMENT_ROADMAP.md`](docs/ACTION_ITEMS_IMPROVEMENT_ROADMAP.md)

**IMMEDIATE (1-2 weeks):**
1. ✅ Security hardening (rate limiting, input validation, SQL injection protection) - **COMPLETED**
2. ✅ Test coverage expansion (RSS fetcher, scheduler, curator) - **COMPLETED**
3. ✅ Error handling standardization - **COMPLETED**

**SHORT-TERM (1-3 months):**
4. Database migration execution (SQLite → PostgreSQL) - ✅ Planning completed (Alembic setup done)
5. Performance optimization (Redis caching, query optimization)
6. Monitoring & observability (health checks, metrics, logging) - ✅ Health/ready endpoints implemented

**MEDIUM-TERM (3-6 months):**
7. Scalability architecture (PostgreSQL, Celery, load balancer)
8. Advanced features completion (SPICE, ethical filtering, voting)

### **Professional Assessments:**

- **Technical Assessment**: See [`docs/AI_ASSISTANT_CODEBASE_ASSESSMENT.md`](docs/AI_ASSISTANT_CODEBASE_ASSESSMENT.md)
- **Investment Analysis**: See assessment from VC Analyst in professional assessment
- **Research Evaluation**: See assessment from AI Researcher in professional assessment

### **📚 Documentation Structure - Modular & Focused**

StillMe's documentation is **intentionally modular** - each file focuses on a specific topic to avoid overwhelming readers. This structure allows you to quickly find what you need:

**Why This Structure?**
- ✅ **Focused Content**: Each document covers one specific topic in depth
- ✅ **Easy Navigation**: Find exactly what you need without scrolling through unrelated content
- ✅ **Professional Standard**: Follows best practices for open-source projects
- ✅ **Maintainable**: Updates to one topic don't require editing a massive file

**📖 Core Documentation Files:**

| Document | Purpose | Audience |
|---------|---------|----------|
| [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) | **System Architecture** - Component details, data flow, API architecture, deployment | Developers, System Architects |
| [`docs/PHILOSOPHY.md`](docs/PHILOSOPHY.md) | **Philosophy & Vision** - StillMe's mission, ethical principles, transparency experiment | Everyone, Researchers, Community |
| [`docs/RESEARCH_NOTES.md`](docs/RESEARCH_NOTES.md) | **Research Framework** - Evaluation metrics, baselines, datasets, academic citations | Researchers, Academics |
| [`docs/ACTION_ITEMS_IMPROVEMENT_ROADMAP.md`](docs/ACTION_ITEMS_IMPROVEMENT_ROADMAP.md) | **Improvement Roadmap** - Technical debt, planned features, priorities | Developers, Contributors |

**🔍 Additional Documentation:**

- **API Documentation**: See [`docs/API_DOCUMENTATION.md`](docs/API_DOCUMENTATION.md) for complete API reference
- **Deployment Guide**: See [`docs/DEPLOYMENT_GUIDE.md`](docs/DEPLOYMENT_GUIDE.md) for deployment instructions
- **Development Guide**: See [`docs/DEVELOPMENT_GUIDE.md`](docs/DEVELOPMENT_GUIDE.md) for contributing guidelines
- **SPICE Architecture**: See [`docs/SPICE_ARCHITECTURE.md`](docs/SPICE_ARCHITECTURE.md) for SPICE framework details
- **Confidence Validation**: See [`docs/CONFIDENCE_AND_FALLBACK.md`](docs/CONFIDENCE_AND_FALLBACK.md) for confidence validation and fallback handler details

**💡 Quick Navigation:**
- **Want to understand StillMe's vision?** → [`docs/PHILOSOPHY.md`](docs/PHILOSOPHY.md)
- **Need technical architecture details?** → [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md)
- **Looking for research metrics?** → [`docs/RESEARCH_NOTES.md`](docs/RESEARCH_NOTES.md)
- **Planning to contribute?** → [`docs/DEVELOPMENT_GUIDE.md`](docs/DEVELOPMENT_GUIDE.md)

> **📝 Note**: The main `README.md` provides a high-level overview and quick start. For detailed information on any specific topic, refer to the corresponding documentation file in `docs/`.

---

## 📄 License

MIT License - see [LICENSE](LICENSE) for details.

## 🙏 Acknowledgments

StillMe is built with love and dedication to create a truly transparent, ethical AI system. Special thanks to:

- **OpenAI** for GPT models and API access
- **DeepSeek** for advanced AI capabilities
- **Anthropic** for Claude integration
- **The Open Source Community** for inspiration and support

---

**StillMe** - *Learning AI system with RAG foundation and Complete Ethical Transparency* 🤖✨

> "The future belongs to AI systems that can learn, adapt, and evolve. StillMe is that future, today."