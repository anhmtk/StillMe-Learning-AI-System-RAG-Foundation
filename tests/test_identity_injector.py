"""
Tests for identity injector
"""

import pytest
from backend.identity.injector import inject_identity, STILLME_IDENTITY


class TestIdentityInjector:
    """Test suite for identity injector"""
    
    def test_inject_identity_default(self):
        """Test identity injection with default system prompt"""
        user_prompt = "What is StillMe?"
        
        result = inject_identity(user_prompt)
        
        assert STILLME_IDENTITY in result
        assert user_prompt in result
        assert "User:" in result
    
    def test_inject_identity_custom(self):
        """Test identity injection with custom system prompt"""
        user_prompt = "What is StillMe?"
        custom_system = "You are a helpful assistant."
        
        result = inject_identity(user_prompt, system_prompt=custom_system)
        
        assert custom_system in result
        assert user_prompt in result
        assert STILLME_IDENTITY not in result
    
    def test_inject_identity_format(self):
        """Test identity injection format"""
        user_prompt = "Test question"
        
        result = inject_identity(user_prompt)
        
        # Should have identity first, then User: then prompt
        assert STILLME_IDENTITY in result
        assert "User:" in result
        assert user_prompt in result
        # Identity should come before User:
        assert result.index(STILLME_IDENTITY) < result.index("User:")
    
    def test_inject_identity_empty_prompt(self):
        """Test identity injection with empty prompt"""
        user_prompt = ""
        
        result = inject_identity(user_prompt)
        
        assert STILLME_IDENTITY in result
        assert "User:" in result

