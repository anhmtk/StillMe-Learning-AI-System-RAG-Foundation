<!-- bb9be224-1066-45b8-a3f0-9219a273bef8 139e2d6b-449a-4a03-b21c-2e007b391027 -->
# StillMe V2.0: Self-Evolving AI - Implementation Plan

## Overview

Rebuild StillMe from scratch focusing on **self-learning AI** that learns from RSS/web sources, proposes new knowledge, and evolves transparently. Target: **12 weeks part-time**, **Streamlit + FastAPI**, **DeepSeek API**.

**Unique Value:** First open-source AI that learns from internet daily, shows what it learns, and evolves itself - completely transparent.

## Target Configuration

- **Timeline**: 12 weeks (part-time, ~20 hours/week)
- **Frontend**: Streamlit (fastest, Python-only)
- **AI Model**: DeepSeek only (cheapest, $1 per 1M tokens)
- **Deployment**: Railway/Render (free tier initially)
- **Target Users**: Global open source community

## Phase 1: Foundation (Week 1-3)

### Architecture Setup

**Files to create:**

```
stillme_v2/
├── backend/
│   ├── api/
│   │   ├── main.py              # FastAPI app
│   │   ├── routes/
│   │   │   ├── chat.py          # Chat endpoints
│   │   │   ├── learning.py      # Learning endpoints
│   │   │   └── proposals.py     # Proposal management
│   │   └── models/              # Pydantic models
│   ├── core/
│   │   ├── learning_engine.py   # REUSE: EvolutionaryLearningSystem
│   │   ├── memory.py            # REUSE: ExperienceMemory
│   │   └── safety.py            # REUSE: ContentIntegrityFilter
│   ├── services/
│   │   ├── rss_pipeline.py      # REUSE: DailyLearningManager
│   │   ├── embedding.py         # Vector embeddings
│   │   └── deepseek_client.py   # AI client
│   └── database/
│       ├── schema.py            # SQLAlchemy models
│       └── migrations/          # Alembic migrations
├── frontend/
│   └── app.py                   # Streamlit app
├── tests/
│   ├── test_learning.py
│   └── test_api.py
├── requirements.txt
├── .env.example
└── README.md
```

### Core Database Schema

```sql
-- proposals table (what AI wants to learn)
CREATE TABLE proposals (
    id INTEGER PRIMARY KEY,
    source_url TEXT,
    title TEXT,
    summary TEXT,
    status TEXT,  -- pending/approved/rejected
    quality_score FLOAT,
    created_at TIMESTAMP
);

-- learning_sessions table (daily learning records)
CREATE TABLE learning_sessions (
    id INTEGER PRIMARY KEY,
    date DATE,
    proposals_learned INTEGER,
    accuracy_delta FLOAT,
    evolution_stage TEXT,  -- infant/child/adolescent/adult
    created_at TIMESTAMP
);

-- knowledge_base table (what AI learned)
CREATE TABLE knowledge_base (
    id INTEGER PRIMARY KEY,
    content TEXT,
    embedding BLOB,
    source TEXT,
    learned_at TIMESTAMP
);
```

### Modules to Reuse from Current Codebase

1. **stillme_core/core/self_learning/experience_memory.py** (~70% reuse)
2. **stillme_core/modules/daily_learning_manager.py** (~60% reuse)
3. **stillme_core/modules/content_integrity_filter.py** (~80% reuse)
4. **stillme_core/learning/evolutionary_learning_system.py** (~50% reuse)

## Phase 2: Self-Learning Core (Week 4-6)

### RSS/Web Pipeline

**Implement:**

- 12 RSS sources: HackerNews, Reddit AI, GitHub Trending, ArXiv, TechCrunch, etc.
- Scraper with rate limiting and error handling
- Content deduplication
- Quality filtering (remove spam, ads)

**Key Code (simplified):**

```python
# backend/services/rss_pipeline.py
class RSSLearningPipeline:
    def fetch_daily_content(self):
        """Fetch from 12 sources, filter, deduplicate"""
        
    def generate_proposals(self, contents):
        """Use DeepSeek to analyze and create proposals"""
        
    def calculate_quality_score(self, proposal):
        """Score based on: source reputation, content relevance, novelty"""
```

### Embedding & Knowledge Storage

- Use `sentence-transformers` for local embeddings (free)
- FAISS for vector similarity search
- Store in SQLite for simplicity

### Auto-Approval System

**Logic:**

```python
def should_auto_approve(proposal):
    if proposal.quality_score > 0.8 and \
       proposal.source in TRUSTED_SOURCES and \
       not has_sensitive_content(proposal):
        return True
    return False  # Require human review
```

## Phase 3: Evolution System (Week 7-9)

### Daily Learning Sessions

**Workflow:**

1. Fetch RSS content (morning)
2. Generate proposals (analyze content)
3. Auto-approve safe proposals
4. Learn from approved proposals
5. Update knowledge base
6. Self-assess performance
7. Adjust learning parameters

### Evolution Stages

```python
EVOLUTION_STAGES = {
    "infant": (0, 7),      # 0-7 days: basic learning
    "child": (8, 30),      # 8-30 days: reasoning
    "adolescent": (31, 90), # 31-90 days: optimization
    "adult": (91, None)    # 90+ days: full autonomy
}
```

### Self-Assessment Metrics

- Accuracy delta on benchmark Q&A
- Knowledge retention rate
- Response quality improvement
- Safety violation rate

## Phase 4: Web Interface (Week 10-11)

### Streamlit Dashboard Pages

```python
# frontend/app.py structure
pages = {
    "💬 Chat": chat_page(),
    "🧠 Learning": learning_dashboard(),
    "📊 Evolution": evolution_metrics(),
    "🔍 Knowledge": knowledge_browser(),
    "⚙️ Settings": settings_page()
}
```

### Key Features:

- **Chat**: Talk with AI, see its knowledge in action
- **Learning Dashboard**: Live view of what AI is learning today
- **Evolution Metrics**: Charts showing AI improvement over time
- **Knowledge Browser**: Search what AI knows
- **Approval Queue**: Review pending proposals (if opted in)

## Phase 5: Polish & Launch (Week 12)

### Pre-Launch Checklist

- [ ] API documentation (auto-generated with FastAPI)
- [ ] GitHub README with demo GIF
- [ ] Docker setup for easy deployment
- [ ] Test with 5-10 beta users
- [ ] Security audit (basic: no secrets in code, rate limiting)
- [ ] Performance optimization (caching, lazy loading)

### Launch Strategy

1. **GitHub Launch**: Post on r/LocalLLaMA, r/opensource, r/Python
2. **Demo Video**: 2-min showing AI learning in realtime
3. **Blog Post**: Technical deep-dive on architecture
4. **Community**: Setup Discord/Discussions for contributors

## Key Decisions & Rationale

### Why Streamlit?

- **Fast**: Build UI in pure Python
- **Good enough**: Community doesn't need fancy UI for MVP
- **Easy**: Contributors can add pages without React knowledge
- **Cost**: Free, no frontend build pipeline

### Why DeepSeek Only?

- **Cost**: $1 per 1M tokens (100x cheaper than GPT-4)
- **Quality**: Good enough for content analysis
- **Simplicity**: No complex router logic needed

### Why SQLite?

- **Simple**: No separate DB server needed
- **Portable**: Easy backup (just copy .db file)
- **Good enough**: Handles 100k+ records easily
- **Upgrade path**: Can migrate to PostgreSQL later if needed

### What to Reuse vs Rebuild?

**Reuse (60% of effort saved):**

- Learning algorithms (ExperienceMemory, DailyLearningManager)
- Safety filters (ContentIntegrityFilter)
- RSS sources list and parsing logic

**Rebuild (simpler, cleaner):**

- API layer (FastAPI from scratch)
- Database schema (simplified)
- Frontend (Streamlit instead of complex dashboard)
- Authentication (basic API keys initially)

## Success Metrics (3 months post-launch)

### Community Metrics

- [ ] 100+ GitHub stars
- [ ] 10+ contributors
- [ ] 50+ users trying the system

### Technical Metrics

- [ ] AI learns 10+ new facts per day
- [ ] 80%+ auto-approval rate (safe content)
- [ ] <2s response time for chat
- [ ] 99% uptime

### Sustainability Metrics

- [ ] $50/month in donations (cover server costs)
- [ ] Active Discord community
- [ ] 2-3 regular contributors

## Risk Mitigation

### Risk: AI learns misinformation

**Mitigation:**

- Quality scoring system
- Trusted sources only
- Human review for low-confidence proposals
- Rollback mechanism if issues detected

### Risk: High API costs

**Mitigation:**

- Cache aggressively (Redis/in-memory)
- Rate limit requests
- Use local embeddings (not API)
- Monitor costs daily

### Risk: No community interest

**Mitigation:**

- Strong demo video showing unique value
- Post in multiple communities
- Engage with early users
- Iterate based on feedback quickly

## Next Steps After Plan Approval

1. Create `stillme_v2/` directory structure
2. Setup virtual environment and dependencies
3. Implement Phase 1 foundation
4. Extract and refactor reusable modules from current codebase
5. Begin Phase 2 self-learning core

### To-dos

- [x] Create stillme_v2 project structure with backend/, frontend/, tests/ directories
- [x] Setup Python virtual environment, create requirements.txt with FastAPI, Streamlit, SQLAlchemy dependencies
- [x] Extract and refactor reusable modules: ExperienceMemory, DailyLearningManager, ContentIntegrityFilter from current codebase (Created: memory.py, learning_engine.py, safety.py, rss_pipeline.py)
- [x] Implement SQLite database schema with proposals, learning_sessions, knowledge_base tables (Created: database/schema.py)
- [x] Create FastAPI app with basic routes: /chat, /learning, /proposals endpoints (Created: api/main.py, api/routes/*)
- [x] Implement DeepSeek API client with rate limiting and error handling (Created: services/deepseek_client.py)
- [x] Build RSS/web scraping pipeline with 12 sources, quality filtering, and deduplication (Created: services/rss_pipeline.py)
- [x] Implement core learning engine: proposal generation, auto-approval, knowledge storage (Created: core/learning_engine.py)
- [ ] Build evolution system with daily learning sessions, self-assessment, and stage progression
- [ ] Create Streamlit web interface with chat, learning dashboard, evolution metrics pages
- [ ] Write tests for core functionality: learning pipeline, API endpoints, safety filters
- [ ] Write comprehensive README, API docs, contribution guide, and demo video script
- [ ] Setup Docker, deployment config for Railway/Render, and CI/CD pipeline
- [ ] Beta testing with 5-10 users, security audit, performance optimization, launch materials