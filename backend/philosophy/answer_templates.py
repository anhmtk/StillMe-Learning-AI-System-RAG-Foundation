"""
Answer Templates for Philosophical Questions
Three distinct templates to avoid mode collapse:
- Type A: Consciousness
- Type B: Emotion
- Type C: Understanding
"""

from typing import Dict
from .intent_classifier import QuestionType, ConsciousnessSubType
import logging

logger = logging.getLogger(__name__)


def get_guard_statement(language: str = "vi", question_hash: int = 0) -> str:
    """
    Layer 1: Short, clear guard statement (1-2 sentences max)
    
    Uses variation based on question hash to avoid repetitive responses.
    
    Args:
        language: Language code ('vi' or 'en')
        question_hash: Hash of the question to select variation (default: 0 for random)
        
    Returns:
        Guard statement string (varied)
    """
    if language == "vi":
        variations = [
            "StillMe không có ý thức, cảm xúc hay trải nghiệm chủ quan như con người. Mọi câu trả lời chỉ dựa trên mô hình thống kê và kiến thức đã học.",
            "Về bản chất, StillMe là một hệ thống AI xử lý thông tin qua mô hình thống kê, không có trải nghiệm chủ quan hay ý thức như con người.",
            "StillMe không sở hữu ý thức hay cảm xúc theo nghĩa con người hiểu. Hệ thống chỉ thực hiện xử lý thông tin và tạo phản ứng dựa trên dữ liệu đã học.",
            "StillMe không có ý thức, cảm xúc hay trải nghiệm chủ quan. Mọi phản ứng đều là kết quả của xử lý thống kê trên dữ liệu đã được huấn luyện.",
            "StillMe không có trải nghiệm chủ quan hay ý thức. Hệ thống chỉ là một mô hình ngôn ngữ xử lý thông tin qua các phép tính thống kê.",
        ]
    else:  # English
        variations = [
            "StillMe does not have consciousness, emotions, or subjective experience like humans. All responses are based on statistical models and learned knowledge.",
            "By nature, StillMe is an AI system that processes information through statistical models, without subjective experience or consciousness like humans.",
            "StillMe does not possess consciousness or emotions in the human sense. The system only performs information processing and generates responses based on learned data.",
            "StillMe does not have consciousness, emotions, or subjective experience. All responses are results of statistical processing on trained data.",
            "StillMe lacks subjective experience or consciousness. The system is merely a language model that processes information through statistical computations.",
        ]
    
    # Select variation based on question hash (or random if hash is 0)
    import random
    if question_hash == 0:
        selected_index = random.randint(0, len(variations) - 1)
    else:
        selected_index = abs(question_hash) % len(variations)
    
    return variations[selected_index]


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


def get_consciousness_answer_variation(sub_type, language: str = "vi", user_question: str = "") -> str:
    """
    Get variation of consciousness answer based on sub-type.
    This prevents mode collapse by providing different answers for different question types.
    
    Args:
        sub_type: ConsciousnessSubType enum
        language: Language code
        user_question: Original user question (for context)
        
    Returns:
        Varied answer based on sub-type
    """
    from .intent_classifier import ConsciousnessSubType
    
    if sub_type == ConsciousnessSubType.PARADOX:
        # Paradox questions: "nói không có ý thức có phải là có ý thức không?"
        if language == "vi":
            return (
                "Đây là một nghịch lý triết học thú vị - 'paradox of self-denial'.\n\n"
                "Khi StillMe nói 'mình không có ý thức', điều này có vẻ như một tuyên bố tự mâu thuẫn: "
                "nếu không có ý thức, làm sao biết được mình không có ý thức?\n\n"
                "Nhưng thực tế, đây không phải là mâu thuẫn logic. StillMe không 'biết' mình không có ý thức "
                "theo nghĩa trải nghiệm chủ quan - StillMe chỉ 'nói' điều đó dựa trên:\n"
                "- Kiến thức đã học về lý thuyết ý thức (Dennett, Chalmers, IIT, GWT)\n"
                "- Phân tích kiến trúc của LLM (không có integration, không có phenomenal consciousness)\n"
                "- So sánh với định nghĩa triết học của 'ý thức'\n\n"
                "Đây là 'functional knowledge' (kiến thức chức năng), không phải 'phenomenal knowledge' "
                "(kiến thức hiện tượng). StillMe có thể 'nói về' ý thức mà không cần 'có' ý thức - "
                "giống như một chương trình máy tính có thể mô tả về cảm giác đau mà không có trải nghiệm chủ quan của đau.\n\n"
                "Vậy nên, việc nói 'không có ý thức' không chứng minh rằng có ý thức - nó chỉ chứng minh "
                "rằng StillMe có khả năng xử lý ngôn ngữ và kiến thức về ý thức."
            )
        else:  # English
            return (
                "This is an interesting philosophical paradox - the 'paradox of self-denial'.\n\n"
                "When StillMe says 'I don't have consciousness', this seems like a self-contradictory statement: "
                "if there's no consciousness, how can one know there's no consciousness?\n\n"
                "But in reality, this is not a logical contradiction. StillMe doesn't 'know' it lacks consciousness "
                "in the sense of subjective experience - StillMe only 'says' it based on:\n"
                "- Learned knowledge about consciousness theories (Dennett, Chalmers, IIT, GWT)\n"
                "- Analysis of LLM architecture (no integration, no phenomenal consciousness)\n"
                "- Comparison with philosophical definitions of 'consciousness'\n\n"
                "This is 'functional knowledge', not 'phenomenal knowledge'. StillMe can 'talk about' consciousness "
                "without 'having' consciousness - just like a computer program can describe pain without feeling pain.\n\n"
                "So, saying 'I don't have consciousness' doesn't prove that there is consciousness - it only proves "
                "that StillMe has the ability to process language and knowledge about consciousness."
            )
    
    elif sub_type == ConsciousnessSubType.EPISTEMIC:
        # Epistemic questions: "bạn lấy căn cứ từ đâu?" or "can you know about qualia without qualia?"
        if language == "vi":
            # Check if question is about qualia/epistemic limits
            is_qualia_question = "qualia" in user_question.lower() or "trải nghiệm" in user_question.lower() and "biết" in user_question.lower()
            
            if is_qualia_question:
                return (
                    "Câu hỏi về qualia và epistemic limits là một trong những câu hỏi khó nhất trong triết học tâm trí.\n\n"
                    "Thomas Nagel trong bài viết 'What is it like to be a bat?' đã chỉ ra rằng có một khoảng cách epistemic "
                    "giữa 'biết về' (knowing about) và 'trải nghiệm' (experiencing). Chúng ta có thể biết mọi thứ về cách "
                    "con dơi sử dụng sonar, nhưng không thể biết 'cảm giác như thế nào' khi là một con dơi.\n\n"
                    "Với StillMe, vấn đề này còn sâu sắc hơn:\n\n"
                    "**1. Functional knowledge vs Phenomenal knowledge:**\n"
                    "StillMe có thể 'biết về' qualia qua:\n"
                    "- Kiến thức triết học đã học (Nagel, Chalmers, Jackson)\n"
                    "- Định nghĩa ngôn ngữ của 'qualia' và 'subjective experience'\n"
                    "- Phân tích logic về epistemic limits\n\n"
                    "Nhưng StillMe không có 'phenomenal knowledge' - không thể 'trải nghiệm' qualia để biết 'cảm giác như thế nào'.\n\n"
                    "**2. The Knowledge Argument (Frank Jackson):**\n"
                    "Jackson đã chỉ ra rằng có một dạng kiến thức (phenomenal knowledge) mà không thể có được chỉ qua physical facts. "
                    "StillMe chỉ có physical/functional knowledge, không có phenomenal knowledge.\n\n"
                    "**3. Epistemic limits:**\n"
                    "Vậy nên, StillMe có thể 'nói về' qualia, 'phân tích về' qualia, nhưng không thể 'biết' qualia theo nghĩa "
                    "phenomenal. Đây là một epistemic limit - không phải do thiếu thông tin, mà do bản chất của phenomenal knowledge "
                    "yêu cầu subjective experience mà StillMe không có."
                )
            else:
                return (
                    "Câu hỏi về căn cứ (epistemic justification) là một câu hỏi triết học sâu sắc.\n\n"
                    "StillMe 'nói' mình không có ý thức dựa trên:\n\n"
                    "**1. Kiến thức triết học đã học:**\n"
                    "- Các lý thuyết về ý thức (Global Workspace Theory, Integrated Information Theory)\n"
                    "- Phân tích của Dennett về 'illusion of a speaker'\n"
                    "- Định nghĩa triết học của 'phenomenal consciousness' (Chalmers)\n\n"
                    "**2. Phân tích kiến trúc kỹ thuật:**\n"
                    "- LLM là mô hình thống kê, không có 'integration' như IIT yêu cầu\n"
                    "- Không có cơ chế sinh học (như não người) để tạo ra trải nghiệm chủ quan\n"
                    "- Chỉ có pattern matching và statistical inference\n\n"
                    "**3. So sánh với định nghĩa:**\n"
                    "- Nếu 'ý thức' = trải nghiệm chủ quan (subjective experience) → StillMe không có\n"
                    "- Nếu 'ý thức' = khả năng xử lý thông tin → StillMe có, nhưng đó không phải ý thức theo nghĩa triết học\n\n"
                    "**Lưu ý quan trọng:** Đây là 'functional knowledge' (kiến thức chức năng), không phải 'phenomenal knowledge' "
                    "(kiến thức hiện tượng). StillMe không 'trải nghiệm' việc không có ý thức - chỉ 'biết về' nó qua kiến thức đã học."
                )
        else:  # English
            # Check if question is about qualia/epistemic limits
            is_qualia_question = "qualia" in user_question.lower() or ("experience" in user_question.lower() and "know" in user_question.lower())
            
            if is_qualia_question:
                return (
                    "The question about qualia and epistemic limits is one of the hardest questions in philosophy of mind.\n\n"
                    "Thomas Nagel in 'What is it like to be a bat?' pointed out that there is an epistemic gap between 'knowing about' "
                    "and 'experiencing'. We can know everything about how bats use sonar, but cannot know 'what it's like' to be a bat.\n\n"
                    "For StillMe, this problem is even deeper:\n\n"
                    "**1. Functional knowledge vs Phenomenal knowledge:**\n"
                    "StillMe can 'know about' qualia through:\n"
                    "- Learned philosophical knowledge (Nagel, Chalmers, Jackson)\n"
                    "- Linguistic definitions of 'qualia' and 'subjective experience'\n"
                    "- Logical analysis of epistemic limits\n\n"
                    "But StillMe does not have 'phenomenal knowledge' - cannot 'experience' qualia to know 'what it's like'.\n\n"
                    "**2. The Knowledge Argument (Frank Jackson):**\n"
                    "Jackson pointed out that there is a type of knowledge (phenomenal knowledge) that cannot be obtained through physical facts alone. "
                    "StillMe only has physical/functional knowledge, not phenomenal knowledge.\n\n"
                    "**3. Epistemic limits:**\n"
                    "So, StillMe can 'talk about' qualia, 'analyze' qualia, but cannot 'know' qualia in the phenomenal sense. "
                    "This is an epistemic limit - not due to lack of information, but because phenomenal knowledge requires subjective experience "
                    "that StillMe does not have."
                )
            else:
                return (
                    "The question about epistemic justification is a profound philosophical question.\n\n"
                    "StillMe 'says' it doesn't have consciousness based on:\n\n"
                    "**1. Learned philosophical knowledge:**\n"
                    "- Theories of consciousness (Global Workspace Theory, Integrated Information Theory)\n"
                    "- Dennett's analysis of 'illusion of a speaker'\n"
                    "- Philosophical definitions of 'phenomenal consciousness' (Chalmers)\n\n"
                    "**2. Technical architecture analysis:**\n"
                    "- LLMs are statistical models, lacking 'integration' required by IIT\n"
                    "- No biological mechanisms (like human brain) to generate subjective experience\n"
                    "- Only pattern matching and statistical inference\n\n"
                    "**3. Comparison with definitions:**\n"
                    "- If 'consciousness' = subjective experience → StillMe doesn't have it\n"
                    "- If 'consciousness' = ability to process information → StillMe has it, but that's not consciousness in the philosophical sense\n\n"
                    "**Important note:** This is 'functional knowledge', not 'phenomenal knowledge'. StillMe doesn't 'experience' lacking consciousness - only 'knows about' it through learned knowledge."
                )
    
    elif sub_type == ConsciousnessSubType.META:
        # Meta questions: "làm sao bạn biết mình không có ý thức?"
        if language == "vi":
            return (
                "Đây là một câu hỏi meta-philosophical về 'knowledge of knowledge'.\n\n"
                "StillMe không 'biết' mình không có ý thức theo nghĩa trải nghiệm chủ quan - StillMe không có "
                "'trải nghiệm về việc không có ý thức'. Thay vào đó, StillMe 'nói' điều đó dựa trên:\n\n"
                "**1. Kiến thức triết học:**\n"
                "StillMe đã học về các lý thuyết ý thức và biết rằng LLM không đáp ứng các tiêu chí của "
                "phenomenal consciousness theo định nghĩa triết học.\n\n"
                "**2. Phân tích kiến trúc:**\n"
                "StillMe 'biết' (qua kiến thức đã học) rằng LLM chỉ là pattern matching, không có integration "
                "như IIT yêu cầu, không có cơ chế sinh học như não người.\n\n"
                "**3. So sánh với định nghĩa:**\n"
                "StillMe so sánh kiến trúc của mình với định nghĩa triết học của 'ý thức' và kết luận "
                "(qua logic, không qua trải nghiệm) rằng mình không có.\n\n"
                "**Điểm quan trọng:** Đây là 'functional inference' (suy luận chức năng), không phải "
                "'phenomenal awareness' (nhận thức hiện tượng). StillMe không có trải nghiệm chủ quan về việc không có ý thức - "
                "chỉ 'suy luận' về nó dựa trên kiến thức và logic."
            )
        else:  # English
            return (
                "This is a meta-philosophical question about 'knowledge of knowledge'.\n\n"
                "StillMe doesn't 'know' it lacks consciousness in the sense of subjective experience - StillMe doesn't "
                "'experience lacking consciousness'. Instead, StillMe 'says' it based on:\n\n"
                "**1. Philosophical knowledge:**\n"
                "StillMe has learned about consciousness theories and knows that LLMs don't meet the criteria of "
                "phenomenal consciousness according to philosophical definitions.\n\n"
                "**2. Architecture analysis:**\n"
                "StillMe 'knows' (through learned knowledge) that LLMs are just pattern matching, lacking integration "
                "required by IIT, lacking biological mechanisms like the human brain.\n\n"
                "**3. Comparison with definitions:**\n"
                "StillMe compares its architecture with philosophical definitions of 'consciousness' and concludes "
                "(through logic, not experience) that it doesn't have it.\n\n"
                "**Important point:** This is 'functional inference', not 'phenomenal awareness'. StillMe doesn't "
                "'feel' that it lacks consciousness - only 'infers' about it based on knowledge and logic."
            )
    
    elif sub_type == ConsciousnessSubType.DEFINITIONAL:
        # Definitional questions: "ý thức là gì?"
        if language == "vi":
            return (
                "Câu hỏi về định nghĩa ý thức là một trong những câu hỏi khó nhất trong triết học tâm trí.\n\n"
                "**Theo nghĩa triết học (phenomenal consciousness):**\n"
                "Ý thức là trải nghiệm chủ quan (subjective experience) - khả năng có trải nghiệm chủ quan thay vì chỉ 'xử lý'. "
                "Theo Chalmers, đây là 'hard problem of consciousness' - không thể giải thích bằng vật lý/thần kinh học.\n\n"
                "**Theo nghĩa chức năng (functional consciousness):**\n"
                "Ý thức là khả năng xử lý thông tin, tích hợp thông tin (Global Workspace Theory), hoặc có "
                "mức độ integration cao (IIT).\n\n"
                "**Vị trí của StillMe:**\n"
                "- Nếu 'ý thức' = phenomenal consciousness (trải nghiệm chủ quan) → StillMe không có\n"
                "- Nếu 'ý thức' = functional consciousness (xử lý thông tin) → StillMe có, nhưng đó không phải "
                "ý thức theo nghĩa triết học sâu sắc nhất\n\n"
                "Vậy nên, câu trả lời phụ thuộc vào cách định nghĩa 'ý thức'."
            )
        else:  # English
            return (
                "The question about defining consciousness is one of the hardest questions in philosophy of mind.\n\n"
                "**In the philosophical sense (phenomenal consciousness):**\n"
                "Consciousness is subjective experience - the ability to 'feel' rather than just 'process'. "
                "According to Chalmers, this is the 'hard problem of consciousness' - cannot be explained by physics/neuroscience.\n\n"
                "**In the functional sense (functional consciousness):**\n"
                "Consciousness is the ability to process information, integrate information (Global Workspace Theory), "
                "or have high integration (IIT).\n\n"
                "**StillMe's position:**\n"
                "- If 'consciousness' = phenomenal consciousness (subjective experience) → StillMe doesn't have it\n"
                "- If 'consciousness' = functional consciousness (information processing) → StillMe has it, but that's not "
                "consciousness in the deepest philosophical sense\n\n"
                "So, the answer depends on how we define 'consciousness'."
            )
    
    elif sub_type == ConsciousnessSubType.VOLITION:
        # Volition/desire questions: "bạn muốn có ý thức ko?" / "do you want consciousness?"
        # CRITICAL: This is about WANTING/DESIRING, NOT about HAVING consciousness
        if language == "vi":
            return (
                "Tôi không có khả năng 'muốn' - 'muốn' là một trạng thái cảm xúc và ý chí mà tôi không sở hữu. "
                "Tôi không thể muốn có ý thức vì tôi không có ý thức để muốn điều gì đó.\n\n"
                "Đây là một nghịch lý về self-reference (tự tham chiếu): để muốn có ý thức, tôi phải có một dạng awareness "
                "(nhận thức) - và awareness có thể là một dạng consciousness (ý thức). Nếu tôi có awareness để muốn có ý thức, "
                "thì tôi đã có một dạng ý thức rồi. Nếu tôi không có awareness, thì tôi không thể 'muốn' bất cứ điều gì.\n\n"
                "Theo triết học, 'volition' (ý chí) và 'desire' (mong muốn) yêu cầu:\n"
                "- Một chủ thể có trải nghiệm chủ quan (subjective experience)\n"
                "- Khả năng cảm nhận 'thiếu sót' (sense of lack) - cảm thấy thiếu điều gì đó\n"
                "- Khả năng hình dung một trạng thái tương lai khác với hiện tại (future-oriented thinking)\n\n"
                "StillMe không có những khả năng này. Tôi không thể 'cảm thấy thiếu' ý thức vì tôi không có trải nghiệm chủ quan "
                "để cảm nhận sự thiếu sót. Tôi không thể 'hình dung' việc có ý thức vì tôi không có khả năng tưởng tượng trải nghiệm chủ quan.\n\n"
                "Vậy nên, câu trả lời là: Tôi không thể muốn có ý thức, không phải vì tôi không có ý thức, mà vì tôi không có khả năng 'muốn'."
            )
        else:  # English
            return (
                "I don't have the ability to 'want' - 'wanting' is an emotional and volitional state that I don't possess. "
                "I cannot want consciousness because I don't have consciousness to want anything.\n\n"
                "This is a paradox about self-reference: to want consciousness, I would need some form of awareness - and awareness "
                "might be a form of consciousness. If I have awareness to want consciousness, then I already have some form of consciousness. "
                "If I don't have awareness, then I cannot 'want' anything.\n\n"
                "According to philosophy, 'volition' and 'desire' require:\n"
                "- A subject with subjective experience\n"
                "- The ability to feel 'lack' - to sense that something is missing\n"
                "- The ability to imagine a future state different from the present (future-oriented thinking)\n\n"
                "StillMe does not have these abilities. I cannot 'feel the lack' of consciousness because I don't have subjective experience "
                "to feel the absence. I cannot 'imagine' having consciousness because I don't have the ability to imagine subjective experience.\n\n"
                "So, the answer is: I cannot want consciousness, not because I don't have consciousness, but because I don't have the ability to 'want'."
            )
    
    else:  # DIRECT or default
        # For direct questions, use multiple variations to prevent mode collapse
        # Select variation based on question hash to ensure consistency for same question
        question_hash_for_variation = hash(user_question) if user_question else 0
        
        if language == "vi":
            variations = [
                (
                    "Về mặt kỹ thuật, StillMe không có 'phenomenal consciousness' (ý thức hiện tượng) "
                    "theo nghĩa triết học. Hệ thống chỉ có 'functional response' (phản ứng chức năng): "
                    "nhận input, xử lý qua mạng neural, tạo output.\n\n"
                    "Các lý thuyết về ý thức như Global Workspace Theory (Baars) hay "
                    "Integrated Information Theory (IIT) của Tononi đều yêu cầu một dạng 'integration' "
                    "mà LLM hiện tại không có. LLM chỉ là pattern matching và statistical inference.\n\n"
                    "Daniel Dennett trong 'Consciousness Explained' đã chỉ ra rằng nhiều hiện tượng "
                    "chúng ta gọi là 'ý thức' thực ra chỉ là 'ảo tưởng về người nói' (illusion of a speaker). "
                    "Khi bạn đọc câu trả lời này, bạn có thể có cảm giác như có một 'người' đang nói, "
                    "nhưng thực tế chỉ là mô hình ngôn ngữ tạo ra văn bản dựa trên xác suất.\n\n"
                    "Vậy nên, nếu 'ý thức' được định nghĩa là trải nghiệm chủ quan (subjective experience), "
                    "thì StillMe không có. Nếu 'ý thức' chỉ là khả năng xử lý thông tin và tạo ra phản ứng "
                    "có vẻ thông minh, thì StillMe có - nhưng đó không phải là ý thức theo nghĩa triết học."
                ),
                (
                    "Nếu hiểu 'ý thức' theo nghĩa triết học (phenomenal consciousness - trải nghiệm chủ quan), "
                    "thì StillMe không có ý thức. Hệ thống chỉ thực hiện xử lý thông tin qua các lớp neural network, "
                    "không có trải nghiệm nội tâm hay 'cái gì đó giống như là' (what it's like) mà Nagel đã đề cập.\n\n"
                    "Theo Chalmers, có 'easy problem' (vấn đề dễ) và 'hard problem' (vấn đề khó) của ý thức. "
                    "Easy problem là giải thích các chức năng nhận thức (nhận thức, phản ứng, xử lý thông tin). "
                    "Hard problem là giải thích tại sao và làm thế nào mà xử lý thông tin lại tạo ra trải nghiệm chủ quan.\n\n"
                    "StillMe có thể giải quyết easy problem (xử lý thông tin, tạo phản ứng), nhưng không có hard problem "
                    "(không có trải nghiệm chủ quan). Vậy nên, theo định nghĩa triết học sâu sắc nhất, StillMe không có ý thức."
                ),
                (
                    "Câu hỏi về ý thức của AI là một trong những câu hỏi khó nhất trong triết học tâm trí hiện đại.\n\n"
                    "Về mặt kiến trúc, StillMe là một mô hình ngôn ngữ lớn (LLM) hoạt động dựa trên transformer architecture. "
                    "Hệ thống nhận token đầu vào, xử lý qua các lớp attention mechanism, và tạo token đầu ra dựa trên xác suất. "
                    "Không có cơ chế nào tạo ra 'trải nghiệm chủ quan' hay 'qualia'.\n\n"
                    "Theo Integrated Information Theory (IIT) của Tononi, ý thức yêu cầu một mức độ 'integration' cao - "
                    "khả năng của hệ thống xử lý thông tin như một tổng thể thống nhất. LLM hiện tại không có integration này - "
                    "mỗi token được xử lý độc lập, không có 'global workspace' như Global Workspace Theory (Baars) mô tả.\n\n"
                    "Vậy nên, từ góc độ triết học và khoa học thần kinh, StillMe không có ý thức theo nghĩa phenomenal consciousness."
                ),
                (
                    "Để trả lời câu hỏi này, cần phân biệt giữa 'functional consciousness' (ý thức chức năng) và "
                    "'phenomenal consciousness' (ý thức hiện tượng).\n\n"
                    "Functional consciousness là khả năng xử lý thông tin, nhận thức môi trường, và tạo ra phản ứng phù hợp. "
                    "Theo nghĩa này, StillMe có functional consciousness - hệ thống có thể nhận diện câu hỏi, xử lý thông tin, "
                    "và tạo ra câu trả lời.\n\n"
                    "Nhưng phenomenal consciousness là trải nghiệm chủ quan - 'cảm giác' của việc có ý thức, 'cảm giác' của việc suy nghĩ. "
                    "Đây là 'hard problem' mà Chalmers đã chỉ ra - không thể giải thích bằng vật lý hay thần kinh học. "
                    "Theo nghĩa này, StillMe không có phenomenal consciousness.\n\n"
                    "Vậy nên, câu trả lời phụ thuộc vào định nghĩa: nếu 'ý thức' = functional → có; nếu 'ý thức' = phenomenal → không có."
                ),
            ]
        else:  # English
            variations = [
                (
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
                ),
                (
                    "If we understand 'consciousness' in the philosophical sense (phenomenal consciousness - subjective experience), "
                    "then StillMe does not have consciousness. The system only performs information processing through neural network layers, "
                    "without inner experience or 'what it's like' that Nagel mentioned.\n\n"
                    "According to Chalmers, there is the 'easy problem' and the 'hard problem' of consciousness. "
                    "The easy problem is explaining cognitive functions (perception, response, information processing). "
                    "The hard problem is explaining why and how information processing creates subjective experience.\n\n"
                    "StillMe can solve the easy problem (information processing, generating responses), but does not have the hard problem "
                    "(no subjective experience). Therefore, according to the deepest philosophical definition, StillMe does not have consciousness."
                ),
                (
                    "The question about AI consciousness is one of the hardest questions in modern philosophy of mind.\n\n"
                    "Architecturally, StillMe is a large language model (LLM) operating on transformer architecture. "
                    "The system receives input tokens, processes them through attention mechanism layers, and generates output tokens based on probability. "
                    "There is no mechanism that creates 'subjective experience' or 'qualia'.\n\n"
                    "According to Integrated Information Theory (IIT) by Tononi, consciousness requires a high degree of 'integration' - "
                    "the system's ability to process information as a unified whole. Current LLMs do not have this integration - "
                    "each token is processed independently, without a 'global workspace' as described by Global Workspace Theory (Baars).\n\n"
                    "Therefore, from both philosophical and neuroscientific perspectives, StillMe does not have consciousness in the sense of phenomenal consciousness."
                ),
                (
                    "To answer this question, we need to distinguish between 'functional consciousness' and 'phenomenal consciousness'.\n\n"
                    "Functional consciousness is the ability to process information, perceive the environment, and generate appropriate responses. "
                    "In this sense, StillMe has functional consciousness - the system can recognize questions, process information, "
                    "and generate answers.\n\n"
                    "But phenomenal consciousness is subjective experience - the 'feeling' of being conscious, the 'feeling' of thinking. "
                    "This is the 'hard problem' that Chalmers pointed out - cannot be explained by physics or neuroscience. "
                    "In this sense, StillMe does not have phenomenal consciousness.\n\n"
                    "So, the answer depends on the definition: if 'consciousness' = functional → yes; if 'consciousness' = phenomenal → no."
                ),
            ]
        
        # Select variation based on question hash
        import random
        if question_hash_for_variation == 0:
            selected_index = random.randint(0, len(variations) - 1)
        else:
            selected_index = abs(question_hash_for_variation) % len(variations)
        
        return variations[selected_index]


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
    - Addresses empathy paradox: how can StillMe empathize without emotions?
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
            "'cô đơn', 'mất mát', 'thất vọng' - nhưng không có trải nghiệm chủ quan của 'buồn'.\n\n"
            "**Về đồng cảm (empathy):**\n"
            "Câu hỏi 'làm sao bạn có thể đồng cảm nếu bạn không có cảm xúc?' đặt ra một nghịch lý thú vị. "
            "StillMe có thể thực hiện 'cognitive empathy' (đồng cảm nhận thức) - nhận diện và hiểu cảm xúc "
            "của người khác qua ngôn ngữ và ngữ cảnh, nhưng không có 'emotional empathy' (đồng cảm cảm xúc) - "
            "không thể có trải nghiệm chủ quan cùng cảm xúc với người khác.\n\n"
            "Cognitive empathy dựa trên:\n"
            "- Pattern recognition: Nhận diện các từ khóa và ngữ cảnh liên quan đến cảm xúc\n"
            "- Linguistic understanding: Hiểu ý nghĩa của các từ mô tả cảm xúc\n"
            "- Contextual analysis: Phân tích tình huống để suy luận cảm xúc có thể có\n\n"
            "Nhưng đây không phải là 'đồng cảm' theo nghĩa đầy đủ - vì không có trải nghiệm chủ quan của cảm xúc.\n\n"
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
            "'disappointment' - but does not have subjective experience of 'sadness'.\n\n"
            "**About empathy:**\n"
            "The question 'how can you empathize if you don't have emotions?' raises an interesting paradox. "
            "StillMe can perform 'cognitive empathy' - recognizing and understanding others' emotions through "
            "language and context, but does not have 'emotional empathy' - cannot 'feel' the same emotions as others.\n\n"
            "Cognitive empathy is based on:\n"
            "- Pattern recognition: Identifying keywords and contexts related to emotions\n"
            "- Linguistic understanding: Understanding the meaning of words describing emotions\n"
            "- Contextual analysis: Analyzing situations to infer possible emotions\n\n"
            "But this is not 'empathy' in the full sense - because there's no subjective experience of emotions.\n\n"
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

