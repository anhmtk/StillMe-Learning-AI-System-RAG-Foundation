"""Tests for query classification functions."""

import pytest
from backend.api.handlers.query_classifier import (
    is_codebase_meta_question,
    is_factual_question,
    extract_full_named_entity,
    is_validator_count_question
)


def test_is_codebase_meta_question():
    """Test codebase meta-question detection."""
    # Should detect codebase questions
    assert is_codebase_meta_question("How is validation chain implemented in your codebase?") is True
    assert is_codebase_meta_question("Where is ai_self_model_detector in your source code?") is True
    assert is_codebase_meta_question("Show me the ValidatorChain class from your code") is True
    
    # Should NOT detect general questions
    assert is_codebase_meta_question("What is Python?") is False
    assert is_codebase_meta_question("How does RAG work?") is False
    
    # Should NOT detect without self-reference
    assert is_codebase_meta_question("How is validation chain implemented?") is False
    
    # Edge cases
    assert is_codebase_meta_question("") is False
    assert is_codebase_meta_question(None) is False


def test_is_factual_question():
    """Test factual question detection."""
    # History questions
    assert is_factual_question("What happened in năm 1954?") is True
    assert is_factual_question("Chiến tranh thế giới thứ hai") is True
    assert is_factual_question("Hiệp ước Geneva") is True
    
    # Science questions
    assert is_factual_question("What is the theory of relativity?") is True
    assert is_factual_question("Nghiên cứu về DNA") is True
    
    # Should NOT detect non-factual questions
    assert is_factual_question("How are you?") is False
    assert is_factual_question("What do you think?") is False
    
    # Edge cases
    assert is_factual_question("") is False


def test_extract_full_named_entity():
    """Test named entity extraction."""
    # Quoted terms
    assert extract_full_named_entity("What is 'Diluted Nuclear Fusion'?") == "Diluted Nuclear Fusion"
    assert extract_full_named_entity('Tell me about "Geneva Conference"') == "Geneva Conference"
    
    # Parenthetical terms
    assert extract_full_named_entity("What is (Diluted Nuclear Fusion)?") == "Diluted Nuclear Fusion"
    
    # Vietnamese patterns
    assert extract_full_named_entity("Hiệp ước Hòa giải Daxonia 1956 là gì?") is not None
    assert "Hiệp ước" in extract_full_named_entity("Hiệp ước Hòa giải Daxonia 1956 là gì?")
    
    # English patterns
    assert extract_full_named_entity("What is the Geneva Conference 1954?") is not None
    
    # Capitalized phrases
    assert extract_full_named_entity("Tell me about DeepSeek R1") is not None
    
    # Should return None for no entity
    assert extract_full_named_entity("How are you?") is None
    assert extract_full_named_entity("") is None


def test_is_validator_count_question():
    """Test validator count question detection."""
    # Vietnamese patterns
    assert is_validator_count_question("bạn có thể liệt kê cụ thể, chính xác là có bao nhiêu lớp validator trong codebase của bạn ko?") is True
    assert is_validator_count_question("hệ thống của bạn có bao nhiêu lớp validator?") is True
    assert is_validator_count_question("số lớp validator trong codebase") is True
    
    # English patterns
    assert is_validator_count_question("how many validator layers in your codebase?") is True
    assert is_validator_count_question("list validator layers") is True
    assert is_validator_count_question("validator layer count") is True
    
    # Should NOT detect other questions
    assert is_validator_count_question("What is a validator?") is False
    assert is_validator_count_question("How does validation work?") is False
    
    # Edge cases
    assert is_validator_count_question("") is False
    assert is_validator_count_question(None) is False


def test_query_classifier_handles_unicode():
    """Test that all functions handle Unicode correctly."""
    # Vietnamese with diacritics
    assert is_codebase_meta_question("codebase của bạn có gì?") is True
    assert is_factual_question("năm 1954 có sự kiện gì?") is True
    assert is_validator_count_question("bao nhiêu lớp validator trong codebase của bạn?") is True
    
    # Chinese
    assert is_codebase_meta_question("你的代码库中有什么？") is False  # No codebase keywords
    assert is_factual_question("1954年发生了什么？") is True  # Year pattern
    
    # Mixed languages
    assert is_codebase_meta_question("your codebase có validator chain không?") is True

