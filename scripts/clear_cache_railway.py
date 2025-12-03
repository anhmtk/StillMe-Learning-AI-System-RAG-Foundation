#!/usr/bin/env python3
"""
Script to clear StillMe backend cache on Railway using Python.

This is a Python equivalent of clear_cache_railway.ps1 for cross-platform compatibility.
"""

import requests
import argparse
import sys

# Ensure UTF-8 output for Windows
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')


def clear_cache(backend_url: str, pattern: str = None, clear_all: bool = False):
    """
    Clear cache on Railway backend.
    
    Args:
        backend_url: Base URL of StillMe backend
        pattern: Optional pattern to clear specific keys (e.g., "llm:response:*")
        clear_all: If True, clear all cache entries
    """
    print("="*60)
    print("StillMe Backend Cache Clearing Script")
    print("="*60)
    
    # Ensure URL has scheme
    if not backend_url.startswith("http://") and not backend_url.startswith("https://"):
        backend_url = "https://" + backend_url
        print(f"ℹ️  Added https:// scheme to URL: {backend_url}")
    
    # Build endpoint URL
    if clear_all:
        endpoint = f"{backend_url}/api/cache/clear"
        print("Attempting to clear ALL cache entries...")
    else:
        if pattern:
            endpoint = f"{backend_url}/api/cache/clear?pattern={pattern}"
            print(f"Attempting to clear cache entries matching pattern: '{pattern}'...")
        else:
            # Default to LLM cache
            pattern = "llm:response:*"
            endpoint = f"{backend_url}/api/cache/clear?pattern={pattern}"
            print(f"Attempting to clear LLM response cache (default pattern: '{pattern}')...")
    
    print()
    
    try:
        print(f"Sending request to: {endpoint}")
        response = requests.post(endpoint, timeout=60)
        
        if response.status_code == 200:
            data = response.json()
            status = data.get("status", "unknown")
            message = data.get("message", "")
            cleared_count = data.get("cleared_count", 0)
            
            print("✅ Cache clear successful!")
            print(f"Status: {status}")
            print(f"Message: {message}")
            if data.get("pattern"):
                print(f"Pattern: {data.get('pattern')}")
            print(f"Cleared Count: {cleared_count}")
            
            print("\n" + "="*60)
            print("Cache cleared. Please test StillMe's response on Railway.")
            print("="*60)
            return True
        else:
            print(f"❌ Request failed with status code {response.status_code}")
            try:
                error_data = response.json()
                error_message = error_data.get("detail", response.text)
                print(f"Response: {error_message}")
            except:
                print(f"Response: {response.text}")
            
            print("\n" + "="*60)
            print("Cache clearing failed. Please check the error messages above.")
            print("Ensure the backend is running and accessible.")
            print("="*60)
            return False
            
    except requests.exceptions.Timeout:
        print("\n⚠️  Request timeout after 60 seconds")
        print("   This could mean:")
        print("   - Backend is processing")
        print("   - Backend is cold starting")
        print("   - Network latency")
        print("\n   Try:")
        print("   1. Wait a few seconds and retry")
        print("   2. Check backend logs on Railway")
        return False
    except requests.exceptions.RequestException as e:
        print(f"\n❌ Request error: {e}")
        print("\n" + "="*60)
        print("Cache clearing failed. Please check network connectivity and backend status.")
        print("="*60)
        return False


def main():
    """Main function"""
    parser = argparse.ArgumentParser(
        description="Clear StillMe backend cache on Railway"
    )
    parser.add_argument(
        "--backend-url",
        type=str,
        default="https://stillme-backend-production.up.railway.app",
        help="Base URL of StillMe backend (default: https://stillme-backend-production.up.railway.app)"
    )
    parser.add_argument(
        "--pattern",
        type=str,
        default="llm:response:*",
        help="Pattern to clear specific keys (default: llm:response:*)"
    )
    parser.add_argument(
        "--clear-all",
        action="store_true",
        help="Clear all cache entries (ignores --pattern)"
    )
    
    args = parser.parse_args()
    
    success = clear_cache(
        backend_url=args.backend_url,
        pattern=args.pattern if not args.clear_all else None,
        clear_all=args.clear_all
    )
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()

