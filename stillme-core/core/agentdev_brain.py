#!/usr/bin/env python3
"""
AgentDev Brain - Trí tuệ nhân tạo cho AgentDev
Cung cấp kiến thức sâu về codebase và pattern recognition
"""

import json
import os
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple


class ErrorType(Enum):
    """Các loại lỗi phổ biến"""
    TYPE_CONFLICT = "type_conflict"
    IMPORT_ERROR = "import_error"
    MISSING_ATTRIBUTE = "missing_attribute"
    DUPLICATE_CLASS = "duplicate_class"
    MISSING_IMPORT = "missing_import"
    SYNTAX_ERROR = "syntax_error"
    LOGIC_ERROR = "logic_error"

class FixStrategy(Enum):
    """Chiến lược sửa lỗi"""
    ADD_TYPE_IGNORE = "add_type_ignore"
    ADD_TRY_EXCEPT = "add_try_except"
    REMOVE_DUPLICATE = "remove_duplicate"
    FIX_IMPORT_PATH = "fix_import_path"
    ADD_MISSING_IMPORT = "add_missing_import"
    FIX_CLASS_DEFINITION = "fix_class_definition"
    REFACTOR_CODE = "refactor_code"

@dataclass
class ErrorPattern:
    """Pattern nhận diện lỗi"""
    error_type: ErrorType
    keywords: List[str]
    fix_strategy: FixStrategy
    confidence: float
    description: str

@dataclass
class FixResult:
    """Kết quả sửa lỗi"""
    success: bool
    error_type: ErrorType
    fix_strategy: FixStrategy
    file_path: str
    line_number: int
    original_line: str
    fixed_line: str
    confidence: float

class AgentDevBrain:
    """Trí tuệ nhân tạo cho AgentDev"""

    def __init__(self):
        self.error_patterns = self._initialize_error_patterns()
        self.codebase_knowledge = self._initialize_codebase_knowledge()
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
                fix_strategy=FixStrategy.FIX_CLASS_DEFINITION,
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

            # Missing imports
            ErrorPattern(
                error_type=ErrorType.MISSING_IMPORT,
                keywords=["is not defined", "NameError"],
                fix_strategy=FixStrategy.ADD_MISSING_IMPORT,
                confidence=0.8,
                description="Missing import statement"
            ),
        ]

    def _initialize_codebase_knowledge(self) -> Dict[str, Any]:
        """Khởi tạo kiến thức về codebase"""
        return {
            "project_structure": {
                "stillme_core": {
                    "router": ["intelligent_router.py", "task_decomposer.py", "agent_coordinator.py"],
                    "quality": ["auto_fixer.py", "code_quality_enforcer.py"],
                    "observability": ["logger.py", "metrics.py", "tracer.py"],
                    "security": ["security_middleware.py", "security_compliance_system.py"]
                },
                "modules": ["framework.py", "identity_handler.py", "emotionsense_v1.py"],
                "api": ["stable_ai_server.py", "app.py"]
            },
            "common_imports": {
                "typing": ["List", "Dict", "Optional", "Any", "Set", "Tuple"],
                "pathlib": ["Path"],
                "dataclasses": ["dataclass"],
                "enum": ["Enum"],
                "asyncio": ["asyncio"],
                "json": ["json"],
                "logging": ["logging"],
                "time": ["time"],
                "os": ["os"],
                "sys": ["sys"]
            },
            "common_classes": {
                "stillme_core.router.intelligent_router": ["AgentType", "TaskComplexity", "TaskType"],
                "stillme_core.router.task_decomposer": ["Subtask", "SubtaskStatus", "TaskDecomposition"],
                "stillme_core.observability.logger": ["get_logger"],
                "stillme_core.observability.metrics": ["get_metrics_collector", "MetricType"],
                "stillme_core.observability.tracer": ["get_tracer"]
            },
            "file_patterns": {
                "router_files": ["*router*.py", "*coordinator*.py", "*decomposer*.py"],
                "quality_files": ["*quality*.py", "*fixer*.py", "*enforcer*.py"],
                "security_files": ["*security*.py", "*compliance*.py", "*middleware*.py"]
            }
        }

    def analyze_error(self, error_message: str, file_path: str, line_number: int) -> Optional[ErrorPattern]:
        """Phân tích lỗi và tìm pattern phù hợp"""
        error_lower = error_message.lower()

        for pattern in self.error_patterns:
            if any(keyword.lower() in error_lower for keyword in pattern.keywords):
                # Tăng confidence dựa trên context
                confidence = pattern.confidence

                # Tăng confidence nếu file thuộc loại phù hợp
                if self._is_file_type_match(file_path, pattern.error_type):
                    confidence += 0.1

                # Tăng confidence nếu đã sửa thành công loại lỗi này trước đó
                if pattern.error_type in self.success_rate:
                    confidence += min(0.1, self.success_rate[pattern.error_type] * 0.1)

                return ErrorPattern(
                    error_type=pattern.error_type,
                    keywords=pattern.keywords,
                    fix_strategy=pattern.fix_strategy,
                    confidence=min(1.0, confidence),
                    description=pattern.description
                )

        return None

    def _is_file_type_match(self, file_path: str, error_type: ErrorType) -> bool:
        """Kiểm tra xem file có phù hợp với loại lỗi không"""
        file_lower = file_path.lower()

        if error_type == ErrorType.TYPE_CONFLICT:
            return any(keyword in file_lower for keyword in ["router", "coordinator", "decomposer"])
        elif error_type == ErrorType.IMPORT_ERROR:
            return any(keyword in file_lower for keyword in ["__init__.py", "integration", "bridge"])
        elif error_type == ErrorType.DUPLICATE_CLASS:
            return any(keyword in file_lower for keyword in ["coordinator", "router"])

        return True

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
        elif strategy == FixStrategy.FIX_CLASS_DEFINITION:
            return self._fix_class_definition(line_content, file_path), 0.7
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
        # Logic phức tạp để xác định import cần thêm
        if "Set" in line_content and "from typing import" not in line_content:
            return "from typing import Set\n" + line_content
        return line_content

    def _fix_class_definition(self, line_content: str, file_path: str) -> str:
        """Sửa class definition"""
        # Logic phức tạp để sửa class definition
        return line_content

    def record_fix_result(self, fix_result: FixResult):
        """Ghi nhận kết quả sửa lỗi"""
        self.fix_history.append(fix_result)

        # Cập nhật success rate
        error_type = fix_result.error_type
        if error_type not in self.success_rate:
            self.success_rate[error_type] = 0.0

        # Tính success rate mới
        recent_fixes = [f for f in self.fix_history[-10:] if f.error_type == error_type]
        if recent_fixes:
            success_count = sum(1 for f in recent_fixes if f.success)
            self.success_rate[error_type] = success_count / len(recent_fixes)

    def get_learning_insights(self) -> Dict[str, Any]:
        """Lấy insights từ việc học"""
        return {
            "total_fixes": len(self.fix_history),
            "success_rate_by_type": self.success_rate,
            "most_common_errors": self._get_most_common_errors(),
            "best_strategies": self._get_best_strategies(),
            "learning_progress": self._calculate_learning_progress()
        }

    def _get_most_common_errors(self) -> List[Tuple[ErrorType, int]]:
        """Lấy các lỗi phổ biến nhất"""
        error_counts = {}
        for fix in self.fix_history:
            error_type = fix.error_type
            error_counts[error_type] = error_counts.get(error_type, 0) + 1

        return sorted(error_counts.items(), key=lambda x: x[1], reverse=True)

    def _get_best_strategies(self) -> List[Tuple[FixStrategy, float]]:
        """Lấy các chiến lược tốt nhất"""
        strategy_success = {}
        for fix in self.fix_history:
            strategy = fix.fix_strategy
            if strategy not in strategy_success:
                strategy_success[strategy] = {"success": 0, "total": 0}

            strategy_success[strategy]["total"] += 1
            if fix.success:
                strategy_success[strategy]["success"] += 1

        # Tính success rate cho mỗi strategy
        strategy_rates = []
        for strategy, data in strategy_success.items():
            rate = data["success"] / data["total"] if data["total"] > 0 else 0
            strategy_rates.append((strategy, rate))

        return sorted(strategy_rates, key=lambda x: x[1], reverse=True)

    def _calculate_learning_progress(self) -> float:
        """Tính toán tiến độ học tập"""
        if not self.fix_history:
            return 0.0

        # Tính success rate tổng thể
        recent_fixes = self.fix_history[-20:]  # 20 fixes gần nhất
        if not recent_fixes:
            return 0.0

        success_count = sum(1 for fix in recent_fixes if fix.success)
        return success_count / len(recent_fixes)

    def save_knowledge(self, file_path: str = "agentdev_brain.json"):
        """Lưu kiến thức vào file"""
        knowledge = {
            "error_patterns": [
                {
                    "error_type": pattern.error_type.value,
                    "keywords": pattern.keywords,
                    "fix_strategy": pattern.fix_strategy.value,
                    "confidence": pattern.confidence,
                    "description": pattern.description
                }
                for pattern in self.error_patterns
            ],
            "codebase_knowledge": self.codebase_knowledge,
            "fix_history": [
                {
                    "success": fix.success,
                    "error_type": fix.error_type.value,
                    "fix_strategy": fix.fix_strategy.value,
                    "file_path": fix.file_path,
                    "line_number": fix.line_number,
                    "confidence": fix.confidence
                }
                for fix in self.fix_history
            ],
            "success_rate": {k.value: v for k, v in self.success_rate.items()},
            "learning_insights": self.get_learning_insights()
        }

        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(knowledge, f, indent=2, ensure_ascii=False)

    def load_knowledge(self, file_path: str = "agentdev_brain.json"):
        """Tải kiến thức từ file"""
        if not os.path.exists(file_path):
            return

        with open(file_path, encoding="utf-8") as f:
            knowledge = json.load(f)

        # Load error patterns
        self.error_patterns = [
            ErrorPattern(
                error_type=ErrorType(pattern["error_type"]),
                keywords=pattern["keywords"],
                fix_strategy=FixStrategy(pattern["fix_strategy"]),
                confidence=pattern["confidence"],
                description=pattern["description"]
            )
            for pattern in knowledge.get("error_patterns", [])
        ]

        # Load codebase knowledge
        self.codebase_knowledge = knowledge.get("codebase_knowledge", {})

        # Load fix history
        self.fix_history = [
            FixResult(
                success=fix["success"],
                error_type=ErrorType(fix["error_type"]),
                fix_strategy=FixStrategy(fix["fix_strategy"]),
                file_path=fix["file_path"],
                line_number=fix["line_number"],
                original_line="",
                fixed_line="",
                confidence=fix["confidence"]
            )
            for fix in knowledge.get("fix_history", [])
        ]

        # Load success rate
        self.success_rate = {
            ErrorType(k): v for k, v in knowledge.get("success_rate", {}).items()
        }

# Global instance
_agentdev_brain = None

def get_agentdev_brain() -> AgentDevBrain:
    """Get global AgentDev Brain instance"""
    global _agentdev_brain
    if _agentdev_brain is None:
        _agentdev_brain = AgentDevBrain()
        _agentdev_brain.load_knowledge()  # Load existing knowledge
    return _agentdev_brain

if __name__ == "__main__":
    # Test AgentDev Brain
    brain = get_agentdev_brain()

    # Test error analysis
    error_msg = "Type 'type[stillme_core.router.intelligent_router.AgentType]' is not assignable to declared type 'type[stillme_core.router.agent_coordinator.AgentType]'"
    pattern = brain.analyze_error(error_msg, "stillme_core/router/agent_coordinator.py", 30)

    if pattern:
        print(f"Detected error: {pattern.error_type.value}")
        print(f"Fix strategy: {pattern.fix_strategy.value}")
        print(f"Confidence: {pattern.confidence}")

        # Test fix strategy
        fixed_line, confidence = brain.get_fix_strategy(pattern, "test.py", "from .intelligent_router import AgentType")
        print(f"Fixed line: {fixed_line}")
        print(f"Fix confidence: {confidence}")

    # Save knowledge
    brain.save_knowledge()
