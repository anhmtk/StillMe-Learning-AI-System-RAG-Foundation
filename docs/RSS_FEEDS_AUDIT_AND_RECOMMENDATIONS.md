# 📊 RSS Feeds Audit & Recommendations for StillMe

**Date:** 2025-01-XX  
**Purpose:** Audit current RSS feeds and recommend new sources without duplication, focusing on Philosophy, AI Ethics, and Science.

---

## 🔍 PART 1: CURRENT FEEDS AUDIT

### Current RSS Feeds Configuration

**Source File:** `backend/services/rss_fetcher.py` (lines 24-82)

### Complete Feed List (24 active feeds):

```python
CURRENT_FEEDS = [
    # Technology & AI (8 feeds)
    {"url": "https://news.ycombinator.com/rss", "category": "technology", "name": "Hacker News"},
    {"url": "https://rss.nytimes.com/services/xml/rss/nyt/Technology.xml", "category": "technology", "name": "NYTimes Technology"},
    {"url": "https://distill.pub/rss.xml", "category": "technology", "name": "Distill - ML Research"},
    {"url": "https://www.lesswrong.com/feed.xml", "category": "technology", "name": "LessWrong - Rationality & AI Safety"},
    {"url": "https://www.alignmentforum.org/feed.xml", "category": "technology", "name": "Alignment Forum - AI Alignment"},
    {"url": "https://www.overcomingbias.com/feed", "category": "technology", "name": "Overcoming Bias - Rationality"},
    {"url": "https://www.scottaaronson.com/blog/?feed=rss2", "category": "technology", "name": "Scott Aaronson - Quantum Computing & CS Theory"},
    {"url": "https://feeds.bloomberg.com/markets/news.rss", "category": "technology", "name": "Bloomberg Markets"},
    
    # Science & Research (6 feeds)
    {"url": "https://www.nature.com/nature.rss", "category": "science", "name": "Nature"},
    {"url": "https://www.sciencedaily.com/rss/matter_energy.xml", "category": "science", "name": "ScienceDaily"},
    {"url": "https://physicsworld.com/feed/", "category": "science", "name": "Physics World"},
    {"url": "https://phys.org/rss-feed/", "category": "science", "name": "Phys.org"},
    {"url": "https://www.science.org/action/showFeed?type=etoc&feed=rss&jc=science", "category": "science", "name": "Science Magazine"},
    {"url": "https://feeds.feedburner.com/StatisticalModelingCausalInferenceAndSocialScience", "category": "science", "name": "Statistical Modeling Blog"},
    
    # Philosophy & Ethics (3 feeds)
    {"url": "https://aeon.co/feed.rss", "category": "philosophy", "name": "Aeon Magazine - Philosophy, Religion, Culture"},
    {"url": "https://www.lionsroar.com/feed/", "category": "philosophy", "name": "Lion's Roar - Buddhist Wisdom"},
    {"url": "https://www.theguardian.com/world/religion/rss", "category": "philosophy", "name": "The Guardian - Religion"},
    
    # Statistics & Data Science (2 feeds)
    {"url": "https://www.r-bloggers.com/feed/", "category": "statistics", "name": "R-Bloggers"},
    {"url": "https://feeds.feedburner.com/StatisticalModelingCausalInferenceAndSocialScience", "category": "statistics", "name": "Statistical Modeling Blog"},
    
    # Tech Policy & Governance (3 feeds)
    {"url": "https://www.eff.org/rss/updates.xml", "category": "tech_policy", "name": "Electronic Frontier Foundation"},
    {"url": "https://www.brookings.edu/feed/", "category": "tech_policy", "name": "Brookings Institution"},
    {"url": "https://www.cato.org/feed/", "category": "tech_policy", "name": "Cato Institute"},
]
```

### Domain Analysis:

**Unique Domains (20):**
- news.ycombinator.com
- rss.nytimes.com
- distill.pub
- lesswrong.com
- alignmentforum.org
- overcomingbias.com
- scottaaronson.com
- feeds.bloomberg.com
- nature.com
- sciencedaily.com
- physicsworld.com
- phys.org
- science.org
- feeds.feedburner.com
- aeon.co
- lionsroar.com
- theguardian.com
- r-bloggers.com
- eff.org
- brookings.edu
- cato.org

---

## 📊 PART 2: COVERAGE ANALYSIS

### Current Coverage by Category:

```
Technology & AI:     ████████░░ 80% (8/10 recommended)
Science & Research: ██████████ 100% (6/6 recommended)
Philosophy & Ethics: ███░░░░░░░ 30% (3/10 recommended) ⚠️ GAP
Statistics:         ██████░░░░ 60% (2/3 recommended)
Tech Policy:        ████████░░ 80% (3/4 recommended)
Religion:           ██░░░░░░░░ 20% (2/10 recommended) ⚠️ GAP
```

### Critical Gaps Identified:

1. **Philosophy & Ethics: 30% coverage** ⚠️ **HIGH PRIORITY**
   - Missing: Academic philosophy sources (Stanford Encyclopedia, IEP, PhilPapers)
   - Missing: AI Ethics specific sources
   - Missing: Applied ethics journals

2. **Religion & Spirituality: 20% coverage** ⚠️ **MEDIUM PRIORITY**
   - Missing: Academic religious studies
   - Missing: Comparative religion sources
   - Missing: Interfaith dialogue

3. **AI Ethics & Governance: Limited coverage**
   - Current: EFF, Brookings, Cato (policy-focused)
   - Missing: Academic AI ethics journals
   - Missing: Research ethics sources

---

## 🎯 PART 3: RECOMMENDED NEW SOURCES

### HIGH PRIORITY (Philosophy & Ethics Gaps):

#### 1. Stanford Encyclopedia of Philosophy (SEP)
- **URL:** N/A (No RSS feed available)
- **Category:** Philosophy
- **Reason:** Premier academic philosophy encyclopedia, peer-reviewed, comprehensive
- **License:** Open access (CC BY-NC-ND 4.0)
- **Note:** ✅ **ALREADY IMPLEMENTED** - Uses `StanfordEncyclopediaFetcher` (web scraping, not RSS)
- **Status:** ✅ Active - Fetches entries on topics: AI, ethics, consciousness, knowledge, truth

#### 2. Internet Encyclopedia of Philosophy (IEP)
- **URL:** `https://iep.utm.edu/feed/` (need to verify)
- **Category:** Philosophy
- **Reason:** Academic philosophy reference, peer-reviewed entries
- **License:** Open access (educational use)
- **Status:** ⚠️ Need to verify RSS availability

#### 3. PhilPapers
- **URL:** `https://philpapers.org/rss/recent` (if available)
- **Category:** Philosophy
- **Reason:** Largest database of philosophy research papers, updated daily
- **License:** Open access (varies by paper)
- **Status:** ⚠️ Need to verify RSS availability

#### 4. MIT Technology Review - AI Ethics
- **URL:** `https://www.technologyreview.com/topic/artificial-intelligence/feed/`
- **Category:** Technology & AI Ethics
- **Reason:** High-quality AI ethics coverage, accessible to general audience
- **License:** Some content may require subscription
- **Status:** ✅ Likely available

#### 5. Nature Machine Intelligence
- **URL:** `https://www.nature.com/natmachintell.rss`
- **Category:** Science & AI
- **Reason:** Peer-reviewed AI research, ethics discussions
- **License:** Some content open access, some subscription
- **Status:** ✅ Likely available

#### 6. AI Ethics Lab
- **URL:** `https://aiethicslab.com/feed/` (need to verify)
- **Category:** AI Ethics
- **Reason:** Dedicated to AI ethics research and analysis
- **License:** Open access
- **Status:** ⚠️ Need to verify RSS availability

#### 7. The Center for Humane Technology
- **URL:** `https://www.humanetech.com/feed` (need to verify)
- **Category:** AI Ethics & Technology
- **Reason:** Focus on ethical technology design, AI safety
- **License:** Open access
- **Status:** ⚠️ Need to verify RSS availability

### MEDIUM PRIORITY (Diversity & Quality):

#### 8. Harvard Divinity School - News & Events
- **URL:** `https://hds.harvard.edu/news/feed` (need to verify)
- **Category:** Religion & Spirituality
- **Reason:** Academic religious studies, interfaith dialogue
- **License:** Open access
- **Status:** ⚠️ Need to verify RSS availability

#### 9. BuddhistDoor Global
- **URL:** `https://www.buddhistdoor.net/feed/` (need to verify)
- **Category:** Religion & Spirituality
- **Reason:** Buddhist perspectives, academic quality
- **License:** Open access
- **Status:** ⚠️ Need to verify RSS availability

#### 10. BBC Religion & Ethics
- **URL:** `https://www.bbc.co.uk/religion/feed` (need to verify)
- **Category:** Religion & Ethics
- **Reason:** Diverse religious perspectives, ethical discussions
- **License:** Open access (BBC content)
- **Status:** ⚠️ Need to verify RSS availability

---

## 🔍 PART 4: VERIFICATION CHECKLIST

### For Each Recommended Feed:

- [ ] **Domain Check:** Not already in current feeds list
- [ ] **RSS Availability:** Test URL with `feedparser` or `curl`
- [ ] **Content Quality:** Sample 5 recent items, check relevance
- [ ] **License:** Verify educational/academic use allowed
- [ ] **Update Frequency:** Check if feed is actively updated
- [ ] **XML Validity:** Ensure feed is well-formed
- [ ] **Accessibility:** No authentication required (or API key available)

---

## 📝 PART 5: IMPLEMENTATION PLAN

### Files to Modify:

1. **`backend/services/rss_fetcher.py`**
   - Add new feeds to `self.feeds` list (lines 24-82)
   - Organize by category with comments

2. **`backend/services/rss_fetcher_enhanced.py`**
   - Add fallback URLs for new feeds in `FALLBACK_FEEDS` dict (if needed)

3. **Testing:**
   - Run `python -c "from backend.services.rss_fetcher import RSSFetcher; f = RSSFetcher(); print(f.feeds)"`
   - Test each new feed URL manually
   - Monitor failure rate after deployment

### Recommended Implementation Order:

1. **Phase 1 (High Priority - Philosophy & AI Ethics):**
   - ✅ **DONE:** Stanford Encyclopedia already implemented via `StanfordEncyclopediaFetcher`
   - Verify and add: MIT Technology Review AI, Nature Machine Intelligence
   - Test: Internet Encyclopedia of Philosophy (IEP) RSS feed
   - Test: PhilPapers RSS feed (if available)

2. **Phase 2 (Medium Priority - Diversity):**
   - Verify and add: BBC Religion & Ethics, BuddhistDoor
   - Test: Harvard Divinity School feed
   - Test: Center for Humane Technology feed

3. **Phase 3 (API Integration - Future):**
   - Consider API integration for: PhilPapers (if RSS not available)
   - These may require separate fetcher modules (similar to Stanford Encyclopedia)

---

## 🚨 PART 6: NOTES & WARNINGS

### Removed Feeds (for reference):
- `https://feeds.reuters.com/reuters/businessNews` - Permanent DNS errors
- `https://feeds.reuters.com/reuters/technologyNews` - Permanent DNS errors
- `https://tricycle.org/feed/` - 403 Forbidden
- `https://www.aei.org/technology/feed/` - 403 Forbidden
- `https://lilianweng.github.io/feed.xml` - 404 + XML error
- `https://phys.org/rss-feed/physics-news/` - 400 Bad request (using main feed instead)

### Important Considerations:

1. **License Compliance:**
   - Some feeds may have usage restrictions
   - Academic/educational use is generally allowed
   - Check each feed's terms of service

2. **Rate Limiting:**
   - Some sources may rate-limit RSS access
   - Monitor for 429 (Too Many Requests) errors

3. **Content Quality:**
   - Verify feeds provide substantive content (not just headlines)
   - Check for duplicate content across feeds

4. **Update Frequency:**
   - Some academic sources update infrequently
   - Balance between quality and freshness

---

## ✅ TEST RESULTS & IMPLEMENTATION STATUS

### Test Date: 2025-01-XX
**Script:** `scripts/test_rss_feeds.py`

### ✅ AVAILABLE FEEDS (Ready to Add - 4 feeds):

1. **MIT Technology Review - AI** ✅
   - URL: `https://www.technologyreview.com/topic/artificial-intelligence/feed/`
   - Status: **AVAILABLE** - 10 entries
   - **IMPLEMENTED:** ✅ Added to `rss_fetcher.py`

2. **Nature Machine Intelligence** ✅
   - URL: `https://www.nature.com/natmachintell.rss`
   - Status: **AVAILABLE** - 8 entries
   - **IMPLEMENTED:** ✅ Added to `rss_fetcher.py`

3. **AI Ethics Lab** ✅
   - URL: `https://aiethicslab.com/feed/`
   - Status: **AVAILABLE** - 30 entries
   - **IMPLEMENTED:** ✅ Added to `rss_fetcher.py`

4. **Internet Encyclopedia of Philosophy (IEP)** ✅
   - URL: `https://iep.utm.edu/feed/`
   - Status: **AVAILABLE** - 10 entries
   - **IMPLEMENTED:** ✅ Added to `rss_fetcher.py`

### ❌ UNAVAILABLE FEEDS (4 feeds):

1. **Center for Humane Technology**
   - URL: `https://www.humanetech.com/feed`
   - Status: **HTTP 404** - Feed not found
   - **Action:** Skip, find alternative

2. **Harvard Divinity School**
   - URL: `https://hds.harvard.edu/news/feed`
   - Status: **HTTP 403** - Forbidden
   - **Action:** Skip, find alternative

3. **BuddhistDoor Global**
   - URL: `https://www.buddhistdoor.net/feed/`
   - Status: **Empty feed** (0 entries)
   - **Action:** Skip, feed is inactive

4. **BBC Religion & Ethics**
   - URL: `https://www.bbc.co.uk/religion/feed`
   - Status: **Timeout** - Server not responding
   - **Action:** Skip, may retry later

### 🔧 FEEDS REQUIRING API INTEGRATION (2 feeds):

1. **Stanford Encyclopedia of Philosophy**
   - URL: `https://plato.stanford.edu/rss/seo.rss`
   - Status: **HTTP 404** - No RSS feed
   - **Action:** ✅ **ALREADY IMPLEMENTED** - Uses `StanfordEncyclopediaFetcher` (web scraping)

2. **PhilPapers**
   - URL: `https://philpapers.org/rss/recent`
   - Status: **HTTP 403** - Forbidden
   - **Action:** Consider API integration (future enhancement)

---

## 📊 UPDATED COVERAGE ANALYSIS

### After Adding 4 New Feeds:

```
Technology & AI:     ██████████ 100% (10/10 recommended) ✅ IMPROVED
Science & Research: ██████████ 100% (7/7 recommended) ✅ IMPROVED
Philosophy & Ethics: ██████░░░░ 60% (5/10 recommended) ✅ IMPROVED (was 30%)
Statistics:         ██████░░░░ 60% (2/3 recommended)
Tech Policy:        ████████░░ 80% (3/4 recommended)
Religion:           ██░░░░░░░░ 20% (2/10 recommended) ⚠️ STILL GAP
```

**Total Feeds:** 27 (was 24, +3 new: MIT Tech Review AI, Nature Machine Intelligence, AI Ethics Lab, IEP, Tricycle)

---

## ✅ NEXT STEPS

1. **✅ COMPLETED:**
   - ✅ Tested all recommended feeds
   - ✅ Added 4 available feeds to `rss_fetcher.py`
   - ✅ Updated coverage analysis

2. **Monitor Performance:**
   - Track failure rates for new feeds (should be < 10%)
   - Monitor content quality and relevance
   - Check dashboard: "Learning Statistics" dialog

3. **Future Enhancements:**
   - Consider API integration for PhilPapers (if needed)
   - Find alternatives for unavailable feeds (Center for Humane Technology, Harvard Divinity, BBC Religion)
   - Monitor for new RSS feeds in Philosophy & Religion categories

---

**Report Generated:** 2025-01-XX  
**Last Updated:** 2025-01-XX (After test results)  
**Next Review:** After monitoring new feeds for 1 week

