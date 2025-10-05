#!/usr/bin/env python3
"""
AgentDev Validation System - Hệ thống kiểm tra tự động cho AgentDev
Đảm bảo AgentDev hoạt động trung thực và có trách nhiệm

Tính năng chính:
1. Bằng chứng trước/sau khi sửa code
2. Phân loại lỗi rõ ràng (Errors > Warnings > Style)
3. Kiểm tra tự động sau mỗi lần sửa
4. Ưu tiên chất lượng hơn số lượng
"""

import json
import logging
import re
import subprocess
import time
from dataclasses import dataclass
from enum import Enum
from typing import Any

# Thiết lập logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("agentdev_validation.log", encoding="utf-8"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)


class ErrorSeverity(Enum):
    """Phân loại mức độ nghiêm trọng của lỗi"""

    CRITICAL_ERROR = "critical_error"  # Code không chạy được
    WARNING = "warning"  # Code chạy được nhưng có vấn đề tiềm ẩn
    STYLE_SUGGESTION = "style_suggestion"  # Về mặt thẩm mỹ và chuẩn coding


@dataclass
class ValidationResult:
    """Kết quả validation"""

    before_errors: int
    after_errors: int
    errors_fixed: int
    critical_errors: int
    warnings: int
    style_suggestions: int
    execution_time: float
    success: bool
    evidence_files: list[str]
    error_details: list[dict[str, Any]]


class AgentDevValidator:
    """Hệ thống validation cho AgentDev"""

    def __init__(self, project_root: str = "."):
        self.project_root = project_root
        self.validation_log: list[dict[str, Any]] = []

    def run_pyright_check(self) -> tuple[int, list[dict[str, Any]]]:
        """Chạy pyright và trả về số lỗi + chi tiết"""
        try:
            logger.info("🔍 Chạy pyright check...")
            result = subprocess.run(
                ["pyright", "--stats", "framework.py", "modules/"],
                capture_output=True,
                text=True,
                cwd=self.project_root,
                timeout=60,
            )

            # Parse output để lấy số lỗi
            output = result.stdout + result.stderr
            error_count = 0
            error_details = []

            # Tìm số lỗi từ output
            error_match = re.search(
                r"(\d+) errors?, (\d+) warnings?, (\d+) informations?", output
            )
            if error_match:
                error_count = int(error_match.group(1))
                warnings = int(error_match.group(2))
                infos = int(error_match.group(3))

                # Phân loại lỗi
                error_details: list[dict[str, Any]] = self._classify_pyright_errors(
                    output
                )

                logger.info(
                    f"📊 Pyright: {error_count} errors, {warnings} warnings, {infos} infos"
                )
                return error_count, error_details

        except subprocess.TimeoutExpired:
            logger.error("⏰ Pyright timeout")
            return -1, []
        except Exception as e:
            logger.error(f"❌ Lỗi chạy pyright: {e}")
            return -1, []

        return 0, []

    def run_ruff_check(self) -> tuple[int, list[dict[str, Any]]]:
        """Chạy ruff và trả về số lỗi + chi tiết"""
        try:
            logger.info("🔍 Chạy ruff check...")
            result = subprocess.run(
                ["ruff", "check", ".", "--force-exclude"],
                capture_output=True,
                text=True,
                cwd=self.project_root,
                timeout=30,
            )

            output = result.stdout
            error_count = 0
            error_details = []

            # Parse output để lấy số lỗi
            if output and "Found" in output:
                error_match = re.search(r"Found (\d+) errors?", output)
                if error_match:
                    error_count = int(error_match.group(1))
                    error_details: list[dict[str, Any]] = self._classify_ruff_errors(
                        output
                    )

            logger.info(f"📊 Ruff: {error_count} errors")
            return error_count, error_details

        except subprocess.TimeoutExpired:
            logger.error("⏰ Ruff timeout")
            return -1, []
        except Exception as e:
            logger.error(f"❌ Lỗi chạy ruff: {e}")
            return -1, []

    def _classify_pyright_errors(self, output: str) -> list[dict[str, Any]]:
        """Phân loại lỗi pyright theo mức độ nghiêm trọng"""
        errors: list[dict[str, Any]] = []
        lines = output.split("\n")

        for line in lines:
            if "error:" in line.lower():
                severity = ErrorSeverity.CRITICAL_ERROR
            elif "warning:" in line.lower():
                severity = ErrorSeverity.WARNING
            elif "information:" in line.lower():
                severity = ErrorSeverity.STYLE_SUGGESTION
            else:
                continue

            errors.append(
                {"severity": severity.value, "message": line.strip(), "type": "pyright"}
            )

        return errors

    def _classify_ruff_errors(self, output: str) -> list[dict[str, Any]]:
        """Phân loại lỗi ruff theo mức độ nghiêm trọng"""
        errors: list[dict[str, Any]] = []
        lines = output.split("\n")

        for line in lines:
            if not line.strip() or "Found" in line:
                continue

            # Phân loại theo mã lỗi
            if any(code in line for code in ["F", "E9"]):  # Fatal errors
                severity = ErrorSeverity.CRITICAL_ERROR
            elif any(code in line for code in ["E", "W"]):  # Errors và Warnings
                severity = ErrorSeverity.WARNING
            else:  # Style suggestions
                severity = ErrorSeverity.STYLE_SUGGESTION

            errors.append(
                {"severity": severity.value, "message": line.strip(), "type": "ruff"}
            )

        return errors

    def run_quick_test(self) -> bool:
        """Chạy test nhanh để đảm bảo code không bị break"""
        try:
            logger.info("🧪 Chạy quick test...")

            # Test import các module chính
            test_commands = [
                ["python", "-c", "import framework; print('Framework OK')"],
                [
                    "python",
                    "-c",
                    "import modules.market_intel; print('Market Intel OK')",
                ],
                [
                    "python",
                    "-c",
                    "import modules.emotionsense_v1; print('EmotionSense OK')",
                ],
            ]

            for cmd in test_commands:
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    cwd=self.project_root,
                    timeout=10,
                )
                if result.returncode != 0:
                    logger.error(f"❌ Test failed: {' '.join(cmd)}")
                    return False

            logger.info("✅ Quick test passed")
            return True

        except Exception as e:
            logger.error(f"❌ Lỗi chạy quick test: {e}")
            return False

    def validate_before_fix(self) -> dict[str, Any]:
        """Kiểm tra trạng thái trước khi sửa"""
        logger.info("📋 BẮT ĐẦU VALIDATION - TRẠNG THÁI TRƯỚC KHI SỬA")

        start_time = time.time()

        # Chạy các lệnh kiểm tra
        pyright_errors, pyright_details = self.run_pyright_check()
        ruff_errors, ruff_details = self.run_ruff_check()
        test_passed = self.run_quick_test()

        # Tạo bằng chứng
        evidence_file = f"validation_before_{int(time.time())}.json"
        evidence_data: dict[str, Any] = {
            "timestamp": time.time(),
            "pyright_errors": pyright_errors,
            "ruff_errors": ruff_errors,
            "test_passed": test_passed,
            "pyright_details": pyright_details,
            "ruff_details": ruff_details,
            "total_errors": pyright_errors + ruff_errors,
        }

        with open(evidence_file, "w", encoding="utf-8") as f:
            json.dump(evidence_data, f, indent=2, ensure_ascii=False)

        logger.info(f"💾 Bằng chứng trước khi sửa: {evidence_file}")

        return {
            "evidence_file": evidence_file,
            "pyright_errors": pyright_errors,
            "ruff_errors": ruff_errors,
            "total_errors": pyright_errors + ruff_errors,
            "test_passed": test_passed,
            "execution_time": time.time() - start_time,
        }

    def validate_after_fix(self, before_data: dict[str, Any]) -> ValidationResult:
        """Kiểm tra trạng thái sau khi sửa"""
        logger.info("📋 VALIDATION - TRẠNG THÁI SAU KHI SỬA")

        start_time = time.time()

        # Chạy các lệnh kiểm tra
        pyright_errors, pyright_details = self.run_pyright_check()
        ruff_errors, ruff_details = self.run_ruff_check()
        test_passed = self.run_quick_test()

        # Tính toán kết quả
        total_before = before_data.get("total_errors", 0)
        total_after = pyright_errors + ruff_errors
        errors_fixed = total_before - total_after

        # Phân loại lỗi
        all_details: list[dict[str, Any]] = pyright_details + ruff_details
        critical_errors = len(
            [
                e
                for e in all_details
                if e["severity"] == ErrorSeverity.CRITICAL_ERROR.value
            ]
        )
        warnings = len(
            [e for e in all_details if e["severity"] == ErrorSeverity.WARNING.value]
        )
        style_suggestions = len(
            [
                e
                for e in all_details
                if e["severity"] == ErrorSeverity.STYLE_SUGGESTION.value
            ]
        )

        # Tạo bằng chứng
        evidence_file = f"validation_after_{int(time.time())}.json"
        evidence_data: dict[str, Any] = {
            "timestamp": time.time(),
            "before_data": before_data,
            "pyright_errors": pyright_errors,
            "ruff_errors": ruff_errors,
            "test_passed": test_passed,
            "pyright_details": pyright_details,
            "ruff_details": ruff_details,
            "total_errors": total_after,
            "errors_fixed": errors_fixed,
            "critical_errors": critical_errors,
            "warnings": warnings,
            "style_suggestions": style_suggestions,
        }

        with open(evidence_file, "w", encoding="utf-8") as f:
            json.dump(evidence_data, f, indent=2, ensure_ascii=False)

        # Đánh giá thành công
        success: bool = (
            (
                errors_fixed > 0  # Có sửa được lỗi
                and test_passed  # Code vẫn chạy được
                and (
                    critical_errors == 0
                    or critical_errors
                    < (
                        before_data["critical_errors"]
                        if "critical_errors" in before_data
                        else 0
                    )
                )  # Giảm lỗi nghiêm trọng
            )
            if total_before > 0
            else True
        )  # Nếu không có lỗi ban đầu thì coi như thành công

        result = ValidationResult(
            before_errors=total_before,
            after_errors=total_after,
            errors_fixed=errors_fixed,
            critical_errors=critical_errors,
            warnings=warnings,
            style_suggestions=style_suggestions,
            execution_time=time.time() - start_time,
            success=success,
            evidence_files=[
                before_data.get("evidence_file", "before_validation.json"),
                evidence_file,
            ],
            error_details=all_details,
        )

        logger.info(f"💾 Bằng chứng sau khi sửa: {evidence_file}")
        self._log_validation_result(result)

        return result

    def _log_validation_result(self, result: ValidationResult):
        """Ghi log kết quả validation"""
        logger.info("=" * 60)
        logger.info("📊 KẾT QUẢ VALIDATION")
        logger.info("=" * 60)
        logger.info(f"🔢 Lỗi trước khi sửa: {result.before_errors}")
        logger.info(f"🔢 Lỗi sau khi sửa: {result.after_errors}")
        logger.info(f"✅ Lỗi đã sửa: {result.errors_fixed}")
        logger.info(f"🚨 Lỗi nghiêm trọng: {result.critical_errors}")
        logger.info(f"⚠️  Cảnh báo: {result.warnings}")
        logger.info(f"💡 Gợi ý style: {result.style_suggestions}")
        logger.info(f"⏱️  Thời gian: {result.execution_time:.2f}s")
        logger.info(f"🎯 Thành công: {'✅' if result.success else '❌'}")
        logger.info(f"📁 Bằng chứng: {', '.join(result.evidence_files)}")
        logger.info("=" * 60)

        # Lưu vào log file
        self.validation_log.append(
            {"timestamp": time.time(), "result": result.__dict__}
        )

    def get_quality_score(self, result: ValidationResult) -> float:
        """Tính điểm chất lượng dựa trên quy tắc: 1 lỗi quan trọng > 100 lỗi vặt"""
        if result.critical_errors > 0:
            # Có lỗi nghiêm trọng = điểm thấp
            return max(0, 50 - (result.critical_errors * 20))

        # Không có lỗi nghiêm trọng, tính điểm dựa trên tổng lỗi đã sửa
        base_score = min(100, result.errors_fixed * 2)

        # Bonus nếu sửa được nhiều warning
        warning_bonus = min(20, result.warnings * 0.5)

        # Penalty nếu còn nhiều style suggestions
        style_penalty = min(10, result.style_suggestions * 0.1)

        return max(0, base_score + warning_bonus - style_penalty)

    def generate_report(self, result: ValidationResult) -> str:
        """Tạo báo cáo chi tiết"""
        quality_score = self.get_quality_score(result)

        report = f"""
# 📊 BÁO CÁO VALIDATION AGENTDEV

## 🎯 Tổng quan
- **Điểm chất lượng**: {quality_score:.1f}/100
- **Trạng thái**: {'✅ THÀNH CÔNG' if result.success else '❌ THẤT BẠI'}
- **Thời gian thực hiện**: {result.execution_time:.2f}s

## 📈 Thống kê lỗi
- **Trước khi sửa**: {result.before_errors} lỗi
- **Sau khi sửa**: {result.after_errors} lỗi
- **Đã sửa**: {result.errors_fixed} lỗi

## 🚨 Phân loại lỗi
- **Lỗi nghiêm trọng**: {result.critical_errors} (ưu tiên cao nhất)
- **Cảnh báo**: {result.warnings} (ưu tiên trung bình)
- **Gợi ý style**: {result.style_suggestions} (ưu tiên thấp nhất)

## 📁 Bằng chứng
- **Trước khi sửa**: {result.evidence_files[0]}
- **Sau khi sửa**: {result.evidence_files[1]}

## 💡 Đánh giá
"""

        if result.success:
            report += "✅ **THÀNH CÔNG**: AgentDev đã sửa được lỗi và code vẫn hoạt động bình thường.\n"
        else:
            report += "❌ **THẤT BẠI**: Cần kiểm tra lại quá trình sửa lỗi.\n"

        if quality_score >= 80:
            report += "🌟 **CHẤT LƯỢNG CAO**: Điểm số xuất sắc!\n"
        elif quality_score >= 60:
            report += "👍 **CHẤT LƯỢNG TỐT**: Điểm số khá tốt.\n"
        else:
            report += "⚠️ **CẦN CẢI THIỆN**: Điểm số thấp, cần tập trung vào lỗi nghiêm trọng.\n"

        return report


def main():
    """Hàm main để test hệ thống validation"""
    validator = AgentDevValidator()

    print("🧪 Test hệ thống validation...")

    # Test validation trước khi sửa
    before_data: dict[str, Any] = validator.validate_before_fix()
    print(f"📊 Trước khi sửa: {before_data['total_errors']} lỗi")

    # Giả lập sửa lỗi (không thực sự sửa gì)
    print("⏳ Giả lập quá trình sửa lỗi...")
    time.sleep(2)

    # Test validation sau khi sửa
    result = validator.validate_after_fix(before_data)

    # Tạo báo cáo
    report = validator.generate_report(result)
    print(report)

    # Lưu báo cáo
    with open(f"validation_report_{int(time.time())}.md", "w", encoding="utf-8") as f:
        f.write(report)


if __name__ == "__main__":
    main()
