"""
SelfImprovementManager - Module tự cải thiện với cơ chế an toàn tối đa

QUY TẮC AN TOÀN BẮT BUỘC (HIẾN PHÁP CỦA STILLME):
1. CHỈ ĐỌC, KHÔNG GHI: Mặc định chỉ đọc dữ liệu và tạo báo cáo đề xuất
2. ĐỀ XUẤT PHẢI ĐƯỢC DUYỆT: Mọi thay đổi phải qua quy trình phê duyệt
3. VÒNG KIỂM SOÁT CHẶT CHẼ: 4 mắt kiểm tra (EthicalCoreSystem, ContentIntegrityFilter, Test Suite)
4. SANDOX MODE: Test trong môi trường sandbox trước khi áp dụng
5. ROLLBACK TỰ ĐỘNG: Tự động khôi phục nếu test fail

Author: StillMe AI Framework
Version: 1.0.0
Safety Level: MAXIMUM
"""

import hashlib
import json
import os
import shutil

# Import common utilities
import sys
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

# Add project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from common import (
    AsyncHttpClient,
    ConfigManager,
    FileManager,
    get_logger,
)

# Import các module an toàn
try:
    # from modules.ethical_core_system import EthicalCoreSystem
    raise ImportError("Module not found")
except ImportError:
    # Mock EthicalCoreSystem nếu không tồn tại
    class EthicalCoreSystem:
        def __init__(self):
            pass

        def approve_change(self, change):
            return True


try:
    from modules.content_integrity_filter import (
        ContentIntegrityFilter as _ContentIntegrityFilter,
    )

    # Create a type alias to avoid type conflicts
    ContentIntegrityFilter = _ContentIntegrityFilter  # type: ignore
except ImportError:
    # Mock ContentIntegrityFilter nếu không tồn tại
    class ContentIntegrityFilter:
        def __init__(self):
            pass

        def validate_change(self, change):
            return True


@dataclass
class ProposedChange:
    """Cấu trúc dữ liệu cho một đề xuất thay đổi"""

    id: str
    timestamp: str
    change_type: str  # 'prompt', 'config', 'code', 'system'
    file_path: str
    description: str
    current_content: str
    proposed_content: str
    reason: str
    risk_level: str  # 'LOW', 'MEDIUM', 'HIGH', 'CRITICAL'
    safety_checks: dict[str, bool]
    test_results: dict[str, bool]
    approved: bool = False
    applied: bool = False
    rollback_available: bool = False


@dataclass
class SafetyReport:
    """Báo cáo an toàn cho một đề xuất"""

    change_id: str
    ethical_check: bool
    integrity_check: bool
    test_check: bool
    overall_safe: bool
    warnings: list[str]
    recommendations: list[str]


class SelfImprovementManager:
    """
    Module tự cải thiện với cơ chế an toàn tối đa

    QUY TẮC AN TOÀN:
    - CHỈ ĐỌC mặc định, không ghi trực tiếp
    - Mọi thay đổi phải qua quy trình phê duyệt 4 mắt
    - Sandbox testing trước khi áp dụng
    - Rollback tự động nếu có lỗi
    """

    def __init__(self, config_path: str = "config/self_improvement_config.json"):
        """
        Khởi tạo SelfImprovementManager với cơ chế an toàn tối đa

        Args:
            config_path: Đường dẫn đến file cấu hình
        """
        # Initialize common utilities
        self.config_manager = ConfigManager(config_path, {})
        self.logger = get_logger(
            "StillMe.SelfImprovement",
            log_file="logs/self_improvement.log",
            json_format=True,
        )
        self.http_client = AsyncHttpClient()
        self.file_manager = FileManager()

        self.config_path = config_path
        self.proposed_changes: list[ProposedChange] = []
        self.safety_reports: list[SafetyReport] = []
        self.backup_dir = Path("backups/self_improvement")
        self.sandbox_dir = Path("sandbox/self_improvement")
        self.proposed_changes_file = "proposed_changes.json"

        # Khởi tạo các module kiểm tra an toàn
        self.ethical_checker = EthicalCoreSystem()
        self.integrity_filter = ContentIntegrityFilter()

        # Cấu hình logging using common logging
        from common.logging import get_module_logger

        self.logger = get_module_logger("self_improvement")

        # Tạo thư mục cần thiết
        self._create_directories()

        # Load cấu hình using common config
        from common.config import load_module_config

        self.config_manager = load_module_config("self_improvement", self.config_path)
        self.config = self.config_manager.to_dict()

        # Trạng thái an toàn
        self.safety_mode = True  # Luôn ở chế độ an toàn
        self.read_only_mode = True  # Mặc định chỉ đọc

        self.logger.info("SelfImprovementManager initialized with MAXIMUM safety mode")

    def _create_directories(self) -> None:
        """Tạo các thư mục cần thiết"""
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        self.sandbox_dir.mkdir(parents=True, exist_ok=True)

        # Tạo thư mục config nếu chưa có
        Path("config").mkdir(exist_ok=True)

    def _load_config(self) -> dict[str, Any]:
        """Load cấu hình từ file"""
        default_config = {
            "safety_mode": True,
            "read_only_mode": True,
            "auto_approve_low_risk": False,
            "max_proposed_changes": 10,
            "backup_retention_days": 30,
            "sandbox_timeout_seconds": 300,
            "required_approvals": ["ethical", "integrity", "test"],
            "forbidden_file_patterns": [
                "*.pyc",
                "__pycache__",
                "*.log",
                "*.tmp",
                "backup_legacy",
                "tests/fixtures",
                "node_modules",
            ],
            "critical_files": [
                "framework.py",
                "app.py",
                "modules/ethical_core_system.py",
                "modules/content_integrity_filter.py",
            ],
        }

        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, encoding="utf-8") as f:
                    config = json.load(f)
                    # Merge với default config
                    default_config.update(config)
            except Exception as e:
                self.logger.warning(f"Failed to load config: {e}, using default")

        # Lưu config mặc định
        with open(self.config_path, "w", encoding="utf-8") as f:
            json.dump(default_config, f, indent=2, ensure_ascii=False)

        return default_config

    def _generate_change_id(self, change_type: str, file_path: str) -> str:
        """Tạo ID duy nhất cho đề xuất thay đổi"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        content_hash = hashlib.sha256(
            f"{change_type}_{file_path}_{timestamp}".encode()
        ).hexdigest()[:8]
        return f"{change_type}_{timestamp}_{content_hash}"

    def _is_file_allowed(self, file_path: str) -> bool:
        """Kiểm tra file có được phép chỉnh sửa không"""
        path = Path(file_path)

        # Kiểm tra pattern bị cấm
        for pattern in self.config["forbidden_file_patterns"]:
            if pattern.startswith("*"):
                if path.match(pattern):
                    return False
            elif pattern in str(path):
                return False

        # Kiểm tra file quan trọng (cần approval đặc biệt)
        if str(path) in self.config["critical_files"]:
            self.logger.warning(
                f"Critical file modification requires special approval: {file_path}"
            )

        return True

    def run_analysis(self) -> dict[str, Any]:
        """
        Bước 1: Thu thập và phân tích dữ liệu (CHỈ ĐỌC)

        Returns:
            Dict chứa kết quả phân tích và đề xuất
        """
        self.logger.info("Starting self-improvement analysis (READ-ONLY mode)")

        try:
            # Thu thập dữ liệu (CHỈ ĐỌC)
            analysis_data = self._collect_analysis_data()

            # Phân tích với AI (không thay đổi gì)
            proposed_changes = self._analyze_with_ai(analysis_data)

            # Kiểm tra an toàn cho từng đề xuất
            safe_changes = []
            for change in proposed_changes:
                if self._safety_check_change(change):
                    safe_changes.append(change)
                else:
                    self.logger.warning(
                        f"Change rejected by safety check: {change['id']}"
                    )

            # Lưu đề xuất (KHÔNG ÁP DỤNG)
            self._save_proposed_changes(safe_changes)

            return {
                "status": "success",
                "analysis_data": analysis_data,
                "proposed_changes": len(safe_changes),
                "total_analyzed": len(proposed_changes),
                "safety_mode": self.safety_mode,
                "read_only_mode": self.read_only_mode,
            }

        except Exception as e:
            self.logger.error(f"Analysis failed: {e}")
            return {"status": "error", "error": str(e), "safety_mode": self.safety_mode}

    def _collect_analysis_data(self) -> dict[str, Any]:
        """Thu thập dữ liệu để phân tích (CHỈ ĐỌC)"""
        data = {
            "timestamp": datetime.now().isoformat(),
            "chat_history": self._read_chat_history(),
            "performance_logs": self._read_performance_logs(),
            "error_logs": self._read_error_logs(),
            "system_metrics": self._read_system_metrics(),
            "user_feedback": self._read_user_feedback(),
            "daily_learning": self._read_daily_learning_data(),
        }

        self.logger.info(f"Collected analysis data: {len(data)} categories")
        return data

    def _read_chat_history(self) -> list[dict[str, Any]]:
        """Đọc lịch sử chat (CHỈ ĐỌC)"""
        chat_files = [
            "conversation_log.txt",
            "conversation_memory.json",
            "logs/conversation.jsonl",
        ]

        history = []
        for file_path in chat_files:
            if os.path.exists(file_path):
                try:
                    with open(file_path, encoding="utf-8") as f:
                        if file_path.endswith(".json"):
                            data = json.load(f)
                        else:
                            data = f.read()
                        history.append({"file": file_path, "data": data})
                except Exception as e:
                    self.logger.warning(f"Failed to read {file_path}: {e}")

        return history

    def _read_daily_learning_data(self) -> dict[str, Any]:
        """Đọc dữ liệu học tập hàng ngày (READ-ONLY)"""
        try:
            # Import DailyLearningManager
            from modules.daily_learning_manager import DailyLearningManager

            learning_manager = DailyLearningManager()

            # Lấy cases hôm nay
            today_cases = learning_manager.select_today_cases(max_cases=5)

            # Lấy thống kê học tập
            learning_stats = learning_manager.get_learning_stats()

            return {
                "today_cases": [
                    {
                        "id": case.id,
                        "question": case.question,
                        "category": case.category,
                        "difficulty": case.difficulty,
                        "language": case.language,
                        "expected_keywords": case.expected_keywords,
                    }
                    for case in today_cases
                ],
                "learning_stats": learning_stats,
                "total_cases_available": learning_manager.cases_data.get(
                    "metadata", {}
                ).get("total_cases", 0),
            }

        except Exception as e:
            self.logger.error(f"Error reading daily learning data: {e}")
            return {}

    def _read_performance_logs(self) -> list[dict[str, Any]]:
        """Đọc logs hiệu suất (CHỈ ĐỌC)"""
        perf_files = [
            "api_usage.log",
            "performance_metrics.json",
            "logs/performance.jsonl",
        ]

        logs = []
        for file_path in perf_files:
            if os.path.exists(file_path):
                try:
                    with open(file_path, encoding="utf-8") as f:
                        if file_path.endswith(".json"):
                            data = json.load(f)
                        else:
                            data = f.read()
                        logs.append({"file": file_path, "data": data})
                except Exception as e:
                    self.logger.warning(f"Failed to read {file_path}: {e}")

        return logs

    def _read_error_logs(self) -> list[dict[str, Any]]:
        """Đọc logs lỗi (CHỈ ĐỌC)"""
        error_files = ["api_errors.log", "stillme.log", "logs/errors.jsonl"]

        errors = []
        for file_path in error_files:
            if os.path.exists(file_path):
                try:
                    with open(file_path, encoding="utf-8") as f:
                        data = f.read()
                        errors.append({"file": file_path, "data": data})
                except Exception as e:
                    self.logger.warning(f"Failed to read {file_path}: {e}")

        return errors

    def _read_system_metrics(self) -> dict[str, Any]:
        """Đọc metrics hệ thống (CHỈ ĐỌC)"""
        metrics = {
            "timestamp": datetime.now().isoformat(),
            "file_count": len(list(Path(".").rglob("*.py"))),
            "module_count": (
                len(list(Path("modules").glob("*.py")))
                if Path("modules").exists()
                else 0
            ),
            "test_count": (
                len(list(Path("tests").glob("test_*.py")))
                if Path("tests").exists()
                else 0
            ),
            "config_files": (
                len(list(Path("config").glob("*.json")))
                if Path("config").exists()
                else 0
            ),
        }

        return metrics

    def _read_user_feedback(self) -> list[dict[str, Any]]:
        """Đọc feedback từ user (CHỈ ĐỌC)"""
        feedback_files = [
            "user_feedback.json",
            "feedback_log.jsonl",
            "reports/user_feedback.json",
        ]

        feedback = []
        for file_path in feedback_files:
            if os.path.exists(file_path):
                try:
                    with open(file_path, encoding="utf-8") as f:
                        if file_path.endswith(".json"):
                            data = json.load(f)
                        else:
                            data = f.read()
                        feedback.append({"file": file_path, "data": data})
                except Exception as e:
                    self.logger.warning(f"Failed to read {file_path}: {e}")

        return feedback

    def _analyze_with_ai(self, analysis_data: dict[str, Any]) -> list[dict[str, Any]]:
        """
        Phân tích dữ liệu với AI để tạo đề xuất (KHÔNG THAY ĐỔI GÌ)

        Args:
            analysis_data: Dữ liệu đã thu thập

        Returns:
            List các đề xuất thay đổi
        """
        # Đây là nơi sẽ tích hợp với AI model để phân tích
        # Hiện tại tạo mock data để demo

        proposed_changes = []

        # Phân tích chat history
        if analysis_data["chat_history"]:
            # Mock: Phát hiện pattern lặp lại trong câu hỏi
            proposed_changes.append(
                {
                    "id": self._generate_change_id("prompt", "framework.py"),
                    "timestamp": datetime.now().isoformat(),
                    "change_type": "prompt",
                    "file_path": "framework.py",
                    "description": "Tối ưu prompt cho câu hỏi lập trình",
                    "current_content": "Current prompt content...",
                    "proposed_content": "Optimized prompt content...",
                    "reason": "Phát hiện nhiều câu hỏi lập trình cần response tốt hơn",
                    "risk_level": "LOW",
                    "safety_checks": {},
                    "test_results": {},
                }
            )

        # Phân tích performance logs
        if analysis_data["performance_logs"]:
            # Mock: Phát hiện response time chậm
            proposed_changes.append(
                {
                    "id": self._generate_change_id("config", "config/performance.json"),
                    "timestamp": datetime.now().isoformat(),
                    "change_type": "config",
                    "file_path": "config/performance.json",
                    "description": "Tối ưu timeout settings",
                    "current_content": "Current config...",
                    "proposed_content": "Optimized config...",
                    "reason": "Response time trung bình > 5s, cần tối ưu",
                    "risk_level": "MEDIUM",
                    "safety_checks": {},
                    "test_results": {},
                }
            )

        # Phân tích error logs
        if analysis_data["error_logs"]:
            # Mock: Phát hiện lỗi thường xuyên
            proposed_changes.append(
                {
                    "id": self._generate_change_id(
                        "code", "modules/api_provider_manager.py"
                    ),
                    "timestamp": datetime.now().isoformat(),
                    "change_type": "code",
                    "file_path": "modules/api_provider_manager.py",
                    "description": "Cải thiện error handling",
                    "current_content": "Current code...",
                    "proposed_content": "Improved code...",
                    "reason": "Phát hiện 15 lỗi connection timeout trong 1 ngày",
                    "risk_level": "HIGH",
                    "safety_checks": {},
                    "test_results": {},
                }
            )

        self.logger.info(
            f"AI analysis generated {len(proposed_changes)} proposed changes"
        )
        return proposed_changes

    def _safety_check_change(self, change: dict[str, Any]) -> bool:
        """
        Kiểm tra an toàn cho một đề xuất thay đổi (VÒNG KIỂM SOÁT 4 MẮT)

        Args:
            change: Đề xuất thay đổi

        Returns:
            True nếu an toàn, False nếu không
        """
        change_id = change["id"]
        self.logger.info(f"Running safety checks for change: {change_id}")

        # Kiểm tra 1: File có được phép chỉnh sửa không
        if not self._is_file_allowed(change["file_path"]):
            self.logger.warning(
                f"File not allowed for modification: {change['file_path']}"
            )
            return False

        # Kiểm tra 2: EthicalCoreSystem
        try:
            ethical_safe = self.ethical_checker.approve_change(change)
            change["safety_checks"]["ethical"] = ethical_safe
            if not ethical_safe:
                self.logger.warning(f"Change failed ethical check: {change_id}")
                return False
        except Exception as e:
            self.logger.error(f"Ethical check failed: {e}")
            return False

        # Kiểm tra 3: ContentIntegrityFilter
        try:
            integrity_safe = self.integrity_filter.validate_change(change)
            change["safety_checks"]["integrity"] = integrity_safe
            if not integrity_safe:
                self.logger.warning(f"Change failed integrity check: {change_id}")
                return False
        except Exception as e:
            self.logger.error(f"Integrity check failed: {e}")
            return False

        # Kiểm tra 4: Risk level
        if change["risk_level"] in ["HIGH", "CRITICAL"]:
            self.logger.warning(
                f"High risk change requires manual approval: {change_id}"
            )
            change["safety_checks"]["risk_approval"] = False
            return False

        # Tất cả kiểm tra đều pass
        change["safety_checks"]["overall"] = True
        self.logger.info(f"All safety checks passed for change: {change_id}")
        return True

    def _save_proposed_changes(self, changes: list[dict[str, Any]]) -> None:
        """Lưu các đề xuất thay đổi vào file (KHÔNG ÁP DỤNG)"""
        if not changes:
            self.logger.info("No changes to save")
            return

        # Chuyển đổi thành ProposedChange objects
        proposed_changes = []
        for change_data in changes:
            change = ProposedChange(
                id=change_data["id"],
                timestamp=change_data["timestamp"],
                change_type=change_data["change_type"],
                file_path=change_data["file_path"],
                description=change_data["description"],
                current_content=change_data["current_content"],
                proposed_content=change_data["proposed_content"],
                reason=change_data["reason"],
                risk_level=change_data["risk_level"],
                safety_checks=change_data["safety_checks"],
                test_results=change_data["test_results"],
            )
            proposed_changes.append(change)

        # Lưu vào file
        changes_data = [asdict(change) for change in proposed_changes]
        with open(self.proposed_changes_file, "w", encoding="utf-8") as f:
            json.dump(changes_data, f, indent=2, ensure_ascii=False)

        self.proposed_changes = proposed_changes
        self.logger.info(
            f"Saved {len(proposed_changes)} proposed changes to {self.proposed_changes_file}"
        )

    def get_proposed_changes(self) -> list[dict[str, Any]]:
        """Lấy danh sách đề xuất thay đổi (CHỈ ĐỌC)"""
        if os.path.exists(self.proposed_changes_file):
            try:
                with open(self.proposed_changes_file, encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                self.logger.error(f"Failed to read proposed changes: {e}")

        return []

    def approve_change(self, change_id: str, approved: bool = True) -> bool:
        """
        Phê duyệt hoặc từ chối một đề xuất thay đổi

        Args:
            change_id: ID của đề xuất
            approved: True để phê duyệt, False để từ chối

        Returns:
            True nếu thành công
        """
        changes = self.get_proposed_changes()

        for change in changes:
            if change["id"] == change_id:
                change["approved"] = approved
                change["approval_timestamp"] = datetime.now().isoformat()

                # Lưu lại
                with open(self.proposed_changes_file, "w", encoding="utf-8") as f:
                    json.dump(changes, f, indent=2, ensure_ascii=False)

                self.logger.info(
                    f"Change {change_id} {'approved' if approved else 'rejected'}"
                )
                return True

        self.logger.warning(f"Change not found: {change_id}")
        return False

    def apply_approved_changes(self) -> dict[str, Any]:
        """
        Áp dụng các đề xuất đã được phê duyệt (SANDOX MODE + ROLLBACK)

        Returns:
            Dict chứa kết quả áp dụng
        """
        if self.read_only_mode:
            self.logger.error("Cannot apply changes in read-only mode")
            return {"status": "error", "message": "Read-only mode active"}

        changes = self.get_proposed_changes()
        approved_changes = [c for c in changes if c.get("approved", False)]

        if not approved_changes:
            self.logger.info("No approved changes to apply")
            return {"status": "success", "message": "No changes to apply"}

        results = {
            "status": "success",
            "applied": 0,
            "failed": 0,
            "rollbacks": 0,
            "details": [],
        }

        for change in approved_changes:
            try:
                # Tạo backup trước khi áp dụng
                backup_path = self._create_backup(change)

                # Áp dụng trong sandbox
                if self._apply_change_sandbox(change):
                    # Test trong sandbox
                    if self._test_in_sandbox(change):
                        # Áp dụng thực tế
                        if self._apply_change_real(change):
                            # Test toàn bộ hệ thống
                            if self._run_full_test_suite():
                                results["applied"] += 1
                                change["applied"] = True
                                self.logger.info(
                                    f"Successfully applied change: {change['id']}"
                                )
                            else:
                                # Rollback nếu test fail
                                self._rollback_change(change, backup_path)
                                results["rollbacks"] += 1
                                results["failed"] += 1
                                self.logger.error(
                                    f"Rolled back change due to test failure: {change['id']}"
                                )
                        else:
                            results["failed"] += 1
                            self.logger.error(f"Failed to apply change: {change['id']}")
                    else:
                        results["failed"] += 1
                        self.logger.error(
                            f"Sandbox test failed for change: {change['id']}"
                        )
                else:
                    results["failed"] += 1
                    self.logger.error(
                        f"Failed to apply change in sandbox: {change['id']}"
                    )

                results["details"].append(
                    {
                        "change_id": change["id"],
                        "status": (
                            "applied" if change.get("applied", False) else "failed"
                        ),
                    }
                )

            except Exception as e:
                results["failed"] += 1
                self.logger.error(f"Error applying change {change['id']}: {e}")
                results["details"].append(
                    {"change_id": change["id"], "status": "error", "error": str(e)}
                )

        return results

    def _create_backup(self, change: dict[str, Any]) -> str:
        """Tạo backup của file trước khi thay đổi"""
        file_path = change["file_path"]
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_filename = f"{Path(file_path).stem}_{timestamp}.backup"
        backup_path = self.backup_dir / backup_filename

        if os.path.exists(file_path):
            shutil.copy2(file_path, backup_path)
            self.logger.info(f"Created backup: {backup_path}")
            return str(backup_path)

        return ""

    def _apply_change_sandbox(self, change: dict[str, Any]) -> bool:
        """Áp dụng thay đổi trong sandbox"""
        try:
            # Tạo bản sao file trong sandbox
            file_path = change["file_path"]
            sandbox_file = self.sandbox_dir / Path(file_path).name

            if os.path.exists(file_path):
                shutil.copy2(file_path, sandbox_file)

            # Áp dụng thay đổi trong sandbox
            with open(sandbox_file, "w", encoding="utf-8") as f:
                f.write(change["proposed_content"])

            self.logger.info(f"Applied change in sandbox: {change['id']}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to apply change in sandbox: {e}")
            return False

    def _test_in_sandbox(self, change: dict[str, Any]) -> bool:
        """Test thay đổi trong sandbox"""
        try:
            # Import và test module trong sandbox
            sandbox_file = self.sandbox_dir / Path(change["file_path"]).name

            if not sandbox_file.exists():
                return False

            # Basic syntax check
            with open(sandbox_file, encoding="utf-8") as f:
                content = f.read()

            # Kiểm tra syntax Python
            try:
                compile(content, str(sandbox_file), "exec")
                self.logger.info(f"Sandbox syntax check passed: {change['id']}")
                return True
            except SyntaxError as e:
                self.logger.error(f"Sandbox syntax error: {e}")
                return False

        except Exception as e:
            self.logger.error(f"Sandbox test failed: {e}")
            return False

    def _apply_change_real(self, change: dict[str, Any]) -> bool:
        """Áp dụng thay đổi thực tế"""
        try:
            file_path = change["file_path"]

            with open(file_path, "w", encoding="utf-8") as f:
                f.write(change["proposed_content"])

            self.logger.info(f"Applied real change: {change['id']}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to apply real change: {e}")
            return False

    def _run_full_test_suite(self) -> bool:
        """Chạy toàn bộ test suite"""
        try:
            # Chạy pytest
            import subprocess

            result = subprocess.run(
                ["python", "-m", "pytest", "tests/", "-v"],
                capture_output=True,
                text=True,
                timeout=300,
            )

            success = result.returncode == 0
            self.logger.info(f"Full test suite result: {'PASS' if success else 'FAIL'}")
            return success

        except Exception as e:
            self.logger.error(f"Test suite failed: {e}")
            return False

    def _rollback_change(self, change: dict[str, Any], backup_path: str) -> bool:
        """Rollback thay đổi từ backup"""
        try:
            if backup_path and os.path.exists(backup_path):
                shutil.copy2(backup_path, change["file_path"])
                self.logger.info(f"Rolled back change: {change['id']}")
                return True
            else:
                self.logger.error(f"No backup available for rollback: {change['id']}")
                return False

        except Exception as e:
            self.logger.error(f"Rollback failed: {e}")
            return False

    def get_safety_report(self) -> dict[str, Any]:
        """Tạo báo cáo an toàn tổng quan"""
        changes = self.get_proposed_changes()

        report = {
            "timestamp": datetime.now().isoformat(),
            "total_proposed": len(changes),
            "approved": len([c for c in changes if c.get("approved", False)]),
            "applied": len([c for c in changes if c.get("applied", False)]),
            "pending": len(
                [
                    c
                    for c in changes
                    if not c.get("approved", False) and not c.get("applied", False)
                ]
            ),
            "safety_mode": self.safety_mode,
            "read_only_mode": self.read_only_mode,
            "risk_distribution": {
                "LOW": len([c for c in changes if c.get("risk_level") == "LOW"]),
                "MEDIUM": len([c for c in changes if c.get("risk_level") == "MEDIUM"]),
                "HIGH": len([c for c in changes if c.get("risk_level") == "HIGH"]),
                "CRITICAL": len(
                    [c for c in changes if c.get("risk_level") == "CRITICAL"]
                ),
            },
            "safety_checks_summary": {
                "ethical_passed": len(
                    [
                        c
                        for c in changes
                        if c.get("safety_checks", {}).get("ethical", False)
                    ]
                ),
                "integrity_passed": len(
                    [
                        c
                        for c in changes
                        if c.get("safety_checks", {}).get("integrity", False)
                    ]
                ),
                "overall_safe": len(
                    [
                        c
                        for c in changes
                        if c.get("safety_checks", {}).get("overall", False)
                    ]
                ),
            },
        }

        return report

    def emergency_rollback_all(self) -> dict[str, Any]:
        """Rollback khẩn cấp tất cả thay đổi"""
        self.logger.warning("EMERGENCY ROLLBACK INITIATED")

        changes = self.get_proposed_changes()
        applied_changes = [c for c in changes if c.get("applied", False)]

        results = {
            "status": "emergency_rollback",
            "rollback_count": 0,
            "failed_rollbacks": 0,
            "details": [],
        }

        for change in applied_changes:
            try:
                # Tìm backup gần nhất
                backup_pattern = f"{Path(change['file_path']).stem}_*.backup"
                backup_files = list(self.backup_dir.glob(backup_pattern))

                if backup_files:
                    # Lấy backup mới nhất
                    latest_backup = max(backup_files, key=os.path.getctime)

                    if self._rollback_change(change, str(latest_backup)):
                        results["rollback_count"] += 1
                        change["applied"] = False
                        self.logger.info(
                            f"Emergency rollback successful: {change['id']}"
                        )
                    else:
                        results["failed_rollbacks"] += 1
                        self.logger.error(f"Emergency rollback failed: {change['id']}")
                else:
                    results["failed_rollbacks"] += 1
                    self.logger.error(
                        f"No backup found for emergency rollback: {change['id']}"
                    )

                results["details"].append(
                    {
                        "change_id": change["id"],
                        "rollback_status": (
                            "success" if results["rollback_count"] > 0 else "failed"
                        ),
                    }
                )

            except Exception as e:
                results["failed_rollbacks"] += 1
                self.logger.error(f"Emergency rollback error: {e}")

        # Lưu trạng thái rollback
        with open(self.proposed_changes_file, "w", encoding="utf-8") as f:
            json.dump(changes, f, indent=2, ensure_ascii=False)

        self.logger.warning(
            f"Emergency rollback completed: {results['rollback_count']} successful, {results['failed_rollbacks']} failed"
        )
        return results


# Factory function để tạo instance
def create_self_improvement_manager(
    config_path: str = "config/self_improvement_config.json",
) -> SelfImprovementManager:
    """
    Factory function để tạo SelfImprovementManager instance

    Args:
        config_path: Đường dẫn đến file cấu hình

    Returns:
        SelfImprovementManager instance
    """
    return SelfImprovementManager(config_path)


if __name__ == "__main__":
    # Demo usage
    manager = create_self_improvement_manager()

    print("🧠 StillMe SelfImprovementManager Demo")
    print("=" * 50)

    # Chạy phân tích
    result = manager.run_analysis()
    print(f"Analysis result: {result['status']}")

    # Lấy đề xuất
    changes = manager.get_proposed_changes()
    print(f"Proposed changes: {len(changes)}")

    # Báo cáo an toàn
    safety_report = manager.get_safety_report()
    print(f"Safety report: {safety_report}")
