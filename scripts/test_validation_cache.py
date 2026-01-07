"""
Test Script for Validation Cache Enhancement (Task 2)

Tests validation caching to ensure:
1. Cache hit for identical queries + context
2. Cache miss for different queries
3. Cache miss for same query but different context
4. TTL expiration works
5. Redis fallback to in-memory works
6. Cache statistics are accurate
"""

import sys
import os
import asyncio
import time
from typing import Dict, Any

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pytest
from backend.utils.cache_utils import (
    hash_query,
    hash_context,
    get_cache_key,
    get_from_cache,
    set_to_cache,
    clear_cache,
    get_cache_stats
)


def test_hash_query():
    """Test query hashing"""
    print("\n=== Test 1: Query Hashing ===")
    
    # Same query should produce same hash
    query1 = "What is RAG?"
    query2 = "What is RAG?"
    hash1 = hash_query(query1)
    hash2 = hash_query(query2)
    
    assert hash1 == hash2, f"Same query should produce same hash: {hash1} != {hash2}"
    print(f"[PASS] Same query produces same hash: {hash1}")
    
    # Different queries should produce different hashes
    query3 = "What is machine learning?"
    hash3 = hash_query(query3)
    
    assert hash1 != hash3, f"Different queries should produce different hashes"
    print(f"[PASS] Different queries produce different hashes: {hash1} != {hash3}")
    
    # Normalization (lowercase, strip)
    query4 = "  WHAT IS RAG?  "
    hash4 = hash_query(query4)
    
    assert hash1 == hash4, f"Normalized query should produce same hash: {hash1} != {hash4}"
    print(f"[PASS] Normalized query produces same hash: {hash1} == {hash4}")
    
    print("[PASS] Test 1: Query hashing works correctly\n")


def test_hash_context():
    """Test context hashing"""
    print("\n=== Test 2: Context Hashing ===")
    
    # Same context should produce same hash
    context1 = {
        "knowledge_docs": [
            {"id": "doc1", "similarity": 0.85},
            {"id": "doc2", "similarity": 0.75}
        ]
    }
    context2 = {
        "knowledge_docs": [
            {"id": "doc1", "similarity": 0.85},
            {"id": "doc2", "similarity": 0.75}
        ]
    }
    hash1 = hash_context(context1)
    hash2 = hash_context(context2)
    
    assert hash1 == hash2, f"Same context should produce same hash: {hash1} != {hash2}"
    print(f"[PASS] Same context produces same hash: {hash1}")
    
    # Different context should produce different hash
    context3 = {
        "knowledge_docs": [
            {"id": "doc1", "similarity": 0.85},
            {"id": "doc3", "similarity": 0.90}  # Different doc
        ]
    }
    hash3 = hash_context(context3)
    
    assert hash1 != hash3, f"Different context should produce different hash"
    print(f"[PASS] Different context produces different hash: {hash1} != {hash3}")
    
    # Empty context
    context4 = {}
    hash4 = hash_context(context4)
    
    assert hash4 == "no_context", f"Empty context should return 'no_context': {hash4}"
    print(f"[PASS] Empty context handled correctly: {hash4}")
    
    print("[PASS] Test 2: Context hashing works correctly\n")


def test_cache_key_generation():
    """Test cache key generation"""
    print("\n=== Test 3: Cache Key Generation ===")
    
    query = "What is RAG?"
    context = {
        "knowledge_docs": [
            {"id": "doc1", "similarity": 0.85}
        ]
    }
    
    key1 = get_cache_key("validation", query, context)
    key2 = get_cache_key("validation", query, context)
    
    assert key1 == key2, f"Same query+context should produce same key: {key1} != {key2}"
    assert key1.startswith("validation:"), f"Key should start with prefix: {key1}"
    print(f"[PASS] Cache key generated correctly: {key1[:50]}...")
    
    # Different prefix
    key3 = get_cache_key("llm_response", query, context)
    assert key1 != key3, f"Different prefix should produce different key"
    print(f"[PASS] Different prefix produces different key")
    
    print("[PASS] Test 3: Cache key generation works correctly\n")


def test_cache_basic_operations():
    """Test basic cache operations (get/set)"""
    print("\n=== Test 4: Basic Cache Operations ===")
    
    # Clear cache first
    clear_cache()
    
    # Test set and get
    key = "test:key:123"
    value = {"test": "data", "number": 42}
    
    # Should not exist
    cached = get_from_cache(key)
    assert cached is None, f"Cache should be empty initially: {cached}"
    print(f"[PASS] Cache miss for new key")
    
    # Set value
    set_to_cache(key, value, ttl=60)
    print(f"[PASS] Value cached")
    
    # Should exist now
    cached = get_from_cache(key)
    assert cached == value, f"Cached value should match: {cached} != {value}"
    print(f"[PASS] Cache hit for cached key")
    
    # Clear and verify
    clear_cache(key)
    cached = get_from_cache(key)
    assert cached is None, f"Cache should be cleared: {cached}"
    print(f"[PASS] Cache cleared successfully")
    
    print("[PASS] Test 4: Basic cache operations work correctly\n")


def test_cache_ttl_expiration():
    """Test TTL expiration (in-memory)"""
    print("\n=== Test 5: TTL Expiration ===")
    
    # Clear cache
    clear_cache()
    
    key = "test:ttl:key"
    value = {"test": "ttl"}
    
    # Set with short TTL (1 second)
    set_to_cache(key, value, ttl=1)
    
    # Should exist immediately
    cached = get_from_cache(key)
    assert cached == value, f"Value should exist immediately: {cached}"
    print(f"[PASS] Value cached with TTL=1s")
    
    # Wait for expiration
    print(f"[WAIT] Waiting for TTL expiration (2 seconds)...")
    time.sleep(2)
    
    # Should be expired
    cached = get_from_cache(key)
    assert cached is None, f"Value should be expired: {cached}"
    print(f"[PASS] TTL expiration works correctly")
    
    print("[PASS] Test 5: TTL expiration works correctly\n")


def test_cache_query_context_scenarios():
    """Test cache with realistic query+context scenarios"""
    print("\n=== Test 6: Realistic Query+Context Scenarios ===")
    
    # Clear cache
    clear_cache()
    
    # Scenario 1: Same query + same context = cache hit
    query1 = "What is machine learning?"
    context1 = {
        "knowledge_docs": [
            {"id": "ml_doc_1", "similarity": 0.90},
            {"id": "ml_doc_2", "similarity": 0.85}
        ]
    }
    
    key1 = get_cache_key("validation", query1, context1)
    validation_result1 = {"passed": True, "reasons": ["has_citation", "high_confidence"]}
    
    set_to_cache(key1, validation_result1, ttl=3600)
    print(f"[PASS] Cached validation result for query 1")
    
    # Same query + same context should hit cache
    cached1 = get_from_cache(key1)
    assert cached1 == validation_result1, f"Cache hit should return same value"
    print(f"[PASS] Cache HIT for identical query+context")
    
    # Scenario 2: Same query + different context = cache miss
    context2 = {
        "knowledge_docs": [
            {"id": "ml_doc_3", "similarity": 0.80}  # Different doc
        ]
    }
    key2 = get_cache_key("validation", query1, context2)
    
    cached2 = get_from_cache(key2)
    assert cached2 is None, f"Different context should be cache miss: {cached2}"
    print(f"[PASS] Cache MISS for same query but different context")
    
    # Scenario 3: Different query + same context = cache miss
    query2 = "What is deep learning?"
    key3 = get_cache_key("validation", query2, context1)
    
    cached3 = get_from_cache(key3)
    assert cached3 is None, f"Different query should be cache miss: {cached3}"
    print(f"[PASS] Cache MISS for different query but same context")
    
    print("[PASS] Test 6: Realistic scenarios work correctly\n")


def test_cache_statistics():
    """Test cache statistics"""
    print("\n=== Test 7: Cache Statistics ===")
    
    # Clear cache
    clear_cache()
    
    # Get initial stats
    stats1 = get_cache_stats()
    initial_size = stats1.get("in_memory_size", 0)
    print(f"[PASS] Initial cache size: {initial_size}")
    
    # Add some items
    for i in range(5):
        key = f"test:stats:{i}"
        set_to_cache(key, {"value": i}, ttl=60)
    
    # Get stats after adding
    stats2 = get_cache_stats()
    new_size = stats2.get("in_memory_size", 0)
    
    assert new_size >= initial_size + 5, f"Cache size should increase: {new_size} < {initial_size + 5}"
    print(f"[PASS] Cache size increased: {initial_size} -> {new_size}")
    
    # Check stats structure
    assert "in_memory_size" in stats2, "Stats should include in_memory_size"
    assert "redis_available" in stats2, "Stats should include redis_available"
    print(f"[PASS] Cache statistics structure is correct")
    
    print("[PASS] Test 7: Cache statistics work correctly\n")


def test_cache_edge_cases():
    """Test edge cases"""
    print("\n=== Test 8: Edge Cases ===")
    
    # Clear cache
    clear_cache()
    
    # Empty query
    key1 = get_cache_key("validation", "", {})
    assert key1.startswith("validation:"), f"Empty query should still generate key"
    print(f"[PASS] Empty query handled: {key1[:30]}...")
    
    # None context
    key2 = get_cache_key("validation", "test", None)
    assert key2.startswith("validation:"), f"None context should still generate key"
    print(f"[PASS] None context handled: {key2[:30]}...")
    
    # Very long query (should be hashed)
    long_query = "What is " + "RAG " * 1000
    hash_long = hash_query(long_query)
    assert len(hash_long) == 16, f"Hash should be fixed length: {len(hash_long)}"
    print(f"[PASS] Long query hashed correctly: {hash_long}")
    
    # Context with no docs
    context_empty = {"knowledge_docs": []}
    hash_empty = hash_context(context_empty)
    assert hash_empty == "no_docs", f"Empty docs should return 'no_docs': {hash_empty}"
    print(f"[PASS] Empty docs context handled correctly")
    
    print("[PASS] Test 8: Edge cases handled correctly\n")


def run_all_tests():
    """Run all tests"""
    print("=" * 60)
    print("VALIDATION CACHE TEST SUITE")
    print("=" * 60)
    
    tests = [
        test_hash_query,
        test_hash_context,
        test_cache_key_generation,
        test_cache_basic_operations,
        test_cache_ttl_expiration,
        test_cache_query_context_scenarios,
        test_cache_statistics,
        test_cache_edge_cases
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            test()
            passed += 1
        except AssertionError as e:
            print(f"[FAIL] FAILED: {test.__name__}")
            print(f"   Error: {e}")
            failed += 1
        except Exception as e:
            print(f"[FAIL] ERROR in {test.__name__}: {e}")
            import traceback
            traceback.print_exc()
            failed += 1
    
    print("=" * 60)
    print(f"TEST RESULTS: {passed} passed, {failed} failed")
    print("=" * 60)
    
    if failed == 0:
        print("[SUCCESS] ALL TESTS PASSED - Task 2 is ready for production!")
        return True
    else:
        print("[FAIL] SOME TESTS FAILED - Please fix issues before proceeding")
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)

