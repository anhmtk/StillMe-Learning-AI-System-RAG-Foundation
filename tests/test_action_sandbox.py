"""
Tests for Action Sandbox with Idempotency

Tests safe action execution, idempotency, dry-run mode, and side-effect blocking.
"""

import time
from unittest.mock import patch

import pytest

from stillme_core.middleware.action_sandbox import ActionSandbox, IdempotencyStore


@pytest.mark.unit
class TestIdempotencyStore:
    """Test idempotency store functionality."""

    def test_store_and_retrieve(self):
        """Test storing and retrieving results."""
        store = IdempotencyStore(max_size=100)

        result = {"ok": True, "result": "test"}
        store.set("key1", result, ttl_seconds=3600)

        retrieved = store.get("key1")
        assert retrieved is not None
        assert retrieved["ok"] is True
        assert retrieved["result"] == "test"
        assert "stored_at" in retrieved

    def test_missing_key_returns_none(self):
        """Test missing key returns None."""
        store = IdempotencyStore()
        assert store.get("nonexistent") is None

    def test_ttl_expiration(self):
        """Test TTL expiration."""
        store = IdempotencyStore()

        result = {"ok": True}
        store.set("key1", result, ttl_seconds=0.1)  # Very short TTL

        # Should be available immediately
        assert store.get("key1") is not None

        # Should expire after TTL
        time.sleep(0.2)
        assert store.get("key1") is None

    def test_max_size_cleanup(self):
        """Test cleanup when store reaches max size."""
        store = IdempotencyStore(max_size=3)

        # Fill store
        for i in range(5):
            store.set(f"key{i}", {"value": i})

        # Should have cleaned up old entries
        assert len(store.store) <= 3


@pytest.mark.unit
class TestActionSandbox:
    """Test Action Sandbox functionality."""

    def test_safe_action_execution(self):
        """Test execution of safe actions."""
        sandbox = ActionSandbox({"dry_run": False})

        result = sandbox.execute(
            action="log_message",
            params={"message": "Hello world"},
            trace_id="test-trace-1",
        )

        assert result["ok"] is True
        assert result["action"] == "log_message"
        assert result["trace_id"] == "test-trace-1"
        assert result["dry_run"] is False
        assert "EXECUTED" in result["result"]

    def test_dangerous_action_blocking(self):
        """Test blocking of dangerous actions."""
        sandbox = ActionSandbox({"dry_run": False, "side_effect_blocking": True})

        result = sandbox.execute(
            action="file_delete", params={"path": "/tmp/test"}, trace_id="test-trace-1"
        )

        assert result["ok"] is False
        assert result["blocked"] is True
        assert "dangerous_action_blocked" in result["error"]

    def test_restricted_action_blocking(self):
        """Test blocking of restricted actions."""
        sandbox = ActionSandbox({"dry_run": False})

        result = sandbox.execute(
            action="user_data_access",
            params={"user_id": "123"},
            trace_id="test-trace-1",
        )

        assert result["ok"] is False
        assert "restricted_action_requires_permission" in result["error"]

    def test_dry_run_mode(self):
        """Test dry-run mode execution."""
        sandbox = ActionSandbox({"dry_run": True})

        result = sandbox.execute(
            action="file_write",
            params={"path": "/tmp/test", "content": "data"},
            trace_id="test-trace-1",
        )

        assert result["ok"] is True
        assert result["dry_run"] is True
        assert "DRY_RUN" in result["result"]
        assert result["side_effects_blocked"] is True

    def test_dry_run_override(self):
        """Test dry-run override parameter."""
        sandbox = ActionSandbox({"dry_run": False})  # Global dry_run = False

        # Override to dry_run = True
        result = sandbox.execute(
            action="file_write",
            params={"path": "/tmp/test"},
            trace_id="test-trace-1",
            dry_run=True,
        )

        assert result["dry_run"] is True
        assert "DRY_RUN" in result["result"]

    def test_idempotency_same_request(self):
        """Test idempotency for identical requests."""
        sandbox = ActionSandbox({"dry_run": False, "idempotency_enabled": True})

        # First execution
        result1 = sandbox.execute(
            action="log_message", params={"message": "Hello"}, trace_id="test-trace-1"
        )

        # Second identical execution
        result2 = sandbox.execute(
            action="log_message", params={"message": "Hello"}, trace_id="test-trace-1"
        )

        assert result1["ok"] is True
        assert result2["ok"] is True
        assert result2["idempotent"] is True
        assert result1["result"] == result2["result"]

    def test_idempotency_different_params(self):
        """Test different params create different results."""
        sandbox = ActionSandbox({"dry_run": False, "idempotency_enabled": True})

        result1 = sandbox.execute(
            action="log_message", params={"message": "Hello"}, trace_id="test-trace-1"
        )

        result2 = sandbox.execute(
            action="log_message", params={"message": "World"}, trace_id="test-trace-1"
        )

        assert result1["ok"] is True
        assert result2["ok"] is True
        assert result2["idempotent"] is False
        assert result1["result"] != result2["result"]

    def test_idempotency_disabled(self):
        """Test idempotency can be disabled."""
        sandbox = ActionSandbox({"dry_run": False, "idempotency_enabled": False})

        result1 = sandbox.execute(
            action="log_message", params={"message": "Hello"}, trace_id="test-trace-1"
        )

        result2 = sandbox.execute(
            action="log_message", params={"message": "Hello"}, trace_id="test-trace-1"
        )

        assert result1["ok"] is True
        assert result2["ok"] is True
        assert result2["idempotent"] is False  # Should not be idempotent

    def test_parameter_validation(self):
        """Test parameter validation."""
        sandbox = ActionSandbox()

        # Invalid parameters (not dict)
        result = sandbox.execute(
            action="log_message",
            params="invalid",  # Should be dict
            trace_id="test-trace-1",
        )

        assert result["ok"] is False
        assert "invalid_parameters" in result["error"]

    def test_suspicious_parameter_blocking(self):
        """Test blocking of suspicious parameters."""
        sandbox = ActionSandbox()

        result = sandbox.execute(
            action="log_message",
            params={"message": "<script>alert('xss')</script>"},
            trace_id="test-trace-1",
        )

        assert result["ok"] is False
        assert "invalid_parameters" in result["error"]

    def test_execution_history(self):
        """Test execution history tracking."""
        sandbox = ActionSandbox()

        # Execute some actions
        sandbox.execute("log_message", {"msg": "test1"}, "trace-1")
        sandbox.execute("log_message", {"msg": "test2"}, "trace-2")

        history = sandbox.get_execution_history()
        assert len(history) == 2
        assert history[0]["trace_id"] == "trace-1"
        assert history[1]["trace_id"] == "trace-2"
        assert history[0]["action"] == "log_message"

    def test_statistics_tracking(self):
        """Test statistics tracking."""
        sandbox = ActionSandbox({"dry_run": False})

        # Execute various actions
        sandbox.execute("log_message", {"msg": "test"}, "trace-1")  # Safe
        sandbox.execute("file_delete", {"path": "/tmp"}, "trace-2")  # Blocked
        sandbox.execute("user_data_access", {"id": "123"}, "trace-3")  # Restricted

        stats = sandbox.get_stats()
        assert stats["stats"]["total_executions"] == 3
        assert stats["stats"]["safe_executions"] == 1
        # Both file_delete and user_data_access are blocked
        assert stats["stats"]["blocked_executions"] == 2
        # restricted_executions is only incremented for successful executions, but these are blocked
        assert stats["stats"]["restricted_executions"] == 0

    def test_reset_statistics(self):
        """Test statistics reset."""
        sandbox = ActionSandbox()

        # Execute some actions
        sandbox.execute("log_message", {"msg": "test"}, "trace-1")

        # Reset
        sandbox.reset_stats()
        stats = sandbox.get_stats()
        assert stats["stats"]["total_executions"] == 0

    def test_clear_idempotency_cache(self):
        """Test clearing idempotency cache."""
        sandbox = ActionSandbox({"idempotency_enabled": True, "dry_run": False})

        # Execute and cache (dry_run=False to enable caching)
        sandbox.execute("log_message", {"msg": "test"}, "trace-1", dry_run=False)
        assert len(sandbox.idempotency_store.store) > 0

        # Clear cache
        sandbox.clear_idempotency_cache()
        assert len(sandbox.idempotency_store.store) == 0


@pytest.mark.unit
class TestActionSandboxIntegration:
    """Integration tests for Action Sandbox."""

    def test_comprehensive_action_types(self):
        """Test comprehensive action type handling."""
        sandbox = ActionSandbox({"dry_run": False})

        test_cases = [
            # Safe actions
            ("log_message", {"msg": "test"}, True),
            ("update_cache", {"key": "value"}, True),
            ("validate_input", {"text": "hello"}, True),
            # Dangerous actions (should be blocked)
            ("file_write", {"path": "/tmp/test"}, False),
            ("system_command", {"cmd": "ls"}, False),
            ("database_drop", {"table": "users"}, False),
            # Restricted actions (should be blocked)
            ("user_data_access", {"user_id": "123"}, False),
            ("payment_process", {"amount": 100}, False),
        ]

        for action, params, expected_success in test_cases:
            result = sandbox.execute(action, params, f"trace-{action}")
            assert result["ok"] == expected_success, f"Failed for action: {action}"

    def test_performance_benchmark(self):
        """Test sandbox performance."""
        sandbox = ActionSandbox({"dry_run": True})

        # Test execution time
        start_time = time.time()
        for i in range(100):
            sandbox.execute("log_message", {"msg": f"test{i}"}, f"trace-{i}")
        elapsed_ms = (time.time() - start_time) * 1000

        # Should be fast (< 100ms for 100 executions)
        assert (
            elapsed_ms < 100
        ), f"Sandbox too slow: {elapsed_ms:.2f}ms for 100 executions"

    def test_idempotency_key_generation(self):
        """Test idempotency key generation consistency."""
        sandbox = ActionSandbox({"idempotency_enabled": True})

        # Same parameters should generate same key
        key1 = sandbox._generate_idempotency_key("action", {"a": 1, "b": 2}, "trace")
        key2 = sandbox._generate_idempotency_key(
            "action", {"b": 2, "a": 1}, "trace"
        )  # Different order
        assert key1 == key2  # Should be same due to sorting

        # Different parameters should generate different keys
        key3 = sandbox._generate_idempotency_key("action", {"a": 1, "b": 3}, "trace")
        assert key1 != key3

    def test_error_handling(self):
        """Test error handling in action execution."""
        sandbox = ActionSandbox()

        # Test with invalid action that might cause exceptions
        with patch.object(
            sandbox, "_execute_real", side_effect=Exception("Test error")
        ):
            result = sandbox.execute("test_action", {}, "trace-1", dry_run=False)

            assert result["ok"] is False
            assert "Test error" in result["error"]
            assert result["processing_time_ms"] > 0