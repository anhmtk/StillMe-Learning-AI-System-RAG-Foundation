"""
StillMe AI - Client Modules
==========================
Client modules for external API integrations with optimized performance.
"""

from .ollama_client import call_ollama_chat, _ollama_ping

__all__ = ['call_ollama_chat', '_ollama_ping']
