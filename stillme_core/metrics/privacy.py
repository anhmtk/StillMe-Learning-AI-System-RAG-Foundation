"""
🔒 StillMe Privacy Manager
=========================

Hệ thống bảo vệ privacy và PII cho metrics collection.
Redaction, anonymization, và compliance với GDPR/CCPA.

Tính năng:
- PII detection và redaction
- Data anonymization
- Privacy compliance
- Audit logging
- Configurable policies

Author: StillMe AI Framework
Version: 1.0.0
Date: 2025-09-28
"""

import hashlib
import json
import logging
import re
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Union

logger = logging.getLogger(__name__)

class PIIType(Enum):
    """Types of PII"""
    EMAIL = "email"
    PHONE = "phone"
    NAME = "name"
    ADDRESS = "address"
    SSN = "ssn"
    CREDIT_CARD = "credit_card"
    IP_ADDRESS = "ip_address"
    USER_ID = "user_id"
    SESSION_ID = "session_id"
    API_KEY = "api_key"
    PASSWORD = "password"

@dataclass
class PIIPattern:
    """PII detection pattern"""
    pii_type: PIIType
    pattern: re.Pattern
    replacement: str
    description: str

@dataclass
class PrivacyConfig:
    """Privacy configuration"""
    enable_redaction: bool = True
    enable_anonymization: bool = True
    enable_audit_log: bool = True
    redaction_method: str = "hash"  # hash, mask, remove
    audit_log_path: str = "logs/privacy_audit.log"
    allowed_domains: List[str] = field(default_factory=list)
    blocked_patterns: List[str] = field(default_factory=list)

class PIIRedactor:
    """
    PII detection và redaction system
    
    Tự động phát hiện và xử lý PII trong metrics data
    để đảm bảo privacy compliance.
    """

    def __init__(self, config: Optional[PrivacyConfig] = None):
        self.config = config or PrivacyConfig()
        self.patterns: List[PIIPattern] = []
        self._load_default_patterns()
        self._setup_audit_logging()

        logger.info(f"PIIRedactor initialized with {len(self.patterns)} patterns")

    def _load_default_patterns(self):
        """Load default PII detection patterns"""
        default_patterns = [
            # Email
            PIIPattern(
                pii_type=PIIType.EMAIL,
                pattern=re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'),
                replacement="[EMAIL_REDACTED]",
                description="Email address"
            ),

            # Phone numbers
            PIIPattern(
                pii_type=PIIType.PHONE,
                pattern=re.compile(r'(\+?1[-.\s]?)?\(?([0-9]{3})\)?[-.\s]?([0-9]{3})[-.\s]?([0-9]{4})'),
                replacement="[PHONE_REDACTED]",
                description="Phone number"
            ),

            # IP addresses
            PIIPattern(
                pii_type=PIIType.IP_ADDRESS,
                pattern=re.compile(r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b'),
                replacement="[IP_REDACTED]",
                description="IP address"
            ),

            # Credit card numbers
            PIIPattern(
                pii_type=PIIType.CREDIT_CARD,
                pattern=re.compile(r'\b(?:4[0-9]{12}(?:[0-9]{3})?|5[1-5][0-9]{14}|3[47][0-9]{13}|3[0-9]{13}|6(?:011|5[0-9]{2})[0-9]{12})\b'),
                replacement="[CARD_REDACTED]",
                description="Credit card number"
            ),

            # SSN
            PIIPattern(
                pii_type=PIIType.SSN,
                pattern=re.compile(r'\b(?:[0-9]{3}-[0-9]{2}-[0-9]{4}|[0-9]{9})\b'),
                replacement="[SSN_REDACTED]",
                description="Social Security Number"
            ),

            # API keys (common patterns)
            PIIPattern(
                pii_type=PIIType.API_KEY,
                pattern=re.compile(r'\b(?:sk-|pk-|api_|key_)[A-Za-z0-9]{20,}\b'),
                replacement="[API_KEY_REDACTED]",
                description="API key"
            ),

            # Passwords (basic detection)
            PIIPattern(
                pii_type=PIIType.PASSWORD,
                pattern=re.compile(r'\b(?:password|passwd|pwd)\s*[:=]\s*[^\s]+\b', re.IGNORECASE),
                replacement="[PASSWORD_REDACTED]",
                description="Password field"
            ),

            # User IDs (common patterns)
            PIIPattern(
                pii_type=PIIType.USER_ID,
                pattern=re.compile(r'\b(?:user_id|uid|id)\s*[:=]\s*[A-Za-z0-9_-]+\b', re.IGNORECASE),
                replacement="[USER_ID_REDACTED]",
                description="User ID"
            ),

            # Session IDs
            PIIPattern(
                pii_type=PIIType.SESSION_ID,
                pattern=re.compile(r'\b(?:session_id|sid|session)\s*[:=]\s*[A-Za-z0-9_-]+\b', re.IGNORECASE),
                replacement="[SESSION_ID_REDACTED]",
                description="Session ID"
            )
        ]

        self.patterns = default_patterns

    def _setup_audit_logging(self):
        """Setup audit logging"""
        if self.config.enable_audit_log:
            audit_dir = Path(self.config.audit_log_path).parent
            audit_dir.mkdir(parents=True, exist_ok=True)

    def detect_pii(self, text: str) -> List[Dict[str, Any]]:
        """Detect PII in text"""
        detected = []

        for pattern in self.patterns:
            matches = pattern.pattern.findall(text)
            if matches:
                detected.append({
                    'type': pattern.pii_type.value,
                    'pattern': pattern.description,
                    'matches': len(matches),
                    'replacement': pattern.replacement
                })

        return detected

    def redact_text(self, text: str) -> str:
        """Redact PII from text"""
        if not self.config.enable_redaction:
            return text

        redacted_text = text
        redactions_made = []

        for pattern in self.patterns:
            original_text = redacted_text
            redacted_text = pattern.pattern.sub(pattern.replacement, redacted_text)

            if redacted_text != original_text:
                redactions_made.append({
                    'type': pattern.pii_type.value,
                    'description': pattern.description
                })

        # Log redactions if audit is enabled
        if redactions_made and self.config.enable_audit_log:
            self._log_redaction(redactions_made, text[:100])

        return redacted_text

    def redact_dict(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Redact PII from dictionary"""
        if not self.config.enable_redaction:
            return data

        redacted_data = {}

        for key, value in data.items():
            # Check if key itself contains PII
            redacted_key = self.redact_text(str(key))

            if isinstance(value, str):
                redacted_value = self.redact_text(value)
            elif isinstance(value, dict):
                redacted_value = self.redact_dict(value)
            elif isinstance(value, list):
                redacted_value = [self.redact_text(str(item)) if isinstance(item, str) else item for item in value]
            else:
                redacted_value = value

            redacted_data[redacted_key] = redacted_value

        return redacted_data

    def anonymize_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Anonymize data by hashing sensitive fields"""
        if not self.config.enable_anonymization:
            return data

        anonymized_data = {}

        for key, value in data.items():
            if self._is_sensitive_field(key):
                if isinstance(value, str):
                    anonymized_data[key] = self._hash_value(value)
                else:
                    anonymized_data[key] = value
            else:
                anonymized_data[key] = value

        return anonymized_data

    def _is_sensitive_field(self, field_name: str) -> bool:
        """Check if field name indicates sensitive data"""
        sensitive_patterns = [
            'id', 'key', 'token', 'secret', 'password', 'passwd',
            'email', 'phone', 'address', 'ssn', 'credit', 'card'
        ]

        field_lower = field_name.lower()
        return any(pattern in field_lower for pattern in sensitive_patterns)

    def _hash_value(self, value: str) -> str:
        """Hash a value for anonymization"""
        return hashlib.sha256(value.encode()).hexdigest()[:16]

    def _log_redaction(self, redactions: List[Dict[str, Any]], original_text: str):
        """Log redaction activity"""
        if not self.config.enable_audit_log:
            return

        log_entry = {
            'timestamp': str(datetime.now()),
            'action': 'redaction',
            'redactions': redactions,
            'original_preview': original_text
        }

        try:
            with open(self.config.audit_log_path, 'a', encoding='utf-8') as f:
                f.write(json.dumps(log_entry) + '\n')
        except Exception as e:
            logger.error(f"Failed to write audit log: {e}")

    def get_redaction_stats(self) -> Dict[str, Any]:
        """Get redaction statistics"""
        if not Path(self.config.audit_log_path).exists():
            return {'total_redactions': 0, 'by_type': {}}

        stats = {'total_redactions': 0, 'by_type': {}}

        try:
            with open(self.config.audit_log_path, encoding='utf-8') as f:
                for line in f:
                    try:
                        entry = json.loads(line.strip())
                        if entry.get('action') == 'redaction':
                            stats['total_redactions'] += 1
                            for redaction in entry.get('redactions', []):
                                pii_type = redaction.get('type', 'unknown')
                                stats['by_type'][pii_type] = stats['by_type'].get(pii_type, 0) + 1
                    except json.JSONDecodeError:
                        continue
        except Exception as e:
            logger.error(f"Failed to read audit log: {e}")

        return stats

class PrivacyManager:
    """
    Privacy management system
    
    Orchestrates PII redaction, anonymization, và compliance
    cho toàn bộ metrics collection system.
    """

    def __init__(self, config: Optional[PrivacyConfig] = None):
        self.config = config or PrivacyConfig()
        self.redactor = PIIRedactor(config)

        logger.info("PrivacyManager initialized")

    def process_metrics_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process metrics data for privacy compliance"""
        # Redact PII
        redacted_data = self.redactor.redact_dict(data)

        # Anonymize sensitive data
        anonymized_data = self.redactor.anonymize_data(redacted_data)

        return anonymized_data

    def process_event_data(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process event data for privacy compliance"""
        # Redact PII in event data
        redacted_data = self.redactor.redact_dict(event_data)

        # Anonymize sensitive fields
        anonymized_data = self.redactor.anonymize_data(redacted_data)

        return anonymized_data

    def validate_privacy_compliance(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate privacy compliance of data"""
        compliance_report = {
            'compliant': True,
            'issues': [],
            'recommendations': []
        }

        # Check for PII
        text_data = json.dumps(data)
        detected_pii = self.redactor.detect_pii(text_data)

        if detected_pii:
            compliance_report['compliant'] = False
            compliance_report['issues'].append(f"PII detected: {len(detected_pii)} types")
            compliance_report['recommendations'].append("Enable PII redaction")

        # Check for sensitive fields
        sensitive_fields = []
        for key in data.keys():
            if self.redactor._is_sensitive_field(key):
                sensitive_fields.append(key)

        if sensitive_fields:
            compliance_report['issues'].append(f"Sensitive fields found: {sensitive_fields}")
            compliance_report['recommendations'].append("Consider anonymization")

        return compliance_report

    def get_privacy_summary(self) -> Dict[str, Any]:
        """Get privacy system summary"""
        return {
            'config': {
                'redaction_enabled': self.config.enable_redaction,
                'anonymization_enabled': self.config.enable_anonymization,
                'audit_enabled': self.config.enable_audit_log
            },
            'redaction_stats': self.redactor.get_redaction_stats(),
            'patterns_loaded': len(self.redactor.patterns)
        }

# Global instance
_privacy_manager_instance: Optional[PrivacyManager] = None

def get_privacy_manager() -> PrivacyManager:
    """Get global privacy manager instance"""
    global _privacy_manager_instance
    if _privacy_manager_instance is None:
        _privacy_manager_instance = PrivacyManager()
    return _privacy_manager_instance

def initialize_privacy_manager(config: Optional[PrivacyConfig] = None) -> PrivacyManager:
    """Initialize global privacy manager with config"""
    global _privacy_manager_instance
    _privacy_manager_instance = PrivacyManager(config)
    return _privacy_manager_instance
