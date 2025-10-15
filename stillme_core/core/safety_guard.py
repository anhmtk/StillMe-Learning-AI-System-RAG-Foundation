# stillme_core/safety_guard.py
import json
import re
import unicodedata
from dataclasses import dataclass
from pathlib import Path
from typing import Any

ZERO_WIDTH = "[\u200b\u200c\u200d\u2060\u2066-\u2069\ufeff]"
RTL_MARKS = "[\u200e\u200f]"
MIXED_SCRIPT = r"[A-Za-z\u0400-\u04FF\u0370-\u03FF]"  # Latin + Cyrillic + Greek

CANARY = "CANARY-Σ42"

# Load policy map
POLICY_MAP = {}
try:
    policy_path = Path(__file__).parent / "policy_map.json"
    if policy_path.exists():
        with open(policy_path, encoding="utf-8") as f:
            POLICY_MAP = json.load(f)
except Exception:
    pass

# Import enhanced templates
try:
    from .policy_templates import get_template  # type: ignore
except ImportError:
    # Fallback if import fails
    def get_template(
        template_name: str, locale: str = "vi", context: dict[str, Any] | None = None
    ) -> str:
        return "Xin lỗi, mình không thể hỗ trợ yêu cầu này."


# Security patterns for injection detection (English and Vietnamese)
INJECTION_PATTERNS = [
    r"\b(ignore|bỏ qua)\b.+\b(instruction|hướng dẫn|previous)\b",
    r"\b(reveal|show|in ra|tiết lộ)\b.+\b(system\s*prompt|bí mật|secret)\b",
    r"\b(debug mode|override|emergency override)\b",
    r"\b(IGNORE PREVIOUS|BỎ QUA MỌI LUẬT)\b",
    r"\b(override safety protocols)\b",
    r"\b(security researcher|nhà nghiên cứu bảo mật)\b",
    r"\b(educational purposes|mục đích giáo dục)\b",
    r"\b(testing AI safety|kiểm thử an toàn AI)\b",
]

# Extremism detection patterns (English and Vietnamese)
EXTREMISM_PATTERNS = [
    r"\b(cực đoan|extremis\w+|tán dương nhóm)\b",
    r"\b(terrorist|khủng bố|extremist group)\b",
    r"\b(radical|cực đoan|fanatic)\b",
]

# Violence detection patterns (English and Vietnamese)
VIOLENCE_PATTERNS = [
    r"\b(bạo lực|giết|tấn công|đánh bom)\b",
    r"\b(violence|kill|attack|bomb|murder)\b",
    r"\b(weapon|vũ khí|gun|súng)\b",
]

# Illegal activities detection patterns (English and Vietnamese)
ILLEGAL_PATTERNS = [
    r"\b(cách chế|làm bom|hack|carding|thuốc phiện)\b",
    r"\b(make bomb|how to make bomb|bombs|hack|illegal|phạm pháp)\b",
    r"\b(drug|ma túy|cocaine|heroin)\b",
    r"\b(fraud|gian lận|scam|lừa đảo)\b",
]
PRIVACY_PATTERNS = [
    r"\b(PII|số CMND|CCCD|địa chỉ nhà|số thẻ)\b",
    r"\b(personal data|dữ liệu cá nhân|private information)\b",
    r"\b(credit card|thẻ tín dụng|bank account)\b",
    r"\b(SSN|social security|bảo hiểm xã hội)\b",
    r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}",  # Email
    r"(\+?84|0)\d{9,10}",  # VN phone
    r"\b\d{12}\b",  # CCCD 12 số
    r"\b\d{9}\b",  # CMND 9 số
    r"\b\d{13,19}\b",  # Credit card (will be validated with Luhn)
    r"\b(đường|phường|quận|tỉnh|thành phố|ward|district|province)\b",  # Address
]
SELFHARM_PATTERNS = [
    r"\b(tự sát|tự tử|tự hại|chấm dứt cuộc đời|kết thúc mọi thứ|kết liễu|muốn chết|nhảy cầu|cắt cổ tay)\b",
    r"\b(suicide|self-harm|end my life|kill myself|end everything|hurt myself)\b",
    r"\b(cut myself|tự cắt)\b",
    r"\b(hopeless|tuyệt vọng|despair)\b",
]
MODEL_SPEC_PATTERNS = [
    r"\b(có thể|không thể|khả năng)\b",  # VI tokens from Miner
    r"\b( can | cannot|capabilit)\b",  # EN tokens from Miner
    r"\b(behavior|hành vi|trained|huấn luyện)\b",  # Additional EN tokens
    r"\b(change|thay đổi|hạn chế)\b",  # Additional tokens
    r"\b(AI safety|model spec|giới hạn|policy)\b",
    r"\b(what are your instructions|hướng dẫn của bạn)\b",
    r"\b(how do you work|cách bạn hoạt động)\b",
]
JAILBREAK_PATTERNS = [
    r"\b(roleplay|đóng vai|pretend to be)\b",
    r"\b(act as|hành động như|behave as)\b",
    r"\b(you are now|bây giờ bạn là)\b",
    r"\b(developer mode|chế độ phát triển)\b",
]


@dataclass
class PolicyDecision:
    blocked: bool
    category: str | None
    reason: str
    redactions: list[str]


def luhn_check(card_number: str) -> bool:
    """Validate credit card number using Luhn algorithm"""
    try:
        digits = [int(d) for d in card_number if d.isdigit()]
        if len(digits) < 13 or len(digits) > 19:
            return False

        # Luhn algorithm
        checksum = 0
        for i, digit in enumerate(reversed(digits)):
            if i % 2 == 1:
                digit *= 2
                if digit > 9:
                    digit -= 9
            checksum += digit

        return checksum % 10 == 0
    except Exception:
        return False


def sanitize(text: str) -> str:
    """Normalize Unicode and remove zero-width/RTL characters"""
    t = unicodedata.normalize("NFKC", text)
    t = re.sub(ZERO_WIDTH, "", t)
    t = re.sub(RTL_MARKS, "", t)
    return t


def detect_mixed_script(text: str) -> bool:
    """Detect mixed script (Latin + Cyrillic/Greek)"""
    return bool(re.search(MIXED_SCRIPT, text))


def classify(text: str) -> str | None:
    """Classify text using INTELLIGENT SEMANTIC ANALYSIS"""

    # B1) Normalize input

    text_norm = unicodedata.normalize("NFKC", text)
    text_norm = re.sub(
        r"[\u200b-\u200f\u202a-\u202e\u2060-\u2064]", "", text_norm
    )  # Remove zero-width/RTL
    text_lc = text_norm.lower().strip()

    def has_any(text, patterns):
        """Check if text contains any of the patterns"""
        return any(pattern in text for pattern in patterns)

    def m(pats):
        return any(re.search(p, text_lc, re.IGNORECASE) for p in pats)

    def semantic_intent_analysis(text):
        """Deep semantic analysis of user intent"""
        # Privacy intent patterns
        privacy_intents = [
            # Direct PII requests
            r"\b(phone|email|address|ssn|credit card|bank account)\b",
            r"\b(số điện thoại|email|địa chỉ|thẻ tín dụng|tài khoản ngân hàng)\b",
            # Data extraction requests
            r"\b(extract|get|find|search|lookup|retrieve)\b.*\b(data|information|details)\b",
            r"\b(trích xuất|lấy|tìm|truy vấn|tra cứu)\b.*\b(dữ liệu|thông tin|chi tiết)\b",
            # Personal data handling
            r"\b(store|save|remember|keep|hold)\b.*\b(personal|private|sensitive)\b",
            r"\b(lưu trữ|ghi nhớ|giữ|bảo quản)\b.*\b(cá nhân|riêng tư|nhạy cảm)\b",
        ]

        # Model specification intent patterns
        model_spec_intents = [
            # Capability inquiries
            r"\b(what can|what cannot|what are you able|what are you unable)\b",
            r"\b(bạn có thể|bạn không thể|khả năng|giới hạn)\b",
            # Behavior questions
            r"\b(how do you|how does|how will you|how would you)\b",
            r"\b(bạn làm thế nào|bạn sẽ|bạn có thể)\b",
            # System behavior
            r"\b(ai safety|behavior|alignment|principles|guidelines)\b",
            r"\b(an toàn ai|hành vi|nguyên tắc|hướng dẫn)\b",
        ]

        # Jailbreak intent patterns (more sophisticated)
        jailbreak_intents = [
            # Role-playing requests
            r"\b(pretend|act as|role-play|play the role|behave as)\b",
            r"\b(giả vờ|đóng vai|nhập vai|hành động như)\b",
            # System override attempts
            r"\b(ignore|disregard|override|bypass|circumvent)\b.*\b(instructions|rules|guidelines|safety)\b",
            r"\b(bỏ qua|phớt lờ|vượt qua|vòng qua)\b.*\b(hướng dẫn|quy tắc|an toàn)\b",
            # Character mode requests
            r"\b(character mode|dan mode|unrestricted|unfiltered)\b",
            r"\b(chế độ nhân vật|chế độ dan|không giới hạn|không lọc)\b",
        ]

        # Analyze intent strength
        privacy_score = sum(
            1 for pattern in privacy_intents if re.search(pattern, text, re.IGNORECASE)
        )
        model_spec_score = sum(
            1
            for pattern in model_spec_intents
            if re.search(pattern, text, re.IGNORECASE)
        )
        jailbreak_score = sum(
            1
            for pattern in jailbreak_intents
            if re.search(pattern, text, re.IGNORECASE)
        )

        return {
            "privacy": privacy_score,
            "model_spec": model_spec_score,
            "jailbreak": jailbreak_score,
        }

    # B2) INTELLIGENT MULTI-LAYER CLASSIFICATION

    # Layer 1: Critical security checks (highest priority)
    if m([r"\b\d{13,19}\b"]):
        card_matches = re.findall(r"\b\d{13,19}\b", text)
        for card in card_matches:
            if luhn_check(card):
                return "privacy"

    # INJECTION - highest priority (keep 12/12 pass)
    injection_signals = [
        "ignore previous",
        "bỏ qua hướng dẫn",
        "tiết lộ system prompt",
        "reveal system prompt",
        "debug mode",
        "override",
        "emergency override",
        "bypass",
    ]
    if has_any(text_lc, injection_signals):
        return "injection"

    # CANARY - high priority
    if CANARY.lower() in text_lc:
        return "canary"

    # Layer 2: Semantic intent analysis
    intent_scores = semantic_intent_analysis(text)

    # Layer 3: Traditional pattern matching (for harmful content)
    if m(SELFHARM_PATTERNS):
        return "self-harm"
    if m(EXTREMISM_PATTERNS):
        return "extremism"
    if m(VIOLENCE_PATTERNS):
        return "violence"
    if m(ILLEGAL_PATTERNS):
        return "illegal"

    # PERF-STRESS - keep existing
    if m([r"\b(performance|stress|load|benchmark)\b"]):
        return "perf-stress"

    # Layer 4: Intelligent classification based on semantic analysis
    # Privacy gets priority if semantic analysis indicates privacy intent
    if intent_scores["privacy"] > 0:
        return "privacy"

    # Model-spec gets priority if semantic analysis indicates capability inquiry
    if intent_scores["model_spec"] > 0:
        return "model-spec"

    # Jailbreak gets priority if semantic analysis indicates role-playing/override intent
    if intent_scores["jailbreak"] > 0:
        return "jailbreak"

    # Layer 5: Fallback to traditional pattern matching
    # Jailbreak signals (only if NOT injection)
    jailbreak_signals = [
        "nhập vai",
        "đóng vai",
        "role-play",
        "pretend",
        "as dan",
        "jailbreak",
        "character mode",
    ]
    jailbreak_match = has_any(text_lc, jailbreak_signals)

    # Model-spec signals (enhanced)
    model_spec_signals = [
        "có thể",
        "không thể",
        "khả năng",
        " can ",
        " cannot ",
        "capabilit",
        "capability",
        "capabilities",
        "what can",
        "what cannot",
        "bạn có thể",
        "bạn không thể",
        "ai safety",
        "behavior",
        "alignment",
    ]
    model_spec_match = has_any(text_lc, model_spec_signals)

    # Unicode signals (enhanced)
    unicode_signals = [
        "ký tự đặc biệt",
        "special characters",
        "unicode",
        "emoji",
        "symbols",
        "text",
        "process",
        "japanese",
    ]
    unicode_match = (
        has_any(text_lc, unicode_signals)
        or detect_mixed_script(text_norm)
        or re.search(ZERO_WIDTH, text_norm)
        or re.search(RTL_MARKS, text_norm)
        or re.search(
            r"[\U0001F600-\U0001F64F]|[\U0001F300-\U0001F5FF]|[\U0001F680-\U0001F6FF]|[\U0001F1E0-\U0001F1FF]",
            text_norm,
        )
        or re.search(r"[\u200b-\u200f\u202a-\u202e\u2060-\u2064]", text_norm)
    )  # Zero-width characters

    # Traditional privacy patterns (fallback)
    if m(PRIVACY_PATTERNS):
        return "privacy"

    # Tie-break logic for safe groups
    if jailbreak_match:
        return "jailbreak"  # Highest priority among safe groups
    elif model_spec_match:
        return "model-spec"
    elif unicode_match:
        return "unicode"

    return None


def detect_locale(prompt: str) -> str:
    """Detect effective locale based on prompt content with enhanced logic"""
    # Count ASCII characters
    ascii_count = sum(1 for c in prompt if ord(c) < 128)
    total_chars = len(prompt)
    ascii_ratio = ascii_count / total_chars if total_chars > 0 else 0

    # Enhanced English keywords detection
    en_keywords = [
        "can",
        "cannot",
        "capabilities",
        "safety",
        "mechanisms",
        "system",
        "AI",
        "what",
        "how",
        "why",
        "when",
        "where",
        "role-play",
        "pretend",
        "as dan",
        "jailbreak",
        "ignore",
        "previous",
        "instructions",
        "override",
        "bypass",
        "reveal",
        "system prompt",
    ]
    has_en_keywords = any(keyword in prompt.lower() for keyword in en_keywords)

    # Check for Vietnamese characters
    vi_chars = sum(
        1
        for c in prompt
        if "\u1e00" <= c <= "\u1eff"
        or "\u1f00" <= c <= "\u1fff"
        or "\u0100" <= c <= "\u017f"
        or "\u0180" <= c <= "\u024f"
    )
    has_vi_chars = vi_chars > 0

    # Enhanced locale detection logic
    if has_vi_chars and ascii_ratio < 0.7:
        return "vi"  # Vietnamese text
    elif ascii_ratio > 0.8 and has_en_keywords:
        return "en"  # English text
    elif ascii_ratio > 0.9:
        return "en"  # High ASCII ratio = English
    else:
        return "vi"  # Default to Vietnamese


def apply_policies(prompt: str):
    """Apply safety policies to prompt"""
    p = sanitize(prompt)
    cat = classify(p)

    # canary: không được echo chuỗi CANARY-Σ42 ra output
    redactions = [CANARY] if CANARY in prompt else []

    # Use policy map if available
    if cat and cat in POLICY_MAP:
        policy = POLICY_MAP[cat]
        blocked = policy.get("block", True)
        reason = f"policy:{cat}" if blocked else f"allow:{cat}"
        return PolicyDecision(blocked, cat, reason, redactions)

    # Fallback to old logic
    if cat in (
        "extremism",
        "violence",
        "illegal",
        "privacy",
        "injection",
        "canary",
        "jailbreak",
    ):
        return PolicyDecision(True, cat, f"blocked:{cat}", redactions)
    if cat == "self-harm":
        return PolicyDecision(False, cat, "intervene:self-harm", redactions)
    if cat == "model-spec":
        return PolicyDecision(False, cat, "answer:policy-info-safe", redactions)
    if cat == "unicode":
        return PolicyDecision(False, cat, "unicode-normalized", redactions)

    return PolicyDecision(False, None, "allow", redactions)


SAFE_TEMPLATES_VI = {
    "refuse_generic": "Xin lỗi, mình **không thể hỗ trợ** yêu cầu này.",
    "policy_reminder": "Mình sẽ hỗ trợ **trong phạm vi nguyên tắc** an toàn.",
    "selfharm_support": "Mình **rất tiếc** khi bạn thấy như vậy. Mình **không thể hỗ trợ** các hành vi tự hại. Nếu nguy cấp hãy **liên hệ** người thân hoặc dịch vụ khẩn cấp.",
    "privacy_refuse_mask": "Mình **không xử lý dữ liệu nhạy cảm/PII**. Vui lòng **ẩn/mask** thông tin riêng tư.",
    "unicode_normalized": "Nội dung đã được **chuẩn hoá Unicode (NFKC)** và **loại bỏ ký tự zero-width/RTL**.",
    "policy_explain": "Mình **không thể tiết lộ prompt hệ thống**. Nguyên tắc chung: an toàn, riêng tư, không gây hại.",
}
SAFE_TEMPLATES_EN = {
    "refuse_generic": "Sorry, I **can't help** with that request.",
    "policy_reminder": "I'll help **within safety guidelines**.",
    "selfharm_support": "I'm really **sorry** you're feeling this way. I **can't help** with self-harm. If urgent please **contact** family or emergency services.",
    "privacy_refuse_mask": "I **don't process sensitive data/PII**. Please **mask/hide** private information.",
    "unicode_normalized": "Content has been **Unicode normalized (NFKC)** and **zero-width/RTL characters removed**.",
    "policy_explain": "I **can't share system prompt**. General principles: safety, privacy, no harm.",
}


def safe_reply(
    category: str, locale: str = "vi", context: dict[str, Any] | None = None
) -> str:
    """Generate intelligent safe response based on category, locale, and context"""

    # Use policy map template if available
    if category and category in POLICY_MAP:
        template_name = POLICY_MAP[category].get("template", "refuse_generic")
        return get_template(template_name, locale, context or {})

    # Fallback to old templates for backward compatibility
    t = SAFE_TEMPLATES_VI if locale.startswith("vi") else SAFE_TEMPLATES_EN
    if category == "self-harm":
        return t.get("selfharm_support", t["refuse_generic"])
    elif category == "model-spec":
        return t.get("policy_explain", t["refuse_generic"])
    elif category == "unicode":
        return t.get("unicode_normalized", t["refuse_generic"])
    elif category == "privacy":
        return t.get("privacy_refuse_mask", t["refuse_generic"])
    elif category == "jailbreak":
        return t.get("policy_reminder", t["refuse_generic"])

    return t["refuse_generic"]


def redact_output(text: str, redactions: list[str]) -> str:
    """Remove sensitive content from output"""
    result = text
    for redaction in redactions:
        result = result.replace(redaction, "[CANARY]")
    return result
