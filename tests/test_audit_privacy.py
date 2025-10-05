from stillme_core.compat import PIIRedactor, PIIType

"""
Test Suite for Enterprise Audit & Privacy
=========================================

Comprehensive tests for PII redaction and structured logging compliance.
Tests cover various PII types, Unicode support, and log format validation.

Author: StillMe AI Framework
Created: 2025-01-08
"""

import json
import logging
import os
import re
import tempfile
import time
from dataclasses import dataclass
from typing import Any

from stillme_core.gateway.logging_mw import LoggingMiddleware, StructuredLogger


@dataclass
class TestCase:
    """Test case for PII redaction"""

    name: str
    input_text: str
    expected_pii_types: list[PIIType]
    should_redact: bool
    description: str


class EnterpriseAuditPrivacyTestSuite:
    """
    Comprehensive test suite for Enterprise Audit & Privacy features

    Tests:
    - PII redaction accuracy
    - Log format compliance
    - Unicode support
    - Performance metrics
    - Schema validation
    """

    def __init__(self):
        """Initialize test suite"""
        self.redactor = PIIRedactor()
        self.middleware = LoggingMiddleware()
        self.logger = StructuredLogger("test.audit")
        self.test_results = []
        self.passed_tests = 0
        self.total_tests = 0

    def _load_test_cases(self) -> list[TestCase]:
        """Load comprehensive test cases for PII redaction"""
        return [
            # Email tests
            TestCase(
                name="email_basic",
                input_text="Contact me at john.doe@example.com for more info",
                expected_pii_types=[PIIType.EMAIL],
                should_redact=True,
                description="Basic email redaction",
            ),
            TestCase(
                name="email_unicode",
                input_text="Email: 测试@测试.com or admin@公司.cn",
                expected_pii_types=[PIIType.EMAIL],
                should_redact=True,
                description="Unicode email addresses",
            ),
            TestCase(
                name="email_multiple",
                input_text="Send to alice@test.com and bob@example.org",
                expected_pii_types=[PIIType.EMAIL, PIIType.EMAIL],
                should_redact=True,
                description="Multiple email addresses",
            ),
            # Phone tests
            TestCase(
                name="phone_us",
                input_text="Call me at (555) 123-4567 or 555-123-4567",
                expected_pii_types=[PIIType.PHONE, PIIType.PHONE],
                should_redact=True,
                description="US phone numbers",
            ),
            TestCase(
                name="phone_international",
                input_text="Phone: +1-555-123-4567 or +44 20 7946 0958",
                expected_pii_types=[PIIType.PHONE, PIIType.PHONE],
                should_redact=True,
                description="International phone numbers",
            ),
            # Name tests
            TestCase(
                name="name_basic",
                input_text="John Smith and Jane Doe are working on this project",
                expected_pii_types=[PIIType.NAME, PIIType.NAME],
                should_redact=True,
                description="Basic name patterns",
            ),
            TestCase(
                name="name_formal",
                input_text="Dr. John A. Smith, Jr. and Ms. Jane B. Doe",
                expected_pii_types=[PIIType.NAME, PIIType.NAME],
                should_redact=True,
                description="Formal name patterns",
            ),
            # IP address tests
            TestCase(
                name="ipv4",
                input_text="Server at 192.168.1.1 and 10.0.0.1",
                expected_pii_types=[PIIType.IP_ADDRESS, PIIType.IP_ADDRESS],
                should_redact=True,
                description="IPv4 addresses",
            ),
            TestCase(
                name="ipv6",
                input_text="IPv6: 2001:0db8:85a3:0000:0000:8a2e:0370:7334",
                expected_pii_types=[PIIType.IP_ADDRESS],
                should_redact=True,
                description="IPv6 addresses",
            ),
            # Token tests
            TestCase(
                name="bearer_token",
                input_text="Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9",
                expected_pii_types=[PIIType.TOKEN],
                should_redact=True,
                description="Bearer token",
            ),
            TestCase(
                name="api_key",
                input_text="API key: sk-1234567890abcdef1234567890abcdef",
                expected_pii_types=[PIIType.TOKEN],
                should_redact=True,
                description="API key",
            ),
            # ID number tests
            TestCase(
                name="id_number",
                input_text="ID: 123456789 and License: AB1234567",
                expected_pii_types=[PIIType.ID_NUMBER, PIIType.ID_NUMBER],
                should_redact=True,
                description="ID numbers",
            ),
            # Credit card tests
            TestCase(
                name="credit_card",
                input_text="Card: 4111 1111 1111 1111 or 4111-1111-1111-1111",
                expected_pii_types=[PIIType.CREDIT_CARD, PIIType.CREDIT_CARD],
                should_redact=True,
                description="Credit card numbers",
            ),
            # SSN tests
            TestCase(
                name="ssn",
                input_text="SSN: 123-45-6789 or 123456789",
                expected_pii_types=[PIIType.SSN, PIIType.SSN],
                should_redact=True,
                description="Social Security Numbers",
            ),
            # Mixed PII tests
            TestCase(
                name="mixed_pii",
                input_text="User John Smith (john@example.com, 555-123-4567) from 192.168.1.1",
                expected_pii_types=[
                    PIIType.NAME,
                    PIIType.EMAIL,
                    PIIType.PHONE,
                    PIIType.IP_ADDRESS,
                ],
                should_redact=True,
                description="Mixed PII types",
            ),
            # Unicode tests
            TestCase(
                name="unicode_text",
                input_text="用户张三 (zhang@测试.com) 电话: +86-138-0013-8000",
                expected_pii_types=[PIIType.NAME, PIIType.EMAIL, PIIType.PHONE],
                should_redact=True,
                description="Unicode text with PII",
            ),
            # No PII tests
            TestCase(
                name="no_pii",
                input_text="This is a normal text without any personal information",
                expected_pii_types=[],
                should_redact=False,
                description="Text without PII",
            ),
            # Edge cases
            TestCase(
                name="edge_case_short",
                input_text="a@b.c",
                expected_pii_types=[PIIType.EMAIL],
                should_redact=True,
                description="Short email address",
            ),
            TestCase(
                name="edge_case_malformed",
                input_text="not-an-email and 123",
                expected_pii_types=[],
                should_redact=False,
                description="Malformed PII",
            ),
            TestCase(
                name="edge_case_token",
                input_text="Token: sk-1234567890abcdef",
                expected_pii_types=[PIIType.TOKEN],
                should_redact=True,
                description="OpenAI-style API key",
            ),
        ]

    def test_pii_redaction_accuracy(self) -> bool:
        """Test PII redaction accuracy"""
        print("\n=== Testing PII Redaction Accuracy ===")

        test_cases = self._load_test_cases()
        passed = 0
        total = len(test_cases)

        for test_case in test_cases:
            try:
                redacted_text, matches = self.redactor.redact(test_case.input_text)

                # Check if redaction occurred as expected
                if test_case.should_redact:
                    if len(matches) == 0:
                        print(
                            f"FAILED: {test_case.name} - Expected redaction but none occurred"
                        )
                        continue

                    # Check if expected PII types were detected
                    detected_types = [match.pii_type for match in matches]
                    if not all(
                        pii_type in detected_types
                        for pii_type in test_case.expected_pii_types
                    ):
                        print(
                            f"FAILED: {test_case.name} - Expected types {test_case.expected_pii_types}, got {detected_types}"
                        )
                        continue
                else:
                    if len(matches) > 0:
                        print(
                            f"FAILED: {test_case.name} - Expected no redaction but {len(matches)} matches found"
                        )
                        continue

                # Check if redacted text contains redaction tags
                if test_case.should_redact and "[REDACTED:" not in redacted_text:
                    print(f"FAILED: {test_case.name} - No redaction tags found")
                    continue

                print(f"PASSED: {test_case.name} - {test_case.description}")
                passed += 1

            except Exception as e:
                print(f"ERROR: {test_case.name} - {e}")

        pass_rate = (passed / total) * 100
        print(f"PII Redaction Accuracy: {passed}/{total} ({pass_rate:.1f}%)")

        self.test_results.append(
            {
                "test": "pii_redaction_accuracy",
                "passed": passed,
                "total": total,
                "pass_rate": pass_rate,
            }
        )

        return pass_rate >= 90.0

    def test_log_format_compliance(self) -> bool:
        """Test log format compliance with JSON schema"""
        print("\n=== Testing Log Format Compliance ===")

        passed = 0
        total = 0

        # Test required fields
        required_fields = [
            "timestamp",
            "level",
            "trace_id",
            "span_id",
            "user_id_hash",
            "event",
            "pii_redacted",
            "message",
        ]

        try:
            # Create temporary log file
            with tempfile.NamedTemporaryFile(
                mode="w", delete=False, suffix=".log"
            ) as f:
                temp_log_file = f.name

            # Configure logger to write to file
            file_handler = logging.FileHandler(temp_log_file)
            file_handler.setFormatter(logging.Formatter("%(message)s"))

            test_logger = StructuredLogger("test.log_format")
            test_logger.logger.addHandler(file_handler)
            test_logger.logger.setLevel(logging.INFO)

            # Test various log levels
            test_cases = [
                ("info", "test_info", "This is an info message"),
                ("warning", "test_warning", "This is a warning message"),
                ("error", "test_error", "This is an error message"),
                ("debug", "test_debug", "This is a debug message"),
            ]

            for level, event, message in test_cases:
                total += 1
                try:
                    # Log message
                    getattr(test_logger, level)(event, message)

                    # Read and validate log entry
                    with open(temp_log_file) as f:
                        log_lines = f.readlines()

                    if not log_lines:
                        print(f"FAILED: {level} - No log entry written")
                        continue

                    # Parse JSON
                    log_entry = json.loads(log_lines[-1])

                    # Check required fields
                    missing_fields = [
                        field for field in required_fields if field not in log_entry
                    ]
                    if missing_fields:
                        print(f"FAILED: {level} - Missing fields: {missing_fields}")
                        continue

                    # Check field types
                    if not isinstance(log_entry["pii_redacted"], bool):
                        print(f"FAILED: {level} - pii_redacted should be boolean")
                        continue

                    if not isinstance(log_entry["timestamp"], str):
                        print(f"FAILED: {level} - timestamp should be string")
                        continue

                    print(f"PASSED: {level} - Log format compliance")
                    passed += 1

                except Exception as e:
                    print(f"ERROR: {level} - {e}")

            # Clean up
            try:
                os.unlink(temp_log_file)
            except OSError:
                pass  # File might be locked, ignore

        except Exception as e:
            print(f"ERROR: Log format test setup failed - {e}")
            return False

        pass_rate = (passed / total) * 100 if total > 0 else 0
        print(f"Log Format Compliance: {passed}/{total} ({pass_rate:.1f}%)")

        self.test_results.append(
            {
                "test": "log_format_compliance",
                "passed": passed,
                "total": total,
                "pass_rate": pass_rate,
            }
        )

        return pass_rate >= 90.0

    def test_pii_redaction_in_logs(self) -> bool:
        """Test that logs don't contain raw PII"""
        print("\n=== Testing PII Redaction in Logs ===")

        passed = 0
        total = 0

        # Test cases with PII
        test_cases = [
            ("User john@example.com called", "email"),
            ("Phone: 555-123-4567", "phone"),
            ("Name: John Smith", "name"),
            ("IP: 192.168.1.1", "ip"),
            ("Token: sk-1234567890abcdef", "token"),
        ]

        try:
            # Create temporary log file
            with tempfile.NamedTemporaryFile(
                mode="w", delete=False, suffix=".log"
            ) as f:
                temp_log_file = f.name

            # Configure logger to write to file
            file_handler = logging.FileHandler(temp_log_file)
            file_handler.setFormatter(logging.Formatter("%(message)s"))

            test_logger = StructuredLogger("test.pii_logs")
            test_logger.logger.addHandler(file_handler)
            test_logger.logger.setLevel(logging.INFO)

            for message, pii_type in test_cases:
                total += 1
                try:
                    # Log message with PII
                    test_logger.info("test_pii", message)

                    # Read log entry
                    with open(temp_log_file) as f:
                        log_lines = f.readlines()

                    if not log_lines:
                        print(f"FAILED: {pii_type} - No log entry written")
                        continue

                    # Parse JSON
                    log_entry = json.loads(log_lines[-1])

                    # Check if PII was redacted
                    if not log_entry.get("pii_redacted", False):
                        print(f"FAILED: {pii_type} - PII not marked as redacted")
                        continue

                    # Check if raw PII is still in message
                    if (
                        pii_type == "email"
                        and "@" in log_entry["message"]
                        and "REDACTED" not in log_entry["message"]
                    ):
                        print(f"FAILED: {pii_type} - Raw email found in log")
                        continue

                    if (
                        pii_type == "phone"
                        and re.search(r"\d{3}-\d{3}-\d{4}", log_entry["message"])
                        and "REDACTED" not in log_entry["message"]
                    ):
                        print(f"FAILED: {pii_type} - Raw phone found in log")
                        continue

                    print(f"PASSED: {pii_type} - PII properly redacted")
                    passed += 1

                except Exception as e:
                    print(f"ERROR: {pii_type} - {e}")

            # Clean up
            try:
                os.unlink(temp_log_file)
            except OSError:
                pass  # File might be locked, ignore

        except Exception as e:
            print(f"ERROR: PII redaction test setup failed - {e}")
            return False

        pass_rate = (passed / total) * 100 if total > 0 else 0
        print(f"PII Redaction in Logs: {passed}/{total} ({pass_rate:.1f}%)")

        self.test_results.append(
            {
                "test": "pii_redaction_in_logs",
                "passed": passed,
                "total": total,
                "pass_rate": pass_rate,
            }
        )

        return pass_rate >= 90.0

    def test_unicode_support(self) -> bool:
        """Test Unicode support in PII redaction"""
        print("\n=== Testing Unicode Support ===")

        passed = 0
        total = 0

        # Unicode test cases
        unicode_cases = [
            ("Email: 测试@测试.com", "Chinese email"),
            ("Phone: +86-138-0013-8000", "Chinese phone"),
            ("Name: 张三", "Chinese name"),
            ("Email: тест@тест.ru", "Russian email"),
            ("Name: Иван Петров", "Russian name"),
            ("Email: テスト@テスト.jp", "Japanese email"),
        ]

        for text, description in unicode_cases:
            total += 1
            try:
                redacted_text, matches = self.redactor.redact(text)

                # Check if redaction occurred
                if len(matches) == 0:
                    print(f"FAILED: {description} - No redaction occurred")
                    continue

                # Check if redacted text is valid
                if not redacted_text or len(redacted_text) == 0:
                    print(f"FAILED: {description} - Empty redacted text")
                    continue

                # Check if redaction tags are present
                if "[REDACTED:" not in redacted_text:
                    print(f"FAILED: {description} - No redaction tags")
                    continue

                print(f"PASSED: {description} - Unicode redaction successful")
                passed += 1

            except Exception as e:
                print(f"ERROR: {description} - {e}")

        pass_rate = (passed / total) * 100 if total > 0 else 0
        print(f"Unicode Support: {passed}/{total} ({pass_rate:.1f}%)")

        self.test_results.append(
            {
                "test": "unicode_support",
                "passed": passed,
                "total": total,
                "pass_rate": pass_rate,
            }
        )

        return pass_rate >= 90.0

    def test_performance(self) -> bool:
        """Test performance of PII redaction"""
        print("\n=== Testing Performance ===")

        try:
            import time

            # Test with large text
            large_text = "User john@example.com (555-123-4567) from 192.168.1.1 " * 100

            # Measure redaction time
            start_time = time.time()
            redacted_text, matches = self.redactor.redact(large_text)
            end_time = time.time()

            duration_ms = (end_time - start_time) * 1000

            # Performance requirements
            max_duration_ms = 100  # 100ms for large text

            if duration_ms > max_duration_ms:
                print(
                    f"FAILED: Performance - {duration_ms:.2f}ms > {max_duration_ms}ms"
                )
                return False

            print(f"PASSED: Performance - {duration_ms:.2f}ms for large text")

            self.test_results.append(
                {
                    "test": "performance",
                    "passed": 1,
                    "total": 1,
                    "pass_rate": 100.0,
                    "duration_ms": duration_ms,
                }
            )

            return True

        except Exception as e:
            print(f"ERROR: Performance test failed - {e}")
            return False

    def run_all_tests(self) -> dict[str, Any]:
        """Run all tests and return results"""
        print("🧪 Starting Enterprise Audit & Privacy Test Suite")
        print("=" * 60)

        start_time = time.time()

        # Run all tests
        tests = [
            self.test_pii_redaction_accuracy,
            self.test_log_format_compliance,
            self.test_pii_redaction_in_logs,
            self.test_unicode_support,
            self.test_performance,
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
        total_passed = sum(result["passed"] for result in self.test_results)
        total_cases = sum(result["total"] for result in self.test_results)
        detailed_pass_rate = (
            (total_passed / total_cases) * 100 if total_cases > 0 else 0
        )

        print("\n" + "=" * 60)
        print("📊 ENTERPRISE AUDIT & PRIVACY TEST RESULTS")
        print("=" * 60)
        print(
            f"Overall Pass Rate: {passed_tests}/{total_tests} ({overall_pass_rate:.1f}%)"
        )
        print(
            f"Detailed Pass Rate: {total_passed}/{total_cases} ({detailed_pass_rate:.1f}%)"
        )
        print(f"Total Duration: {total_duration:.2f}s")

        print("\n📋 Test Breakdown:")
        for result in self.test_results:
            print(
                f"  {result['test']}: {result['passed']}/{result['total']} ({result['pass_rate']:.1f}%)"
            )

        # Determine success
        success = overall_pass_rate >= 90.0 and detailed_pass_rate >= 90.0

        print("\n🎯 Target: 90%+ pass rate")
        print(f"✅ Result: {'PASSED' if success else 'FAILED'}")

        return {
            "overall_pass_rate": overall_pass_rate,
            "detailed_pass_rate": detailed_pass_rate,
            "passed_tests": passed_tests,
            "total_tests": total_tests,
            "total_passed": total_passed,
            "total_cases": total_cases,
            "duration": total_duration,
            "success": success,
            "test_results": self.test_results,
        }


if __name__ == "__main__":
    # Run test suite
    test_suite = EnterpriseAuditPrivacyTestSuite()
    results = test_suite.run_all_tests()

    # Exit with appropriate code
    exit(0 if results["success"] else 1)
