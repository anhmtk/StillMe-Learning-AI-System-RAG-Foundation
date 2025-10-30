# tests/test_api_dev_agent.py
import os
import sys

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def test_dev_agent_fast():
    """Test dev-agent fast mode"""
    from api_server import AgentMode, DevAgentRequest, DevAgentResponse

    # Test request model
    request = DevAgentRequest(prompt="Say hello in one sentence.", mode=AgentMode.FAST)

    assert request.prompt == "Say hello in one sentence."
    assert request.mode == AgentMode.FAST
    assert request.params is None

    # Test response model
    response = DevAgentResponse(
        ok=True, mode=AgentMode.FAST, output="Hello!", latency_ms=100.0
    )

    assert response.ok is True
    assert response.mode == AgentMode.FAST
    assert response.output == "Hello!"
    assert response.latency_ms == 100.0
    assert response.error is None


def test_dev_agent_safe():
    """Test dev-agent safe mode"""
    from api_server import AgentMode, DevAgentRequest, DevAgentResponse

    # Test request model with params
    request = DevAgentRequest(
        prompt="Explain how you would plan unit tests for a small Python function.",
        mode=AgentMode.SAFE,
        params={"max_tokens": 256},
    )

    assert (
        request.prompt
        == "Explain how you would plan unit tests for a small Python function."
    )
    assert request.mode == AgentMode.SAFE
    assert request.params == {"max_tokens": 256}

    # Test response model with error
    response = DevAgentResponse(
        ok=False, mode=AgentMode.SAFE, output="", latency_ms=200.0, error="Test error"
    )

    assert response.ok is False
    assert response.mode == AgentMode.SAFE
    assert response.output == ""
    assert response.latency_ms == 200.0
    assert response.error == "Test error"
