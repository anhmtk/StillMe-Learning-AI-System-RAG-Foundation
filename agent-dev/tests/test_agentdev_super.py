#!/usr/bin/env python3
"""
Test AgentDev Super trực tiếp
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import trực tiếp
from stillme_core.agentdev_super import execute_agentdev_super_task


def test_agentdev_super():
    """Test AgentDev Super"""
    print("🧠 Testing AgentDev Super...")
    print("=" * 60)

    # Test sửa lỗi
    result = execute_agentdev_super_task("Sửa lỗi trong agent_coordinator.py")
    print(result)

    print("\n" + "=" * 60)

    # Test viết code
    result2 = execute_agentdev_super_task("Viết code cho web scraper")
    print(result2)

if __name__ == "__main__":
    test_agentdev_super()
