"""
StillMe Core - Core AI Framework for StillMe AI

StillMe Core is the foundational AI framework that provides:
- Core AI functionality and modules
- Provider adapters and integrations
- Common utilities and helpers
- Configuration management

Author: StillMe AI Team
Version: 2.0.0
"""

from .framework import StillMeFramework
from .health import HealthChecker

__version__ = "2.0.0"
__author__ = "StillMe AI Team"
__description__ = "Core AI Framework for StillMe AI"

# Import main framework
# Import compatibility layer
# Import AI manager functions
from .ai_manager import health, set_mode
from .compat import *


# Stub implementations to avoid complex imports
def warmup(model=None):
    """Stub warmup function"""
    return {"status": "warmed_up", "model": model}


def dev_agent(task, mode="fast", **params):
    """Stub dev_agent function"""
    return f"Stub response for: {task}"


__all__ = [
    "StillMeFramework",
    "HealthChecker",
    # Re-exported from compat - commented out due to F405 errors
    # "SearchResult",
    # "EthicalPrinciple", 
    # "ViolationSeverity",
    # "SimulationStatus",
    # "AttackCategory",
    # "AttackSeverity",
    # "MemoryItem",
    # "LongTermMemory",
    # "QualityIssue",
    # "QualityReport",
    # "RedisEventBus",
    # "DAGExecutor",
    # "RBACManager",
    # "SessionManager",
    # "apply_policies",
    # "safe_reply",
    # "classify",
    # "sanitize",
    # "redact_output",
    # "CANARY",
    # "AgentDevLogger",
    # "log_step",
    # "health",
    # "set_mode",
    # "warmup",
    # "dev_agent",
    # "controller",
    # Missing implementations
    # "NodeType",
    # "ImpactLevel",
    # "MatchType",
    # "SemanticSearchEngine",
    # "RedisEventBus",
    # "DAGExecutor",
    # "RBACManager",
    # "SessionManager",
]
