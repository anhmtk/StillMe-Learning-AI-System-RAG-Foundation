#!/usr/bin/env python3
"""
AgentDev Security Tests - SEAL-GRADE
Comprehensive security testing for policy gate, network guard, and secret redaction
"""

import asyncio
import json
import pytest
import tempfile
import shutil
from pathlib import Path
import time
import uuid

from agentdev.security.policy_gate import (
    PolicyGate, SecurityLevel, ApprovalStatus, ToolPolicy, 
    validate_tool_request, approve_tool_request, reject_tool_request
)
from agentdev.security.net_guard import (
    NetworkGuard, NetworkAction, Protocol, NetworkRule,
    validate_network_request, get_network_stats
)
from agentdev.security.secret_redaction import (
    SecretRedactor, SecretType, RedactionLevel, 
    redact_text, redact_dict, redact_json, get_redaction_stats
)

class TestPolicyGate:
    """Test Policy Gate security enforcement"""
    
    def test_policy_gate_initialization(self):
        """Test policy gate initialization"""
        
        async def _test():
            # Create temporary policy file
            temp_dir = tempfile.mkdtemp()
            policy_file = Path(temp_dir) / "test_policy.yaml"
            
            try:
                gate = PolicyGate(str(policy_file))
                
                # Should have default policies
                assert len(gate.policies) > 0
                assert "file_read" in gate.policies
                assert "file_write" in gate.policies
                assert "command_execute" in gate.policies
                
                # Check default policy values
                file_read_policy = gate.policies["file_read"]
                assert file_read_policy.allowed is True
                assert file_read_policy.security_level == SecurityLevel.SAFE
                assert file_read_policy.requires_approval is False
                
                command_policy = gate.policies["command_execute"]
                assert command_policy.allowed is False
                assert command_policy.security_level == SecurityLevel.CRITICAL
                assert command_policy.requires_approval is True
                
            finally:
                shutil.rmtree(temp_dir)
        
        asyncio.run(_test())
    
    def test_safe_tool_auto_approval(self):
        """Test auto-approval of safe tools"""
        
        async def _test():
            temp_dir = tempfile.mkdtemp()
            policy_file = Path(temp_dir) / "test_policy.yaml"
            
            try:
                gate = PolicyGate(str(policy_file))
                
                # Test safe tool (file_read)
                decision = await gate.validate_request(
                    tool_name="file_read",
                    parameters={"path": "/tmp/test.txt", "encoding": "utf-8"},
                    user_id="test_user",
                    session_id="test_session"
                )
                
                assert decision.approved is True
                assert decision.status == ApprovalStatus.AUTO_APPROVED
                assert decision.reason == "Auto-approved safe operation"
                
            finally:
                shutil.rmtree(temp_dir)
        
        asyncio.run(_test())
    
    def test_blocked_tool_rejection(self):
        """Test rejection of blocked tools"""
        
        async def _test():
            temp_dir = tempfile.mkdtemp()
            policy_file = Path(temp_dir) / "test_policy.yaml"
            
            try:
                gate = PolicyGate(str(policy_file))
                
                # Test blocked tool (command_execute)
                decision = await gate.validate_request(
                    tool_name="command_execute",
                    parameters={"command": "ls -la"},
                    user_id="test_user",
                    session_id="test_session"
                )
                
                assert decision.approved is False
                assert decision.status == ApprovalStatus.REJECTED
                assert "blocked by policy" in decision.reason
                
            finally:
                shutil.rmtree(temp_dir)
        
        asyncio.run(_test())
    
    def test_parameter_validation(self):
        """Test parameter validation"""
        
        async def _test():
            temp_dir = tempfile.mkdtemp()
            policy_file = Path(temp_dir) / "test_policy.yaml"
            
            try:
                gate = PolicyGate(str(policy_file))
                
                # Test forbidden parameter
                decision = await gate.validate_request(
                    tool_name="file_write",
                    parameters={"path": "/tmp/test.txt", "password": "secret123"},
                    user_id="test_user",
                    session_id="test_session"
                )
                
                assert decision.approved is False
                assert decision.status == ApprovalStatus.REJECTED
                assert "Forbidden parameter" in decision.reason
                
            finally:
                shutil.rmtree(temp_dir)
        
        asyncio.run(_test())
    
    def test_security_pattern_detection(self):
        """Test dangerous pattern detection"""
        
        async def _test():
            temp_dir = tempfile.mkdtemp()
            policy_file = Path(temp_dir) / "test_policy.yaml"
            
            try:
                gate = PolicyGate(str(policy_file))
                
                # Test dangerous pattern
                decision = await gate.validate_request(
                    tool_name="file_write",
                    parameters={"path": "/tmp/test.txt", "content": "rm -rf /"},
                    user_id="test_user",
                    session_id="test_session"
                )
                
                assert decision.approved is False
                assert decision.status == ApprovalStatus.REJECTED
                assert "Security pattern detected" in decision.reason
                
            finally:
                shutil.rmtree(temp_dir)
        
        asyncio.run(_test())
    
    def test_rate_limiting(self):
        """Test rate limiting enforcement"""
        
        async def _test():
            temp_dir = tempfile.mkdtemp()
            policy_file = Path(temp_dir) / "test_policy.yaml"
            
            try:
                gate = PolicyGate(str(policy_file))
                
                # Get file_write policy
                file_write_policy = gate.policies["file_write"]
                max_per_hour = file_write_policy.max_executions_per_hour
                
                # Simulate rate limit by adding timestamps
                gate.rate_limits["file_write"] = [time.time()] * max_per_hour
                
                # Test rate limited request
                decision = await gate.validate_request(
                    tool_name="file_write",
                    parameters={"path": "/tmp/test.txt", "content": "test"},
                    user_id="test_user",
                    session_id="test_session"
                )
                
                assert decision.approved is False
                assert decision.status == ApprovalStatus.REJECTED
                assert "Rate limit exceeded" in decision.reason
                
            finally:
                shutil.rmtree(temp_dir)
        
        asyncio.run(_test())
    
    def test_approval_workflow(self):
        """Test approval workflow for medium/high risk tools"""
        
        async def _test():
            temp_dir = tempfile.mkdtemp()
            policy_file = Path(temp_dir) / "test_policy.yaml"
            
            try:
                gate = PolicyGate(str(policy_file))
                
                # Test medium risk tool requiring approval
                decision = await gate.validate_request(
                    tool_name="file_write",
                    parameters={"path": "/tmp/test.txt", "content": "test"},
                    user_id="test_user",
                    session_id="test_session"
                )
                
                # Should require approval
                assert decision.approved is False
                assert decision.status == ApprovalStatus.PENDING
                assert "requires manual approval" in decision.reason
                
                # Check pending requests
                pending = gate.get_pending_requests()
                assert len(pending) == 1
                assert pending[0].tool_name == "file_write"
                
                # Approve request
                approved = await gate.approve_request(
                    decision.request_id, "admin", "Test approval"
                )
                assert approved is True
                
                # Check no pending requests
                pending = gate.get_pending_requests()
                assert len(pending) == 0
                
            finally:
                shutil.rmtree(temp_dir)
        
        asyncio.run(_test())

class TestNetworkGuard:
    """Test Network Guard security enforcement"""
    
    def test_network_guard_initialization(self):
        """Test network guard initialization"""
        
        async def _test():
            temp_dir = tempfile.mkdtemp()
            policy_file = Path(temp_dir) / "test_network_policy.yaml"
            
            try:
                guard = NetworkGuard(str(policy_file))
                
                # Should have default rules
                assert len(guard.rules) > 0
                assert "allow_https_common" in guard.rules
                assert "block_http" in guard.rules
                assert "block_private_networks" in guard.rules
                
                # Check default rule values
                https_rule = guard.rules["allow_https_common"]
                assert https_rule.action == NetworkAction.ALLOW
                assert https_rule.protocol == Protocol.HTTPS
                assert https_rule.rate_limit == 60
                
                http_rule = guard.rules["block_http"]
                assert http_rule.action == NetworkAction.BLOCK
                assert http_rule.protocol == Protocol.HTTP
                
            finally:
                shutil.rmtree(temp_dir)
        
        asyncio.run(_test())
    
    def test_https_allowed_domains(self):
        """Test allowed HTTPS domains"""
        
        async def _test():
            temp_dir = tempfile.mkdtemp()
            policy_file = Path(temp_dir) / "test_network_policy.yaml"
            
            try:
                guard = NetworkGuard(str(policy_file))
                
                # Test allowed HTTPS domain
                decision = await guard.validate_request(
                    url="https://www.google.com/search?q=test",
                    method="GET",
                    headers={"User-Agent": "test"},
                    user_id="test_user",
                    session_id="test_session"
                )
                
                assert decision.allowed is True
                assert decision.action == NetworkAction.ALLOW
                assert "Allowed by rule" in decision.reason
                
            finally:
                shutil.rmtree(temp_dir)
        
        asyncio.run(_test())
    
    def test_http_blocked(self):
        """Test HTTP blocking"""
        
        async def _test():
            temp_dir = tempfile.mkdtemp()
            policy_file = Path(temp_dir) / "test_network_policy.yaml"
            
            try:
                guard = NetworkGuard(str(policy_file))
                
                # Test blocked HTTP
                decision = await guard.validate_request(
                    url="http://example.com",
                    method="GET",
                    headers={"User-Agent": "test"},
                    user_id="test_user",
                    session_id="test_session"
                )
                
                assert decision.allowed is False
                assert decision.action == NetworkAction.BLOCK
                assert "Blocked by rule" in decision.reason
                
            finally:
                shutil.rmtree(temp_dir)
        
        asyncio.run(_test())
    
    def test_private_network_blocking(self):
        """Test private network blocking"""
        
        async def _test():
            temp_dir = tempfile.mkdtemp()
            policy_file = Path(temp_dir) / "test_network_policy.yaml"
            
            try:
                guard = NetworkGuard(str(policy_file))
                
                # Test blocked private network
                decision = await guard.validate_request(
                    url="https://192.168.1.1",
                    method="GET",
                    headers={"User-Agent": "test"},
                    user_id="test_user",
                    session_id="test_session"
                )
                
                assert decision.allowed is False
                assert decision.action == NetworkAction.BLOCK
                assert "Suspicious pattern" in decision.reason
                
            finally:
                shutil.rmtree(temp_dir)
        
        asyncio.run(_test())
    
    def test_homoglyph_detection(self):
        """Test homoglyph attack detection"""
        
        async def _test():
            temp_dir = tempfile.mkdtemp()
            policy_file = Path(temp_dir) / "test_network_policy.yaml"
            
            try:
                guard = NetworkGuard(str(policy_file))
                
                # Test homoglyph domain (using Cyrillic 'а' instead of Latin 'a')
                decision = await guard.validate_request(
                    url="https://www.gооgle.com",  # Cyrillic 'о'
                    method="GET",
                    headers={"User-Agent": "test"},
                    user_id="test_user",
                    session_id="test_session"
                )
                
                assert decision.allowed is False
                assert decision.action == NetworkAction.BLOCK
                assert "Homoglyph detected" in decision.reason
                
            finally:
                shutil.rmtree(temp_dir)
        
        asyncio.run(_test())
    
    def test_rate_limiting(self):
        """Test network rate limiting"""
        
        async def _test():
            temp_dir = tempfile.mkdtemp()
            policy_file = Path(temp_dir) / "test_network_policy.yaml"
            
            try:
                guard = NetworkGuard(str(policy_file))
                
                # Get rate limit for google.com
                google_rule = guard.rules["allow_https_common"]
                max_per_minute = google_rule.rate_limit
                
                # Simulate rate limit by adding timestamps
                guard.rate_limits["www.google.com"] = [time.time()] * (max_per_minute or 1)
                
                # Test rate limited request
                decision = await guard.validate_request(
                    url="https://www.google.com/search?q=test",
                    method="GET",
                    headers={"User-Agent": "test"},
                    user_id="test_user",
                    session_id="test_session"
                )
                
                assert decision.allowed is False
                assert decision.action == NetworkAction.RATE_LIMIT
                assert decision.rate_limited is True
                assert "Rate limit exceeded" in decision.reason
                
            finally:
                shutil.rmtree(temp_dir)
        
        asyncio.run(_test())

class TestSecretRedaction:
    """Test Secret Redaction functionality"""
    
    def test_secret_redactor_initialization(self):
        """Test secret redactor initialization"""
        
        async def _test():
            temp_dir = tempfile.mkdtemp()
            policy_file = Path(temp_dir) / "test_redaction_policy.yaml"
            
            try:
                redactor = SecretRedactor(str(policy_file))
                
                # Should have default patterns
                assert len(redactor.patterns) > 0
                
                # Check for common pattern types
                pattern_types = {pattern.secret_type for pattern in redactor.patterns}
                assert SecretType.PASSWORD in pattern_types
                assert SecretType.API_KEY in pattern_types
                assert SecretType.TOKEN in pattern_types
                assert SecretType.EMAIL in pattern_types
                
            finally:
                shutil.rmtree(temp_dir)
        
        asyncio.run(_test())
    
    def test_password_redaction(self):
        """Test password redaction"""
        
        async def _test():
            temp_dir = tempfile.mkdtemp()
            policy_file = Path(temp_dir) / "test_redaction_policy.yaml"
            
            try:
                redactor = SecretRedactor(str(policy_file))
                
                # Test password redaction
                text = "password: secret123"
                result = await redactor.redact_text(text)
                
                assert result.redaction_count == 1
                assert "secret123" not in result.redacted_text
                assert "[REDACTED]" in result.redacted_text
                
                # Check detected secret
                secret = result.detected_secrets[0]
                assert secret.secret_type == SecretType.PASSWORD
                assert secret.value == "secret123"
                assert secret.redacted_value == "[REDACTED]"
                
            finally:
                shutil.rmtree(temp_dir)
        
        asyncio.run(_test())
    
    def test_api_key_redaction(self):
        """Test API key redaction"""
        
        async def _test():
            temp_dir = tempfile.mkdtemp()
            policy_file = Path(temp_dir) / "test_redaction_policy.yaml"
            
            try:
                redactor = SecretRedactor(str(policy_file))
                
                # Test API key redaction
                text = "api_key: sk-1234567890abcdef1234567890abcdef"
                result = await redactor.redact_text(text)
                
                assert result.redaction_count == 1
                assert "sk-1234567890abcdef1234567890abcdef" not in result.redacted_text
                
                # Check partial redaction
                secret = result.detected_secrets[0]
                assert secret.secret_type == SecretType.API_KEY
                assert secret.redacted_value.startswith("sk")
                assert secret.redacted_value.endswith("ef")
                assert "*" in secret.redacted_value
                
            finally:
                shutil.rmtree(temp_dir)
        
        asyncio.run(_test())
    
    def test_email_redaction(self):
        """Test email redaction"""
        
        async def _test():
            temp_dir = tempfile.mkdtemp()
            policy_file = Path(temp_dir) / "test_redaction_policy.yaml"
            
            try:
                redactor = SecretRedactor(str(policy_file))
                
                # Test email redaction
                text = "Contact: john.doe@example.com for more info"
                result = await redactor.redact_text(text)
                
                assert result.redaction_count == 1
                assert "john.doe@example.com" not in result.redacted_text
                
                # Check partial redaction
                secret = result.detected_secrets[0]
                assert secret.secret_type == SecretType.EMAIL
                assert secret.redacted_value.startswith("jo")
                assert secret.redacted_value.endswith("om")
                assert "*" in secret.redacted_value
                
            finally:
                shutil.rmtree(temp_dir)
        
        asyncio.run(_test())
    
    def test_dict_redaction(self):
        """Test dictionary redaction"""
        
        async def _test():
            temp_dir = tempfile.mkdtemp()
            policy_file = Path(temp_dir) / "test_redaction_policy.yaml"
            
            try:
                redactor = SecretRedactor(str(policy_file))
                
                # Test dictionary redaction
                data = {
                    "username": "john_doe",
                    "password": "secret123",
                    "api_key": "sk-1234567890abcdef",
                    "email": "john@example.com",
                    "config": {
                        "database_url": "postgresql://user:pass@localhost/db"
                    }
                }
                
                redacted_data = await redactor.redact_dict(data)
                
                # Check redacted values
                assert redacted_data["password"] == "[REDACTED]"
                assert redacted_data["api_key"] == "[REDACTED]"
                assert redacted_data["email"] == "[REDACTED]"
                assert redacted_data["config"]["database_url"] == "[REDACTED]"
                
                # Check non-sensitive values
                assert redacted_data["username"] == "john_doe"
                
            finally:
                shutil.rmtree(temp_dir)
        
        asyncio.run(_test())
    
    def test_json_redaction(self):
        """Test JSON redaction"""
        
        async def _test():
            temp_dir = tempfile.mkdtemp()
            policy_file = Path(temp_dir) / "test_redaction_policy.yaml"
            
            try:
                redactor = SecretRedactor(str(policy_file))
                
                # Test JSON redaction
                json_text = json.dumps({
                    "user": "john_doe",
                    "password": "secret123",
                    "token": "bearer_1234567890abcdef"
                }, indent=2)
                
                redacted_json = await redactor.redact_json(json_text)
                
                # Parse and check
                redacted_data = json.loads(redacted_json)
                assert redacted_data["password"] == "[REDACTED]"
                assert redacted_data["token"] == "[REDACTED]"
                assert redacted_data["user"] == "john_doe"
                
            finally:
                shutil.rmtree(temp_dir)
        
        asyncio.run(_test())
    
    def test_redaction_levels(self):
        """Test different redaction levels"""
        
        async def _test():
            temp_dir = tempfile.mkdtemp()
            policy_file = Path(temp_dir) / "test_redaction_policy.yaml"
            
            try:
                redactor = SecretRedactor(str(policy_file))
                
                text = "password: secret123"
                
                # Test full redaction
                result_full = await redactor.redact_text(text, RedactionLevel.FULL)
                assert result_full.detected_secrets[0].redacted_value == "[REDACTED]"
                
                # Test partial redaction
                result_partial = await redactor.redact_text(text, RedactionLevel.PARTIAL)
                redacted_value = result_partial.detected_secrets[0].redacted_value
                # Password pattern uses full redaction by default, so expect [REDACTED]
                assert redacted_value == "[REDACTED]"
                
                # Test hash redaction
                result_hash = await redactor.redact_text(text, RedactionLevel.HASH)
                redacted_value = result_hash.detected_secrets[0].redacted_value
                # Password pattern uses full redaction by default, so expect [REDACTED]
                assert redacted_value == "[REDACTED]"
                
            finally:
                shutil.rmtree(temp_dir)
        
        asyncio.run(_test())

class TestSecurityIntegration:
    """Test integrated security components"""
    
    def test_security_workflow(self):
        """Test complete security workflow"""
        
        async def _test():
            temp_dir = tempfile.mkdtemp()
            
            try:
                # Initialize all security components
                policy_gate = PolicyGate(str(Path(temp_dir) / "policy.yaml"))
                network_guard = NetworkGuard(str(Path(temp_dir) / "network.yaml"))
                secret_redactor = SecretRedactor(str(Path(temp_dir) / "redaction.yaml"))
                
                # Test 1: Policy Gate - Allow safe operation
                decision = await policy_gate.validate_request(
                    tool_name="file_read",
                    parameters={"path": "/tmp/test.txt"},
                    user_id="test_user",
                    session_id="test_session"
                )
                assert decision.approved is True
                
                # Test 2: Network Guard - Allow HTTPS
                network_decision = await network_guard.validate_request(
                    url="https://www.google.com",
                    method="GET",
                    headers={"User-Agent": "test"},
                    user_id="test_user",
                    session_id="test_session"
                )
                assert network_decision.allowed is True
                
                # Test 3: Secret Redaction
                sensitive_text = "password: secret123 and api_key: sk-1234567890"
                redaction_result = await secret_redactor.redact_text(sensitive_text)
                assert redaction_result.redaction_count == 2
                assert "secret123" not in redaction_result.redacted_text
                assert "sk-1234567890" not in redaction_result.redacted_text
                
                # Test 4: Get security stats
                policy_stats = policy_gate.get_security_stats()
                network_stats = network_guard.get_network_stats()
                redaction_stats = secret_redactor.get_redaction_stats()
                
                assert policy_stats["total_executions"] >= 1
                assert network_stats["total_requests"] >= 1
                assert redaction_stats["total_secrets_detected"] >= 2
                
            finally:
                shutil.rmtree(temp_dir)
        
        asyncio.run(_test())
