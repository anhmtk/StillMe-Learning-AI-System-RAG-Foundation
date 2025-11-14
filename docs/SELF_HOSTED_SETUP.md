# StillMe Self-Hosted Setup Guide

## Overview

StillMe supports **100% self-hosted deployment**, allowing you to:
- Control your own data and infrastructure
- Choose any LLM provider (DeepSeek, OpenAI, Claude, Gemini, Ollama, Custom)
- Pay only for what you use
- Maintain complete privacy

## Quick Start

### 1. Clone Repository

```bash
git clone https://github.com/your-org/StillMe-Learning-AI-System-RAG-Foundation.git
cd StillMe-Learning-AI-System-RAG-Foundation
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure Environment Variables

Create `.env` file:

```bash
# LLM Provider (choose one or use request-level config)
DEEPSEEK_API_KEY=your_deepseek_key_here
# OR
OPENAI_API_KEY=your_openai_key_here
# OR
ANTHROPIC_API_KEY=your_claude_key_here
# OR
GOOGLE_API_KEY=your_gemini_key_here
# OR (for local Ollama)
OLLAMA_URL=http://localhost:11434

# StillMe API Key (for RAG injection authentication)
STILLME_API_KEY=your_stillme_api_key_here

# Optional: Vector DB path
VECTOR_DB_PATH=data/vector_db

# Optional: Enable validators
ENABLE_VALIDATORS=true
```

### 4. Start Backend

```bash
cd backend
uvicorn api.main:app --host 0.0.0.0 --port 8000
```

### 5. Start Dashboard (Optional)

```bash
streamlit run dashboard.py
```

## LLM Provider Configuration

### Option 1: Environment Variables (Global)

Set one of these in `.env`:
- `DEEPSEEK_API_KEY` - For DeepSeek
- `OPENAI_API_KEY` - For OpenAI
- `ANTHROPIC_API_KEY` - For Claude
- `GOOGLE_API_KEY` - For Gemini
- `OLLAMA_URL` - For local Ollama (default: `http://localhost:11434`)

### Option 2: Request-Level (Per Request)

Send LLM config in each chat request:

```json
{
  "message": "What is StillMe?",
  "llm_provider": "deepseek",
  "llm_api_key": "your_api_key_here",
  "llm_model_name": "deepseek-chat",
  "llm_api_url": null
}
```

**Supported Providers:**
- `deepseek` - DeepSeek API
- `openai` - OpenAI API
- `claude` - Anthropic Claude API
- `gemini` - Google Gemini API
- `ollama` - Local Ollama (no API key needed)
- `custom` - Custom OpenAI-compatible API

**Example Requests:**

#### DeepSeek
```json
{
  "message": "Hello",
  "llm_provider": "deepseek",
  "llm_api_key": "sk-...",
  "llm_model_name": "deepseek-chat"
}
```

#### OpenAI
```json
{
  "message": "Hello",
  "llm_provider": "openai",
  "llm_api_key": "sk-...",
  "llm_model_name": "gpt-4"
}
```

#### Claude
```json
{
  "message": "Hello",
  "llm_provider": "claude",
  "llm_api_key": "sk-ant-...",
  "llm_model_name": "claude-3-opus-20240229"
}
```

#### Gemini
```json
{
  "message": "Hello",
  "llm_provider": "gemini",
  "llm_api_key": "AIza...",
  "llm_model_name": "gemini-pro"
}
```

#### Ollama (Local)
```json
{
  "message": "Hello",
  "llm_provider": "ollama",
  "llm_api_url": "http://localhost:11434",
  "llm_model_name": "llama2"
}
```

#### Custom Provider
```json
{
  "message": "Hello",
  "llm_provider": "custom",
  "llm_api_key": "your_key",
  "llm_api_url": "https://your-api.com/v1/chat/completions",
  "llm_model_name": "your-model"
}
```

## RAG Injection Authentication

To add knowledge to RAG, you need API key authentication:

```bash
curl -X POST http://localhost:8000/api/rag/add_knowledge \
  -H "X-API-Key: your_stillme_api_key_here" \
  -H "Content-Type: application/json" \
  -d '{
    "content": "Your knowledge content here...",
    "source": "your-source",
    "content_type": "knowledge",
    "metadata": {"title": "Title"}
  }'
```

## Ethics Guard

StillMe includes built-in ethics guard that filters:
- Violence and self-harm content
- Hate speech
- Illegal content
- Spam/scam content

Content is automatically validated before being added to RAG.

## Deployment Options

### Local Development
```bash
# Backend
cd backend
uvicorn api.main:app --reload

# Dashboard
streamlit run dashboard.py
```

### Production (Railway/Render/Fly.io)

1. Set environment variables in your platform
2. Deploy backend
3. (Optional) Deploy dashboard separately

### Docker (Coming Soon)

```bash
docker build -t stillme .
docker run -p 8000:8000 -e DEEPSEEK_API_KEY=... stillme
```

## Cost Estimation

### Self-Hosted Costs:
- **Infrastructure**: $0 (if using free tier) or $5-20/month (VPS)
- **LLM API**: Pay per use (varies by provider)
  - DeepSeek: ~$0.14 per 1M tokens
  - OpenAI GPT-3.5: ~$0.50 per 1M tokens
  - Claude: ~$3 per 1M tokens
- **Vector DB**: Free (local ChromaDB) or $0-10/month (managed)

### Example Monthly Cost:
- 1000 requests/day × 30 days = 30,000 requests
- Average 500 tokens/request = 15M tokens/month
- DeepSeek: ~$2.10/month
- **Total: ~$2-25/month** (depending on provider and infrastructure)

## Troubleshooting

### "I need API keys to provide real responses"
- Check that you've set environment variables OR provided `llm_provider` + `llm_api_key` in request
- Verify API key is valid

### "Ollama API error"
- Make sure Ollama is running: `ollama serve`
- Check `OLLAMA_URL` is correct (default: `http://localhost:11434`)

### "Content failed ethics validation"
- Content contains blocked keywords/phrases
- Review content and remove inappropriate material

### "API key required" (RAG injection)
- Set `STILLME_API_KEY` in environment
- Include `X-API-Key` header in request

## Next Steps

1. **Add Foundational Knowledge**:
   ```bash
   python scripts/add_foundational_knowledge.py
   ```

2. **Configure RSS Feeds** (optional):
   - Edit `backend/services/rss_fetcher.py`
   - Add your RSS feed URLs

3. **Start Learning Cycles**:
   - StillMe automatically learns every 4 hours
   - Or trigger manually via API

## Support

- GitHub Issues: [Link]
- Documentation: [Link]
- Community: [Link]

