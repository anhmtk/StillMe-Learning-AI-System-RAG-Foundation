# Task Status Report - Community Learning Integration

## ✅ COMPLETED TASKS

### 1. URGENT: Tích hợp approved proposals vào learning scheduler ✅ DONE

**Status:** ✅ **COMPLETED**

**Implementation:**
- ✅ Created `URLFetcher` service (`backend/services/url_fetcher.py`)
  - Fetches content from arbitrary URLs (RSS feeds or articles)
  - Auto-detects RSS vs article
  - Extracts text from HTML
  - Error handling and logging

- ✅ Added `get_approved_proposals_not_learned()` to `community_proposals.py`
  - Returns approved proposals that haven't been learned yet
  - Ordered by votes (highest first)

- ✅ Added `mark_proposal_as_learned()` to `community_proposals.py`
  - Marks proposal as learned after adding to RAG
  - Tracks learning cycle ID

- ✅ Integrated into learning cycle (`learning_router.py`)
  - Community proposals processed FIRST (priority)
  - Content fetched from proposal URLs
  - Added to RAG with proper metadata
  - Marked as learned after successful addition

**Files Modified:**
- `backend/services/url_fetcher.py` (NEW)
- `backend/services/community_proposals.py`
- `backend/api/routers/learning_router.py`

**Test Status:** ✅ Logic implemented, ready for integration testing

---

### 2. IMPLEMENTED: 70/30 Learning Allocation System ✅ DONE

**Status:** ✅ **COMPLETED** (Just fixed to be percentage-based)

**Implementation:**
- ✅ **Percentage-based allocation** (NOT hard limit)
  - Community: 30% of total available items
  - Automatic: 70% of total available items
  - Calculated dynamically based on actual items fetched

- ✅ **Priority system:**
  - Community proposals processed FIRST
  - Automatic sources processed SECOND
  - Quotas calculated after fetching all items

- ✅ **Dynamic allocation:**
  - If community has fewer items than 30%, automatic can use more
  - If community has more items than 30%, it's limited to 30%
  - Total items = community + automatic (no hard cap)

**Files Modified:**
- `backend/api/routers/learning_router.py`

**Test Status:** ⚠️ Test file created but has import issues (needs dependency setup)

---

## ⚠️ IN PROGRESS / PENDING TASKS

### 3. IMPORTANT: Làm vote threshold configurable/dynamic ⚠️ PENDING

**Status:** ⚠️ **NOT STARTED**

**Current State:**
- `MIN_VOTES_TO_LEARN = 10` (hardcoded in `backend/services/community_proposals.py`)
- Not configurable via environment variable
- Not dynamic based on community size

**What Needs to Be Done:**
1. Add environment variable: `COMMUNITY_MIN_VOTES` (default: 10)
2. Make it configurable in `community_proposals.py`
3. (Optional) Add dynamic threshold based on community size

**Effort:** Low (30 minutes)
**Priority:** IMPORTANT (but not blocking)

**Files to Modify:**
- `backend/services/community_proposals.py`

---

### 4. NICE TO HAVE: StillMe auto-proposal dựa trên knowledge gaps ❌ NOT STARTED

**Status:** ❌ **NOT IMPLEMENTED**

**Current State:**
- ✅ `SelfDiagnosisAgent` can detect knowledge gaps
- ✅ `SelfDiagnosisAgent` can suggest learning focus
- ❌ **NO code** that creates community proposals from knowledge gaps
- ❌ **NO integration** between self-diagnosis and community proposals

**What Needs to Be Done:**
1. Create `AIProposalGenerator` service
   - Detects knowledge gaps from chat queries
   - Searches for relevant sources (RSS feeds, articles)
   - Creates community proposals automatically
   - Marks proposals with `proposer_id: "stillme_ai"`

2. Integrate into chat flow
   - When confidence < 0.5 and no context
   - Detect knowledge gap
   - Generate proposal
   - Submit to community for voting

3. Community voting on AI proposals
   - AI proposals go through same voting process
   - Community can approve/reject StillMe's suggestions
   - Maintains community control

**Effort:** High (4-6 hours)
**Priority:** NICE TO HAVE (enhancement, not critical)

**Files to Create:**
- `backend/services/ai_proposal_generator.py` (NEW)

**Files to Modify:**
- `backend/api/routers/chat_router.py` or `learning_router.py`
- `backend/services/community_proposals.py` (add `proposer_id: "stillme_ai"` support)

---

## Summary

### ✅ Completed (2/4):
1. ✅ **URGENT: Tích hợp approved proposals** - DONE
2. ✅ **70/30 Allocation System** - DONE (just fixed to percentage-based)

### ⚠️ Pending (2/4):
3. ⚠️ **IMPORTANT: Vote threshold configurable** - NOT STARTED (30 min effort)
4. ❌ **NICE TO HAVE: StillMe auto-proposal** - NOT STARTED (4-6 hours effort)

---

## Next Steps

1. **Fix 70/30 logic** (DONE - changed to percentage-based)
2. **Test 70/30 allocation** (needs dependency setup for test)
3. **Implement vote threshold configurable** (30 min)
4. **Implement StillMe auto-proposal** (4-6 hours, future enhancement)

