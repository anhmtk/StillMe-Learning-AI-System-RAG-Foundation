"""
Test suite for Enterprise Audit Logger - Phase 3

Tests for AuditLogger, PrivacyFilter, and ComplianceManager
"""

import json
import os
import tempfile
from pathlib import Path

import pytest

from stillme_core.modules.audit_logger import (
    AuditEvent,
    AuditLogger,
    ComplianceManager,
    PrivacyFilter,
)


class TestPrivacyFilter:
    """Test PrivacyFilter functionality"""

    @pytest.fixture
    def privacy_filter(self):
        """Create a PrivacyFilter instance for testing"""
        config = {
            "redact_pii": True,
            "privacy_filters": [
                "email",
                "password",
                "api_key",
                "token",
                "secret",
                "credit_card",
                "ssn",
            ],
        }
        return PrivacyFilter(config)

    def test_privacy_filter_initialization(self, privacy_filter):
        """Test PrivacyFilter initialization"""
        assert privacy_filter is not None
        assert privacy_filter.redact_pii is True
        assert "email" in privacy_filter.privacy_filters
        assert "password" in privacy_filter.privacy_filters
        assert len(privacy_filter.pii_patterns) > 0

    def test_redact_email(self, privacy_filter):
        """Test email redaction"""
        text = "Contact me at john.doe@example.com for more info"
        redacted = privacy_filter.redact(text)

        assert "[EMAIL_REDACTED]" in redacted
        assert "john.doe@example.com" not in redacted

    def test_redact_phone(self, privacy_filter):
        """Test phone number redaction"""
        text = "Call me at 555-123-4567 or 555.123.4567"
        redacted = privacy_filter.redact(text)

        assert "[PHONE_REDACTED]" in redacted
        assert "555-123-4567" not in redacted
        assert "555.123.4567" not in redacted

    def test_redact_ssn(self, privacy_filter):
        """Test SSN redaction"""
        text = "My SSN is 123-45-6789"
        redacted = privacy_filter.redact(text)

        assert "[SSN_REDACTED]" in redacted
        assert "123-45-6789" not in redacted

    def test_redact_credit_card(self, privacy_filter):
        """Test credit card redaction"""
        text = "Card number: 1234-5678-9012-3456"
        redacted = privacy_filter.redact(text)

        assert "[CARD_REDACTED]" in redacted
        assert "1234-5678-9012-3456" not in redacted

    def test_redact_api_key(self, privacy_filter):
        """Test API key redaction"""
        text = "API key: sk-1234567890abcdef1234567890abcdef"
        redacted = privacy_filter.redact(text)

        assert "[API_KEY_REDACTED]" in redacted
        assert "sk-1234567890abcdef1234567890abcdef" not in redacted

    def test_redact_password(self, privacy_filter):
        """Test password redaction"""
        text = 'password: "secret123"'
        redacted = privacy_filter.redact(text)

        assert "[PASSWORD_REDACTED]" in redacted
        assert "secret123" not in redacted

    def test_redact_token(self, privacy_filter):
        """Test token redaction"""
        text = 'token: "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9"'
        redacted = privacy_filter.redact(text)

        assert "[TOKEN_REDACTED]" in redacted
        assert "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9" not in redacted

    def test_redact_dict(self, privacy_filter):
        """Test dictionary redaction"""
        data = {
            "user": "john@example.com",
            "password": "secret123",
            "info": {"email": "jane@example.com", "phone": "555-123-4567"},
        }
        redacted = privacy_filter.redact(data)

        assert redacted["user"] == "[EMAIL_REDACTED]"
        assert redacted["password"] == "[PASSWORD_REDACTED]"
        assert redacted["info"]["email"] == "[EMAIL_REDACTED]"
        assert redacted["info"]["phone"] == "[PHONE_REDACTED]"

    def test_redact_list(self, privacy_filter):
        """Test list redaction"""
        data = ["john@example.com", "jane@example.com", "normal text"]
        redacted = privacy_filter.redact(data)

        assert redacted[0] == "[EMAIL_REDACTED]"
        assert redacted[1] == "[EMAIL_REDACTED]"
        assert redacted[2] == "normal text"

    def test_redact_disabled(self, privacy_filter):
        """Test redaction when disabled"""
        privacy_filter.redact_pii = False
        text = "Contact me at john@example.com"
        redacted = privacy_filter.redact(text)

        assert redacted == text
        assert "john@example.com" in redacted

    def test_redact_empty_input(self, privacy_filter):
        """Test redaction with empty input"""
        assert privacy_filter.redact("") == ""
        assert privacy_filter.redact(None) is None
        assert privacy_filter.redact({}) == {}


class TestComplianceManager:
    """Test ComplianceManager functionality"""

    @pytest.fixture
    def compliance_manager(self):
        """Create a ComplianceManager instance for testing"""
        config = {
            "compliance": {
                "gdpr_enabled": True,
                "ccpa_enabled": True,
                "sox_enabled": False,
            },
            "retention_days": 90,
            "fields": [
                "trace_id",
                "user_id",
                "domain",
                "mode",
                "question",
                "success",
                "timestamp",
                "input_type",
            ],
        }
        return ComplianceManager(config)

    def test_compliance_manager_initialization(self, compliance_manager):
        """Test ComplianceManager initialization"""
        assert compliance_manager is not None
        assert compliance_manager.gdpr_enabled is True
        assert compliance_manager.ccpa_enabled is True
        assert compliance_manager.sox_enabled is False
        assert compliance_manager.retention_days == 90
        assert len(compliance_manager.required_fields) == 8

    def test_get_compliance_flags(self, compliance_manager):
        """Test getting compliance flags"""
        flags = compliance_manager.get_compliance_flags()

        assert "gdpr" in flags
        assert "ccpa" in flags
        assert "sox" not in flags

    def test_validate_event_valid(self, compliance_manager):
        """Test event validation with valid event"""
        event = AuditEvent(
            timestamp=1234567890.0,
            trace_id="test_trace_123",
            user_id="test_user",
            session_id="test_session",
            event_type="clarification_request",
            domain="web",
            mode="careful",
            input_type="text",
            question="What do you need?",
            options=["option1", "option2"],
            suggestions=["suggestion1"],
            success=True,
            confidence=0.8,
            reasoning="Test reasoning",
            metadata={"test": "data"},
            compliance_flags=["gdpr", "ccpa"],
        )

        validation = compliance_manager.validate_event(event)

        assert validation["valid"] is True
        assert len(validation["errors"]) == 0
        assert "gdpr" in validation["compliance_flags"]
        assert "ccpa" in validation["compliance_flags"]

    def test_validate_event_missing_user_id(self, compliance_manager):
        """Test event validation with missing user_id (GDPR violation)"""
        event = AuditEvent(
            timestamp=1234567890.0,
            trace_id="test_trace_123",
            user_id=None,  # Missing user_id
            session_id="test_session",
            event_type="clarification_request",
            domain="web",
            mode="careful",
            input_type="text",
            question="What do you need?",
            options=["option1", "option2"],
            suggestions=["suggestion1"],
            success=True,
            confidence=0.8,
            reasoning="Test reasoning",
            metadata={"test": "data"},
            compliance_flags=["gdpr", "ccpa"],
        )

        validation = compliance_manager.validate_event(event)

        assert validation["valid"] is False
        assert len(validation["errors"]) > 0
        assert any("GDPR requires user_id" in error for error in validation["errors"])

    def test_validate_event_missing_trace_id(self, compliance_manager):
        """Test event validation with missing trace_id (GDPR violation)"""
        event = AuditEvent(
            timestamp=1234567890.0,
            trace_id=None,  # Missing trace_id
            user_id="test_user",
            session_id="test_session",
            event_type="clarification_request",
            domain="web",
            mode="careful",
            input_type="text",
            question="What do you need?",
            options=["option1", "option2"],
            suggestions=["suggestion1"],
            success=True,
            confidence=0.8,
            reasoning="Test reasoning",
            metadata={"test": "data"},
            compliance_flags=["gdpr", "ccpa"],
        )

        validation = compliance_manager.validate_event(event)

        assert validation["valid"] is False
        assert any("GDPR requires trace_id" in error for error in validation["errors"])

    def test_validate_event_missing_timestamp(self, compliance_manager):
        """Test event validation with missing timestamp (CCPA violation)"""
        event = AuditEvent(
            timestamp=None,  # Missing timestamp
            trace_id="test_trace_123",
            user_id="test_user",
            session_id="test_session",
            event_type="clarification_request",
            domain="web",
            mode="careful",
            input_type="text",
            question="What do you need?",
            options=["option1", "option2"],
            suggestions=["suggestion1"],
            success=True,
            confidence=0.8,
            reasoning="Test reasoning",
            metadata={"test": "data"},
            compliance_flags=["gdpr", "ccpa"],
        )

        validation = compliance_manager.validate_event(event)

        assert validation["valid"] is False
        assert any("CCPA requires timestamp" in error for error in validation["errors"])


class TestAuditLogger:
    """Test AuditLogger functionality"""

    @pytest.fixture
    def temp_log_file(self):
        """Create a temporary log file for testing"""
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".jsonl") as f:
            temp_file = f.name
        yield temp_file
        # Cleanup
        if os.path.exists(temp_file):
            os.unlink(temp_file)

    @pytest.fixture
    def audit_logger(self, temp_log_file):
        """Create an AuditLogger instance for testing"""
        config = {
            "enabled": True,
            "store_format": "jsonl",
            "log_file": temp_log_file,
            "retention_days": 90,
            "redact_pii": True,
            "privacy_filters": ["email", "password", "api_key"],
            "compliance": {
                "gdpr_enabled": True,
                "ccpa_enabled": True,
                "sox_enabled": False,
            },
        }
        return AuditLogger(config)

    def test_audit_logger_initialization(self, audit_logger):
        """Test AuditLogger initialization"""
        assert audit_logger is not None
        assert audit_logger.enabled is True
        assert audit_logger.store_format == "jsonl"
        assert audit_logger.retention_days == 90
        assert audit_logger.privacy_filter is not None
        assert audit_logger.compliance_manager is not None

    def test_generate_trace_id(self, audit_logger):
        """Test trace ID generation"""
        user_id = "test_user"
        timestamp = 1234567890.0

        trace_id = audit_logger._generate_trace_id(user_id, timestamp)

        assert trace_id is not None
        assert len(trace_id) == 16  # MD5 hash truncated to 16 chars
        assert isinstance(trace_id, str)

    def test_serialize_event(self, audit_logger):
        """Test event serialization"""
        event = AuditEvent(
            timestamp=1234567890.0,
            trace_id="test_trace_123",
            user_id="test_user",
            session_id="test_session",
            event_type="clarification_request",
            domain="web",
            mode="careful",
            input_type="text",
            question="What do you need?",
            options=["option1", "option2"],
            suggestions=["suggestion1"],
            success=True,
            confidence=0.8,
            reasoning="Test reasoning",
            metadata={"test": "data"},
            compliance_flags=["gdpr", "ccpa"],
        )

        serialized = audit_logger._serialize_event(event)

        assert isinstance(serialized, str)
        # Should be valid JSON
        parsed = json.loads(serialized)
        assert parsed["trace_id"] == "test_trace_123"
        assert parsed["user_id"] == "test_user"
        assert parsed["event_type"] == "clarification_request"

    def test_log_clarification_request(self, audit_logger):
        """Test logging clarification request"""
        user_id = "test_user"
        session_id = "test_session"
        input_text = "Build a web application"
        input_type = "text"
        domain = "web"
        mode = "careful"
        context = {"user_id": user_id, "session_id": session_id}

        trace_id = audit_logger.log_clarification_request(
            user_id=user_id,
            session_id=session_id,
            input_text=input_text,
            input_type=input_type,
            domain=domain,
            mode=mode,
            context=context,
        )

        assert trace_id is not None
        assert trace_id != "audit_disabled"
        assert audit_logger.stats["total_events"] == 1

        # Check that log file was created and contains the event
        log_path = Path(audit_logger.log_file)
        assert log_path.exists()

        with open(log_path) as f:
            lines = f.readlines()
            assert len(lines) == 1

            event_data = json.loads(lines[0])
            assert event_data["trace_id"] == trace_id
            assert event_data["user_id"] == user_id
            assert event_data["event_type"] == "clarification_request"
            assert event_data["domain"] == domain
            assert event_data["mode"] == mode

    def test_log_clarification_response(self, audit_logger):
        """Test logging clarification response"""
        trace_id = "test_trace_123"
        user_id = "test_user"
        question = "What type of application do you want to build?"
        options = ["Web app", "Mobile app", "Desktop app"]
        suggestions = ["Use React", "Use Flutter", "Use Electron"]
        confidence = 0.8
        reasoning = "Generated based on user input"
        success = True

        result = audit_logger.log_clarification_response(
            trace_id=trace_id,
            user_id=user_id,
            question=question,
            options=options,
            suggestions=suggestions,
            confidence=confidence,
            reasoning=reasoning,
            success=success,
        )

        assert result is True
        assert audit_logger.stats["total_events"] == 1

        # Check log file
        log_path = Path(audit_logger.log_file)
        with open(log_path) as f:
            lines = f.readlines()
            assert len(lines) == 1

            event_data = json.loads(lines[0])
            assert event_data["trace_id"] == trace_id
            assert event_data["user_id"] == user_id
            assert event_data["event_type"] == "clarification_response"
            assert event_data["question"] == question
            assert event_data["options"] == options
            assert event_data["suggestions"] == suggestions
            assert event_data["success"] == success

    def test_log_suggestion_usage(self, audit_logger):
        """Test logging suggestion usage"""
        trace_id = "test_trace_123"
        user_id = "test_user"
        suggestion = "Use React for web development"
        category = "ux"
        success = True

        result = audit_logger.log_suggestion_usage(
            trace_id=trace_id,
            user_id=user_id,
            suggestion=suggestion,
            category=category,
            success=success,
        )

        assert result is True
        assert audit_logger.stats["total_events"] == 1

        # Check log file
        log_path = Path(audit_logger.log_file)
        with open(log_path) as f:
            lines = f.readlines()
            assert len(lines) == 1

            event_data = json.loads(lines[0])
            assert event_data["trace_id"] == trace_id
            assert event_data["user_id"] == user_id
            assert event_data["event_type"] == "suggestion_used"
            assert event_data["domain"] == category
            assert event_data["suggestions"] == [suggestion]
            assert event_data["success"] == success

    def test_log_error(self, audit_logger):
        """Test logging error event"""
        trace_id = "test_trace_123"
        user_id = "test_user"
        error_type = "validation_error"
        error_message = "Invalid input format"
        context = {"input": "test input", "error_details": "malformed"}

        result = audit_logger.log_error(
            trace_id=trace_id,
            user_id=user_id,
            error_type=error_type,
            error_message=error_message,
            context=context,
        )

        assert result is True
        assert audit_logger.stats["total_events"] == 1

        # Check log file
        log_path = Path(audit_logger.log_file)
        with open(log_path) as f:
            lines = f.readlines()
            assert len(lines) == 1

            event_data = json.loads(lines[0])
            assert event_data["trace_id"] == trace_id
            assert event_data["user_id"] == user_id
            assert event_data["event_type"] == "error"
            assert event_data["success"] is False
            assert event_data["metadata"]["error_type"] == error_type
            assert event_data["metadata"]["error_message"] == error_message

    def test_log_with_pii_redaction(self, audit_logger):
        """Test logging with PII redaction"""
        user_id = "test_user"
        input_text = "Contact me at john@example.com with password secret123"

        audit_logger.log_clarification_request(
            user_id=user_id,
            session_id="test_session",
            input_text=input_text,
            input_type="text",
            domain="web",
            mode="careful",
        )

        # Check that PII was redacted in the log
        log_path = Path(audit_logger.log_file)
        with open(log_path) as f:
            lines = f.readlines()
            event_data = json.loads(lines[0])

            # Original input should be redacted
            redacted_input = event_data["metadata"]["redacted_input"]
            assert "[EMAIL_REDACTED]" in redacted_input
            assert "[PASSWORD_REDACTED]" in redacted_input
            assert "john@example.com" not in redacted_input
            assert "secret123" not in redacted_input

    def test_get_audit_stats(self, audit_logger):
        """Test getting audit statistics"""
        # Log some events
        audit_logger.log_clarification_request(
            user_id="user1",
            session_id="session1",
            input_text="test1",
            input_type="text",
            domain="web",
            mode="careful",
        )
        audit_logger.log_clarification_request(
            user_id="user2",
            session_id="session2",
            input_text="test2",
            input_type="text",
            domain="data",
            mode="quick",
        )

        stats = audit_logger.get_audit_stats()

        assert stats["enabled"] is True
        assert stats["total_events"] == 2
        assert stats["redacted_events"] == 0  # No PII in test inputs
        assert stats["compliance_violations"] == 0
        assert stats["redaction_rate"] == 0.0
        assert stats["log_file"] == audit_logger.log_file
        assert stats["retention_days"] == 90
        assert "gdpr" in stats["compliance_flags"]
        assert "ccpa" in stats["compliance_flags"]

    def test_export_audit_logs(self, audit_logger):
        """Test exporting audit logs"""
        # Log some events
        audit_logger.log_clarification_request(
            user_id="user1",
            session_id="session1",
            input_text="test1",
            input_type="text",
            domain="web",
            mode="careful",
        )
        audit_logger.log_clarification_request(
            user_id="user2",
            session_id="session2",
            input_text="test2",
            input_type="text",
            domain="data",
            mode="quick",
        )

        # Export all logs
        all_logs = audit_logger.export_audit_logs()
        assert len(all_logs) == 2

        # Export logs for specific user
        user1_logs = audit_logger.export_audit_logs(user_id="user1")
        assert len(user1_logs) == 1
        assert user1_logs[0]["user_id"] == "user1"

        # Export logs with time filter
        import time

        current_time = time.time()
        recent_logs = audit_logger.export_audit_logs(start_time=current_time - 3600)
        assert len(recent_logs) == 2  # Both logs are recent

    def test_clear_audit_logs(self, audit_logger):
        """Test clearing audit logs"""
        # Log some events
        audit_logger.log_clarification_request(
            user_id="user1",
            session_id="session1",
            input_text="test1",
            input_type="text",
            domain="web",
            mode="careful",
        )

        # Verify log file exists and has content
        log_path = Path(audit_logger.log_file)
        assert log_path.exists()
        assert audit_logger.stats["total_events"] == 1

        # Clear logs
        result = audit_logger.clear_audit_logs()
        assert result is True

        # Verify log file is deleted and stats are reset
        assert not log_path.exists()
        assert audit_logger.stats["total_events"] == 0
        assert audit_logger.stats["redacted_events"] == 0
        assert audit_logger.stats["compliance_violations"] == 0

    def test_audit_logger_disabled(self, temp_log_file):
        """Test audit logger when disabled"""
        config = {"enabled": False, "log_file": temp_log_file}
        disabled_logger = AuditLogger(config)

        trace_id = disabled_logger.log_clarification_request(
            user_id="test_user",
            session_id="test_session",
            input_text="test",
            input_type="text",
            domain="web",
            mode="careful",
        )

        assert trace_id == "audit_disabled"
        assert disabled_logger.stats["total_events"] == 0

        # Log file should not exist
        assert not Path(temp_log_file).exists()


class TestAuditIntegration:
    """Integration tests for audit logging"""

    @pytest.fixture
    def temp_log_file(self):
        """Create a temporary log file for testing"""
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".jsonl") as f:
            temp_file = f.name
        yield temp_file
        if os.path.exists(temp_file):
            os.unlink(temp_file)

    @pytest.fixture
    def full_audit_system(self, temp_log_file):
        """Create a full audit system for testing"""
        config = {
            "enabled": True,
            "store_format": "jsonl",
            "log_file": temp_log_file,
            "retention_days": 90,
            "redact_pii": True,
            "privacy_filters": ["email", "password", "api_key", "token", "secret"],
            "compliance": {
                "gdpr_enabled": True,
                "ccpa_enabled": True,
                "sox_enabled": False,
            },
        }
        return AuditLogger(config)

    def test_full_workflow_clarification_request_response(self, full_audit_system):
        """Test complete workflow: request -> response"""
        user_id = "test_user"
        session_id = "test_session"

        # Log clarification request
        trace_id = full_audit_system.log_clarification_request(
            user_id=user_id,
            session_id=session_id,
            input_text="Build a web application with user authentication",
            input_type="text",
            domain="web",
            mode="careful",
        )

        assert trace_id is not None
        assert full_audit_system.stats["total_events"] == 1

        # Log clarification response
        result = full_audit_system.log_clarification_response(
            trace_id=trace_id,
            user_id=user_id,
            question="What type of web application do you want to build?",
            options=["E-commerce", "Blog", "SaaS", "Portfolio"],
            suggestions=["Use React", "Implement authentication", "Add database"],
            confidence=0.8,
            reasoning="Generated based on web domain and authentication mention",
            success=True,
        )

        assert result is True
        assert full_audit_system.stats["total_events"] == 2

        # Log suggestion usage
        suggestion_result = full_audit_system.log_suggestion_usage(
            trace_id=trace_id,
            user_id=user_id,
            suggestion="Use React",
            category="ux",
            success=True,
        )

        assert suggestion_result is True
        assert full_audit_system.stats["total_events"] == 3

        # Verify all events in log file
        log_path = Path(full_audit_system.log_file)
        with open(log_path) as f:
            lines = f.readlines()
            assert len(lines) == 3

            # Check request event
            request_event = json.loads(lines[0])
            assert request_event["event_type"] == "clarification_request"
            assert request_event["trace_id"] == trace_id
            assert request_event["domain"] == "web"

            # Check response event
            response_event = json.loads(lines[1])
            assert response_event["event_type"] == "clarification_response"
            assert response_event["trace_id"] == trace_id
            assert response_event["success"] is True

            # Check suggestion event
            suggestion_event = json.loads(lines[2])
            assert suggestion_event["event_type"] == "suggestion_used"
            assert suggestion_event["trace_id"] == trace_id
            assert suggestion_event["domain"] == "ux"

    def test_pii_redaction_workflow(self, full_audit_system):
        """Test PII redaction in complete workflow"""
        user_id = "test_user"
        input_text = (
            "My email is john@example.com and my API key is sk-1234567890abcdef"
        )

        full_audit_system.log_clarification_request(
            user_id=user_id,
            session_id="test_session",
            input_text=input_text,
            input_type="text",
            domain="web",
            mode="careful",
        )

        # Check that PII was redacted
        log_path = Path(full_audit_system.log_file)
        with open(log_path) as f:
            lines = f.readlines()
            event_data = json.loads(lines[0])

            redacted_input = event_data["metadata"]["redacted_input"]
            assert "[EMAIL_REDACTED]" in redacted_input
            assert "[API_KEY_REDACTED]" in redacted_input
            assert "john@example.com" not in redacted_input
            assert "sk-1234567890abcdef" not in redacted_input

    def test_compliance_validation_workflow(self, full_audit_system):
        """Test compliance validation in workflow"""
        # This should pass compliance checks
        trace_id = full_audit_system.log_clarification_request(
            user_id="compliant_user",
            session_id="compliant_session",
            input_text="test input",
            input_type="text",
            domain="web",
            mode="careful",
        )

        assert trace_id is not None
        assert full_audit_system.stats["compliance_violations"] == 0

        # Check compliance flags in logged event
        log_path = Path(full_audit_system.log_file)
        with open(log_path) as f:
            lines = f.readlines()
            event_data = json.loads(lines[0])

            assert "gdpr" in event_data["compliance_flags"]
            assert "ccpa" in event_data["compliance_flags"]
            assert "sox" not in event_data["compliance_flags"]

    def test_error_handling_workflow(self, full_audit_system):
        """Test error handling in workflow"""
        # Log an error
        result = full_audit_system.log_error(
            trace_id="error_trace_123",
            user_id="test_user",
            error_type="processing_error",
            error_message="Failed to process input",
            context={"input": "test", "error_code": 500},
        )

        assert result is True
        assert full_audit_system.stats["total_events"] == 1

        # Verify error event
        log_path = Path(full_audit_system.log_file)
        with open(log_path) as f:
            lines = f.readlines()
            event_data = json.loads(lines[0])

            assert event_data["event_type"] == "error"
            assert event_data["success"] is False
            assert event_data["metadata"]["error_type"] == "processing_error"
            assert event_data["metadata"]["error_message"] == "Failed to process input"

    def test_performance_large_workflow(self, full_audit_system):
        """Test performance with large number of events"""
        import time

        # Log many events
        start_time = time.time()
        for i in range(100):
            full_audit_system.log_clarification_request(
                user_id=f"user_{i}",
                session_id=f"session_{i}",
                input_text=f"test input {i}",
                input_type="text",
                domain="web",
                mode="careful",
            )
        end_time = time.time()

        # Should complete within reasonable time
        assert (end_time - start_time) < 5.0  # 5 seconds max
        assert full_audit_system.stats["total_events"] == 100

        # Verify all events were logged
        log_path = Path(full_audit_system.log_file)
        with open(log_path) as f:
            lines = f.readlines()
            assert len(lines) == 100
