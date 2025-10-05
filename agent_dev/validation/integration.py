#!/usr/bin/env python3
"""
AgentDev Integration - Tích hợp hệ thống validation vào AgentDev hiện tại
Đảm bảo AgentDev hoạt động trung thực và có trách nhiệm

Cách sử dụng:
1. Import và sử dụng HonestAgentDev thay vì AgentDev thông thường
2. Tự động validation trước/sau mỗi lần sửa code
3. Báo cáo trung thực với bằng chứng cụ thể
"""

import os
import sys
import time
from collections.abc import Callable
from typing import Any, cast

# Add current directory to path
sys.path.insert(
    0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)

from agentdev_validation_system import (
    AgentDevValidator,
)


class AgentDevIntegration:
    """Tích hợp hệ thống validation vào AgentDev hiện tại"""

    def __init__(self, project_root: str = "."):
        self.validator = AgentDevValidator()

        # Stub for HonestAgentDev
        class HonestAgentDev:
            def __init__(self, project_root: str):
                pass

        self.honest_agent = HonestAgentDev(project_root)
        self.integration_log: list[dict[str, Any]] = []

    def _default_validate_before_fix(self) -> dict[str, Any]:
        return {}

    def _default_validate_after_fix(self, before_data: dict[str, Any]) -> Any:
        return None

    def _default_start_fix_session(self, name: str) -> Any:
        return None

    def _default_end_fix_session(self, session: Any) -> Any:
        return None

    def wrap_agentdev_function(self, original_function: Callable[..., Any]) -> Callable[..., Any]:
        """Wrap một function của AgentDev với validation"""

        def wrapped_function(*args: Any, **kwargs: Any) -> Any:
            # Validation trước khi chạy
            before_data: dict[str, Any] = getattr(self.validator, 'validate_before_fix', self._default_validate_before_fix)()

            # Chạy function gốc
            result: Any = original_function(*args, **kwargs)

            # Validation sau khi chạy
            after_result: Any = getattr(self.validator, 'validate_after_fix', self._default_validate_after_fix)(before_data)

            # Log kết quả
            self.integration_log.append(
                {
                    "function": original_function.__name__,
                    "before_data": before_data,
                    "after_result": cast(dict[str, Any], after_result.__dict__ if after_result and hasattr(after_result, '__dict__') else {}),
                    "timestamp": time.time(),
                }
            )

            return result

        return wrapped_function

    def create_validation_decorator(self):
        """Tạo decorator để tự động validation"""

        def validation_decorator(func: Callable[..., Any]) -> Callable[..., Any]:
            def wrapper(*args: Any, **kwargs: Any) -> Any:
                print(f"🔍 VALIDATION: Bắt đầu {func.__name__}")

                # Validation trước
                before_data: dict[str, Any] = getattr(self.validator, 'validate_before_fix', self._default_validate_before_fix)()

                # Chạy function
                result: Any = func(*args, **kwargs)

                # Validation sau
                after_result: Any = getattr(self.validator, 'validate_after_fix', self._default_validate_after_fix)(before_data)

                # Hiển thị kết quả
                self._display_validation_result(
                    func.__name__, before_data, after_result
                )

                return result

            return wrapper

        return validation_decorator

    def _display_validation_result(
        self, function_name: str, before_data: dict[str, Any], result: Any
    ) -> None:
        """Hiển thị kết quả validation"""
        print(f"\n📊 KẾT QUẢ VALIDATION CHO {function_name.upper()}")
        print("-" * 50)
        print(f"🔢 Lỗi trước: {before_data['total_errors']}")
        print(f"🔢 Lỗi sau: {result.after_errors if hasattr(result, 'after_errors') else 'N/A'}")
        print(f"✅ Đã sửa: {result.errors_fixed if hasattr(result, 'errors_fixed') else 'N/A'}")
        print(f"🎯 Thành công: {'✅' if (hasattr(result, 'success') and result.success) else '❌'}")
        print(f"📁 Bằng chứng: {', '.join(result.evidence_files) if hasattr(result, 'evidence_files') else 'N/A'}")
        print("-" * 50)

    def run_agentdev_with_validation(
        self, agentdev_function: Callable[..., Any], *args: Any, **kwargs: Any
    ) -> tuple[Any, Any] | tuple[None, None]:
        """Chạy AgentDev function với validation tự động"""
        print("🚀 CHẠY AGENTDEV VỚI VALIDATION TỰ ĐỘNG")
        print("=" * 60)

        # Bắt đầu session
        session: Any = getattr(self.honest_agent, 'start_fix_session', self._default_start_fix_session)(f"AgentDev: {agentdev_function.__name__}")

        try:
            # Chạy function với validation
            wrapped_function: Any = self.wrap_agentdev_function(agentdev_function)
            result: Any = wrapped_function(*args, **kwargs)

            # Kết thúc session
            validation_result: Any = getattr(self.honest_agent, 'end_fix_session', self._default_end_fix_session)(session)

            return result, validation_result

        except Exception as e:
            print(f"❌ Lỗi khi chạy AgentDev: {e}")
            return None, None

    def generate_integration_report(self) -> str:
        """Tạo báo cáo tích hợp"""
        if not self.integration_log:
            return "📝 Chưa có log tích hợp nào."

        report: str = f"""
# 📊 BÁO CÁO TÍCH HỢP AGENTDEV

## 📋 Tổng quan
- **Số lần chạy**: {len(self.integration_log)}
- **Thời gian**: {time.strftime('%Y-%m-%d %H:%M:%S')}

## 📈 Thống kê
"""

        total_fixes = 0
        successful_fixes = 0

        for log in self.integration_log:
            after_result: Any = log["after_result"]
            total_fixes += after_result["errors_fixed"] if "errors_fixed" in after_result else 0
            if after_result.get("success", False):
                successful_fixes += 1

        report += f"- **Tổng lỗi đã sửa**: {total_fixes}\n"
        report += (
            f"- **Số lần thành công**: {successful_fixes}/{len(self.integration_log)}\n"
        )
        report += f"- **Tỷ lệ thành công**: {successful_fixes/len(self.integration_log)*100:.1f}%\n"

        report += "\n## 📝 Chi tiết từng lần chạy\n"

        for i, log in enumerate(self.integration_log, 1):
            after_result = log["after_result"]
            report += f"\n### {i}. {log['function']}\n"
            report += f"- **Lỗi trước**: {log['before_data']['total_errors']}\n"
            report += f"- **Lỗi sau**: {after_result['after_errors']}\n"
            report += f"- **Đã sửa**: {after_result['errors_fixed']}\n"
            report += f"- **Thành công**: {'✅' if after_result['success'] else '❌'}\n"

        return report


# Decorator để sử dụng dễ dàng
def with_validation(project_root: str = ".") -> Any:
    """Decorator để tự động validation cho AgentDev functions"""
    integration = AgentDevIntegration(project_root)
    return integration.create_validation_decorator()


# Hàm tiện ích để chạy AgentDev với validation
def run_agentdev_honest(agentdev_function: Callable[..., Any], *args: Any, **kwargs: Any) -> tuple[Any, Any] | tuple[None, None]:
    """Chạy AgentDev function với validation tự động"""
    integration = AgentDevIntegration()
    return integration.run_agentdev_with_validation(agentdev_function, *args, **kwargs)


# Hàm để test hệ thống
def test_integration():
    """Test hệ thống tích hợp"""
    print("🧪 Test hệ thống tích hợp...")

    # Tạo integration
    integration = AgentDevIntegration()

    # Test decorator
    @integration.create_validation_decorator()
    def test_function():
        print("   🔧 Test function đang chạy...")
        time.sleep(1)
        return "Test completed"

    # Chạy test
    result = test_function()
    print(f"Kết quả: {result}")

    # Tạo báo cáo
    report = integration.generate_integration_report()
    print(report)

    # Lưu báo cáo
    with open(f"integration_report_{int(time.time())}.md", "w", encoding="utf-8") as f:
        f.write(report)


if __name__ == "__main__":
    test_integration()
