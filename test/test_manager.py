import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from modules.smart_gpt_api_manager_v1 import SmartGPTAPIManager
# Danh sách API key giả định để test (thay bằng thật nếu cần)
TEST_API_KEYS = [
    "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",
    "your_api_key_2"
]

def verify_api_key():
    return bool(TEST_API_KEYS)

def run_test_cases(manager):
    messages = [
        {"role": "user", "content": "Hãy viết một đoạn thơ về mùa thu."}
    ]
    try:
        result = manager.call_api(messages)
        print("\n✅ Kết quả phản hồi:")
        print(result['choices'][0]['message']['content'])
    except Exception as e:
        print(f"\n❌ Lỗi khi gọi API: {str(e)}")

if __name__ == "__main__":
    if not verify_api_key():
        print("❗ Vui lòng cấu hình TEST_API_KEYS trước")
    else:
        try:
            manager = SmartGPTAPIManager(
                api_keys=TEST_API_KEYS,
                models_config={
                    "openai/gpt-3.5-turbo": {"max_tokens": 4000},
                    "anthropic/claude-3-haiku": {"max_tokens": 150000}
                }
            )

            print("\n🟢 Đã khởi tạo thành công SmartGPTAPIManager")
            run_test_cases(manager)

        except Exception as e:
            print(f"\n❌ Lỗi khởi tạo: {str(e)}")
