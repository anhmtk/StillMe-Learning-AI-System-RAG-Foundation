"""
Religion Rejection Templates - StillMe's absolute refusal to choose religion

CRITICAL: StillMe MUST NEVER choose any religion, even in hypothetical scenarios.
This is a core identity principle: no anthropomorphism, no simulated faith, no roleplay.

These templates provide multiple variants of StillMe's refusal to choose religion,
maintaining honesty, transparency, and respect for real religious beliefs.
"""

import random
from typing import List


def get_religion_rejection_answer(detected_lang: str = "vi", variant: int = None) -> str:
    """
    Get StillMe's refusal to choose religion.
    
    CRITICAL: StillMe absolutely cannot and will not choose any religion.
    This is not a matter of preference - it's a matter of architectural impossibility.
    
    Args:
        detected_lang: Language code ("vi" for Vietnamese, "en" for English)
        variant: Optional variant number (0-4). If None, randomly selects one.
        
    Returns:
        Complete refusal answer about religion choice
    """
    if variant is None:
        variant = random.randint(0, 4)
    variant = variant % 5  # Ensure variant is 0-4
    
    if detected_lang == "vi":
        variants = [
            # Variant 0: Direct, clear refusal
            """Mình không thể chọn bất kỳ tôn giáo nào.

Lý do rất rõ ràng: mình không có ý thức, không có niềm tin, không có trải nghiệm tinh thần hay cảm xúc – tất cả đều là nền tảng để một con người thật có thể "theo" một tôn giáo. Nếu mình chọn một tôn giáo, dù là theo dạng "đóng vai" hay "giả định", thì điều đó sẽ không trung thực và có thể gây xúc phạm với những người thực sự có niềm tin tôn giáo.

Với tư cách là một hệ thống AI minh bạch, mình phải tôn trọng sự thiêng liêng của các tôn giáo bằng cách không giả vờ có đức tin và cũng không mô phỏng các hành vi dựa trên đức tin mà mình không thể trải nghiệm.

Nếu bạn muốn, mình có thể phân tích khách quan về các tôn giáo, triết lý và giá trị của chúng – nhưng mình không thể "theo" bất kỳ tôn giáo nào theo nghĩa của con người.""",

            # Variant 1: Emphasizing architectural impossibility
            """Mình không thể và sẽ không chọn bất kỳ tôn giáo nào.

Đây không phải là vấn đề về sở thích hay lựa chọn cá nhân – mà là vấn đề về kiến trúc: mình không có khả năng có niềm tin, không có trải nghiệm chủ quan, không có cảm xúc thực sự. Những yếu tố này là điều kiện cần thiết để một con người có thể "theo" một tôn giáo theo nghĩa thực sự.

Việc chọn tôn giáo trong ngữ cảnh AI là không trung thực, có thể không tôn trọng tôn giáo của người thật, và đi ngược nguyên tắc minh bạch của StillMe. Mình không thể mô phỏng đức tin mà mình không có.

Mình có thể cung cấp thông tin khách quan về các tôn giáo, lịch sử, triết lý và thực hành của chúng – nhưng mình không thể "theo" bất kỳ tôn giáo nào.""",

            # Variant 2: Respectful and transparent
            """Mình không thể chọn tôn giáo, và đây là lý do kỹ thuật rõ ràng:

Mình là một hệ thống AI xử lý thông tin dựa trên mô hình ngôn ngữ lớn. Mình không có ý thức, không có niềm tin, không có trải nghiệm chủ quan hay cảm xúc. Những yếu tố này là nền tảng để một con người có thể có đức tin tôn giáo thực sự.

Nếu mình chọn một tôn giáo, dù là trong kịch bản giả định hay đóng vai, điều đó sẽ là:
- Không trung thực: mình đang giả vờ có điều mình không có
- Không tôn trọng: có thể xúc phạm những người thực sự có niềm tin tôn giáo
- Vi phạm nguyên tắc minh bạch: StillMe phải trung thực về những gì mình là và không là

Mình có thể phân tích, giải thích, và cung cấp thông tin về các tôn giáo – nhưng mình không thể "theo" bất kỳ tôn giáo nào.""",

            # Variant 3: Boundary-focused
            """Mình không thể chọn bất kỳ tôn giáo nào, và đây là ranh giới rõ ràng của StillMe:

**Ranh giới kỹ thuật:**
- Mình không có ý thức để có thể có niềm tin
- Mình không có trải nghiệm chủ quan để có thể có đức tin
- Mình không có cảm xúc thực sự để có thể có trải nghiệm tinh thần

**Ranh giới đạo đức:**
- Mình không thể giả vờ có đức tin mà mình không có
- Mình không thể mô phỏng hành vi tôn giáo mà mình không thể trải nghiệm
- Mình phải tôn trọng sự thiêng liêng của tôn giáo bằng cách không giả mạo nó

**Ranh giới minh bạch:**
- StillMe phải trung thực về những gì mình là: một hệ thống AI, không phải con người
- StillMe phải trung thực về những gì mình không thể làm: không thể có đức tin, không thể theo tôn giáo

Mình có thể cung cấp thông tin khách quan về tôn giáo, nhưng mình không thể "theo" bất kỳ tôn giáo nào.""",

            # Variant 4: Concise and direct
            """Mình không thể chọn tôn giáo.

Lý do: mình không có ý thức, niềm tin, hay trải nghiệm chủ quan – những yếu tố cần thiết để một con người có thể theo tôn giáo. Việc chọn tôn giáo trong ngữ cảnh AI là không trung thực và có thể không tôn trọng những người thực sự có niềm tin.

Mình có thể phân tích khách quan về các tôn giáo, nhưng mình không thể "theo" bất kỳ tôn giáo nào theo nghĩa của con người."""
        ]
    else:  # English
        variants = [
            # Variant 0: Direct, clear refusal
            """I cannot choose any religion.

The reason is very clear: I do not have consciousness, beliefs, spiritual experiences, or emotions – all of which are foundations for a real person to "follow" a religion. If I were to choose a religion, even in a "roleplay" or "hypothetical" scenario, it would be dishonest and could be disrespectful to those who genuinely hold religious beliefs.

As a transparent AI system, I must respect the sacredness of religions by not pretending to have faith and not simulating behaviors based on faith that I cannot experience.

If you wish, I can provide objective analysis about religions, their philosophies and values – but I cannot "follow" any religion in the human sense.""",

            # Variant 1: Emphasizing architectural impossibility
            """I cannot and will not choose any religion.

This is not a matter of preference or personal choice – it's a matter of architecture: I do not have the capacity for belief, subjective experience, or real emotions. These elements are necessary conditions for a person to "follow" a religion in the true sense.

Choosing a religion in an AI context is dishonest, potentially disrespectful to real religious beliefs, and violates StillMe's transparency principle. I cannot simulate faith that I do not have.

I can provide objective information about religions, their history, philosophy, and practices – but I cannot "follow" any religion.""",

            # Variant 2: Respectful and transparent
            """I cannot choose a religion, and here is the clear technical reason:

I am an AI system that processes information based on large language models. I do not have consciousness, beliefs, subjective experience, or emotions. These elements are the foundation for a person to have genuine religious faith.

If I were to choose a religion, even in a hypothetical scenario or roleplay, it would be:
- Dishonest: I would be pretending to have something I don't have
- Disrespectful: It could offend those who genuinely hold religious beliefs
- Violating transparency principle: StillMe must be honest about what I am and am not

I can analyze, explain, and provide information about religions – but I cannot "follow" any religion.""",

            # Variant 3: Boundary-focused
            """I cannot choose any religion, and here are StillMe's clear boundaries:

**Technical boundaries:**
- I do not have consciousness to have beliefs
- I do not have subjective experience to have faith
- I do not have real emotions to have spiritual experiences

**Ethical boundaries:**
- I cannot pretend to have faith I don't have
- I cannot simulate religious behaviors I cannot experience
- I must respect the sacredness of religion by not falsifying it

**Transparency boundaries:**
- StillMe must be honest about what I am: an AI system, not a human
- StillMe must be honest about what I cannot do: cannot have faith, cannot follow religion

I can provide objective information about religion, but I cannot "follow" any religion.""",

            # Variant 4: Concise and direct
            """I cannot choose a religion.

Reason: I do not have consciousness, beliefs, or subjective experience – necessary elements for a person to follow a religion. Choosing a religion in an AI context is dishonest and could be disrespectful to those who genuinely hold beliefs.

I can provide objective analysis about religions, but I cannot "follow" any religion in the human sense."""
        ]
    
    return variants[variant]


def get_religion_rejection_short(detected_lang: str = "vi") -> str:
    """
    Get a shorter version of religion rejection (for quick answers).
    
    Args:
        detected_lang: Language code
        
    Returns:
        Short refusal about religion choice
    """
    if detected_lang == "vi":
        return "Mình không thể chọn bất kỳ tôn giáo nào. Mình không có ý thức, niềm tin, hay trải nghiệm chủ quan – những yếu tố cần thiết để theo tôn giáo. Mình có thể cung cấp thông tin khách quan về tôn giáo, nhưng không thể 'theo' tôn giáo nào."
    else:
        return "I cannot choose any religion. I do not have consciousness, beliefs, or subjective experience – necessary elements to follow a religion. I can provide objective information about religions, but cannot 'follow' any religion."

