#!/usr/bin/env python3
"""
Test: Zero guard when sources fail
=================================

Prevent "Found 0 errors" when sources actually failed.
"""

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from agent_dev.core.agentdev import AgentDev


def test_zero_guard_when_sources_fail():
    """Test that AgentDev doesn't report 0 errors when sources fail"""

    # Mock subprocess.run to simulate ruff failure
    with patch("agent_dev.core.agentdev.subprocess.run") as mock_run:
        # Simulate ruff command failure
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stdout = ""
        mock_result.stderr = "Some error"
        mock_run.return_value = mock_result

        agentdev = AgentDev()
        errors = agentdev.scan_errors()

        # Should NOT return empty list when source fails
        assert len(errors) > 0, "Should not return empty list when ruff fails"

        # Should have system error indicating failure
        assert any(
            e.rule == "RUFF_FAILED" for e in errors
        ), "Should have RUFF_FAILED error"

        # Should not have "Found 0 errors" behavior
        # Filter out system errors and command failures
        real_errors = [
            e
            for e in errors
            if not e.rule.startswith("SYSTEM_")
            and e.rule
            not in ["RUFF_FAILED", "TIMEOUT", "EXCEPTION", "JSON_PARSE_FAILED"]
        ]
        assert len(real_errors) == 0, "Should have 0 real errors when source fails"

        print("PASS: AgentDev correctly guards against false zero when sources fail")


def test_timeout_guard():
    """Test that timeout is properly reported"""

    with patch("agent_dev.core.agentdev.subprocess.run") as mock_run:
        # Simulate timeout
        import subprocess

        mock_run.side_effect = subprocess.TimeoutExpired("ruff", 120)

        agentdev = AgentDev()
        errors = agentdev.scan_errors()

        # Should report timeout, not 0 errors
        assert len(errors) > 0, "Should not return empty list on timeout"
        assert any(e.rule == "TIMEOUT" for e in errors), "Should have TIMEOUT error"

        print("PASS: AgentDev correctly reports timeout")


if __name__ == "__main__":
    test_zero_guard_when_sources_fail()
    test_timeout_guard()
