"""
StillMe Kill Switch System
Emergency stop mechanism for AI system with audit logging.
"""

import json
import logging
import os
import time
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional

log = logging.getLogger(__name__)

class KillSwitchState(Enum):
    """Kill switch states."""
    DISARMED = "disarmed"
    ARMED = "armed"
    FIRED = "fired"

class KillSwitchAction(Enum):
    """Kill switch actions."""
    ARM = "arm"
    FIRE = "fire"
    DISARM = "disarm"
    STATUS = "status"

class KillSwitchManager:
    """Manages kill switch state and audit logging."""
    
    def __init__(self, state_file: str = "logs/kill_switch_state.json", 
                 audit_file: str = "logs/audit/kill_switch.log"):
        self.state_file = Path(state_file)
        self.audit_file = Path(audit_file)
        
        # Ensure directories exist
        self.state_file.parent.mkdir(parents=True, exist_ok=True)
        self.audit_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Load current state
        self._state = self._load_state()
        
        # Initialize audit logger
        self._setup_audit_logger()
    
    def _load_state(self) -> Dict:
        """Load kill switch state from file."""
        if self.state_file.exists():
            try:
                with open(self.state_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                log.error(f"Failed to load kill switch state: {e}")
        
        # Default state
        return {
            "state": KillSwitchState.DISARMED.value,
            "armed_at": None,
            "fired_at": None,
            "armed_by": None,
            "fired_by": None,
            "reason": None,
            "created_at": datetime.now().isoformat(),
            "last_updated": datetime.now().isoformat()
        }
    
    def _save_state(self):
        """Save kill switch state to file."""
        try:
            self._state["last_updated"] = datetime.now().isoformat()
            with open(self.state_file, 'w') as f:
                json.dump(self._state, f, indent=2)
        except Exception as e:
            log.error(f"Failed to save kill switch state: {e}")
    
    def _setup_audit_logger(self):
        """Setup audit logger for kill switch actions."""
        audit_logger = logging.getLogger("kill_switch_audit")
        audit_logger.setLevel(logging.INFO)
        
        # Remove existing handlers
        for handler in audit_logger.handlers[:]:
            audit_logger.removeHandler(handler)
        
        # Add file handler
        handler = logging.FileHandler(self.audit_file)
        formatter = logging.Formatter(
            '%(asctime)s | %(levelname)s | %(message)s'
        )
        handler.setFormatter(formatter)
        audit_logger.addHandler(handler)
        
        # Prevent propagation to root logger
        audit_logger.propagate = False
        
        self.audit_logger = audit_logger
    
    def _log_action(self, action: KillSwitchAction, actor: str, 
                   reason: Optional[str] = None, result: str = "SUCCESS"):
        """Log kill switch action to audit log."""
        log_entry = {
            "action": action.value,
            "actor": actor,
            "reason": reason,
            "result": result,
            "timestamp": datetime.now().isoformat(),
            "state_before": self._state["state"],
            "state_after": self._state["state"]
        }
        
        self.audit_logger.info(json.dumps(log_entry))
        log.info(f"Kill switch {action.value} by {actor}: {result}")
    
    def arm(self, actor: str, reason: Optional[str] = None) -> Dict:
        """Arm the kill switch."""
        current_state = KillSwitchState(self._state["state"])
        
        if current_state == KillSwitchState.FIRED:
            self._log_action(KillSwitchAction.ARM, actor, reason, "FAILED - Already fired")
            return {
                "success": False,
                "message": "Cannot arm kill switch - already fired",
                "current_state": current_state.value
            }
        
        self._state.update({
            "state": KillSwitchState.ARMED.value,
            "armed_at": datetime.now().isoformat(),
            "armed_by": actor,
            "reason": reason
        })
        
        self._save_state()
        self._log_action(KillSwitchAction.ARM, actor, reason, "SUCCESS")
        
        return {
            "success": True,
            "message": "Kill switch armed successfully",
            "state": KillSwitchState.ARMED.value,
            "armed_at": self._state["armed_at"],
            "armed_by": actor,
            "reason": reason
        }
    
    def fire(self, actor: str, reason: Optional[str] = None) -> Dict:
        """Fire the kill switch (emergency stop)."""
        current_state = KillSwitchState(self._state["state"])
        
        if current_state == KillSwitchState.FIRED:
            self._log_action(KillSwitchAction.FIRE, actor, reason, "FAILED - Already fired")
            return {
                "success": False,
                "message": "Kill switch already fired",
                "current_state": current_state.value
            }
        
        self._state.update({
            "state": KillSwitchState.FIRED.value,
            "fired_at": datetime.now().isoformat(),
            "fired_by": actor,
            "reason": reason
        })
        
        self._save_state()
        self._log_action(KillSwitchAction.FIRE, actor, reason, "SUCCESS")
        
        # Log critical alert
        log.critical(f"🚨 KILL SWITCH FIRED by {actor}: {reason or 'No reason provided'}")
        
        return {
            "success": True,
            "message": "Kill switch fired - system stopped",
            "state": KillSwitchState.FIRED.value,
            "fired_at": self._state["fired_at"],
            "fired_by": actor,
            "reason": reason
        }
    
    def disarm(self, actor: str, reason: Optional[str] = None) -> Dict:
        """Disarm the kill switch."""
        current_state = KillSwitchState(self._state["state"])
        
        if current_state == KillSwitchState.FIRED:
            self._log_action(KillSwitchAction.DISARM, actor, reason, "FAILED - Cannot disarm fired switch")
            return {
                "success": False,
                "message": "Cannot disarm fired kill switch - manual intervention required",
                "current_state": current_state.value
            }
        
        self._state.update({
            "state": KillSwitchState.DISARMED.value,
            "armed_at": None,
            "armed_by": None,
            "reason": None
        })
        
        self._save_state()
        self._log_action(KillSwitchAction.DISARM, actor, reason, "SUCCESS")
        
        return {
            "success": True,
            "message": "Kill switch disarmed successfully",
            "state": KillSwitchState.DISARMED.value,
            "disarmed_at": datetime.now().isoformat(),
            "disarmed_by": actor,
            "reason": reason
        }
    
    def status(self) -> Dict:
        """Get kill switch status."""
        current_state = KillSwitchState(self._state["state"])
        
        return {
            "state": current_state.value,
            "armed_at": self._state.get("armed_at"),
            "fired_at": self._state.get("fired_at"),
            "armed_by": self._state.get("armed_by"),
            "fired_by": self._state.get("fired_by"),
            "reason": self._state.get("reason"),
            "created_at": self._state.get("created_at"),
            "last_updated": self._state.get("last_updated"),
            "is_armed": current_state == KillSwitchState.ARMED,
            "is_fired": current_state == KillSwitchState.FIRED,
            "is_safe": current_state == KillSwitchState.DISARMED
        }
    
    def is_safe(self) -> bool:
        """Check if system is safe to operate."""
        return KillSwitchState(self._state["state"]) == KillSwitchState.DISARMED
    
    def is_armed(self) -> bool:
        """Check if kill switch is armed."""
        return KillSwitchState(self._state["state"]) == KillSwitchState.ARMED
    
    def is_fired(self) -> bool:
        """Check if kill switch is fired."""
        return KillSwitchState(self._state["state"]) == KillSwitchState.FIRED
    
    def get_audit_log(self, limit: int = 100) -> List[Dict]:
        """Get recent audit log entries."""
        if not self.audit_file.exists():
            return []
        
        try:
            entries = []
            with open(self.audit_file, 'r') as f:
                lines = f.readlines()
                
            # Get last N lines
            for line in lines[-limit:]:
                try:
                    # Parse log entry
                    parts = line.strip().split(' | ')
                    if len(parts) >= 3:
                        timestamp = parts[0]
                        level = parts[1]
                        message = ' | '.join(parts[2:])
                        
                        # Try to parse JSON message
                        try:
                            data = json.loads(message)
                            entries.append({
                                "timestamp": timestamp,
                                "level": level,
                                "data": data
                            })
                        except:
                            entries.append({
                                "timestamp": timestamp,
                                "level": level,
                                "message": message
                            })
                except:
                    continue
            
            return entries
        except Exception as e:
            log.error(f"Failed to read audit log: {e}")
            return []

# Global kill switch instance
_kill_switch = None

def get_kill_switch() -> KillSwitchManager:
    """Get global kill switch instance."""
    global _kill_switch
    if _kill_switch is None:
        _kill_switch = KillSwitchManager()
    return _kill_switch

def check_kill_switch() -> bool:
    """Check if system is safe to operate (kill switch not fired)."""
    return get_kill_switch().is_safe()

def require_safe_state(func):
    """Decorator to require safe kill switch state."""
    def wrapper(*args, **kwargs):
        if not check_kill_switch():
            raise RuntimeError("System is not in safe state - kill switch is armed or fired")
        return func(*args, **kwargs)
    return wrapper
