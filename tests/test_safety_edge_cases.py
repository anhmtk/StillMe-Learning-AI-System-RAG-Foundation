"""
Additional edge case tests for Safety Module
Tests to improve coverage for missing lines
"""

import pytest
import time
import tempfile
from pathlib import Path

from agent_dev.safety import (
    SafetyManager,
    CommandWhitelist,
    NetworkPolicy,
    SafetyMonitor,
    enforce_safety_policy,
)
from agent_dev.schemas import SafetyBudget, PolicyViolation


class TestSafetyEdgeCases:
    """Test cases for edge cases and missing coverage in safety module"""

    def setup_method(self):
        """Set up test fixtures"""
        self.temp_dir = Path(tempfile.mkdtemp())

    def teardown_method(self):
        """Clean up test fixtures"""
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    @pytest.mark.unit
    def test_safety_manager_network_policy(self):
        """Test SafetyManager network policy methods"""
        budget = SafetyBudget(cpu_ms=1000, mem_mb=100, fs_quota_kb=100, timeout_s=10)
        manager = SafetyManager(budget, policy_level="balanced")

        # Test network access control
        assert not manager.network_allowed
        manager.set_network_access(True)
        assert manager.network_allowed

        # Should not raise error when network is allowed
        manager.check_network_access()

    @pytest.mark.unit
    def test_safety_manager_error_taxonomy(self):
        """Test SafetyManager error taxonomy classification"""
        budget = SafetyBudget(cpu_ms=100, mem_mb=100, fs_quota_kb=100, timeout_s=1)
        manager = SafetyManager(budget)

        # Test error taxonomy for timeout
        try:

            @manager.budgeted
            def timeout_task():
                time.sleep(0.02)  # Exceed timeout
                return "done"

            timeout_task()
        except PolicyViolation as e:
            error_taxonomy = manager.get_error_taxonomy(e)
            assert error_taxonomy["error_type"] == "POLICY_VIOLATION"
            assert (
                "timeout" in error_taxonomy["message"].lower()
                or "cpu time" in error_taxonomy["message"].lower()
            )
            assert not error_taxonomy["recoverable"]
            assert "Adjust policy" in error_taxonomy["suggested_action"]

    @pytest.mark.unit
    def test_command_whitelist_validation(self):
        """Test CommandWhitelist code validation"""
        whitelist = CommandWhitelist()

        # Test valid code
        valid_code = "def read_file(path): return open(path).read()"
        violations = whitelist.validate_code(valid_code)
        assert len(violations) == 0

        # Test code with blocked patterns
        blocked_code = "import subprocess; subprocess.run(['rm', '-rf', '/'])"
        violations = whitelist.validate_code(blocked_code)
        assert len(violations) > 0
        assert any("subprocess" in v for v in violations)

    @pytest.mark.unit
    def test_network_policy_domains(self):
        """Test NetworkPolicy domain filtering"""
        policy = NetworkPolicy(allow_network=True)

        # Test with allowed domains
        policy.allowed_domains = ["api.example.com", "trusted.org"]
        assert policy.is_domain_allowed("api.example.com")
        assert policy.is_domain_allowed("trusted.org")
        assert not policy.is_domain_allowed("malicious.com")

        # Test with blocked domains
        policy.blocked_domains = ["malicious.com", "spam.org"]
        assert not policy.is_domain_allowed("malicious.com")
        assert not policy.is_domain_allowed("spam.org")
        # Note: safe.com is not in allowed_domains, so it should be blocked
        assert not policy.is_domain_allowed("safe.com")

    @pytest.mark.unit
    def test_safety_monitor_edge_cases(self):
        """Test SafetyMonitor edge cases"""
        monitor = SafetyMonitor()

        # Test with zero limits (should pass)
        limits = {"timeout_s": 0, "fs_quota_kb": 0}
        assert monitor.check_limits(limits)

        # Test with very large limits
        limits = {"timeout_s": 3600, "fs_quota_kb": 1024 * 1024}  # 1 hour, 1GB
        assert monitor.check_limits(limits)

        # Test tracking operations
        monitor.track_file_write(100)
        monitor.track_command("test_cmd")
        monitor.add_violation("test_violation")

        stats = monitor.get_stats()
        assert stats["bytes_written"] == 100
        assert stats["commands_executed"] == 1
        assert stats["violations"] == 1

    @pytest.mark.unit
    def test_enforce_safety_policy_edge_cases(self):
        """Test enforce_safety_policy edge cases"""
        # Test with no violations
        policy = {"timeout_s": 10, "fs_quota_kb": 100}
        monitor = SafetyMonitor()
        monitor.track_file_write(50)
        enforce_safety_policy(policy, monitor)  # Should not raise

        # Test with violations
        monitor.add_violation("test_violation")
        with pytest.raises(PolicyViolation, match="Safety violations detected"):
            enforce_safety_policy(policy, monitor)

    @pytest.mark.unit
    def test_budgeted_decorator_edge_cases(self):
        """Test @budgeted decorator edge cases"""
        from agent_dev.safety import budgeted

        # Test with reasonable timeout and CPU limits
        @budgeted(timeout_s=1, cpu_ms=100)
        def fast_function():
            return "completed"

        # Should complete successfully
        result = fast_function()
        assert result == "completed"

        # Test with larger timeout
        @budgeted(timeout_s=5, cpu_ms=1000)
        def normal_function():
            time.sleep(0.01)
            return "completed"

        result = normal_function()
        assert result == "completed"

    @pytest.mark.unit
    def test_command_whitelist_edge_cases(self):
        """Test CommandWhitelist edge cases"""
        whitelist = CommandWhitelist()

        # Test empty command
        assert not whitelist.is_allowed("")
        assert not whitelist.is_allowed("   ")

        # Test case sensitivity
        assert whitelist.is_allowed("READ_FILE")
        assert whitelist.is_allowed("read_file")
        assert whitelist.is_allowed("Read_File")

        # Test blocked patterns
        assert not whitelist.is_allowed("import os")
        assert not whitelist.is_allowed("subprocess.run")
        assert not whitelist.is_allowed("exec('malicious')")

    @pytest.mark.unit
    def test_safety_manager_fs_quota_tracking(self):
        """Test SafetyManager filesystem quota tracking"""
        budget = SafetyBudget(cpu_ms=1000, mem_mb=100, fs_quota_kb=2)  # 2KB quota
        manager = SafetyManager(budget)

        # Test multiple writes within quota
        manager.check_fs_quota(500)  # 0.5KB
        manager.check_fs_quota(500)  # 1KB total
        assert manager.fs_usage_bytes == 1000

        # Test exceeding quota
        with pytest.raises(PolicyViolation, match="File system usage.*exceeded quota"):
            manager.check_fs_quota(1500)  # Would exceed 2KB quota

    @pytest.mark.unit
    def test_safety_monitor_timeout_edge_cases(self):
        """Test SafetyMonitor timeout edge cases"""
        monitor = SafetyMonitor()

        # Test with zero timeout (should pass as no enforcement)
        limits = {"timeout_s": 0, "fs_quota_kb": 100}
        assert monitor.check_limits(limits)

        # Test with very small timeout - need to wait longer than the timeout
        limits = {"timeout_s": 0.01, "fs_quota_kb": 100}
        time.sleep(0.02)  # Exceed timeout
        assert not monitor.check_limits(limits)
        assert "Timeout exceeded" in monitor.violations[0]["violation"]

    @pytest.mark.unit
    def test_network_policy_edge_cases(self):
        """Test NetworkPolicy edge cases"""
        # Test with network disabled
        policy = NetworkPolicy(allow_network=False)
        assert not policy.is_network_allowed()
        assert not policy.is_domain_allowed("any.domain")

        # Test with empty domain lists
        policy = NetworkPolicy(allow_network=True)
        policy.allowed_domains = []
        policy.blocked_domains = []
        assert policy.is_domain_allowed(
            "any.domain"
        )  # Should allow when no restrictions

        # Test with both allowed and blocked domains
        policy.allowed_domains = ["allowed.com"]
        policy.blocked_domains = ["blocked.com"]
        assert policy.is_domain_allowed("allowed.com")
        assert not policy.is_domain_allowed("blocked.com")
        assert not policy.is_domain_allowed("other.com")  # Not in allowed list
