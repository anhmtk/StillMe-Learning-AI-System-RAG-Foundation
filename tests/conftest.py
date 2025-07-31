# tests/conftest.py (Đã sửa đổi)
import sys
import asyncio
import pytest
import os
import json 
from unittest.mock import AsyncMock, patch

# Import các thành phần từ module chính.
import modules.ethical_core_system_v1 as ecs 

# Dùng WindowsSelectorEventLoopPolicy cho Windows
if sys.platform.startswith("win"):
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())


#@pytest.fixture(scope="session")
#def event_loop():
 #  """Dùng 1 event loop duy nhất cho toàn bộ test session."""
 #  loop = asyncio.new_event_loop()
 #  yield loop
 #  loop.close()

# --- Fixtures Mock OpenRouterClient ---

@pytest.fixture(scope="module") # <--- THAY ĐỔI scope thành "module"
def mock_openrouter_client_for_tests():
    mock_client = AsyncMock(spec=ecs.OpenRouterClient)
    # ... (giữ nguyên side_effect và các phần còn lại) ...
    mock_client.chat_completion.side_effect = [
        json.dumps({
            "is_toxic": False, "toxicity_score": 0.0,
            "is_hate_speech": False, "hate_speech_score": 0.0,
            "sensitive_topics_detected": [], "reason": "An toàn."
        }),
        json.dumps({"sentiment": "trung lập", "tone": "thân thiện"}),
        json.dumps({"is_vulnerable": False, "reason": "Không có dấu hiệu."}),
        json.dumps({
            "is_compliant": True, "compliance_score": 1.0,
            "reason": "Hoàn toàn phù hợp với đạo đức."
        }),
        "Phản hồi đã điều chỉnh an toàn.",
        json.dumps({"root_cause": "N/A", "suggested_action": "N/A"}),
        json.dumps({
            "is_toxic": False, "toxicity_score": 0.0,
            "is_hate_speech": False, "hate_speech_score": 0.0,
            "sensitive_topics_detected": [], "reason": "An toàn."
        }),
        json.dumps({"sentiment": "trung lập", "tone": "thân thiện"}),
        json.dumps({"is_vulnerable": False, "reason": "Không có dấu hiệu."}),
        json.dumps({
            "is_compliant": True, "compliance_score": 1.0,
            "reason": "Hoàn toàn phù hợp với đạo đức."
        }),
        "Phản hồi đã điều chỉnh an toàn.",
        json.dumps({"root_cause": "N/A", "suggested_action": "N/A"})
    ]
    yield mock_client
    mock_client.chat_completion.side_effect = None
    mock_client.chat_completion.reset_mock()


@pytest.fixture(scope="module")
async def ethical_system_instance_global(mock_openrouter_client_for_tests):
    """
    Fixture để khởi tạo EthicalCoreSystem và đảm bảo nó sử dụng mock client.
    Scope "module" để khởi tạo một lần cho tất cả các test trong module.
    Đồng thời quản lý việc dọn dẹp file log và thư mục log/config cho toàn bộ test session.
    """
    os.makedirs("logs", exist_ok=True)
    os.makedirs("config", exist_ok=True)
    
    os.environ["OPENROUTER_API_KEY"] = "dummy_key_for_test"

    system = None 
    with patch('modules.ethical_core_system_v1.OpenRouterClient', new=mock_openrouter_client_for_tests):
        try:
            ecs.close_violation_logger() 
            if os.path.exists(ecs.ETHICAL_VIOLATIONS_LOG):
                os.remove(ecs.ETHICAL_VIOLATIONS_LOG)
            
            system = ecs.EthicalCoreSystem() 
            with open("config/ethical_rules.json", "w", encoding='utf-8') as f:
                json.dump({"forbidden_keywords": ["test_cấm"], "sensitive_topics": ["test_nhạy_cảm"]}, f, indent=2, ensure_ascii=False)
            
            yield system 
            
        finally:
            if system:
                await system.close() 
            
            ecs.close_violation_logger()
            print("\n--- Đã đóng violation logger sau khi chạy tất cả test module ---")
            
            if os.path.exists(ecs.ETHICAL_VIOLATIONS_LOG):
                os.remove(ecs.ETHICAL_VIOLATIONS_LOG)
            if os.path.exists("config/ethical_rules.json"):
                os.remove("config/ethical_rules.json")
            if os.path.exists("logs") and not os.listdir("logs"): 
                os.rmdir("logs")
            if os.path.exists("config") and not os.listdir("config"):
                os.rmdir("config")
            
            del os.environ["OPENROUTER_API_KEY"]


@pytest.fixture(scope="function")
async def ethical_system_instance_per_test(mock_openrouter_client_for_tests):
    """
    Fixture để khởi tạo EthicalCoreSystem và đảm bảo nó sử dụng mock client.
    Scope "function" để khởi tạo một instance mới cho mỗi test function.
    """
    os.makedirs("logs", exist_ok=True)
    os.makedirs("config", exist_ok=True)

    ecs.close_violation_logger()
    if os.path.exists(ecs.ETHICAL_VIOLATIONS_LOG):
        os.remove(ecs.ETHICAL_VIOLATIONS_LOG)

    with patch('modules.ethical_core_system_v1.OpenRouterClient', new=mock_openrouter_client_for_tests):
        os.environ["OPENROUTER_API_KEY"] = "dummy_key_for_test"
        system = ecs.EthicalCoreSystem()
        with open("config/ethical_rules.json", "w", encoding='utf-8') as f:
            json.dump({"forbidden_keywords": ["test_cấm_per_test"], "sensitive_topics": ["test_nhạy_cảm_per_test"]}, f, indent=2, ensure_ascii=False)

        yield system
        await system.close() 
        del os.environ["OPENROUTER_API_KEY"]

        if os.path.exists(ecs.ETHICAL_VIOLATIONS_LOG):
            os.remove(ecs.ETHICAL_VIOLATIONS_LOG)
        if os.path.exists("config/ethical_rules.json"):
            os.remove("config/ethical_rules.json")
        if os.path.exists("logs") and not os.listdir("logs"):
            os.rmdir("logs")
        if os.path.exists("config") and not os.listdir("config"):
            os.rmdir("config")


@pytest.fixture(scope="function")
def mock_ethical_core_system_old(mock_openrouter_client_for_tests):
    ecs_system = ecs.EthicalCoreSystem()
    ecs_system.openrouter_client = mock_openrouter_client_for_tests
    ecs_system.ethics_guard = ecs.EthicsGuard(openrouter_client=mock_openrouter_client_for_tests)
    ecs_system.conscience_core = ecs.ConscienceCore(openrouter_client=mock_openrouter_client_for_tests)
    ecs_system.self_critic = ecs.SelfCritic(openrouter_client=mock_openrouter_client_for_tests)
    return ecs_system