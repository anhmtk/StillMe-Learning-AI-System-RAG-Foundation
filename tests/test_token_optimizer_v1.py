import pytest
from modules.token_optimizer_v1 import TokenOptimizer

def test_class_exists():
    """Check if TokenOptimizer class exists."""
    optimizer = TokenOptimizer()
    assert optimizer is not None

def test_optimize_tokens():
    """Check if optimize method returns optimized tokens."""
    optimizer = TokenOptimizer()
    tokens = ["this", "is", "a", "test"]
    optimized = optimizer.optimize(tokens)
    assert isinstance(optimized, list)
