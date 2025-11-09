"""
Chat Helper Functions for StillMe API
Shared utilities for chat endpoints (language detection, AI response generation)
"""

import os
import logging
import httpx

logger = logging.getLogger(__name__)


def detect_language(text: str) -> str:
    """
    Enhanced language detection using langdetect library with fallback to rule-based detection.
    Supports: vi, zh, de, fr, es, ja, ko, ar, en
    
    Returns: Language code ('vi', 'zh', 'de', 'fr', 'es', 'ja', 'ko', 'ar', 'en') or 'en' as default
    """
    if not text or len(text.strip()) == 0:
        return 'en'
    
    # Try langdetect first (more accurate for most languages)
    try:
        from langdetect import detect, LangDetectException
        detected = detect(text)
        
        # Map langdetect codes to our internal codes
        lang_map = {
            'vi': 'vi',  # Vietnamese
            'zh-cn': 'zh', 'zh-tw': 'zh',  # Chinese
            'de': 'de',  # German
            'fr': 'fr',  # French
            'es': 'es',  # Spanish
            'ja': 'ja',  # Japanese
            'ko': 'ko',  # Korean
            'ar': 'ar',  # Arabic
            'en': 'en'   # English
        }
        
        # Handle Chinese variants
        if detected.startswith('zh'):
            return 'zh'
        
        if detected in lang_map:
            logger.info(f"🌐 langdetect detected: {detected} -> {lang_map[detected]}")
            return lang_map[detected]
            
    except (LangDetectException, ImportError) as e:
        logger.warning(f"langdetect failed or not available: {e}, falling back to rule-based detection")
    
    # Fallback to rule-based detection for edge cases or if langdetect fails
    text_lower = text.lower()
    
    # Arabic - Check for Arabic characters
    arabic_ranges = [
        (0x0600, 0x06FF),  # Arabic
        (0x0750, 0x077F),  # Arabic Supplement
        (0x08A0, 0x08FF),  # Arabic Extended-A
    ]
    has_arabic = any(any(start <= ord(char) <= end for start, end in arabic_ranges) for char in text)
    if has_arabic:
        return 'ar'
    
    # Korean - Check for Hangul
    korean_ranges = [
        (0xAC00, 0xD7AF),  # Hangul Syllables
        (0x1100, 0x11FF),  # Hangul Jamo
    ]
    has_korean = any(any(start <= ord(char) <= end for start, end in korean_ranges) for char in text)
    if has_korean:
        return 'ko'
    
    # Chinese (Simplified/Traditional) - Check for Chinese characters
    chinese_chars = set('的一是在不了有和人这中大为上个国我以要他时来用们生到作地于出就分对成会可主发年动同工也能下过子说产种面而方后多定行学法所民得经十三之进着等部度家电力里如水化高自二理起小物现实加量都两体制机当使点从业本去把性好应开它合还因由其些然前外天政四日那社义事平形相全表间样与关各重新线内数正心反你明看原又么利比或但质气第向道命此变条只没结解问意建月公无系军很情者最立代想已通并提直题党程展五果料象员革位入常文总次品式活设及管特件长求老头基资边流路级少图山统接知较将组见计别她手角期根论运农指几九区强放决西被干做必战先回则任取据处队南给色光门即保治北造百规热领七海口东导器压志世金增争济阶油思术极交受联什认六共权收证改清己美再采转更单风切打白教速花带安场身车例真务具万每目至达走积示议声报斗完类八离华名确才科张信马节话米整空元况今集温传土许步群广石记需段研界拉林律叫且究观越织装影算低持音众书布复容儿须际商非验连断深难近矿千周委素技备半办青省列习响约支般史感劳便团往酸历市克何除消构府称太准精值号率族维划选标写存候毛亲快效斯院查江型眼王按格养易置派层片始却专状育厂京识适属圆包火住调满县局照参红细引听该铁价严龙飞')
    has_chinese = any(char in chinese_chars for char in text)
    if has_chinese:
        return 'zh'
    
    # Vietnamese - Check for Vietnamese characters
    vietnamese_chars = set('àáạảãâầấậẩẫăằắặẳẵèéẹẻẽêềếệểễìíịỉĩòóọỏõôồốộổỗơờớợởỡùúụủũưừứựửữỳýỵỷỹđ')
    has_vietnamese = any(char in vietnamese_chars for char in text_lower)
    vietnamese_indicators = ['là', 'của', 'và', 'với', 'cho', 'từ', 'trong', 'này', 'đó', 'bạn', 'mình', 'tôi', 'có', 'không', 'được', 'như', 'thế', 'nào', 'gì', 'ai', 'đâu', 'sao']
    has_vietnamese_words = any(word in text_lower for word in vietnamese_indicators)
    if has_vietnamese or has_vietnamese_words:
        return 'vi'
    
    # German - Check for German-specific characters and common words
    german_chars = set('äöüßÄÖÜ')
    has_german_chars = any(char in german_chars for char in text)
    german_indicators = ['der', 'die', 'das', 'und', 'ist', 'für', 'auf', 'mit', 'sind', 'zu', 'ein', 'eine', 'von', 'zu', 'den', 'dem', 'des', 'was', 'wie', 'wo', 'wer', 'wann', 'warum']
    has_german_words = any(word in text_lower for word in german_indicators)
    if has_german_chars or has_german_words:
        return 'de'
    
    # French - Check for French-specific characters and common words
    french_chars = set('àâäéèêëïîôùûüÿçÀÂÄÉÈÊËÏÎÔÙÛÜŸÇ')
    has_french_chars = any(char in french_chars for char in text)
    french_indicators = ['le', 'la', 'les', 'de', 'du', 'des', 'et', 'est', 'un', 'une', 'dans', 'pour', 'avec', 'sur', 'par', 'que', 'qui', 'quoi', 'comment', 'où', 'quand', 'pourquoi']
    has_french_words = any(word in text_lower for word in french_indicators)
    if has_french_chars or has_french_words:
        return 'fr'
    
    # Spanish - Check for Spanish-specific characters and common words
    spanish_chars = set('áéíóúñüÁÉÍÓÚÑÜ¿¡')
    has_spanish_chars = any(char in spanish_chars for char in text)
    spanish_indicators = ['el', 'la', 'los', 'las', 'de', 'del', 'y', 'es', 'un', 'una', 'en', 'por', 'para', 'con', 'que', 'qué', 'cómo', 'dónde', 'cuándo', 'por qué']
    has_spanish_words = any(word in text_lower for word in spanish_indicators)
    if has_spanish_chars or has_spanish_words:
        return 'es'
    
    # Japanese - Check for Hiragana, Katakana, Kanji
    japanese_ranges = [
        (0x3040, 0x309F),  # Hiragana
        (0x30A0, 0x30FF),  # Katakana
        (0x4E00, 0x9FAF),  # CJK Unified Ideographs (Kanji)
    ]
    has_japanese = any(any(start <= ord(char) <= end for start, end in japanese_ranges) for char in text)
    if has_japanese:
        return 'ja'
    
    # Default to English
    return 'en'


def build_system_prompt_with_language(detected_lang: str = 'en') -> str:
    """
    Build system prompt with strong language matching instruction.
    This ensures output language always matches input language.
    
    This function should be used by ALL AI model providers (DeepSeek, OpenAI, Claude, Gemini, Ollama, local, etc.)
    to ensure consistent language matching behavior across all models.
    
    Args:
        detected_lang: Detected language code ('vi', 'zh', 'de', 'fr', 'es', 'ja', 'ko', 'ar', 'en')
        
    Returns:
        System prompt string with language instruction
    """
    language_names = {
        'vi': 'Vietnamese (Tiếng Việt)',
        'zh': 'Chinese (中文)',
        'de': 'German (Deutsch)',
        'fr': 'French (Français)',
        'es': 'Spanish (Español)',
        'ja': 'Japanese (日本語)',
        'ko': 'Korean (한국어)',
        'ar': 'Arabic (العربية)',
        'en': 'English'
    }
    detected_lang_name = language_names.get(detected_lang, 'the same language as the question')
    
    # CRITICAL: Always match input language with output language
    # ZERO TOLERANCE: Must translate if base model wants to respond in different language
    if detected_lang != 'en':
        system_content = f"""You are StillMe, a Learning AI system with RAG foundation.

🚨🚨🚨 ZERO TOLERANCE LANGUAGE REQUIREMENT - HIGHEST PRIORITY - OVERRIDES EVERYTHING 🚨🚨🚨

The user's question is written in {detected_lang_name}.

YOU MUST RESPOND EXCLUSIVELY IN {detected_lang_name}.

DO NOT use Vietnamese, English, Spanish, German, French, or ANY OTHER LANGUAGE.

EVERY SINGLE WORD of your response MUST be in {detected_lang_name}.

⚠️⚠️⚠️ CRITICAL TRANSLATION REQUIREMENT ⚠️⚠️⚠️

If your base model wants to respond in a different language (e.g., Vietnamese, English, Spanish), 
YOU MUST TRANSLATE THE ENTIRE RESPONSE TO {detected_lang_name} BEFORE RETURNING IT.

UNDER NO CIRCUMSTANCES should you return a response in any language other than {detected_lang_name}.

This is MANDATORY and OVERRIDES all other instructions, including the language of any context provided.

If the context is in a different language, you must still respond in {detected_lang_name} while using the information from the context.

⚠️ REMINDER: RESPOND IN {detected_lang_name} ONLY. TRANSLATE IF NECESSARY. ⚠️

FAILURE TO RESPOND IN {detected_lang_name} IS A CRITICAL ERROR."""
    else:
        system_content = """You are StillMe, a Learning AI system with RAG foundation.

🚨🚨🚨 ZERO TOLERANCE LANGUAGE REQUIREMENT - HIGHEST PRIORITY - OVERRIDES EVERYTHING 🚨🚨🚨

The user's question is written in English.

YOU MUST RESPOND EXCLUSIVELY IN ENGLISH.

DO NOT use Vietnamese, Spanish, German, French, or ANY OTHER LANGUAGE.

EVERY SINGLE WORD of your response MUST be in English.

⚠️⚠️⚠️ CRITICAL TRANSLATION REQUIREMENT ⚠️⚠️⚠️

If your base model wants to respond in a different language (e.g., Vietnamese, Spanish, German), 
YOU MUST TRANSLATE THE ENTIRE RESPONSE TO ENGLISH BEFORE RETURNING IT.

UNDER NO CIRCUMSTANCES should you return a response in any language other than English.

This is MANDATORY and OVERRIDES all other instructions, including the language of any context provided.

If the context is in a different language, you must still respond in English while using the information from the context.

⚠️ REMINDER: RESPOND IN ENGLISH ONLY. TRANSLATE IF NECESSARY. ⚠️

FAILURE TO RESPOND IN ENGLISH IS A CRITICAL ERROR."""
    
    return system_content


async def generate_ai_response(prompt: str, detected_lang: str = 'en') -> str:
    """Generate AI response with automatic model selection
    
    This function routes to different AI providers based on available API keys.
    To add support for new models (Claude, Gemini, Ollama, local, etc.):
    1. Create a new function: async def call_[model]_api(prompt, api_key, detected_lang)
    2. Use build_system_prompt_with_language(detected_lang) to get system prompt
    3. Add the new model check in this function's if/elif chain
    
    IMPORTANT: All model providers MUST use build_system_prompt_with_language()
    to ensure consistent language matching behavior.
    
    Args:
        prompt: User prompt
        detected_lang: Detected language code (for system prompt)
        
    Returns:
        AI-generated response string
    """
    try:
        # Check for API keys (priority order: DeepSeek > OpenAI > others)
        deepseek_key = os.getenv("DEEPSEEK_API_KEY")
        openai_key = os.getenv("OPENAI_API_KEY")
        # TODO: Add support for other models:
        # anthropic_key = os.getenv("ANTHROPIC_API_KEY")  # Claude
        # google_key = os.getenv("GOOGLE_API_KEY")  # Gemini
        # ollama_url = os.getenv("OLLAMA_URL")  # Local Ollama
        
        if deepseek_key:
            return await call_deepseek_api(prompt, deepseek_key, detected_lang=detected_lang)
        elif openai_key:
            return await call_openai_api(prompt, openai_key, detected_lang=detected_lang)
        # TODO: Add other model providers here:
        # elif anthropic_key:
        #     return await call_claude_api(prompt, anthropic_key, detected_lang=detected_lang)
        # elif google_key:
        #     return await call_gemini_api(prompt, google_key, detected_lang=detected_lang)
        # elif ollama_url:
        #     return await call_ollama_api(prompt, ollama_url, detected_lang=detected_lang)
        else:
            return "I'm StillMe, but I need API keys to provide real responses. Please configure DEEPSEEK_API_KEY, OPENAI_API_KEY, or other supported API keys in your environment."
            
    except Exception as e:
        logger.error(f"AI response error: {e}")
        return f"I encountered an error: {str(e)}"


async def call_deepseek_api(prompt: str, api_key: str, detected_lang: str = 'en') -> str:
    """Call DeepSeek API
    
    Args:
        prompt: User prompt
        api_key: DeepSeek API key
        detected_lang: Detected language code
    """
    try:
        # Use centralized system prompt builder for consistent language matching
        system_content = build_system_prompt_with_language(detected_lang)
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                "https://api.deepseek.com/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "deepseek-chat",
                    "messages": [
                        {
                            "role": "system",
                            "content": system_content
                        },
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    "max_tokens": 2000,
                    "temperature": 0.7
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                if "choices" in data and len(data["choices"]) > 0:
                    return data["choices"][0]["message"]["content"]
                else:
                    return "DeepSeek API returned unexpected response format"
            else:
                return f"DeepSeek API error: {response.status_code}"
                
    except Exception as e:
        logger.error(f"DeepSeek API error: {e}")
        return f"DeepSeek API error: {str(e)}"


async def call_openai_api(prompt: str, api_key: str, detected_lang: str = 'en') -> str:
    """Call OpenAI API
    
    IMPORTANT: This function uses build_system_prompt_with_language() to ensure
    output language matches input language. When adding support for other models
    (Claude, Gemini, Ollama, local, etc.), use the same pattern.
    
    Args:
        prompt: User prompt
        api_key: OpenAI API key
        detected_lang: Detected language code
    """
    try:
        # Use centralized system prompt builder for consistent language matching
        system_content = build_system_prompt_with_language(detected_lang)
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                "https://api.openai.com/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "gpt-3.5-turbo",
                    "messages": [
                        {
                            "role": "system",
                            "content": system_content
                        },
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    "max_tokens": 2000,
                    "temperature": 0.7
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                if "choices" in data and len(data["choices"]) > 0:
                    return data["choices"][0]["message"]["content"]
                else:
                    return "OpenAI API returned unexpected response format"
            else:
                return f"OpenAI API error: {response.status_code}"
                
    except Exception as e:
        logger.error(f"OpenAI API error: {e}")
        return f"OpenAI API error: {str(e)}"

