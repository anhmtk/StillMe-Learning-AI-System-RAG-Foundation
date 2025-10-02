#!/usr/bin/env python3
"""
Test: AgentDev scan_errors() matches ruff output
===============================================

Invariant test to prevent "tô hồng" - AgentDev must report the same count as ruff.
"""

import json
import subprocess
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from agent_dev.core.agentdev import AgentDev


def test_scan_matches_ruff():
    """Test that AgentDev scan_errors() matches ruff output exactly"""
    
    # Run ruff directly
    try:
        result = subprocess.run(
            ["ruff", "check", ".", "--output-format", "json"],
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='replace',
            timeout=120
        )
        
        if result.returncode != 0:
            # If ruff fails, AgentDev should also report failure
            agentdev = AgentDev()
            errors = agentdev.scan_errors()
            
            # Should have system error indicating ruff failed
            assert len(errors) > 0, "AgentDev should report system error when ruff fails"
            assert any(e.rule == "RUFF_FAILED" for e in errors), "Should have RUFF_FAILED error"
            print("PASS: AgentDev correctly reports ruff failure")
            return
        
        # Parse ruff output
        ruff_data = json.loads(result.stdout)
        if not isinstance(ruff_data, list):
            ruff_data = []
        
        ruff_count = len(ruff_data)
        
    except (subprocess.TimeoutExpired, json.JSONDecodeError, Exception) as e:
        # If ruff command fails, AgentDev should also report failure
        agentdev = AgentDev()
        errors = agentdev.scan_errors()
        
        assert len(errors) > 0, "AgentDev should report system error when ruff command fails"
        assert any(e.rule in ["RUFF_FAILED", "TIMEOUT", "EXCEPTION"] for e in errors), "Should have system error"
        print("PASS: AgentDev correctly reports ruff command failure")
        return
    
    # Run AgentDev scan
    agentdev = AgentDev()
    agentdev_errors = agentdev.scan_errors()
    
    # Filter out system errors for count comparison
    real_errors = [e for e in agentdev_errors if not e.rule.startswith("SYSTEM_") and e.rule != "RUFF_FAILED"]
    agentdev_count = len(real_errors)
    
    # Assert counts match
    assert agentdev_count == ruff_count, f"AgentDev count ({agentdev_count}) != ruff count ({ruff_count})"
    
    print(f"PASS: AgentDev count ({agentdev_count}) matches ruff count ({ruff_count})")


if __name__ == "__main__":
    test_scan_matches_ruff()
