"""
Test Alternative RSS Feeds for Unavailable Sources
"""

import feedparser
import requests
from typing import Dict, List, Tuple
import time

# Alternative feeds to test
ALTERNATIVE_FEEDS = {
    "ai_ethics": [
        {
            "url": "https://www.technologyreview.com/topic/artificial-intelligence/feed/",
            "name": "MIT Technology Review - AI",
            "category": "ai_ethics",
            "note": "Already added"
        },
        {
            "url": "https://venturebeat.com/ai/feed/",
            "name": "VentureBeat - AI",
            "category": "ai_ethics"
        },
        {
            "url": "https://www.theverge.com/ai-artificial-intelligence/rss/index.xml",
            "name": "The Verge - AI",
            "category": "ai_ethics"
        },
        {
            "url": "https://www.wired.com/feed/tag/artificial-intelligence/latest/rss",
            "name": "Wired - AI",
            "category": "ai_ethics"
        },
    ],
    "religion": [
        {
            "url": "https://religionnews.com/feed/",
            "name": "Religion News Service",
            "category": "religion"
        },
        {
            "url": "https://www.christianitytoday.com/ct/rss/",
            "name": "Christianity Today",
            "category": "religion"
        },
        {
            "url": "https://www.hinduismtoday.com/blogs-news/feed/",
            "name": "Hinduism Today",
            "category": "religion"
        },
        {
            "url": "https://www.islamic-relief.org/feed/",
            "name": "Islamic Relief Worldwide",
            "category": "religion"
        },
        {
            "url": "https://www.patheos.com/feed/",
            "name": "Patheos - Multi-faith",
            "category": "religion"
        },
    ],
    "buddhist": [
        {
            "url": "https://www.lionsroar.com/feed/",
            "name": "Lion's Roar",
            "category": "buddhist",
            "note": "Already in system"
        },
        {
            "url": "https://www.tricycle.org/feed/",
            "name": "Tricycle",
            "category": "buddhist",
            "note": "Previously 403, retry"
        },
        {
            "url": "https://www.buddhistdoor.net/feed/",
            "name": "BuddhistDoor Global",
            "category": "buddhist",
            "note": "Previously empty, retry"
        },
    ]
}

def test_feed(feed_info: Dict) -> Tuple[bool, str, int]:
    """Test a single RSS feed URL"""
    url = feed_info["url"]
    name = feed_info["name"]
    
    try:
        response = requests.get(url, timeout=10, headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        })
        
        if response.status_code != 200:
            return False, f"HTTP {response.status_code}", 0
        
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
    """Test all alternative feeds"""
    print("=" * 80)
    print("ALTERNATIVE RSS FEEDS TEST")
    print("=" * 80)
    print()
    
    results = {
        "available": [],
        "unavailable": []
    }
    
    for category, feeds in ALTERNATIVE_FEEDS.items():
        print(f"🔵 {category.upper().replace('_', ' ')} FEEDS:")
        print("-" * 80)
        
        for feed in feeds:
            if "note" in feed and "Already" in feed["note"]:
                print(f"⏭️  Skipping: {feed['name']} ({feed.get('note', '')})")
                print()
                continue
            
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
    
    # Summary
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"✅ Available: {len(results['available'])}")
    print(f"❌ Unavailable: {len(results['unavailable'])}")
    print()
    
    if results["available"]:
        print("AVAILABLE ALTERNATIVE FEEDS (Ready to add):")
        for feed in results["available"]:
            print(f"  - {feed['name']}: {feed['url']} ({feed['entry_count']} entries)")
        print()
    
    if results["unavailable"]:
        print("UNAVAILABLE ALTERNATIVE FEEDS:")
        for feed in results["unavailable"]:
            print(f"  - {feed['name']}: {feed['error']}")
        print()

if __name__ == "__main__":
    main()

