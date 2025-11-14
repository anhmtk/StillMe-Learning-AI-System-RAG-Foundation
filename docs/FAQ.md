# ❓ Frequently Asked Questions (FAQ)

Common questions about StillMe and their answers.

## 🌟 General Questions

### What is StillMe?

StillMe is a **Learning AI system** that continuously learns from multiple sources (RSS feeds, arXiv, Wikipedia, etc.) and provides context-aware responses using RAG (Retrieval-Augmented Generation). StillMe's core philosophy is **Intellectual Humility** - admitting when it doesn't know.

### How is StillMe different from ChatGPT or other AIs?

**Key Differences:**
1. **RAG Foundation**: StillMe searches its internal knowledge base before answering
2. **Validation Chain**: Multiple validators ensure response quality and reduce hallucinations
3. **Intellectual Humility**: StillMe admits when it doesn't know (doesn't make things up)
4. **Transparency**: StillMe shows citations and validation results
5. **Continuous Learning**: StillMe learns from new sources every 4 hours
6. **100% Open Source**: Full transparency, community-driven

### Is StillMe free to use?

StillMe is **100% open source** (MIT License). However, you need to provide your own LLM API keys (DeepSeek, OpenAI, Claude, etc.) for the AI responses. StillMe itself is free, but LLM API calls may have costs depending on your provider.

### Can I use StillMe without API keys?

No. StillMe needs an LLM provider to generate responses. You can use:
- **DeepSeek** (affordable)
- **OpenAI** (GPT models)
- **Claude** (Anthropic)
- **Gemini** (Google)
- **Ollama** (local, free but requires setup)

---

## 🔧 Technical Questions

### How does RAG work in StillMe?

1. **User asks a question**
2. **StillMe searches** its ChromaDB vector database for relevant context
3. **StillMe retrieves** top-k most relevant documents
4. **StillMe generates** response using LLM with retrieved context
5. **StillMe validates** response with Validation Chain
6. **StillMe returns** answer with citations and confidence score

### What is the Validation Chain?

Validation Chain is a series of validators that check StillMe's responses:
- **Citation Required**: Ensures StillMe cites sources when available
- **Evidence Overlap**: Checks if answer matches retrieved context
- **Language Match**: Ensures StillMe responds in your language
- **Confidence Score**: Indicates how certain StillMe is
- **Ethics Validation**: Ensures responses are ethical

### How accurate is StillMe?

StillMe provides **confidence scores** (0.0-1.0) to indicate accuracy:
- **0.8-1.0**: High confidence, reliable
- **0.5-0.8**: Medium confidence, verify with sources
- **0.0-0.5**: Low confidence, StillMe may not have enough information

**Important**: No AI is 100% accurate. Always verify critical information, especially for important decisions.

### Can StillMe search the internet?

**No.** StillMe can only search its **internal knowledge base** (ChromaDB), which contains documents learned from:
- RSS feeds (Nature, Science, Hacker News, etc.)
- arXiv (AI/ML papers)
- CrossRef (academic papers)
- Wikipedia (general knowledge)
- Other sources (updated every 4 hours)

StillMe **cannot** access live websites or perform real-time web search.

### What sources does StillMe learn from?

**Current Sources:**
- RSS Feeds: Nature, Science, Hacker News, Tech Policy blogs, Academic blogs
- arXiv: AI/ML papers (cs.AI, cs.LG)
- CrossRef: Academic papers
- Wikipedia: General knowledge
- Papers with Code: Recent papers with implementations
- Conference Proceedings: NeurIPS, ICML, ACL, ICLR
- Stanford Encyclopedia of Philosophy: Philosophy entries

**See**: [`docs/PLATFORM_ENGINEERING_ROADMAP.md`](PLATFORM_ENGINEERING_ROADMAP.md) for full list.

---

## 🎯 Usage Questions

### How do I get the best results from StillMe?

**Tips:**
1. **Ask clear questions**: Be specific, avoid vague queries
2. **Check citations**: Verify information using provided sources
3. **Understand confidence scores**: Higher = more reliable
4. **Use your language**: StillMe supports 14+ languages
5. **Rephrase if needed**: If StillMe says "I don't know", try rephrasing

### Why does StillMe say "I don't know"?

**This is a feature, not a bug!** StillMe's core value is **Intellectual Humility** - admitting when it doesn't know rather than making things up.

**Reasons StillMe might say "I don't know":**
- Information not in StillMe's knowledge base
- Question too vague or unclear
- StillMe doesn't have enough context
- Topic outside StillMe's learning scope

**What to do:**
- Rephrase your question
- Ask about a different aspect
- Check if StillMe learns from sources relevant to your question

### Can I trust StillMe's answers?

**Trust but verify:**
- Check **confidence scores** (higher = more reliable)
- Verify **citations** - check sources StillMe used
- Cross-reference with other sources for critical information
- Remember: No AI is 100% accurate

**StillMe is designed to:**
- Admit when uncertain (Intellectual Humility)
- Provide citations for transparency
- Validate responses for quality
- Reduce hallucinations through Validation Chain

### How do citations work?

StillMe provides citations `[1]`, `[2]`, `[3]` in responses:
- These refer to sources in StillMe's knowledge base
- Click citations to see full source details
- Citations indicate StillMe found relevant context
- If no citations: StillMe may not have found relevant sources

---

## 🚀 Deployment Questions

### Can I self-host StillMe?

**Yes!** StillMe is 100% open source and can be self-hosted.

**See**: [`docs/SELF_HOSTED_SETUP.md`](SELF_HOSTED_SETUP.md) for detailed guide.

**Benefits:**
- Full control over data
- Use your own LLM API keys
- Customize StillMe for your needs
- No dependency on external services

### What are the system requirements?

**Minimum:**
- Python 3.12+
- 2GB RAM
- 5GB disk space (for vector DB and models)

**Recommended:**
- Python 3.12+
- 4GB+ RAM
- 10GB+ disk space
- GPU (optional, for faster embeddings)

### Can I use StillMe with my own LLM?

**Yes!** StillMe supports:
- DeepSeek (default)
- OpenAI (GPT models)
- Claude (Anthropic)
- Gemini (Google)
- Ollama (local)
- Custom providers (OpenAI-compatible APIs)

**See**: [`docs/SELF_HOSTED_SETUP.md`](SELF_HOSTED_SETUP.md) for configuration.

---

## 🤝 Contributing Questions

### How can I contribute?

**Many ways to contribute:**
- **Code**: Fix bugs, add features, improve architecture
- **Documentation**: Improve guides, write tutorials
- **Testing**: Test StillMe, report bugs, suggest improvements
- **Community**: Help others, answer questions, share ideas

**See**: [`CONTRIBUTING.md`](../CONTRIBUTING.md) for detailed guide.

### Do I need to be a developer to contribute?

**No!** StillMe welcomes contributions from:
- Developers (all levels)
- Designers
- Writers
- Testers
- Community builders

**Non-technical contributions:**
- Documentation
- UI/UX design
- Testing and feedback
- Community building
- Content creation

### Can I use AI to help contribute?

**Yes!** StillMe was built with AI assistance. We encourage using AI tools to:
- Understand the codebase
- Generate code (then review with human judgment)
- Write documentation
- Create tests

**See**: [`CONTRIBUTING.md`](../CONTRIBUTING.md) for AI-assisted contribution guide.

---

## 🔒 Privacy & Security

### Is my data private?

**Self-hosted**: Your data stays on your server - fully private.

**Shared deployment**: Check the deployment's privacy policy. StillMe itself is open source, so you can audit the code.

### Does StillMe store my conversations?

StillMe can learn from conversations **with your permission**:
- You can enable/disable conversation learning
- StillMe asks for permission before learning
- You can review what StillMe learned

**See**: API documentation for conversation learning endpoints.

### Is StillMe secure?

StillMe follows security best practices:
- API key authentication for sensitive endpoints
- Rate limiting to prevent abuse
- Ethics validation to prevent malicious content
- Open source for transparency and auditability

**See**: [`docs/SECURITY.md`](SECURITY.md) for details.

---

## 📊 Performance Questions

### How fast is StillMe?

**Typical response time:**
- RAG retrieval: ~0.5-1.0s
- LLM inference: ~2-5s (depends on provider)
- Validation: ~0.3-1.0s
- **Total: ~3-7s** (varies by provider and query complexity)

**Optimizations:**
- Parallel RAG retrieval (Tier 1 optimization)
- Embedding cache (Tier 1 optimization)
- Streaming response (Tier 2 optimization - reduces perceived latency)

### Can StillMe handle high traffic?

**Current limitations:**
- Single-threaded scheduler
- SQLite database (PostgreSQL migration planned)
- ChromaDB memory-based (persistence planned)

**For production scale:**
- Use PostgreSQL (migration in roadmap)
- Deploy with load balancer
- Use distributed task queue
- Scale horizontally

**See**: [`docs/PLATFORM_ENGINEERING_ROADMAP.md`](PLATFORM_ENGINEERING_ROADMAP.md) for scaling plans.

---

## 🐛 Troubleshooting

### StillMe doesn't understand my question

**Solutions:**
- Rephrase more clearly
- Break complex questions into smaller parts
- Check if StillMe supports your language
- Try asking in English first

### StillMe gives low confidence

**What to do:**
- Check citations - are sources relevant?
- Rephrase your question
- Ask about a different aspect
- StillMe may not have enough information

### StillMe responds in wrong language

**Solutions:**
- StillMe should auto-detect, but if it doesn't:
- Explicitly request: "Please respond in [your language]"
- Report the issue - we want to fix this

### API returns errors

**Common issues:**
- Missing API key: Check `.env` file
- Invalid API key: Verify key is correct
- Rate limiting: Wait and retry
- Service unavailable: Check deployment status

---

## 📚 More Questions?

- **Documentation**: Check [`docs/`](.) directory
- **GitHub Discussions**: Ask questions, share ideas
- **Issues**: Report bugs or request features
- **Contributing Guide**: [`CONTRIBUTING.md`](../CONTRIBUTING.md)

---

**StillMe** - *Learning AI system with RAG foundation* 🤖✨

