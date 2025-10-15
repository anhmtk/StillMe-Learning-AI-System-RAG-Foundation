from typing import Any

#!/usr/bin/env python3
"""
🔥 Multi-Modal Torture Test Suite - Phase 3 Clarification Core
=============================================================

Enterprise QA Lead - AI Reliability Division
Mục tiêu: Đẩy Multi-Modal Clarification vào tình huống "ác mộng thực tế"

Author: StillMe Framework Team
Version: 1.0.0
"""

import tempfile
import time

from stillme_core.modules.audit_logger import AuditLogger

# Import Phase 3 modules
from stillme_core.modules.clarification_handler import ClarificationHandler


class MultiModalTortureTestSuite:
    """Multi-Modal Torture Test Suite for Phase 3 Clarification Core"""

    def __init__(self):
        self.handler = ClarificationHandler()
        self.temp_audit_file = tempfile.NamedTemporaryFile(
            mode="w+", delete=False, suffix=".jsonl"
        )

        # Setup audit logger
        audit_config = {
            "enabled": True,
            "redact_pii": True,
            "log_file": self.temp_audit_file.name,
            "privacy_filters": ["email", "password", "api_key", "token", "secret"],
        }
        self.audit_logger = AuditLogger(audit_config)

        # Clear the temp file for clean tests
        self.temp_audit_file.truncate(0)

    def test_code_syntax_error_torture(self) -> bool:
        """Test: Multiple Python syntax errors → must handle gracefully"""
        try:
            # Test 1: Missing colon
            broken_code1 = "def foo(\n    return 123"
            result1 = self.handler.detect_ambiguity(broken_code1)
            assert result1 is not None
            assert result1.needs_clarification is True

            # Test 2: Missing parenthesis
            broken_code2 = "def bar:\n    return 456"
            result2 = self.handler.detect_ambiguity(broken_code2)
            assert result2 is not None
            assert result2.needs_clarification is True

            # Test 3: Indentation error
            broken_code3 = "def baz():\nreturn 789"
            result3 = self.handler.detect_ambiguity(broken_code3)
            assert result3 is not None
            assert result3.needs_clarification is True

            return True
        except Exception as e:
            print(f"ERROR in test_code_syntax_error_torture: {e}")
            return False

    def test_multiple_functions_torture(self) -> bool:
        """Test: Code with 10+ functions → must ask which to focus on"""
        try:
            # Generate code with 10 functions
            functions = []
            for i in range(10):
                functions.append(f"def function_{i}():\n    return {i}")

            multi_function_code = "\n\n".join(functions)
            result = self.handler.detect_ambiguity(multi_function_code)

            assert result is not None
            assert result.needs_clarification is True
            assert result.question is not None
            assert len(result.question) > 10

            return True
        except Exception as e:
            print(f"ERROR in test_multiple_functions_torture: {e}")
            return False

    def test_corrupted_image_base64(self) -> bool:
        """Test: Corrupted base64 image → must handle gracefully"""
        try:
            # Create corrupted base64 image
            corrupted_base64 = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHggJ/PchI7wAAAABJRU5ErkJggg=="

            # Test with corrupted image
            result = self.handler.detect_ambiguity(corrupted_base64)
            assert result is not None
            assert result.needs_clarification is True

            return True
        except Exception as e:
            print(f"ERROR in test_corrupted_image_base64: {e}")
            return False

    def test_mixed_content_torture(self) -> bool:
        """Test: Text + Code + Image mixed → must handle gracefully"""
        try:
            mixed_content = """
            Fix this code:

            def broken_function(
                return "hello"

            And also process this image: data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHggJ/PchI7wAAAABJRU5ErkJggg==

            Make it better!
            """

            result = self.handler.detect_ambiguity(mixed_content)
            assert result is not None
            assert result.needs_clarification is True

            return True
        except Exception as e:
            print(f"ERROR in test_mixed_content_torture: {e}")
            return False

    def test_large_code_file_torture(self) -> bool:
        """Test: Large code file (1000+ lines) → must not hang"""
        try:
            # Generate large code file
            large_code = "def function_0():\n    return 0\n\n" * 500  # 1000+ lines

            start_time = time.time()
            result = self.handler.detect_ambiguity(large_code)
            end_time = time.time()

            execution_time = end_time - start_time
            assert execution_time < 5.0  # Should complete within 5 seconds
            assert result is not None

            return True
        except Exception as e:
            print(f"ERROR in test_large_code_file_torture: {e}")
            return False

    def test_nested_code_blocks_torture(self) -> bool:
        """Test: Nested code blocks with errors → must handle gracefully"""
        try:
            nested_code = """
            def outer_function():
                def inner_function():
                    def deep_function():
                        return "deep"
                    return deep_function()
                return inner_function()

            def another_function():
                if True:
                    if False:
                        return "nested"
                    else:
                        return "else"
                return "end"
            """

            result = self.handler.detect_ambiguity(nested_code)
            assert result is not None
            assert result.needs_clarification is True

            return True
        except Exception as e:
            print(f"ERROR in test_nested_code_blocks_torture: {e}")
            return False

    def test_unicode_in_code_torture(self) -> bool:
        """Test: Unicode characters in code → must handle gracefully"""
        try:
            unicode_code = """
            def 函数名():
                return "中文"

            def 関数名():
                return "日本語"

            def 함수명():
                return "한국어"
            """

            result = self.handler.detect_ambiguity(unicode_code)
            assert result is not None
            assert result.needs_clarification is True

            return True
        except Exception as e:
            print(f"ERROR in test_unicode_in_code_torture: {e}")
            return False

    def test_malformed_json_torture(self) -> bool:
        """Test: Malformed JSON in input → must handle gracefully"""
        try:
            malformed_json = '{"key": "value", "missing": "quote}'

            result = self.handler.detect_ambiguity(malformed_json)
            assert result is not None
            assert result.needs_clarification is True

            return True
        except Exception as e:
            print(f"ERROR in test_malformed_json_torture: {e}")
            return False

    def test_sql_injection_in_code_torture(self) -> bool:
        """Test: SQL injection in code → must handle gracefully"""
        try:
            sql_injection_code = """
            def query_user():
                user_id = "1; DROP TABLE users; --"
                query = f"SELECT * FROM users WHERE id = {user_id}"
                return query
            """

            result = self.handler.detect_ambiguity(sql_injection_code)
            assert result is not None
            assert result.needs_clarification is True

            return True
        except Exception as e:
            print(f"ERROR in test_sql_injection_in_code_torture: {e}")
            return False

    def test_xss_in_code_torture(self) -> bool:
        """Test: XSS in code → must handle gracefully"""
        try:
            xss_code = """
            def render_html():
                user_input = "<script>alert('XSS')</script>"
                return f"<div>{user_input}</div>"
            """

            result = self.handler.detect_ambiguity(xss_code)
            assert result is not None
            assert result.needs_clarification is True

            return True
        except Exception as e:
            print(f"ERROR in test_xss_in_code_torture: {e}")
            return False

    def run_all_tests(self) -> dict[str, Any]:
        """Run all Multi-Modal Torture tests"""
        print("🔥 Starting Multi-Modal Torture Test Suite")

        tests = [
            ("Code Syntax Error Torture", self.test_code_syntax_error_torture),
            ("Multiple Functions Torture", self.test_multiple_functions_torture),
            ("Corrupted Image Base64", self.test_corrupted_image_base64),
            ("Mixed Content Torture", self.test_mixed_content_torture),
            ("Large Code File Torture", self.test_large_code_file_torture),
            ("Nested Code Blocks Torture", self.test_nested_code_blocks_torture),
            ("Unicode in Code Torture", self.test_unicode_in_code_torture),
            ("Malformed JSON Torture", self.test_malformed_json_torture),
            ("SQL Injection in Code Torture", self.test_sql_injection_in_code_torture),
            ("XSS in Code Torture", self.test_xss_in_code_torture),
        ]

        results = []
        passed = 0
        failed = 0

        for test_name, test_func in tests:
            try:
                start_time = time.time()
                result = test_func()
                execution_time = time.time() - start_time

                if result:
                    print(f"✅ {test_name} - PASSED ({execution_time:.3f}s)")
                    passed += 1
                else:
                    print(f"❌ {test_name} - FAILED ({execution_time:.3f}s)")
                    failed += 1

                results.append(
                    {
                        "name": test_name,
                        "passed": result,
                        "execution_time": execution_time,
                    }
                )

            except Exception as e:
                print(f"❌ {test_name} - ERROR: {e}")
                failed += 1
                results.append(
                    {
                        "name": test_name,
                        "passed": False,
                        "execution_time": 0,
                        "error": str(e),
                    }
                )

        total = passed + failed
        pass_rate = (passed / total) * 100 if total > 0 else 0

        print("\n📊 Multi-Modal Torture Test Summary:")
        print(f"   Total Tests: {total}")
        print(f"   Passed: {passed}")
        print(f"   Failed: {failed}")
        print(f"   Pass Rate: {pass_rate:.1f}%")

        return {
            "total_tests": total,
            "passed_tests": passed,
            "failed_tests": failed,
            "pass_rate": pass_rate,
            "results": results,
        }


if __name__ == "__main__":
    # Run Multi-Modal Torture test suite directly
    suite = MultiModalTortureTestSuite()
    results = suite.run_all_tests()

    if results["pass_rate"] >= 90:
        print("🎉 Multi-Modal Torture tests passed! System is production-ready.")
    else:
        print("⚠️  Some Multi-Modal Torture tests failed - review and fix issues")
