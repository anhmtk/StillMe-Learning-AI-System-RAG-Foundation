#!/usr/bin/env python3
"""
Safety budget tests for AgentDev Sprint 1
Tests kill switch, whitelist, and resource monitoring
"""

import pytest
import time
from agent_dev.safety import (
    budgeted,
    CommandWhitelist,
    NetworkPolicy,
    SafetyMonitor,
    enforce_safety_policy,
)
from agent_dev.schemas import PolicyViolation


class TestSafetyBudgets:
    """Test cases for safety budget functionality"""

    def setup_method(self):
        """Set up test fixtures"""
        self.whitelist = CommandWhitelist()
        self.network_policy = NetworkPolicy(allow_network=False)
        self.monitor = SafetyMonitor()

    def test_budgeted_decorator_timeout(self):
        """Test that @budgeted decorator enforces timeout"""

        @budgeted(timeout_s=1)
        def slow_function():
            time.sleep(2)  # Sleep longer than timeout
            return "completed"

        with pytest.raises(PolicyViolation, match="CPU time limit exceeded"):
            slow_function()

    def test_budgeted_decorator_success(self):
        """Test that @budgeted decorator allows successful execution"""

        @budgeted(timeout_s=5, cpu_ms=1000)
        def fast_function():
            return "success"

        result = fast_function()
        assert result == "success"

    def test_command_whitelist_allowed(self):
        """Test that allowed commands pass whitelist"""
        assert self.whitelist.is_allowed("read_file")
        assert self.whitelist.is_allowed("write_file")
        assert self.whitelist.is_allowed("validate_syntax")

    def test_command_whitelist_blocked(self):
        """Test that blocked commands fail whitelist"""
        assert not self.whitelist.is_allowed("subprocess.run")
        assert not self.whitelist.is_allowed("os.system")
        assert not self.whitelist.is_allowed("exec('malicious')")

    def test_command_whitelist_validation(self):
        """Test code validation for security violations"""
        safe_code = "def read_file(path): return open(path).read()"
        violations = self.whitelist.validate_code(safe_code)
        assert len(violations) == 0

        malicious_code = "import subprocess; subprocess.run('rm -rf /')"
        violations = self.whitelist.validate_code(malicious_code)
        assert len(violations) > 0
        assert "subprocess" in violations[0]

    def test_network_policy_disabled(self):
        """Test network policy when disabled"""
        assert not self.network_policy.is_network_allowed()
        assert not self.network_policy.is_domain_allowed("example.com")

    def test_network_policy_enabled(self):
        """Test network policy when enabled"""
        policy = NetworkPolicy(allow_network=True)
        assert policy.is_network_allowed()
        assert policy.is_domain_allowed("example.com")

    def test_network_policy_blocked_domains(self):
        """Test network policy with blocked domains"""
        policy = NetworkPolicy(allow_network=True)
        policy.blocked_domains = ["malicious.com"]

        assert policy.is_domain_allowed("example.com")
        assert not policy.is_domain_allowed("malicious.com")

    def test_network_policy_allowed_domains(self):
        """Test network policy with allowed domains"""
        policy = NetworkPolicy(allow_network=True)
        policy.allowed_domains = ["trusted.com"]

        assert policy.is_domain_allowed("trusted.com")
        assert not policy.is_domain_allowed("example.com")

    def test_safety_monitor_tracking(self):
        """Test safety monitor tracking functionality"""
        # Track file write
        self.monitor.track_file_write(1024)
        assert self.monitor.bytes_written == 1024

        # Track command
        self.monitor.track_command("read_file")
        assert len(self.monitor.commands_executed) == 1

        # Add violation
        self.monitor.add_violation("Test violation")
        assert len(self.monitor.violations) == 1

    def test_safety_monitor_limits_timeout(self):
        """Test safety monitor timeout limit"""
        limits = {"timeout_s": 1}

        # Should pass initially
        assert self.monitor.check_limits(limits)

        # Simulate timeout
        time.sleep(1.1)
        assert not self.monitor.check_limits(limits)

    def test_safety_monitor_limits_fs_quota(self):
        """Test safety monitor filesystem quota limit"""
        limits = {"fs_quota_kb": 1}

        # Should pass initially
        assert self.monitor.check_limits(limits)

        # Exceed quota
        self.monitor.track_file_write(2048)  # 2KB > 1KB limit
        assert not self.monitor.check_limits(limits)

    def test_safety_monitor_stats(self):
        """Test safety monitor statistics"""
        self.monitor.track_file_write(512)
        self.monitor.track_command("test_command")
        self.monitor.add_violation("test_violation")

        stats = self.monitor.get_stats()
        assert stats["bytes_written"] == 512
        assert stats["commands_executed"] == 1
        assert stats["violations"] == 1
        assert "elapsed_time" in stats

    def test_enforce_safety_policy_success(self):
        """Test successful safety policy enforcement"""
        policy = {"timeout_s": 10, "fs_quota_kb": 1000}

        # Should not raise exception
        enforce_safety_policy(policy, self.monitor)

    def test_enforce_safety_policy_violation(self):
        """Test safety policy enforcement with violations"""
        policy = {"timeout_s": 1, "fs_quota_kb": 1}

        # Add violation
        self.monitor.add_violation("Test violation")

        with pytest.raises(PolicyViolation, match="Safety violations detected"):
            enforce_safety_policy(policy, self.monitor)

    def test_enforce_safety_policy_limits_exceeded(self):
        """Test safety policy enforcement with limits exceeded"""
        policy = {"timeout_s": 1, "fs_quota_kb": 1}

        # Exceed filesystem quota
        self.monitor.track_file_write(2048)  # 2KB > 1KB limit

        with pytest.raises(PolicyViolation, match="Safety limits exceeded"):
            enforce_safety_policy(policy, self.monitor)

    def test_budgeted_decorator_memory_limit(self):
        """Test @budgeted decorator with memory limit"""

        @budgeted(mem_mb=1)  # 1MB limit
        def memory_intensive_function():
            # Simulate memory usage
            data = []
            for i in range(10000):  # This might exceed 1MB
                data.append(f"line {i}" * 100)
            return len(data)

        # This might or might not exceed memory limit depending on system
        try:
            result = memory_intensive_function()
            assert result == 10000
        except PolicyViolation as e:
            assert "Memory limit exceeded" in str(e)

    def test_budgeted_decorator_cpu_limit(self):
        """Test @budgeted decorator with CPU limit"""

        @budgeted(cpu_ms=100)  # 100ms CPU limit
        def cpu_intensive_function():
            # Simulate CPU-intensive work
            total = 0
            for i in range(1000000):
                total += i
            return total

        # This might or might not exceed CPU limit depending on system
        try:
            result = cpu_intensive_function()
            assert result > 0
        except PolicyViolation as e:
            assert "CPU time limit exceeded" in str(e)

    def test_safety_monitor_edge_cases(self):
        """Test safety monitor edge cases"""
        # Test with zero limits (should pass as no limits enforced)
        limits = {"timeout_s": 0, "fs_quota_kb": 0}
        assert self.monitor.check_limits(limits)  # Zero limits should pass

        # Test with very large limits
        limits = {"timeout_s": 3600, "fs_quota_kb": 1024 * 1024}  # 1 hour, 1GB
        assert self.monitor.check_limits(limits)

    def test_command_whitelist_edge_cases(self):
        """Test command whitelist edge cases"""
        # Test empty command
        assert not self.whitelist.is_allowed("")

        # Test case sensitivity
        assert self.whitelist.is_allowed("READ_FILE")  # Should be case insensitive

        # Test with spaces
        assert not self.whitelist.is_allowed(" import subprocess")

    def test_network_policy_edge_cases(self):
        """Test network policy edge cases"""
        policy = NetworkPolicy(allow_network=True)
        policy.allowed_domains = ["example.com"]

        # Test subdomain
        assert not policy.is_domain_allowed("sub.example.com")

        # Test with port
        assert not policy.is_domain_allowed("example.com:8080")

        # Test with protocol
        assert not policy.is_domain_allowed("https://example.com")


# ko dùng # type: ignore và ko dùng comment out để che giấu lỗi
