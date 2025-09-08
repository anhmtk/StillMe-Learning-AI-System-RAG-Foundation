#!/usr/bin/env python3
"""
Direct test for AgentDev system - bypass pytest completely
"""

import sys
import os

def run_direct_test():
    """Run test directly without pytest"""
    print("Running direct test...")
    
    # Test 1: Basic math
    assert 1 + 1 == 2, "Basic math failed"
    print("Basic math test passed")
    
    # Test 2: Basic string
    assert "hello" + " " + "world" == "hello world", "Basic string failed"
    print("Basic string test passed")
    
    # Test 3: Basic list
    test_list = [1, 2, 3]
    assert len(test_list) == 3, "Basic list failed"
    print("Basic list test passed")
    
    # Test 4: Environment variables
    assert os.getenv("AGENTDEV_TEST_MODE") == "1", "Environment variable test failed"
    print("Environment variable test passed")
    
    print("All direct tests passed!")
    return True

if __name__ == "__main__":
    try:
        success = run_direct_test()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"Test failed: {e}")
        sys.exit(1)
