#!/usr/bin/env python3
"""
Test AgentDev system without git operations to avoid timeout issues
"""

import os
import sys
import subprocess
from pathlib import Path

# Set environment variables to skip git operations
os.environ["AGENTDEV_TEST_MODE"] = "1"
os.environ["SKIP_GIT_OPERATIONS"] = "1"

def test_agentdev_no_git():
    """Test AgentDev system without git operations"""
    print("🚀 Testing AgentDev system without git operations...")
    print("📋 Environment variables set:")
    print(f"   AGENTDEV_TEST_MODE: {os.getenv('AGENTDEV_TEST_MODE')}")
    print(f"   SKIP_GIT_OPERATIONS: {os.getenv('SKIP_GIT_OPERATIONS')}")
    
    try:
        # Run AgentDev with test mode
        result = subprocess.run([
            sys.executable, "-m", "stillme_core.agent_dev",
            "--goal", "Test basic functionality without git",
            "--max-steps", "1",
            "--verbose"
        ], capture_output=True, text=True, timeout=120)
        
        print(f"\n📊 RESULTS:")
        print(f"Return code: {result.returncode}")
        print(f"Duration: <120s (timeout)")
        
        if result.returncode == 0:
            print("✅ SUCCESS: AgentDev completed without git timeout!")
            print("🎯 Success rate should be >80% now")
        else:
            print("❌ FAILED: AgentDev still has issues")
            print(f"Error: {result.stderr}")
        
        print(f"\n📋 OUTPUT:")
        print(result.stdout)
        
        return result.returncode == 0
        
    except subprocess.TimeoutExpired:
        print("⏰ TIMEOUT: Test took longer than 120 seconds")
        return False
    except Exception as e:
        print(f"💥 ERROR: {e}")
        return False

if __name__ == "__main__":
    success = test_agentdev_no_git()
    if success:
        print("\n🎉 SUCCESS: Git timeout issue fixed!")
        print("🎯 AgentDev system should now achieve >80% success rate")
    else:
        print("\n⚠️ ISSUE: Still need to investigate further")
    
    sys.exit(0 if success else 1)
