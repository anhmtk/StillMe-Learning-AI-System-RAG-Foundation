# 📖 StillMe User Guide

Welcome to StillMe! This guide will help you get started and make the most of StillMe's capabilities.

## 🌟 What is StillMe?

StillMe is a **Learning AI system** that:
- Continuously learns from multiple sources (RSS feeds, arXiv, Wikipedia, etc.)
- Provides context-aware responses using RAG (Retrieval-Augmented Generation)
- Validates responses to reduce hallucinations and ensure accuracy
- Admits when it doesn't know (Intellectual Humility)

**Core Philosophy:** *"In the AI era, true value lies not in what AI can do, but in what AI chooses NOT to do."*

---

## 🚀 Quick Start

### Option 1: Use StillMe Dashboard (Easiest)

1. **Access the Dashboard:**
   - Local: http://localhost:8501
   - Production: https://stillme-dashboard.up.railway.app (if deployed)

2. **Start Chatting:**
   - Type your question in the chat interface
   - StillMe will search its knowledge base and provide context-aware answers
   - Check citations to see sources StillMe used

3. **Explore Features:**
   - View RAG retrieval results
   - See validation chain results
   - Monitor learning metrics

### Option 2: Use API Directly

**Simple Chat Request:**
```bash
curl -X POST https://stillme-backend-production.up.railway.app/api/chat/rag \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What is RAG?",
    "use_rag": true,
    "context_limit": 3
  }'
```

**Response:**
```json
{
  "response": "RAG (Retrieval-Augmented Generation) is...",
  "confidence_score": 0.85,
  "citations": ["[1]", "[2]"],
  "sources": [...]
}
```

---

## 💡 How to Use StillMe Effectively

### 1. Ask Clear Questions

**Good:**
- "What is the difference between RAG and fine-tuning?"
- "Explain how StillMe's validation chain works"
- "What sources does StillMe learn from?"

**Less Effective:**
- "tell me stuff" (too vague)
- "ai" (too broad)

### 2. Use Citations

StillMe provides citations `[1]`, `[2]`, `[3]` in responses. These refer to sources in StillMe's knowledge base:
- Click on citations to see source details
- Verify information by checking sources
- Citations indicate StillMe found relevant context

### 3. Understand Confidence Scores

StillMe provides confidence scores (0.0-1.0):
- **0.8-1.0**: High confidence, reliable answer
- **0.5-0.8**: Medium confidence, verify with sources
- **0.0-0.5**: Low confidence, StillMe may not have enough information

**What to do:**
- High confidence: Trust the answer, but still verify if critical
- Medium confidence: Check citations, verify sources
- Low confidence: Ask for clarification or rephrase your question

### 4. Multi-Language Support

StillMe supports multiple languages:
- **Vietnamese (Tiếng Việt)**
- **English**
- **Chinese (中文)**
- **French (Français)**
- **Spanish (Español)**
- **German (Deutsch)**
- **Japanese (日本語)**
- **Korean (한국어)**
- **Arabic (العربية)**
- **Russian (Русский)**
- And more...

**How to use:**
- Ask questions in your preferred language
- StillMe will respond in the same language
- No need to specify language - StillMe detects automatically

### 5. Check Validation Results

StillMe uses a Validation Chain to ensure quality:
- **Citation Required**: Ensures StillMe cites sources when available
- **Evidence Overlap**: Checks if answer matches retrieved context
- **Language Match**: Ensures StillMe responds in your language
- **Confidence Score**: Indicates how certain StillMe is
- **Ethics Validation**: Ensures responses are ethical

**What this means:**
- If validation passes: High-quality, reliable answer
- If validation fails: StillMe may use fallback or ask for clarification

---

## 🎯 Use Cases

### 1. Research & Learning

**Example:**
```
You: "What are the latest developments in RAG systems?"

StillMe: [Provides answer with citations from recent papers]
```

**Best for:**
- Understanding complex topics
- Getting up-to-date information
- Learning from multiple sources

### 2. Technical Questions

**Example:**
```
You: "How does StillMe's validation chain work?"

StillMe: [Explains validation chain with technical details]
```

**Best for:**
- Technical documentation
- Architecture questions
- Implementation details

### 3. Multi-Language Communication

**Example:**
```
You: "Giải thích RAG là gì bằng tiếng Việt"

StillMe: [Responds in Vietnamese with detailed explanation]
```

**Best for:**
- Non-English speakers
- Learning in your native language
- Cross-cultural communication

### 4. Fact-Checking

**Example:**
```
You: "Is it true that RAG reduces hallucinations?"

StillMe: [Provides answer with citations and confidence score]
```

**Best for:**
- Verifying information
- Understanding claims
- Getting reliable sources

---

## ⚠️ Limitations & What StillMe Can't Do

### StillMe CAN:
- ✅ Search its internal knowledge base (RAG)
- ✅ Provide context-aware answers
- ✅ Cite sources from its knowledge base
- ✅ Admit when it doesn't know
- ✅ Validate responses for quality

### StillMe CANNOT:
- ❌ Search the internet in real-time
- ❌ Access live websites
- ❌ Provide information not in its knowledge base
- ❌ Guarantee 100% accuracy (no AI can)
- ❌ Replace human judgment for critical decisions

### What This Means:

**If StillMe says "I don't know":**
- StillMe doesn't have information in its knowledge base
- This is a feature, not a bug - StillMe admits limitations
- Try rephrasing your question or asking about a different topic

**If StillMe provides low confidence:**
- StillMe found some information but isn't certain
- Check citations to verify
- Consider asking for clarification

---

## 🔍 Understanding StillMe's Responses

### Response Structure

**Typical Response:**
```
[Answer text with citations [1], [2]]

Sources:
[1] Source name - Brief description
[2] Source name - Brief description

Confidence: 0.85
Validation: Passed
```

### Citation Format

- `[1]`, `[2]`, `[3]` = References to sources in StillMe's knowledge base
- Click citations to see full source details
- Citations indicate StillMe found relevant context

### Confidence Scores

- **0.9-1.0**: Very high confidence
- **0.7-0.9**: High confidence
- **0.5-0.7**: Medium confidence
- **0.3-0.5**: Low confidence
- **0.0-0.3**: Very low confidence

---

## 🛠️ Advanced Usage

### Custom LLM Provider

StillMe supports multiple LLM providers:
- DeepSeek (default)
- OpenAI
- Claude (Anthropic)
- Gemini (Google)
- Ollama (local)
- Custom providers

**How to use:**
```json
{
  "message": "Your question",
  "llm_provider": "openai",
  "llm_api_key": "your-api-key",
  "llm_model_name": "gpt-4"
}
```

### Self-Hosted Deployment

For self-hosted deployments:
1. Set up your own backend
2. Configure your LLM provider
3. Use your own API keys
4. See [`docs/SELF_HOSTED_SETUP.md`](SELF_HOSTED_SETUP.md) for details

---

## ❓ Troubleshooting

### StillMe doesn't understand my question

**Solutions:**
- Rephrase your question more clearly
- Break complex questions into smaller parts
- Check if StillMe supports your language
- Try asking in English first, then your language

### StillMe gives low confidence

**What to do:**
- Check citations - are sources relevant?
- Rephrase your question
- Ask about a different aspect of the topic
- StillMe may not have enough information in its knowledge base

### StillMe responds in wrong language

**Solutions:**
- StillMe should auto-detect language, but if it doesn't:
- Explicitly request: "Please respond in [your language]"
- Report the issue - this is a bug we want to fix

### StillMe says "I don't know"

**This is normal:**
- StillMe admits when it doesn't know (Intellectual Humility)
- Try rephrasing or asking about a different topic
- StillMe's knowledge base may not have information on this topic

---

## 📚 Learn More

- **Architecture**: See [`docs/ARCHITECTURE.md`](ARCHITECTURE.md)
- **Philosophy**: See [`docs/PHILOSOPHY.md`](PHILOSOPHY.md)
- **API Reference**: See [`docs/API_DOCUMENTATION.md`](API_DOCUMENTATION.md)
- **Contributing**: See [`CONTRIBUTING.md`](../CONTRIBUTING.md)

---

## 🤝 Getting Help

- **GitHub Discussions**: Ask questions, share ideas
- **Issues**: Report bugs or request features
- **Documentation**: Check docs for detailed information

---

**StillMe** - *Learning AI system with RAG foundation* 🤖✨

