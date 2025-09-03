import pytest
from modules.example_module import some_function_in_module

def test_some_function_in_module():
    # Test should fail for now
    with pytest.raises(ZeroDivisionError):
        some_function_in_module()
