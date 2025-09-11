"""
STILLME AI Framework - Modules Package
"""

__version__ = "2.1.0"
__author__ = "StillMe Framework Team"

# Import all modules for easy access
try:
    from .api_provider_manager import UnifiedAPIManager
    from .conversational_core_v1 import ConversationalCore
    from .layered_memory_v1 import LayeredMemoryV1
    from .token_optimizer_v1 import TokenOptimizer, TokenOptimizerConfig
    from .secure_memory_manager import SecureMemoryManager
    from .persona_morph import PersonaMorph
    from .content_integrity_filter import ContentIntegrityFilter
    from .identity_handler import IdentityHandler
    
    __all__ = [
        "UnifiedAPIManager",
        "ConversationalCore", 
        "LayeredMemoryV1",
        "TokenOptimizer",
        "TokenOptimizerConfig",
        "SecureMemoryManager",
        "PersonaMorph",
        "ContentIntegrityFilter",
        "IdentityHandler"
    ]
    
except ImportError as e:
    # Graceful fallback if some modules can't be imported
    print(f"Warning: Some modules could not be imported: {e}")
    __all__ = []
