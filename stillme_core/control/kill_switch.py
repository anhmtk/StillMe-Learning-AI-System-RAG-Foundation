"""
Kill Switch for StillMe AI Framework
====================================

Provides emergency shutdown capabilities for the AI system.
"""

import logging
import os
import time
from dataclasses import dataclass
from enum import Enum
from typing import Any, Optional

logger = logging.getLogger(__name__)


class KillSwitchState(Enum):
    """Kill switch states"""

    ACTIVE = "active"
    INACTIVE = "inactive"
    EMERGENCY = "emergency"


@dataclass
class KillSwitchConfig:
    """Configuration for kill switch"""

    enabled: bool = True
    emergency_threshold: int = 5  # Number of critical errors before emergency mode
    cooldown_seconds: int = 300  # 5 minutes cooldown
    auto_recovery: bool = True
    notification_enabled: bool = True


class KillSwitch:
    """
    Emergency kill switch for StillMe AI Framework

    Provides multiple levels of system shutdown:
    - Soft kill: Disable new requests, allow current to complete
    - Hard kill: Immediate shutdown of all operations
    - Emergency kill: Critical system protection
    """

    def __init__(self, config: Optional[dict[str, Any]] = None):
        self.config = KillSwitchConfig(**(config or {}))
        self.state = KillSwitchState.ACTIVE
        self.error_count = 0
        self.last_error_time = 0
        self.kill_reason = ""
        self.kill_timestamp = 0
        self._logger = logging.getLogger("stillme.killswitch")

        # Load from environment
        self._load_from_env()

        # Initialize state
        self._initialize_state()

    def _load_from_env(self):
        """Load kill switch configuration from environment variables"""
        if os.getenv("STILLME_KILL_SWITCH_ENABLED", "").lower() == "false":
            self.config.enabled = False

        if os.getenv("STILLME_KILL_SWITCH_EMERGENCY_THRESHOLD"):
            try:
                self.config.emergency_threshold = int(
                    os.getenv("STILLME_KILL_SWITCH_EMERGENCY_THRESHOLD")
                )
            except ValueError:
                pass

        if os.getenv("STILLME_KILL_SWITCH_COOLDOWN"):
            try:
                self.config.cooldown_seconds = int(
                    os.getenv("STILLME_KILL_SWITCH_COOLDOWN")
                )
            except ValueError:
                pass

    def _initialize_state(self):
        """Initialize kill switch state"""
        if not self.config.enabled:
            self.state = KillSwitchState.INACTIVE
            return

        # Check for existing kill state
        kill_file = os.getenv("STILLME_KILL_FILE", "/tmp/stillme_kill_switch")
        if os.path.exists(kill_file):
            try:
                with open(kill_file) as f:
                    content = f.read().strip()
                    if content == "EMERGENCY":
                        self.state = KillSwitchState.EMERGENCY
                        self.kill_reason = "Emergency kill switch activated"
                        self.kill_timestamp = os.path.getmtime(kill_file)
                        self._logger.critical(
                            "Emergency kill switch detected from file"
                        )
            except Exception as e:
                self._logger.error(f"Error reading kill switch file: {e}")

    def is_active(self) -> bool:
        """Check if kill switch is active (system should continue)"""
        if not self.config.enabled:
            return True

        if self.state == KillSwitchState.INACTIVE:
            return True

        if self.state == KillSwitchState.EMERGENCY:
            return False

        # Check for cooldown period
        if self.state == KillSwitchState.ACTIVE:
            if self.kill_timestamp > 0:
                elapsed = time.time() - self.kill_timestamp
                if elapsed < self.config.cooldown_seconds:
                    return False
                else:
                    # Auto-recovery after cooldown
                    if self.config.auto_recovery:
                        self._recover()
                        return True

        return self.state == KillSwitchState.ACTIVE

    def soft_kill(self, reason: str = "Manual soft kill"):
        """Soft kill: Disable new requests, allow current to complete"""
        if not self.config.enabled:
            return

        self.state = KillSwitchState.INACTIVE
        self.kill_reason = reason
        self.kill_timestamp = time.time()

        self._logger.warning(f"SOFT KILL ACTIVATED: {reason}")
        self._write_kill_file("SOFT")

        if self.config.notification_enabled:
            self._send_notification(f"Soft kill activated: {reason}")

    def hard_kill(self, reason: str = "Manual hard kill"):
        """Hard kill: Immediate shutdown of all operations"""
        if not self.config.enabled:
            return

        self.state = KillSwitchState.INACTIVE
        self.kill_reason = reason
        self.kill_timestamp = time.time()

        self._logger.critical(f"HARD KILL ACTIVATED: {reason}")
        self._write_kill_file("HARD")

        if self.config.notification_enabled:
            self._send_notification(f"Hard kill activated: {reason}")

    def emergency_kill(self, reason: str = "Emergency protection"):
        """Emergency kill: Critical system protection"""
        if not self.config.enabled:
            return

        self.state = KillSwitchState.EMERGENCY
        self.kill_reason = reason
        self.kill_timestamp = time.time()

        self._logger.critical(f"EMERGENCY KILL ACTIVATED: {reason}")
        self._write_kill_file("EMERGENCY")

        if self.config.notification_enabled:
            self._send_notification(f"EMERGENCY KILL: {reason}")

    def record_error(self, error_type: str = "unknown"):
        """Record an error and check for emergency threshold"""
        if not self.config.enabled:
            return

        self.error_count += 1
        self.last_error_time = time.time()

        self._logger.warning(
            f"Error recorded: {error_type} (count: {self.error_count})"
        )

        # Check for emergency threshold
        if self.error_count >= self.config.emergency_threshold:
            self.emergency_kill(
                f"Emergency threshold reached: {self.error_count} errors"
            )

    def reset_errors(self):
        """Reset error count"""
        self.error_count = 0
        self.last_error_time = 0
        self._logger.info("Error count reset")

    def _recover(self):
        """Recover from kill state"""
        self.state = KillSwitchState.ACTIVE
        self.kill_reason = ""
        self.kill_timestamp = 0
        self.reset_errors()

        self._logger.info("Kill switch recovered - system active")
        self._remove_kill_file()

    def _write_kill_file(self, kill_type: str):
        """Write kill switch state to file"""
        kill_file = os.getenv("STILLME_KILL_FILE", "/tmp/stillme_kill_switch")
        try:
            with open(kill_file, "w") as f:
                f.write(kill_type)
                f.write(f"\n{self.kill_reason}\n")
                f.write(f"{self.kill_timestamp}\n")
        except Exception as e:
            self._logger.error(f"Error writing kill switch file: {e}")

    def _remove_kill_file(self):
        """Remove kill switch file"""
        kill_file = os.getenv("STILLME_KILL_FILE", "/tmp/stillme_kill_switch")
        try:
            if os.path.exists(kill_file):
                os.remove(kill_file)
        except Exception as e:
            self._logger.error(f"Error removing kill switch file: {e}")

    def _send_notification(self, message: str):
        """Send kill switch notification"""
        # In a real implementation, this would send to monitoring systems
        self._logger.critical(f"KILL SWITCH NOTIFICATION: {message}")

        # Could integrate with:
        # - Slack/Discord webhooks
        # - Email notifications
        # - PagerDuty alerts
        # - Custom monitoring systems

    def get_status(self) -> dict[str, Any]:
        """Get current kill switch status"""
        return {
            "enabled": self.config.enabled,
            "state": self.state.value,
            "error_count": self.error_count,
            "last_error_time": self.last_error_time,
            "kill_reason": self.kill_reason,
            "kill_timestamp": self.kill_timestamp,
            "cooldown_remaining": max(
                0, self.config.cooldown_seconds - (time.time() - self.kill_timestamp)
            )
            if self.kill_timestamp > 0
            else 0,
            "auto_recovery": self.config.auto_recovery,
        }

    def manual_activate(self):
        """Manually activate kill switch (for testing)"""
        if not self.config.enabled:
            self._logger.warning("Kill switch is disabled")
            return

        self.soft_kill("Manual activation for testing")

    def manual_deactivate(self):
        """Manually deactivate kill switch"""
        if not self.config.enabled:
            self._logger.warning("Kill switch is disabled")
            return

        self._recover()


# Global kill switch instance
_kill_switch: Optional[KillSwitch] = None


def get_kill_switch() -> KillSwitch:
    """Get global kill switch instance"""
    global _kill_switch
    if _kill_switch is None:
        _kill_switch = KillSwitch()
    return _kill_switch


def check_kill_switch() -> bool:
    """Quick check if kill switch is active"""
    return get_kill_switch().is_active()


def activate_kill_switch(reason: str = "Manual activation"):
    """Activate kill switch"""
    get_kill_switch().soft_kill(reason)


def deactivate_kill_switch():
    """Deactivate kill switch"""
    get_kill_switch().manual_deactivate()
