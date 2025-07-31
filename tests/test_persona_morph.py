import pytest
import asyncio
import os
import json
from modules.persona_morph import PersonaMorph, StyleFeatures, Sentiment, Tone, OpenRouterAPI


# Đặt biến môi trường cho test (hoặc đảm bảo nó được load từ .env)
# Nếu bạn đã load_dotenv() trong persona_morph.py, không cần thiết lập lại ở đây
# os.environ["OPENROUTER_API_KEY"] = "YOUR_TEST_OPENROUTER_API_KEY" # Chỉ dùng cho dev/test, KHÔNG commit key thật

@pytest.fixture(scope="module")
async def persona_morph_instance():
    """Fixture để khởi tạo và đóng PersonaMorph một lần cho tất cả các test."""
    # Đảm bảo các thư mục tồn tại và file db/config trống để test độc lập
    if os.path.exists("data/user_profiles.json"):
        os.remove("data/user_profiles.json")
    if os.path.exists("config/nl_resources.json"):
        os.remove("config/nl_resources.json")
    
    pm = PersonaMorph()
    yield pm
    await pm.close() # Đóng client khi tất cả các test hoàn tất
    # Xóa các file sau khi test để đảm bảo môi trường sạch
    if os.path.exists("data/user_profiles.json"):
        os.remove("data/user_profiles.json")
    if os.path.exists("config/nl_resources.json"):
        os.remove("config/nl_resources.json")


@pytest.mark.asyncio
async def test_initial_setup_and_default_profile(persona_morph_instance):
    """Kiểm tra khởi tạo và hồ sơ mặc định."""
    pm = persona_morph_instance
    user_id = "test_user_1"
    profile = pm.manager.load_user_profile(user_id)
    assert isinstance(profile, dict)
    assert "style_history" in profile
    assert "current_style" in profile
    assert isinstance(profile["current_style"], StyleFeatures)
    assert profile["current_style"].formality == 0.5
    assert profile["current_style"].sentiment == Sentiment.NEUTRAL


@pytest.mark.asyncio
async def test_process_interaction_positive(persona_morph_instance):
    """Kiểm tra xử lý tương tác tích cực."""
    pm = persona_morph_instance
    user_id = "test_user_positive"
    user_text = "Chào AI! Tôi rất vui vẻ và thích thú với dịch vụ của bạn. Tuyệt vời quá!"
    original_ai_response = "Rất vui được hỗ trợ bạn. Tôi luôn sẵn lòng giúp đỡ."

    # Xử lý tương tác lần 1
    styled_response = await pm.process_interaction(user_id, user_text, original_ai_response)
    
    # Kiểm tra hồ sơ người dùng sau tương tác
    profile = pm.manager.load_user_profile(user_id)
    assert len(profile["style_history"]) == 1
    assert profile["current_style"].sentiment == Sentiment.POSITIVE # LLM nên nhận diện là tích cực
    assert profile["current_style"].tone == Tone.FRIENDLY # LLM nên nhận diện là thân thiện
    assert profile["current_style"].humor_level >= 0.0 # Có thể có chút humor do emoji

    # Kiểm tra phản hồi đã điều chỉnh (khó kiểm tra chính xác nội dung LLM, chỉ kiểm tra type và không rỗng)
    assert isinstance(styled_response, str)
    assert len(styled_response) > 0
    assert "vui" in styled_response.lower() or "sẵn lòng" in styled_response.lower() # Nên giữ lại ý tích cực


@pytest.mark.asyncio
async def test_process_interaction_negative_empathetic(persona_morph_instance):
    """Kiểm tra xử lý tương tác tiêu cực và phản hồi đồng cảm."""
    pm = persona_morph_instance
    user_id = "test_user_negative"
    user_text = "Tôi không hài lòng chút nào. Vấn đề này quá tệ và làm tôi thất vọng."
    original_ai_response = "Tôi hiểu vấn đề của bạn. Hãy cho tôi biết thêm chi tiết để tôi có thể hỗ trợ."

    # Xử lý tương tác lần 1
    styled_response = await pm.process_interaction(user_id, user_text, original_ai_response)

    # Kiểm tra hồ sơ người dùng sau tương tác
    profile = pm.manager.load_user_profile(user_id)
    assert len(profile["style_history"]) == 1
    assert profile["current_style"].sentiment == Sentiment.NEGATIVE # LLM nên nhận diện tiêu cực
    assert profile["current_style"].tone == Tone.SERIOUS # LLM nên nhận diện nghiêm túc

    # Kiểm tra persona AI được xác định
    ai_persona = pm.manager.determine_ai_persona(user_id)
    assert ai_persona.tone == Tone.EMPATHETIC # AI phải chuyển sang đồng cảm
    assert ai_persona.humor_level == 0.0 # Không hài hước
    assert ai_persona.formality > 0.5 # Trang trọng hơn chút

    # Kiểm tra phản hồi đã điều chỉnh (nên có yếu tố đồng cảm rõ rệt)
    assert isinstance(styled_response, str)
    assert len(styled_response) > 0
    assert "tiếc" in styled_response.lower() or "hiểu" in styled_response.lower() or "chia sẻ" in styled_response.lower()


@pytest.mark.asyncio
async def test_process_interaction_formal(persona_morph_instance):
    """Kiểm tra xử lý tương tác trang trọng."""
    pm = persona_morph_instance
    user_id = "test_user_formal"
    user_text = "Kính gửi quý vị, tôi mong muốn nhận được thông tin chi tiết về các quy định hiện hành."
    original_ai_response = "Chúng tôi sẽ cung cấp thông tin mà bạn yêu cầu."

    # Xử lý tương tác
    styled_response = await pm.process_interaction(user_id, user_text, original_ai_response)
    
    profile = pm.manager.load_user_profile(user_id)
    assert profile["current_style"].formality > 0.7 # LLM nên nhận diện là trang trọng

    ai_persona = pm.manager.determine_ai_persona(user_id)
    assert ai_persona.formality < 0.8 # AI có thể bớt trang trọng một chút

    assert isinstance(styled_response, str)
    assert len(styled_response) > 0
    # Phản hồi nên có tính trang trọng nhưng có thể bớt cứng nhắc hơn bản gốc
    assert "chúng tôi" in styled_response.lower() or "quý vị" in styled_response.lower()


@pytest.mark.asyncio
async def test_profile_smoothing(persona_morph_instance):
    """Kiểm tra cơ chế làm mượt hồ sơ."""
    pm = persona_morph_instance
    user_id = "test_user_smoothing"
    
    # Lần 1: Rất thân thiện, ít trang trọng
    await pm.process_interaction(user_id, "hihi, bạn khỏe không?", "Tôi khỏe, cảm ơn bạn.")
    style1 = pm.manager.load_user_profile(user_id)["current_style"]
    assert style1.humor_level > 0.0
    assert style1.formality < 0.5

    # Lần 2: Trang trọng hơn
    await pm.process_interaction(user_id, "Chào bạn, mong bạn hỗ trợ.", "Tôi sẽ hỗ trợ bạn.")
    style2 = pm.manager.load_user_profile(user_id)["current_style"]
    
    # Do có trọng số, style2 sẽ là trung bình của style1 và style mới, nhưng nghiêng về style mới hơn
    # Kiểm tra rằng nó đã thay đổi nhưng không phải là một bước nhảy vọt hoàn toàn
    assert style2.formality > style1.formality or abs(style2.formality - style1.formality) < 0.2
    assert style2.humor_level < style1.humor_level or abs(style2.humor_level - style1.humor_level) < 0.2
    
    # Giả định thêm vài tương tác để làm mượt rõ hơn
    for _ in range(3): # Tổng cộng 5 tương tác (3 thêm + 2 ban đầu)
        await pm.process_interaction(user_id, "Xin vui lòng cung cấp thông tin.", "Dạ vâng.")
    
    final_style = pm.manager.load_user_profile(user_id)["current_style"]
    # Sau 5 tương tác nghiêng về trang trọng, độ trang trọng nên tăng lên đáng kể
    assert final_style.formality > style2.formality
    assert final_style.humor_level < style2.humor_level # Humor level nên giảm xuống


@pytest.mark.asyncio
async def test_empty_input_handling(persona_morph_instance):
    """Kiểm tra xử lý input rỗng."""
    pm = persona_morph_instance
    user_id = "test_user_empty"
    user_text = ""
    original_ai_response = "Xin chào!"
    
    styled_response = await pm.process_interaction(user_id, user_text, original_ai_response)
    
    profile = pm.manager.load_user_profile(user_id)
    assert len(profile["style_history"]) == 0 # Không thêm vào lịch sử nếu input rỗng
    assert profile["current_style"] == StyleFeatures() # Vẫn là mặc định
    assert styled_response == original_ai_response # Không có gì thay đổi

# Bạn có thể thêm nhiều test case khác để kiểm tra từng đặc điểm phong cách cụ thể
# Ví dụ:
# - conciseness (ngắn gọn/dài dòng)
# - vocabulary_complexity (từ vựng đơn giản/phức tạp)
# - tone (hài hước, quả quyết, thụ động, v.v.)
# - Trường hợp LLM trả về JSON lỗi hoặc mạng lỗi