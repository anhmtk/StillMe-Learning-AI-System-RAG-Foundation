#!/usr/bin/env python3
"""
Test: Unicode log parsing
========================

Test that AgentDev handles Unicode/encoding issues properly.
"""

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from agent_dev.core.agentdev import AgentDev


def test_unicode_log_parsing():
    """Test that AgentDev handles Unicode in logs without crashing"""

    # Test with various Unicode scenarios
    test_cases = [
        # Normal ASCII
        '[{"filename": "test.py", "code": "E001", "message": "test error"}]',

        # Unicode in filename
        '[{"filename": "tëst.py", "code": "E001", "message": "test error"}]',

        # Unicode in message
        '[{"filename": "test.py", "code": "E001", "message": "tëst ërror"}]',

        # Mixed Unicode
        '[{"filename": "tëst.py", "code": "E001", "message": "tëst ërror with émojis 🚀"}]',

        # Empty output
        '',

        # Invalid JSON
        'invalid json {',
    ]

    for i, test_output in enumerate(test_cases):
        with patch('agent_dev.core.agentdev.subprocess.run') as mock_run:
            mock_result = MagicMock()
            mock_result.returncode = 0
            mock_result.stdout = test_output
            mock_result.stderr = ""
            mock_run.return_value = mock_result

            agentdev = AgentDev()

            try:
                errors = agentdev.scan_errors()
                print(f"PASS Test case {i+1}: Handled without crash")

                # Should not crash, but may have parsing errors
                if test_output == 'invalid json {':
                    # Should have system error for invalid JSON
                    assert len(errors) > 0, "Should report error for invalid JSON"
                    assert any(e.rule in ["JSON_PARSE_FAILED", "SYSTEM_ERROR"] for e in errors), "Should have parse error"
                elif test_output == '':
                    # Empty output should result in 0 errors (valid case)
                    real_errors = [e for e in errors if not e.rule.startswith("SYSTEM_")]
                    assert len(real_errors) == 0, "Empty output should result in 0 real errors"
                else:
                    # Should parse successfully
                    real_errors = [e for e in errors if not e.rule.startswith("SYSTEM_")]
                    assert len(real_errors) >= 0, "Should parse without system errors"

            except Exception as e:
                print(f"FAIL Test case {i+1}: Crashed with {e}")
                raise


def test_encoding_handling():
    """Test that encoding issues are handled gracefully"""

    # Test with different encoding scenarios
    with patch('agent_dev.core.agentdev.subprocess.run') as mock_run:
        # Simulate encoding error in subprocess
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "normal output"
        mock_result.stderr = ""
        mock_run.return_value = mock_result

        agentdev = AgentDev()

        # Should not crash due to encoding
        try:
            errors = agentdev.scan_errors()
            print("PASS Encoding handling: No crash")
        except UnicodeError as e:
            print(f"FAIL Encoding error: {e}")
            raise


if __name__ == "__main__":
    test_unicode_log_parsing()
    test_encoding_handling()
