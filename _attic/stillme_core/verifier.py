"""Verifier for StillMe Framework"""

import logging
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class VerificationStatus(Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"


class VerificationType(Enum):
    CODE_QUALITY = "code_quality"
    SECURITY = "security"
    PERFORMANCE = "performance"
    FUNCTIONALITY = "functionality"
    INTEGRATION = "integration"


@dataclass
class VerificationResult:
    """Verification result record"""

    result_id: str
    verification_type: VerificationType
    status: VerificationStatus
    description: str
    details: dict[str, Any]
    timestamp: datetime
    duration: float | None = None
    metadata: dict[str, Any] | None = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class LegacyVerifier:
    """Legacy Verifier for StillMe Framework - DEPRECATED"""

    def __init__(self):
        self.logger = logger
        self.verification_results: list[VerificationResult] = []
        self.verification_config = self._initialize_verification_config()
        self.logger.info("✅ Legacy Verifier initialized")

    def _initialize_verification_config(self) -> dict[str, Any]:
        """Initialize verification configuration"""
        return {
            "max_verification_time": 300,  # 5 minutes
            "parallel_verifications": 3,
            "retry_attempts": 2,
            "verification_types": [
                "code_quality",
                "security",
                "performance",
                "functionality",
                "integration",
            ],
            "pass_threshold": 0.8,
        }

    def verify_code_quality(
        self, code_content: str, file_path: str | None = None
    ) -> VerificationResult:
        """Verify code quality"""
        try:
            result_id = f"verify_{len(self.verification_results) + 1}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            start_time = datetime.now()

            # Simple code quality checks
            issues = []
            score = 100.0

            # Check for basic issues
            if len(code_content) == 0:
                issues.append("Empty code content")
                score -= 50.0

            if "TODO" in code_content:
                issues.append("Contains TODO comments")
                score -= 10.0

            if "FIXME" in code_content:
                issues.append("Contains FIXME comments")
                score -= 15.0

            if "print(" in code_content:
                issues.append("Contains print statements")
                score -= 5.0

            # Determine status
            if score >= 80:
                status = VerificationStatus.PASSED
            elif score >= 60:
                status = VerificationStatus.FAILED
            else:
                status = VerificationStatus.FAILED

            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()

            result = VerificationResult(
                result_id=result_id,
                verification_type=VerificationType.CODE_QUALITY,
                status=status,
                description=f"Code quality verification for {file_path or 'unknown file'}",
                details={
                    "score": score,
                    "issues": issues,
                    "file_path": file_path,
                    "code_length": len(code_content),
                },
                timestamp=datetime.now(),
                duration=duration,
            )

            self.verification_results.append(result)
            self.logger.info(
                f"✅ Code quality verification: {status.value} (score: {score:.1f})"
            )
            return result

        except Exception as e:
            self.logger.error(f"❌ Failed to verify code quality: {e}")
            raise

    def verify_security(
        self, code_content: str, file_path: str | None = None
    ) -> VerificationResult:
        """Verify security"""
        try:
            result_id = f"verify_{len(self.verification_results) + 1}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            start_time = datetime.now()

            # Simple security checks
            vulnerabilities = []
            score = 100.0

            # Check for common security issues
            if "password" in code_content.lower():
                vulnerabilities.append("Potential hardcoded password")
                score -= 20.0

            if "secret" in code_content.lower():
                vulnerabilities.append("Potential hardcoded secret")
                score -= 20.0

            if "eval(" in code_content:
                vulnerabilities.append("Use of eval() function")
                score -= 30.0

            if "exec(" in code_content:
                vulnerabilities.append("Use of exec() function")
                score -= 30.0

            if "subprocess" in code_content and "shell=True" in code_content:
                vulnerabilities.append("Unsafe subprocess with shell=True")
                score -= 25.0

            # Determine status
            if score >= 80:
                status = VerificationStatus.PASSED
            elif score >= 60:
                status = VerificationStatus.FAILED
            else:
                status = VerificationStatus.FAILED

            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()

            result = VerificationResult(
                result_id=result_id,
                verification_type=VerificationType.SECURITY,
                status=status,
                description=f"Security verification for {file_path or 'unknown file'}",
                details={
                    "score": score,
                    "vulnerabilities": vulnerabilities,
                    "file_path": file_path,
                    "code_length": len(code_content),
                },
                timestamp=datetime.now(),
                duration=duration,
            )

            self.verification_results.append(result)
            self.logger.info(
                f"✅ Security verification: {status.value} (score: {score:.1f})"
            )
            return result

        except Exception as e:
            self.logger.error(f"❌ Failed to verify security: {e}")
            raise

    def verify_performance(
        self, code_content: str, file_path: str | None = None
    ) -> VerificationResult:
        """Verify performance"""
        try:
            result_id = f"verify_{len(self.verification_results) + 1}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            start_time = datetime.now()

            # Simple performance checks
            issues = []
            score = 100.0

            # Check for performance issues
            if "while True:" in code_content:
                issues.append("Infinite loop detected")
                score -= 30.0

            if "for i in range(len(" in code_content:
                issues.append("Inefficient loop pattern")
                score -= 10.0

            if "time.sleep(" in code_content:
                issues.append("Blocking sleep operation")
                score -= 15.0

            # Determine status
            if score >= 80:
                status = VerificationStatus.PASSED
            elif score >= 60:
                status = VerificationStatus.FAILED
            else:
                status = VerificationStatus.FAILED

            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()

            result = VerificationResult(
                result_id=result_id,
                verification_type=VerificationType.PERFORMANCE,
                status=status,
                description=f"Performance verification for {file_path or 'unknown file'}",
                details={
                    "score": score,
                    "issues": issues,
                    "file_path": file_path,
                    "code_length": len(code_content),
                },
                timestamp=datetime.now(),
                duration=duration,
            )

            self.verification_results.append(result)
            self.logger.info(
                f"✅ Performance verification: {status.value} (score: {score:.1f})"
            )
            return result

        except Exception as e:
            self.logger.error(f"❌ Failed to verify performance: {e}")
            raise

    def run_comprehensive_verification(
        self, code_content: str, file_path: str | None = None
    ) -> list[VerificationResult]:
        """Run comprehensive verification"""
        try:
            results = []

            # Run all verification types
            results.append(self.verify_code_quality(code_content, file_path))
            results.append(self.verify_security(code_content, file_path))
            results.append(self.verify_performance(code_content, file_path))

            self.logger.info(
                f"🔍 Comprehensive verification completed: {len(results)} checks"
            )
            return results

        except Exception as e:
            self.logger.error(f"❌ Failed to run comprehensive verification: {e}")
            return []

    def get_verification_results_by_type(
        self, verification_type: VerificationType
    ) -> list[VerificationResult]:
        """Get verification results by type"""
        return [
            r
            for r in self.verification_results
            if r.verification_type == verification_type
        ]

    def get_verification_results_by_status(
        self, status: VerificationStatus
    ) -> list[VerificationResult]:
        """Get verification results by status"""
        return [r for r in self.verification_results if r.status == status]

    def get_verification_summary(self) -> dict[str, Any]:
        """Get verification summary"""
        try:
            total_verifications = len(self.verification_results)
            passed_verifications = len(
                self.get_verification_results_by_status(VerificationStatus.PASSED)
            )
            failed_verifications = len(
                self.get_verification_results_by_status(VerificationStatus.FAILED)
            )

            verifications_by_type = {}
            verifications_by_status = {}

            for result in self.verification_results:
                # By type
                type_key = result.verification_type.value
                verifications_by_type[type_key] = (
                    verifications_by_type.get(type_key, 0) + 1
                )

                # By status
                status_key = result.status.value
                verifications_by_status[status_key] = (
                    verifications_by_status.get(status_key, 0) + 1
                )

            # Calculate pass rate
            pass_rate = (passed_verifications / max(1, total_verifications)) * 100

            return {
                "total_verifications": total_verifications,
                "passed_verifications": passed_verifications,
                "failed_verifications": failed_verifications,
                "pass_rate": pass_rate,
                "verifications_by_type": verifications_by_type,
                "verifications_by_status": verifications_by_status,
                "verification_config": self.verification_config,
                "timestamp": datetime.now().isoformat(),
            }

        except Exception as e:
            self.logger.error(f"❌ Failed to get verification summary: {e}")
            return {"error": str(e)}

    def clear_verification_results(self):
        """Clear all verification results"""
        self.verification_results.clear()
        self.logger.info("🧹 All verification results cleared")

    def verify(
        self,
        step: dict[str, Any],
        exec_result: dict[str, Any],
        success_criteria: dict[str, Any] | None = None,
    ) -> bool | dict[str, Any]:
        """Verify execution result against step criteria"""
        try:
            # Use provided success_criteria or extract from step
            if success_criteria is None:
                success_criteria = step.get("success_criteria", {})

            # Ensure success_criteria is not None
            if success_criteria is None:
                success_criteria = {}

            expected_exit_code = success_criteria.get("exit_code", 0)
            stdout_patterns = success_criteria.get("stdout_patterns", [])
            stderr_patterns = success_criteria.get("stderr_patterns", [])

            # Check basic execution success
            if not exec_result.get("ok", False):
                return {
                    "passed": False,
                    "reason": "execution failed",
                    "details": exec_result,
                }

            # Check exit code
            actual_exit_code = exec_result.get("exit_code", 0)
            if actual_exit_code != expected_exit_code:
                return {
                    "passed": False,
                    "reason": f"exit code mismatch: expected {expected_exit_code}, got {actual_exit_code}",
                    "details": exec_result,
                }

            # Check stdout patterns
            stdout = exec_result.get("stdout", "")
            for pattern in stdout_patterns:
                if not self._check_patterns(stdout, [pattern]):
                    return {
                        "passed": False,
                        "reason": f"stdout pattern not matched: {pattern}",
                        "details": exec_result,
                    }

            # Check stderr patterns
            stderr = exec_result.get("stderr", "")
            for pattern in stderr_patterns:
                if not self._check_patterns(stderr, [pattern]):
                    return {
                        "passed": False,
                        "reason": f"stderr pattern not matched: {pattern}",
                        "details": exec_result,
                    }

            # Default success patterns if no custom criteria
            if not stdout_patterns and not stderr_patterns:
                success_patterns = [r"(\d+)\s+passed", r"PASSED", r"SUCCESS"]
                if self._check_patterns(stdout, success_patterns):
                    return {
                        "passed": True,
                        "reason": "success patterns matched",
                        "details": exec_result,
                    }
                else:
                    return {
                        "passed": False,
                        "reason": "no success patterns found in output",
                        "details": exec_result,
                    }

            return {
                "passed": True,
                "reason": "all criteria met",
                "details": exec_result,
            }

        except Exception as e:
            self.logger.error(f"Verification error: {e}")
            return {
                "passed": False,
                "reason": f"verification error: {e}",
                "details": exec_result,
            }

    def verify_test_results(self, exec_result: dict[str, Any]) -> dict[str, Any]:
        """Verify test execution results"""
        try:
            stdout = exec_result.get("stdout", "")
            exec_result.get("stderr", "")
            exit_code = exec_result.get("exit_code", 0)

            # Extract test statistics
            stats = self._extract_test_stats(stdout)

            # Determine if tests passed
            if exit_code == 0 and stats.get("failed", 0) == 0:
                return {
                    "passed": True,
                    "reason": "test results verification passed",
                    "stats": stats,
                    "details": {"stats": stats, "exec_result": exec_result},
                }
            else:
                return {
                    "passed": False,
                    "reason": "test results verification failed",
                    "stats": stats,
                    "details": {"stats": stats, "exec_result": exec_result},
                }

        except Exception as e:
            self.logger.error(f"Test verification error: {e}")
            return {
                "passed": False,
                "reason": f"test verification error: {e}",
                "details": exec_result,
            }

    def _extract_test_stats(self, text: str) -> dict[str, Any]:
        """Extract test statistics from output text"""
        import re

        stats = {"passed": 0, "failed": 0, "skipped": 0, "total": 0, "collected": 0}

        # Common test output patterns
        patterns = {
            "passed": [r"(\d+)\s+passed", r"PASSED\s*(\d+)", r"✓\s*(\d+)"],
            "failed": [r"(\d+)\s+failed", r"FAILED\s*(\d+)", r"✗\s*(\d+)"],
            "skipped": [r"(\d+)\s+skipped", r"SKIPPED\s*(\d+)"],
            "total": [r"(\d+)\s+total", r"(\d+)\s+tests"],
            "collected": [r"collected\s+(\d+)\s+items?", r"(\d+)\s+collected"],
        }

        for stat_type, pattern_list in patterns.items():
            for pattern in pattern_list:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    try:
                        stats[stat_type] = int(match.group(1))
                    except (ValueError, IndexError):
                        pass

        # Calculate total if not found
        if stats["total"] == 0:
            stats["total"] = stats["passed"] + stats["failed"] + stats["skipped"]

        return stats

    def _check_patterns(self, text: str, patterns: list[str]) -> bool:
        """Check if text matches any of the patterns"""
        import re

        for pattern in patterns:
            try:
                if re.search(pattern, text, re.IGNORECASE):
                    return True
            except re.error:
                # If pattern is invalid, treat as literal string match
                if pattern in text:
                    return True

        return False


# Backward compatibility alias
Verifier = LegacyVerifier
