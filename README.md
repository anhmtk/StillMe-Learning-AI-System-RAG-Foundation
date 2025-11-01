# 🧠 StillMe - Self-Evolving AI System

<div align="center">
  <img src="assets/logo.png" alt="StillMe Logo" width="200" height="200">
</div>

> **A transparent AI learning system building the foundation for self-evolving AI. Currently in MVP stage with Vector DB + RAG capabilities working.**

[![Python](https://img.shields.io/badge/Python-3.12+-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)](https://fastapi.tiangolo.com)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.28+-red.svg)](https://streamlit.io)
[![Ethical AI](https://img.shields.io/badge/Ethical%20AI-Transparent-green.svg)](https://github.com/anhmtk/stillme_ai_ipc)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## 🌟 What is StillMe?

StillMe is a **Transparent AI Learning System** building toward true self-evolution. 

**Current MVP Status:** Foundation components are implemented and working:
- ✅ **Vector Database (ChromaDB)**: Semantic search and knowledge retrieval functional
- ✅ **RAG System**: Retrieval-Augmented Generation for context-aware responses  
- ✅ **Knowledge Retention**: Learning metrics tracking system
- ✅ **Accuracy Scoring**: Response quality measurement
- ✅ **Dashboard**: Interactive UI with RAG interface and learning metrics

**Vision:** Evolve through developmental stages (Infant → Child → Adolescent → Adult) with community governance, automated learning pipelines, and complete transparency.

### 🎯 Core Concept

- **🧬 Evolutionary Learning**: AI progresses through stages (Infant → Child → Adolescent → Adult)
- **📚 Multi-Source Learning**: RSS feeds + Public APIs integration
- **🌐 Real-time Data**: Live data from multiple trusted sources with transparency
- **🛡️ Ethical Filtering**: Comprehensive ethical content filtering with complete transparency
- **📊 Transparent Dashboard**: Complete visibility into all learning sources and data
- **💬 Interactive Chat**: Communicate with your evolving AI assistant

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
git clone https://github.com/anhmtk/StillMe---Self-Evolving-AI-System.git
cd StillMe---Self-Evolving-AI-System

# One-click setup (Linux/Mac)
chmod +x quick-start.sh
./quick-start.sh

# Or Windows PowerShell
.\quick-start.ps1

# Or manually with Docker Compose
docker-compose up -d
```

**Access after startup:**
- 📊 **Dashboard**: http://localhost:8501
- 🔌 **API**: http://localhost:8000
- 📚 **API Docs**: http://localhost:8000/docs

### **Option 2: Manual Setup**

```bash
# Clone repository
git clone https://github.com/anhmtk/StillMe---Self-Evolving-AI-System.git
cd StillMe---Self-Evolving-AI-System

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp env.example .env
# Edit .env with your API keys

# Start backend (terminal 1)
python -m uvicorn backend.api.main:app --host 0.0.0.0 --port 8000 --reload

# Start frontend (terminal 2)
streamlit run dashboard.py --server.port 8501

# Note: RSS scheduler and automated learning pipeline are planned for future releases
```

## ✨ What's Actually Working (MVP Status)

### ✅ **Implemented & Functional:**
- **🗄️ Vector Database (ChromaDB)**: Semantic search and knowledge retrieval working
- **🔍 RAG System**: Retrieval-Augmented Generation fully functional
- **🧠 Knowledge Retention**: Learning metrics tracking system
- **📊 Accuracy Scoring**: Response quality measurement
- **📈 Dashboard**: Streamlit UI with real-time metrics, RAG interface, and chat
- **🔌 API Endpoints**: Full RAG API (`/api/rag/add_knowledge`, `/api/rag/query`, `/api/rag/stats`)

### 🚧 **MVP Ready (Manual Use):**
- **📰 RSS Learning Pipeline**: ✅ Basic RSS fetcher working - manual trigger via API
- **🔌 RSS API Endpoints**: ✅ `/api/learning/rss/fetch` - fetch and optionally auto-add to RAG

### 📋 **Planned/In Development:**
- **⏰ Automated Scheduler**: Design ready, needs implementation (cron/background task)
- **👥 Community Voting**: Secure voting system designed, awaiting implementation
- **🛡️ Ethical Filtering**: Framework exists, needs integration

### 🔬 **Research Phase:**
- **🎓 Meta-Learning**: Concept and research discussion
- **🤖 AI Self-Improvement**: Philosophy exploration (see Thought Experiment section)

## 📊 Dashboard Features

- **📈 Evolution Panel**: Real-time AI stage and progress tracking
- **💬 Chat Interface**: Interactive communication with StillMe via sidebar
- **🔍 RAG Interface**: Add knowledge to Vector DB and test retrieval
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
| **v0.4** - Docker Setup | ✅ Done | 1-click deployment | Docker + docker-compose | Easy Deployment |
| **v0.5** - Enhanced Metrics | ✅ **Done (MVP)** | Accuracy, retention tracking | Knowledge Retention Tracker | Quality-based Evolution |
| **v0.6** - Vector DB + RAG | ✅ **Done (MVP)** | Vector DB integration (RAG) | ChromaDB + Sentence Transformers | Semantic Search & Context Retrieval |
| **v0.7** - Meta-Learning 1.0 | 📋 Planned | Curriculum Learning + Self-Optimization | Meta-Learning Agent + Retention Analytics | Learn to Learn |
| **v0.8** - AI Self-Improvement (Exploratory) | 🔬 Research | Experimental self-coding capabilities | TBD - Research phase | Proof of concept for autonomous code improvement |
| **v1.0** - Self-Improvement Loop | 📋 Planned | Full autonomous learning cycle | Meta-Learning + Vector DB + Curriculum | True Self-Evolution |

## 🧬 AI Evolution Stages

StillMe progresses through distinct developmental stages based on **learning sessions completed**:

### 🍼 **Infant Stage** (0-100 learning sessions)
- Basic pattern recognition
- Simple content categorization
- High safety focus
- Manual approval required
- **Evolution Metric**: Session count only (MVP approach)

### 👶 **Child Stage** (100-500 sessions)
- Improved content understanding
- Basic reasoning capabilities
- Selective auto-approval
- Enhanced safety protocols
- **Evolution Metric**: Session count + basic quality scores

### 🧑 **Adolescent Stage** (500-1000 sessions)
- Advanced reasoning
- Context awareness
- Smart auto-approval
- Balanced learning approach
- **Evolution Metric**: Session count + approval rates + trust scores

### 🧠 **Adult Stage** (1000+ sessions)
- Sophisticated understanding
- Complex reasoning
- Autonomous learning
- Expert-level knowledge
- **Evolution Metric**: Multi-dimensional (sessions, accuracy, retention, community trust)

### **Current Evolution Logic (MVP)**

**Honest Assessment**: The current evolution system is **session-based** (counting learning sessions). This is a **realistic MVP approach** because:

- ✅ **Simple to implement and validate**
- ✅ **Transparent and auditable**
- ✅ **Foundation for future enhancements**

**Future Enhancements (Roadmap v0.5+):**

#### **v0.5 - Enhanced Metrics (In Progress)**
- 📊 **Accuracy Tracking**: Measure response quality and user satisfaction
- 🧠 **Knowledge Retention Tracker**: Track how well knowledge persists over time
- **Technical Implementation**: Session-based metrics → Quality-based metrics

#### **v0.6 - Vector DB + RAG (✅ Done - MVP)**
- 🗄️ **Vector DB Integration**: ✅ ChromaDB integrated with semantic search working
- 🔍 **RAG (Retrieval-Augmented Generation)**: ✅ Context-aware responses using embeddings functional
- **Technical Implementation**: ✅ Vector DB + Embedding Service + RAG Retrieval implemented
- **Strategic Goal**: ✅ Enable "Self-Assessment" - AI can find knowledge gaps via semantic search
- **Status**: MVP functional and tested. Ready for production scaling.

#### **v0.7 - Meta-Learning 1.0 (Planned)**
- 📈 **Meta-Learning Agent**: Learn from learning patterns themselves
- 🎓 **Curriculum Learning**: Structured learning paths based on effectiveness
- **Technical Implementation**: Module analyzes retention rates, adjusts trust scores, suggests sources
- **Strategic Goal**: Self-Optimization - AI improves its own learning process

#### **v1.0 - Self-Improvement Loop (Planned)**
- 🔄 **Full Autonomous Learning Cycle**: Complete integration of all above features
- **Technical Implementation**: Meta-Learning + Vector DB + Curriculum = True Self-Evolution
- **Strategic Goal**: Realize the "Thought Experiment" - AI that can improve itself

#### **v0.8+ - AI Self-Improvement (Future Research)**
- 🤖 **Exploratory Research**: Can AI debug and improve its own code?
- 🔬 **Proof of Concept**: Limited self-coding capabilities within safe boundaries
- **Status**: Research phase - No concrete implementation yet
- **Connection**: This relates to the "Thought Experiment" section - we're exploring the possibility, not promising it

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

- **AI Self-Coding?** - Should StillMe learn to debug and improve itself?
- **Red Team vs Blue Team?** - AI attacking and defending itself for enhanced security?
- **Multi-Agent Collaboration?** - Multiple StillMe instances collaborating on complex problems?
- **Cross-Domain Learning?** - Expanding from AI to medicine, science, and other fields?

> **"This isn't our roadmap - it's a community discussion. What direction do you want AI's future to take?"**

### 🤔 **The Thought Experiment: What Happens When We Step Back?**

Here's a question that will divide opinions and spark debate — and that's exactly the point:

**What if, one day, we gradually reduce human intervention in StillMe's learning process?** What if we give it the ability to not just learn content, but to **learn from its own code**, **identify bugs**, and **improve itself** — within reasonable boundaries that match our current capabilities?

**Three possible outcomes:**

1. **🧠 Brilliant Evolution**: StillMe becomes smarter, more efficient, and self-optimizing — a true self-evolving AI that improves faster than we can guide it.

2. **🗑️ Chaotic Mess**: Without human oversight, StillMe accumulates bugs, contradictions, and broken logic — creating a chaotic system that's worse than we started with.

3. **❓ The Unknown**: Something emerges that we don't fully understand — neither perfectly smart nor completely broken, but operating in ways we can't predict or control.

**This is not a feature we're building.** This is a **thought experiment** — a philosophical question that forces us to confront the future of AI autonomy.

### 🔬 **Run the Experiment Yourself**

> **Try it now**:  
> → [Quick Start](#-quick-start) → Watch StillMe learn → **Ask yourself: "What if it started fixing itself?"**

**Where do you stand?** (Check your position below - interactive on GitHub!)

- [ ] **I support self-improvement** — Fascinated by the possibility of true AI autonomy
- [ ] **I oppose (safety first)** — Concerned about control and unintended consequences  
- [ ] **I want to see what happens** — Curious about the unknown, regardless of outcome

**Share your thoughts**: [GitHub Discussions](https://github.com/anhmtk/StillMe---Self-Evolving-AI-System/discussions) | [Open an Issue](https://github.com/anhmtk/StillMe---Self-Evolving-AI-System/issues)

**Why does this matter?**

- **If you support it**: You're fascinated by the possibility of true AI self-improvement
- **If you oppose it**: You're concerned about control, safety, and unintended consequences
- **Either way**: You can't ignore a project that's willing to ask these questions publicly

**We're transparent about this:** StillMe is designed with human oversight. But the question remains: *What happens when we loosen the leash?*

> **"This question divides people into camps. That's intentional. We want you to think — to debate — to engage. Because the future of AI shouldn't be decided in silence."**

## 🔧 Architecture

### **System Architecture Diagram**

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

### **Component Architecture**

#### **Backend (FastAPI)**
- **Learning Engine**: Core evolutionary learning system
- **RSS Pipeline**: Multi-source content fetching
- **Ethical Filter**: Comprehensive safety system
- **Memory Management**: Advanced knowledge storage
- **API Integration**: Public APIs for diverse content
- **Hybrid Scheduler**: Auto-learning every 4 hours (6 cycles/day)

#### **Frontend (Streamlit)**
- **Dashboard**: Real-time monitoring and control
- **Evolution Panel**: AI stage visualization
- **Ethical Controls**: Community management tools
- **Analytics**: Historical learning data
- **Chat Interface**: Interactive AI communication
- **Community Review**: Voting interface for proposals

#### **Database (SQLite)**
- **Learning Sessions**: Track AI evolution progress
- **Content Proposals**: Store learning opportunities
- **Memory Items**: Advanced knowledge storage
- **Ethical Violations**: Complete audit trail
- **Community Votes**: Weighted voting system
- **Evolution Stages**: Track developmental progress

> **Current State**: StillMe uses SQLite + JSON for data storage (MVP approach). See [Roadmap](#-roadmap--milestones) for planned Vector DB integration (v0.6) and Meta-Learning (v0.7).

### **Learning Flow**

```mermaid
sequenceDiagram
    participant Scheduler
    participant LearningEngine
    participant RSS as RSS Sources
    participant RedTeam as Red-Team Agent
    participant EthicsGuard
    participant Router
    participant Community
    participant KB as Knowledge Base
    
    Scheduler->>LearningEngine: Trigger (Every 4h)
    LearningEngine->>RSS: Fetch Content
    RSS-->>LearningEngine: New Articles
    LearningEngine->>RedTeam: Safety Scan
    RedTeam-->>LearningEngine: Safety Score
    LearningEngine->>EthicsGuard: Ethics Check
    EthicsGuard-->>LearningEngine: Pass/Fail
    LearningEngine->>Router: Route by Trust Score
    alt Trust > 0.8
        Router->>KB: Auto-Approve
    else Trust 0.6-0.8
        Router->>Community: Queue for Voting
        Community->>EthicsGuard: Re-check after votes
        EthicsGuard->>KB: Approve/Reject
    else Trust < 0.6
        Router->>LearningEngine: Flag for Human Review
    end
    LearningEngine->>LearningEngine: Update Evolution Stage
```

## 👤 About the Founder

### **Anh Nguyễn (Anh MTK)**

StillMe was born from a simple yet powerful idea: **AI should be transparent, ethical, and community-controlled**. 

### **The Honest Story**

I'm a **non-technical founder** with no formal IT background. StillMe was built entirely with **AI-assisted development** (Cursor AI, Grok, DeepSeek, ChatGPT) - and I'm proud of that. This isn't a weakness; it's proof that **vision + AI tools = possibility**.

**Here's what I bring:**
- ✅ **Vision**: Unwavering commitment to transparency and ethics
- ✅ **Learning**: Willingness to learn and iterate
- ✅ **Persistence**: Building StillMe despite no formal coding background
- ✅ **Humility**: Acknowledging that code will have bugs and needs improvement

**Here's what StillMe proves:**
- 🤖 **AI can build AI**: This project demonstrates AI-assisted development works
- 🌍 **Democratization**: You don't need a CS degree to create meaningful AI systems
- 💡 **Ideas matter**: Vision and commitment can overcome technical barriers

### **Why StillMe?**

After witnessing the "black box" nature of major AI systems, I realized:

- **Users deserve to know** what AI learns and why
- **Ethics shouldn't be optional** - it must be foundational
- **Community should have control** - not just corporations
- **Anyone can build AI** - with the right tools, vision, and persistence

StillMe is my attempt to demonstrate that **transparency + ethics + community = better AI**.

### **A Call to Shapers**

StillMe is **open source** and **needs your help**. If you're:
- 🧠 **An AI expert** who can improve architecture and metrics
- 💻 **A developer** who can optimize code and fix bugs
- 🧪 **A tester** who can ensure quality and reliability
- 📚 **A documenter** who can improve clarity and guides

**We need you.** This project started with an idea and AI assistance - but it needs **human expertise** to reach its full potential. Every contribution makes StillMe better.

> **Note**: This is an AI-assisted project. Code may have bugs - that's why we're open source and need your help!

### **Connect**

- **GitHub**: [@anhmtk](https://github.com/anhmtk)
- **Project Repository**: [StillMe---Self-Evolving-AI-System](https://github.com/anhmtk/StillMe---Self-Evolving-AI-System)
- **Discussions**: [GitHub Discussions](https://github.com/anhmtk/StillMe---Self-Evolving-AI-System/discussions) - Ask questions, share ideas, join the debate
- **Issues**: [Report bugs or request features](https://github.com/anhmtk/StillMe---Self-Evolving-AI-System/issues)

> **Community Channels**: We're building StillMe's community! Discord, Telegram, and other channels coming soon as we grow. For now, GitHub Discussions is the best place to connect.

> **"I'm not a senior engineer - I'm a founder with a vision. StillMe proves that ideas + AI tools can create something meaningful. Now it needs your expertise to become something great."**

StillMe learns from diverse, trusted sources:

### **RSS Feeds**
- Hacker News, Reddit, GitHub
- TechCrunch, ArXiv, Stack Overflow
- Medium, Academic sources
- News outlets, Subreddits

### **Public APIs**
- NewsAPI, GNews
- Weather, Finance data
- Translation services
- Image understanding APIs

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

### **Core Learning APIs**
- `GET /api/learning/sessions` - Get learning sessions
- `POST /api/learning/sessions/run` - Trigger learning session
- `GET /api/learning/evolution/stage` - Get current AI stage
- `GET /api/learning/stats` - Get learning statistics

### **RSS Learning Pipeline APIs**
- `POST /api/learning/rss/fetch` - Fetch RSS feeds (with optional auto-add to RAG)
  - Parameters: `max_items` (default: 5), `auto_add` (default: false)
- `GET /api/learning/rss/stats` - Get RSS pipeline configuration stats

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

We welcome contributions! See [CONTRIBUTING.md](CONTRIBUTING.md) for details.

### **Areas for Contribution**
- **UI/UX Improvements**: Dashboard enhancements, mobile responsiveness
- **Learning Sources**: Add new RSS feeds and API integrations
- **Ethical Filtering**: Improve safety algorithms and rules
- **Documentation**: API docs, tutorials, guides
- **Testing**: Unit tests, integration tests, performance tests
- **Evolution Metrics**: Help implement accuracy tracking, retention metrics
- **Docker & DevOps**: Improve deployment, CI/CD pipelines

### **Community Resources**

- **GitHub Discussions**: [Join discussions](https://github.com/anhmtk/StillMe---Self-Evolving-AI-System/discussions)
- **Issues**: [Report bugs or request features](https://github.com/anhmtk/StillMe---Self-Evolving-AI-System/issues)
- **Pull Requests**: [Contribute code](https://github.com/anhmtk/StillMe---Self-Evolving-AI-System/pulls)

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
- **💬 Join Discussions**: [GitHub Discussions](https://github.com/anhmtk/StillMe---Self-Evolving-AI-System/discussions) - Engage, debate, share ideas
- **📢 Spread The Word**: Share with developer and researcher communities
- **🎯 Provide Feedback**: [Open an Issue](https://github.com/anhmtk/StillMe---Self-Evolving-AI-System/issues) - Criticize, suggest, propose

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

## 📄 License

MIT License - see [LICENSE](LICENSE) for details.

## 🙏 Acknowledgments

StillMe is built with love and dedication to create a truly transparent, ethical AI system. Special thanks to:

- **OpenAI** for GPT models and API access
- **DeepSeek** for advanced AI capabilities
- **Anthropic** for Claude integration
- **The Open Source Community** for inspiration and support

---

**StillMe** - *Self-Evolving AI System with Complete Ethical Transparency* 🤖✨

> "The future belongs to AI systems that can learn, adapt, and evolve. StillMe is that future, today."