# 📋 RSS Feeds Implementation Guide

**Quick Reference:** How to add new RSS feeds to StillMe

---

## 🎯 Quick Steps

### 1. Test Feed Availability

```bash
# Run the test script
python scripts/test_rss_feeds.py
```

This will test all recommended feeds and show which ones are available.

### 2. Add Feed to Configuration

**File:** `backend/services/rss_fetcher.py`

**Location:** Lines 24-82 (inside `self.feeds` list)

**Format:**
```python
# Category comment
"https://example.com/feed/",  # Feed Name - Description
```

**Example:**
```python
# Philosophy & Ethics
"https://aeon.co/feed.rss",  # Aeon Magazine - Philosophy, Religion, Culture
"https://www.technologyreview.com/topic/artificial-intelligence/feed/",  # MIT Technology Review - AI Ethics
```

### 3. Add Fallback (Optional)

**File:** `backend/services/rss_fetcher_enhanced.py`

**Location:** Lines 19-49 (inside `FALLBACK_FEEDS` dict)

**Format:**
```python
"https://primary-feed-url.com/feed/": [
    "https://fallback-1.com/feed/",
    "https://fallback-2.com/feed/"
],
```

### 4. Test Integration

```bash
# Test RSS fetcher
python -c "from backend.services.rss_fetcher import RSSFetcher; f = RSSFetcher(); print(f'Total feeds: {len(f.feeds)}')"
```

### 5. Monitor Performance

After deployment, monitor:
- Failure rate (should be < 10%)
- Feed update frequency
- Content quality

**Dashboard:** Check "Learning Statistics" for feed performance

**API:** `GET /api/monitoring/rss-feeds`

---

## 📊 Current Feed Categories

### Technology & AI (8 feeds)
- Hacker News
- NYTimes Technology
- Distill (ML Research)
- LessWrong
- Alignment Forum
- Overcoming Bias
- Scott Aaronson
- Bloomberg Markets

### Science & Research (6 feeds)
- Nature
- ScienceDaily
- Physics World
- Phys.org
- Science Magazine
- Statistical Modeling Blog

### Philosophy & Ethics (3 feeds) ⚠️ **GAP**
- Aeon Magazine
- Lion's Roar (Buddhist)
- The Guardian Religion

### Tech Policy (3 feeds)
- EFF
- Brookings
- Cato Institute

### Statistics (2 feeds)
- R-Bloggers
- Statistical Modeling Blog

---

## ✅ Recommended New Feeds (After Testing)

### High Priority:

1. **MIT Technology Review - AI**
   - URL: `https://www.technologyreview.com/topic/artificial-intelligence/feed/`
   - Category: Technology & AI Ethics
   - **Status:** ⚠️ Test first

2. **Nature Machine Intelligence**
   - URL: `https://www.nature.com/natmachintell.rss`
   - Category: Science & AI
   - **Status:** ⚠️ Test first

3. **Internet Encyclopedia of Philosophy**
   - URL: `https://iep.utm.edu/feed/`
   - Category: Philosophy
   - **Status:** ⚠️ Test first

### Medium Priority:

4. **BBC Religion & Ethics**
   - URL: `https://www.bbc.co.uk/religion/feed`
   - Category: Religion & Ethics
   - **Status:** ⚠️ Test first

5. **BuddhistDoor Global**
   - URL: `https://www.buddhistdoor.net/feed/`
   - Category: Religion
   - **Status:** ⚠️ Test first

---

## 🚨 Important Notes

### Already Implemented (Not RSS):
- ✅ **Stanford Encyclopedia of Philosophy** - Uses `StanfordEncyclopediaFetcher` (web scraping)
- ✅ **arXiv** - Uses `ArxivFetcher` (API)
- ✅ **CrossRef** - Uses `CrossrefFetcher` (API)
- ✅ **Wikipedia** - Uses `WikipediaFetcher` (API)
- ✅ **Papers with Code** - Uses `PapersWithCodeFetcher` (web scraping)
- ✅ **Conference Proceedings** - Uses `ConferenceFetcher` (RSS + web scraping)

### Removed Feeds (Do Not Re-add):
- ❌ `https://feeds.reuters.com/reuters/businessNews` - Permanent DNS errors
- ❌ `https://feeds.reuters.com/reuters/technologyNews` - Permanent DNS errors
- ❌ `https://tricycle.org/feed/` - 403 Forbidden
- ❌ `https://www.aei.org/technology/feed/` - 403 Forbidden
- ❌ `https://lilianweng.github.io/feed.xml` - 404 + XML error

---

## 🔍 Testing Checklist

Before adding a new feed:

- [ ] Feed URL is accessible (HTTP 200)
- [ ] Feed is well-formed XML (no parse errors)
- [ ] Feed has entries (at least 1 recent entry)
- [ ] Domain is not already in current feeds
- [ ] Content is relevant to StillMe's learning goals
- [ ] License allows educational/academic use
- [ ] Feed updates regularly (not stale)

---

## 📈 Monitoring

After adding feeds:

1. **Check failure rate:**
   ```bash
   # Should be < 10%
   GET /api/monitoring/rss-feeds
   ```

2. **Review learning statistics:**
   - Dashboard: "Learning Statistics" dialog
   - API: `GET /api/learning/rss/fetch-history`

3. **Monitor for issues:**
   - High failure rate (> 10%)
   - Empty feeds (0 entries)
   - XML parse errors
   - 403/404 errors

---

**Last Updated:** 2025-01-XX

