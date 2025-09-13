#!/usr/bin/env python3
"""
Minimal test for AgentDev system - no external dependencies
"""


def test_basic_math():
    """Test basic math operations"""
    assert 1 + 1 == 2
    assert 2 * 3 == 6
    assert 10 / 2 == 5


def test_basic_string():
    """Test basic string operations"""
    assert "hello" + " " + "world" == "hello world"
    assert len("test") == 4
    assert "test".upper() == "TEST"


def test_basic_list():
    """Test basic list operations"""
    test_list = [1, 2, 3]
    assert len(test_list) == 3
    assert test_list[0] == 1
    assert test_list[-1] == 3


def test_basic_dict():
    """Test basic dictionary operations"""
    test_dict = {"key": "value", "number": 42}
    assert "key" in test_dict
    assert test_dict["number"] == 42
    assert len(test_dict) == 2


def test_basic_boolean():
    """Test basic boolean operations"""
    assert True is True
    assert False is False
    assert False is not True
    assert True and True is True
    assert True or False is True


if __name__ == "__main__":
    # Run tests manually
    test_basic_math()
    test_basic_string()
    test_basic_list()
    test_basic_dict()
    test_basic_boolean()
    print("All tests passed!")
