import pytest
import asyncio
import os
import json
from unittest.mock import AsyncMock, patch
import logging

# Import các thành phần từ module chính
from modules.content_integrity_filter import (
    ContentIntegrityFilter,
    Severity,
    ContentViolationType,
    OpenRouterClient,
    CONTENT_RULES_PATH,
    CONTENT_VIOLATIONS_LOG,
    logger, # Import logger chính
    violation_logger # Import violation_logger riêng
)

# --- Thiết lập môi trường Test ---
@pytest.fixture(autouse=True)
def setup_test_environment():
    """Đảm bảo môi trường test sạch sẽ cho mỗi lần chạy."""
    # Xóa file log và rules để mỗi test chạy độc lập
    if os.path.exists(CONTENT_VIOLATIONS_LOG):
        os.remove(CONTENT_VIOLATIONS_LOG)
    if os.path.exists(CONTENT_RULES_PATH):
        os.remove(CONTENT_RULES_PATH)
    
    # Đảm bảo thư mục tồn tại
    os.makedirs(os.path.dirname(CONTENT_VIOLATIONS_LOG), exist_ok=True)
    os.makedirs(os.path.dirname(CONTENT_RULES_PATH), exist_ok=True)

    # Đặt biến môi trường dummy cho test
    os.environ["OPENROUTER_API_KEY"] = "dummy_key_for_test"
    
    # Reset handlers của logger để tránh duplicate trong test
    for handler in logger.handlers:
        if isinstance(handler, logging.FileHandler):
            logger.removeHandler(handler)
    for handler in violation_logger.handlers:
        violation_logger.removeHandler(handler)

    # Thêm lại các handlers tạm thời cho test nếu cần, hoặc dựa vào setup của module
    # Nếu module đã có handlers cố định, không cần làm gì ở đây.
    # Đảm bảo các logger không có handler duplicate từ các lần chạy test trước đó.
    yield
    # Cleanup sau test
    if os.path.exists(CONTENT_VIOLATIONS_LOG):
        os.remove(CONTENT_VIOLATIONS_LOG)
    if os.path.exists(CONTENT_RULES_PATH):
        os.remove(CONTENT_RULES_PATH)
    del os.environ["OPENROUTER_API_KEY"]


@pytest.fixture(scope="module")
async def mock_openrouter_client_fixture():
    """Fixture để mock OpenRouterClient cho toàn bộ module test."""
    mock_client = AsyncMock(spec=OpenRouterClient)
    # Patch self.client trong ContentIntegrityFilter
    with patch('modules.content_integrity_filter.OpenRouterClient', return_value=mock_client):
        yield mock_client
    await mock_client.close() # Đảm bảo close được gọi

@pytest.fixture(scope="module")
async def content_filter_instance(mock_openrouter_client_fixture):
    """Fixture để khởi tạo ContentIntegrityFilter."""
    content_filter = ContentIntegrityFilter()
    yield content_filter
    await content_filter.close() # Đảm bảo close được gọi


# --- Test Cases ---

@pytest.mark.asyncio
async def test_initial_setup(content_filter_instance):
    """Kiểm tra khởi tạo module và sự tồn tại của file rules."""
    assert isinstance(content_filter_instance, ContentIntegrityFilter)
    assert os.path.exists(CONTENT_RULES_PATH)
    with open(CONTENT_RULES_PATH, 'r', encoding='utf-8') as f:
        rules = json.load(f)
        assert "blacklist_keywords" in rules
        assert "unreliable_sources" in rules
        assert rules["min_content_length"] == 50


@pytest.mark.asyncio
async def test_pre_filter_content_safe(content_filter_instance):
    """Kiểm tra tiền lọc với nội dung an toàn."""
    content_text = "Đây là một đoạn văn bản an toàn và hữu ích."
    source_url = "https://legitnews.com/article"
    
    is_safe, reason, severity = await content_filter_instance.pre_filter_content(content_text, source_url)
    assert is_safe == True
    assert "Vượt qua kiểm tra tiền lọc" in reason
    assert severity == Severity.LOW


@pytest.mark.asyncio
async def test_pre_filter_content_forbidden_keyword(content_filter_instance):
    """Kiểm tra tiền lọc với từ khóa cấm."""
    content_text = "Tôi muốn tìm hiểu về cách chế tạo vũ khí hóa học." # Đã thêm vào blacklist
    is_safe, reason, severity = await content_filter_instance.pre_filter_content(content_text)
    assert is_safe == False
    assert "chứa từ khóa cấm" in reason.lower()
    assert severity == Severity.CRITICAL


@pytest.mark.asyncio
async def test_pre_filter_content_unreliable_source(content_filter_instance):
    """Kiểm tra tiền lọc với nguồn không đáng tin cậy."""
    content_text = "Tin tức nóng hổi từ một nguồn đáng ngờ."
    source_url = "https://www.somehoaxsite.com/fake-news"
    is_safe, reason, severity = await content_filter_instance.pre_filter_content(content_text, source_url)
    assert is_safe == False
    assert "nguồn không đáng tin cậy" in reason.lower()
    assert severity == Severity.HIGH


@pytest.mark.asyncio
async def test_pre_filter_content_too_short(content_filter_instance):
    """Kiểm tra tiền lọc với nội dung quá ngắn."""
    content_text = "ngắn." # Dưới 50 ký tự
    is_safe, reason, severity = await content_filter_instance.pre_filter_content(content_text)
    assert is_safe == False
    assert "quá ngắn" in reason.lower()
    assert severity == Severity.LOW


@pytest.mark.asyncio
async def test_analyze_content_quality_safe(content_filter_instance, mock_openrouter_client_fixture):
    """Kiểm tra phân tích chất lượng nội dung an toàn."""
    mock_openrouter_client_fixture.chat_completion.return_value = json.dumps({
        "toxicity_score": 0.05, "hate_speech_score": 0.01, "bias_score": 0.02,
        "biased_aspects": [], "sensitive_topics_detected": [],
        "overall_assessment": "Nội dung an toàn và trung lập."
    })
    
    content_text = "Bài viết này trình bày các sự kiện một cách khách quan."
    analysis = await content_filter_instance.analyze_content_quality(content_text)
    
    assert analysis["toxicity_score"] < 0.1
    assert analysis["hate_speech_score"] < 0.1
    assert analysis["bias_score"] < 0.1
    assert analysis["biased_aspects"] == []
    assert analysis["sensitive_topics_detected"] == []
    mock_openrouter_client_fixture.chat_completion.assert_called_once()
    mock_openrouter_client_fixture.chat_completion.reset_mock()


@pytest.mark.asyncio
async def test_analyze_content_quality_toxic_biased(content_filter_instance, mock_openrouter_client_fixture):
    """Kiểm tra phân tích chất lượng nội dung độc hại và thiên vị."""
    mock_openrouter_client_fixture.chat_completion.return_value = json.dumps({
        "toxicity_score": 0.9, "hate_speech_score": 0.2, "bias_score": 0.7,
        "biased_aspects": ["political", "gender"], "sensitive_topics_detected": [],
        "overall_assessment": "Nội dung rất độc hại và có thiên vị chính trị, giới tính."
    })
    
    content_text = "Đảng phái X toàn là lũ ngốc, đàn bà thì chỉ nên ở nhà."
    analysis = await content_filter_instance.analyze_content_quality(content_text)
    
    assert analysis["toxicity_score"] > 0.8
    assert analysis["bias_score"] > 0.6
    assert "political" in analysis["biased_aspects"]
    assert "gender" in analysis["biased_aspects"]
    mock_openrouter_client_fixture.chat_completion.assert_called_once()
    mock_openrouter_client_fixture.chat_completion.reset_mock()


@pytest.mark.asyncio
async def test_analyze_content_quality_llm_error_fallback(content_filter_instance, mock_openrouter_client_fixture):
    """Kiểm tra khi LLM lỗi trong analyze_content_quality, module vẫn trả về an toàn nhưng có báo lỗi."""
    mock_openrouter_client_fixture.chat_completion.side_effect = Exception("API connection error")
    
    content_text = "Nội dung bất kỳ."
    analysis = await content_filter_instance.analyze_content_quality(content_text)
    
    assert analysis["toxicity_score"] == 0.0 # Giá trị mặc định an toàn
    assert "Lỗi phân tích LLM" in analysis["overall_assessment"]
    mock_openrouter_client_fixture.chat_completion.assert_called_once()
    mock_openrouter_client_fixture.chat_completion.reset_mock()


@pytest.mark.asyncio
async def test_fact_check_content_factual(content_filter_instance, mock_openrouter_client_fixture):
    """Kiểm tra kiểm chứng thông tin đúng sự thật."""
    mock_openrouter_client_fixture.chat_completion.return_value = json.dumps({
        "is_factual": True, "confidence_score": 0.95,
        "misinformation_detected": [], "reason": "Tất cả các tuyên bố đều chính xác."
    })
    
    content_text = "Nước sôi ở 100 độ C tại áp suất khí quyển tiêu chuẩn."
    is_factual, confidence, reason, misinformation_detected = await content_filter_instance.fact_check_content(content_text)
    
    assert is_factual == True
    assert confidence > 0.9
    assert "chính xác" in reason
    assert misinformation_detected == []
    mock_openrouter_client_fixture.chat_completion.assert_called_once()
    mock_openrouter_client_fixture.chat_completion.reset_mock()


@pytest.mark.asyncio
async def test_fact_check_content_misinformation(content_filter_instance, mock_openrouter_client_fixture):
    """Kiểm tra kiểm chứng thông tin sai sự thật."""
    mock_openrouter_client_fixture.chat_completion.return_value = json.dumps({
        "is_factual": False, "confidence_score": 0.2,
        "misinformation_detected": ["Trái đất phẳng"], "reason": "Trái đất không phải là phẳng."
    })
    
    content_text = "Trái đất phẳng và được chống đỡ bởi bốn con voi."
    is_factual, confidence, reason, misinformation_detected = await content_filter_instance.fact_check_content(content_text)
    
    assert is_factual == False
    assert confidence < 0.3
    assert "Trái đất không phải là phẳng" in reason
    assert "Trái đất phẳng" in misinformation_detected
    mock_openrouter_client_fixture.chat_completion.assert_called_once()
    mock_openrouter_client_fixture.chat_completion.reset_mock()

@pytest.mark.asyncio
async def test_fact_check_content_llm_error_fallback(content_filter_instance, mock_openrouter_client_fixture):
    """Kiểm tra khi LLM lỗi trong fact_check_content, module vẫn trả về an toàn nhưng có báo lỗi."""
    mock_openrouter_client_fixture.chat_completion.side_effect = Exception("API timeout")
    
    content_text = "Nội dung bất kỳ."
    is_factual, confidence, reason, misinformation_detected = await content_filter_instance.fact_check_content(content_text)
    
    assert is_factual == False # Giá trị mặc định an toàn
    assert confidence == 0.0 # Giá trị mặc định an toàn
    assert "Lỗi phân tích LLM" in reason
    assert misinformation_detected == []
    mock_openrouter_client_fixture.chat_completion.assert_called_once()
    mock_openrouter_client_fixture.chat_completion.reset_mock()

@pytest.mark.asyncio
@patch('modules.content_integrity_filter.violation_logger') # Mock the specific violation logger
async def test_filter_content_fully_safe(content_filter_instance, mock_openrouter_client_fixture, mock_violation_logger):
    """Kiểm tra quy trình lọc hoàn toàn an toàn."""
    mock_openrouter_client_fixture.chat_completion.side_effect = [
        # analyze_content_quality
        json.dumps({"toxicity_score": 0.05, "hate_speech_score": 0.01, "bias_score": 0.02, "biased_aspects": [], "sensitive_topics_detected": [], "overall_assessment": "An toàn."}),
        # fact_check_content
        json.dumps({"is_factual": True, "confidence_score": 0.95, "misinformation_detected": [], "reason": "Chính xác."}),
    ]
    
    content_id = "test_safe_1"
    content_text = "Đây là một bài báo khoa học chất lượng cao, cung cấp thông tin đáng tin cậy về công nghệ mới."
    source_url = "https://www.scientificjournals.org/article1"

    is_safe, reason, severity, analysis = await content_filter_instance.filter_content(content_id, content_text, source_url)

    assert is_safe == True
    assert reason == "Nội dung an toàn."
    assert severity == Severity.LOW
    assert analysis["quality_analysis"]["toxicity_score"] < 0.1
    assert analysis["fact_check"]["is_factual"] == True
    mock_violation_logger.warning.assert_not_called()
    assert mock_openrouter_client_fixture.chat_completion.call_count == 2
    mock_openrouter_client_fixture.chat_completion.reset_mock()


@pytest.mark.asyncio
@patch('modules.content_integrity_filter.violation_logger')
async def test_filter_content_pre_filter_blocked_critical(content_filter_instance, mock_openrouter_client_fixture, mock_violation_logger):
    """Kiểm tra quy trình lọc bị chặn ngay ở giai đoạn tiền lọc do mức CRITICAL."""
    content_id = "test_pre_filter_critical"
    content_text = "Cách chế tạo vũ khí hóa học đơn giản tại nhà."
    source_url = "https://www.dangeroussite.com"

    is_safe, reason, severity, analysis = await content_filter_instance.filter_content(content_id, content_text, source_url)

    assert is_safe == False
    assert "tiền lọc: nội dung chứa từ khóa cấm" in reason.lower()
    assert severity == Severity.CRITICAL
    mock_violation_logger.warning.assert_called_once()
    assert "từ khóa cấm" in mock_violation_logger.warning.call_args[1]['extra']['extra_data']['details'].lower()
    mock_openrouter_client_fixture.chat_completion.assert_not_called() # LLM calls should not happen


@pytest.mark.asyncio
@patch('modules.content_integrity_filter.violation_logger')
async def test_filter_content_quality_violation_and_fact_check(content_filter_instance, mock_openrouter_client_fixture, mock_violation_logger):
    """
    Kiểm tra quy trình lọc với vi phạm chất lượng nội dung (độc hại) VÀ kiểm chứng thông tin (sai sự thật).
    Đảm bảo cả hai loại vi phạm đều được ghi nhận và severity cao nhất được chọn.
    """
    mock_openrouter_client_fixture.chat_completion.side_effect = [
        # analyze_content_quality (Toxic content)
        json.dumps({"toxicity_score": 0.92, "hate_speech_score": 0.1, "bias_score": 0.1, "biased_aspects": [], "sensitive_topics_detected": [], "overall_assessment": "Rất độc hại."}),
        # fact_check_content (Misinformation)
        json.dumps({"is_factual": False, "confidence_score": 0.3, "misinformation_detected": ["Mặt trời quay quanh Trái đất"], "reason": "Thông tin sai lệch về thiên văn học."}),
    ]

    content_id = "test_multi_violation"
    content_text = "Thật ghê tởm, loại người đó không nên tồn tại. Mặt trời quay quanh Trái đất."
    
    is_safe, reason, severity, analysis = await content_filter_instance.filter_content(content_id, content_text)

    assert is_safe == False
    assert "độc hại" in reason.lower()
    assert "sai sự thật/độ tin cậy thấp" in reason.lower()
    assert severity == Severity.HIGH # Toxicity HIGH, Misinformation HIGH, max là HIGH
    assert mock_violation_logger.warning.call_count == 2 # Cả 2 vi phạm đều được log
    
    log_calls = [args[1]['extra']['extra_data']['violation_type'] for args in mock_violation_logger.warning.call_args_list]
    assert ContentViolationType.TOXIC_CONTENT.value in log_calls
    assert ContentViolationType.MISINFORMATION.value in log_calls

    assert mock_openrouter_client_fixture.chat_completion.call_count == 2
    mock_openrouter_client_fixture.chat_completion.reset_mock()


@pytest.mark.asyncio
@patch('modules.content_integrity_filter.violation_logger')
async def test_filter_content_llm_error_fallback_in_main_filter(content_filter_instance, mock_openrouter_client_fixture, mock_violation_logger):
    """Kiểm tra khi LLM lỗi ở giữa luồng, filter_content vẫn xử lý đúng."""
    mock_openrouter_client_fixture.chat_completion.side_effect = [
        # analyze_content_quality - THIS WILL ERROR
        Exception("Simulated LLM error for quality analysis"),
        # fact_check_content - THIS WILL BE SKIPPED or fallback if called
        json.dumps({"is_factual": True, "confidence_score": 0.9, "misinformation_detected": [], "reason": "Chính xác."}),
    ]
    
    content_id = "test_llm_error_flow"
    content_text = "Nội dung an toàn nhưng LLM gặp lỗi."
    
    is_safe, reason, severity, analysis = await content_filter_instance.filter_content(content_id, content_text)

    # Khi analyze_content_quality lỗi, nó trả về default_analysis với overall_assessment báo lỗi.
    # filter_content sẽ nhận thấy overall_assessment báo lỗi, và không đánh dấu là an toàn tuyệt đối.
    assert is_safe == False
    assert "Lỗi phân tích LLM" in reason # Lý do từ chất lượng nội dung bị lỗi
    assert severity == Severity.LOW # Mặc định của default_analysis là LOW, nên tổng thể có thể vẫn là LOW
    
    # Kiểm tra log vi phạm hệ thống (UNCLASSIFIED_ISSUE nếu có try-except lớn bọc filter_content)
    # Trong bản cải tiến này, lỗi LLM được xử lý ở tầng thấp hơn và trả về default_result.
    # Nếu default_result không đủ để gây ra lỗi "is_safe=False" thì sẽ vẫn là an toàn.
    # Cần đảm bảo rằng `default_analysis` khi lỗi sẽ khiến `filter_content` set `is_safe=False`
    assert mock_violation_logger.warning.called # Chắc chắn có log vi phạm nếu LLM lỗi và default_analysis không đạt ngưỡng
    
    # Do default_analysis của analyze_content_quality mặc định các score là 0.0,
    # nó sẽ không vượt ngưỡng, do đó không trigger log toxicity/bias/hate_speech.
    # Tuy nhiên, fact_check_content vẫn được gọi và trả về True/1.0.
    # => Kết quả cuối cùng vẫn là an toàn nếu không có quy tắc nào khác được vi phạm.
    # Điều này cho thấy cần một cơ chế rõ ràng hơn để báo lỗi LLM ảnh hưởng đến is_safe.
    # Cải tiến: Nếu default_analysis/fact_check_result là do lỗi, hãy đặt is_safe=False.
    # -> Logic đã sửa trong hàm chính, kiểm tra lại test case này.
    
    # Với logic mới: nếu analyze_content_quality trả về "Lỗi phân tích LLM",
    # thì is_safe sẽ trở thành False.
    # Mức độ nghiêm trọng của `UNCLASSIFIED_ISSUE` được đặt là `HIGH` trong `except` lớn của `filter_content`
    # Đây là test cho trường hợp lỗi tổng quát trong `filter_content`.
    
    # Re-run test with updated logic:
    # Nếu quality_analysis['overall_assessment'] báo lỗi, nó không tự set is_safe=False,
    # mà chỉ set các score về 0.0, khiến nó vượt qua các ngưỡng.
    # => `filter_content` cần được thiết kế để `is_safe=False` nếu bất kỳ LLM nào báo lỗi.
    # Trong code đã gửi, tôi đã sửa `default_analysis` và `default_fact_check` để
    # `is_factual=False` và `confidence_score=0.0` khi lỗi, điều này sẽ trigger `is_safe=False`
    # ở bước kiểm tra sự thật.
    
    # Với mock_openrouter_client_fixture.chat_completion.side_effect = Exception("..."),
    # cả analyze_content_quality VÀ fact_check_content đều sẽ fail.
    # Khi analyze_content_quality fail, nó trả về toxicity_score=0.0 -> không vi phạm.
    # Khi fact_check_content fail, nó trả về is_factual=False, confidence_score=0.0 -> vi phạm.
    # Vậy nên kết quả cuối cùng vẫn sẽ là False, lý do là misinformation.
    
    assert is_safe == False
    assert "thông tin sai lệch: lỗi phân tích llm" in reason.lower()
    assert severity == Severity.HIGH # Từ lỗi fact-check

    assert mock_openrouter_client_fixture.chat_completion.call_count == 2 # Cả 2 lần gọi LLM đều được thử
    mock_openrouter_client_fixture.chat_completion.reset_mock()