"""
Integration Test
----------------
Kiểm tra hoạt động của tất cả module chính trong project.
"""

import pytest
from modules.conversational_core_v1 import ConversationalCore
from modules.layered_memory_v1 import LayeredMemory
from modules.smart_gpt_api_manager_v1 import SmartGPTAPIManager
from modules.token_optimizer_v1 import TokenOptimizer

def test_conversational_core():
    core = ConversationalCore()
    core.add_message("Alice", "Hello")
    history = core.get_history("Alice")
    assert "Hello" in history
    assert isinstance(core._extract_topics([], []), list)

def test_layered_memory():
    mem = LayeredMemory()
    mem.add_memory("test")
    assert "test" in mem.retrieve_memory()

def test_smart_gpt_api_manager():
    mgr = SmartGPTAPIManager()
    result = mgr.simulate_call("Hello")
    assert "Hello" in result

def test_token_optimizer():
    optimizer = TokenOptimizer()
    tokens = ["this", "is", "a", "test", "this"]
    optimized = optimizer.optimize(tokens)
    assert "test" in optimized
    assert optimized.count("this") == 1
