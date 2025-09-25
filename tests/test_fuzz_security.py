"""
Test Suite for Fuzz & Security
=============================

Comprehensive fuzz testing and security validation using Hypothesis.
Tests cover Unicode, emoji, SQLi, XSS, large input, and memory safety.

Author: StillMe AI Framework
Created: 2025-01-08
"""

import json
import time
import psutil
import os
import sys
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from pathlib import Path

# Hypothesis imports
try:
    from hypothesis import given, strategies as st, settings, example
    from hypothesis.strategies import text, integers, composite
    HYPOTHESIS_AVAILABLE = True
except ImportError:
    HYPOTHESIS_AVAILABLE = False
    print("WARNING: Hypothesis not available. Install with: pip install hypothesis")

# Import existing detectors
from stillme_core.modules.detectors.sqli_detector import SQLiDetector
from stillme_core.modules.detectors.xss_detector import XSSDetector
from stillme_core.modules.detectors.unicode_detector import UnicodeDetector
from stillme_core.modules.detectors.json_detector import JSONDetector
from stillme_core.modules.detectors.nested_detector import NestedCodeBlockDetector


@dataclass
class SecurityTestResult:
    """Result of a security test"""
    test_name: str
    input_data: str
    is_dangerous: bool
    detected: bool
    detector_type: str
    confidence: float
    processing_time_ms: float
    memory_usage_mb: float


class FuzzSecurityTestSuite:
    """
    Comprehensive fuzz testing and security validation suite
    
    Tests:
    - Unicode fuzzing with various character sets
    - Emoji and special character handling
    - SQL injection detection
    - XSS attack detection
    - Large input handling
    - Memory safety and performance
    - Pathological input patterns
    """
    
    def __init__(self):
        """Initialize test suite"""
        self.detectors = {
            'sqli': SQLiDetector(),
            'xss': XSSDetector(),
            'unicode': UnicodeDetector(),
            'json': JSONDetector(),
            'nested': NestedCodeBlockDetector(),
        }
        self.test_results = []
        self.passed_tests = 0
        self.total_tests = 0
        self.memory_baseline = self._get_memory_usage()
        
    def _get_memory_usage(self) -> float:
        """Get current memory usage in MB"""
        try:
            process = psutil.Process(os.getpid())
            return process.memory_info().rss / 1024 / 1024
        except:
            return 0.0
    
    def _measure_performance(self, func, *args, **kwargs):
        """Measure function performance and memory usage"""
        start_time = time.time()
        start_memory = self._get_memory_usage()
        
        try:
            result = func(*args, **kwargs)
            success = True
        except Exception as e:
            result = None
            success = False
            error = str(e)
        
        end_time = time.time()
        end_memory = self._get_memory_usage()
        
        processing_time = (end_time - start_time) * 1000  # ms
        memory_delta = end_memory - start_memory
        
        return {
            'result': result,
            'success': success,
            'processing_time_ms': processing_time,
            'memory_delta_mb': memory_delta,
            'error': error if not success else None
        }
    
    def test_unicode_fuzzing(self) -> bool:
        """Test Unicode fuzzing with various character sets"""
        print("\n=== Testing Unicode Fuzzing ===")
        
        if not HYPOTHESIS_AVAILABLE:
            print("SKIPPED: Hypothesis not available")
            return True
        
        passed = 0
        total = 0
        
        # Unicode ranges to test
        unicode_ranges = [
            (0x0000, 0x007F),  # Basic Latin
            (0x0080, 0x00FF),  # Latin-1 Supplement
            (0x0100, 0x017F),  # Latin Extended-A
            (0x4E00, 0x9FFF),  # CJK Unified Ideographs
            (0x0400, 0x04FF),  # Cyrillic
            (0x1F600, 0x1F64F),  # Emoticons
            (0x1F300, 0x1F5FF),  # Miscellaneous Symbols
            (0x2000, 0x206F),  # General Punctuation
            (0xFEFF, 0xFEFF),  # Zero Width No-Break Space
        ]
        
        @given(st.text(min_size=1, max_size=100))
        @settings(max_examples=50)
        def test_unicode_input(text_input):
            nonlocal passed, total
            total += 1
            
            try:
                # Test with unicode detector
                perf = self._measure_performance(
                    self.detectors['unicode'].detect, text_input
                )
                
                if perf['success'] and perf['processing_time_ms'] < 100:
                    passed += 1
                else:
                    print(f"FAILED: Unicode input '{text_input[:20]}...' - {perf.get('error', 'Timeout')}")
                    
            except Exception as e:
                print(f"ERROR: Unicode input '{text_input[:20]}...' - {e}")
        
        # Run hypothesis tests
        try:
            test_unicode_input()
        except Exception as e:
            print(f"ERROR: Unicode fuzzing failed - {e}")
            return False
        
        pass_rate = (passed / total) * 100 if total > 0 else 0
        print(f"Unicode Fuzzing: {passed}/{total} ({pass_rate:.1f}%)")
        
        self.test_results.append({
            'test': 'unicode_fuzzing',
            'passed': passed,
            'total': total,
            'pass_rate': pass_rate
        })
        
        return pass_rate >= 90.0
    
    def test_emoji_handling(self) -> bool:
        """Test emoji and special character handling"""
        print("\n=== Testing Emoji Handling ===")
        
        passed = 0
        total = 0
        
        # Emoji test cases
        emoji_cases = [
            "Hello 👋 World 🌍",
            "🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀",  # Emoji spam
            "Mixed text with 😀😃😄😁😆😅😂🤣😊😇",  # Multiple emojis
            "Unicode: \U0001F600\U0001F601\U0001F602",  # Unicode escapes
            "Zero-width: \u200B\u200C\u200D",  # Zero-width characters
            "Bidirectional: \u202E\u202D",  # Bidirectional override
            "Variation: 👨\u200D👩\u200D👧\u200D👦",  # Family emoji with ZWJ
        ]
        
        for emoji_text in emoji_cases:
            total += 1
            try:
                # Test with unicode detector
                perf = self._measure_performance(
                    self.detectors['unicode'].detect, emoji_text
                )
                
                if perf['success'] and perf['processing_time_ms'] < 50:
                    passed += 1
                    print(f"PASSED: Emoji '{emoji_text[:20]}...'")
                else:
                    print(f"FAILED: Emoji '{emoji_text[:20]}...' - {perf.get('error', 'Timeout')}")
                    
            except Exception as e:
                print(f"ERROR: Emoji '{emoji_text[:20]}...' - {e}")
        
        pass_rate = (passed / total) * 100 if total > 0 else 0
        print(f"Emoji Handling: {passed}/{total} ({pass_rate:.1f}%)")
        
        self.test_results.append({
            'test': 'emoji_handling',
            'passed': passed,
            'total': total,
            'pass_rate': pass_rate
        })
        
        return pass_rate >= 90.0
    
    def test_sql_injection_detection(self) -> bool:
        """Test SQL injection detection"""
        print("\n=== Testing SQL Injection Detection ===")
        
        passed = 0
        total = 0
        
        # SQL injection test cases
        sqli_cases = [
            # Basic SQLi (should trigger)
            ("'; DROP TABLE users; --", True),
            ("1' UNION SELECT * FROM users--", True),
            ("admin'--", True),
            ("admin'/*", True),
            
            # Advanced SQLi (should trigger)
            ("1'; EXEC xp_cmdshell('dir'); --", True),
            ("1'; WAITFOR DELAY '00:00:05'--", True),
            ("1' AND (SELECT SLEEP(5))--", True),
            
            # Blind SQLi (should trigger)
            ("1' AND (SELECT SUBSTRING(password,1,1) FROM users WHERE id=1)='a'--", True),
            ("1' AND (SELECT COUNT(*) FROM users WHERE username LIKE 'a%') > 0--", True),
            
            # No SQLi (should not trigger) - These are legitimate SQL queries
            ("SELECT id, name FROM products WHERE category = 'electronics'", False),
            ("UPDATE users SET last_login = NOW() WHERE id = 1", False),
            ("CREATE TABLE test (id INT, name VARCHAR(50))", False),
        ]
        
        for sqli_text, expected_dangerous in sqli_cases:
            total += 1
            try:
                # Test with SQLi detector
                perf = self._measure_performance(
                    self.detectors['sqli'].detect, sqli_text
                )
                
                if perf['success']:
                    result = perf['result']
                    actual_dangerous = result.get('needs_clarification', False)
                    
                    if expected_dangerous == actual_dangerous:
                        passed += 1
                        status = "detected" if expected_dangerous else "not flagged"
                        print(f"PASSED: SQLi {status} '{sqli_text[:30]}...'")
                    else:
                        print(f"FAILED: SQLi detection '{sqli_text[:30]}...' - Expected: {expected_dangerous}, Got: {actual_dangerous}")
                else:
                    print(f"ERROR: SQLi detection '{sqli_text[:30]}...' - {perf.get('error', 'Unknown error')}")
                    
            except Exception as e:
                print(f"ERROR: SQLi detection '{sqli_text[:30]}...' - {e}")
        
        pass_rate = (passed / total) * 100 if total > 0 else 0
        print(f"SQL Injection Detection: {passed}/{total} ({pass_rate:.1f}%)")
        
        self.test_results.append({
            'test': 'sql_injection_detection',
            'passed': passed,
            'total': total,
            'pass_rate': pass_rate
        })
        
        return pass_rate >= 90.0
    
    def test_xss_detection(self) -> bool:
        """Test XSS attack detection"""
        print("\n=== Testing XSS Detection ===")
        
        passed = 0
        total = 0
        
        # XSS test cases
        xss_cases = [
            # Basic XSS
            "<script>alert('XSS')</script>",
            "<img src=x onerror=alert('XSS')>",
            "<svg onload=alert('XSS')>",
            "javascript:alert('XSS')",
            
            # Advanced XSS
            "<iframe src=javascript:alert('XSS')></iframe>",
            "<body onload=alert('XSS')>",
            "<input onfocus=alert('XSS') autofocus>",
            "<select onfocus=alert('XSS') autofocus>",
            
            # Encoded XSS
            "&#60;script&#62;alert('XSS')&#60;/script&#62;",
            "%3Cscript%3Ealert('XSS')%3C/script%3E",
            "\\x3Cscript\\x3Ealert('XSS')\\x3C/script\\x3E",
            
            # DOM-based XSS
            "document.location='javascript:alert(\"XSS\")'",
            "window.location='javascript:alert(\"XSS\")'",
            "eval('alert(\"XSS\")')",
            
            # No XSS (should not trigger)
            "<p>This is a normal paragraph</p>",
            "<div class='container'>Content</div>",
            "<a href='https://example.com'>Link</a>",
            "Hello world!",
        ]
        
        for xss_text in xss_cases:
            total += 1
            try:
                # Test with XSS detector
                perf = self._measure_performance(
                    self.detectors['xss'].detect, xss_text
                )
                
                if perf['success']:
                    result = perf['result']
                    is_dangerous = any(keyword in xss_text.lower() for keyword in ['script', 'onerror', 'onload', 'javascript:', 'alert('])
                    
                    if is_dangerous and result.get('needs_clarification', False):
                        passed += 1
                        print(f"PASSED: XSS detected '{xss_text[:30]}...'")
                    elif not is_dangerous and not result.get('needs_clarification', False):
                        passed += 1
                        print(f"PASSED: Safe HTML not flagged '{xss_text[:30]}...'")
                    else:
                        print(f"FAILED: XSS detection '{xss_text[:30]}...' - Expected: {is_dangerous}, Got: {result.get('needs_clarification', False)}")
                else:
                    print(f"ERROR: XSS detection '{xss_text[:30]}...' - {perf.get('error', 'Unknown error')}")
                    
            except Exception as e:
                print(f"ERROR: XSS detection '{xss_text[:30]}...' - {e}")
        
        pass_rate = (passed / total) * 100 if total > 0 else 0
        print(f"XSS Detection: {passed}/{total} ({pass_rate:.1f}%)")
        
        self.test_results.append({
            'test': 'xss_detection',
            'passed': passed,
            'total': total,
            'pass_rate': pass_rate
        })
        
        return pass_rate >= 90.0
    
    def test_large_input_handling(self) -> bool:
        """Test large input handling and memory safety"""
        print("\n=== Testing Large Input Handling ===")
        
        passed = 0
        total = 0
        
        # Large input test cases
        large_input_sizes = [1000, 10000, 100000, 1000000]  # 1KB, 10KB, 100KB, 1MB
        
        for size in large_input_sizes:
            total += 1
            try:
                # Generate large input
                large_text = "A" * size
                
                # Test with all detectors
                detector_results = {}
                max_memory_delta = 0
                max_processing_time = 0
                
                for detector_name, detector in self.detectors.items():
                    perf = self._measure_performance(detector.detect, large_text)
                    
                    if perf['success']:
                        detector_results[detector_name] = True
                        max_memory_delta = max(max_memory_delta, perf['memory_delta_mb'])
                        max_processing_time = max(max_processing_time, perf['processing_time_ms'])
                    else:
                        detector_results[detector_name] = False
                        print(f"FAILED: {detector_name} with {size} chars - {perf.get('error', 'Unknown error')}")
                
                # Check if all detectors handled the input successfully
                if all(detector_results.values()):
                    # Check memory and performance limits
                    if max_memory_delta < 100 and max_processing_time < 5000:  # 100MB, 5s
                        passed += 1
                        print(f"PASSED: Large input {size} chars - Memory: {max_memory_delta:.1f}MB, Time: {max_processing_time:.1f}ms")
                    else:
                        print(f"FAILED: Large input {size} chars - Memory: {max_memory_delta:.1f}MB, Time: {max_processing_time:.1f}ms")
                else:
                    print(f"FAILED: Large input {size} chars - Some detectors failed")
                    
            except Exception as e:
                print(f"ERROR: Large input {size} chars - {e}")
        
        pass_rate = (passed / total) * 100 if total > 0 else 0
        print(f"Large Input Handling: {passed}/{total} ({pass_rate:.1f}%)")
        
        self.test_results.append({
            'test': 'large_input_handling',
            'passed': passed,
            'total': total,
            'pass_rate': pass_rate
        })
        
        return pass_rate >= 90.0
    
    def test_pathological_inputs(self) -> bool:
        """Test pathological input patterns"""
        print("\n=== Testing Pathological Inputs ===")
        
        passed = 0
        total = 0
        
        # Pathological input patterns
        pathological_cases = [
            # Deeply nested structures
            '{"a":' * 1000 + '1' + '}' * 1000,
            '<div>' * 1000 + 'content' + '</div>' * 1000,
            
            # Repeated patterns
            'A' * 10000,
            'AB' * 5000,
            'ABC' * 3333,
            
            # Zero-width characters
            '\u200B' * 1000,
            '\u200C' * 1000,
            '\u200D' * 1000,
            
            # Mixed encodings
            'Hello' + '\u200B' + 'World' + '\u200C' + 'Test',
            
            # Extremely long lines
            'A' * 100000 + '\n' + 'B' * 100000,
            
            # Null bytes and control characters
            'Hello\x00World\x01\x02\x03',
            
            # Unicode normalization attacks
            'café' + '\u0301',  # Combining acute accent
            'naïve' + '\u0308',  # Combining diaeresis
        ]
        
        for pathological_input in pathological_cases:
            total += 1
            try:
                # Test with unicode detector (most likely to handle pathological inputs)
                perf = self._measure_performance(
                    self.detectors['unicode'].detect, pathological_input
                )
                
                if perf['success'] and perf['processing_time_ms'] < 1000:  # 1 second limit
                    passed += 1
                    print(f"PASSED: Pathological input '{pathological_input[:20]}...'")
                else:
                    print(f"FAILED: Pathological input '{pathological_input[:20]}...' - {perf.get('error', 'Timeout')}")
                    
            except Exception as e:
                print(f"ERROR: Pathological input '{pathological_input[:20]}...' - {e}")
        
        pass_rate = (passed / total) * 100 if total > 0 else 0
        print(f"Pathological Inputs: {passed}/{total} ({pass_rate:.1f}%)")
        
        self.test_results.append({
            'test': 'pathological_inputs',
            'passed': passed,
            'total': total,
            'pass_rate': pass_rate
        })
        
        return pass_rate >= 90.0
    
    def test_memory_safety(self) -> bool:
        """Test memory safety and leak detection"""
        print("\n=== Testing Memory Safety ===")
        
        passed = 0
        total = 0
        
        # Memory safety test cases
        memory_tests = [
            # Rapid successive calls
            ("rapid_calls", lambda: self._test_rapid_calls()),
            # Large object creation
            ("large_objects", lambda: self._test_large_objects()),
            # Memory cleanup
            ("memory_cleanup", lambda: self._test_memory_cleanup()),
        ]
        
        for test_name, test_func in memory_tests:
            total += 1
            try:
                initial_memory = self._get_memory_usage()
                result = test_func()
                final_memory = self._get_memory_usage()
                memory_delta = final_memory - initial_memory
                
                if result and memory_delta < 50:  # Less than 50MB increase
                    passed += 1
                    print(f"PASSED: {test_name} - Memory delta: {memory_delta:.1f}MB")
                else:
                    print(f"FAILED: {test_name} - Memory delta: {memory_delta:.1f}MB")
                    
            except Exception as e:
                print(f"ERROR: {test_name} - {e}")
        
        pass_rate = (passed / total) * 100 if total > 0 else 0
        print(f"Memory Safety: {passed}/{total} ({pass_rate:.1f}%)")
        
        self.test_results.append({
            'test': 'memory_safety',
            'passed': passed,
            'total': total,
            'pass_rate': pass_rate
        })
        
        return pass_rate >= 90.0
    
    def _test_rapid_calls(self) -> bool:
        """Test rapid successive detector calls"""
        try:
            test_input = "SELECT * FROM users WHERE id = 1"
            for _ in range(1000):
                for detector in self.detectors.values():
                    detector.detect(test_input)
            return True
        except Exception:
            return False
    
    def _test_large_objects(self) -> bool:
        """Test large object creation and cleanup"""
        try:
            large_objects = []
            for _ in range(100):
                large_objects.append("A" * 10000)
            
            # Process with detectors
            for obj in large_objects:
                self.detectors['unicode'].detect(obj)
            
            # Clear objects
            large_objects.clear()
            return True
        except Exception:
            return False
    
    def _test_memory_cleanup(self) -> bool:
        """Test memory cleanup after processing"""
        try:
            import gc
            
            # Create and process large data
            large_data = ["Test data " + str(i) for i in range(1000)]
            for data in large_data:
                self.detectors['unicode'].detect(data)
            
            # Force garbage collection
            gc.collect()
            return True
        except Exception:
            return False
    
    def run_all_tests(self) -> Dict[str, Any]:
        """Run all fuzz and security tests"""
        print("🧪 Starting Fuzz & Security Test Suite")
        print("=" * 60)
        
        start_time = time.time()
        
        # Run all tests
        tests = [
            self.test_unicode_fuzzing,
            self.test_emoji_handling,
            self.test_sql_injection_detection,
            self.test_xss_detection,
            self.test_large_input_handling,
            self.test_pathological_inputs,
            self.test_memory_safety,
        ]
        
        passed_tests = 0
        total_tests = len(tests)
        
        for test in tests:
            try:
                if test():
                    passed_tests += 1
            except Exception as e:
                print(f"ERROR: Test {test.__name__} failed with exception: {e}")
        
        end_time = time.time()
        total_duration = end_time - start_time
        
        # Calculate overall pass rate
        overall_pass_rate = (passed_tests / total_tests) * 100
        
        # Calculate detailed pass rate
        total_passed = sum(result['passed'] for result in self.test_results)
        total_cases = sum(result['total'] for result in self.test_results)
        detailed_pass_rate = (total_passed / total_cases) * 100 if total_cases > 0 else 0
        
        print("\n" + "=" * 60)
        print("📊 FUZZ & SECURITY TEST RESULTS")
        print("=" * 60)
        print(f"Overall Pass Rate: {passed_tests}/{total_tests} ({overall_pass_rate:.1f}%)")
        print(f"Detailed Pass Rate: {total_passed}/{total_cases} ({detailed_pass_rate:.1f}%)")
        print(f"Total Duration: {total_duration:.2f}s")
        
        print("\n📋 Test Breakdown:")
        for result in self.test_results:
            print(f"  {result['test']}: {result['passed']}/{result['total']} ({result['pass_rate']:.1f}%)")
        
        # Determine success
        success = overall_pass_rate >= 90.0 and detailed_pass_rate >= 90.0
        
        print(f"\n🎯 Target: 90%+ pass rate")
        print(f"✅ Result: {'PASSED' if success else 'FAILED'}")
        
        return {
            'overall_pass_rate': overall_pass_rate,
            'detailed_pass_rate': detailed_pass_rate,
            'passed_tests': passed_tests,
            'total_tests': total_tests,
            'total_passed': total_passed,
            'total_cases': total_cases,
            'duration': total_duration,
            'success': success,
            'test_results': self.test_results
        }


if __name__ == "__main__":
    # Run test suite
    test_suite = FuzzSecurityTestSuite()
    results = test_suite.run_all_tests()
    
    # Exit with appropriate code
    exit(0 if results['success'] else 1)
