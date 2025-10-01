# stillme_core/security/__init__.py
"""
Security scanning and vulnerability assessment module
"""

from .security_scanner import SecurityScanner, VulnerabilityLevel
from .attack_simulator import AttackSimulator, AttackType

try:
    from .vulnerability_assessor import VulnerabilityAssessor
except ImportError:
    VulnerabilityAssessor = None

__all__ = [
    "SecurityScanner",
    "VulnerabilityLevel",
    "AttackSimulator",
    "AttackType",
    "VulnerabilityAssessor",
]
