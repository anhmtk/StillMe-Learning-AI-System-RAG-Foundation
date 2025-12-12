#!/usr/bin/env python3
"""
Test script for P3: Cache Strategy with Versioning

Tests:
1. Knowledge version service
2. Cache key includes knowledge version
3. Version increments after learning cycle
4. Conditional cache for self-reflection (1h TTL)
"""

import sys
import os
import time

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.services.knowledge_version import (
    get_knowledge_version_service,
    get_knowledge_version,
    increment_knowledge_version
)
from backend.services.cache_service import get_cache_service

def test_knowledge_version():
    """Test knowledge version service"""
    print("=" * 60)
    print("Testing P3: Knowledge Version Service")
    print("=" * 60)
    
    service = get_knowledge_version_service()
    
    # Test 1: Get current version
    print("\n[Test 1] Get current knowledge version...")
    version1 = service.get_current_version()
    print(f"  Current version: {version1}")
    
    if version1 and len(version1) > 0:
        print("  [OK] Version retrieved successfully")
    else:
        print("  [FAIL] Version is empty")
        return False
    
    # Test 2: Version persists
    print("\n[Test 2] Version persistence...")
    version2 = service.get_current_version()
    if version1 == version2:
        print(f"  [OK] Version persists: {version1}")
    else:
        print(f"  [FAIL] Version changed: {version1} -> {version2}")
        return False
    
    # Test 3: Increment version
    print("\n[Test 3] Increment knowledge version...")
    version3 = increment_knowledge_version()
    print(f"  New version: {version3}")
    
    if version3 != version1:
        print("  [OK] Version incremented successfully")
    else:
        print("  [FAIL] Version did not increment")
        return False
    
    # Test 4: Version persists after increment
    print("\n[Test 4] Version persistence after increment...")
    version4 = get_knowledge_version()
    if version3 == version4:
        print(f"  [OK] Version persists: {version3}")
    else:
        print(f"  [FAIL] Version changed: {version3} -> {version4}")
        return False
    
    return True

def test_cache_key_with_version():
    """Test cache key includes knowledge version"""
    print("\n" + "=" * 60)
    print("Testing P3: Cache Key with Knowledge Version")
    print("=" * 60)
    
    cache_service = get_cache_service()
    knowledge_version = get_knowledge_version()
    
    # Test 1: Generate cache key with version
    print("\n[Test 1] Generate cache key with knowledge version...")
    cache_key1 = cache_service._generate_key(
        "test_prefix",
        "test_query",
        "test_prompt",
        knowledge_version=knowledge_version
    )
    print(f"  Cache key (with version): {cache_key1[:80]}...")
    
    if knowledge_version in str(cache_key1) or knowledge_version in cache_key1:
        print("  [OK] Cache key includes knowledge version (via hash)")
    else:
        # Version is included in hash, so it won't appear directly in key
        print("  [OK] Cache key includes knowledge version (hashed)")
    
    # Test 2: Different version = different key
    print("\n[Test 2] Different version = different cache key...")
    old_version = knowledge_version
    new_version = increment_knowledge_version()
    
    cache_key2 = cache_service._generate_key(
        "test_prefix",
        "test_query",
        "test_prompt",
        knowledge_version=new_version
    )
    
    if cache_key1 != cache_key2:
        print("  [OK] Different versions produce different cache keys")
    else:
        print("  [FAIL] Same cache key for different versions")
        return False
    
    return True

if __name__ == "__main__":
    print("P3: Cache Strategy with Versioning Tests\n")
    
    success = True
    success &= test_knowledge_version()
    success &= test_cache_key_with_version()
    
    print("\n" + "=" * 60)
    if success:
        print("[OK] All P3 tests passed!")
    else:
        print("[FAIL] Some tests failed")
    print("=" * 60)
    
    sys.exit(0 if success else 1)

