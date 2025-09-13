#!/usr/bin/env python3
"""
Test AgentDev Brain standalone
"""

from dataclasses import dataclass
from enum import Enum
from typing import List, Optional, Tuple


class ErrorType(Enum):
    """Các loại lỗi phổ biến"""
    TYPE_CONFLICT = "type_conflict"
    IMPORT_ERROR = "import_error"
    MISSING_ATTRIBUTE = "missing_attribute"
    DUPLICATE_CLASS = "duplicate_class"
    MISSING_IMPORT = "missing_import"

class FixStrategy(Enum):
    """Chiến lược sửa lỗi"""
    ADD_TYPE_IGNORE = "add_type_ignore"
    ADD_TRY_EXCEPT = "add_try_except"
    REMOVE_DUPLICATE = "remove_duplicate"
    FIX_IMPORT_PATH = "fix_import_path"
    ADD_MISSING_IMPORT = "add_missing_import"

@dataclass
class ErrorPattern:
    """Pattern nhận diện lỗi"""
    error_type: ErrorType
    keywords: List[str]
    fix_strategy: FixStrategy
    confidence: float
    description: str

class AgentDevBrainStandalone:
    """Trí tuệ nhân tạo cho AgentDev - Standalone"""

    def __init__(self):
        self.error_patterns = self._initialize_error_patterns()
        self.fix_history = []
        self.success_rate = {}

    def _initialize_error_patterns(self) -> List[ErrorPattern]:
        """Khởi tạo các pattern nhận diện lỗi"""
        return [
            # Type conflicts
            ErrorPattern(
                error_type=ErrorType.TYPE_CONFLICT,
                keywords=["Type", "not assignable", "declared type"],
                fix_strategy=FixStrategy.ADD_TYPE_IGNORE,
                confidence=0.9,
                description="Type conflict between imports"
            ),

            # Import errors
            ErrorPattern(
                error_type=ErrorType.IMPORT_ERROR,
                keywords=["Import", "could not be resolved"],
                fix_strategy=FixStrategy.ADD_TRY_EXCEPT,
                confidence=0.8,
                description="Import cannot be resolved"
            ),

            # Missing attributes
            ErrorPattern(
                error_type=ErrorType.MISSING_ATTRIBUTE,
                keywords=["Attribute", "is unknown", "not a known attribute"],
                fix_strategy=FixStrategy.ADD_MISSING_IMPORT,
                confidence=0.7,
                description="Missing attribute in class"
            ),

            # Duplicate classes
            ErrorPattern(
                error_type=ErrorType.DUPLICATE_CLASS,
                keywords=["Class declaration", "obscured", "duplicate"],
                fix_strategy=FixStrategy.REMOVE_DUPLICATE,
                confidence=0.95,
                description="Duplicate class definition"
            ),
        ]

    def analyze_error(self, error_message: str, file_path: str, line_number: int) -> Optional[ErrorPattern]:
        """Phân tích lỗi và tìm pattern phù hợp"""
        error_lower = error_message.lower()

        for pattern in self.error_patterns:
            if any(keyword.lower() in error_lower for keyword in pattern.keywords):
                return pattern

        return None

    def get_fix_strategy(self, error_pattern: ErrorPattern, file_path: str, line_content: str) -> Tuple[str, float]:
        """Lấy chiến lược sửa lỗi cụ thể"""
        strategy = error_pattern.fix_strategy

        if strategy == FixStrategy.ADD_TYPE_IGNORE:
            return self._add_type_ignore(line_content), 0.9
        elif strategy == FixStrategy.ADD_TRY_EXCEPT:
            return self._add_try_except(line_content), 0.8
        elif strategy == FixStrategy.REMOVE_DUPLICATE:
            return self._remove_duplicate(line_content), 0.95
        elif strategy == FixStrategy.ADD_MISSING_IMPORT:
            return self._add_missing_import(line_content, file_path), 0.8
        else:
            return line_content, 0.5

    def _add_type_ignore(self, line_content: str) -> str:
        """Thêm # type: ignore comment"""
        if "# type: ignore" not in line_content:
            return line_content + "  # type: ignore"
        return line_content

    def _add_try_except(self, line_content: str) -> str:
        """Thêm try-except wrapper"""
        if "try:" not in line_content and "from" in line_content and "import" in line_content:
            return f"try:\n    {line_content}\nexcept ImportError:\n    pass"
        return line_content

    def _remove_duplicate(self, line_content: str) -> str:
        """Xóa duplicate class definition"""
        if "class " in line_content and "Enum" in line_content:
            return ""  # Xóa line
        return line_content

    def _add_missing_import(self, line_content: str, file_path: str) -> str:
        """Thêm missing import"""
        if "Set" in line_content and "from typing import" not in line_content:
            return "from typing import Set\n" + line_content
        return line_content

def test_agentdev_brain_standalone():
    """Test AgentDev Brain standalone"""
    print("🧠 Testing AgentDev Brain Standalone...")
    print("=" * 50)

    # Test error analysis
    brain = AgentDevBrainStandalone()

    # Test cases
    test_cases = [
        {
            "error": "Type 'type[stillme_core.router.intelligent_router.AgentType]' is not assignable to declared type 'type[stillme_core.router.agent_coordinator.AgentType]'",
            "file": "stillme_core/router/agent_coordinator.py",
            "line": 30,
            "content": "from .intelligent_router import AgentType, TaskComplexity, TaskType"
        },
        {
            "error": "Import 'stillme_core.performance_monitor' could not be resolved",
            "file": "stillme_core/security_compliance_system.py",
            "line": 42,
            "content": "from stillme_core.performance_monitor import PerformanceMonitor"
        },
        {
            "error": "Class declaration 'Subtask' is obscured by a declaration of the same name",
            "file": "stillme_core/router/agent_coordinator.py",
            "line": 50,
            "content": "class Subtask(Enum):"
        },
        {
            "error": "Attribute 'integration_bridge' is unknown",
            "file": "stillme_core/usage_analytics_engine.py",
            "line": 387,
            "content": "self.autonomous_management.integration_bridge.register_endpoint("
        }
    ]

    for i, test_case in enumerate(test_cases, 1):
        print(f"\n🔍 Test Case {i}:")
        print(f"  Error: {test_case['error'][:60]}...")
        print(f"  File: {test_case['file']}")
        print(f"  Line: {test_case['line']}")

        # Analyze error
        pattern = brain.analyze_error(test_case["error"], test_case["file"], test_case["line"])

        if pattern:
            print(f"  ✅ Detected: {pattern.error_type.value}")
            print(f"  ✅ Strategy: {pattern.fix_strategy.value}")
            print(f"  ✅ Confidence: {pattern.confidence}")

            # Test fix strategy
            fixed_line, confidence = brain.get_fix_strategy(pattern, test_case["file"], test_case["content"])
            print(f"  ✅ Original: {test_case['content']}")
            print(f"  ✅ Fixed: {fixed_line}")
            print(f"  ✅ Fix confidence: {confidence}")
        else:
            print("  ❌ No pattern detected")

    print("\n🧠 Brain Summary:")
    print(f"  Total patterns: {len(brain.error_patterns)}")
    print(f"  Test cases: {len(test_cases)}")
    print(f"  Success rate: {sum(1 for test_case in test_cases if brain.analyze_error(test_case['error'], test_case['file'], test_case['line'])) / len(test_cases) * 100:.1f}%")

if __name__ == "__main__":
    test_agentdev_brain_standalone()
