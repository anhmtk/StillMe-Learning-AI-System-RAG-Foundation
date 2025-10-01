
"""
Unit tests cho SelfImprovementManager

Test các cơ chế an toàn tối đa:
1. CHỈ ĐỌC, KHÔNG GHI
2. ĐỀ XUẤT PHẢI ĐƯỢC DUYỆT
3. VÒNG KIỂM SOÁT 4 MẮT
4. SANDOX MODE
5. ROLLBACK TỰ ĐỘNG

Author: StillMe AI Framework
Version: 1.0.0
"""

import json
import os
import shutil
import tempfile
from datetime import datetime
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from stillme_core.modules.self_improvement_manager import (
    ProposedChange,
    SafetyReport,
    SelfImprovementManager,
    create_self_improvement_manager,
)


class TestSelfImprovementManager:
    """Test class cho SelfImprovementManager"""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test environment"""
        # Tạo temporary directory cho test
        self.test_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()
        os.chdir(self.test_dir)

        # Tạo cấu trúc thư mục test
        Path("config").mkdir(exist_ok=True)
        Path("modules").mkdir(exist_ok=True)
        Path("tests").mkdir(exist_ok=True)
        Path("logs").mkdir(exist_ok=True)

        # Tạo config file test
        self.config_path = "config/self_improvement_config.json"
        self.manager = SelfImprovementManager(self.config_path)

        yield

        # Cleanup
        os.chdir(self.original_cwd)
        shutil.rmtree(self.test_dir)

    def test_initialization(self):
        """Test khởi tạo SelfImprovementManager"""
        assert self.manager.safety_mode is True
        assert self.manager.read_only_mode is True
        assert self.manager.config is not None
        assert "safety_mode" in self.manager.config
        assert "read_only_mode" in self.manager.config

    def test_config_loading(self):
        """Test load cấu hình"""
        config = self.manager.config

        # Kiểm tra các key quan trọng
        assert config["safety_mode"] is True
        assert config["read_only_mode"] is True
        assert config["auto_approve_low_risk"] is False
        assert "forbidden_file_patterns" in config
        assert "critical_files" in config

    def test_file_allowed_check(self):
        """Test kiểm tra file có được phép chỉnh sửa"""
        # File được phép
        assert self.manager._is_file_allowed("modules/test_module.py") is True
        assert self.manager._is_file_allowed("config/test_config.json") is True

        # File bị cấm
        assert self.manager._is_file_allowed("__pycache__/test.pyc") is False
        assert self.manager._is_file_allowed("backup_legacy/test.py") is False
        assert self.manager._is_file_allowed("tests/fixtures/test.py") is False
        assert self.manager._is_file_allowed("node_modules/test.js") is False

    def test_critical_file_warning(self):
        """Test cảnh báo file quan trọng"""
        # File quan trọng cần approval đặc biệt
        with patch.object(self.manager.logger, "warning") as mock_warning:
            self.manager._is_file_allowed("framework.py")
            mock_warning.assert_called_once()

    def test_change_id_generation(self):
        """Test tạo ID duy nhất cho đề xuất"""
        id1 = self.manager._generate_change_id("prompt", "test.py")
        id2 = self.manager._generate_change_id("prompt", "test.py")

        # ID phải khác nhau
        assert id1 != id2

        # ID phải có format đúng
        assert id1.startswith("prompt_")
        assert len(id1) > 10

    def test_collect_analysis_data(self):
        """Test thu thập dữ liệu phân tích (CHỈ ĐỌC)"""
        # Tạo file test
        with open("conversation_log.txt", "w") as f:
            f.write("Test conversation log")

        with open("api_usage.log", "w") as f:
            f.write("Test performance log")

        with open("api_errors.log", "w") as f:
            f.write("Test error log")

        # Thu thập dữ liệu
        data = self.manager._collect_analysis_data()

        # Kiểm tra cấu trúc dữ liệu
        assert "timestamp" in data
        assert "chat_history" in data
        assert "performance_logs" in data
        assert "error_logs" in data
        assert "system_metrics" in data
        assert "user_feedback" in data

        # Kiểm tra dữ liệu đã đọc
        assert len(data["chat_history"]) > 0
        assert len(data["performance_logs"]) > 0
        assert len(data["error_logs"]) > 0

    def test_read_chat_history(self):
        """Test đọc lịch sử chat"""
        # Tạo file test
        with open("conversation_log.txt", "w") as f:
            f.write("Test conversation")

        with open("conversation_memory.json", "w") as f:
            json.dump({"test": "data"}, f)

        # Đọc lịch sử
        history = self.manager._read_chat_history()

        assert len(history) >= 2
        assert any("conversation_log.txt" in h["file"] for h in history)
        assert any("conversation_memory.json" in h["file"] for h in history)

    def test_read_performance_logs(self):
        """Test đọc logs hiệu suất"""
        # Tạo file test
        with open("api_usage.log", "w") as f:
            f.write("Test performance log")

        with open("performance_metrics.json", "w") as f:
            json.dump({"response_time": 1.5}, f)

        # Đọc logs
        logs = self.manager._read_performance_logs()

        assert len(logs) >= 2
        assert any("api_usage.log" in l["file"] for l in logs)
        assert any("performance_metrics.json" in l["file"] for l in logs)

    def test_read_error_logs(self):
        """Test đọc logs lỗi"""
        # Tạo file test
        with open("api_errors.log", "w") as f:
            f.write("Test error log")

        with open("stillme.log", "w") as f:
            f.write("Test system log")

        # Đọc logs
        errors = self.manager._read_error_logs()

        assert len(errors) >= 2
        assert any("api_errors.log" in e["file"] for e in errors)
        assert any("stillme.log" in e["file"] for e in errors)

    def test_read_system_metrics(self):
        """Test đọc metrics hệ thống"""
        # Tạo file test
        with open("modules/test_module.py", "w") as f:
            f.write("# Test module")

        with open("tests/test_something.py", "w") as f:
            f.write("# Test file")

        # Đọc metrics
        metrics = self.manager._read_system_metrics()

        assert "timestamp" in metrics
        assert "file_count" in metrics
        assert "module_count" in metrics
        assert "test_count" in metrics
        assert metrics["module_count"] >= 1
        assert metrics["test_count"] >= 1

    @patch("modules.self_improvement_manager.EthicalCoreSystem")
    @patch("modules.self_improvement_manager.ContentIntegrityFilter")
    def test_safety_check_change(self, mock_integrity, mock_ethical):
        """Test kiểm tra an toàn đề xuất (VÒNG KIỂM SOÁT 4 MẮT)"""
        # Mock các module kiểm tra
        mock_ethical_instance = Mock()
        mock_ethical_instance.approve_change.return_value = True
        mock_ethical.return_value = mock_ethical_instance

        mock_integrity_instance = Mock()
        mock_integrity_instance.validate_change.return_value = True
        mock_integrity.return_value = mock_integrity_instance

        # Tạo đề xuất test
        change = {
            "id": "test_change_1",
            "file_path": "modules/test_module.py",
            "risk_level": "LOW",
            "safety_checks": {},
            "test_results": {},
        }

        # Kiểm tra an toàn
        result = self.manager._safety_check_change(change)

        assert result is True
        assert change["safety_checks"]["ethical"] is True
        assert change["safety_checks"]["integrity"] is True
        assert change["safety_checks"]["overall"] is True

        # Verify các module được gọi
        mock_ethical_instance.approve_change.assert_called_once_with(change)
        mock_integrity_instance.validate_change.assert_called_once_with(change)

    def test_safety_check_high_risk(self):
        """Test kiểm tra an toàn cho đề xuất rủi ro cao"""
        change = {
            "id": "test_change_1",
            "file_path": "modules/test_module.py",
            "risk_level": "HIGH",
            "safety_checks": {},
            "test_results": {},
        }

        # Kiểm tra an toàn
        result = self.manager._safety_check_change(change)

        assert result is False
        assert change["safety_checks"]["risk_approval"] is False

    def test_safety_check_forbidden_file(self):
        """Test kiểm tra an toàn cho file bị cấm"""
        change = {
            "id": "test_change_1",
            "file_path": "__pycache__/test.pyc",
            "risk_level": "LOW",
            "safety_checks": {},
            "test_results": {},
        }

        # Kiểm tra an toàn
        result = self.manager._safety_check_change(change)

        assert result is False

    @patch("modules.self_improvement_manager.EthicalCoreSystem")
    @patch("modules.self_improvement_manager.ContentIntegrityFilter")
    def test_run_analysis(self, mock_integrity, mock_ethical):
        """Test chạy phân tích tổng thể"""
        # Mock các module kiểm tra
        mock_ethical_instance = Mock()
        mock_ethical_instance.approve_change.return_value = True
        mock_ethical.return_value = mock_ethical_instance

        mock_integrity_instance = Mock()
        mock_integrity_instance.validate_change.return_value = True
        mock_integrity.return_value = mock_integrity_instance

        # Tạo file test
        with open("conversation_log.txt", "w") as f:
            f.write("Test conversation")

        # Chạy phân tích
        result = self.manager.run_analysis()

        assert result["status"] == "success"
        assert "analysis_data" in result
        assert "proposed_changes" in result
        assert result["safety_mode"] is True
        assert result["read_only_mode"] is True

    def test_save_proposed_changes(self):
        """Test lưu đề xuất thay đổi"""
        changes = [
            {
                "id": "test_change_1",
                "timestamp": datetime.now().isoformat(),
                "change_type": "prompt",
                "file_path": "test.py",
                "description": "Test change",
                "current_content": "old content",
                "proposed_content": "new content",
                "reason": "Test reason",
                "risk_level": "LOW",
                "safety_checks": {"overall": True},
                "test_results": {},
            }
        ]

        # Lưu đề xuất
        self.manager._save_proposed_changes(changes)

        # Kiểm tra file đã được tạo
        assert os.path.exists(self.manager.proposed_changes_file)

        # Kiểm tra nội dung
        with open(self.manager.proposed_changes_file) as f:
            saved_changes = json.load(f)

        assert len(saved_changes) == 1
        assert saved_changes[0]["id"] == "test_change_1"

    def test_get_proposed_changes(self):
        """Test lấy danh sách đề xuất"""
        # Tạo file đề xuất test
        test_changes = [
            {"id": "test_change_1", "description": "Test change 1", "approved": False},
            {"id": "test_change_2", "description": "Test change 2", "approved": True},
        ]

        with open(self.manager.proposed_changes_file, "w") as f:
            json.dump(test_changes, f)

        # Lấy đề xuất
        changes = self.manager.get_proposed_changes()

        assert len(changes) == 2
        assert changes[0]["id"] == "test_change_1"
        assert changes[1]["id"] == "test_change_2"

    def test_approve_change(self):
        """Test phê duyệt đề xuất"""
        # Tạo file đề xuất test
        test_changes = [
            {"id": "test_change_1", "description": "Test change 1", "approved": False}
        ]

        with open(self.manager.proposed_changes_file, "w") as f:
            json.dump(test_changes, f)

        # Phê duyệt đề xuất
        result = self.manager.approve_change("test_change_1", True)

        assert result is True

        # Kiểm tra đã được lưu
        changes = self.manager.get_proposed_changes()
        assert changes[0]["approved"] is True
        assert "approval_timestamp" in changes[0]

    def test_approve_nonexistent_change(self):
        """Test phê duyệt đề xuất không tồn tại"""
        result = self.manager.approve_change("nonexistent_change", True)
        assert result is False

    def test_create_backup(self):
        """Test tạo backup"""
        # Tạo file test
        test_file = "test_file.py"
        with open(test_file, "w") as f:
            f.write("test content")

        # Tạo backup
        change = {"file_path": test_file}
        backup_path = self.manager._create_backup(change)

        assert backup_path != ""
        assert os.path.exists(backup_path)

        # Kiểm tra nội dung backup
        with open(backup_path) as f:
            backup_content = f.read()
        assert backup_content == "test content"

    def test_apply_change_sandbox(self):
        """Test áp dụng thay đổi trong sandbox"""
        # Tạo file test
        test_file = "test_file.py"
        with open(test_file, "w") as f:
            f.write("old content")

        # Tạo đề xuất
        change = {
            "id": "test_change_1",
            "file_path": test_file,
            "proposed_content": "new content",
        }

        # Áp dụng trong sandbox
        result = self.manager._apply_change_sandbox(change)

        assert result is True

        # Kiểm tra file sandbox
        sandbox_file = self.manager.sandbox_dir / Path(test_file).name
        assert sandbox_file.exists()

        with open(sandbox_file) as f:
            content = f.read()
        assert content == "new content"

    def test_test_in_sandbox(self):
        """Test kiểm tra trong sandbox"""
        # Tạo file sandbox với syntax đúng
        sandbox_file = self.manager.sandbox_dir / "test_syntax.py"
        with open(sandbox_file, "w") as f:
            f.write("print('Hello, World!')")

        change = {"file_path": "test_syntax.py"}
        result = self.manager._test_in_sandbox(change)

        assert result is True

    def test_test_in_sandbox_syntax_error(self):
        """Test kiểm tra trong sandbox với syntax lỗi"""
        # Tạo file sandbox với syntax lỗi
        sandbox_file = self.manager.sandbox_dir / "test_syntax_error.py"
        with open(sandbox_file, "w") as f:
            f.write("print('Hello, World!'")  # Thiếu dấu đóng ngoặc

        change = {"file_path": "test_syntax_error.py"}
        result = self.manager._test_in_sandbox(change)

        assert result is False

    def test_apply_change_real(self):
        """Test áp dụng thay đổi thực tế"""
        # Tạo file test
        test_file = "test_file.py"
        with open(test_file, "w") as f:
            f.write("old content")

        # Tạo đề xuất
        change = {
            "id": "test_change_1",
            "file_path": test_file,
            "proposed_content": "new content",
        }

        # Áp dụng thực tế
        result = self.manager._apply_change_real(change)

        assert result is True

        # Kiểm tra file đã được thay đổi
        with open(test_file) as f:
            content = f.read()
        assert content == "new content"

    @patch("subprocess.run")
    def test_run_full_test_suite(self, mock_run):
        """Test chạy toàn bộ test suite"""
        # Mock subprocess thành công
        mock_run.return_value.returncode = 0

        result = self.manager._run_full_test_suite()

        assert result is True
        mock_run.assert_called_once()

    @patch("subprocess.run")
    def test_run_full_test_suite_failure(self, mock_run):
        """Test chạy test suite thất bại"""
        # Mock subprocess thất bại
        mock_run.return_value.returncode = 1

        result = self.manager._run_full_test_suite()

        assert result is False

    def test_rollback_change(self):
        """Test rollback thay đổi"""
        # Tạo file test
        test_file = "test_file.py"
        with open(test_file, "w") as f:
            f.write("modified content")

        # Tạo backup
        backup_file = "backup_file.py"
        with open(backup_file, "w") as f:
            f.write("original content")

        # Tạo đề xuất
        change = {"file_path": test_file}

        # Rollback
        result = self.manager._rollback_change(change, backup_file)

        assert result is True

        # Kiểm tra file đã được rollback
        with open(test_file) as f:
            content = f.read()
        assert content == "original content"

    def test_rollback_change_no_backup(self):
        """Test rollback khi không có backup"""
        change = {"file_path": "nonexistent.py"}
        result = self.manager._rollback_change(change, "")

        assert result is False

    def test_get_safety_report(self):
        """Test tạo báo cáo an toàn"""
        # Tạo file đề xuất test
        test_changes = [
            {
                "id": "test_change_1",
                "risk_level": "LOW",
                "approved": True,
                "applied": True,
                "safety_checks": {"ethical": True, "integrity": True, "overall": True},
            },
            {
                "id": "test_change_2",
                "risk_level": "HIGH",
                "approved": False,
                "applied": False,
                "safety_checks": {
                    "ethical": False,
                    "integrity": True,
                    "overall": False,
                },
            },
        ]

        with open(self.manager.proposed_changes_file, "w") as f:
            json.dump(test_changes, f)

        # Tạo báo cáo
        report = self.manager.get_safety_report()

        assert report["total_proposed"] == 2
        assert report["approved"] == 1
        assert report["applied"] == 1
        assert report["pending"] == 1
        assert report["safety_mode"] is True
        assert report["read_only_mode"] is True
        assert report["risk_distribution"]["LOW"] == 1
        assert report["risk_distribution"]["HIGH"] == 1
        assert report["safety_checks_summary"]["ethical_passed"] == 1
        assert report["safety_checks_summary"]["overall_safe"] == 1

    def test_emergency_rollback_all(self):
        """Test rollback khẩn cấp tất cả"""
        # Tạo file đề xuất với thay đổi đã áp dụng
        test_changes = [
            {"id": "test_change_1", "file_path": "test_file.py", "applied": True}
        ]

        with open(self.manager.proposed_changes_file, "w") as f:
            json.dump(test_changes, f)

        # Tạo backup
        test_file = "test_file.py"
        with open(test_file, "w") as f:
            f.write("modified content")

        backup_file = self.manager.backup_dir / "test_file_20250101_120000.backup"
        with open(backup_file, "w") as f:
            f.write("original content")

        # Rollback khẩn cấp
        result = self.manager.emergency_rollback_all()

        assert result["status"] == "emergency_rollback"
        assert result["rollback_count"] == 1
        assert result["failed_rollbacks"] == 0

    def test_factory_function(self):
        """Test factory function"""
        manager = create_self_improvement_manager(self.config_path)

        assert isinstance(manager, SelfImprovementManager)
        assert manager.config_path == self.config_path


class TestProposedChange:
    """Test class cho ProposedChange dataclass"""

    def test_proposed_change_creation(self):
        """Test tạo ProposedChange"""
        change = ProposedChange(
            id="test_id",
            timestamp="2025-01-01T12:00:00",
            change_type="prompt",
            file_path="test.py",
            description="Test change",
            current_content="old",
            proposed_content="new",
            reason="Test reason",
            risk_level="LOW",
            safety_checks={"test": True},
            test_results={"test": True},
        )

        assert change.id == "test_id"
        assert change.change_type == "prompt"
        assert change.risk_level == "LOW"
        assert change.approved is False
        assert change.applied is False
        assert change.rollback_available is False

    def test_proposed_change_asdict(self):
        """Test chuyển ProposedChange thành dict"""
        change = ProposedChange(
            id="test_id",
            timestamp="2025-01-01T12:00:00",
            change_type="prompt",
            file_path="test.py",
            description="Test change",
            current_content="old",
            proposed_content="new",
            reason="Test reason",
            risk_level="LOW",
            safety_checks={"test": True},
            test_results={"test": True},
        )

        from dataclasses import asdict
        change_dict = asdict(change)

        assert isinstance(change_dict, dict)
        assert change_dict["id"] == "test_id"
        assert change_dict["change_type"] == "prompt"


class TestSafetyReport:
    """Test class cho SafetyReport dataclass"""

    def test_safety_report_creation(self):
        """Test tạo SafetyReport"""
        report = SafetyReport(
            change_id="test_id",
            ethical_check=True,
            integrity_check=True,
            test_check=True,
            overall_safe=True,
            warnings=["Test warning"],
            recommendations=["Test recommendation"],
        )

        assert report.change_id == "test_id"
        assert report.ethical_check is True
        assert report.overall_safe is True
        assert len(report.warnings) == 1
        assert len(report.recommendations) == 1


@pytest.mark.integration
class TestSelfImprovementManagerIntegration:
    """Integration tests cho SelfImprovementManager"""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup integration test environment"""
        self.test_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()
        os.chdir(self.test_dir)

        # Tạo cấu trúc thư mục đầy đủ
        Path("config").mkdir(exist_ok=True)
        Path("modules").mkdir(exist_ok=True)
        Path("tests").mkdir(exist_ok=True)
        Path("logs").mkdir(exist_ok=True)
        Path("backups").mkdir(exist_ok=True)

        self.manager = SelfImprovementManager()

        yield

        os.chdir(self.original_cwd)
        shutil.rmtree(self.test_dir)

    def test_full_workflow(self):
        """Test workflow đầy đủ từ phân tích đến áp dụng"""
        # Tạo dữ liệu test
        with open("conversation_log.txt", "w") as f:
            f.write(
                "User: How to code in Python?\nAI: Python is a programming language..."
            )

        with open("api_usage.log", "w") as f:
            f.write("Response time: 5.2s\nResponse time: 4.8s")

        # Bước 1: Chạy phân tích
        analysis_result = self.manager.run_analysis()
        assert analysis_result["status"] == "success"

        # Bước 2: Lấy đề xuất
        changes = self.manager.get_proposed_changes()
        assert len(changes) > 0

        # Bước 3: Phê duyệt đề xuất
        if changes:
            change_id = changes[0]["id"]
            approval_result = self.manager.approve_change(change_id, True)
            assert approval_result is True

        # Bước 4: Tạo báo cáo an toàn
        safety_report = self.manager.get_safety_report()
        assert safety_report["total_proposed"] > 0

        # Bước 5: Kiểm tra trạng thái an toàn
        assert safety_report["safety_mode"] is True
        assert safety_report["read_only_mode"] is True


if __name__ == "__main__":
    # Chạy tests
    pytest.main([__file__, "-v"])
