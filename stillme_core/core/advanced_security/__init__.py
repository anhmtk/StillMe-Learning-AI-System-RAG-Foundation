# stillme_core/advanced_security/__init__.py
"""
Advanced Security Framework for AgentDev
"""

from .safe_attack_simulator import AttackScenario, SafeAttackSimulator, SimulationResult

try:
    from .vulnerability_detector import VulnerabilityDetector, VulnerabilityReport
except ImportError:
    VulnerabilityDetector = None
    VulnerabilityReport = None

try:
    from .defense_tester import DefenseTester, DefenseTestResult
except ImportError:
    DefenseTester = None
    DefenseTestResult = None

try:
    from .security_reporter import SecurityAssessment, SecurityReporter
except ImportError:
    SecurityReporter = None
    SecurityAssessment = None

__all__ = [
    "SafeAttackSimulator",
    "AttackScenario",
    "SimulationResult",
    "VulnerabilityDetector",
    "VulnerabilityReport",
    "DefenseTester",
    "DefenseTestResult",
    "SecurityReporter",
    "SecurityAssessment",
]
