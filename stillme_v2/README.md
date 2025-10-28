# 🧠 StillMe V2 - Self-Evolving AI System

<div align="center">
  <img src="assets/logo.png" alt="StillMe V2 Logo" width="200"/>
</div>

> **A revolutionary AI system that learns and evolves from the internet daily, becoming smarter with each interaction.**

[![Python](https://img.shields.io/badge/Python-3.12+-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)](https://fastapi.tiangolo.com)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.28+-red.svg)](https://streamlit.io)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## 🌟 What is StillMe V2?

StillMe V2 is a **Self-Evolving AI System** that continuously learns from the internet, adapts to new information, and evolves through different developmental stages - just like a growing organism. Unlike traditional AI systems that remain static, StillMe V2 gets smarter every day.

### 🎯 Core Concept

- **🧬 Evolutionary Learning**: AI progresses through stages (Infant → Child → Adolescent → Adult)
- **📚 Multi-Source Learning**: RSS feeds + Public APIs integration (Hacker News, GitHub, Reddit, ArXiv)
- **🌐 Real-time Data**: Live data from multiple trusted sources with transparency
- **🔄 Self-Assessment**: Continuous performance evaluation with ReasoningBank concepts
- **📊 Transparent Dashboard**: Complete visibility into all learning sources and data
- **📈 Historical Analytics**: Track learning progress over time with flexible timeline analysis
- **🔍 Raw Data Access**: View actual API responses for verification and trust
- **💬 Interactive Chat**: Communicate with your evolving AI assistant
- **🛡️ Ethical Filtering**: Comprehensive ethical content filtering with complete transparency

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │    Backend      │    │   Database      │
│   (Streamlit)   │◄──►│   (FastAPI)     │◄──►│   (SQLite)      │
│                 │    │                 │    │                 │
│ • Dashboard     │    │ • Learning API  │    │ • Proposals     │
│ • Chat Interface│    │ • Evolution API │    │ • Sessions      │
│ • Admin Panel   │    │ • RSS Pipeline  │    │ • Daily Stats   │
│ • Analytics     │    │ • Analytics API │    │ • Memory        │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### 🔧 Technology Stack

- **Backend**: FastAPI + SQLAlchemy + Uvicorn
- **Frontend**: Streamlit Dashboard with transparent data visualization
- **Database**: SQLite (with migration support)
- **AI Integration**: OpenAI, DeepSeek, Anthropic APIs
- **Learning Sources**: RSS feeds + Public APIs (Hacker News, GitHub, Reddit ML, ArXiv, Weather)
- **Data Transparency**: Complete visibility into all sources with trust scoring
- **Monitoring**: Real-time metrics, evolution tracking, and source performance
- **Analytics**: Historical learning analysis with flexible timeline comparison

## 🚀 Quick Start

### Prerequisites

- Python 3.12+
- pip package manager

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/stillme-v2.git
   cd stillme-v2
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment**
   ```bash
   cp env.example .env
   # Edit .env with your API keys
   ```

4. **Start the system**
   ```bash
   # Terminal 1: Start Backend
   python -m uvicorn backend.api.main:app --port 8000
   
   # Terminal 2: Start Frontend
   streamlit run dashboard.py --server.port 8501
   ```

5. **Access the dashboard**
   - Frontend: http://localhost:8501
   - Backend API: http://localhost:8000
   - API Docs: http://localhost:8000/docs

## 📋 Features

### 🧠 Evolutionary Learning Engine

- **Stage Progression**: AI evolves through 4 developmental stages
- **Daily Learning**: Automatic RSS feed processing and content analysis
- **Quality Assessment**: Intelligent filtering of learning content with advanced scoring
- **Performance Tracking**: Continuous monitoring of learning effectiveness
- **Trust Score Management**: Dynamic trust scoring based on learning outcomes
- **Auto-approval System**: Smart content approval based on quality and trust metrics

### 📊 Dashboard Features

- **Evolution Panel**: Real-time AI stage and progress tracking
- **Learning Table**: History of all learning sessions
- **Metrics Charts**: Visual representation of AI performance
- **Chat Interface**: Interactive communication with AI
- **Admin Panel**: System configuration and management
- **📈 Historical Analytics**: Flexible timeline analysis (Today vs Yesterday, Last 7/30/90 Days, Custom Range)
- **Manual Controls**: Fetch content, generate proposals, update stats
- **Real-time Status**: Live monitoring of all data sources

### 🛡️ Ethical Safety Filter

StillMe V2 features a comprehensive ethical content filtering system that ensures responsible AI learning:

#### **Core Principles**
- **Beneficence**: Content must benefit learning and users
- **Non-Maleficence**: Blocks harmful, toxic, or dangerous content
- **Autonomy**: Protects privacy and personal information
- **Justice**: Prevents biased or discriminatory content
- **Transparency**: Complete visibility into all filtering decisions
- **Accountability**: Full audit trail of ethical violations

#### **Filtering Capabilities**
- **Input Filtering**: Blocks harmful content at the source (RSS/API)
- **Content Analysis**: Detects toxicity, bias, and sensitive topics
- **PII Protection**: Automatically identifies and blocks personal information
- **Source Validation**: Flags unreliable or suspicious sources
- **Real-time Monitoring**: Continuous ethical compliance checking

#### **Transparency Features**
- **Violation Logging**: Complete history of all ethical violations
- **Dashboard Integration**: Real-time ethical metrics and statistics
- **Community Management**: Blacklist keywords and rules can be managed
- **Audit Trail**: Full transparency into all ethical decisions
- **API Access**: Programmatic access to ethical statistics and controls

### 🔌 API Endpoints

#### Core Learning APIs
- `GET /health` - System health check
- `GET /stats` - System statistics
- `POST /chat` - Chat with AI
- `GET /learning/history` - Learning session history
- `POST /learning/session` - Trigger learning session
- `GET /proposals` - View learning proposals

#### RSS & Content APIs
- `GET /api/learning/rss/pipeline-stats` - RSS and Public APIs statistics
- `POST /api/learning/rss/fetch-content` - Fetch live content from all sources
- `GET /api/learning/rss/fetched-content` - View recently fetched content
- `GET /api/learning/proposals/learned` - View learned proposals

#### Historical Analytics APIs
- `GET /api/learning/analytics/historical` - Get stats for date range
- `GET /api/learning/analytics/comparison` - Compare two dates
- `GET /api/learning/analytics/trends` - Analyze trends over N days
- `POST /api/learning/analytics/update-today` - Update today's statistics

#### Advanced Learning APIs
- `GET /api/learning/knowledge/stats` - Knowledge consolidation statistics
- `POST /api/learning/knowledge/consolidate` - Trigger knowledge consolidation
- `GET /api/learning/knowledge/search` - Search consolidated knowledge
- `GET /api/learning/memory/stats` - Advanced memory management stats
- `POST /api/learning/memory/optimize` - Optimize memory usage

#### Ethical Safety APIs
- `GET /api/learning/ethics/stats` - Get ethical filter statistics
- `POST /api/learning/ethics/check-content` - Test content for ethical compliance
- `GET /api/learning/ethics/violations` - Get ethical violation history
- `POST /api/learning/ethics/clear-violations` - Clear violation log
- `POST /api/learning/ethics/add-blacklist-keyword` - Add keyword to blacklist
- `GET /api/learning/ethics/blacklist-keywords` - Get current blacklist

## 🌐 Public APIs Integration

StillMe V2 integrates with multiple public APIs to provide diverse, real-time learning sources:

### 📡 Data Sources

| Source | Category | Trust Score | Rate Limit | Description |
|--------|----------|-------------|------------|-------------|
| **Hacker News API** | Technology | 0.9 | 1000/hour | Top tech stories and discussions |
| **GitHub Trending** | Development | 0.85 | 500/hour | Popular repositories and projects |
| **Reddit ML** | AI Community | 0.8 | 100/hour | Machine learning discussions |
| **ArXiv API** | Research | 0.95 | 200/hour | Latest AI research papers |
| **OpenWeatherMap** | Context | 0.9 | 1000/hour | Weather data for context |

### 🔍 Transparency Features

- **✅ Complete Source Visibility**: All data sources are listed in the dashboard
- **✅ Trust Scoring**: Each source has a transparent trust score
- **✅ Rate Limiting**: Clear display of API usage limits
- **✅ Raw Data Access**: View actual API responses in the dashboard
- **✅ Error Handling**: Graceful fallbacks when sources are unavailable
- **✅ Real-time Status**: Live monitoring of all data sources

### 🛡️ Data Quality & Trust

- **Trust Scoring System**: Each source is rated based on reliability and accuracy
- **Content Validation**: Automatic filtering of low-quality content
- **Duplicate Detection**: Prevents learning from duplicate information
- **Rate Limiting**: Respects API limits to maintain good relationships
- **Error Recovery**: Continues learning even when some sources fail
- **Dynamic Trust Updates**: Trust scores evolve based on learning outcomes

## 📈 Historical Learning Analytics

StillMe V2 provides comprehensive historical analysis of learning progress:

### 🕒 Timeline Analysis

- **Today vs Yesterday**: Compare daily learning metrics
- **Last 7 Days**: Weekly learning trends and patterns
- **Last 30 Days**: Monthly progress analysis
- **Last 90 Days**: Quarterly evolution tracking
- **Custom Range**: Analyze any specific time period

### 📊 Analytics Features

- **Learning Efficiency**: Track content-to-proposal conversion rates
- **Quality Trends**: Monitor average quality scores over time
- **Evolution Tracking**: See AI stage progression
- **Source Performance**: Analyze which sources provide the best content
- **Growth Metrics**: Calculate learning growth rates and patterns
- **Best Learning Days**: Identify peak learning periods

### 🔄 Manual Controls

- **📡 Fetch Content Now**: Manually trigger content fetching
- **🧠 Generate Proposals**: Create learning proposals from fetched content
- **📊 Update Stats**: Refresh today's learning statistics

## 🛣️ Roadmap

### Phase 1: Foundation (✅ Completed)
- ✅ Core evolutionary learning engine
- ✅ Transparent dashboard interface
- ✅ RSS feed integration
- ✅ Public APIs integration (Hacker News, GitHub, Reddit, ArXiv)
- ✅ SQLite database schema
- ✅ FastAPI backend structure
- ✅ ReasoningBank concepts integration
- ✅ Trust scoring system
- ✅ Raw data access transparency

### Phase 2: Advanced Learning (✅ Completed)
- ✅ Historical Learning Analytics with timeline comparison
- ✅ Dynamic trust score management
- ✅ Advanced quality scoring system
- ✅ Knowledge consolidation service
- ✅ Advanced memory management
- ✅ Manual learning controls
- ✅ Daily statistics tracking
- ✅ Learning efficiency metrics

### Phase 3: Intelligence (🔄 Current)
- 🔄 Enhanced chat interface with memory integration
- 🔄 Performance optimization
- 🔄 Comprehensive testing suite
- 🔄 Community feedback integration
- 🔄 Export learning reports (CSV, JSON)

### Phase 4: Evolution (📅 Future)
- 📅 Advanced AI model integration
- 📅 Community learning features
- 📅 Mobile application
- 📅 Cloud deployment
- 📅 Enterprise features

### Phase 5: Vision (🚀 Long-term)
- 🚀 Autonomous learning optimization
- 🚀 Cross-platform synchronization
- 🚀 Advanced analytics with ML insights
- 🚀 Plugin ecosystem
- 🚀 Global AI network

## 🔧 Configuration

### Environment Variables

```bash
# Core Configuration
STILLME_DRY_RUN=1
RUNTIME_BASE_URL=http://localhost:8000

# AI Provider API Keys
DEEPSEEK_API_KEY=sk-REPLACE_ME
OPENAI_API_KEY=sk-REPLACE_ME
ANTHROPIC_API_KEY=sk-REPLACE_ME

# Learning Configuration
MAX_DAILY_PROPOSALS=50
AUTO_APPROVAL_THRESHOLD=0.8
LEARNING_SESSION_HOUR=9

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
NOTIFY_EVOLUTION=true

# RSS Sources
RSS_SOURCES=https://hnrss.org/frontpage,https://www.reddit.com/r/MachineLearning.rss
```

### Learning Sources

Configure RSS feeds and learning topics in `config.py`:

```python
RSS_FEEDS = [
    "https://feeds.bbci.co.uk/news/rss.xml",
    "https://rss.cnn.com/rss/edition.rss",
    "https://feeds.reuters.com/reuters/technologyNews"
]

LEARNING_TOPICS = [
    "technology",
    "artificial intelligence", 
    "machine learning",
    "programming",
    "software development"
]
```

## 📊 Evolution Stages

| Stage | Duration | Characteristics |
|-------|----------|----------------|
| 👶 **Infant** | 0-7 days | Basic learning, simple patterns |
| 🧒 **Child** | 8-30 days | Improved accuracy, better filtering |
| 👦 **Adolescent** | 31-90 days | Advanced reasoning, complex topics |
| 👨 **Adult** | 90+ days | Expert-level knowledge, autonomous learning |

## 🧠 Advanced Learning Features

### 🔄 Knowledge Consolidation

- **Deduplication**: Automatic removal of duplicate content
- **Clustering**: Group similar knowledge items together
- **Summarization**: Create concise summaries of related content
- **Indexing**: Efficient search and retrieval system

### 🧠 Advanced Memory Management

- **Memory Prioritization**: Important memories are prioritized
- **Memory Compression**: Efficient storage of large amounts of data
- **Memory Clustering**: Related memories are grouped together
- **Context-aware Retrieval**: Memories retrieved based on context

### 📊 Quality Scoring System

- **Semantic Quality**: How well content aligns with its topic
- **Technical Depth**: Estimation of technical complexity
- **Readability**: Assessment of content readability
- **Keyword Density**: Relevance based on keyword presence
- **Content Length**: Optimal length scoring
- **Title Quality**: Engagement and informativeness

## 🤝 Community Trust & Transparency

StillMe V2 is built on the principle of **complete transparency** to build trust with the open-source community:

### 🔍 What We Show You

- **📊 All Data Sources**: Every RSS feed and API endpoint is visible
- **🔢 Trust Scores**: Transparent scoring system for data quality
- **📈 Rate Limits**: Clear display of API usage constraints
- **🔍 Raw Data**: Access to actual API responses for verification
- **⚠️ Error Handling**: See when sources fail and how we handle it
- **📋 Learning History**: Complete audit trail of what the AI learns
- **📈 Historical Analytics**: Track learning progress over any time period
- **🧠 Memory Contents**: View what the AI has learned and remembered

### 🛡️ Privacy & Ethics

- **No Hidden APIs**: All data sources are documented and visible
- **No Secret Endpoints**: Every API call is transparent
- **No Data Hoarding**: We show you exactly what data we collect
- **No Black Box**: The learning process is completely transparent
- **Community Driven**: Built for the community, by the community

### 🎯 Why Transparency Matters

> **"Transparency builds trust. Trust builds community. Community builds the future."**

- **🔬 Research**: Researchers can verify our learning sources
- **🛡️ Security**: Security experts can audit our data handling
- **🤝 Community**: Developers can contribute and improve
- **📚 Education**: Students can learn from our implementation
- **🌍 Open Source**: Complete codebase available for inspection

## 🚀 Getting Started Guide

### 1. First Time Setup

```bash
# Clone and setup
git clone https://github.com/yourusername/stillme-v2.git
cd stillme-v2
pip install -r requirements.txt
cp env.example .env

# Edit .env with your API keys
nano .env
```

### 2. Start the System

```bash
# Start backend
python -m uvicorn backend.api.main:app --port 8000

# Start frontend (new terminal)
streamlit run dashboard.py --server.port 8501
```

### 3. First Learning Session

1. Open http://localhost:8501
2. Click **"📡 Fetch Content Now"** to fetch content
3. Click **"🧠 Generate Proposals"** to create learning proposals
4. Select timeline analysis to see progress
5. Monitor learning efficiency and quality metrics

### 4. Daily Usage

- **Automatic**: Scheduler runs learning sessions every hour
- **Manual**: Use dashboard controls for immediate learning
- **Analytics**: Check historical progress with timeline selector
- **Monitoring**: Watch evolution stage progression

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guidelines](CONTRIBUTING.md) for details.

### Development Setup

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Make your changes
4. Run tests: `python -m pytest tests/`
5. Commit changes: `git commit -m 'Add amazing feature'`
6. Push to branch: `git push origin feature/amazing-feature`
7. Open a Pull Request

### Development Areas

- **🧠 Learning Algorithms**: Improve content processing and quality scoring
- **📊 Analytics**: Enhance historical analysis and visualization
- **🔌 API Integration**: Add new data sources and APIs
- **🎨 UI/UX**: Improve dashboard design and user experience
- **🧪 Testing**: Expand test coverage and quality assurance
- **📚 Documentation**: Improve guides and API documentation

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- FastAPI team for the excellent web framework
- Streamlit team for the amazing dashboard framework
- OpenAI, DeepSeek, and Anthropic for AI capabilities
- The open-source community for inspiration and tools
- ReasoningBank research for self-learning concepts
- Sparse Memory Finetuning research for memory management

## 📞 Support

- 📧 Email: support@stillme.ai
- 💬 Discord: [StillMe Community](https://discord.gg/stillme)
- 📖 Documentation: [docs.stillme.ai](https://docs.stillme.ai)
- 🐛 Issues: [GitHub Issues](https://github.com/yourusername/stillme-v2/issues)

## 🎯 Key Features Summary

### ✅ What's Working Now

- **🧠 Self-Evolving AI**: Learns and evolves through developmental stages
- **📊 Real-time Dashboard**: Complete transparency into learning process
- **📈 Historical Analytics**: Track progress over any time period
- **🌐 Multi-Source Learning**: RSS + Public APIs integration
- **🔄 Manual Controls**: Fetch content, generate proposals, update stats
- **📊 Quality Scoring**: Advanced content quality assessment
- **🧠 Memory Management**: Efficient knowledge storage and retrieval
- **📧 Notifications**: Email and Telegram integration
- **🔍 Transparency**: Complete visibility into all data sources

### 🚀 What Makes StillMe V2 Special

1. **Complete Transparency**: Every data source, API call, and learning decision is visible
2. **Historical Analysis**: Track learning progress over any time period
3. **Dynamic Trust Scoring**: Trust scores evolve based on learning outcomes
4. **Advanced Memory**: Sophisticated memory management with prioritization
5. **Community Focus**: Built for open-source community with full transparency
6. **Real-time Monitoring**: Live dashboard with manual controls
7. **Quality Assurance**: Advanced scoring system ensures high-quality learning

---

**StillMe V2** - *Where AI meets Evolution* 🧠✨

> "The future belongs to AI systems that can learn, adapt, and evolve. StillMe V2 is that future, today."