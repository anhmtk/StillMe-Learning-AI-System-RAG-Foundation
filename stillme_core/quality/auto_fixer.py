"""Auto Fixer for StillMe Framework"""

import logging
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

class FixType(Enum):
    STYLE = "style"
    COMPLEXITY = "complexity"
    SECURITY = "security"
    PERFORMANCE = "performance"
    MAINTAINABILITY = "maintainability"
    TESTABILITY = "testability"

class FixStatus(Enum):
    PENDING = "pending"
    APPLIED = "applied"
    FAILED = "failed"
    SKIPPED = "skipped"

@dataclass
class AutoFix:
    """Auto fix record"""
    fix_id: str
    fix_type: FixType
    status: FixStatus
    file_path: str
    line_number: int
    original_code: str
    fixed_code: str
    description: str
    confidence: float
    timestamp: datetime
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

class AutoFixer:
    """Auto fixer for StillMe Framework"""

    def __init__(self):
        self.logger = logger
        self.fixes: List[AutoFix] = []
        self.fix_rules = self._initialize_fix_rules()
        self.logger.info("✅ AutoFixer initialized")

    def _initialize_fix_rules(self) -> Dict[FixType, List[str]]:
        """Initialize auto fix rules"""
        return {
            FixType.STYLE: [
                "remove_trailing_whitespace",
                "fix_line_length",
                "add_missing_docstring",
                "remove_unused_imports"
            ],
            FixType.COMPLEXITY: [
                "reduce_nesting",
                "extract_method",
                "simplify_condition"
            ],
            FixType.SECURITY: [
                "sanitize_input",
                "use_secure_functions",
                "add_validation"
            ],
            FixType.PERFORMANCE: [
                "optimize_loops",
                "cache_results",
                "reduce_complexity"
            ],
            FixType.MAINTAINABILITY: [
                "extract_constants",
                "improve_naming",
                "reduce_duplication"
            ],
            FixType.TESTABILITY: [
                "add_docstrings",
                "reduce_dependencies",
                "improve_modularity"
            ]
        }

    def suggest_fixes(self,
                     file_path: str,
                     code_content: str,
                     quality_violations: List[Any] = None) -> List[AutoFix]:
        """Suggest auto fixes for code"""
        try:
            fixes = []

            # Style fixes
            style_fixes = self._suggest_style_fixes(file_path, code_content)
            fixes.extend(style_fixes)

            # Complexity fixes
            complexity_fixes = self._suggest_complexity_fixes(file_path, code_content)
            fixes.extend(complexity_fixes)

            # Security fixes
            security_fixes = self._suggest_security_fixes(file_path, code_content)
            fixes.extend(security_fixes)

            # Performance fixes
            performance_fixes = self._suggest_performance_fixes(file_path, code_content)
            fixes.extend(performance_fixes)

            # Maintainability fixes
            maintainability_fixes = self._suggest_maintainability_fixes(file_path, code_content)
            fixes.extend(maintainability_fixes)

            # Testability fixes
            testability_fixes = self._suggest_testability_fixes(file_path, code_content)
            fixes.extend(testability_fixes)

            # Record fixes
            for fix in fixes:
                self.fixes.append(fix)
                self.logger.info(f"🔧 Auto fix suggested: {fix.fix_type.value} - {fix.description}")

            return fixes

        except Exception as e:
            self.logger.error(f"❌ Failed to suggest fixes: {e}")
            return []

    def _suggest_style_fixes(self, file_path: str, code_content: str) -> List[AutoFix]:
        """Suggest style fixes"""
        fixes = []
        lines = code_content.split('\n')

        for i, line in enumerate(lines, 1):
            # Fix trailing whitespace
            if line.rstrip() != line:
                fix = AutoFix(
                    fix_id=f"style_{len(self.fixes) + 1}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                    fix_type=FixType.STYLE,
                    status=FixStatus.PENDING,
                    file_path=file_path,
                    line_number=i,
                    original_code=line,
                    fixed_code=line.rstrip(),
                    description="Remove trailing whitespace",
                    confidence=1.0,
                    timestamp=datetime.now()
                )
                fixes.append(fix)

            # Fix line length
            if len(line) > 120:
                # Simple fix: break at spaces
                if ' ' in line:
                    words = line.split(' ')
                    fixed_line = ""
                    current_line = ""

                    for word in words:
                        if len(current_line + word) > 120:
                            if fixed_line:
                                fixed_line += "\n" + current_line.rstrip()
                            else:
                                fixed_line = current_line.rstrip()
                            current_line = word + " "
                        else:
                            current_line += word + " "

                    if current_line:
                        if fixed_line:
                            fixed_line += "\n" + current_line.rstrip()
                        else:
                            fixed_line = current_line.rstrip()

                    fix = AutoFix(
                        fix_id=f"style_{len(self.fixes) + 1}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                        fix_type=FixType.STYLE,
                        status=FixStatus.PENDING,
                        file_path=file_path,
                        line_number=i,
                        original_code=line,
                        fixed_code=fixed_line,
                        description="Break long line into multiple lines",
                        confidence=0.8,
                        timestamp=datetime.now()
                    )
                    fixes.append(fix)

        return fixes

    def _suggest_complexity_fixes(self, file_path: str, code_content: str) -> List[AutoFix]:
        """Suggest complexity fixes"""
        fixes = []

        # Check for high nesting
        lines = code_content.split('\n')
        max_nesting = 0
        current_nesting = 0

        for i, line in enumerate(lines, 1):
            stripped = line.strip()
            if stripped.startswith(('if ', 'for ', 'while ', 'try:', 'with ')):
                current_nesting += 1
                max_nesting = max(max_nesting, current_nesting)
            elif stripped and not stripped.startswith('#'):
                if current_nesting > 0 and not stripped.startswith((' ', '\t')):
                    current_nesting -= 1

        if max_nesting > 4:
            fix = AutoFix(
                fix_id=f"complexity_{len(self.fixes) + 1}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                fix_type=FixType.COMPLEXITY,
                status=FixStatus.PENDING,
                file_path=file_path,
                line_number=1,
                original_code="High nesting detected",
                fixed_code="Extract methods to reduce nesting",
                description="Refactor to reduce nesting depth",
                confidence=0.6,
                timestamp=datetime.now()
            )
            fixes.append(fix)

        return fixes

    def _suggest_security_fixes(self, file_path: str, code_content: str) -> List[AutoFix]:
        """Suggest security fixes"""
        fixes = []

        # Check for hardcoded secrets
        if any(keyword in code_content.lower() for keyword in ['password', 'secret', 'key', 'token']):
            fix = AutoFix(
                fix_id=f"security_{len(self.fixes) + 1}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                fix_type=FixType.SECURITY,
                status=FixStatus.PENDING,
                file_path=file_path,
                line_number=1,
                original_code="Hardcoded secret detected",
                fixed_code="Use environment variable or secure config",
                description="Replace hardcoded secrets with secure alternatives",
                confidence=0.9,
                timestamp=datetime.now()
            )
            fixes.append(fix)

        return fixes

    def _suggest_performance_fixes(self, file_path: str, code_content: str) -> List[AutoFix]:
        """Suggest performance fixes"""
        fixes = []

        # Check for inefficient patterns
        if 'for i in range(len(' in code_content:
            fix = AutoFix(
                fix_id=f"performance_{len(self.fixes) + 1}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                fix_type=FixType.PERFORMANCE,
                status=FixStatus.PENDING,
                file_path=file_path,
                line_number=1,
                original_code="for i in range(len(collection)):",
                fixed_code="for item in collection:",
                description="Use direct iteration instead of range(len())",
                confidence=0.8,
                timestamp=datetime.now()
            )
            fixes.append(fix)

        return fixes

    def _suggest_maintainability_fixes(self, file_path: str, code_content: str) -> List[AutoFix]:
        """Suggest maintainability fixes"""
        fixes = []

        # Check for magic numbers
        import re
        magic_numbers = re.findall(r'\b\d{3,}\b', code_content)
        if magic_numbers:
            fix = AutoFix(
                fix_id=f"maintainability_{len(self.fixes) + 1}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                fix_type=FixType.MAINTAINABILITY,
                status=FixStatus.PENDING,
                file_path=file_path,
                line_number=1,
                original_code=f"Magic numbers: {magic_numbers}",
                fixed_code="Define constants for magic numbers",
                description="Replace magic numbers with named constants",
                confidence=0.7,
                timestamp=datetime.now()
            )
            fixes.append(fix)

        return fixes

    def _suggest_testability_fixes(self, file_path: str, code_content: str) -> List[AutoFix]:
        """Suggest testability fixes"""
        fixes = []

        # Check for missing docstrings
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
                        fix = AutoFix(
                            fix_id=f"testability_{len(self.fixes) + 1}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                            fix_type=FixType.TESTABILITY,
                            status=FixStatus.PENDING,
                            file_path=file_path,
                            line_number=function_line,
                            original_code="Function without docstring",
                            fixed_code='"""Add function docstring here"""',
                            description="Add docstring to function",
                            confidence=0.9,
                            timestamp=datetime.now()
                        )
                        fixes.append(fix)
                    in_function = False

        return fixes

    def apply_fix(self, fix_id: str) -> bool:
        """Apply a specific fix"""
        try:
            for fix in self.fixes:
                if fix.fix_id == fix_id:
                    # In a real implementation, this would modify the actual file
                    fix.status = FixStatus.APPLIED
                    self.logger.info(f"✅ Fix applied: {fix_id}")
                    return True

            self.logger.warning(f"⚠️ Fix not found: {fix_id}")
            return False

        except Exception as e:
            self.logger.error(f"❌ Failed to apply fix: {e}")
            return False

    def get_fixes_by_type(self, fix_type: FixType) -> List[AutoFix]:
        """Get fixes by type"""
        return [f for f in self.fixes if f.fix_type == fix_type]

    def get_fixes_by_status(self, status: FixStatus) -> List[AutoFix]:
        """Get fixes by status"""
        return [f for f in self.fixes if f.status == status]

    def get_fix_summary(self) -> Dict[str, Any]:
        """Get auto fix summary"""
        try:
            total_fixes = len(self.fixes)

            fixes_by_type = {}
            fixes_by_status = {}

            for fix in self.fixes:
                # By type
                type_key = fix.fix_type.value
                fixes_by_type[type_key] = fixes_by_type.get(type_key, 0) + 1

                # By status
                status_key = fix.status.value
                fixes_by_status[status_key] = fixes_by_status.get(status_key, 0) + 1

            return {
                "total_fixes": total_fixes,
                "fixes_by_type": fixes_by_type,
                "fixes_by_status": fixes_by_status,
                "timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            self.logger.error(f"❌ Failed to get fix summary: {e}")
            return {"error": str(e)}

    def clear_fixes(self):
        """Clear all fixes"""
        self.fixes.clear()
        self.logger.info("🧹 All auto fixes cleared")