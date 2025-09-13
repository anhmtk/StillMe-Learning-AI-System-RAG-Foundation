#!/usr/bin/env python3
"""
Test AgentDev Brain trực tiếp
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import trực tiếp
from stillme_core.agentdev_brain import get_agentdev_brain


def test_agentdev_brain():
    """Test AgentDev Brain"""
    print("🧠 Testing AgentDev Brain...")
    print("=" * 50)

    # Test error analysis
    brain = get_agentdev_brain()

    # Test error analysis
    error_msg = "Type 'type[stillme_core.router.intelligent_router.AgentType]' is not assignable to declared type 'type[stillme_core.router.agent_coordinator.AgentType]'"
    pattern = brain.analyze_error(error_msg, "stillme_core/router/agent_coordinator.py", 30)

    if pattern:
        print(f"✅ Detected error: {pattern.error_type.value}")
        print(f"✅ Fix strategy: {pattern.fix_strategy.value}")
        print(f"✅ Confidence: {pattern.confidence}")

        # Test fix strategy
        fixed_line, confidence = brain.get_fix_strategy(pattern, "test.py", "from .intelligent_router import AgentType")
        print(f"✅ Fixed line: {fixed_line}")
        print(f"✅ Fix confidence: {confidence}")
    else:
        print("❌ No pattern detected")

    # Test learning insights
    insights = brain.get_learning_insights()
    print("\n🧠 Learning Insights:")
    for key, value in insights.items():
        print(f"  {key}: {value}")

    # Save knowledge
    brain.save_knowledge("test_brain.json")
    print("\n✅ Knowledge saved to test_brain.json")

if __name__ == "__main__":
    test_agentdev_brain()
