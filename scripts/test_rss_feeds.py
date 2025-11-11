"""
Test RSS Feeds Script
Tests all RSS feeds configured in RSSFetcher to ensure they are accessible and working
"""

import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.services.rss_fetcher import RSSFetcher
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_rss_feeds():
    """Test all RSS feeds and report status"""
    fetcher = RSSFetcher()
    
    print("=" * 60)
    print("RSS FEEDS TEST")
    print("=" * 60)
    print(f"\nTotal feeds configured: {len(fetcher.feeds)}\n")
    
    results = []
    
    for feed_url in fetcher.feeds:
        print(f"Testing: {feed_url}")
        try:
            entries = fetcher.fetch_single_feed(feed_url, max_items=3)
            
            if entries:
                status = "[OK]"
                item_count = len(entries)
                sample_title = entries[0].get("title", "N/A")[:60]
                print(f"  Status: {status}")
                print(f"  Items fetched: {item_count}")
                print(f"  Sample title: {sample_title}...")
                results.append({
                    "url": feed_url,
                    "status": "OK",
                    "items": item_count,
                    "error": None
                })
            else:
                status = "[EMPTY]"
                print(f"  Status: {status}")
                print(f"  Items fetched: 0")
                results.append({
                    "url": feed_url,
                    "status": "EMPTY",
                    "items": 0,
                    "error": "No items returned"
                })
        except Exception as e:
            status = "[ERROR]"
            error_msg = str(e)[:100]
            print(f"  Status: {status}")
            print(f"  Error: {error_msg}")
            results.append({
                "url": feed_url,
                "status": "ERROR",
                "items": 0,
                "error": error_msg
            })
        
        print()
    
    # Summary
    print("=" * 60)
    print("SUMMARY")
    print("=" * 60)
    
    ok_count = sum(1 for r in results if r["status"] == "OK")
    empty_count = sum(1 for r in results if r["status"] == "EMPTY")
    error_count = sum(1 for r in results if r["status"] == "ERROR")
    
    print(f"[OK]: {ok_count}/{len(results)}")
    print(f"[EMPTY]: {empty_count}/{len(results)}")
    print(f"[ERROR]: {error_count}/{len(results)}")
    
    if error_count > 0:
        print("\n[WARNING] Failed feeds:")
        for r in results:
            if r["status"] == "ERROR":
                print(f"  - {r['url']}: {r['error']}")
    
    if empty_count > 0:
        print("\n[WARNING] Empty feeds (may need investigation):")
        for r in results:
            if r["status"] == "EMPTY":
                print(f"  - {r['url']}")
    
    print("\n" + "=" * 60)
    
    return results


if __name__ == "__main__":
    test_rss_feeds()

