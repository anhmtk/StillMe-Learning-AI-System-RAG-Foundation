# 🚀 Getting Started with StillMe

Quick start guide to get StillMe up and running in minutes.

## ⚡ Quick Start (5 minutes)

### Prerequisites

- Python 3.12+ installed
- API key from one of: DeepSeek, OpenAI, Claude, or Gemini
- (Optional) Docker for containerized setup

### Step 1: Clone Repository

```bash
git clone https://github.com/anhmtk/StillMe-Learning-AI-System-RAG-Foundation.git
cd StillMe-Learning-AI-System-RAG-Foundation
```

### Step 2: Install Dependencies

```bash
# Create virtual environment
python -m venv venv

# Activate (Windows)
venv\Scripts\activate

# Activate (Linux/Mac)
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Step 3: Configure Environment

```bash
# Copy example env file
cp env.example .env

# Edit .env and add your API key (at minimum, one of):
# DEEPSEEK_API_KEY=sk-your-key-here
# OPENAI_API_KEY=sk-your-key-here
# ANTHROPIC_API_KEY=sk-ant-your-key-here
# GOOGLE_API_KEY=your-key-here
```

### Step 4: Start Services

**Terminal 1 - Backend:**
```bash
python -m uvicorn backend.api.main:app --host 0.0.0.0 --port 8000 --reload
```

**Terminal 2 - Dashboard:**
```bash
streamlit run dashboard.py --server.port 8501
```

### Step 5: Access StillMe

- **Dashboard**: http://localhost:8501
- **API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

**That's it!** You're ready to use StillMe.

---

## 🐳 Docker Setup (Recommended)

### Quick Start with Docker

```bash
# Copy environment template
cp env.example .env
# Edit .env with your API keys

# Start all services
docker compose up -d

# Check logs
docker compose logs -f

# Stop services
docker compose down
```

**Access:**
- Dashboard: http://localhost:8501
- API: http://localhost:8000

---

## 📝 First Steps

### 1. Test API Connection

```bash
curl http://localhost:8000/api/status
```

Should return:
```json
{
  "status": "healthy",
  "service": "stillme-backend"
}
```

### 2. Send Your First Chat

**Via Dashboard:**
- Open http://localhost:8501
- Type a question in the chat interface
- StillMe will respond with citations

**Via API:**
```bash
curl -X POST http://localhost:8000/api/chat/rag \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What is StillMe?",
    "use_rag": true
  }'
```

### 3. Explore Features

- **RAG Interface**: See how StillMe retrieves context
- **Validation Panel**: Monitor validation chain results
- **Learning Metrics**: Track StillMe's learning progress

---

## 🔧 Configuration Options

### Environment Variables

**Required:**
- `DEEPSEEK_API_KEY` or `OPENAI_API_KEY` - LLM API key

**Optional:**
- `ENABLE_VALIDATORS=true` - Enable validation chain (default: true)
- `ENABLE_ARXIV=true` - Enable arXiv fetching (default: true)
- `ENABLE_WIKIPEDIA=true` - Enable Wikipedia fetching (default: true)
- `OLLAMA_URL=http://localhost:11434` - For local Ollama

See `env.example` for full list.

---

## 🎯 Next Steps

### For Users

1. **Read User Guide**: [`docs/USER_GUIDE.md`](USER_GUIDE.md)
2. **Explore Dashboard**: Try different questions
3. **Check API Docs**: http://localhost:8000/docs

### For Developers

1. **Read Contributing Guide**: [`CONTRIBUTING.md`](../CONTRIBUTING.md)
2. **Explore Architecture**: [`docs/ARCHITECTURE.md`](ARCHITECTURE.md)
3. **Check Roadmap**: [`docs/PLATFORM_ENGINEERING_ROADMAP.md`](PLATFORM_ENGINEERING_ROADMAP.md)

---

## ❓ Common Issues

### "API key not found"

**Solution:**
- Check `.env` file exists and has your API key
- Restart backend after changing `.env`
- Verify API key is correct

### "ChromaDB not initialized"

**Solution:**
- First run may take time to initialize
- Check logs for initialization progress
- Ensure `data/vector_db` directory is writable

### "Port already in use"

**Solution:**
- Change port in command: `--port 8001`
- Or stop existing service on that port

### "Module not found"

**Solution:**
- Ensure virtual environment is activated
- Run `pip install -r requirements.txt` again
- Check Python version: `python --version` (should be 3.12+)

---

## 🆘 Need Help?

- **Documentation**: Check [`docs/`](.) directory
- **GitHub Issues**: Report bugs or ask questions
- **Discussions**: Share ideas and get help

---

**Welcome to StillMe!** 🎉

Start exploring and see what StillMe can do. Remember: StillMe admits when it doesn't know - that's a feature, not a bug!

