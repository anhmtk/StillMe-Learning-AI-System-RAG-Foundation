# Testing StillMe's Self-Time Estimation Awareness

## Overview

This guide helps verify that StillMe:
1. **Detects time estimation queries** correctly
2. **Provides time estimates** based on historical performance data
3. **Shows self-awareness** about being AI and tracking its own performance
4. **Mentions its self-tracking capability** when appropriate

## Quick Test

### Automated Test Script

```bash
python scripts/test_self_time_estimation.py --backend-url stillme-backend-production.up.railway.app
```

This script tests 5 different queries and checks for:
- Time estimate presence
- Self-awareness indicators
- Historical data mentions
- AI identity statements

## Manual Testing

### Test 1: Direct Time Estimation Query

**Query:**
```
How long will it take to learn 100 articles?
```

**Expected Response Should Include:**
- ⏱️ Time Estimate section
- Mention of "historical performance" or "hiệu suất lịch sử"
- AI identity statement (e.g., "I'm an AI system that tracks...")
- Confidence level (e.g., "low confidence, 30%")
- Time range (e.g., "24-96 minutes")

### Test 2: Vietnamese Time Estimation Query

**Query:**
```
Bao lâu để học 100 bài viết?
```

**Expected Response Should Include:**
- ⏱️ Ước tính thời gian section
- Vietnamese AI identity statement
- Historical performance mention
- Time estimate in Vietnamese

### Test 3: Self-Tracking Awareness Query

**Query:**
```
Do you track your own execution time?
```

**Expected Response Should Include:**
- Direct answer about self-tracking capability
- Explanation of how StillMe tracks time
- Mention of learning from historical data
- AI identity (not claiming human-like experiences)

### Test 4: Validation Time Query

**Query:**
```
How long does validation take?
```

**Expected Response Should Include:**
- Time estimate for validation
- Based on historical validation data
- Self-aware statement about tracking

## What to Look For

### ✅ Good Signs

1. **Time Estimate Section**:
   - Clear ⏱️ emoji or "Time Estimate" header
   - Time range (e.g., "24-96 minutes")
   - Confidence level

2. **Self-Awareness**:
   - "I'm an AI system that tracks my own performance"
   - "Based on my historical performance"
   - "I estimate based on patterns I've learned"

3. **AI Identity**:
   - Explicitly states it's an AI system
   - Mentions statistical model or LLM
   - Doesn't claim human-like experiences

4. **Historical Data**:
   - Mentions "similar tasks" or "historical data"
   - Explains confidence based on data availability
   - Acknowledges when no historical data exists

### ❌ Red Flags

1. **Missing Time Estimate**:
   - Query is about time but no estimate provided
   - No ⏱️ section in response

2. **No Self-Awareness**:
   - Doesn't mention being AI
   - Doesn't explain how it estimates
   - Claims human-like intuition

3. **Anthropomorphization**:
   - "I feel like..."
   - "I experience..."
   - "I have a sense that..."

4. **Hallucinated Data**:
   - Makes up specific numbers without basis
   - Claims to have data it doesn't have
   - Overconfident without evidence

## Example Good Response

```
⏱️ **Time Estimate:**
Based on my historical performance, I estimate this will take 24-96 minutes 
(low confidence, 30%). No similar historical tasks found, using complexity-based 
estimate. I'm an AI system that tracks my own execution time to improve estimates 
over time. I estimate based on my historical performance data, similar to how 
humans estimate based on experience, but I'm a statistical model that learns from 
patterns.
```

## Troubleshooting

### Issue: No Time Estimate in Response

**Possible Causes:**
1. Intent detection failed (check logs)
2. Time estimation not integrated in chat endpoint
3. Response was cached before integration

**Solution:**
- Check backend logs for intent detection
- Clear cache: `POST /api/cache/clear?pattern=llm:response:*`
- Verify time estimation integration in `chat_router.py`

### Issue: No Self-Awareness Mentioned

**Possible Causes:**
1. `format_self_aware_response` not including AI identity
2. Response format doesn't include self-awareness section

**Solution:**
- Check `stillme_core/monitoring/self_tracking.py`
- Verify `format_self_aware_response` includes AI identity
- Check if `include_identity=True` is set

### Issue: Wrong Model Name Mentioned

**Possible Causes:**
1. Cached response with old model name
2. Foundational knowledge has wrong model name

**Solution:**
- Clear cache: `POST /api/cache/clear?pattern=llm:response:*`
- Update foundational knowledge: `python scripts/update_foundational_knowledge_model_name.py`
- Verify foundational knowledge in RAG database

## Success Criteria

A successful test should show:

1. ✅ **Time estimates are provided** for time-related queries
2. ✅ **Self-awareness is mentioned** in time estimation responses
3. ✅ **AI identity is clear** (not anthropomorphized)
4. ✅ **Historical data is referenced** when available
5. ✅ **Confidence levels are provided** with estimates

## Next Steps

After testing:
1. Review test results
2. Fix any issues found
3. Update documentation if needed
4. Consider adding more test cases

