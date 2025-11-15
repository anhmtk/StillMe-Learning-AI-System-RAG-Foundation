# Dashboard Features Explained

This document explains the purpose and usage of various dashboard features in StillMe.

---

## 1. Nested Learning Metrics

### Purpose
Nested Learning Metrics tracks a **tiered update frequency system** that reduces embedding costs by updating knowledge at different frequencies based on importance tiers.

### Why It Shows 0
The metrics will show 0 if:
1. **Nested Learning is disabled** - Requires `ENABLE_CONTINUUM_MEMORY=true` in backend environment variables
2. **No learning cycles have run yet** - Metrics are only updated when learning cycles execute
3. **No knowledge items have been assigned to tiers** - The system needs to process learning content first

### How to Enable
1. Set `ENABLE_CONTINUUM_MEMORY=true` in backend `.env` file
2. Restart/redeploy backend service
3. Run a learning cycle (either manually via "Run Learning Cycle" or wait for scheduled cycle)
4. Refresh the Nested Learning Metrics page

### What It Tracks
- **Current Cycle**: Number of learning cycles completed
- **Cost Reduction**: Percentage of embedding operations skipped (saved costs)
- **Total Operations**: Total embedding operations attempted
- **Skipped Operations**: Operations skipped due to tier-based update frequency
- **Tier Distribution**: Knowledge items distributed across L0, L1, L2, L3 tiers

### When Metrics Update
Metrics update automatically when:
- Learning cycles run (every 4 hours by default, or manually triggered)
- Knowledge items are processed and assigned to tiers
- Tier promotions/demotions occur

---

## 2. Validation Metrics

### Purpose
Validation Metrics monitors the **Validator Chain performance** to track how well StillMe reduces hallucinations and ensures response quality.

### Why It Shows "No validation data yet"
The message appears when:
1. **No chat messages have been sent yet** - Validation metrics are only recorded when you chat with StillMe
2. **Validators are enabled but no interactions occurred** - The system is ready but waiting for user interaction

### Important Note
**Both Sidebar Chat and Floating Widget record validation metrics!** The previous message was misleading. Both interfaces call the same API endpoint (`/api/chat/smart_router` or `/api/chat/rag`), which triggers the validation chain and records metrics.

### How to Generate Metrics
Simply **chat with StillMe** using either:
- Sidebar Chat (in the dashboard sidebar)
- Floating Widget (the floating chat panel)

Every message you send will:
1. Trigger the validation chain
2. Record validation results (passed/failed, reasons, overlap scores, confidence scores)
3. Update the metrics dashboard automatically

### What It Tracks
- **Total Validations**: Number of responses validated
- **Pass Rate**: Percentage of validations that passed
- **Passed/Failed Counts**: Breakdown of validation results
- **Evidence Overlap**: Average overlap score between response and RAG context
- **Reasons Histogram**: Breakdown of why validations passed or failed
- **Confidence Scores**: Distribution of AI confidence levels

---

## 3. Memory Health

### Purpose
Memory Health displays the **Continuum Memory System** status, showing how knowledge is organized into tiers (L0-L3) and tracked over time.

### Tier System
- **L0 (Session)**: Hot, newly fetched knowledge (TTL: hours-days)
- **L1 (Working)**: Validated knowledge with usage tracking (TTL: weeks)
- **L2 (Canonical)**: Standard knowledge with high confidence (TTL: months+)
- **L3 (Core)**: Immutable rules and standards (permanent)

### Why Audit Log Shows "No audit records available"
The audit log shows this message when:
1. **Continuum Memory is disabled** - Requires `ENABLE_CONTINUUM_MEMORY=true`
2. **No tier promotions/demotions have occurred yet** - Audit log only records when knowledge items move between tiers
3. **Backend API endpoint not implemented or returning empty data** - The `/api/v1/tiers/audit` endpoint may not have data yet

### Why Forgetting Trends Shows "Forgetting trends not available"
The forgetting trends show this message when:
1. **Continuum Memory is disabled** - Requires `ENABLE_CONTINUUM_MEMORY=true`
2. **No forgetting evaluations have been run yet** - The system needs to evaluate Recall@k degradation over time
3. **Backend API endpoint not implemented or returning empty data** - The `/api/v1/tiers/forgetting-trends` endpoint may not have data yet

### What It Tracks (When Enabled)
- **Tier Distribution**: Count of knowledge items in each tier
- **Promotion/Demotion**: Items moved between tiers (last 7 days)
- **Audit Log**: History of all tier movements with reasons
- **Forgetting Trends**: Recall@k degradation over time (measures how well StillMe remembers knowledge)

### How to Enable
1. Set `ENABLE_CONTINUUM_MEMORY=true` in backend `.env` file
2. Restart/redeploy backend service
3. Run learning cycles to populate tiers
4. Wait for tier promotions/demotions to occur (happens automatically based on surprise scores)

---

## 4. Learning Sessions

### Purpose
Learning Sessions allows you to **manually record learning interactions** for tracking and analysis. This is useful for:
- Testing how StillMe learns from specific prompts/responses
- Recording important conversations for later analysis
- Scoring responses to measure quality
- Training StillMe on specific patterns

### How It Works
1. **Enter a Prompt**: The question or input you want to test
2. **Enter a Response**: The expected or actual response from StillMe
3. **Select Model**: Which LLM model was used (deepseek-chat, ollama, openai)
4. **Record Session**: Saves the interaction to the database
5. **Score Response**: Evaluates the response quality (optional)

### Use Cases
- **Quality Testing**: Record test cases and score responses to track improvement
- **Pattern Learning**: Record specific conversation patterns you want StillMe to learn
- **Debugging**: Record problematic interactions for analysis
- **Training Data**: Build a dataset of high-quality interactions

### API Endpoints
- `POST /api/learning/sessions/run` - Record a learning session
- `POST /api/learning/score_response` - Score a response quality

### When to Use
- When testing new features or prompts
- When you want to track specific learning patterns
- When building a training dataset
- When debugging response quality issues

---

## Summary

| Feature | Requires Enable? | When Data Appears | Purpose |
|---------|-----------------|-------------------|---------|
| **Nested Learning Metrics** | `ENABLE_CONTINUUM_MEMORY=true` | After learning cycles run | Track cost reduction from tiered updates |
| **Validation Metrics** | `ENABLE_VALIDATORS=true` (default) | After chatting with StillMe | Monitor validation chain performance |
| **Memory Health** | `ENABLE_CONTINUUM_MEMORY=true` | After tier movements occur | Track knowledge organization and forgetting |
| **Learning Sessions** | Always available | After manual recording | Record and analyze learning interactions |

---

## Troubleshooting

### All Metrics Show 0 or Empty
1. **Check backend is running**: Ensure backend service is active
2. **Check environment variables**: Verify required flags are set
3. **Run a learning cycle**: Trigger manual learning cycle to generate data
4. **Chat with StillMe**: Send messages to generate validation metrics
5. **Check backend logs**: Look for errors in backend logs

### Validation Metrics Not Updating
- **Both sidebar and floating widget work** - The message was misleading
- Ensure you're actually sending messages (not just viewing the chat interface)
- Check that `ENABLE_VALIDATORS=true` is set
- Verify backend is processing requests (check logs)

### Memory Health Shows Empty
- Ensure `ENABLE_CONTINUUM_MEMORY=true` is set
- Run learning cycles to populate tiers
- Wait for tier promotions/demotions (happens automatically)
- Check that backend API endpoints are implemented and returning data

---

*Last Updated: 2025-01-14*

