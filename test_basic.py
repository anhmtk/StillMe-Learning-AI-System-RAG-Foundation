"""
Basic test to verify pytest works
"""

def test_simple():
    """Simple test that should always pass"""
    assert 1 + 1 == 2

def test_string():
    """Test string operations"""
    text = "StillMe"
    assert len(text) == 7
    assert "Still" in text

def test_list():
    """Test list operations"""
    items = ["a", "b", "c"]
    assert len(items) == 3
    assert "b" in items
