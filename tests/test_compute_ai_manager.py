# tests/test_compute_ai_manager.py
from stillme_core.ai_manager import compute_number


def test_compute_37x29():
    out = compute_number("Compute 37*29 and print only the number.")
    assert out == "1073"