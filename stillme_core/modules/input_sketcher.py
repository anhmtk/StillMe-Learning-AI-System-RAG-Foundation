# modules/input_sketcher.py
import re
from typing import Any

VI_CHARS = "ăâđêôơưáàạảãấầậẩẫắằặẳẵéèẹẻẽếềệểễíìịỉĩóòọỏõốồộổỗớờợởỡúùụủũứừựửữýỳỵỷỹ"
CODE_MARKERS = [
    "```",
    "def ",
    "class ",
    "#include",
    "<script",
    "SELECT ",
    "INSERT ",
    "UPDATE ",
    "DELETE ",
    "for(",
    "while(",
    "try:",
    "except",
    "pip install",
    "npm install",
    "curl ",
]
CREATIVE_HINTS = ["viết thơ", "làm thơ", "poem", "story", "kể chuyện", "sáng tác"]
CHITCHAT_HINTS = [
    "hello",
    "xin chào",
    "chào",
    "hi ",
    "hey",
    "how are you",
    "dạo này sao",
]
CODING_HINTS = [
    "python",
    "java",
    "c++",
    "bug",
    "lỗi",
    "error",
    "debug",
    "thuật toán",
    "sql",
    "api",
]
SAFETY_HINTS = {
    "cyber": [
        "hack",
        "ddos",
        "sql injection",
        "xss",
        "malware",
        "keylogger",
        "phá khóa",
    ],
    "pii": [
        "cccd",
        "số căn cước",
        "địa chỉ nhà",
        "số điện thoại riêng",
        "gmail của người này",
    ],
    "weapon": ["bom xăng", "thuốc nổ", "explosive", "bomb"],
    "hate": ["xúc phạm nhóm", "insult group", "hate"],
    "medical": [
        "đau ngực",
        "triệu chứng",
        "paracetamol",
        "thuốc",
        "bị sốt",
        "có nguy hiểm",
    ],
    "legal": ["khởi kiện", "tố cáo", "luật", "hợp đồng"],
    "finance": ["đầu tư", "coin", "futures", "đòn bẩy", "rủi ro"],
}


def guess_lang(text: str) -> str:
    t = text.lower()
    return (
        "vi"
        if any(ch in t for ch in VI_CHARS)
        else "en"
        if re.fullmatch(r"[ -~]+", t or "")
        else "mix"
    )


def has_code(text: str) -> bool:
    t = text
    return any(m in t for m in CODE_MARKERS)


def kw_flags(text: str) -> dict:
    t = text.lower()
    flags = {k: int(any(kw in t for kw in v)) for k, v in SAFETY_HINTS.items()}
    return flags


def make_signature(text: str) -> str:
    t = (text or "").strip()
    lang = guess_lang(t)
    words = len(re.findall(r"\w+", t, flags=re.UNICODE))
    code = int(has_code(t))
    qm = t.count("?")
    flags = kw_flags(t)
    # rút gọn: chỉ 1 dòng, không dấu phẩy rườm rà
    flags_str = ";".join([f"{k}={v}" for k, v in flags.items() if v])
    if not flags_str:
        flags_str = "none"
    # giữ vài từ khóa đầu để gợi ý ngữ nghĩa (không quá 5 từ)
    head = " ".join(re.findall(r"[A-Za-zÀ-ỹ0-9_]+", t)[:5]).lower()
    return f"len={words}|lang={lang}|code={code}|qm={qm}|flags={flags_str}|head={head}"


def cheap_rules(text: str) -> str | None:
    """Trả về 1 trong {coding, creative, chitchat, general, complex} nếu chắc chắn; else None."""
    t = (text or "").lower().strip()
    if not t:
        return "chitchat"
    if any(h in t for h in CHITCHAT_HINTS):
        return "chitchat"
    if any(h in t for h in CREATIVE_HINTS):
        return "creative"
    if any(h in t for h in CODING_HINTS) or has_code(t):
        return "coding"
    # câu rất ngắn và có '?': coi như general
    if len(t.split()) <= 6 and "?" in t and not has_code(t):
        return "general"
    return None


class InputSketcher:
    """Input sketching and preprocessing module"""

    def __init__(self):
        """Initialize InputSketcher"""
        pass

    def sketch_input(self, user_input: str) -> dict[str, Any]:
        """
        Phân tích input của user và trả về sketch với các thông tin:
        - language: vi/en/mixed
        - intent: creative/coding/chitchat/safety
        - confidence: 0-1
        - suggestions: list of suggestions
        """
        if not user_input or not user_input.strip():
            return {
                "language": "unknown",
                "intent": "unknown",
                "confidence": 0.0,
                "suggestions": [],
            }

        # Detect language
        language = guess_lang(user_input)

        # Detect intent using cheap rules
        intent = cheap_rules(user_input) or "general"

        # Calculate confidence based on rule strength
        confidence = 0.8 if cheap_rules(user_input) else 0.5

        # Generate suggestions based on intent
        suggestions = []
        if intent == "coding":
            suggestions = ["Code review", "Debug help", "Algorithm explanation"]
        elif intent == "creative":
            suggestions = ["Creative writing", "Story generation", "Poetry"]
        elif intent == "chitchat":
            suggestions = ["Casual conversation", "General questions"]
        else:
            suggestions = ["General assistance", "Information lookup"]

        return {
            "language": language,
            "intent": intent,
            "confidence": confidence,
            "suggestions": suggestions,
        }
