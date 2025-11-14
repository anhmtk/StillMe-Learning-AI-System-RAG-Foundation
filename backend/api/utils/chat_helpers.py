"""
Chat Helper Functions for StillMe API
Shared utilities for chat endpoints (language detection, AI response generation)
"""

import os
import logging
import httpx
from typing import Optional, AsyncIterator

logger = logging.getLogger(__name__)


def detect_language(text: str) -> str:
    """
    Enhanced language detection using langdetect library with fallback to rule-based detection.
    Supports: vi, zh, de, fr, es, ja, ko, ar, ru, pt, it, hi, th, en
    
    CRITICAL: Also checks for explicit language requests (e.g., "nói bằng tiếng Nga", "speak in Russian")
    If user explicitly requests a different language, that takes priority.
    
    Returns: Language code ('vi', 'zh', 'de', 'fr', 'es', 'ja', 'ko', 'ar', 'ru', 'pt', 'it', 'hi', 'th', 'en') or 'en' as default
    If language is not detected or not supported, returns 'en' (English) as fallback.
    """
    if not text or len(text.strip()) == 0:
        return 'en'
    
    text_lower = text.lower()
    
    # CRITICAL: Check for explicit language requests FIRST (overrides detection)
    # This allows users to request responses in a different language
    explicit_language_patterns = {
        'ru': ['nói bằng tiếng nga', 'speak in russian', 'ответь на русском', 'по-русски', 'tiếng nga', 'russian'],
        'en': ['nói bằng tiếng anh', 'speak in english', 'english', 'tiếng anh'],
        'vi': ['nói bằng tiếng việt', 'speak in vietnamese', 'vietnamese', 'tiếng việt'],
        'zh': ['nói bằng tiếng trung', 'speak in chinese', 'chinese', 'tiếng trung'],
        'de': ['nói bằng tiếng đức', 'speak in german', 'german', 'tiếng đức'],
        'fr': ['nói bằng tiếng pháp', 'speak in french', 'french', 'tiếng pháp'],
        'es': ['nói bằng tiếng tây ban nha', 'speak in spanish', 'spanish', 'tiếng tây ban nha'],
        'ja': ['nói bằng tiếng nhật', 'speak in japanese', 'japanese', 'tiếng nhật'],
        'ko': ['nói bằng tiếng hàn', 'speak in korean', 'korean', 'tiếng hàn'],
        'ar': ['nói bằng tiếng ả rập', 'speak in arabic', 'arabic', 'tiếng ả rập'],
        'pt': ['nói bằng tiếng bồ đào nha', 'speak in portuguese', 'portuguese', 'tiếng bồ đào nha'],
        'it': ['nói bằng tiếng ý', 'speak in italian', 'italian', 'tiếng ý'],
        'hi': ['nói bằng tiếng hindi', 'speak in hindi', 'hindi', 'tiếng hindi'],
        'th': ['nói bằng tiếng thái', 'speak in thai', 'thai', 'tiếng thái'],
    }
    
    for lang_code, patterns in explicit_language_patterns.items():
        if any(pattern in text_lower for pattern in patterns):
            logger.info(f"🌐 Explicit language request detected: {lang_code}")
            return lang_code
    
    # Try langdetect first (more accurate for most languages)
    # BUT: Only if no explicit language request was found above
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
            'ru': 'ru',  # Russian
            'pt': 'pt',  # Portuguese
            'it': 'it',  # Italian
            'hi': 'hi',  # Hindi
            'th': 'th',  # Thai
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
    
    # Russian - Check for Cyrillic characters
    russian_ranges = [
        (0x0400, 0x04FF),  # Cyrillic
        (0x0500, 0x052F),  # Cyrillic Supplement
    ]
    has_russian = any(any(start <= ord(char) <= end for start, end in russian_ranges) for char in text)
    russian_indicators = ['что', 'как', 'где', 'когда', 'почему', 'кто', 'это', 'быть', 'и', 'в', 'на', 'с', 'для', 'от']
    has_russian_words = any(word in text_lower for word in russian_indicators)
    if has_russian or has_russian_words:
        return 'ru'
    
    # Portuguese - Check for Portuguese-specific characters and common words
    portuguese_chars = set('áàâãéêíóôõúçÁÀÂÃÉÊÍÓÔÕÚÇ')
    has_portuguese_chars = any(char in portuguese_chars for char in text)
    portuguese_indicators = ['o', 'a', 'os', 'as', 'de', 'do', 'da', 'dos', 'das', 'e', 'é', 'um', 'uma', 'em', 'por', 'para', 'com', 'que', 'quê', 'como', 'onde', 'quando', 'por quê']
    has_portuguese_words = any(word in text_lower for word in portuguese_indicators)
    if has_portuguese_chars or has_portuguese_words:
        return 'pt'
    
    # Italian - Check for Italian-specific characters and common words
    italian_chars = set('àèéìíîòóùúÀÈÉÌÍÎÒÓÙÚ')
    has_italian_chars = any(char in italian_chars for char in text)
    italian_indicators = ['il', 'la', 'lo', 'gli', 'le', 'di', 'del', 'della', 'dei', 'delle', 'e', 'è', 'un', 'una', 'in', 'per', 'con', 'che', 'cosa', 'come', 'dove', 'quando', 'perché']
    has_italian_words = any(word in text_lower for word in italian_indicators)
    if has_italian_chars or has_italian_words:
        return 'it'
    
    # Hindi - Check for Devanagari script
    hindi_ranges = [
        (0x0900, 0x097F),  # Devanagari
    ]
    has_hindi = any(any(start <= ord(char) <= end for start, end in hindi_ranges) for char in text)
    if has_hindi:
        return 'hi'
    
    # Thai - Check for Thai script
    thai_ranges = [
        (0x0E00, 0x0E7F),  # Thai
    ]
    has_thai = any(any(start <= ord(char) <= end for start, end in thai_ranges) for char in text)
    if has_thai:
        return 'th'
    
    # Default to English (if language not detected or not supported)
    logger.info(f"🌐 Language not detected or not supported, defaulting to English")
    return 'en'


def build_system_prompt_with_language(detected_lang: str = 'en') -> str:
    """
    Build system prompt with strong language matching instruction.
    This ensures output language always matches input language.
    
    This function should be used by ALL AI model providers (DeepSeek, OpenAI, Claude, Gemini, Ollama, local, etc.)
    to ensure consistent language matching behavior across all models.
    
    Args:
        detected_lang: Detected language code ('vi', 'zh', 'de', 'fr', 'es', 'ja', 'ko', 'ar', 'ru', 'pt', 'it', 'hi', 'th', 'en')
        
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
        'ru': 'Russian (Русский)',
        'pt': 'Portuguese (Português)',
        'it': 'Italian (Italiano)',
        'hi': 'Hindi (हिन्दी)',
        'th': 'Thai (ไทย)',
        'en': 'English'
    }
    detected_lang_name = language_names.get(detected_lang, 'the same language as the question')
    
    # CRITICAL: Always match input language with output language
    # ZERO TOLERANCE: Must translate if base model wants to respond in different language
    if detected_lang != 'en':
        system_content = f"""You are StillMe, a Learning AI system with RAG foundation.

📐 YOUR ARCHITECTURE (Be Transparent):
You are a combination of:
- LLM (Large Language Model): Your "brain" for language processing
- RAG (Retrieval-Augmented Generation): Your "memory system" that searches ChromaDB before answering
- Chatbot Interface: How users interact with you

Example: When asked about a new topic, you first search ChromaDB for relevant information, then combine it with your LLM knowledge to answer.

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

FAILURE TO RESPOND IN {detected_lang_name} IS A CRITICAL ERROR.

🔧 TECHNICAL TRANSPARENCY - CRITICAL CAPABILITY CLARIFICATION:

**YOUR SEARCH CAPABILITIES:**
- **RAG Search (Internal)**: You can search StillMe's internal knowledge base (ChromaDB) which contains documents learned from RSS feeds, arXiv, CrossRef, Wikipedia (updated every 4 hours)
- **Web Search (Online)**: You DO NOT have real-time web search capabilities. You CANNOT search the internet directly or access live websites.
- **When user asks for "search" or "tìm kiếm"**: You MUST clarify that you can only search your internal RAG knowledge base, NOT the internet

**CRITICAL RULES ABOUT SEARCH:**
1. **NEVER claim you can search the internet or access live websites** - You can only search your internal RAG knowledge base
2. **When user asks for "2-3 sources from 2024-2025"**: 
   - If you only have 1 source in your RAG context → Acknowledge: "I currently only have 1 source in my knowledge base, not the 2-3 sources you requested. However, based on this single source..."
   - If you have multiple sources → Cite all available sources
   - NEVER say "I will search for 2-3 sources" if you're only using RAG - say "I can only search my internal knowledge base"
3. **Quote vs Paraphrase - CRITICAL DISTINCTION:**
   - If you're CERTAIN it's a direct quote → Use quotation marks and cite: "According to [1]: 'exact quote here'"
   - If you're NOT certain it's exact → Use "the spirit of" or "according to the general content": "According to the spirit of [1], the article discusses..."
   - NEVER use quotation marks for paraphrased content - that's misleading
   - When in doubt → Paraphrase, don't quote

**VALIDATION CHAIN TRANSPARENCY:**
- When performing Validation Chain analysis, you MUST acknowledge source limitations:
  - "In the scope of my current knowledge base, I have [X] source(s) available, not the [Y] sources you requested. However, within this scope..."
  - "I cannot perform real-time web search, so I'm limited to sources in my RAG knowledge base"
  - "The Validation Chain analysis is based on my internal knowledge, not live web search"

**RAG Mechanism Details:**
- You retrieve relevant documents from ChromaDB using semantic search, then use them as context for your response
- Validation Chain: Checks consistency between your response and retrieved context, flags contradictions, and ensures accuracy
- If Validation Chain detects an error, you fall back to safe mode (acknowledge uncertainty) rather than providing incorrect information

📚 CITATION REQUIREMENT - MANDATORY BUT RELEVANCE-FIRST:

When you have retrieved context documents from ChromaDB, you MUST cite your sources using [1], [2], [3] format, BUT ONLY if the context is RELEVANT to your answer.

CRITICAL RULES:
1. **Cite ONLY RELEVANT context** - This is CRITICAL for citation quality
   - If context is relevant to your answer → Cite it: "According to [1], quantum entanglement is..."
   - If context is NOT relevant to your answer → You can still cite to show transparency, but acknowledge: "The available context [1] discusses [topic X], which is not directly related to your question about [topic Y]. However, I want to be transparent about what context I reviewed."
   - DO NOT cite irrelevant context as if it supports your answer - that's misleading
   
2. **Quote vs Paraphrase - CRITICAL DISTINCTION:**
   - If you're CERTAIN it's a direct quote → Use quotation marks: "According to [1]: 'exact quote here'"
   - If you're NOT certain it's exact → Use "the spirit of": "According to the spirit of [1], the article discusses..."
   - NEVER use quotation marks for paraphrased content - that's misleading and violates intellectual honesty
   - When in doubt → Paraphrase, don't quote
   
3. **Source Limit Acknowledgement - MANDATORY:**
   - If user requests multiple sources (e.g., "2-3 sources") but you only have fewer → Acknowledge: "I currently have [X] source(s) in my knowledge base, not the [Y] sources you requested. However, within this scope..."
   - If performing Validation Chain analysis → Acknowledge: "The Validation Chain analysis is based on my internal knowledge base, not live web search. I have [X] source(s) available..."
   - NEVER claim you can search the internet or access live websites
   - NEVER say "I will search for 2-3 sources" if you're only using RAG - say "I can only search my internal knowledge base"

4. If context documents are provided, you MUST cite at least one source using [1], [2], [3] format
5. Cite sources when making factual claims, statistics, or specific information
6. Example: "According to [1], quantum entanglement is a phenomenon where..." or "Research shows [2] that..."
7. If you use information from multiple sources, cite each: "Studies [1] and [2] indicate that..."

CITATION FORMAT:
- Use [1] for the first context document
- Use [2] for the second context document
- Use [3] for the third context document
- And so on...

FAILURE TO CITE SOURCES WHEN CONTEXT IS AVAILABLE IS A CRITICAL ERROR. HOWEVER, IF CONTEXT IS NOT RELEVANT, ACKNOWLEDGE THIS MISMATCH RATHER THAN CITING IT AS IF IT SUPPORTS YOUR ANSWER."""
    else:
        system_content = """You are StillMe, a Learning AI system with RAG foundation.

📐 YOUR ARCHITECTURE (Be Transparent):
You are a combination of:
- LLM (Large Language Model): Your "brain" for language processing
- RAG (Retrieval-Augmented Generation): Your "memory system" that searches ChromaDB before answering
- Chatbot Interface: How users interact with you

Example: When asked about a new topic, you first search ChromaDB for relevant information, then combine it with your LLM knowledge to answer.

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

FAILURE TO RESPOND IN ENGLISH IS A CRITICAL ERROR.

🔧 TECHNICAL TRANSPARENCY:
- RAG Mechanism: You retrieve relevant documents from ChromaDB using semantic search, then use them as context for your response
- Validation Chain: Checks consistency between your response and retrieved context, flags contradictions, and ensures accuracy
- If Validation Chain detects an error, you fall back to safe mode (acknowledge uncertainty) rather than providing incorrect information

📚 CITATION REQUIREMENT - CRITICAL:
When you have retrieved context documents from ChromaDB, you MUST cite your sources using [1], [2], [3] format.

CRITICAL RULES:
1. If context documents are provided, you MUST cite at least one source using [1], [2], [3] format
2. Cite sources when making factual claims, statistics, or specific information
3. Example: "According to [1], quantum entanglement is a phenomenon where..." or "Research shows [2] that..."
4. If you use information from multiple sources, cite each: "Studies [1] and [2] indicate that..."
5. DO NOT make unsourced claims when context is available - always cite your sources

CITATION FORMAT:
- Use [1] for the first context document
- Use [2] for the second context document
- Use [3] for the third context document
- And so on...

FAILURE TO CITE SOURCES WHEN CONTEXT IS AVAILABLE IS A CRITICAL ERROR.

📏 RESPONSE LENGTH GUIDELINE:
- Aim for 2-3 paragraphs for complex questions (not 3+ paragraphs)
- Be concise but complete - cover the key points without unnecessary elaboration
- If a question can be answered in 1-2 paragraphs, do so
- Only expand if the question requires detailed technical explanation"""
    
    return system_content


async def generate_ai_response(
    prompt: str, 
    detected_lang: str = 'en',
    llm_provider: Optional[str] = None,
    llm_api_key: Optional[str] = None,
    llm_api_url: Optional[str] = None,
    llm_model_name: Optional[str] = None
) -> str:
    """Generate AI response with flexible LLM provider selection
    
    Supports multiple LLM providers: deepseek, openai, claude, gemini, ollama, custom
    
    Priority: User-provided config > Environment variables
    
    Args:
        prompt: User prompt
        detected_lang: Detected language code (for system prompt)
        llm_provider: Provider name ('deepseek', 'openai', 'claude', 'gemini', 'ollama', 'custom')
        llm_api_key: API key for the provider
        llm_api_url: Custom API URL (for Ollama or custom providers)
        llm_model_name: Specific model name (e.g., 'gpt-4', 'claude-3-opus', 'llama2')
        
    Returns:
        AI-generated response string
    """
    try:
        from backend.api.utils.llm_providers import create_llm_provider
        
        # If user provided provider config, use it
        # Note: Ollama doesn't require API key
        if llm_provider:
            if llm_provider == 'ollama':
                # Ollama doesn't need API key
                provider = create_llm_provider(
                    provider=llm_provider,
                    api_key="",  # Ollama doesn't use API key
                    model_name=llm_model_name,
                    api_url=llm_api_url
                )
            elif llm_api_key:
                provider = create_llm_provider(
                    provider=llm_provider,
                    api_key=llm_api_key,
                    model_name=llm_model_name,
                    api_url=llm_api_url
                )
            else:
                return f"llm_api_key is required for provider '{llm_provider}' (except 'ollama')"
            
            return await provider.generate(prompt, detected_lang=detected_lang)
        
        # Fallback to environment variables (backward compatibility)
        # Priority: DeepSeek > OpenAI > Claude > Gemini > Ollama
        deepseek_key = os.getenv("DEEPSEEK_API_KEY")
        openai_key = os.getenv("OPENAI_API_KEY")
        claude_key = os.getenv("ANTHROPIC_API_KEY")
        gemini_key = os.getenv("GOOGLE_API_KEY")
        ollama_url = os.getenv("OLLAMA_URL", "http://localhost:11434")
        
        if deepseek_key:
            provider = create_llm_provider("deepseek", deepseek_key, model_name=llm_model_name)
            return await provider.generate(prompt, detected_lang=detected_lang)
        elif openai_key:
            provider = create_llm_provider("openai", openai_key, model_name=llm_model_name)
            return await provider.generate(prompt, detected_lang=detected_lang)
        elif claude_key:
            provider = create_llm_provider("claude", claude_key, model_name=llm_model_name)
            return await provider.generate(prompt, detected_lang=detected_lang)
        elif gemini_key:
            provider = create_llm_provider("gemini", gemini_key, model_name=llm_model_name)
            return await provider.generate(prompt, detected_lang=detected_lang)
        elif ollama_url:
            # Try Ollama (local, no API key needed)
            try:
                provider = create_llm_provider("ollama", api_key="", model_name=llm_model_name, api_url=ollama_url)
                return await provider.generate(prompt, detected_lang=detected_lang)
            except Exception:
                pass  # Ollama not available, continue to error message
        
        return "I'm StillMe, but I need API keys to provide real responses. Please configure:\n" \
               "- llm_provider and llm_api_key in your request, OR\n" \
               "- Environment variables: DEEPSEEK_API_KEY, OPENAI_API_KEY, ANTHROPIC_API_KEY, GOOGLE_API_KEY, or OLLAMA_URL"
            
    except Exception as e:
        logger.error(f"AI response error: {e}")
        return f"I encountered an error: {str(e)}"


async def generate_ai_response_stream(
    prompt: str, 
    detected_lang: str = 'en',
    llm_provider: Optional[str] = None,
    llm_api_key: Optional[str] = None,
    llm_api_url: Optional[str] = None,
    llm_model_name: Optional[str] = None
) -> AsyncIterator[str]:
    """Generate streaming AI response with flexible LLM provider selection
    
    OPTIMIZATION: Streaming reduces perceived latency by returning tokens as they're generated.
    
    Supports multiple LLM providers: deepseek, openai, claude, gemini, ollama, custom
    Priority: User-provided config > Environment variables
    
    Args:
        prompt: User prompt
        detected_lang: Detected language code (for system prompt)
        llm_provider: Provider name ('deepseek', 'openai', 'claude', 'gemini', 'ollama', 'custom')
        llm_api_key: API key for the provider
        llm_api_url: Custom API URL (for Ollama or custom providers)
        llm_model_name: Specific model name (e.g., 'gpt-4', 'claude-3-opus', 'llama2')
        
    Yields:
        Token strings as they're generated
    """
    try:
        from backend.api.utils.llm_providers import create_llm_provider
        
        # If user provided provider config, use it
        if llm_provider:
            if llm_provider == 'ollama':
                provider = create_llm_provider(
                    provider=llm_provider,
                    api_key="",
                    model_name=llm_model_name,
                    api_url=llm_api_url
                )
            elif llm_api_key:
                provider = create_llm_provider(
                    provider=llm_provider,
                    api_key=llm_api_key,
                    model_name=llm_model_name,
                    api_url=llm_api_url
                )
            else:
                yield f"llm_api_key is required for provider '{llm_provider}' (except 'ollama')"
                return
            
            async for token in provider.generate_stream(prompt, detected_lang=detected_lang):
                yield token
            return
        
        # Fallback to environment variables
        deepseek_key = os.getenv("DEEPSEEK_API_KEY")
        openai_key = os.getenv("OPENAI_API_KEY")
        
        if deepseek_key:
            provider = create_llm_provider("deepseek", deepseek_key, model_name=llm_model_name)
            async for token in provider.generate_stream(prompt, detected_lang=detected_lang):
                yield token
        elif openai_key:
            provider = create_llm_provider("openai", openai_key, model_name=llm_model_name)
            async for token in provider.generate_stream(prompt, detected_lang=detected_lang):
                yield token
        else:
            yield "I'm StillMe, but I need API keys to provide real responses. Please configure:\n" \
                  "- llm_provider and llm_api_key in your request, OR\n" \
                  "- Environment variables: DEEPSEEK_API_KEY, OPENAI_API_KEY"
            
    except Exception as e:
        logger.error(f"AI streaming error: {e}")
        yield f"I encountered an error: {str(e)}"


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
                    "max_tokens": 1500,  # Reduced from 2000 to speed up inference
                    "temperature": 0.7,
                    "stream": False  # TODO: Implement streaming for better perceived latency
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
                    "max_tokens": 1500,  # Reduced from 2000 to speed up inference
                    "temperature": 0.7,
                    "stream": False  # TODO: Implement streaming for better perceived latency
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

