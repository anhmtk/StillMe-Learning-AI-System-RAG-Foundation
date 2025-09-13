"""
StillMe AI - Client Modules
==========================
Client modules for external API integrations with optimized performance.
"""

from .ollama_client import _ollama_ping, call_ollama_chat

__all__ = ["_ollama_ping", "call_ollama_chat"]
