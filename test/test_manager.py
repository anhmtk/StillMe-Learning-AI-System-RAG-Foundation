import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from stillme_core.modules.api_provider_manager import UnifiedAPIManager

# Danh sách API key giả định để test (thay bằng thật nếu cần)
TEST_API_KEYS = [
    "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",
    "your_api_key_2",
]


def verify_api_key():
    return bool(TEST_API_KEYS)


def run_test_cases(manager):
    prompt = "Hãy viết một đoạn thơ về mùa thu."
    try:
        result = manager.call_api(prompt)
        print("\n✅ Kết quả phản hồi:")
        print(result)
    except Exception as e:
        print(f"\n❌ Lỗi khi gọi API: {e!s}")


if __name__ == "__main__":
    if not verify_api_key():
        print("❗ Vui lòng cấu hình TEST_API_KEYS trước")
    else:
        try:
            manager = UnifiedAPIManager(
                model_preferences=["gpt-3.5-turbo", "claude-3-haiku"]
            )

            print("\n🟢 Đã khởi tạo thành công UnifiedAPIManager")
            run_test_cases(manager)

        except Exception as e:
            print(f"\n❌ Lỗi khởi tạo: {e!s}")
