#!/usr/bin/env python3
"""
Test Validation System - Script test đơn giản cho hệ thống validation
"""

import os
import sys
import time

# Add current directory to path
sys.path.insert(
    0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)

from agentdev_validation_system import AgentDevValidator


def main():
    """Test hệ thống validation"""
    print("🧪 TEST HỆ THỐNG VALIDATION")
    print("=" * 50)

    # Tạo validator
    validator = AgentDevValidator()

    # Test validation trước
    print("📋 Test validation trước khi sửa...")
    before_data = validator.validate_before_fix()

    print("📊 Kết quả:")
    print(f"   🔢 Pyright errors: {before_data['pyright_errors']}")
    print(f"   🔢 Ruff errors: {before_data['ruff_errors']}")
    print(f"   🔢 Total errors: {before_data['total_errors']}")
    print(f"   🧪 Test passed: {'✅' if before_data['test_passed'] else '❌'}")

    # Giả lập sửa lỗi
    print("\n⏳ Giả lập sửa lỗi...")
    time.sleep(2)

    # Test validation sau
    print("📋 Test validation sau khi sửa...")
    result = validator.validate_after_fix(before_data)

    print("\n📊 Kết quả cuối cùng:")
    print(f"   🔢 Lỗi trước: {result.before_errors}")
    print(f"   🔢 Lỗi sau: {result.after_errors}")
    print(f"   ✅ Đã sửa: {result.errors_fixed}")
    print(f"   🚨 Lỗi nghiêm trọng: {result.critical_errors}")
    print(f"   ⚠️  Cảnh báo: {result.warnings}")
    print(f"   💡 Gợi ý style: {result.style_suggestions}")
    print(f"   🎯 Thành công: {'✅' if result.success else '❌'}")

    # Tạo báo cáo
    report = validator.generate_report(result)
    print("\n📄 Báo cáo:")
    print(report)

    print("\n🎉 Test hoàn tất!")


if __name__ == "__main__":
    main()
