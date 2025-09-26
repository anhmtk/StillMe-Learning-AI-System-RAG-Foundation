"""
Reflex Safety (skeleton)

Provides hooks to SafetyGuard/EthicsGuard. In Phase 1: permissive stubs.
"""

from __future__ import annotations


class ReflexSafety:
    def quick_check(self, text: str) -> bool:
        """Fast, lightweight screening. Phase 1: always True."""
        return True

    async def deep_check(self, text: str) -> bool:
        """Deeper, asynchronous safety check. Phase 1: always True."""
        return True


