"""
Test RSS Feed URLs for Availability
Quick script to verify RSS feed URLs before adding to StillMe
"""

import feedparser
import requests
from typing import Dict, List, Tuple
import time

# Feeds to test
TEST_FEEDS = {
    "high_priority": [
        {
            "url": "https://www.technologyreview.com/topic/artificial-intelligence/feed/",
            "name": "MIT Technology Review - AI",
            "category": "technology_ai_ethics"
        },
        {
            "url": "https://www.nature.com/natmachintell.rss",
            "name": "Nature Machine Intelligence",
            "category": "science_ai"
        },
        {
            "url": "https://www.humanetech.com/feed",
            "name": "Center for Humane Technology",
            "category": "ai_ethics"
        },
        {
            "url": "https://aiethicslab.com/feed/",
            "name": "AI Ethics Lab",
            "category": "ai_ethics"
        },
    ],
    "medium_priority": [
        {
            "url": "https://hds.harvard.edu/news/feed",
            "name": "Harvard Divinity School",
            "category": "religion"
        },
        {
            "url": "https://www.buddhistdoor.net/feed/",
            "name": "BuddhistDoor Global",
            "category": "religion"
        },
        {
            "url": "https://www.bbc.co.uk/religion/feed",
            "name": "BBC Religion & Ethics",
            "category": "religion_ethics"
        },
    ],
    "philosophy_sources": [
        {
            "url": "https://plato.stanford.edu/rss/seo.rss",
            "name": "Stanford Encyclopedia of Philosophy RSS",
            "category": "philosophy",
            "note": "May not have RSS - might need API"
        },
        {
            "url": "https://iep.utm.edu/feed/",
            "name": "Internet Encyclopedia of Philosophy",
            "category": "philosophy"
        },
        {
            "url": "https://philpapers.org/rss/recent",
            "name": "PhilPapers Recent",
            "category": "philosophy",
            "note": "May not have RSS - might need API"
        },
    ]
}

def test_feed(feed_info: Dict) -> Tuple[bool, str, int]:
    """
    Test a single RSS feed URL
    
    Returns:
        (is_available, error_message, entry_count)
    """
    url = feed_info["url"]
    name = feed_info["name"]
    
    try:
        # Test HTTP availability first
        response = requests.get(url, timeout=10, headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        })
        
        if response.status_code != 200:
            return False, f"HTTP {response.status_code}", 0
        
        # Parse feed
        feed = feedparser.parse(url)
        
        if feed.bozo and feed.bozo_exception:
            return False, f"Parse error: {feed.bozo_exception}", 0
        
        entry_count = len(feed.entries)
        
        if entry_count == 0:
            return False, "Feed is empty (0 entries)", 0
        
        return True, "OK", entry_count
        
    except requests.exceptions.Timeout:
        return False, "Timeout", 0
    except requests.exceptions.ConnectionError:
        return False, "Connection error", 0
    except Exception as e:
        return False, f"Error: {str(e)[:100]}", 0

def main():
    """Test all feeds and generate report"""
    print("=" * 80)
    print("RSS FEED AVAILABILITY TEST")
    print("=" * 80)
    print()
    
    results = {
        "available": [],
        "unavailable": [],
        "needs_api": []
    }
    
    # Test high priority feeds
    print("🔴 HIGH PRIORITY FEEDS:")
    print("-" * 80)
    for feed in TEST_FEEDS["high_priority"]:
        print(f"Testing: {feed['name']}")
        print(f"  URL: {feed['url']}")
        is_available, error, count = test_feed(feed)
        
        if is_available:
            print(f"  ✅ AVAILABLE - {count} entries")
            results["available"].append({**feed, "entry_count": count})
        else:
            print(f"  ❌ UNAVAILABLE - {error}")
            results["unavailable"].append({**feed, "error": error})
        print()
        time.sleep(1)  # Be nice to servers
    
    # Test medium priority feeds
    print("\n🟡 MEDIUM PRIORITY FEEDS:")
    print("-" * 80)
    for feed in TEST_FEEDS["medium_priority"]:
        print(f"Testing: {feed['name']}")
        print(f"  URL: {feed['url']}")
        is_available, error, count = test_feed(feed)
        
        if is_available:
            print(f"  ✅ AVAILABLE - {count} entries")
            results["available"].append({**feed, "entry_count": count})
        else:
            print(f"  ❌ UNAVAILABLE - {error}")
            results["unavailable"].append({**feed, "error": error})
        print()
        time.sleep(1)
    
    # Test philosophy sources (may need API)
    print("\n🔵 PHILOSOPHY SOURCES (May require API integration):")
    print("-" * 80)
    for feed in TEST_FEEDS["philosophy_sources"]:
        print(f"Testing: {feed['name']}")
        print(f"  URL: {feed['url']}")
        if "note" in feed:
            print(f"  Note: {feed['note']}")
        is_available, error, count = test_feed(feed)
        
        if is_available:
            print(f"  ✅ AVAILABLE - {count} entries")
            results["available"].append({**feed, "entry_count": count})
        else:
            print(f"  ❌ UNAVAILABLE - {error}")
            if "API" in feed.get("note", ""):
                results["needs_api"].append({**feed, "error": error})
            else:
                results["unavailable"].append({**feed, "error": error})
        print()
        time.sleep(1)
    
    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"✅ Available: {len(results['available'])}")
    print(f"❌ Unavailable: {len(results['unavailable'])}")
    print(f"🔧 Needs API: {len(results['needs_api'])}")
    print()
    
    if results["available"]:
        print("AVAILABLE FEEDS (Ready to add):")
        for feed in results["available"]:
            print(f"  - {feed['name']}: {feed['url']} ({feed['entry_count']} entries)")
        print()
    
    if results["unavailable"]:
        print("UNAVAILABLE FEEDS:")
        for feed in results["unavailable"]:
            print(f"  - {feed['name']}: {feed['error']}")
        print()
    
    if results["needs_api"]:
        print("FEEDS THAT MAY NEED API INTEGRATION:")
        for feed in results["needs_api"]:
            print(f"  - {feed['name']}: {feed.get('note', 'No note')}")
        print()

if __name__ == "__main__":
    main()
