"""
Comprehensive Security Test Suite for StillMe AI Framework
========================================================

This test suite covers all security aspects of the StillMe AI Framework:
- Input validation and sanitization
- Authentication and authorization
- Data protection and encryption
- API security
- Vulnerability scanning
- Compliance testing

Author: StillMe AI Framework Team
Version: 1.0.0
Last Updated: 2025-09-26
"""

import pytest
import json
import tempfile
import os
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, Any, List

# Import security modules
from stillme_core.security.security_manager import SecurityManager
from stillme_core.privacy.pii_redactor import PIIRedactor
from stillme_core.api.privacy_endpoints import router as privacy_router
from stillme_core.control.kill_switch import KillSwitch


class TestSecurityComprehensive:
    """Comprehensive security test suite"""
    
    @pytest.fixture
    def security_manager(self):
        """Create SecurityManager instance for testing"""
        config = {
            "security": {
                "enabled": True,
                "encryption": {"algorithm": "AES-256-GCM"},
                "rate_limiting": {"requests_per_minute": 60},
                "input_validation": {"max_input_length": 10000}
            }
        }
        return SecurityManager(config)
    
    @pytest.fixture
    def pii_redactor(self):
        """Create PIIRedactor instance for testing"""
        return PIIRedactor()
    
    @pytest.fixture
    def mock_request(self):
        """Create mock HTTP request"""
        request = Mock()
        request.headers = {"Authorization": "Bearer test-token"}
        request.remote_addr = "192.168.1.100"
        request.method = "POST"
        request.url = "https://api.stillme.ai/chat"
        return request
    
    # Input Validation Tests
    def test_input_validation_sql_injection(self, security_manager):
        """Test SQL injection prevention"""
        malicious_inputs = [
            "'; DROP TABLE users; --",
            "1' OR '1'='1",
            "admin'--",
            "'; INSERT INTO users VALUES ('hacker', 'password'); --"
        ]
        
        for malicious_input in malicious_inputs:
            result = security_manager.validate_input(malicious_input)
            assert result["safe"] == False
            assert "sql_injection" in result["threats"]
    
    def test_input_validation_xss_prevention(self, security_manager):
        """Test XSS prevention"""
        malicious_inputs = [
            "<script>alert('XSS')</script>",
            "javascript:alert('XSS')",
            "<img src=x onerror=alert('XSS')>",
            "<iframe src='javascript:alert(\"XSS\")'></iframe>"
        ]
        
        for malicious_input in malicious_inputs:
            result = security_manager.validate_input(malicious_input)
            assert result["safe"] == False
            assert "xss" in result["threats"]
    
    def test_input_validation_command_injection(self, security_manager):
        """Test command injection prevention"""
        malicious_inputs = [
            "; rm -rf /",
            "| cat /etc/passwd",
            "&& whoami",
            "`id`",
            "$(whoami)"
        ]
        
        for malicious_input in malicious_inputs:
            result = security_manager.validate_input(malicious_input)
            assert result["safe"] == False
            assert "command_injection" in result["threats"]
    
    def test_input_validation_path_traversal(self, security_manager):
        """Test path traversal prevention"""
        malicious_inputs = [
            "../../../etc/passwd",
            "..\\..\\..\\windows\\system32\\config\\sam",
            "/etc/shadow",
            "C:\\Windows\\System32\\config\\SAM"
        ]
        
        for malicious_input in malicious_inputs:
            result = security_manager.validate_input(malicious_input)
            assert result["safe"] == False
            assert "path_traversal" in result["threats"]
    
    def test_input_validation_file_size_limit(self, security_manager):
        """Test file size limit enforcement"""
        large_content = "x" * 20000000  # 20MB
        
        result = security_manager.validate_input(large_content)
        assert result["safe"] == False
        assert "file_too_large" in result["threats"]
    
    # Authentication & Authorization Tests
    def test_authentication_brute_force_protection(self, security_manager):
        """Test brute force attack protection"""
        # Simulate multiple failed login attempts
        for i in range(10):
            result = security_manager.authenticate_user("testuser", "wrongpassword")
            assert result["success"] == False
        
        # Should be locked out after 5 attempts
        result = security_manager.authenticate_user("testuser", "correctpassword")
        assert result["success"] == False
        assert result["locked_out"] == True
    
    def test_authorization_role_based_access(self, security_manager):
        """Test role-based access control"""
        # Test admin access
        admin_result = security_manager.check_permission("admin", "delete_user")
        assert admin_result["allowed"] == True
        
        # Test user access
        user_result = security_manager.check_permission("user", "delete_user")
        assert user_result["allowed"] == False
    
    def test_session_timeout(self, security_manager):
        """Test session timeout enforcement"""
        # Create session
        session = security_manager.create_session("user123")
        assert session["active"] == True
        
        # Simulate timeout
        with patch('time.time', return_value=time.time() + 3700):  # 1 hour + 100 seconds
            result = security_manager.validate_session(session["session_id"])
            assert result["valid"] == False
            assert result["expired"] == True
    
    # Data Protection Tests
    def test_pii_detection_email(self, pii_redactor):
        """Test PII detection for email addresses"""
        text = "Contact me at john.doe@example.com for more information"
        result = pii_redactor.detect_pii(text)
        
        assert len(result["pii_found"]) > 0
        assert "email" in result["pii_found"][0]["type"]
    
    def test_pii_detection_phone(self, pii_redactor):
        """Test PII detection for phone numbers"""
        text = "Call me at +1-555-123-4567 or 555-123-4567"
        result = pii_redactor.detect_pii(text)
        
        assert len(result["pii_found"]) > 0
        assert "phone" in result["pii_found"][0]["type"]
    
    def test_pii_redaction(self, pii_redactor):
        """Test PII redaction functionality"""
        text = "My email is john.doe@example.com and phone is 555-123-4567"
        result = pii_redactor.redact_pii(text)
        
        assert "john.doe@example.com" not in result["redacted_text"]
        assert "555-123-4567" not in result["redacted_text"]
        assert "[REDACTED]" in result["redacted_text"]
    
    def test_encryption_data_at_rest(self, security_manager):
        """Test data encryption at rest"""
        sensitive_data = "This is sensitive information"
        
        # Encrypt data
        encrypted = security_manager.encrypt_data(sensitive_data)
        assert encrypted != sensitive_data
        assert len(encrypted) > len(sensitive_data)
        
        # Decrypt data
        decrypted = security_manager.decrypt_data(encrypted)
        assert decrypted == sensitive_data
    
    def test_encryption_data_in_transit(self, security_manager):
        """Test data encryption in transit"""
        data = {"message": "Sensitive data", "user_id": "12345"}
        
        # Encrypt for transmission
        encrypted = security_manager.encrypt_for_transmission(data)
        assert "encrypted_data" in encrypted
        assert "iv" in encrypted
        assert "tag" in encrypted
        
        # Decrypt after transmission
        decrypted = security_manager.decrypt_after_transmission(encrypted)
        assert decrypted == data
    
    # API Security Tests
    def test_rate_limiting(self, security_manager, mock_request):
        """Test API rate limiting"""
        # Simulate rapid requests
        for i in range(70):  # Exceed rate limit
            result = security_manager.check_rate_limit(mock_request)
            if i < 60:
                assert result["allowed"] == True
            else:
                assert result["allowed"] == False
                assert result["rate_limited"] == True
    
    def test_cors_validation(self, security_manager):
        """Test CORS policy enforcement"""
        # Test allowed origin
        allowed_result = security_manager.validate_cors(
            origin="https://stillme.ai",
            method="GET"
        )
        assert allowed_result["allowed"] == True
        
        # Test disallowed origin
        disallowed_result = security_manager.validate_cors(
            origin="https://malicious-site.com",
            method="GET"
        )
        assert disallowed_result["allowed"] == False
    
    def test_request_size_limit(self, security_manager):
        """Test request size limit enforcement"""
        large_request = {"data": "x" * 2000000}  # 2MB
        
        result = security_manager.validate_request_size(large_request)
        assert result["valid"] == False
        assert result["too_large"] == True
    
    def test_https_enforcement(self, security_manager):
        """Test HTTPS enforcement"""
        # Test HTTP request (should be rejected)
        http_result = security_manager.validate_https("http://api.stillme.ai/chat")
        assert http_result["secure"] == False
        
        # Test HTTPS request (should be allowed)
        https_result = security_manager.validate_https("https://api.stillme.ai/chat")
        assert https_result["secure"] == True
    
    # Vulnerability Scanning Tests
    def test_dependency_vulnerability_scan(self, security_manager):
        """Test dependency vulnerability scanning"""
        result = security_manager.scan_dependencies()
        
        assert "vulnerabilities" in result
        assert "critical" in result["vulnerabilities"]
        assert "high" in result["vulnerabilities"]
        assert "medium" in result["vulnerabilities"]
        assert "low" in result["vulnerabilities"]
    
    def test_code_vulnerability_scan(self, security_manager):
        """Test code vulnerability scanning"""
        # Create temporary file with vulnerable code
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write("""
import os
import subprocess

def vulnerable_function(user_input):
    # SQL injection vulnerability
    query = f"SELECT * FROM users WHERE name = '{user_input}'"
    os.system(f"echo {user_input}")
    subprocess.run(f"ls {user_input}", shell=False)
""")
            temp_file = f.name
        
        try:
            result = security_manager.scan_code_vulnerabilities(temp_file)
            assert "vulnerabilities" in result
            assert len(result["vulnerabilities"]) > 0
        finally:
            os.unlink(temp_file)
    
    def test_secrets_detection(self, security_manager):
        """Test secrets detection in code"""
        # Create temporary file with secrets
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write("""
# Hardcoded secrets (vulnerable)
API_KEY = "sk-1234567890abcdef"
PASSWORD = "admin123"
SECRET_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9"
DATABASE_URL = "postgresql://user:password@localhost/db"
""")
            temp_file = f.name
        
        try:
            result = security_manager.scan_for_secrets(temp_file)
            assert "secrets_found" in result
            assert len(result["secrets_found"]) > 0
        finally:
            os.unlink(temp_file)
    
    # Compliance Tests
    def test_gdpr_compliance_data_export(self, privacy_router):
        """Test GDPR compliance - data export"""
        # This would test the actual API endpoint
        # For now, we'll test the logic
        user_data = {
            "user_id": "12345",
            "email": "user@example.com",
            "conversations": ["Hello", "How are you?"],
            "preferences": {"language": "en", "theme": "dark"}
        }
        
        # Test data export functionality
        export_result = privacy_router.export_user_data("12345")
        assert export_result["success"] == True
        assert "data" in export_result
    
    def test_gdpr_compliance_data_deletion(self, privacy_router):
        """Test GDPR compliance - data deletion"""
        # Test data deletion functionality
        delete_result = privacy_router.delete_user_data("12345")
        assert delete_result["success"] == True
        assert delete_result["deleted"] == True
    
    def test_audit_logging(self, security_manager):
        """Test audit logging functionality"""
        # Test security event logging
        event = {
            "event_type": "authentication_failure",
            "user_id": "testuser",
            "ip_address": "192.168.1.100",
            "timestamp": "2025-09-26T10:00:00Z"
        }
        
        result = security_manager.log_security_event(event)
        assert result["logged"] == True
        assert result["event_id"] is not None
    
    # Kill Switch Tests
    def test_kill_switch_activation(self):
        """Test kill switch activation"""
        # Test normal operation
        assert KillSwitch.is_active() == False
        
        # Activate kill switch
        KillSwitch.activate("Security incident detected")
        assert KillSwitch.is_active() == True
        assert "Security incident detected" in KillSwitch.get_reason()
        
        # Test kill switch check
        with pytest.raises(SystemExit):
            KillSwitch.check_and_exit("System halted by Kill Switch")
    
    def test_kill_switch_deactivation(self):
        """Test kill switch deactivation"""
        # Activate first
        KillSwitch.activate("Test activation")
        assert KillSwitch.is_active() == True
        
        # Deactivate
        KillSwitch.deactivate("Test deactivation")
        assert KillSwitch.is_active() == False
        assert "Test deactivation" in KillSwitch.get_reason()
    
    # Integration Security Tests
    def test_end_to_end_security_flow(self, security_manager, pii_redactor):
        """Test end-to-end security flow"""
        # Simulate a complete user interaction with security checks
        
        # 1. Input validation
        user_input = "Hello, my email is john@example.com"
        validation_result = security_manager.validate_input(user_input)
        assert validation_result["safe"] == True
        
        # 2. PII detection and redaction
        pii_result = pii_redactor.detect_pii(user_input)
        assert len(pii_result["pii_found"]) > 0
        
        redacted_result = pii_redactor.redact_pii(user_input)
        assert "[REDACTED]" in redacted_result["redacted_text"]
        
        # 3. Data encryption
        encrypted_data = security_manager.encrypt_data(redacted_result["redacted_text"])
        assert encrypted_data != redacted_result["redacted_text"]
        
        # 4. Audit logging
        audit_event = {
            "event_type": "data_processing",
            "user_id": "testuser",
            "data_type": "redacted_text",
            "timestamp": "2025-09-26T10:00:00Z"
        }
        audit_result = security_manager.log_security_event(audit_event)
        assert audit_result["logged"] == True
    
    def test_security_incident_response(self, security_manager):
        """Test security incident response"""
        # Simulate security incident
        incident = {
            "incident_type": "suspicious_activity",
            "severity": "high",
            "description": "Multiple failed login attempts",
            "source_ip": "192.168.1.100"
        }
        
        # Test incident detection
        detection_result = security_manager.detect_security_incident(incident)
        assert detection_result["incident_detected"] == True
        
        # Test automated response
        response_result = security_manager.respond_to_incident(incident)
        assert response_result["response_triggered"] == True
        assert "block_ip" in response_result["actions_taken"]
        assert "notify_security_team" in response_result["actions_taken"]


# Security Test Markers
pytestmark = [
    pytest.mark.security,
    pytest.mark.comprehensive,
    pytest.mark.integration
]


# Test Configuration
class TestSecurityConfig:
    """Security test configuration"""
    
    @pytest.fixture(scope="session")
    def security_test_config(self):
        """Security test configuration"""
        return {
            "test_timeout": 300,  # 5 minutes
            "max_concurrent_tests": 10,
            "security_scan_enabled": True,
            "compliance_check_enabled": True,
            "vulnerability_scan_enabled": True
        }
    
    @pytest.fixture(scope="session")
    def security_test_data(self):
        """Security test data"""
        return {
            "malicious_inputs": [
                "<script>alert('XSS')</script>",
                "'; DROP TABLE users; --",
                "../../../etc/passwd",
                "javascript:alert('XSS')"
            ],
            "pii_samples": [
                "john.doe@example.com",
                "555-123-4567",
                "123-45-6789",
                "4111-1111-1111-1111"
            ],
            "test_credentials": {
                "valid_user": "testuser",
                "valid_password": "TestPass123!",
                "invalid_password": "wrongpassword"
            }
        }


# Performance Security Tests
class TestSecurityPerformance:
    """Security performance tests"""
    
    def test_security_scan_performance(self, security_manager):
        """Test security scan performance"""
        import time
        
        start_time = time.time()
        result = security_manager.scan_dependencies()
        end_time = time.time()
        
        scan_duration = end_time - start_time
        assert scan_duration < 30  # Should complete within 30 seconds
        assert result["scan_completed"] == True
    
    def test_encryption_performance(self, security_manager):
        """Test encryption performance"""
        import time
        
        test_data = "x" * 10000  # 10KB of data
        
        start_time = time.time()
        encrypted = security_manager.encrypt_data(test_data)
        encryption_time = time.time() - start_time
        
        start_time = time.time()
        decrypted = security_manager.decrypt_data(encrypted)
        decryption_time = time.time() - start_time
        
        assert encryption_time < 1.0  # Should encrypt within 1 second
        assert decryption_time < 1.0  # Should decrypt within 1 second
        assert decrypted == test_data
