#!/usr/bin/env python3
"""
Unit tests for Security Thinking Module
Tests security analysis and vulnerability detection
"""

import pytest

# Import AgentDev modules
from agent_dev.core.security_thinking import (
    SecurityLevel,
    SecurityThinking,
)


class TestSecurityThinking:
    """Test cases for Security Thinking Module"""

    def setup_method(self):
        """Set up test fixtures"""
        self.security_thinking = SecurityThinking()

    @pytest.mark.unit
    def test_security_thinking_initialization(self):
        """Test SecurityThinking initialization"""
        assert self.security_thinking is not None
        assert hasattr(self.security_thinking, "analyze_security")
        assert hasattr(self.security_thinking, "detect_vulnerabilities")
        assert hasattr(self.security_thinking, "assess_security_risk")

    @pytest.mark.unit
    def test_security_analysis_basic(self):
        """Test basic security analysis"""
        # Test data
        code_data = {
            "files": ["auth.py", "api.py", "database.py"],
            "lines_of_code": 1000,
            "authentication_methods": ["jwt", "oauth2"],
            "encryption_used": True,
            "input_validation": True,
            "sql_injection_protection": True,
            "xss_protection": True,
        }

        security_result = self.security_thinking.analyze_security(code_data)

        assert isinstance(security_result, dict)
        assert "security_level" in security_result
        assert "vulnerabilities" in security_result
        assert "recommendations" in security_result
        assert "security_score" in security_result

        # Security score should be between 0 and 1
        assert 0.0 <= security_result["security_score"] <= 1.0

    @pytest.mark.unit
    def test_vulnerability_detection(self):
        """Test vulnerability detection"""
        # Code with known vulnerabilities
        vulnerable_code = {
            "files": ["login.py", "user_management.py"],
            "code_snippets": [
                "SELECT * FROM users WHERE username = '"
                + user_input
                + "'",  # SQL injection
                "document.write('<script>alert(\"XSS\")</script>')",  # XSS
                "password = request.form['password']",  # No hashing
                "file = open(user_file, 'r')",  # Path traversal
            ],
            "authentication": False,
            "input_validation": False,
            "encryption": False,
        }

        vulnerabilities = self.security_thinking.detect_vulnerabilities(vulnerable_code)

        assert isinstance(vulnerabilities, list)
        assert len(vulnerabilities) > 0

        # Should detect common vulnerabilities
        vulnerability_types = [v.get("type", "") for v in vulnerabilities]
        assert any("sql_injection" in vtype.lower() for vtype in vulnerability_types)
        assert any("xss" in vtype.lower() for vtype in vulnerability_types)

    @pytest.mark.unit
    def test_security_level_assessment(self):
        """Test security level assessment"""
        # High security code
        secure_code = {
            "files": ["secure_auth.py", "encrypted_storage.py"],
            "authentication": True,
            "authorization": True,
            "encryption": True,
            "input_validation": True,
            "output_encoding": True,
            "secure_headers": True,
            "https_only": True,
            "session_security": True,
        }

        security_level = self.security_thinking.assess_security_level(secure_code)

        assert isinstance(security_level, SecurityLevel)
        assert security_level in [
            SecurityLevel.LOW,
            SecurityLevel.MEDIUM,
            SecurityLevel.HIGH,
            SecurityLevel.CRITICAL,
        ]

    @pytest.mark.unit
    def test_owasp_vulnerability_analysis(self):
        """Test OWASP vulnerability analysis"""
        # OWASP Top 10 vulnerabilities
        owasp_data = {
            "injection_vulnerabilities": True,
            "broken_authentication": True,
            "sensitive_data_exposure": True,
            "xml_external_entities": True,
            "broken_access_control": True,
            "security_misconfiguration": True,
            "cross_site_scripting": True,
            "insecure_deserialization": True,
            "known_vulnerabilities": True,
            "insufficient_logging": True,
        }

        owasp_result = self.security_thinking.analyze_owasp_vulnerabilities(owasp_data)

        assert "owasp_score" in owasp_result
        assert "critical_vulnerabilities" in owasp_result
        assert "high_vulnerabilities" in owasp_result
        assert "medium_vulnerabilities" in owasp_result
        assert "low_vulnerabilities" in owasp_result

        # Should detect multiple OWASP vulnerabilities
        assert owasp_result["critical_vulnerabilities"] > 0
        assert owasp_result["owasp_score"] < 0.5  # Low security score

    @pytest.mark.unit
    def test_security_best_practices_check(self):
        """Test security best practices check"""
        # Code following best practices
        best_practices_code = {
            "files": ["secure_app.py"],
            "authentication": True,
            "authorization": True,
            "input_validation": True,
            "output_encoding": True,
            "encryption_at_rest": True,
            "encryption_in_transit": True,
            "secure_headers": True,
            "error_handling": True,
            "logging": True,
            "monitoring": True,
        }

        practices_result = self.security_thinking.check_best_practices(
            best_practices_code
        )

        assert "practices_followed" in practices_result
        assert "practices_missing" in practices_result
        assert "compliance_score" in practices_result

        # Should have high compliance score
        assert practices_result["compliance_score"] > 0.8
        assert len(practices_result["practices_followed"]) > len(
            practices_result["practices_missing"]
        )

    @pytest.mark.unit
    def test_security_risk_assessment(self):
        """Test security risk assessment"""
        # High-risk scenario
        high_risk_data = {
            "public_facing": True,
            "handles_pii": True,
            "financial_data": True,
            "admin_access": True,
            "external_integrations": True,
            "third_party_dependencies": True,
            "legacy_code": True,
            "no_security_review": True,
        }

        risk_result = self.security_thinking.assess_security_risk(high_risk_data)

        assert "risk_level" in risk_result
        assert "risk_factors" in risk_result
        assert "mitigation_strategies" in risk_result
        assert "priority_actions" in risk_result

        # Should identify high risk
        assert risk_result["risk_level"] in ["high", "critical"]
        assert len(risk_result["risk_factors"]) > 0
        assert len(risk_result["priority_actions"]) > 0

    @pytest.mark.unit
    def test_security_recommendations(self):
        """Test security recommendations generation"""
        # Vulnerable code scenario
        vulnerable_data = {
            "files": ["insecure_app.py"],
            "vulnerabilities": [
                {"type": "sql_injection", "severity": "high"},
                {"type": "xss", "severity": "medium"},
                {"type": "csrf", "severity": "medium"},
            ],
            "missing_practices": [
                "input_validation",
                "output_encoding",
                "csrf_protection",
            ],
        }

        recommendations = self.security_thinking.generate_security_recommendations(
            vulnerable_data
        )

        assert isinstance(recommendations, list)
        assert len(recommendations) > 0

        # Should provide specific recommendations
        recommendation_text = " ".join(recommendations).lower()
        assert (
            "input validation" in recommendation_text
            or "sql injection" in recommendation_text
        )
        assert "output encoding" in recommendation_text or "xss" in recommendation_text

    @pytest.mark.unit
    def test_security_thinking_deterministic(self):
        """Test that security thinking is deterministic"""
        code_data = {
            "files": ["auth.py", "api.py"],
            "authentication": True,
            "encryption": True,
            "input_validation": True,
        }

        # Run analysis multiple times
        result1 = self.security_thinking.analyze_security(code_data)
        result2 = self.security_thinking.analyze_security(code_data)

        # Results should be identical
        assert abs(result1["security_score"] - result2["security_score"]) < 0.001
        assert result1["security_level"] == result2["security_level"]
        assert result1["vulnerabilities"] == result2["vulnerabilities"]

    @pytest.mark.unit
    def test_security_thinking_performance(self):
        """Test security thinking performance"""
        import time

        code_data = {
            "files": ["large_app.py"] * 100,  # Large codebase
            "lines_of_code": 50000,
            "authentication": True,
            "encryption": True,
            "input_validation": True,
        }

        start_time = time.time()
        result = self.security_thinking.analyze_security(code_data)
        end_time = time.time()

        # Should complete within reasonable time
        assert (end_time - start_time) < 2.0  # Less than 2 seconds

    @pytest.mark.unit
    def test_empty_input_handling(self):
        """Test handling of empty or invalid inputs"""
        # Test with empty data
        empty_data = {}

        with pytest.raises((ValueError, KeyError)):
            self.security_thinking.analyze_security(empty_data)

        # Test with None
        with pytest.raises((ValueError, TypeError)):
            self.security_thinking.analyze_security(None)

    @pytest.mark.unit
    def test_security_thinking_edge_cases(self):
        """Test edge cases for security thinking"""
        # Very large codebase
        large_codebase = {
            "files": ["file" + str(i) + ".py" for i in range(10000)],
            "lines_of_code": 1000000,
            "authentication": False,
            "encryption": False,
            "input_validation": False,
        }

        result = self.security_thinking.analyze_security(large_codebase)

        # Should handle large codebases
        assert result["security_score"] < 0.5  # Low security score
        assert len(result["vulnerabilities"]) > 0
        assert result["security_level"] in ["low", "medium"]


# ko dùng # type: ignore và ko dùng comment out để che giấu lỗi
