# tests/test_conversational_core_v1.py
import pytest
from unittest.mock import MagicMock
from modules.conversational_core_v1 import ConversationalCore
import logging

class TestPersonaEngine:
    def __init__(self):
        self.call_count = 0
        
    def generate_response(self, user_input, history):
        self.call_count += 1
        if "error" in user_input:
            raise ValueError("Simulated error")
        return f"Mock response to: {user_input}"

@pytest.fixture
def mock_persona():
    return TestPersonaEngine()

@pytest.fixture
def core(mock_persona):
    return ConversationalCore(mock_persona, max_history=5)

def test_initialization(core, mock_persona):
    assert core.persona_engine == mock_persona
    assert len(core.delay_messages) == len(ConversationalCore.DEFAULT_DELAY_MESSAGES)
    assert core.max_history == 5

def test_normal_response(core, mock_persona):
    response = core.respond("Hello")
    assert "Mock response" in response
    assert mock_persona.call_count == 1
    assert len(core.history) == 2

def test_empty_input(core):
    response = core.respond("   ")
    assert any(phrase in response for phrase in ["nhắc lại", "chưa hiểu"])
    assert len(core.history) == 0

def test_error_handling(core, mock_persona):
    response = core.respond("trigger error")
    assert response in core.delay_messages
    assert mock_persona.call_count == 1

def test_history_management(core):
    for i in range(15):
        core.respond(f"Msg {i}")
    assert len(core.history) == 10  # 5 cặp Q-A

def test_delay_messages(core):
    initial_count = len(core.delay_messages)
    core.add_delay_message("New delay message")
    assert len(core.delay_messages) == initial_count + 1
    
    messages = {core.get_random_delay_message() for _ in range(10)}
    assert len(messages) > 1

def test_reset_history(core):
    core.respond("Test")
    assert len(core.history) > 0
    core.reset_history()
    assert len(core.history) == 0

def test_stress_test(core, mock_persona):
    for i in range(100):
        response = core.respond(f"Stress {i}")
        assert response
    assert mock_persona.call_count == 100
    assert len(core.history) <= 10

def test_fallback_response(core, mock_persona):
    mock_persona.generate_response = lambda *args, **kwargs: ""
    response = core.respond("Test")
    assert any(phrase in response for phrase in ["chưa hiểu", "thêm thông tin"])