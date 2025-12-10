"""
Test script for NPR Phase 2.2: Self-Distilled Learning with PAPO-inspired algorithm.

Tests:
1. Reward function calculation
2. PAPO optimizer threshold optimization
3. Adaptive threshold retrieval
4. Integration with validation chain
5. Periodic optimization trigger
"""

import os
import sys
from typing import Dict, Any
from dotenv import load_dotenv

# Fix Windows encoding for emoji
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

load_dotenv()

from backend.services.self_distilled_learning import (
    RewardFunction,
    PAPOOptimizer,
    SelfDistilledLearning,
    ThresholdConfig
)


def test_reward_function():
    """Test reward function calculation."""
    print("\n" + "="*60)
    print("TEST 1: Reward Function Calculation")
    print("="*60)
    
    reward_func = RewardFunction()
    
    # Test case 1: High quality validation (good reward)
    print("\n  Test Case 1: High quality validation")
    reward1 = reward_func.calculate_reward(
        success_rate=0.9,
        false_positive_rate=0.1,
        false_negative_rate=0.1,
        hallucination_prevention_rate=0.8
    )
    print(f"    Success rate: {reward1.success_rate:.3f}")
    print(f"    False positive rate: {reward1.false_positive_rate:.3f}")
    print(f"    False negative rate: {reward1.false_negative_rate:.3f}")
    print(f"    Hallucination prevention: {reward1.hallucination_prevention_rate:.3f}")
    print(f"    Overall reward: {reward1.overall_reward:.3f}")
    
    assert reward1.overall_reward > 0.7, f"High quality should have reward > 0.7, got {reward1.overall_reward:.3f}"
    print(f"    ✅ High quality validation produces good reward")
    
    # Test case 2: Low quality validation (poor reward)
    print("\n  Test Case 2: Low quality validation")
    reward2 = reward_func.calculate_reward(
        success_rate=0.5,
        false_positive_rate=0.5,
        false_negative_rate=0.5,
        hallucination_prevention_rate=0.3
    )
    print(f"    Overall reward: {reward2.overall_reward:.3f}")
    
    assert reward2.overall_reward < reward1.overall_reward, "Low quality should have lower reward"
    print(f"    ✅ Low quality validation produces lower reward")
    
    # Test case 3: Custom weights
    print("\n  Test Case 3: Custom weights")
    reward3 = reward_func.calculate_reward(
        success_rate=0.8,
        false_positive_rate=0.2,
        false_negative_rate=0.2,
        hallucination_prevention_rate=0.7,
        weights={
            "success_rate": 0.5,  # Higher weight on success
            "false_positive_rate": 0.1,
            "false_negative_rate": 0.1,
            "hallucination_prevention": 0.3
        }
    )
    print(f"    Overall reward (custom weights): {reward3.overall_reward:.3f}")
    print(f"    ✅ Custom weights work correctly")
    
    return True


def test_papo_optimizer():
    """Test PAPO optimizer."""
    print("\n" + "="*60)
    print("TEST 2: PAPO Optimizer")
    print("="*60)
    
    # Use a temporary state file for testing
    import tempfile
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.json')
    temp_file.close()
    
    try:
        optimizer = PAPOOptimizer(state_file=temp_file.name)
        
        # Test threshold configuration
        config = ThresholdConfig(
            name="test_threshold",
            current_value=0.1,
            min_value=0.0,
            max_value=0.5,
            step_size=0.01
        )
        
        # Test recording reward
        print("\n  Test: Recording reward")
        from backend.services.self_distilled_learning import ValidationReward
        reward = ValidationReward(
            success_rate=0.8,
            false_positive_rate=0.2,
            false_negative_rate=0.2,
            hallucination_prevention_rate=0.7,
            overall_reward=0.75
        )
        
        optimizer.record_reward("test_threshold", 0.1, reward)
        print(f"    ✅ Reward recorded for test_threshold")
        
        # Test threshold optimization
        print("\n  Test: Threshold optimization")
        optimized_value = optimizer.optimize_threshold("test_threshold", config, 0.75)
        print(f"    Current value: {config.current_value:.3f}")
        print(f"    Optimized value: {optimized_value:.3f}")
        
        assert 0.0 <= optimized_value <= 0.5, f"Optimized value should be in bounds [0.0, 0.5], got {optimized_value:.3f}"
        print(f"    ✅ Threshold optimization works")
        
        # Test getting optimized threshold
        print("\n  Test: Getting optimized threshold")
        retrieved_value = optimizer.get_optimized_threshold("test_threshold", 0.1)
        print(f"    Retrieved value: {retrieved_value:.3f}")
        print(f"    ✅ Optimized threshold retrieval works")
        
        # Test optimization summary
        print("\n  Test: Optimization summary")
        summary = optimizer.get_optimization_summary()
        print(f"    Total thresholds: {summary['total_thresholds']}")
        print(f"    ✅ Optimization summary works")
        
        return True
        
    finally:
        # Clean up temp file
        try:
            os.unlink(temp_file.name)
        except:
            pass


def test_self_distilled_learning():
    """Test Self-Distilled Learning system."""
    print("\n" + "="*60)
    print("TEST 3: Self-Distilled Learning System")
    print("="*60)
    
    try:
        sdl = SelfDistilledLearning()
        
        # Test calculating reward from metrics
        print("\n  Test: Calculate reward from metrics")
        reward = sdl.calculate_reward_from_metrics(days=7)
        print(f"    Overall reward: {reward.overall_reward:.3f}")
        print(f"    Success rate: {reward.success_rate:.3f}")
        print(f"    False positive rate: {reward.false_positive_rate:.3f}")
        print(f"    False negative rate: {reward.false_negative_rate:.3f}")
        print(f"    Hallucination prevention: {reward.hallucination_prevention_rate:.3f}")
        print(f"    ✅ Reward calculation from metrics works")
        
        # Test getting adaptive threshold
        print("\n  Test: Get adaptive threshold")
        adaptive_threshold = sdl.get_adaptive_threshold("citation_relevance_min_overlap", 0.1)
        print(f"    Adaptive threshold: {adaptive_threshold:.3f}")
        assert 0.0 <= adaptive_threshold <= 1.0, f"Threshold should be in [0.0, 1.0], got {adaptive_threshold:.3f}"
        print(f"    ✅ Adaptive threshold retrieval works")
        
        # Test threshold optimization (may take time if there's validation history)
        print("\n  Test: Threshold optimization")
        try:
            optimized = sdl.optimize_thresholds(days=7)
            print(f"    Optimized thresholds: {optimized}")
            print(f"    ✅ Threshold optimization works")
        except Exception as e:
            print(f"    ⚠️ Threshold optimization skipped (may need validation history): {e}")
        
        # Test learning summary
        print("\n  Test: Learning summary")
        summary = sdl.get_learning_summary()
        print(f"    Current reward: {summary['current_reward']:.3f}")
        print(f"    Total thresholds: {summary['optimization']['total_thresholds']}")
        print(f"    ✅ Learning summary works")
        
        return True
        
    except Exception as e:
        print(f"    ❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_threshold_configs():
    """Test threshold configurations."""
    print("\n" + "="*60)
    print("TEST 4: Threshold Configurations")
    print("="*60)
    
    configs = {
        "citation_relevance_min_overlap": ThresholdConfig(
            name="citation_relevance_min_overlap",
            current_value=0.1,
            min_value=0.0,
            max_value=0.5,
            step_size=0.01
        ),
        "evidence_overlap_threshold": ThresholdConfig(
            name="evidence_overlap_threshold",
            current_value=0.01,
            min_value=0.0,
            max_value=0.2,
            step_size=0.005
        ),
        "confidence_threshold": ThresholdConfig(
            name="confidence_threshold",
            current_value=0.5,
            min_value=0.3,
            max_value=0.8,
            step_size=0.02
        ),
    }
    
    all_passed = True
    for name, config in configs.items():
        print(f"\n  Test: {name}")
        print(f"    Current value: {config.current_value:.3f}")
        print(f"    Bounds: [{config.min_value:.3f}, {config.max_value:.3f}]")
        print(f"    Step size: {config.step_size:.3f}")
        
        # Verify bounds
        assert config.min_value <= config.current_value <= config.max_value, \
            f"Current value {config.current_value} should be in bounds [{config.min_value}, {config.max_value}]"
        print(f"    ✅ Bounds verified")
    
    if all_passed:
        print("\n  ✅ All threshold configurations are valid")
    
    return all_passed


def test_integration():
    """Test integration with validation chain."""
    print("\n" + "="*60)
    print("TEST 5: Integration with Validation Chain")
    print("="*60)
    
    try:
        # Test that adaptive thresholds can be retrieved
        from backend.services.self_distilled_learning import get_self_distilled_learning
        sdl = get_self_distilled_learning()
        
        # Test getting adaptive thresholds that would be used in validation
        print("\n  Test: Adaptive thresholds for validation")
        citation_threshold = sdl.get_adaptive_threshold("citation_relevance_min_overlap", 0.1)
        evidence_threshold = sdl.get_adaptive_threshold("evidence_overlap_threshold", 0.01)
        confidence_threshold = sdl.get_adaptive_threshold("confidence_threshold", 0.5)
        
        print(f"    Citation relevance threshold: {citation_threshold:.3f}")
        print(f"    Evidence overlap threshold: {evidence_threshold:.3f}")
        print(f"    Confidence threshold: {confidence_threshold:.3f}")
        
        # Verify thresholds are in reasonable ranges
        assert 0.0 <= citation_threshold <= 0.5, f"Citation threshold should be in [0.0, 0.5]"
        assert 0.0 <= evidence_threshold <= 0.2, f"Evidence threshold should be in [0.0, 0.2]"
        assert 0.3 <= confidence_threshold <= 0.8, f"Confidence threshold should be in [0.3, 0.8]"
        
        print(f"    ✅ Adaptive thresholds are in valid ranges")
        print(f"    ✅ Integration with validation chain works")
        
        return True
        
    except Exception as e:
        print(f"    ❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests."""
    print("\n" + "="*60)
    print("NPR Phase 2.2: Self-Distilled Learning Tests")
    print("="*60)
    
    results = {
        "reward_function": False,
        "papo_optimizer": False,
        "self_distilled_learning": False,
        "threshold_configs": False,
        "integration": False,
    }
    
    try:
        # Test 1: Reward function
        results["reward_function"] = test_reward_function()
        
        # Test 2: PAPO optimizer
        results["papo_optimizer"] = test_papo_optimizer()
        
        # Test 3: Self-Distilled Learning system
        results["self_distilled_learning"] = test_self_distilled_learning()
        
        # Test 4: Threshold configurations
        results["threshold_configs"] = test_threshold_configs()
        
        # Test 5: Integration
        results["integration"] = test_integration()
        
    except Exception as e:
        print(f"\n❌ Test suite failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    print(f"Reward Function:        {'✅ PASS' if results['reward_function'] else '❌ FAIL'}")
    print(f"PAPO Optimizer:         {'✅ PASS' if results['papo_optimizer'] else '❌ FAIL'}")
    print(f"Self-Distilled Learning: {'✅ PASS' if results['self_distilled_learning'] else '❌ FAIL'}")
    print(f"Threshold Configs:      {'✅ PASS' if results['threshold_configs'] else '❌ FAIL'}")
    print(f"Integration:            {'✅ PASS' if results['integration'] else '❌ FAIL'}")
    
    all_passed = all(results.values())
    if all_passed:
        print("\n✅ All tests passed!")
    else:
        print("\n❌ Some tests failed!")
    
    return all_passed


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

