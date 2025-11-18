"""
ConfidenceValidator - Detects when AI should express uncertainty
"""

import re
from typing import List, Optional
from .base import ValidationResult
import logging

logger = logging.getLogger(__name__)


def _detect_language_from_text(text: str) -> str:
    """
    Detect language from text content using character patterns.
    
    Args:
        text: Text to analyze
        
    Returns:
        Language code (e.g., 'vi', 'fr', 'ar', 'ru', 'de', 'es', 'en')
    """
    if not text or len(text.strip()) < 10:
        return 'en'  # Default to English
    
    text_lower = text.lower()
    
    # Vietnamese: àáạảãâầấậẩẫăằắặẳẵèéẹẻẽêềếệểễìíịỉĩòóọỏõôồốộổỗơờớợởỡùúụủũưừứựửữỳýỵỷỹđ
    if re.search(r'[àáạảãâầấậẩẫăằắặẳẵèéẹẻẽêềếệểễìíịỉĩòóọỏõôồốộổỗơờớợởỡùúụủũưừứựửữỳýỵỷỹđ]', text, re.IGNORECASE):
        return 'vi'
    
    # Arabic: ا-ي
    if re.search(r'[\u0600-\u06FF]', text):
        return 'ar'
    
    # Russian: а-я, ё
    if re.search(r'[а-яё]', text_lower):
        return 'ru'
    
    # French: àâäéèêëïîôùûüÿç
    if re.search(r'[àâäéèêëïîôùûüÿç]', text, re.IGNORECASE):
        return 'fr'
    
    # German: äöüß
    if re.search(r'[äöüß]', text, re.IGNORECASE):
        return 'de'
    
    # Spanish: áéíóúñü
    if re.search(r'[áéíóúñü]', text, re.IGNORECASE):
        return 'es'
    
    # Chinese: 中文
    if re.search(r'[\u4e00-\u9fff]', text):
        return 'zh'
    
    # Japanese: ひらがな, カタカナ, 漢字
    if re.search(r'[\u3040-\u309F\u30A0-\u30FF\u4e00-\u9fff]', text):
        return 'ja'
    
    # Korean: 한글
    if re.search(r'[\uAC00-\uD7A3]', text):
        return 'ko'
    
    # Portuguese: áàâãéêíóôõúç
    if re.search(r'[áàâãéêíóôõúç]', text, re.IGNORECASE):
        return 'pt'
    
    # Italian: àèéìíîòóùú
    if re.search(r'[àèéìíîòóùú]', text, re.IGNORECASE):
        return 'it'
    
    # Hindi: Devanagari
    if re.search(r'[\u0900-\u097F]', text):
        return 'hi'
    
    # Thai: ไทย
    if re.search(r'[\u0E00-\u0E7F]', text):
        return 'th'
    
    # Default to English
    return 'en'


# Patterns that indicate uncertainty (good!)
UNCERTAINTY_PATTERNS = [
    r"i don't know",
    r"i'm not (certain|sure)",
    r"i cannot (answer|determine|verify)",
    r"i don't have (sufficient|enough) (information|context|data)",
    r"based on the context (provided|available),? i (cannot|don't)",
    r"my knowledge base (doesn't|does not) (contain|have)",
    r"not (certain|sure|confident) (about|regarding)",
    r"unable to (answer|determine|verify)",
    r"không (biết|chắc|rõ)",
    r"không có (đủ|thông tin|dữ liệu)",
    r"không thể (trả lời|xác định|xác minh)",
    r"tôi (không|chưa) (biết|có|rõ)",
    r"hiện tại (tôi|mình) (không|chưa) (có|biết)"
]

# Patterns that indicate overconfidence (bad!)
OVERCONFIDENCE_PATTERNS = [
    r"definitely",
    r"absolutely (certain|sure)",
    r"without a doubt",
    r"i'm 100% (sure|certain)",
    r"chắc chắn 100%",
    r"hoàn toàn chắc chắn"
]


class ConfidenceValidator:
    """Validator that checks if AI appropriately expresses uncertainty"""
    
    def __init__(self, require_uncertainty_when_no_context: bool = True):
        """
        Initialize confidence validator
        
        Args:
            require_uncertainty_when_no_context: If True, require uncertainty expressions when no context
        """
        self.require_uncertainty_when_no_context = require_uncertainty_when_no_context
        logger.info(f"ConfidenceValidator initialized (require_uncertainty_when_no_context={require_uncertainty_when_no_context})")
    
    def run(self, answer: str, ctx_docs: List[str], context_quality: Optional[str] = None, 
            avg_similarity: Optional[float] = None, is_philosophical: bool = False) -> ValidationResult:
        """
        Check if answer appropriately expresses uncertainty
        
        Args:
            answer: The answer to validate
            ctx_docs: List of context documents from RAG
            context_quality: Context quality from RAG ("high", "medium", "low")
            avg_similarity: Average similarity score of retrieved context (0.0-1.0)
            is_philosophical: If True, relax uncertainty requirements for philosophical questions (don't force "I don't know" for theoretical reasoning)
            
        Returns:
            ValidationResult with passed status and reasons
        """
        answer_lower = answer.lower()
        
        # Tier 3.5: Force uncertainty when context quality is low
        # BUT: Skip for philosophical questions (theoretical reasoning doesn't need context)
        if not is_philosophical and (context_quality == "low" or (avg_similarity is not None and avg_similarity < 0.3)):
            # Check if answer already expresses uncertainty
            has_uncertainty = any(
                re.search(pattern, answer_lower, re.IGNORECASE)
                for pattern in UNCERTAINTY_PATTERNS
            )
            
            if not has_uncertainty:
                # CRITICAL: Detect language from answer and use appropriate template
                # Skip English uncertainty templates at the start to detect actual answer language
                answer_for_detection = answer
                # Remove common English uncertainty prefixes
                english_uncertainty_prefixes = [
                    "I don't have sufficient information",
                    "The retrieved context has low relevance",
                    "I don't have enough information",
                    "I cannot answer this accurately"
                ]
                for prefix in english_uncertainty_prefixes:
                    if answer_for_detection.strip().startswith(prefix):
                        # Find the first newline or double newline after prefix
                        newline_pos = answer_for_detection.find('\n', len(prefix))
                        if newline_pos > 0:
                            answer_for_detection = answer_for_detection[newline_pos:].strip()
                            break
                
                # Detect multiple languages from answer content (skip English uncertainty template)
                detected_lang_from_answer = _detect_language_from_text(answer_for_detection)
                
                uncertainty_templates = {
                    'vi': "Mình không có đủ thông tin để trả lời chính xác câu hỏi này. Ngữ cảnh được tìm thấy có độ liên quan thấp với câu hỏi của bạn.",
                    'fr': "Je n'ai pas suffisamment d'informations pour répondre avec précision à cette question. Le contexte récupéré a une faible pertinence par rapport à votre question.",
                    'de': "Ich habe nicht genügend Informationen, um diese Frage genau zu beantworten. Der abgerufene Kontext hat eine geringe Relevanz für Ihre Frage.",
                    'es': "No tengo suficiente información para responder con precisión a esta pregunta. El contexto recuperado tiene poca relevancia para su pregunta.",
                    'ar': "ليس لدي معلومات كافية للإجابة على هذا السؤال بدقة. السياق المسترجع له صلة منخفضة بسؤالك.",
                    'ru': "У меня недостаточно информации, чтобы точно ответить на этот вопрос. Извлеченный контекст имеет низкую релевантность к вашему вопросу.",
                    'zh': "我没有足够的信息来准确回答这个问题。检索到的上下文与您的问题相关性较低。",
                    'ja': "この質問に正確に答えるための十分な情報がありません。取得されたコンテキストは、あなたの質問との関連性が低いです。",
                    'ko': "이 질문에 정확하게 답하기에 충분한 정보가 없습니다. 검색된 컨텍스트는 귀하의 질문과 관련성이 낮습니다.",
                    'pt': "Não tenho informações suficientes para responder com precisão a esta pergunta. O contexto recuperado tem baixa relevância para sua pergunta.",
                    'it': "Non ho informazioni sufficienti per rispondere con precisione a questa domanda. Il contesto recuperato ha una bassa rilevanza per la tua domanda.",
                    'hi': "मेरे पास इस प्रश्न का सटीक उत्तर देने के लिए पर्याप्त जानकारी नहीं है। पुनर्प्राप्त संदर्भ का आपके प्रश्न से कम प्रासंगिकता है।",
                    'th': "ฉันไม่มีข้อมูลเพียงพอที่จะตอบคำถามนี้อย่างแม่นยำ บริบทที่ดึงมามีความเกี่ยวข้องต่ำกับคำถามของคุณ",
                }
                
                uncertainty_template = uncertainty_templates.get(detected_lang_from_answer, 
                    "I don't have sufficient information to answer this accurately. The retrieved context has low relevance to your question.")
                # Prepend uncertainty to answer
                patched_answer = f"{uncertainty_template}\n\n{answer}"
                logger.warning("⚠️ Forced uncertainty expression due to low context quality")
                return ValidationResult(
                    passed=True,
                    reasons=["forced_uncertainty_low_context_quality"],
                    patched_answer=patched_answer
                )
        
        # Check for uncertainty expressions
        has_uncertainty = any(
            re.search(pattern, answer_lower, re.IGNORECASE)
            for pattern in UNCERTAINTY_PATTERNS
        )
        
        # Check for overconfidence
        has_overconfidence = any(
            re.search(pattern, answer_lower, re.IGNORECASE)
            for pattern in OVERCONFIDENCE_PATTERNS
        )
        
        # If no context, check for transparency about knowledge source
        if not ctx_docs or len(ctx_docs) == 0:
            # For philosophical questions, don't force uncertainty (theoretical reasoning doesn't need context)
            if is_philosophical:
                logger.debug("Philosophical question with no context - allowing theoretical reasoning without forcing uncertainty")
                return ValidationResult(passed=True)
            
            if self.require_uncertainty_when_no_context:
                # Check if AI acknowledges using base knowledge/training data (transparency)
                transparency_patterns = [
                    r"based on (general knowledge|training data|my training|base knowledge)",
                    r"from (my|general|base) (training data|knowledge base|knowledge)",
                    r"not from (stillme|rag) (knowledge base|knowledge)",
                    r"(general|base) knowledge",
                    r"training data",
                    r"kiến thức (chung|cơ bản)",
                    r"dữ liệu (huấn luyện|training)",
                    r"không (từ|phải từ) (stillme|rag)",
                    r"dựa trên (kiến thức|dữ liệu) (chung|huấn luyện|cơ bản)",
                    r"tuy nhiên.*stillme.*không.*có",  # "However, StillMe doesn't have..."
                    r"however.*stillme.*(doesn't|does not).*have",  # English version
                    r"dựa trên.*kiến thức.*chung",  # "Based on general knowledge"
                    r"theo.*kiến thức.*chung"  # "According to general knowledge"
                ]
                has_transparency = any(
                    re.search(pattern, answer_lower, re.IGNORECASE)
                    for pattern in transparency_patterns
                )
                
                # If AI is transparent about using base knowledge, that's acceptable
                if has_transparency:
                    logger.debug("✅ Good: AI is transparent about using base knowledge when no RAG context")
                    return ValidationResult(passed=True)
                elif has_uncertainty:
                    logger.debug("✅ Good: AI expressed uncertainty when no context available")
                    return ValidationResult(passed=True)
                else:
                    logger.warning("❌ AI should express uncertainty OR acknowledge using base knowledge when no context is available")
                    return ValidationResult(
                        passed=False,
                        reasons=["missing_uncertainty_no_context"]
                    )
            else:
                return ValidationResult(passed=True)
        
        # If context exists but answer is overconfident, warn
        if has_overconfidence and not has_uncertainty:
            logger.warning("⚠️ AI expressed overconfidence - may need more humility")
            # Don't fail, just warn
            return ValidationResult(
                passed=True,
                reasons=["overconfidence_detected"]
            )
        
        return ValidationResult(passed=True)

