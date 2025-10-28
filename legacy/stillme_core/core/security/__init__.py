# stillme_core/security/__init__.py
"""
Security scanning and vulnerability assessment module
"""

from .attack_simulator import AttackSimulator, AttackType
from .security_scanner import SecurityScanner, VulnerabilityLevel

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
