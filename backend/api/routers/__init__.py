"""
API Routers for StillMe
Modular router organization for better maintainability
"""

from .chat_router import router as chat_router
from .learning_router import router as learning_router
from .rag_router import router as rag_router
from .tiers_router import router as tiers_router
from .spice_router import router as spice_router

__all__ = [
    "chat_router",
    "learning_router",
    "rag_router",
    "tiers_router",
    "spice_router"
]

