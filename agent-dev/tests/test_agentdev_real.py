#!/usr/bin/env python3
"""
Test AgentDev Real trực tiếp
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import trực tiếp
from stillme_core.core.legacy_agentdev.agentdev_real import execute_agentdev_task


def test_agentdev_real():
    """Test AgentDev thực sự"""
    print("🤖 Testing AgentDev Real...")
    print("=" * 50)

    # Test sửa lỗi
    result = execute_agentdev_task("Sửa lỗi trong agent_coordinator.py")
    print(result)

    print("\n" + "=" * 50)

    # Test viết code
    result2 = execute_agentdev_task("Viết code cho web scraper")
    print(result2)

if __name__ == "__main__":
    test_agentdev_real()
