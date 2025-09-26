"""
Privacy manager for StillMe AI Framework.
Handles privacy modes, data retention, and user data deletion.
"""

import logging
import json
import os
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class PrivacyMode(Enum):
    """Privacy modes for data handling."""
    STRICT = "strict"
    BALANCED = "balanced"
    PERMISSIVE = "permissive"


@dataclass
class PrivacyConfig:
    """Configuration for privacy management."""
    mode: PrivacyMode
    memory_retention_days: int
    opt_in_memory_storage: bool
    redact_pii: bool
    data_deletion_endpoint: str
    audit_logging: bool
    anonymize_logs: bool


class PrivacyManager:
    """Manager for privacy and data protection."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.mode = PrivacyMode(self.config.get("mode", "balanced"))
        self.memory_retention_days = self.config.get("memory_retention_days", 30)
        self.opt_in_memory_storage = self.config.get("opt_in_memory_storage", False)
        self.redact_pii = self.config.get("redact_pii", True)
        self.data_deletion_endpoint = self.config.get("data_deletion_endpoint", "/data/delete")
        self.audit_logging = self.config.get("audit_logging", True)
        self.anonymize_logs = self.config.get("anonymize_logs", True)
        
        # Privacy configurations for different modes
        self.privacy_configs = {
            PrivacyMode.STRICT: PrivacyConfig(
                mode=PrivacyMode.STRICT,
                memory_retention_days=0,  # No memory storage
                opt_in_memory_storage=True,
                redact_pii=True,
                data_deletion_endpoint="/data/delete",
                audit_logging=True,
                anonymize_logs=True
            ),
            PrivacyMode.BALANCED: PrivacyConfig(
                mode=PrivacyMode.BALANCED,
                memory_retention_days=30,
                opt_in_memory_storage=False,
                redact_pii=True,
                data_deletion_endpoint="/data/delete",
                audit_logging=True,
                anonymize_logs=False
            ),
            PrivacyMode.PERMISSIVE: PrivacyConfig(
                mode=PrivacyMode.PERMISSIVE,
                memory_retention_days=90,
                opt_in_memory_storage=False,
                redact_pii=False,
                data_deletion_endpoint="/data/delete",
                audit_logging=False,
                anonymize_logs=False
            )
        }
    
    def get_privacy_config(self) -> PrivacyConfig:
        """Get the current privacy configuration."""
        return self.privacy_configs[self.mode]
    
    def set_privacy_mode(self, mode: Union[PrivacyMode, str]):
        """Set the privacy mode."""
        if isinstance(mode, str):
            mode = PrivacyMode(mode)
        
        self.mode = mode
        logger.info(f"Privacy mode set to: {mode.value}")
    
    def can_store_memory(self, user_id: Optional[str] = None, opt_in: bool = False) -> bool:
        """Check if memory can be stored for a user."""
        config = self.get_privacy_config()
        
        if config.memory_retention_days == 0:
            return False
        
        if config.opt_in_memory_storage and not opt_in:
            return False
        
        return True
    
    def should_redact_pii(self) -> bool:
        """Check if PII should be redacted."""
        config = self.get_privacy_config()
        return config.redact_pii
    
    def should_audit_log(self) -> bool:
        """Check if audit logging should be enabled."""
        config = self.get_privacy_config()
        return config.audit_logging
    
    def should_anonymize_logs(self) -> bool:
        """Check if logs should be anonymized."""
        config = self.get_privacy_config()
        return config.anonymize_logs
    
    def get_memory_retention_days(self) -> int:
        """Get the memory retention period in days."""
        config = self.get_privacy_config()
        return config.memory_retention_days
    
    def get_data_deletion_endpoint(self) -> str:
        """Get the data deletion endpoint."""
        config = self.get_privacy_config()
        return config.data_deletion_endpoint
    
    def redact_pii_data(self, data: Any) -> Any:
        """Redact PII from data."""
        if not self.should_redact_pii():
            return data
        
        if isinstance(data, str):
            return self._redact_string(data)
        elif isinstance(data, dict):
            return {k: self.redact_pii_data(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [self.redact_pii_data(item) for item in data]
        else:
            return data
    
    def _redact_string(self, text: str) -> str:
        """Redact PII from a string."""
        import re
        
        # Redact email addresses
        text = re.sub(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', '[REDACTED:EMAIL]', text)
        
        # Redact phone numbers
        text = re.sub(r'\b\d{3}-\d{3}-\d{4}\b', '[REDACTED:PHONE]', text)
        text = re.sub(r'\b\(\d{3}\)\s*\d{3}-\d{4}\b', '[REDACTED:PHONE]', text)
        
        # Redact credit card numbers
        text = re.sub(r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b', '[REDACTED:CREDIT_CARD]', text)
        
        # Redact SSN
        text = re.sub(r'\b\d{3}-\d{2}-\d{4}\b', '[REDACTED:SSN]', text)
        
        # Redact API keys
        text = re.sub(r'sk-[a-zA-Z0-9]{20,}', '[REDACTED:API_KEY]', text)
        text = re.sub(r'pk-[a-zA-Z0-9]{20,}', '[REDACTED:API_KEY]', text)
        
        return text
    
    def anonymize_user_id(self, user_id: str) -> str:
        """Anonymize a user ID for logging."""
        if not self.should_anonymize_logs():
            return user_id
        
        import hashlib
        return hashlib.sha256(user_id.encode()).hexdigest()[:8]
    
    def log_privacy_event(self, event_type: str, user_id: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        """Log a privacy-related event."""
        if not self.should_audit_log():
            return
        
        log_data = {
            "timestamp": datetime.now().isoformat(),
            "event_type": event_type,
            "privacy_mode": self.mode.value,
            "details": details or {}
        }
        
        if user_id:
            log_data["user_id"] = self.anonymize_user_id(user_id)
        
        logger.info(f"PRIVACY_EVENT: {json.dumps(log_data)}")
    
    def validate_data_deletion_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Validate a data deletion request."""
        validation_result = {
            "valid": True,
            "errors": [],
            "warnings": [],
            "privacy_mode": self.mode.value
        }
        
        # Check required fields
        if "user_id" not in request:
            validation_result["errors"].append("Missing required field: user_id")
            validation_result["valid"] = False
        
        # Check confirmation
        if "confirmation" not in request:
            validation_result["errors"].append("Missing required field: confirmation")
            validation_result["valid"] = False
        elif request["confirmation"] != "DELETE MY DATA":
            validation_result["errors"].append("Invalid confirmation text")
            validation_result["valid"] = False
        
        # Privacy mode specific validations
        if self.mode == PrivacyMode.STRICT:
            # Strict mode: require additional confirmation
            if "additional_confirmation" not in request:
                validation_result["warnings"].append("Additional confirmation recommended in strict mode")
        
        return validation_result
    
    def get_privacy_summary(self) -> Dict[str, Any]:
        """Get a summary of the current privacy configuration."""
        config = self.get_privacy_config()
        return {
            "mode": self.mode.value,
            "memory_retention_days": config.memory_retention_days,
            "opt_in_memory_storage": config.opt_in_memory_storage,
            "redact_pii": config.redact_pii,
            "data_deletion_endpoint": config.data_deletion_endpoint,
            "audit_logging": config.audit_logging,
            "anonymize_logs": config.anonymize_logs
        }


# Global privacy manager instance
_privacy_manager: Optional[PrivacyManager] = None


def get_privacy_manager() -> PrivacyManager:
    """Get the global privacy manager instance."""
    global _privacy_manager
    
    if _privacy_manager is None:
        _privacy_manager = PrivacyManager()
    
    return _privacy_manager


def set_privacy_manager(manager: PrivacyManager):
    """Set the global privacy manager instance."""
    global _privacy_manager
    _privacy_manager = manager
