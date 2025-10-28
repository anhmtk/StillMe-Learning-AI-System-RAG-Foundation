"""
API Routes for StillMe V2
"""

from .chat import router as chat_router
from .learning import router as learning_router
from .proposals import router as proposals_router

__all__ = ["chat_router", "learning_router", "proposals_router"]
