"""
Enterprise Audit Logger - Phase 3

This module provides comprehensive audit logging for clarification events
with privacy protection, compliance features, and structured logging.

Author: StillMe AI Platform
Version: 3.0.0
"""

import json
import logging
import re
import time
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timedelta
import hashlib

logger = logging.getLogger(__name__)

@dataclass
class AuditEvent:
    """Structured audit event for clarification activities"""
    timestamp: float
    trace_id: str
    user_id: str
    session_id: Optional[str]
    event_type: str  # "clarification_request", "clarification_response", "suggestion_used", "error"
    domain: Optional[str]
    mode: str  # "quick", "careful"
    input_type: str  # "text", "code", "image", "mixed"
    question: Optional[str]
    options: Optional[List[str]]
    suggestions: Optional[List[str]]
    success: Optional[bool]
    confidence: float
    reasoning: str
    metadata: Dict[str, Any]
    compliance_flags: List[str]  # "gdpr", "ccpa", "sox", etc.
    redacted: bool = False

class PrivacyFilter:
    """
    Handles privacy filtering and PII redaction for audit logs
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.redact_pii = config.get("redact_pii", True)
        self.privacy_filters = config.get("privacy_filters", [
            "email", "password", "api_key", "token", "secret", 
            "credit_card", "ssn", "phone", "address"
        ])
        
        # Compiled regex patterns for common PII
        self.pii_patterns = {
            "email": re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'),
            "phone": re.compile(r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b'),
            "ssn": re.compile(r'\b\d{3}-\d{2}-\d{4}\b'),
            "credit_card": re.compile(r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b'),
            "api_key": re.compile(r'\b[A-Za-z0-9]{20,}\b'),  # Generic API key pattern
            "password": re.compile(r'\bpassword["\']?\s*(?:[:=]|is)\s*["\']?[^"\'\s]+["\']?', re.IGNORECASE),
            "token": re.compile(r'\btoken["\']?\s*[:=]\s*["\']?[A-Za-z0-9._-]+["\']?', re.IGNORECASE),
            "secret": re.compile(r'\bsecret["\']?\s*[:=]\s*["\']?[A-Za-z0-9._-]+["\']?', re.IGNORECASE)
        }
    
    def _redact_text(self, text: str) -> str:
        """Redact PII from text content"""
        if not self.redact_pii or not text:
            return text
        
        redacted_text = text
        
        for pii_type, pattern in self.pii_patterns.items():
            if pii_type in self.privacy_filters:
                if pii_type == "email":
                    redacted_text = pattern.sub("[EMAIL_REDACTED]", redacted_text)
                elif pii_type == "phone":
                    redacted_text = pattern.sub("[PHONE_REDACTED]", redacted_text)
                elif pii_type == "ssn":
                    redacted_text = pattern.sub("[SSN_REDACTED]", redacted_text)
                elif pii_type == "credit_card":
                    redacted_text = pattern.sub("[CARD_REDACTED]", redacted_text)
                elif pii_type in ["api_key", "password", "token", "secret"]:
                    redacted_text = pattern.sub(f"[{pii_type.upper()}_REDACTED]", redacted_text)
        
        return redacted_text
    
    def _redact_dict(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Recursively redact PII from dictionary data"""
        if not self.redact_pii:
            return data
        
        redacted_data = {}
        
        for key, value in data.items():
            if isinstance(value, str):
                redacted_data[key] = self._redact_text(value)
            elif isinstance(value, dict):
                redacted_data[key] = self._redact_dict(value)
            elif isinstance(value, list):
                redacted_data[key] = [
                    self._redact_text(item) if isinstance(item, str) 
                    else self._redact_dict(item) if isinstance(item, dict)
                    else item for item in value
                ]
            else:
                redacted_data[key] = value
        
        return redacted_data
    
    def redact(self, data: Union[str, Dict[str, Any]]) -> Union[str, Dict[str, Any]]:
        """Main redaction method"""
        if isinstance(data, str):
            return self._redact_text(data)
        elif isinstance(data, dict):
            return self._redact_dict(data)
        else:
            return data

class ComplianceManager:
    """
    Manages compliance requirements for audit logging
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.gdpr_enabled = config.get("compliance", {}).get("gdpr_enabled", False)
        self.ccpa_enabled = config.get("compliance", {}).get("ccpa_enabled", False)
        self.sox_enabled = config.get("compliance", {}).get("sox_enabled", False)
        
        # Compliance requirements
        self.retention_days = config.get("retention_days", 90)
        self.required_fields = config.get("fields", [
            "trace_id", "user_id", "domain", "mode", "question", "success", "timestamp", "input_type"
        ])
    
    def get_compliance_flags(self) -> List[str]:
        """Get list of applicable compliance requirements"""
        flags = []
        
        if self.gdpr_enabled:
            flags.append("gdpr")
        if self.ccpa_enabled:
            flags.append("ccpa")
        if self.sox_enabled:
            flags.append("sox")
        
        return flags
    
    def validate_event(self, event: AuditEvent) -> Dict[str, Any]:
        """Validate audit event against compliance requirements"""
        validation_result = {
            "valid": True,
            "warnings": [],
            "errors": [],
            "compliance_flags": self.get_compliance_flags()
        }
        
        # Check required fields
        event_dict = asdict(event)
        for field in self.required_fields:
            if field not in event_dict or event_dict[field] is None:
                validation_result["warnings"].append(f"Missing required field: {field}")
        
        # GDPR compliance checks
        if self.gdpr_enabled:
            if not event.user_id:
                validation_result["errors"].append("GDPR requires user_id for data processing")
            if not event.trace_id:
                validation_result["errors"].append("GDPR requires trace_id for data tracking")
        
        # SOX compliance checks
        if self.sox_enabled:
            if event.event_type in ["clarification_request", "clarification_response"]:
                if event.success is None:
                    validation_result["warnings"].append("SOX requires success tracking for financial operations")
        
        # CCPA compliance checks
        if self.ccpa_enabled:
            if not event.timestamp:
                validation_result["errors"].append("CCPA requires timestamp for data collection")
        
        validation_result["valid"] = len(validation_result["errors"]) == 0
        
        return validation_result

class AuditLogger:
    """
    Main audit logger for clarification events
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.enabled = config.get("enabled", True)
        self.store_format = config.get("store_format", "jsonl")
        self.log_file = config.get("log_file", "logs/clarification_audit.jsonl")
        self.retention_days = config.get("retention_days", 90)
        
        # Initialize components
        self.privacy_filter = PrivacyFilter(config)
        self.compliance_manager = ComplianceManager(config)
        
        # Ensure log directory exists
        log_path = Path(self.log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Statistics
        self.stats = {
            "total_events": 0,
            "redacted_events": 0,
            "compliance_violations": 0,
            "last_cleanup": time.time()
        }
    
    def _generate_trace_id(self, user_id: str, timestamp: float) -> str:
        """Generate unique trace ID for audit trail"""
        trace_data = f"{user_id}_{timestamp}_{time.time()}"
        return hashlib.sha256(trace_data.encode()).hexdigest()[:16]
    
    def _serialize_event(self, event: AuditEvent) -> str:
        """Serialize audit event to JSON string"""
        try:
            event_dict = asdict(event)
            
            # Redact sensitive information
            if self.privacy_filter.redact_pii:
                event_dict = self.privacy_filter.redact(event_dict)
                event.redacted = True
            
            return json.dumps(event_dict, ensure_ascii=False, separators=(',', ':'))
        except Exception as e:
            logger.error(f"Failed to serialize audit event: {e}")
            return json.dumps({
                "error": "serialization_failed",
                "timestamp": time.time(),
                "trace_id": "unknown"
            })
    
    def _write_event(self, event: AuditEvent):
        """Write audit event to log file"""
        try:
            # Validate event
            validation = self.compliance_manager.validate_event(event)
            if not validation["valid"]:
                self.stats["compliance_violations"] += 1
                logger.warning(f"Compliance validation failed: {validation['errors']}")
                return
            
            # Serialize and write
            event_json = self._serialize_event(event)
            
            with open(self.log_file, 'a', encoding='utf-8') as f:
                f.write(event_json + '\n')
            
            # Update statistics
            self.stats["total_events"] += 1
            if event.redacted:
                self.stats["redacted_events"] += 1
            
            logger.debug(f"Audit event logged: {event.trace_id}")
            
        except Exception as e:
            logger.error(f"Failed to write audit event: {e}")
    
    def _cleanup_old_logs(self):
        """Clean up old log entries based on retention policy"""
        try:
            cutoff_time = time.time() - (self.retention_days * 24 * 60 * 60)
            
            if not Path(self.log_file).exists():
                return
            
            # Read all lines
            with open(self.log_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            # Filter out old entries
            valid_lines = []
            for line in lines:
                try:
                    event_data = json.loads(line.strip())
                    event_timestamp = event_data.get("timestamp", 0)
                    if event_timestamp >= cutoff_time:
                        valid_lines.append(line)
                except json.JSONDecodeError:
                    # Skip malformed lines
                    continue
            
            # Write back valid lines
            with open(self.log_file, 'w', encoding='utf-8') as f:
                f.writelines(valid_lines)
            
            self.stats["last_cleanup"] = time.time()
            logger.info(f"Cleaned up old audit logs, kept {len(valid_lines)} entries")
            
        except Exception as e:
            logger.error(f"Failed to cleanup old logs: {e}")
    
    def log_clarification_request(self, 
                                user_id: str,
                                session_id: Optional[str],
                                input_text: str,
                                input_type: str,
                                domain: Optional[str],
                                mode: str,
                                context: Dict[str, Any] = None) -> str:
        """Log clarification request event"""
        if not self.enabled:
            return "audit_disabled"
        
        try:
            timestamp = time.time()
            trace_id = self._generate_trace_id(user_id, timestamp)
            
            # Redact input text
            redacted_input = self.privacy_filter.redact(input_text)
            
            event = AuditEvent(
                timestamp=timestamp,
                trace_id=trace_id,
                user_id=user_id,
                session_id=session_id,
                event_type="clarification_request",
                domain=domain,
                mode=mode,
                input_type=input_type,
                question=None,
                options=None,
                suggestions=None,
                success=None,
                confidence=0.0,
                reasoning="Clarification request received",
                metadata={
                    "input_length": len(input_text),
                    "redacted_input": redacted_input,
                    "context_keys": list(context.keys()) if context else []
                },
                compliance_flags=self.compliance_manager.get_compliance_flags()
            )
            
            self._write_event(event)
            return trace_id
            
        except Exception as e:
            logger.error(f"Failed to log clarification request: {e}")
            return "error"
    
    def log_clarification_response(self,
                                 trace_id: str,
                                 user_id: str,
                                 question: str,
                                 options: List[str],
                                 suggestions: List[str],
                                 confidence: float,
                                 reasoning: str,
                                 success: bool = None) -> bool:
        """Log clarification response event"""
        if not self.enabled:
            return False
        
        try:
            # Redact question and options
            redacted_question = self.privacy_filter.redact(question)
            redacted_options = [self.privacy_filter.redact(opt) for opt in options] if options else None
            redacted_suggestions = [self.privacy_filter.redact(sug) for sug in suggestions] if suggestions else None
            
            event = AuditEvent(
                timestamp=time.time(),
                trace_id=trace_id,
                user_id=user_id,
                session_id=None,
                event_type="clarification_response",
                domain=None,
                mode=None,
                input_type=None,
                question=redacted_question,
                options=redacted_options,
                suggestions=redacted_suggestions,
                success=success,
                confidence=confidence,
                reasoning=reasoning,
                metadata={
                    "options_count": len(options) if options else 0,
                    "suggestions_count": len(suggestions) if suggestions else 0
                },
                compliance_flags=self.compliance_manager.get_compliance_flags()
            )
            
            self._write_event(event)
            return True
            
        except Exception as e:
            logger.error(f"Failed to log clarification response: {e}")
            return False
    
    def log_suggestion_usage(self,
                           trace_id: str,
                           user_id: str,
                           suggestion: str,
                           category: str,
                           success: bool) -> bool:
        """Log proactive suggestion usage event"""
        if not self.enabled:
            return False
        
        try:
            redacted_suggestion = self.privacy_filter.redact(suggestion)
            
            event = AuditEvent(
                timestamp=time.time(),
                trace_id=trace_id,
                user_id=user_id,
                session_id=None,
                event_type="suggestion_used",
                domain=category,
                mode=None,
                input_type=None,
                question=None,
                options=None,
                suggestions=[redacted_suggestion],
                success=success,
                confidence=1.0 if success else 0.0,
                reasoning=f"Suggestion '{category}' used with success={success}",
                metadata={
                    "suggestion_category": category,
                    "original_suggestion": suggestion
                },
                compliance_flags=self.compliance_manager.get_compliance_flags()
            )
            
            self._write_event(event)
            return True
            
        except Exception as e:
            logger.error(f"Failed to log suggestion usage: {e}")
            return False
    
    def log_error(self,
                 trace_id: str,
                 user_id: str,
                 error_type: str,
                 error_message: str,
                 context: Dict[str, Any] = None) -> bool:
        """Log error event"""
        if not self.enabled:
            return False
        
        try:
            redacted_message = self.privacy_filter.redact(error_message)
            redacted_context = self.privacy_filter.redact(context) if context else {}
            
            event = AuditEvent(
                timestamp=time.time(),
                trace_id=trace_id,
                user_id=user_id,
                session_id=None,
                event_type="error",
                domain=None,
                mode=None,
                input_type=None,
                question=None,
                options=None,
                suggestions=None,
                success=False,
                confidence=0.0,
                reasoning=f"Error occurred: {error_type}",
                metadata={
                    "error_type": error_type,
                    "error_message": redacted_message,
                    "context": redacted_context
                },
                compliance_flags=self.compliance_manager.get_compliance_flags()
            )
            
            self._write_event(event)
            return True
            
        except Exception as e:
            logger.error(f"Failed to log error event: {e}")
            return False
    
    def get_audit_stats(self) -> Dict[str, Any]:
        """Get audit logging statistics"""
        try:
            # Check if cleanup is needed
            if time.time() - self.stats["last_cleanup"] > 24 * 60 * 60:  # 24 hours
                self._cleanup_old_logs()
            
            return {
                "enabled": self.enabled,
                "total_events": self.stats["total_events"],
                "redacted_events": self.stats["redacted_events"],
                "compliance_violations": self.stats["compliance_violations"],
                "redaction_rate": self.stats["redacted_events"] / max(self.stats["total_events"], 1),
                "log_file": self.log_file,
                "retention_days": self.retention_days,
                "compliance_flags": self.compliance_manager.get_compliance_flags(),
                "last_cleanup": datetime.fromtimestamp(self.stats["last_cleanup"]).isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to get audit stats: {e}")
            return {"error": str(e)}
    
    def export_audit_logs(self, 
                         start_time: Optional[float] = None,
                         end_time: Optional[float] = None,
                         user_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Export audit logs with optional filtering"""
        try:
            if not Path(self.log_file).exists():
                return []
            
            exported_events = []
            
            with open(self.log_file, 'r', encoding='utf-8') as f:
                for line in f:
                    try:
                        event_data = json.loads(line.strip())
                        
                        # Apply filters
                        if start_time and event_data.get("timestamp", 0) < start_time:
                            continue
                        if end_time and event_data.get("timestamp", 0) > end_time:
                            continue
                        if user_id and event_data.get("user_id") != user_id:
                            continue
                        
                        exported_events.append(event_data)
                        
                    except json.JSONDecodeError:
                        continue
            
            return exported_events
            
        except Exception as e:
            logger.error(f"Failed to export audit logs: {e}")
            return []
    
    def clear_audit_logs(self) -> bool:
        """Clear all audit logs (use with caution)"""
        try:
            if Path(self.log_file).exists():
                Path(self.log_file).unlink()
            
            # Reset statistics
            self.stats = {
                "total_events": 0,
                "redacted_events": 0,
                "compliance_violations": 0,
                "last_cleanup": time.time()
            }
            
            logger.warning("All audit logs cleared")
            return True
            
        except Exception as e:
            logger.error(f"Failed to clear audit logs: {e}")
            return False
