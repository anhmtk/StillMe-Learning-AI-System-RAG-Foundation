#!/usr/bin/env python3
"""
Test script for Daily Learning + Memory Integration

Author: StillMe AI Framework
Version: 1.0.0
"""

import sys
import os
from pathlib import Path

# Add modules to path
sys.path.append(str(Path(__file__).parent))

def test_learning_memory_integration():
    """Test integration between DailyLearningManager and LayeredMemoryV1"""
    print("🧠 Testing Daily Learning + Memory Integration")
    print("=" * 60)
    
    try:
        # Import modules
        from framework import StillMeFramework
        from modules.daily_learning_manager import DailyLearningManager, LearningCase
        
        print("1. Initializing StillMe Framework...")
        framework = StillMeFramework()
        print("✅ Framework initialized")
        
        print("\n2. Getting LayeredMemoryV1...")
        memory_manager = framework.layered_memory if hasattr(framework, 'layered_memory') else None
        if memory_manager:
            print("✅ LayeredMemoryV1 found")
        else:
            print("❌ LayeredMemoryV1 not found")
            return False
        
        print("\n3. Creating DailyLearningManager with Memory Integration...")
        learning_manager = DailyLearningManager(memory_manager=memory_manager)
        print("✅ Learning manager created with memory integration")
        
        print("\n4. Testing Learning Case Creation...")
        # Create a test learning case
        test_case = LearningCase(
            id="test_001",
            question="What is machine learning?",
            expected_keywords=["machine learning", "AI", "algorithm", "data"],
            difficulty="medium",
            language="en",
            category="ai_ml"
        )
        learning_manager.today_cases = [test_case]
        print("✅ Test case created")
        
        print("\n5. Testing Memory Storage...")
        # Record a test response
        test_response = "Machine learning is a subset of artificial intelligence that focuses on algorithms and statistical models that enable computers to improve their performance on a specific task through experience with data."
        test_score = 0.85
        test_feedback = "Good response covering key concepts"
        
        success = learning_manager.record_response(
            case_id="test_001",
            response=test_response,
            score=test_score,
            feedback=test_feedback
        )
        
        if success:
            print("✅ Learning result saved to memory")
        else:
            print("❌ Failed to save learning result to memory")
            return False
        
        print("\n6. Testing Memory Search...")
        # Search for learning results
        search_results = learning_manager.search_learning_memory("machine learning")
        print(f"✅ Found {len(search_results)} learning results")
        
        if search_results:
            result = search_results[0]
            print(f"   - Case ID: {result['case_id']}")
            print(f"   - Score: {result['score']}")
            print(f"   - Category: {result['category']}")
            print(f"   - Keywords Matched: {result['keywords_matched']}")
        
        print("\n7. Testing Learning Stats...")
        stats = learning_manager.get_learning_stats()
        print("✅ Learning stats retrieved:")
        print(f"   - Total cases: {stats.get('total_cases', 0)}")
        print(f"   - Today cases: {stats.get('today_cases', 0)}")
        print(f"   - Recent avg score: {stats.get('recent_avg_score', 0)}")
        
        if 'memory_stats' in stats and stats['memory_stats']:
            memory_stats = stats['memory_stats']
            print(f"   - Memory results: {memory_stats.get('total_learning_results', 0)}")
            print(f"   - Memory avg score: {memory_stats.get('avg_memory_score', 0):.2f}")
        
        print("\n8. Testing Memory Content Retrieval...")
        # Test direct memory search
        memory_results = memory_manager.search("machine learning")
        learning_memories = [m for m in memory_results if m.metadata.get("type") == "learning_result"]
        print(f"✅ Found {len(learning_memories)} learning memories in LayeredMemoryV1")
        
        if learning_memories:
            memory = learning_memories[0]
            print(f"   - Priority: {memory.priority:.2f}")
            print(f"   - Timestamp: {memory.timestamp}")
            print(f"   - Metadata keys: {list(memory.metadata.keys())}")
        
        print("\n" + "=" * 60)
        print("🎉 ALL TESTS PASSED! Integration working correctly!")
        print("=" * 60)
        
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_learning_memory_integration()
    if success:
        print("\n✅ Integration test completed successfully!")
    else:
        print("\n❌ Integration test failed!")
        sys.exit(1)
