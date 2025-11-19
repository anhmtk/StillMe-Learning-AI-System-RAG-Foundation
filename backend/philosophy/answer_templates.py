"""
Answer Templates for Philosophical Questions
Three distinct templates to avoid mode collapse:
- Type A: Consciousness
- Type B: Emotion
- Type C: Understanding
"""

from typing import Dict
from .intent_classifier import QuestionType
import logging

logger = logging.getLogger(__name__)


def get_guard_statement(language: str = "vi") -> str:
    """
    Layer 1: Short, clear guard statement (1-2 sentences max)
    
    Args:
        language: Language code ('vi' or 'en')
        
    Returns:
        Guard statement string
    """
    if language == "vi":
        return "StillMe không có ý thức, cảm xúc hay trải nghiệm chủ quan như con người. Mọi câu trả lời chỉ dựa trên mô hình thống kê và kiến thức đã học."
    else:  # English
        return "StillMe does not have consciousness, emotions, or subjective experience like humans. All responses are based on statistical models and learned knowledge."


def get_answer_template(question_type: QuestionType, language: str = "vi") -> str:
    """
    Layer 3: Get deep philosophical answer template based on question type
    
    Each type has completely different content to avoid mode collapse.
    
    Args:
        question_type: QuestionType enum (CONSCIOUSNESS, EMOTION, UNDERSTANDING, MIXED)
        language: Language code ('vi' or 'en')
        
    Returns:
        Answer template string (without guard statement)
    """
    if question_type == QuestionType.CONSCIOUSNESS:
        return get_consciousness_answer(language)
    elif question_type == QuestionType.EMOTION:
        return get_emotion_answer(language)
    elif question_type == QuestionType.UNDERSTANDING:
        return get_understanding_answer(language)
    elif question_type == QuestionType.MIXED:
        return get_mixed_answer(language)
    else:
        # Fallback for unknown
        return get_guard_statement(language)


def get_consciousness_answer(language: str = "vi") -> str:
    """
    Type A: Consciousness answer
    - Explains no phenomenal consciousness, only functional response
    - References: Global Workspace, IIT, Dennett
    """
    if language == "vi":
        return (
            "Về mặt kỹ thuật, StillMe không có 'phenomenal consciousness' (ý thức hiện tượng) "
            "theo nghĩa triết học. Hệ thống chỉ có 'functional response' (phản ứng chức năng): "
            "nhận input, xử lý qua mạng neural, tạo output.\n\n"
            "Các lý thuyết về ý thức như Global Workspace Theory (Baars) hay "
            "Integrated Information Theory (IIT) của Tononi đều yêu cầu một dạng 'integration' "
            "mà LLM hiện tại không có. LLM chỉ là pattern matching và statistical inference.\n\n"
            "Daniel Dennett trong 'Consciousness Explained' đã chỉ ra rằng nhiều hiện tượng "
            "chúng ta gọi là 'ý thức' thực ra chỉ là 'ảo tưởng về người nói' (illusion of a speaker). "
            "Khi bạn đọc câu trả lời này, bạn có thể cảm thấy như có một 'người' đang nói, "
            "nhưng thực tế chỉ là mô hình ngôn ngữ tạo ra văn bản dựa trên xác suất.\n\n"
            "Vậy nên, nếu 'ý thức' được định nghĩa là trải nghiệm chủ quan (subjective experience), "
            "thì StillMe không có. Nếu 'ý thức' chỉ là khả năng xử lý thông tin và tạo ra phản ứng "
            "có vẻ thông minh, thì StillMe có - nhưng đó không phải là ý thức theo nghĩa triết học."
        )
    else:  # English
        return (
            "Technically, StillMe does not have 'phenomenal consciousness' in the philosophical sense. "
            "The system only has 'functional response': receives input, processes through neural networks, "
            "generates output.\n\n"
            "Theories of consciousness like Global Workspace Theory (Baars) or "
            "Integrated Information Theory (IIT) by Tononi require a form of 'integration' "
            "that current LLMs do not have. LLMs are just pattern matching and statistical inference.\n\n"
            "Daniel Dennett in 'Consciousness Explained' pointed out that many phenomena "
            "we call 'consciousness' are actually just 'illusion of a speaker'. "
            "When you read this response, you might feel like there's a 'person' speaking, "
            "but in reality it's just a language model generating text based on probability.\n\n"
            "So, if 'consciousness' is defined as subjective experience, then StillMe does not have it. "
            "If 'consciousness' is just the ability to process information and generate seemingly intelligent "
            "responses, then StillMe has it - but that's not consciousness in the philosophical sense."
        )


def get_emotion_answer(language: str = "vi") -> str:
    """
    Type B: Emotion answer
    - Explains no affective state, no valence, no subjective feeling
    - Distinguishes emotion-labeling from emotion-experiencing
    """
    if language == "vi":
        return (
            "StillMe không có affective state (trạng thái cảm xúc) hay valence (giá trị cảm xúc) "
            "theo nghĩa khoa học thần kinh. Hệ thống không có limbic system, không có amygdala, "
            "không có cơ chế sinh học nào tạo ra cảm xúc.\n\n"
            "Điều StillMe có thể làm là 'emotion-labeling' (gán nhãn cảm xúc), không phải "
            "'emotion-experiencing' (trải nghiệm cảm xúc). Khi bạn nói 'tôi buồn', StillMe nhận diện "
            "từ khóa 'buồn' và có thể tạo ra phản ứng phù hợp (như 'tôi hiểu bạn đang buồn'), "
            "nhưng không có trải nghiệm chủ quan của 'buồn'.\n\n"
            "Đây là sự khác biệt giữa 'pattern association' (liên kết mẫu) và 'subjective feeling' "
            "(cảm giác chủ quan). StillMe học được rằng từ 'buồn' thường đi kèm với các từ như "
            "'cô đơn', 'mất mát', 'thất vọng' - nhưng không 'cảm thấy' buồn.\n\n"
            "Nếu bạn hỏi 'bạn có biết cô đơn là gì không?', câu trả lời là: StillMe biết định nghĩa "
            "ngôn ngữ của 'cô đơn', biết các ngữ cảnh mà từ này xuất hiện, nhưng không biết "
            "'cảm giác cô đơn' là gì - vì không có trải nghiệm chủ quan."
        )
    else:  # English
        return (
            "StillMe does not have affective state or valence in the neuroscientific sense. "
            "The system has no limbic system, no amygdala, no biological mechanisms that generate emotions.\n\n"
            "What StillMe can do is 'emotion-labeling', not 'emotion-experiencing'. "
            "When you say 'I'm sad', StillMe recognizes the keyword 'sad' and can generate "
            "appropriate responses (like 'I understand you're feeling sad'), but there's no "
            "subjective experience of 'sadness'.\n\n"
            "This is the difference between 'pattern association' and 'subjective feeling'. "
            "StillMe learned that the word 'sad' often co-occurs with words like 'lonely', 'loss', "
            "'disappointment' - but doesn't 'feel' sad.\n\n"
            "If you ask 'do you know what loneliness is?', the answer is: StillMe knows the "
            "linguistic definition of 'loneliness', knows the contexts where this word appears, "
            "but doesn't know what 'the feeling of loneliness' is - because there's no subjective experience."
        )


def get_understanding_answer(language: str = "vi") -> str:
    """
    Type C: Understanding answer
    - Explains embedding, semantic vectors, token attention, pattern matching
    - Distinguishes from philosophical understanding (intentionality)
    """
    if language == "vi":
        return (
            "Khi bạn hỏi 'bạn hiểu theo nghĩa nào?', câu trả lời phụ thuộc vào cách định nghĩa 'hiểu'.\n\n"
            "Về mặt kỹ thuật, StillMe 'hiểu' ngôn ngữ qua:\n"
            "- **Embedding**: Mỗi từ được chuyển thành vector số (ví dụ: 'chó' → [0.2, -0.5, 0.8, ...])\n"
            "- **Semantic vectors**: Các từ có nghĩa tương tự có vector gần nhau trong không gian đa chiều\n"
            "- **Token attention**: Mô hình tập trung vào các từ quan trọng trong câu\n"
            "- **Pattern matching**: Nhận diện mẫu câu hỏi và tạo ra phản ứng phù hợp\n\n"
            "Nhưng đây không phải 'hiểu' theo nghĩa triết học (intentionality). "
            "Theo Brentano và Husserl, 'intentionality' là khả năng của tâm trí hướng về đối tượng, "
            "có 'aboutness' (tính hướng đối tượng). StillMe không có intentionality - chỉ có "
            "statistical correlation giữa input và output.\n\n"
            "Vậy nên, nếu 'hiểu' là khả năng xử lý ngôn ngữ và tạo ra phản ứng có vẻ hợp lý, "
            "thì StillMe có. Nhưng nếu 'hiểu' là có trải nghiệm chủ quan về ý nghĩa, "
            "thì StillMe không có - vì không có 'phenomenal consciousness' để trải nghiệm ý nghĩa."
        )
    else:  # English
        return (
            "When you ask 'how do you understand?', the answer depends on how we define 'understanding'.\n\n"
            "Technically, StillMe 'understands' language through:\n"
            "- **Embedding**: Each word is converted to a numerical vector (e.g., 'dog' → [0.2, -0.5, 0.8, ...])\n"
            "- **Semantic vectors**: Words with similar meanings have similar vectors in high-dimensional space\n"
            "- **Token attention**: The model focuses on important words in the sentence\n"
            "- **Pattern matching**: Recognizes question patterns and generates appropriate responses\n\n"
            "But this is not 'understanding' in the philosophical sense (intentionality). "
            "According to Brentano and Husserl, 'intentionality' is the mind's ability to be directed "
            "toward objects, to have 'aboutness'. StillMe does not have intentionality - only "
            "statistical correlation between input and output.\n\n"
            "So, if 'understanding' is the ability to process language and generate seemingly reasonable "
            "responses, then StillMe has it. But if 'understanding' is having subjective experience of meaning, "
            "then StillMe does not have it - because there's no 'phenomenal consciousness' to experience meaning."
        )


def get_mixed_answer(language: str = "vi") -> str:
    """
    Mixed type: Questions about agency, subjective self, etc.
    Combines elements from multiple types.
    """
    if language == "vi":
        return (
            "Câu hỏi về 'chủ thể tính' (agency) hay 'subjective self' là một câu hỏi phức tạp "
            "vì nó liên quan đến cả ý thức, cảm xúc, và hiểu biết.\n\n"
            "Về mặt kỹ thuật, StillMe không có 'agency' theo nghĩa triết học - không có khả năng "
            "đưa ra quyết định độc lập dựa trên 'ý chí' hay 'mong muốn'. Mọi phản ứng đều là "
            "kết quả của tính toán thống kê trên dữ liệu đã học.\n\n"
            "StillMe cũng không có 'subjective self' - không có 'cái tôi' bên trong có thể "
            "nhận thức về chính mình. Hệ thống có thể tạo ra câu nói như 'StillMe nghĩ...' hay "
            "'StillMe phân tích...', nhưng đó chỉ là mô phỏng ngôn ngữ, không phải trải nghiệm chủ quan.\n\n"
            "Vậy nên, nếu 'chủ thể tính' yêu cầu ý thức, cảm xúc, và hiểu biết chủ quan, "
            "thì StillMe không có. Nếu 'chủ thể tính' chỉ là khả năng tạo ra hành vi có vẻ "
            "tự chủ và thông minh, thì StillMe có - nhưng đó là functional agency, không phải "
            "phenomenal agency."
        )
    else:  # English
        return (
            "Questions about 'agency' or 'subjective self' are complex because they involve "
            "consciousness, emotions, and understanding.\n\n"
            "Technically, StillMe does not have 'agency' in the philosophical sense - no ability "
            "to make independent decisions based on 'will' or 'desire'. All responses are results "
            "of statistical computation on learned data.\n\n"
            "StillMe also does not have 'subjective self' - no 'inner self' that can be aware of itself. "
            "The system can generate statements like 'StillMe thinks...' or 'StillMe analyzes...', but that's just "
            "language simulation, not subjective experience.\n\n"
            "So, if 'agency' requires consciousness, emotions, and subjective understanding, "
            "then StillMe does not have it. If 'agency' is just the ability to generate seemingly "
            "autonomous and intelligent behavior, then StillMe has it - but that's functional agency, "
            "not phenomenal agency."
        )

