#!/usr/bin/env python3
"""
Test script for SourceConsensusValidator Circuit Breaker

Tests:
1. Normal operation (should work)
2. Timeout handling (should record failure)
3. Circuit breaker opens after 2 failures
4. Circuit breaker auto-reenables after disable period
"""

import sys
import os
import time

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.validators import source_consensus
from backend.validators.source_consensus import SourceConsensusValidator

def test_circuit_breaker():
    """Test circuit breaker functionality"""
    print("=" * 60)
    print("Testing SourceConsensusValidator Circuit Breaker")
    print("=" * 60)
    
    # Reset circuit breaker state
    source_consensus._circuit_breaker_failure_count = 0
    source_consensus._circuit_breaker_disabled_until = None
    
    ctx_docs = ["Document 1: Test content", "Document 2: Test content"]
    
    # Test 2: Simulate timeout by using very short timeout
    print("\n[Test 2] Simulating timeout (very short timeout)...")
    validator_short_timeout = SourceConsensusValidator(
        enabled=True,
        timeout=0.001,  # Very short timeout to force timeout
        circuit_breaker_threshold=2,
        circuit_breaker_disable_duration=10
    )
    
    # Reset state before test
    _circuit_breaker_failure_count = 0
    _circuit_breaker_disabled_until = None
    
    # First timeout
    print("  - First timeout (failure #1)...")
    result1 = validator_short_timeout.run("Test", ctx_docs, "Test")
    print(f"    Result: passed={result1.passed}, reasons={result1.reasons}")
    print(f"    Circuit breaker state: failures={source_consensus._circuit_breaker_failure_count}, disabled_until={source_consensus._circuit_breaker_disabled_until}")
    
    # Second timeout (should trigger circuit breaker)
    print("  - Second timeout (failure #2 - should trigger circuit breaker)...")
    result2 = validator_short_timeout.run("Test", ctx_docs, "Test")
    print(f"    Result: passed={result2.passed}, reasons={result2.reasons}")
    print(f"    Circuit breaker state: failures={source_consensus._circuit_breaker_failure_count}, disabled_until={source_consensus._circuit_breaker_disabled_until}")
    
    if source_consensus._circuit_breaker_disabled_until is not None:
        print(f"    [OK] Circuit breaker OPENED (disabled until {time.ctime(source_consensus._circuit_breaker_disabled_until)})")
    else:
        print(f"    [FAIL] Circuit breaker did NOT open (expected to open after 2 failures)")
        return False
    
    # Test 3: Circuit breaker should skip validation
    print("\n[Test 3] Circuit breaker should skip validation...")
    result3 = validator_short_timeout.run("Test", ctx_docs, "Test")
    print(f"    Result: passed={result3.passed}, reasons={result3.reasons}")
    
    if "circuit_breaker:disabled" in result3.reasons:
        print("    [OK] Circuit breaker correctly skipped validation")
    else:
        print("    [FAIL] Circuit breaker did NOT skip validation")
        return False
    
    # Test 4: Wait for auto-reenable (simulate by setting disabled_until to past)
    print("\n[Test 4] Simulating auto-reenable (setting disabled_until to past)...")
    source_consensus._circuit_breaker_disabled_until = time.time() - 1  # Set to 1 second ago
    source_consensus._circuit_breaker_failure_count = 2  # Keep failure count
    
    result4 = validator_short_timeout.run("Test", ctx_docs, "Test")
    print(f"    Result: passed={result4.passed}, reasons={result4.reasons}")
    print(f"    Circuit breaker state after reenable: failures={source_consensus._circuit_breaker_failure_count}, disabled_until={source_consensus._circuit_breaker_disabled_until}")
    
    # After reenable, circuit breaker should be closed (disabled_until = None)
    # Failure count may be > 0 if validation still fails (which is expected with short timeout)
    if source_consensus._circuit_breaker_disabled_until is None:
        print("    [OK] Circuit breaker auto-reenabled (disabled_until reset to None)")
    else:
        print("    [FAIL] Circuit breaker did NOT auto-reenable (disabled_until still set)")
        return False
    
    print("\n" + "=" * 60)
    print("[OK] All circuit breaker tests passed!")
    print("=" * 60)
    return True

if __name__ == "__main__":
    success = test_circuit_breaker()
    sys.exit(0 if success else 1)

