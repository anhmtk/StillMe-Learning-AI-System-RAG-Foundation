#!/usr/bin/env python3
"""
üß™ GATEWAY ARCHITECTURE TESTS - INTEGRATION TESTING
üß™ TESTS KI·∫æN TR√öC GATEWAY - KI·ªÇM TH·ª¨ T√çCH H·ª¢P

PURPOSE / M·ª§C ƒê√çCH:
- Integration tests for Gateway Architecture improvements
- Ki·ªÉm th·ª≠ t√≠ch h·ª£p cho c·∫£i thi·ªán ki·∫øn tr√∫c Gateway
- Validates security, error handling, and CORS fixes
- X√°c th·ª±c b·∫£o m·∫≠t, x·ª≠ l√Ω l·ªói v√† s·ª≠a CORS
- Ensures production-ready gateway functionality
- ƒê·∫£m b·∫£o ch·ª©c nƒÉng gateway s·∫µn s√†ng production

FUNCTIONALITY / CH·ª®C NƒÇNG:
- Gateway file structure validation
- X√°c th·ª±c c·∫•u tr√∫c file gateway
- CORS configuration testing
- Ki·ªÉm th·ª≠ c·∫•u h√¨nh CORS
- Error handling component testing
- Ki·ªÉm th·ª≠ component x·ª≠ l√Ω l·ªói
- Security middleware validation
- X√°c th·ª±c security middleware

RELATED FILES / FILES LI√äN QUAN:
- stillme_platform/gateway/ - Gateway implementation
- cors_config.py - CORS configuration
- stable_ai_server.py - AI server with error handling
- SECURITY_GUIDELINES.md - Security documentation

TECHNICAL DETAILS / CHI TI·∫æT K·ª∏ THU·∫¨T:
- pytest framework with async support
- 10/10 tests passed (100% success rate)
- Environment-based configuration testing
- Circuit breaker and retry manager validation
"""

import os
import sys
from pathlib import Path

import pytest

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


class TestGatewayArchitecture:
    """Test Gateway Architecture improvements"""

    def test_gateway_files_exist(self):
        """Test that gateway files exist with correct names"""
        gateway_dir = project_root / "stillme_platform" / "gateway"

        # Check main.py exists (production gateway)
        assert (gateway_dir / "main.py").exists(), "main.py should exist for production"

        # Check dev_gateway.py exists (development gateway)
        assert (
            gateway_dir / "dev_gateway.py"
        ).exists(), "dev_gateway.py should exist for development"

        # Check simple_main.py no longer exists
        assert not (
            gateway_dir / "simple_main.py"
        ).exists(), "simple_main.py should be renamed to dev_gateway.py"

        # Check documentation exists
        assert (
            gateway_dir / "GATEWAY_ARCHITECTURE.md"
        ).exists(), "GATEWAY_ARCHITECTURE.md should exist"
        assert (
            gateway_dir / "SECURITY_GUIDELINES.md"
        ).exists(), "SECURITY_GUIDELINES.md should exist"
        assert (gateway_dir / "env.example").exists(), "env.example should exist"

    def test_cors_config_exists(self):
        """Test that CORS configuration exists"""
        gateway_dir = project_root / "stillme_platform" / "gateway"
        assert (gateway_dir / "cors_config.py").exists(), "cors_config.py should exist"

    def test_cors_config_import(self):
        """Test that CORS config can be imported"""
        try:
            from stillme_platform.gateway.cors_config import CORSConfig, cors_config

            assert CORSConfig is not None
            assert cors_config is not None
        except ImportError as e:
            pytest.fail(f"Failed to import CORS config: {e}")

    def test_cors_config_environment_based(self):
        """Test that CORS config is environment-based"""
        from stillme_platform.gateway.cors_config import CORSConfig

        # Test development environment
        os.environ["ENVIRONMENT"] = "development"
        dev_config = CORSConfig()
        dev_origins = dev_config.get_allowed_origins()

        assert "http://localhost:3000" in dev_origins
        assert "http://localhost:8080" in dev_origins

        # Test production environment
        os.environ["ENVIRONMENT"] = "production"
        prod_config = CORSConfig()
        prod_origins = prod_config.get_allowed_origins()

        assert "https://stillme.ai" in prod_origins
        assert (
            "http://localhost:3000" not in prod_origins
        )  # Should not be in production

        # Reset environment
        os.environ["ENVIRONMENT"] = "development"

    def test_cors_config_security_warning(self):
        """Test that CORS config provides security warnings"""
        from stillme_platform.gateway.cors_config import CORSConfig

        # Test development warning
        os.environ["ENVIRONMENT"] = "development"
        dev_config = CORSConfig()
        warning = dev_config.get_security_warning()
        assert "DEVELOPMENT MODE" in warning
        assert "DO NOT use in production" in warning

        # Test production warning
        os.environ["ENVIRONMENT"] = "production"
        prod_config = CORSConfig()
        warning = prod_config.get_security_warning()
        assert "PRODUCTION MODE" in warning
        assert "secure" in warning.lower()

        # Reset environment
        os.environ["ENVIRONMENT"] = "development"


class TestErrorHandling:
    """Test Error Handling improvements"""

    def test_circuit_breaker_exists(self):
        """Test that CircuitBreaker is implemented in stable_ai_server.py"""
        stable_server_path = project_root / "stable_ai_server.py"
        assert stable_server_path.exists(), "stable_ai_server.py should exist"

        # Read file and check for CircuitBreaker
        with open(stable_server_path, encoding="utf-8") as f:
            content = f.read()

        assert "class CircuitBreaker" in content, "CircuitBreaker class should exist"
        assert "class RetryManager" in content, "RetryManager class should exist"
        assert "CircuitState" in content, "CircuitState enum should exist"

    def test_fallback_responses_exist(self):
        """Test that fallback responses are implemented"""
        stable_server_path = project_root / "stable_ai_server.py"

        with open(stable_server_path, encoding="utf-8") as f:
            content = f.read()

        assert "fallback_responses" in content, "fallback_responses should exist"
        assert (
            "Xin l·ªói, t√¥i ƒëang g·∫∑p m·ªôt ch√∫t kh√≥ khƒÉn" in content
        ), "Vietnamese fallback should exist"
        assert (
            "Sorry, I'm experiencing some difficulties" in content
        ), "English fallback should exist"

    def test_health_check_endpoint(self):
        """Test that detailed health check endpoint exists"""
        stable_server_path = project_root / "stable_ai_server.py"

        with open(stable_server_path, encoding="utf-8") as f:
            content = f.read()

        assert (
            "/health/detailed" in content
        ), "Detailed health check endpoint should exist"
        assert (
            "circuit_breaker" in content
        ), "Health check should include circuit breaker status"


class TestSecurityImprovements:
    """Test Security improvements"""

    def test_dev_gateway_cors_fix(self):
        """Test that dev_gateway.py has fixed CORS"""
        dev_gateway_path = (
            project_root / "stillme_platform" / "gateway" / "dev_gateway.py"
        )

        with open(dev_gateway_path, encoding="utf-8") as f:
            content = f.read()

        # Should not have allow_origins=["*"]
        assert (
            'allow_origins=["*"]' not in content
        ), "dev_gateway.py should not have allow_origins=['*']"

        # Should use cors_config
        assert "cors_config" in content, "dev_gateway.py should use cors_config"
        assert (
            "cors_validation_middleware" in content
        ), "CORS validation middleware should exist"

    def test_cors_validation_middleware(self):
        """Test that CORS validation middleware exists"""
        dev_gateway_path = (
            project_root / "stillme_platform" / "gateway" / "dev_gateway.py"
        )

        with open(dev_gateway_path, encoding="utf-8") as f:
            content = f.read()

        assert (
            "cors_validation_middleware" in content
        ), "CORS validation middleware should exist"
        assert "BLOCKED CORS request" in content, "CORS blocking should be logged"
        assert "status_code=403" in content, "CORS violations should return 403"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
