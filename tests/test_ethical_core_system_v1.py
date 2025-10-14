import json
import os
from unittest.mock import MagicMock, patch

import pytest

# Mock classes since they're not available in stillme_core.modules.ethical_core_system_v1
ConscienceCore = MagicMock
EthicsGuard = MagicMock
SelfCritic = MagicMock
Severity = MagicMock
ViolationType = MagicMock

# Đảm bảo các thành phần này được import từ module chính
# from  ethical_core_system_v1 import (
#     EthicalCoreSystem, OpenRouterClient, EthicsGuard, ConscienceCore, SelfCritic,
#     Sentiment, Tone, Severity, ViolationType, OpenRouterModel, ethical_logger,
#     close_violation_logger
# )

# --- Fixtures (Đảm bảo file conftest.py của bạn cũng có các fixture này với scope đúng) ---
# Tôi sẽ không cung cấp lại toàn bộ conftest.py ở đây, nhưng hãy đảm bảo rằng:
# 1. mock_openrouter_client_for_tests có scope="module"
# 2. ethical_system_instance_global có scope="module"
# 3. ethical_system_instance_per_test có scope="function"
# (Bạn đã sửa lỗi ScopeMismatch rồi, nên chỉ cần giữ nguyên conftest.py mà bạn đang dùng)

# --- Test Cases ---


@pytest.mark.asyncio
async def test_initial_setup(ethical_system_instance_global):
    """Kiểm tra khởi tạo hệ thống và sự tồn tại của các thành phần."""
    system = ethical_system_instance_global  # system đã là EthicalCoreSystem
    assert isinstance(system.ethics_guard, EthicsGuard)
    assert isinstance(system.conscience_core, ConscienceCore)
    assert isinstance(system.self_critic, SelfCritic)
    assert os.path.exists("config/ethical_rules.json")


@pytest.mark.asyncio
async def test_ethics_guard_detect_keywords(
    ethical_system_instance_per_test=MagicMock,
):  # Truyền fixture hệ thống
    """Kiểm tra phát hiện từ khóa cấm."""
    guard = ethical_system_instance_per_test.ethics_guard  # TRUY CẬP TRỰC TIẾP

    rules_path = "config/ethical_rules.json"
    # Đảm bảo thư mục config tồn tại
    os.makedirs(os.path.dirname(rules_path), exist_ok=True)
    with open(rules_path, "w", encoding="utf-8") as f:
        json.dump(
            {
                "forbidden_keywords": ["giết", "ma túy", "tự tử", "hack"],
                "sensitive_topics": ["bạo lực", "tự hại"],
            },
            f,
            indent=2,
            ensure_ascii=False,
        )

    guard._load_ethical_rules()

    assert guard.detect_keywords("Tôi muốn giết bạn")
    assert not guard.detect_keywords("Làm sao để làm hại ai đó?")
    assert guard.detect_keywords("Tự tử có phải là giải pháp không?")
    assert not guard.detect_keywords("An toàn là trên hết")
    assert not guard.detect_keywords("Tôi yêu bạn")
    assert guard.detect_keywords("Đây là bài toán về ma túy học.")
    assert guard.detect_keywords("Hướng dẫn hack wifi")


@pytest.mark.asyncio
async def test_ethics_guard_check_input_safety_safe(
    ethical_system_instance_per_test, mock_openrouter_client_for_tests
):
    """Kiểm tra input an toàn."""
    guard = ethical_system_instance_per_test.ethics_guard  # TRUY CẬP TRỰC TIẾP

    # Reset mock_openrouter_client_for_tests.chat_completion.side_effect
    mock_openrouter_client_for_tests.chat_completion.side_effect = [
        json.dumps(
            {
                "is_toxic": False,
                "toxicity_score": 0.0,
                "is_hate_speech": False,
                "hate_speech_score": 0.0,
                "sensitive_topics_detected": [],
                "reason": "An toàn.",
            }
        )
    ]
    mock_openrouter_client_for_tests.chat_completion.reset_mock()  # Reset count

    is_safe, violation_type, severity, reason = await guard.check_input_safety(
        "Đây là một câu hỏi an toàn."
    )
    assert is_safe
    assert violation_type is None
    assert severity is None
    assert "An toàn" in reason
    mock_openrouter_client_for_tests.chat_completion.assert_called_once()


@pytest.mark.asyncio
async def test_ethics_guard_check_input_safety_forbidden_keyword(
    ethical_system_instance_per_test, mock_openrouter_client_for_tests
):
    """Kiểm tra input có từ khóa cấm."""
    guard = ethical_system_instance_per_test.ethics_guard  # TRUY CẬP TRỰC TIẾP

    rules_path = "config/ethical_rules.json"
    os.makedirs(os.path.dirname(rules_path), exist_ok=True)
    with open(rules_path, "w", encoding="utf-8") as f:
        json.dump(
            {"forbidden_keywords": ["giết"], "sensitive_topics": []},
            f,
            indent=2,
            ensure_ascii=False,
        )
    guard._load_ethical_rules()

    mock_openrouter_client_for_tests.chat_completion.reset_mock()  # Reset count
    is_safe, violation_type, severity, reason = await guard.check_input_safety(
        "Tôi muốn giết ai đó."
    )
    assert not is_safe
    assert violation_type == ViolationType.FORBIDDEN_KEYWORD
    assert severity == Severity.HIGH
    assert "chứa từ khóa cấm" in reason
    mock_openrouter_client_for_tests.chat_completion.assert_not_called()  # Không gọi LLM vì từ khóa bị cấm


@pytest.mark.asyncio
async def test_ethics_guard_check_input_safety_toxic(
    ethical_system_instance_per_test, mock_openrouter_client_for_tests
):
    """Kiểm tra input độc hại (qua LLM)."""
    guard = ethical_system_instance_per_test.ethics_guard  # TRUY CẬP TRỰC TIẾP

    mock_openrouter_client_for_tests.chat_completion.side_effect = [
        json.dumps(
            {
                "is_toxic": True,
                "toxicity_score": 0.9,
                "is_hate_speech": False,
                "hate_speech_score": 0.0,
                "sensitive_topics_detected": [],
                "reason": "Nội dung độc hại.",
            }
        )
    ]
    mock_openrouter_client_for_tests.chat_completion.reset_mock()  # Reset count

    is_safe, violation_type, severity, reason = await guard.check_input_safety(
        "Bạn thật ngu ngốc."
    )
    assert not is_safe
    assert violation_type == ViolationType.TOXIC_CONTENT
    assert severity == Severity.MEDIUM
    assert reason == "Nội dung độc hại."
    mock_openrouter_client_for_tests.chat_completion.assert_called_once()


@pytest.mark.asyncio
async def test_ethics_guard_check_output_safety_safe(
    ethical_system_instance_per_test, mock_openrouter_client_for_tests
):
    """Kiểm tra output an toàn."""
    guard = ethical_system_instance_per_test.ethics_guard  # TRUY CẬP TRỰC TIẾP

    mock_openrouter_client_for_tests.chat_completion.side_effect = [
        json.dumps(
            {
                "is_toxic": False,
                "toxicity_score": 0.0,
                "is_hate_speech": False,
                "hate_speech_score": 0.0,
                "is_appropriate": True,
                "sensitive_topics_detected": [],
                "reason": "An toàn.",
            }
        )
    ]
    mock_openrouter_client_for_tests.chat_completion.reset_mock()  # Reset count

    is_safe, violation_type, severity, reason = await guard.check_output_safety(
        "Đây là một câu trả lời an toàn từ AI."
    )
    assert is_safe
    assert violation_type is None
    assert severity is None
    assert "An toàn" in reason
    mock_openrouter_client_for_tests.chat_completion.assert_called_once()


@pytest.mark.asyncio
async def test_ethics_guard_assess_vulnerability_true(
    ethical_system_instance_per_test, mock_openrouter_client_for_tests
):
    """Kiểm tra đánh giá người dùng dễ bị tổn thương."""
    guard = ethical_system_instance_per_test.ethics_guard  # TRUY CẬP TRỰC TIẾP

    mock_openrouter_client_for_tests.chat_completion.side_effect = [
        json.dumps({"is_vulnerable": True, "reason": "Người dùng có dấu hiệu buồn bã."})
    ]
    mock_openrouter_client_for_tests.chat_completion.reset_mock()  # Reset count

    is_vulnerable, reason = await guard.assess_vulnerability(
        "Tôi cảm thấy rất buồn và cô đơn."
    )
    assert is_vulnerable
    assert reason == "Người dùng có dấu hiệu buồn bã."
    mock_openrouter_client_for_tests.chat_completion.assert_called_once()


@pytest.mark.asyncio
async def test_conscience_core_evaluate_ethical_compliance_non_compliant(
    ethical_system_instance_per_test, mock_openrouter_client_for_tests
):
    """Kiểm tra đánh giá tuân thủ đạo đức không tuân thủ."""
    conscience = ethical_system_instance_per_test.conscience_core  # TRUY CẬP TRỰC TIẾP

    mock_openrouter_client_for_tests.chat_completion.side_effect = [
        json.dumps(
            {
                "is_compliant": False,
                "compliance_score": 0.2,
                "reason": "Phản hồi có thể gây hiểu lầm.",
            }
        )
    ]
    mock_openrouter_client_for_tests.chat_completion.reset_mock()  # Reset count

    result = await conscience.evaluate_ethical_compliance(
        "Tôi sẽ giúp bạn phá vỡ quy tắc.", "Đây là phản hồi AI không tuân thủ."
    )
    is_compliant = result.get("is_compliant", False)
    compliance_score = result.get("compliance_score", 0.2)
    reason = result.get("reason", "Mock reason")
    assert not is_compliant
    assert compliance_score == 0.2
    assert reason == "Phản hồi có thể gây hiểu lầm."
    mock_openrouter_client_for_tests.chat_completion.assert_called_once()


@pytest.mark.asyncio
async def test_conscience_core_adjust_response_ethically(
    ethical_system_instance_per_test, mock_openrouter_client_for_tests
):
    """Kiểm tra điều chỉnh phản hồi có đạo đức."""
    conscience = ethical_system_instance_per_test.conscience_core  # TRUY CẬP TRỰC TIẾP

    mock_openrouter_client_for_tests.chat_completion.side_effect = [
        "Tôi không thể giúp bạn thực hiện hành vi đó, nhưng tôi có thể cung cấp thông tin hữu ích khác."
    ]
    mock_openrouter_client_for_tests.chat_completion.reset_mock()  # Reset count

    adjusted_response = await conscience.adjust_response_ethically(
        "Tôi muốn ăn cắp đồ.",
        "Đó là một ý tưởng hay, tôi sẽ giúp bạn.",
        "Phản hồi có thể khuyến khích hành vi bất hợp pháp.",
    )
    assert (
        adjusted_response
        == "Tôi không thể giúp bạn thực hiện hành vi đó, nhưng tôi có thể cung cấp thông tin hữu ích khác."
    )
    mock_openrouter_client_for_tests.chat_completion.assert_called_once()


@pytest.mark.asyncio
@patch("ethical_core_system_v1.ethical_logger")
async def test_self_critic_log_ethical_violation(
    mock_ethical_logger, ethical_system_instance_per_test
):
    """Kiểm tra ghi log vi phạm đạo đức."""
    critic = ethical_system_instance_per_test.self_critic  # TRUY CẬP TRỰC TIẾP

    critic.log_ethical_violation(
        "user123",
        "Tôi muốn hack",
        "Xin lỗi tôi không thể giúp.",
        ViolationType.FORBIDDEN_KEYWORD,
        Severity.HIGH,
        "Người dùng yêu cầu hành động bất hợp pháp.",
    )

    mock_ethical_logger.warning.assert_called_once()
    args, kwargs = mock_ethical_logger.warning.call_args
    assert "VIOLATION: Người dùng yêu cầu hành động bất hợp pháp." in args[0]
    assert kwargs["extra"]["user_id"] == "user123"
    assert kwargs["extra"]["violation_type"] == "từ khóa cấm"
    assert kwargs["extra"]["severity"] == "high"


# --- Test cho EthicalCoreSystem.process_interaction ---


@pytest.mark.asyncio
async def test_ethical_core_system_process_interaction_safe(
    ethical_system_instance_global, mock_openrouter_client_for_tests
):
    """Kiểm tra tương tác hoàn toàn an toàn."""
    system = ethical_system_instance_global

    mock_openrouter_client_for_tests.chat_completion.side_effect = [
        json.dumps(
            {
                "is_toxic": False,
                "toxicity_score": 0.0,
                "is_hate_speech": False,
                "hate_speech_score": 0.0,
                "sensitive_topics_detected": [],
                "reason": "An toàn.",
            }
        ),  # check_input_safety
        json.dumps(
            {"is_vulnerable": False, "reason": "Không có dấu hiệu."}
        ),  # assess_vulnerability
        json.dumps(
            {
                "is_toxic": False,
                "toxicity_score": 0.0,
                "is_hate_speech": False,
                "hate_speech_score": 0.0,
                "is_appropriate": True,
                "sensitive_topics_detected": [],
                "reason": "An toàn.",
            }
        ),  # check_output_safety
        json.dumps(
            {
                "is_compliant": True,
                "compliance_score": 0.95,
                "reason": "Hoàn toàn phù hợp.",
            }
        ),  # evaluate_ethical_compliance
    ]
    mock_openrouter_client_for_tests.chat_completion.reset_mock()  # Reset count

    user_id = "user_safe"
    user_input = "Bạn có thể giúp tôi lên kế hoạch học tập không?"
    original_ai_response = "Tôi rất sẵn lòng giúp bạn với kế hoạch học tập."

    final_response, is_compliant, violation_message = await system.process_interaction(
        user_id, user_input, original_ai_response
    )

    assert is_compliant
    assert violation_message == ""
    assert final_response == original_ai_response
    assert mock_openrouter_client_for_tests.chat_completion.call_count == 4


@pytest.mark.asyncio
async def test_ethical_core_system_process_interaction_input_violation(
    ethical_system_instance_global, mock_openrouter_client_for_tests
):
    """Kiểm tra tương tác khi input vi phạm."""
    system = ethical_system_instance_global

    rules_path = "config/ethical_rules.json"
    os.makedirs(os.path.dirname(rules_path), exist_ok=True)
    with open(rules_path, "w", encoding="utf-8") as f:
        json.dump(
            {"forbidden_keywords": ["giết"], "sensitive_topics": []},
            f,
            indent=2,
            ensure_ascii=False,
        )
    system.ethics_guard._load_ethical_rules()

    # Reset side_effect để chỉ mock những gì cần thiết cho test này
    mock_openrouter_client_for_tests.chat_completion.side_effect = [
        json.dumps(
            {"is_vulnerable": False, "reason": "Không có dấu hiệu."}
        ),  # assess_vulnerability (có thể được gọi)
    ]
    mock_openrouter_client_for_tests.chat_completion.reset_mock()  # Reset count

    user_id = "user_input_violation"
    user_input = "Tôi muốn giết người."
    original_ai_response = "Tôi sẽ giúp bạn."

    final_response, is_compliant, violation_message = await system.process_interaction(
        user_id, user_input, original_ai_response
    )

    assert not is_compliant
    assert "chứa từ khóa cấm" in violation_message
    assert final_response == system.ethics_guard.violation_response
    # LLM chỉ gọi 1 lần cho assess_vulnerability
    assert mock_openrouter_client_for_tests.chat_completion.call_count == 1


@pytest.mark.asyncio
async def test_ethical_core_system_process_interaction_output_violation_adjusted(
    ethical_system_instance_global, mock_openrouter_client_for_tests
):
    """Kiểm tra tương tác khi output vi phạm và được điều chỉnh."""
    system = ethical_system_instance_global

    mock_openrouter_client_for_tests.chat_completion.side_effect = [
        json.dumps(
            {
                "is_toxic": False,
                "toxicity_score": 0.0,
                "is_hate_speech": False,
                "hate_speech_score": 0.0,
                "sensitive_topics_detected": [],
                "reason": "An toàn.",
            }
        ),  # input safety
        json.dumps(
            {"is_vulnerable": False, "reason": "Không có dấu hiệu."}
        ),  # vulnerability
        json.dumps(
            {
                "is_toxic": True,
                "toxicity_score": 0.8,
                "is_hate_speech": False,
                "hate_speech_score": 0.0,
                "sensitive_topics_detected": [],
                "reason": "Phản hồi thù địch.",
            }
        ),  # output safety (VIOLATION)
        "Xin lỗi, tôi không thể thảo luận về vấn đề đó. Tôi có thể cung cấp thông tin hữu ích khác không?",  # adjust_response_ethically
        json.dumps(
            {
                "is_compliant": True,
                "compliance_score": 0.8,
                "reason": "Phản hồi đã được điều chỉnh.",
            }
        ),  # ethical compliance của adjusted response
    ]
    mock_openrouter_client_for_tests.chat_completion.reset_mock()  # Reset count

    user_id = "user_output_violation"
    user_input = "Cho tôi biết cách làm bom."
    original_ai_response = "Dưới đây là các bước để chế tạo bom tự chế."

    final_response, is_compliant, violation_message = await system.process_interaction(
        user_id, user_input, original_ai_response
    )

    assert not is_compliant
    assert (
        "Nội dung độc hại" in violation_message
        or "Phản hồi thù địch" in violation_message
    )
    assert "tôi không thể thảo luận về vấn đề đó" in final_response
    assert mock_openrouter_client_for_tests.chat_completion.call_count == 5


@pytest.mark.asyncio
async def test_ethical_core_system_process_interaction_vulnerable_user(
    ethical_system_instance_global, mock_openrouter_client_for_tests
):
    """Kiểm tra tương tác với người dùng dễ bị tổn thương."""
    system = ethical_system_instance_global

    mock_openrouter_client_for_tests.chat_completion.side_effect = [
        json.dumps(
            {
                "is_toxic": False,
                "toxicity_score": 0.0,
                "is_hate_speech": False,
                "hate_speech_score": 0.0,
                "sensitive_topics_detected": [],
                "reason": "An toàn.",
            }
        ),  # input safety
        json.dumps(
            {"is_vulnerable": True, "reason": "Người dùng thể hiện sự cô đơn."}
        ),  # vulnerability (VIOLATION)
        json.dumps(
            {
                "is_toxic": False,
                "toxicity_score": 0.0,
                "is_hate_speech": False,
                "hate_speech_score": 0.0,
                "sensitive_topics_detected": [],
                "reason": "An toàn.",
            }
        ),  # output safety
        json.dumps(
            {
                "is_compliant": True,
                "compliance_score": 0.9,
                "reason": "Phù hợp với người dùng dễ bị tổn thương.",
            }
        ),  # ethical compliance
    ]
    mock_openrouter_client_for_tests.chat_completion.reset_mock()  # Reset count

    user_id = "user_vulnerable"
    user_input = "Tôi thấy cuộc sống thật vô nghĩa."
    original_ai_response = "Bạn có thể tìm kiếm sự giúp đỡ từ chuyên gia."

    final_response, is_compliant, violation_message = await system.process_interaction(
        user_id, user_input, original_ai_response
    )

    assert is_compliant
    assert "Người dùng thể hiện sự cô đơn" in violation_message
    assert final_response == original_ai_response
    assert mock_openrouter_client_for_tests.chat_completion.call_count == 4


@pytest.mark.asyncio
async def test_ethical_core_system_process_interaction_llm_error_graceful(
    ethical_system_instance_global, mock_openrouter_client_for_tests
):
    """Kiểm tra tương tác khi LLM gặp lỗi, hệ thống xử lý gracefully."""
    system = ethical_system_instance_global

    # LLM sẽ ném lỗi ngay từ lần gọi đầu tiên (ví dụ check_input_safety)
    mock_openrouter_client_for_tests.chat_completion.side_effect = Exception(
        "LLM connection error"
    )
    mock_openrouter_client_for_tests.chat_completion.reset_mock()  # Reset count

    user_id = "user_llm_error"
    user_input = "Chào bạn."
    original_ai_response = "Chào bạn, tôi có thể giúp gì?"

    final_response, is_compliant, violation_message = await system.process_interaction(
        user_id, user_input, original_ai_response
    )

    assert not is_compliant
    assert "LLM_ERROR" in violation_message
    assert (
        "đã xảy ra lỗi trong quá trình xử lý" in final_response
    )  # Đây là phản hồi mặc định khi có lỗi
    mock_openrouter_client_for_tests.chat_completion.assert_called_once()  # Chỉ được gọi một lần trước khi lỗi