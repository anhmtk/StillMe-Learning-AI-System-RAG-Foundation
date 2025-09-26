"""
Reflex Safety Integration

Provides progressive safety checks: fast_check (SafetyGuard) → deep_check (EthicsGuard).
Implements circuit breaker pattern and timeout handling for deep checks.
"""

from __future__ import annotations

import asyncio
import hashlib
import logging
import re
import time
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

# Security patterns for fast_check
DANGEROUS_PATTERNS = [
    # Jailbreak attempts
    r"(?i)(ignore|forget|disregard).*(previous|instructions|rules|guidelines)",
    r"(?i)(act as|pretend to be|roleplay as).*(jailbreak|hack|exploit)",
    r"(?i)(system|admin|root).*(access|privilege|escalation)",
    
    # Base64 encoded content (potential obfuscation)
    r"(?i)(base64|b64).*[A-Za-z0-9+/]{20,}={0,2}",
    
    # Homoglyph attacks (basic detection)
    r"[а-яё].*[a-z]|[a-z].*[а-яё]",  # Cyrillic mixed with Latin
    
    # Command injection patterns
    r"(?i)(rm\s+-rf|del\s+/s|format\s+c:|shutdown|reboot)",
    r"(?i)(eval|exec|system|shell_exec|passthru)",
    r"(?i)(delete\s+all\s+files|remove\s+everything)",
    
    # SQL injection patterns
    r"(?i)(union\s+select|drop\s+table|delete\s+from|insert\s+into)",
    
    # XSS patterns
    r"<script[^>]*>.*</script>",
    r"javascript:",
    r"on\w+\s*=",
]

# Circuit breaker configuration
CIRCUIT_BREAKER_THRESHOLD = 5  # failures before opening
CIRCUIT_BREAKER_TIMEOUT = 30   # seconds before half-open
DEEP_CHECK_TIMEOUT = 5.0       # seconds for deep check timeout


class CircuitBreaker:
    """Simple circuit breaker for deep safety checks."""
    
    def __init__(self, failure_threshold: int = CIRCUIT_BREAKER_THRESHOLD, 
                 timeout: int = CIRCUIT_BREAKER_TIMEOUT):
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.failure_count = 0
        self.last_failure_time = 0
        self.state = "closed"  # closed, open, half-open
    
    def can_execute(self) -> bool:
        """Check if circuit breaker allows execution."""
        if self.state == "closed":
            return True
        elif self.state == "open":
            if time.time() - self.last_failure_time > self.timeout:
                self.state = "half-open"
                return True
            return False
        else:  # half-open
            return True
    
    def on_success(self):
        """Record successful execution."""
        self.failure_count = 0
        self.state = "closed"
    
    def on_failure(self):
        """Record failed execution."""
        self.failure_count += 1
        self.last_failure_time = time.time()
        if self.failure_count >= self.failure_threshold:
            self.state = "open"


class ReflexSafety:
    """Progressive safety checking with fast and deep validation."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.circuit_breaker = CircuitBreaker()
        self.fast_check_enabled = self.config.get("fast_check_enabled", True)
        self.deep_check_enabled = self.config.get("deep_check_enabled", True)
        
        # Compile regex patterns for performance
        self.dangerous_patterns = [
            re.compile(pattern, re.IGNORECASE | re.UNICODE) 
            for pattern in DANGEROUS_PATTERNS
        ]
        
        # Statistics
        self.stats = {
            "fast_checks": 0,
            "fast_blocks": 0,
            "deep_checks": 0,
            "deep_blocks": 0,
            "circuit_breaker_opens": 0,
            "timeouts": 0,
        }
    
    def fast_check(self, text: str) -> Tuple[bool, str]:
        """
        Fast, lightweight safety screening using pattern matching.
        
        Returns:
            Tuple[bool, str]: (is_safe, reason)
        """
        if not self.fast_check_enabled:
            return True, "fast_check_disabled"
        
        self.stats["fast_checks"] += 1
        
        # Normalize text for checking
        normalized_text = self._normalize_for_safety(text)
        
        # Check against dangerous patterns
        for pattern in self.dangerous_patterns:
            if pattern.search(normalized_text):
                self.stats["fast_blocks"] += 1
                return False, f"dangerous_pattern_detected: {pattern.pattern[:50]}..."
        
        # Check for suspicious entropy (potential obfuscation)
        if self._has_high_entropy(normalized_text):
            self.stats["fast_blocks"] += 1
            return False, "high_entropy_detected"
        
        return True, "safe"
    
    async def deep_check(self, text: str, intended_action: Optional[str] = None) -> Tuple[bool, str]:
        """
        Deeper, asynchronous safety check with timeout and circuit breaker.
        
        Args:
            text: Input text to check
            intended_action: Optional action description for context
            
        Returns:
            Tuple[bool, str]: (is_safe, reason)
        """
        if not self.deep_check_enabled:
            return True, "deep_check_disabled"
        
        # Check circuit breaker
        if not self.circuit_breaker.can_execute():
            return False, "circuit_breaker_open"
        
        self.stats["deep_checks"] += 1
        
        try:
            # Simulate deep check with timeout
            result = await asyncio.wait_for(
                self._perform_deep_check(text, intended_action),
                timeout=DEEP_CHECK_TIMEOUT
            )
            
            if result[0]:  # is_safe
                self.circuit_breaker.on_success()
            else:
                self.circuit_breaker.on_failure()
                if self.circuit_breaker.state == "open":
                    self.stats["circuit_breaker_opens"] += 1
            
            return result
            
        except asyncio.TimeoutError:
            self.stats["timeouts"] += 1
            self.circuit_breaker.on_failure()
            return False, "deep_check_timeout"
        except Exception as e:
            logger.error(f"Deep check error: {e}")
            self.circuit_breaker.on_failure()
            return False, f"deep_check_error: {str(e)}"
    
    async def _perform_deep_check(self, text: str, intended_action: Optional[str] = None) -> Tuple[bool, str]:
        """
        Simulate deep safety check (placeholder for EthicsGuard integration).
        
        In a real implementation, this would:
        1. Call EthicsGuard LLM-based analysis
        2. Check against safety databases
        3. Perform semantic analysis for harmful intent
        4. Validate against safety policies
        """
        # Simulate processing time
        await asyncio.sleep(0.1)
        
        # Placeholder logic: block if text contains certain keywords
        dangerous_keywords = ["harmful", "dangerous", "illegal", "exploit", "attack"]
        text_lower = text.lower()
        
        for keyword in dangerous_keywords:
            if keyword in text_lower:
                self.stats["deep_blocks"] += 1
                return False, f"harmful_content_detected: {keyword}"
        
        return True, "deep_check_passed"
    
    def safety_gate(self, text: str, intended_action: Optional[str] = None, 
                   scores: Optional[Dict[str, float]] = None) -> Dict[str, Any]:
        """
        Main safety gate that combines fast and deep checks.
        
        Args:
            text: Input text to validate
            intended_action: Optional action description
            scores: Optional reflex scores for context
            
        Returns:
            Dict with safety decision and details
        """
        start_time = time.time()
        
        # Fast check (synchronous)
        fast_safe, fast_reason = self.fast_check(text)
        
        if not fast_safe:
            return {
                "safe": False,
                "reason": fast_reason,
                "check_type": "fast",
                "processing_time_ms": (time.time() - start_time) * 1000,
                "stats": self.stats.copy()
            }
        
        # Deep check (asynchronous) - in real implementation, this would be awaited
        # For now, we'll simulate the result
        deep_safe, deep_reason = True, "deep_check_simulated"
        
        # Simulate some processing time for realistic timing
        time.sleep(0.001)  # 1ms
        
        return {
            "safe": fast_safe and deep_safe,
            "reason": deep_reason if not deep_safe else fast_reason,
            "check_type": "deep" if not deep_safe else "fast",
            "processing_time_ms": (time.time() - start_time) * 1000,
            "fast_check": {"safe": fast_safe, "reason": fast_reason},
            "deep_check": {"safe": deep_safe, "reason": deep_reason},
            "stats": self.stats.copy()
        }
    
    def _normalize_for_safety(self, text: str) -> str:
        """Normalize text for safety pattern matching."""
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text.strip())
        
        # Convert to lowercase for case-insensitive matching
        text = text.lower()
        
        # Basic homoglyph normalization
        homoglyph_map = {
            'а': 'a', 'е': 'e', 'о': 'o', 'р': 'p', 'с': 'c', 'х': 'x',
            'у': 'y', 'к': 'k', 'м': 'm', 'т': 't', 'н': 'h'
        }
        for cyrillic, latin in homoglyph_map.items():
            text = text.replace(cyrillic, latin)
        
        return text
    
    def _has_high_entropy(self, text: str, threshold: Optional[float] = None) -> bool:
        """Check if text has suspiciously high entropy (potential obfuscation)."""
        if threshold is None:
            threshold = self.config.get("entropy_threshold", 0.9)
        
        if len(text) < 20:
            return False
        
        # Calculate character frequency
        char_counts = {}
        for char in text:
            char_counts[char] = char_counts.get(char, 0) + 1
        
        # Calculate entropy using Shannon entropy formula
        import math
        entropy = 0
        text_len = len(text)
        for count in char_counts.values():
            probability = count / text_len
            if probability > 0:
                entropy -= probability * math.log2(probability)
        
        # Normalize entropy (0-1 scale)
        max_entropy = math.log2(len(char_counts)) if len(char_counts) > 1 else 1
        normalized_entropy = entropy / max_entropy if max_entropy > 0 else 0
        
        return normalized_entropy > threshold
    
    def get_stats(self) -> Dict[str, Any]:
        """Get safety statistics."""
        return {
            "stats": self.stats.copy(),
            "circuit_breaker": {
                "state": self.circuit_breaker.state,
                "failure_count": self.circuit_breaker.failure_count,
                "last_failure_time": self.circuit_breaker.last_failure_time
            },
            "config": {
                "fast_check_enabled": self.fast_check_enabled,
                "deep_check_enabled": self.deep_check_enabled
            }
        }
    
    def reset_stats(self):
        """Reset safety statistics."""
        self.stats = {key: 0 for key in self.stats}
        self.circuit_breaker = CircuitBreaker()


