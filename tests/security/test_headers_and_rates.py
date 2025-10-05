"""
Security Headers and Rate Limiting Tests
Tests for OWASP ASVS compliance - security headers and rate limiting
"""

import time

import pytest

from stillme_core.security import RateLimiter, SecurityHeaders


class TestSecurityHeaders:
    """Test security headers implementation"""

    @pytest.fixture
    def security_headers(self):
        """Create security headers instance"""
        return SecurityHeaders()

    def test_content_security_policy_header(self, security_headers):
        """Test Content-Security-Policy header"""
        headers = (
            security_headers.get_security_headers()
            if hasattr(security_headers, "get_security_headers")
            else {}
        )

        assert "Content-Security-Policy" in headers
        csp = headers["Content-Security-Policy"]

        # Check for essential CSP directives
        assert "default-src 'self'" in csp
        assert "script-src 'self'" in csp
        assert "style-src 'self'" in csp
        assert "img-src 'self'" in csp
        assert "connect-src 'self'" in csp

    def test_strict_transport_security_header(self, security_headers):
        """Test Strict-Transport-Security header"""
        headers = (
            security_headers.get_security_headers()
            if hasattr(security_headers, "get_security_headers")
            else {}
        )

        assert "Strict-Transport-Security" in headers
        hsts = headers["Strict-Transport-Security"]

        # Check for HSTS directives
        assert "max-age=" in hsts
        assert "includeSubDomains" in hsts
        assert "preload" in hsts

    def test_x_content_type_options_header(self, security_headers):
        """Test X-Content-Type-Options header"""
        headers = (
            security_headers.get_security_headers()
            if hasattr(security_headers, "get_security_headers")
            else {}
        )

        assert "X-Content-Type-Options" in headers
        assert headers["X-Content-Type-Options"] == "nosniff"

    def test_x_frame_options_header(self, security_headers):
        """Test X-Frame-Options header"""
        headers = (
            security_headers.get_security_headers()
            if hasattr(security_headers, "get_security_headers")
            else {}
        )

        assert "X-Frame-Options" in headers
        assert headers["X-Frame-Options"] == "DENY"

    def test_referrer_policy_header(self, security_headers):
        """Test Referrer-Policy header"""
        headers = (
            security_headers.get_security_headers()
            if hasattr(security_headers, "get_security_headers")
            else {}
        )

        assert "Referrer-Policy" in headers
        assert headers["Referrer-Policy"] == "strict-origin-when-cross-origin"

    def test_x_xss_protection_header(self, security_headers):
        """Test X-XSS-Protection header"""
        headers = (
            security_headers.get_security_headers()
            if hasattr(security_headers, "get_security_headers")
            else {}
        )

        assert "X-XSS-Protection" in headers
        assert headers["X-XSS-Protection"] == "1; mode=block"

    def test_permissions_policy_header(self, security_headers):
        """Test Permissions-Policy header"""
        headers = (
            security_headers.get_security_headers()
            if hasattr(security_headers, "get_security_headers")
            else {}
        )

        assert "Permissions-Policy" in headers
        permissions = headers["Permissions-Policy"]

        # Check for essential permissions
        assert "camera=()" in permissions
        assert "microphone=()" in permissions
        assert "geolocation=()" in permissions
        assert "payment=()" in permissions

    def test_cors_headers(self, security_headers):
        """Test CORS headers"""
        headers = security_headers.get_cors_headers()

        assert "Access-Control-Allow-Origin" in headers
        assert "Access-Control-Allow-Methods" in headers
        assert "Access-Control-Allow-Headers" in headers
        assert "Access-Control-Max-Age" in headers

    def test_cors_origin_validation(self, security_headers):
        """Test CORS origin validation"""
        # Test allowed origin
        allowed_origins = ["https://stillme.ai", "https://staging.stillme.ai"]
        headers = security_headers.get_cors_headers(allowed_origins)

        assert "Access-Control-Allow-Origin" in headers

        # Test disallowed origin
        disallowed_origins = ["https://malicious.com"]
        headers = security_headers.get_cors_headers(disallowed_origins)

        # Should not include the disallowed origin
        assert headers["Access-Control-Allow-Origin"] != "https://malicious.com"


class TestRateLimiting:
    """Test rate limiting implementation"""

    @pytest.fixture
    def rate_limiter(self):
        """Create rate limiter instance"""
        return RateLimiter()

    def test_rate_limiter_initialization(self, rate_limiter):
        """Test rate limiter initialization"""
        assert rate_limiter is not None
        assert hasattr(rate_limiter, "check_rate_limit")

    def test_rate_limit_allowed(self, rate_limiter):
        """Test rate limit when within limits"""
        client_id = "test_client"

        # First request should be allowed
        result = rate_limiter.check_rate_limit(client_id, limit=10, window=60)
        assert result["allowed"] is True
        assert result["remaining"] == 9
        assert result["reset_time"] > 0

    def test_rate_limit_exceeded(self, rate_limiter):
        """Test rate limit when exceeded"""
        client_id = "test_client_2"

        # Exceed the rate limit
        for _i in range(11):  # 11 requests with limit of 10
            result = rate_limiter.check_rate_limit(client_id, limit=10, window=60)

        # Last request should be denied
        assert result["allowed"] is False
        assert result["remaining"] == 0
        assert result["reset_time"] > 0

    def test_rate_limit_window_reset(self, rate_limiter):
        """Test rate limit window reset"""
        client_id = "test_client_3"

        # Exceed the rate limit
        for _i in range(11):
            rate_limiter.check_rate_limit(
                client_id, limit=10, window=1
            )  # 1 second window

        # Wait for window to reset
        time.sleep(1.1)

        # New request should be allowed
        result = rate_limiter.check_rate_limit(client_id, limit=10, window=1)
        assert result["allowed"] is True
        assert result["remaining"] == 9

    def test_different_clients_separate_limits(self, rate_limiter):
        """Test that different clients have separate rate limits"""
        client1 = "client_1"
        client2 = "client_2"

        # Both clients should be allowed
        result1 = rate_limiter.check_rate_limit(client1, limit=5, window=60)
        result2 = rate_limiter.check_rate_limit(client2, limit=5, window=60)

        assert result1["allowed"] is True
        assert result2["allowed"] is True
        assert result1["remaining"] == 4
        assert result2["remaining"] == 4

    def test_rate_limit_headers(self, rate_limiter):
        """Test rate limit response headers"""
        client_id = "test_client_4"

        result = rate_limiter.check_rate_limit(client_id, limit=10, window=60)
        headers = rate_limiter.get_rate_limit_headers(result)

        assert "X-RateLimit-Limit" in headers
        assert "X-RateLimit-Remaining" in headers
        assert "X-RateLimit-Reset" in headers
        assert headers["X-RateLimit-Limit"] == "10"
        assert headers["X-RateLimit-Remaining"] == str(result["remaining"])


class TestSecurityIntegration:
    """Test security features integration"""

    def test_security_headers_integration(self):
        """Test security headers integration with web framework"""
        from stillme_core.security import SecurityHeaders

        headers = SecurityHeaders()
        security_headers = headers.get_security_headers()

        # Verify all required headers are present
        required_headers = [
            "Content-Security-Policy",
            "Strict-Transport-Security",
            "X-Content-Type-Options",
            "X-Frame-Options",
            "Referrer-Policy",
            "X-XSS-Protection",
            "Permissions-Policy",
        ]

        for header in required_headers:
            assert header in security_headers, f"Missing required header: {header}"

    def test_rate_limiting_integration(self):
        """Test rate limiting integration"""
        from stillme_core.security import RateLimiter

        rate_limiter = RateLimiter()

        # Test basic functionality
        result = rate_limiter.check_rate_limit("test", limit=5, window=60)
        assert result["allowed"] is True

        # Test headers generation
        headers = rate_limiter.get_rate_limit_headers(result)
        assert "X-RateLimit-Limit" in headers

    def test_security_middleware_integration(self):
        """Test security middleware integration"""
        from stillme_core.security import SecurityMiddleware

        middleware = SecurityMiddleware()

        # Test middleware initialization
        assert middleware is not None
        assert hasattr(middleware, "process_request")
        assert hasattr(middleware, "process_response")

    def test_security_configuration(self):
        """Test security configuration"""
        from stillme_core.security import SecurityConfig

        config = SecurityConfig()

        # Test configuration loading
        assert config is not None
        assert hasattr(config, "get_security_settings")

        settings = config.get_security_settings()
        assert "headers" in settings
        assert "rate_limiting" in settings
        assert "cors" in settings


class TestSecurityCompliance:
    """Test OWASP ASVS compliance"""

    def test_owasp_asvs_level2_compliance(self):
        """Test OWASP ASVS Level 2 compliance"""
        from stillme_core.security import RateLimiter, SecurityHeaders

        # Test security headers compliance
        headers = SecurityHeaders()
        security_headers = headers.get_security_headers()

        # ASVS V9.1.1 - Communication Security
        assert "Strict-Transport-Security" in security_headers

        # ASVS V5.1.1 - Input Validation
        assert "Content-Security-Policy" in security_headers

        # ASVS V5.2.1 - Output Encoding
        assert "X-Content-Type-Options" in security_headers

        # Test rate limiting compliance
        rate_limiter = RateLimiter()

        # ASVS V4.1.3 - Access Control Rate Limiting
        result = rate_limiter.check_rate_limit("test", limit=100, window=60)
        assert result["allowed"] is True

    def test_owasp_asvs_level3_compliance(self):
        """Test OWASP ASVS Level 3 compliance"""
        from stillme_core.security import RateLimiter, SecurityHeaders

        # Test advanced security headers
        headers = SecurityHeaders()
        security_headers = headers.get_security_headers()

        # ASVS V9.1.1 - Advanced Communication Security
        assert "Strict-Transport-Security" in security_headers
        hsts = security_headers["Strict-Transport-Security"]
        assert "preload" in hsts  # Advanced HSTS

        # ASVS V5.1.1 - Advanced Input Validation
        csp = security_headers["Content-Security-Policy"]
        assert "object-src 'none'" in csp  # Advanced CSP

        # Test advanced rate limiting
        rate_limiter = RateLimiter()

        # ASVS V4.1.3 - Advanced Access Control Rate Limiting
        result = rate_limiter.check_rate_limit("test", limit=10, window=60)
        assert result["allowed"] is True

        # Test burst protection
        for _i in range(15):  # Exceed limit
            result = rate_limiter.check_rate_limit("test", limit=10, window=60)

        assert result["allowed"] is False  # Should be blocked
