# 🧠 StillMe - Self-Evolving AI System

<div align="center">
  <img src="assets/logo.png" alt="StillMe Logo" width="200"/>
</div>

> **A revolutionary AI system that learns and evolves from the internet daily, becoming smarter with each interaction.**

[![Python](https://img.shields.io/badge/Python-3.12+-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)](https://fastapi.tiangolo.com)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.28+-red.svg)](https://streamlit.io)
[![Ethical AI](https://img.shields.io/badge/Ethical%20AI-Transparent-green.svg)](https://github.com/anhmtk/stillme_ai_ipc)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## 🌟 What is StillMe?

StillMe is a **Self-Evolving AI System** that continuously learns from the internet, adapts to new information, and evolves through different developmental stages - just like a growing organism. Unlike traditional AI systems that remain static, StillMe gets smarter every day.

### 🎯 Core Concept

- **🧬 Evolutionary Learning**: AI progresses through stages (Infant → Child → Adolescent → Adult)
- **📚 Multi-Source Learning**: RSS feeds + Public APIs integration
- **🌐 Real-time Data**: Live data from multiple trusted sources with transparency
- **🛡️ Ethical Filtering**: Comprehensive ethical content filtering with complete transparency
- **📊 Transparent Dashboard**: Complete visibility into all learning sources and data
- **💬 Interactive Chat**: Communicate with your evolving AI assistant

## 🛡️ Ethical AI Transparency

StillMe features the world's first **completely transparent ethical filtering system**:

- **Complete Visibility**: All ethical violations are logged and visible
- **Open Source**: Filtering rules and algorithms are publicly available
- **Community Driven**: Blacklist and rules can be managed by the community
- **Audit Trail**: Full history of all ethical decisions and violations
- **Configurable**: Ethics level can be adjusted based on community needs

This transparency ensures StillMe learns responsibly while maintaining community trust.

## 🚀 Quick Start

```bash
# Clone repository
git clone https://github.com/anhmtk/stillme_ai_ipc.git
cd stillme_ai_ipc

# Install dependencies
pip install -r requirements.txt

# Start backend
python start_backend.py

# Start frontend (new terminal)
python start_frontend.py
```

## 📊 Dashboard Features

- **Evolution Panel**: Real-time AI stage and progress tracking
- **Ethical Filter**: Complete transparency into ethical decisions
- **Learning Analytics**: Historical progress with flexible timeline analysis
- **Community Controls**: Manage ethical rules and blacklist
- **Raw Data Access**: View actual API responses for verification

## 🧬 AI Evolution Stages

StillMe progresses through distinct developmental stages:

### 🍼 **Infant Stage** (0-100 learning sessions)
- Basic pattern recognition
- Simple content categorization
- High safety focus
- Manual approval required

### 👶 **Child Stage** (100-500 sessions)
- Improved content understanding
- Basic reasoning capabilities
- Selective auto-approval
- Enhanced safety protocols

### 🧑 **Adolescent Stage** (500-1000 sessions)
- Advanced reasoning
- Context awareness
- Smart auto-approval
- Balanced learning approach

### 🧠 **Adult Stage** (1000+ sessions)
- Sophisticated understanding
- Complex reasoning
- Autonomous learning
- Expert-level knowledge

## 🔧 Architecture

### **Backend (FastAPI)**
- **Learning Engine**: Core evolutionary learning system
- **RSS Pipeline**: Multi-source content fetching
- **Ethical Filter**: Comprehensive safety system
- **Memory Management**: Advanced knowledge storage
- **API Integration**: Public APIs for diverse content

### **Frontend (Streamlit)**
- **Dashboard**: Real-time monitoring and control
- **Evolution Panel**: AI stage visualization
- **Ethical Controls**: Community management tools
- **Analytics**: Historical learning data
- **Chat Interface**: Interactive AI communication

### **Database (SQLite)**
- **Learning Sessions**: Track AI evolution progress
- **Content Proposals**: Store learning opportunities
- **Memory Items**: Advanced knowledge storage
- **Ethical Violations**: Complete audit trail

## 📚 Learning Sources

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

## 🔧 Configuration

### **Environment Setup**
```bash
# Copy environment template
cp env.example .env

# Edit with your API keys
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
```

## 📊 API Endpoints

### **Core Learning APIs**
- `GET /api/learning/sessions` - Get learning sessions
- `POST /api/learning/sessions/run` - Trigger learning session
- `GET /api/learning/evolution/stage` - Get current AI stage
- `GET /api/learning/stats` - Get learning statistics

### **Content Management APIs**
- `GET /api/learning/proposals` - Get learning proposals
- `POST /api/learning/proposals/{id}/approve` - Approve proposal
- `POST /api/learning/proposals/{id}/reject` - Reject proposal
- `GET /api/learning/rss/pipeline-stats` - Get RSS pipeline stats
- `POST /api/learning/rss/fetch-content` - Fetch content manually

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