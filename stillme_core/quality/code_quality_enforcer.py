"""Code Quality Enforcer for StillMe Framework"""

import logging
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

class QualityLevel(Enum):
    EXCELLENT = "excellent"
    GOOD = "good"
    FAIR = "fair"
    POOR = "poor"
    CRITICAL = "critical"

class QualityCategory(Enum):
    STYLE = "style"
    COMPLEXITY = "complexity"
    SECURITY = "security"
    PERFORMANCE = "performance"
    MAINTAINABILITY = "maintainability"
    TESTABILITY = "testability"

@dataclass
class QualityViolation:
    """Quality violation record"""
    violation_id: str
    category: QualityCategory
    level: QualityLevel
    file_path: str
    line_number: int
    description: str
    suggested_fix: str
    timestamp: datetime
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

class CodeQualityEnforcer:
    """Code quality enforcer for StillMe Framework"""

    def __init__(self):
        self.logger = logger
        self.violations: List[QualityViolation] = []
        self.quality_rules = self._initialize_quality_rules()
        self.logger.info("✅ CodeQualityEnforcer initialized")

    def _initialize_quality_rules(self) -> Dict[QualityCategory, List[str]]:
        """Initialize quality rules"""
        return {
            QualityCategory.STYLE: [
                "line_length_exceeded",
                "missing_docstring",
                "unused_import",
                "trailing_whitespace"
            ],
            QualityCategory.COMPLEXITY: [
                "cyclomatic_complexity_high",
                "nested_depth_exceeded",
                "function_too_long",
                "class_too_large"
            ],
            QualityCategory.SECURITY: [
                "hardcoded_secret",
                "sql_injection_risk",
                "unsafe_file_operation",
                "weak_cryptography"
            ],
            QualityCategory.PERFORMANCE: [
                "inefficient_loop",
                "unnecessary_computation",
                "memory_leak_risk",
                "blocking_operation"
            ],
            QualityCategory.MAINTAINABILITY: [
                "duplicate_code",
                "magic_number",
                "poor_naming",
                "tight_coupling"
            ],
            QualityCategory.TESTABILITY: [
                "missing_tests",
                "untestable_code",
                "hard_dependencies",
                "side_effects"
            ]
        }

    def analyze_code_quality(self,
                           file_path: str,
                           code_content: str,
                           metadata: Dict[str, Any] = None) -> List[QualityViolation]:
        """Analyze code quality and return violations"""
        try:
            violations = []

            # Check style violations
            style_violations = self._check_style_violations(file_path, code_content)
            violations.extend(style_violations)

            # Check complexity violations
            complexity_violations = self._check_complexity_violations(file_path, code_content)
            violations.extend(complexity_violations)

            # Check security violations
            security_violations = self._check_security_violations(file_path, code_content)
            violations.extend(security_violations)

            # Check performance violations
            performance_violations = self._check_performance_violations(file_path, code_content)
            violations.extend(performance_violations)

            # Check maintainability violations
            maintainability_violations = self._check_maintainability_violations(file_path, code_content)
            violations.extend(maintainability_violations)

            # Check testability violations
            testability_violations = self._check_testability_violations(file_path, code_content)
            violations.extend(testability_violations)

            # Record violations
            for violation in violations:
                self.violations.append(violation)
                self.logger.warning(f"⚠️ Quality violation: {violation.category.value} - {violation.description}")

            return violations

        except Exception as e:
            self.logger.error(f"❌ Failed to analyze code quality: {e}")
            return []

    def _check_style_violations(self, file_path: str, code_content: str) -> List[QualityViolation]:
        """Check for style violations"""
        violations = []
        lines = code_content.split('\n')

        for i, line in enumerate(lines, 1):
            # Check line length
            if len(line) > 120:
                violation = QualityViolation(
                    violation_id=f"style_{len(self.violations) + 1}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                    category=QualityCategory.STYLE,
                    level=QualityLevel.FAIR,
                    file_path=file_path,
                    line_number=i,
                    description=f"Line length exceeds 120 characters ({len(line)} chars)",
                    suggested_fix="Break long lines into multiple lines",
                    timestamp=datetime.now()
                )
                violations.append(violation)

            # Check trailing whitespace
            if line.rstrip() != line:
                violation = QualityViolation(
                    violation_id=f"style_{len(self.violations) + 1}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                    category=QualityCategory.STYLE,
                    level=QualityLevel.GOOD,
                    file_path=file_path,
                    line_number=i,
                    description="Trailing whitespace detected",
                    suggested_fix="Remove trailing whitespace",
                    timestamp=datetime.now()
                )
                violations.append(violation)

        return violations

    def _check_complexity_violations(self, file_path: str, code_content: str) -> List[QualityViolation]:
        """Check for complexity violations"""
        violations = []

        # Simple complexity check - count nested structures
        lines = code_content.split('\n')
        max_nesting = 0
        current_nesting = 0

        for i, line in enumerate(lines, 1):
            stripped = line.strip()
            if stripped.startswith(('if ', 'for ', 'while ', 'try:', 'with ', 'class ', 'def ')):
                current_nesting += 1
                max_nesting = max(max_nesting, current_nesting)
            elif stripped.startswith(('else:', 'elif ', 'except:', 'finally:')):
                # These don't increase nesting
                pass
            elif stripped and not stripped.startswith('#'):
                # Check if we're decreasing nesting
                if current_nesting > 0 and not stripped.startswith((' ', '\t')):
                    current_nesting -= 1

        if max_nesting > 4:
            violation = QualityViolation(
                violation_id=f"complexity_{len(self.violations) + 1}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                category=QualityCategory.COMPLEXITY,
                level=QualityLevel.POOR,
                file_path=file_path,
                line_number=1,
                description=f"High nesting depth detected ({max_nesting} levels)",
                suggested_fix="Refactor to reduce nesting depth",
                timestamp=datetime.now()
            )
            violations.append(violation)

        return violations

    def _check_security_violations(self, file_path: str, code_content: str) -> List[QualityViolation]:
        """Check for security violations"""
        violations = []

        # Check for hardcoded secrets
        if any(keyword in code_content.lower() for keyword in ['password', 'secret', 'key', 'token']):
            violation = QualityViolation(
                violation_id=f"security_{len(self.violations) + 1}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                category=QualityCategory.SECURITY,
                level=QualityLevel.CRITICAL,
                file_path=file_path,
                line_number=1,
                description="Potential hardcoded secret detected",
                suggested_fix="Use environment variables or secure configuration",
                timestamp=datetime.now()
            )
            violations.append(violation)

        return violations

    def _check_performance_violations(self, file_path: str, code_content: str) -> List[QualityViolation]:
        """Check for performance violations"""
        violations = []

        # Check for inefficient patterns
        if 'for i in range(len(' in code_content:
            violation = QualityViolation(
                violation_id=f"performance_{len(self.violations) + 1}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                category=QualityCategory.PERFORMANCE,
                level=QualityLevel.FAIR,
                file_path=file_path,
                line_number=1,
                description="Inefficient loop pattern detected",
                suggested_fix="Use enumerate() or direct iteration",
                timestamp=datetime.now()
            )
            violations.append(violation)

        return violations

    def _check_maintainability_violations(self, file_path: str, code_content: str) -> List[QualityViolation]:
        """Check for maintainability violations"""
        violations = []

        # Check for magic numbers
        import re
        magic_numbers = re.findall(r'\b\d{3,}\b', code_content)
        if magic_numbers:
            violation = QualityViolation(
                violation_id=f"maintainability_{len(self.violations) + 1}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                category=QualityCategory.MAINTAINABILITY,
                level=QualityLevel.FAIR,
                file_path=file_path,
                line_number=1,
                description=f"Magic numbers detected: {magic_numbers}",
                suggested_fix="Define constants for magic numbers",
                timestamp=datetime.now()
            )
            violations.append(violation)

        return violations

    def _check_testability_violations(self, file_path: str, code_content: str) -> List[QualityViolation]:
        """Check for testability violations"""
        violations = []

        # Check for missing docstrings in functions
        lines = code_content.split('\n')
        in_function = False
        function_line = 0

        for i, line in enumerate(lines, 1):
            stripped = line.strip()
            if stripped.startswith('def '):
                in_function = True
                function_line = i
            elif stripped and not stripped.startswith('#'):
                if in_function:
                    if not stripped.startswith('"""') and not stripped.startswith("'''"):
                        violation = QualityViolation(
                            violation_id=f"testability_{len(self.violations) + 1}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                            category=QualityCategory.TESTABILITY,
                            level=QualityLevel.GOOD,
                            file_path=file_path,
                            line_number=function_line,
                            description="Function missing docstring",
                            suggested_fix="Add docstring to function",
                            timestamp=datetime.now()
                        )
                        violations.append(violation)
                    in_function = False

        return violations

    def get_violations_by_category(self, category: QualityCategory) -> List[QualityViolation]:
        """Get violations by category"""
        return [v for v in self.violations if v.category == category]

    def get_violations_by_level(self, level: QualityLevel) -> List[QualityViolation]:
        """Get violations by level"""
        return [v for v in self.violations if v.level == level]

    def get_quality_summary(self) -> Dict[str, Any]:
        """Get quality summary"""
        try:
            total_violations = len(self.violations)

            violations_by_category = {}
            violations_by_level = {}

            for violation in self.violations:
                # By category
                category_key = violation.category.value
                violations_by_category[category_key] = violations_by_category.get(category_key, 0) + 1

                # By level
                level_key = violation.level.value
                violations_by_level[level_key] = violations_by_level.get(level_key, 0) + 1

            return {
                "total_violations": total_violations,
                "violations_by_category": violations_by_category,
                "violations_by_level": violations_by_level,
                "timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            self.logger.error(f"❌ Failed to get quality summary: {e}")
            return {"error": str(e)}

    def clear_violations(self):
        """Clear all violations"""
        self.violations.clear()
        self.logger.info("🧹 All quality violations cleared")