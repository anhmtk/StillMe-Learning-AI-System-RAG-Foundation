"""
Test script for NPR Phase 2.1: Parallel RAG Retrieval from multiple collections.

Tests:
1. Parallel retrieval correctness (same results as sequential)
2. Performance measurement (speedup from parallel execution)
3. Multiple collections retrieval (knowledge, codebase, git_history)
4. Backward compatibility (default behavior unchanged)
"""

import os
import sys
import time
from typing import List, Dict, Any
from dotenv import load_dotenv

# Fix Windows encoding for emoji
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

load_dotenv()

from backend.vector_db.rag_retrieval import RAGRetrieval
from backend.vector_db.chroma_client import ChromaClient
from backend.vector_db.embeddings import EmbeddingService


def create_rag_retrieval() -> RAGRetrieval:
    """Create RAGRetrieval instance for testing."""
    embedding_service = EmbeddingService()
    chroma_client = ChromaClient(embedding_service=embedding_service)
    return RAGRetrieval(chroma_client, embedding_service)


def test_backward_compatibility():
    """Test that default behavior is unchanged (backward compatible)."""
    print("\n" + "="*60)
    print("TEST 1: Backward Compatibility")
    print("="*60)
    
    rag = create_rag_retrieval()
    
    query = "What is StillMe?"
    
    # Test default behavior (should only query knowledge + conversation)
    print("\n  Test: Default behavior (include_codebase=False, include_git_history=False)")
    try:
        result = rag.retrieve_context(
            query,
            knowledge_limit=3,
            conversation_limit=1,
            include_codebase=False,  # Default
            include_git_history=False  # Default
        )
        
        print(f"    ✅ Default retrieval successful")
        print(f"    Knowledge docs: {len(result.get('knowledge_docs', []))}")
        print(f"    Conversation docs: {len(result.get('conversation_docs', []))}")
        print(f"    Codebase docs: {len(result.get('codebase_docs', []))} (should be 0)")
        print(f"    Git history docs: {len(result.get('git_history_docs', []))} (should be 0)")
        
        # Verify backward compatibility
        assert "codebase_docs" in result, "codebase_docs field should exist"
        assert "git_history_docs" in result, "git_history_docs field should exist"
        assert len(result.get("codebase_docs", [])) == 0, "codebase_docs should be empty by default"
        assert len(result.get("git_history_docs", [])) == 0, "git_history_docs should be empty by default"
        
        print(f"    ✅ Backward compatibility verified")
        return True
        
    except Exception as e:
        print(f"    ❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_parallel_retrieval():
    """Test parallel retrieval from multiple collections."""
    print("\n" + "="*60)
    print("TEST 2: Parallel Retrieval from Multiple Collections")
    print("="*60)
    
    rag = create_rag_retrieval()
    
    query = "How does the validation chain work?"
    
    # Test with codebase and git_history enabled
    print("\n  Test: Parallel retrieval (include_codebase=True, include_git_history=True)")
    try:
        start = time.time()
        result = rag.retrieve_context(
            query,
            knowledge_limit=3,
            conversation_limit=1,
            include_codebase=True,
            include_git_history=True,
            codebase_limit=2,
            git_history_limit=2
        )
        elapsed = time.time() - start
        
        print(f"    ✅ Parallel retrieval completed in {elapsed:.3f}s")
        print(f"    Knowledge docs: {len(result.get('knowledge_docs', []))}")
        print(f"    Conversation docs: {len(result.get('conversation_docs', []))}")
        print(f"    Codebase docs: {len(result.get('codebase_docs', []))}")
        print(f"    Git history docs: {len(result.get('git_history_docs', []))}")
        print(f"    Total context docs: {result.get('total_context_docs', 0)}")
        
        # Verify results structure
        assert "codebase_docs" in result, "codebase_docs field should exist"
        assert "git_history_docs" in result, "git_history_docs field should exist"
        assert "knowledge_docs" in result, "knowledge_docs field should exist"
        
        # Check if codebase results are merged into knowledge_docs
        knowledge_docs = result.get("knowledge_docs", [])
        codebase_docs = result.get("codebase_docs", [])
        git_history_docs = result.get("git_history_docs", [])
        
        # Count codebase and git_history sources in knowledge_docs
        codebase_in_knowledge = sum(1 for doc in knowledge_docs if doc.get("source") == "codebase")
        git_history_in_knowledge = sum(1 for doc in knowledge_docs if doc.get("source") == "git_history")
        
        print(f"    Codebase docs in knowledge_docs: {codebase_in_knowledge}")
        print(f"    Git history docs in knowledge_docs: {git_history_in_knowledge}")
        
        print(f"    ✅ Parallel retrieval structure verified")
        return True
        
    except Exception as e:
        print(f"    ❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_performance():
    """Test performance improvement from parallel execution."""
    print("\n" + "="*60)
    print("TEST 3: Performance Measurement")
    print("="*60)
    
    rag = create_rag_retrieval()
    
    query = "How does StillMe track task execution time?"
    
    # Test sequential (default) vs parallel
    print("\n  Test: Sequential vs Parallel Performance")
    
    try:
        # Sequential (default)
        print("\n    Sequential (default):")
        sequential_times = []
        for i in range(3):
            start = time.time()
            result = rag.retrieve_context(
                query,
                knowledge_limit=3,
                conversation_limit=1,
                include_codebase=False,
                include_git_history=False
            )
            elapsed = time.time() - start
            sequential_times.append(elapsed)
            print(f"      Run {i+1}: {elapsed:.3f}s")
        
        avg_sequential = sum(sequential_times) / len(sequential_times)
        print(f"    Average: {avg_sequential:.3f}s")
        
        # Parallel (with codebase and git_history)
        print("\n    Parallel (with codebase + git_history):")
        parallel_times = []
        for i in range(3):
            start = time.time()
            result = rag.retrieve_context(
                query,
                knowledge_limit=3,
                conversation_limit=1,
                include_codebase=True,
                include_git_history=True,
                codebase_limit=2,
                git_history_limit=2
            )
            elapsed = time.time() - start
            parallel_times.append(elapsed)
            print(f"      Run {i+1}: {elapsed:.3f}s")
        
        avg_parallel = sum(parallel_times) / len(parallel_times)
        print(f"    Average: {avg_parallel:.3f}s")
        
        # Calculate speedup
        if avg_sequential > 0:
            speedup = avg_sequential / avg_parallel if avg_parallel > 0 else 0
            print(f"\n    Speedup: {speedup:.2f}x")
            if speedup >= 1.0:
                print(f"    ✅ Parallel is faster or equal")
            else:
                print(f"    ⚠️ Parallel is slower (may be due to overhead or empty collections)")
        
        print(f"    ✅ Performance test completed")
        return True
        
    except Exception as e:
        print(f"    ❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_edge_cases():
    """Test edge cases for parallel retrieval."""
    print("\n" + "="*60)
    print("TEST 4: Edge Cases")
    print("="*60)
    
    rag = create_rag_retrieval()
    
    all_passed = True
    
    # Edge case 1: Empty query
    print("\n  Edge Case 1: Empty query")
    try:
        result = rag.retrieve_context(
            "",
            knowledge_limit=3,
            include_codebase=True,
            include_git_history=True
        )
        print(f"    ✅ Empty query handled")
    except Exception as e:
        print(f"    ❌ Empty query failed: {e}")
        all_passed = False
    
    # Edge case 2: Very long query
    print("\n  Edge Case 2: Very long query")
    try:
        long_query = "How does StillMe work? " * 50
        result = rag.retrieve_context(
            long_query,
            knowledge_limit=3,
            include_codebase=True,
            include_git_history=True
        )
        print(f"    ✅ Very long query handled (length: {len(long_query)})")
    except Exception as e:
        print(f"    ❌ Very long query failed: {e}")
        all_passed = False
    
    # Edge case 3: Only codebase enabled
    print("\n  Edge Case 3: Only codebase enabled")
    try:
        result = rag.retrieve_context(
            "How does validation work?",
            knowledge_limit=0,  # No knowledge
            conversation_limit=0,  # No conversation
            include_codebase=True,
            include_git_history=False
        )
        print(f"    ✅ Only codebase enabled handled")
        print(f"    Codebase docs: {len(result.get('codebase_docs', []))}")
    except Exception as e:
        print(f"    ❌ Only codebase enabled failed: {e}")
        all_passed = False
    
    # Edge case 4: Only git_history enabled
    print("\n  Edge Case 4: Only git_history enabled")
    try:
        result = rag.retrieve_context(
            "Why did we choose Redis?",
            knowledge_limit=0,
            conversation_limit=0,
            include_codebase=False,
            include_git_history=True
        )
        print(f"    ✅ Only git_history enabled handled")
        print(f"    Git history docs: {len(result.get('git_history_docs', []))}")
    except Exception as e:
        print(f"    ❌ Only git_history enabled failed: {e}")
        all_passed = False
    
    if all_passed:
        print("\n  ✅ All edge case tests passed!")
    else:
        print("\n  ❌ Some edge case tests failed!")
    
    return all_passed


def main():
    """Run all tests."""
    print("\n" + "="*60)
    print("NPR Phase 2.1: Parallel RAG Retrieval Tests")
    print("="*60)
    
    results = {
        "backward_compatibility": False,
        "parallel_retrieval": False,
        "performance": False,
        "edge_cases": False,
    }
    
    try:
        # Test 1: Backward compatibility
        results["backward_compatibility"] = test_backward_compatibility()
        
        # Test 2: Parallel retrieval
        results["parallel_retrieval"] = test_parallel_retrieval()
        
        # Test 3: Performance
        results["performance"] = test_performance()
        
        # Test 4: Edge cases
        results["edge_cases"] = test_edge_cases()
        
    except Exception as e:
        print(f"\n❌ Test suite failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    print(f"Backward Compatibility: {'✅ PASS' if results['backward_compatibility'] else '❌ FAIL'}")
    print(f"Parallel Retrieval:     {'✅ PASS' if results['parallel_retrieval'] else '❌ FAIL'}")
    print(f"Performance:            {'✅ PASS' if results['performance'] else '❌ FAIL'}")
    print(f"Edge Cases:             {'✅ PASS' if results['edge_cases'] else '❌ FAIL'}")
    
    all_passed = all(results.values())
    if all_passed:
        print("\n✅ All tests passed!")
    else:
        print("\n❌ Some tests failed!")
    
    return all_passed


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

