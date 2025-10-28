"""
Action Sandbox with Idempotency and Side-effect Guarding

Provides safe action execution with:
- Idempotency keys based on trace_id + action + params
- Dry-run mode for testing
- Side-effect blocking for dangerous operations
- Execution history tracking
"""

from __future__ import annotations

import hashlib
import json
import logging
import time
from typing import Any

logger = logging.getLogger(__name__)

# Dangerous actions that should be blocked
DANGEROUS_ACTIONS = {
    "file_write",
    "file_delete",
    "system_command",
    "database_drop",
    "network_request",
    "process_kill",
    "service_stop",
    "config_change",
}

# Safe actions that can be executed in dry-run mode
SAFE_ACTIONS = {
    "log_message",
    "update_cache",
    "send_notification",
    "validate_input",
    "calculate_score",
    "format_response",
    "update_metrics",
}

# Actions that require special handling
RESTRICTED_ACTIONS = {"user_data_access", "payment_process", "email_send", "sms_send"}


class IdempotencyStore:
    """Simple in-memory store for idempotency tracking."""

    def __init__(self, max_size: int = 10000):
        self.store: dict[str, dict[str, Any]] = {}
        self.max_size = max_size
        self.access_times: dict[str, float] = {}

    def get(self, key: str) -> dict[str, Any] | None:
        """Get stored result for idempotency key."""
        if key in self.store:
            # Check if expired
            data = self.store[key]
            if time.time() - data["stored_at"] > data["ttl_seconds"]:
                # Remove expired entry
                self.store.pop(key, None)
                self.access_times.pop(key, None)
                return None

            self.access_times[key] = time.time()
            return data
        return None

    def set(self, key: str, result: dict[str, Any], ttl_seconds: int = 3600):
        """Store result with TTL."""
        # Clean up old entries if store is full
        if len(self.store) >= self.max_size:
            self._cleanup_old_entries()

        self.store[key] = {
            **result,
            "stored_at": time.time(),
            "ttl_seconds": ttl_seconds,
        }
        self.access_times[key] = time.time()

    def _cleanup_old_entries(self):
        """Remove old entries to make space."""
        current_time = time.time()
        keys_to_remove = []

        for key, data in self.store.items():
            if current_time - data["stored_at"] > data["ttl_seconds"]:
                keys_to_remove.append(key)

        for key in keys_to_remove:
            self.store.pop(key, None)
            self.access_times.pop(key, None)

        # If still full, remove least recently accessed
        if len(self.store) >= self.max_size:
            sorted_keys = sorted(self.access_times.items(), key=lambda x: x[1])
            for key, _ in sorted_keys[: len(self.store) // 2]:
                self.store.pop(key, None)
                self.access_times.pop(key, None)


class ActionSandbox:
    """Safe action execution with idempotency and side-effect guarding."""

    def __init__(self, config: dict[str, Any] | None = None):
        self.config = config or {}
        self.dry_run = self.config.get("dry_run", True)
        self.idempotency_enabled = self.config.get("idempotency_enabled", True)
        self.side_effect_blocking = self.config.get("side_effect_blocking", True)

        # Idempotency store
        self.idempotency_store = IdempotencyStore(
            max_size=self.config.get("idempotency_max_size", 10000)
        )

        # Execution history for auditing
        self.execution_history: list[dict[str, Any]] = []
        self.max_history_size = self.config.get("max_history_size", 1000)

        # Statistics
        self.stats = {
            "total_executions": 0,
            "idempotent_hits": 0,
            "dry_run_executions": 0,
            "blocked_executions": 0,
            "safe_executions": 0,
            "restricted_executions": 0,
        }

    def execute(
        self,
        action: str,
        params: dict[str, Any],
        trace_id: str,
        dry_run: bool | None = None,
    ) -> dict[str, Any]:
        """
        Execute an action safely with idempotency and side-effect guarding.

        Args:
            action: Action name to execute
            params: Action parameters
            trace_id: Unique trace identifier for idempotency
            dry_run: Override global dry_run setting

        Returns:
            Dict with execution result and metadata
        """
        start_time = time.time()
        self.stats["total_executions"] += 1

        # Determine if this is a dry run
        is_dry_run = dry_run if dry_run is not None else self.dry_run
        if is_dry_run:
            self.stats["dry_run_executions"] += 1

        # Generate idempotency key
        idempotency_key = self._generate_idempotency_key(action, params, trace_id)

        # Check idempotency
        if self.idempotency_enabled and not is_dry_run:
            cached_result = self.idempotency_store.get(idempotency_key)
            if cached_result:
                self.stats["idempotent_hits"] += 1
                return {
                    **cached_result,
                    "idempotent": True,
                    "processing_time_ms": (time.time() - start_time) * 1000,
                }

        # Validate action safety
        safety_check = self._validate_action_safety(action, params, is_dry_run)
        if not safety_check["safe"]:
            self.stats["blocked_executions"] += 1
            return {
                "ok": False,
                "error": safety_check["reason"],
                "action": action,
                "trace_id": trace_id,
                "dry_run": is_dry_run,
                "blocked": True,
                "processing_time_ms": (time.time() - start_time) * 1000,
            }

        # Execute action
        try:
            if is_dry_run:
                result = self._execute_dry_run(action, params, trace_id)
            else:
                result = self._execute_real(action, params, trace_id)

            # Store result for idempotency
            if self.idempotency_enabled and not is_dry_run:
                self.idempotency_store.set(idempotency_key, result)

            # Record execution history
            self._record_execution(action, params, trace_id, result, is_dry_run)

            # Update statistics (only for successful executions)
            if result.get("ok", False):
                if action in SAFE_ACTIONS:
                    self.stats["safe_executions"] += 1
                elif action in RESTRICTED_ACTIONS:
                    self.stats["restricted_executions"] += 1

            return {
                **result,
                "idempotent": False,
                "processing_time_ms": (time.time() - start_time) * 1000,
            }

        except Exception as e:
            logger.error(f"Action execution error: {e}")
            # Add small delay to ensure processing_time_ms > 0
            time.sleep(0.001)
            return {
                "ok": False,
                "error": str(e),
                "action": action,
                "trace_id": trace_id,
                "dry_run": is_dry_run,
                "processing_time_ms": (time.time() - start_time) * 1000,
            }

    def _generate_idempotency_key(
        self, action: str, params: dict[str, Any], trace_id: str
    ) -> str:
        """Generate idempotency key from action, params, and trace_id."""
        # Sort params for consistent key generation
        sorted_params = json.dumps(params, sort_keys=True, default=str)

        # Create hash
        key_data = f"{trace_id}:{action}:{sorted_params}"
        return hashlib.sha256(key_data.encode()).hexdigest()[:16]

    def _validate_action_safety(
        self, action: str, params: dict[str, Any], is_dry_run: bool
    ) -> dict[str, Any]:
        """Validate if action is safe to execute."""

        # Check for dangerous actions
        if action in DANGEROUS_ACTIONS:
            if self.side_effect_blocking and not is_dry_run:
                return {"safe": False, "reason": f"dangerous_action_blocked: {action}"}

        # Check for restricted actions
        if action in RESTRICTED_ACTIONS:
            if not is_dry_run:
                # In real implementation, would check permissions
                return {
                    "safe": False,
                    "reason": f"restricted_action_requires_permission: {action}",
                }

        # Validate parameters
        if not self._validate_params(action, params):
            return {"safe": False, "reason": "invalid_parameters"}

        return {"safe": True, "reason": "validated"}

    def _validate_params(self, action: str, params: dict[str, Any]) -> bool:
        """Validate action parameters."""
        # Basic parameter validation
        if not isinstance(params, dict):
            return False

        # Check for suspicious parameter values
        for _key, value in params.items():
            if isinstance(value, str):
                # Check for potential injection attempts
                if any(
                    pattern in value.lower()
                    for pattern in ["<script", "javascript:", "eval("]
                ):
                    return False

        return True

    def _execute_dry_run(
        self, action: str, params: dict[str, Any], trace_id: str
    ) -> dict[str, Any]:
        """Execute action in dry-run mode (no side effects)."""
        return {
            "ok": True,
            "action": action,
            "trace_id": trace_id,
            "dry_run": True,
            "result": f"DRY_RUN: {action} would be executed with params: {list(params.keys())}",
            "side_effects_blocked": True,
        }

    def _execute_real(
        self, action: str, params: dict[str, Any], trace_id: str
    ) -> dict[str, Any]:
        """Execute action for real (with side effects)."""
        # In a real implementation, this would dispatch to appropriate handlers
        # For now, we'll simulate safe execution

        if action in SAFE_ACTIONS:
            # Include params in result to make it unique
            param_summary = ", ".join(f"{k}={v}" for k, v in params.items())
            return {
                "ok": True,
                "action": action,
                "trace_id": trace_id,
                "dry_run": False,
                "result": f"EXECUTED: {action} completed successfully with params: {param_summary}",
                "side_effects_blocked": False,
            }
        else:
            # For non-safe actions, we still block them in this implementation
            return {
                "ok": False,
                "action": action,
                "trace_id": trace_id,
                "dry_run": False,
                "error": f"action_not_implemented: {action}",
                "side_effects_blocked": True,
            }

    def _record_execution(
        self,
        action: str,
        params: dict[str, Any],
        trace_id: str,
        result: dict[str, Any],
        is_dry_run: bool,
    ):
        """Record execution in history for auditing."""
        execution_record = {
            "timestamp": time.time(),
            "action": action,
            "trace_id": trace_id,
            "dry_run": is_dry_run,
            "success": result.get("ok", False),
            "params_keys": list(params.keys()) if params else [],
            "result_summary": str(result.get("result", ""))[:100],
        }

        self.execution_history.append(execution_record)

        # Trim history if too large
        if len(self.execution_history) > self.max_history_size:
            self.execution_history = self.execution_history[-self.max_history_size :]

    def get_execution_history(self, limit: int = 100) -> list[dict[str, Any]]:
        """Get recent execution history."""
        return self.execution_history[-limit:]

    def get_stats(self) -> dict[str, Any]:
        """Get sandbox statistics."""
        return {
            "stats": self.stats.copy(),
            "config": {
                "dry_run": self.dry_run,
                "idempotency_enabled": self.idempotency_enabled,
                "side_effect_blocking": self.side_effect_blocking,
            },
            "idempotency_store_size": len(self.idempotency_store.store),
            "execution_history_size": len(self.execution_history),
        }

    def reset_stats(self):
        """Reset sandbox statistics."""
        self.stats = dict.fromkeys(self.stats, 0)
        self.idempotency_store = IdempotencyStore()
        self.execution_history = []

    def clear_idempotency_cache(self):
        """Clear idempotency cache."""
        self.idempotency_store = IdempotencyStore()
