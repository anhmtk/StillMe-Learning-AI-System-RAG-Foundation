# modules/api_provider_manager.py
import logging
import os

# Import common utilities
import sys
import time
from typing import Any, Dict, List, Optional

from openai import OpenAI

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from common.config import load_module_config
from common.errors import APIError, NetworkError
from common.http import AsyncHttpClient, HTTPClientConfig
from common.logging import get_module_logger

# CRITICAL: Load environment variables from .env file
try:
    from dotenv import load_dotenv

    load_dotenv()  # Load .env file into os.environ
    print("✅ API Provider Manager: Environment variables loaded from .env file")
except ImportError:
    print(
        "⚠️ API Provider Manager: python-dotenv not installed. Install with: pip install python-dotenv"
    )
except Exception as e:
    print(f"⚠️ API Provider Manager: Error loading .env file: {e}")


class TokenOptimizer:
    """Mock class nếu không import được từ token_optimizer_v1"""

    @staticmethod
    def optimize(prompt: str) -> str:
        return prompt[:5000]  # Giả lập cắt bớt prompt dài


class UnifiedAPIManager:
    """Unified API Manager for multiple providers (DeepSeek, OpenRouter, OpenAI, Ollama)."""

    def __init__(
        self,
        model_preferences: Optional[List[str]] = None,
        fallback_model: str = "gpt-3.5-turbo",
    ):
        """
        Initialize Unified API Manager.

        Args:
            model_preferences: List of preferred models (e.g., ['deepseek-coder', 'gpt-4o'])
            fallback_model: Fallback model when main models fail
        """
        self.model_preferences = model_preferences or [
            "gemma2:2b",           # Local model for simple questions
            "deepseek-coder:6.7b", # Local model for coding questions  
            "deepseek-chat"        # Cloud model for complex questions
        ]  # Default to local models first
        self.fallback_model = fallback_model or "gemma2:2b"

        # Initialize common utilities
        self.logger = get_module_logger("api_provider_manager")
        self.config = load_module_config(
            "api_provider_manager", "config/api_provider_config.json"
        )

        # HTTP client configuration
        http_config = HTTPClientConfig(
            timeout=30.0,
            max_retries=3,
            retry_delay=1.0,
            default_headers={"User-Agent": "StillMe-API-Provider/2.1.1"},
        )
        self.http_client = AsyncHttpClient(http_config)

        # Provider configuration
        self.preferred_provider = os.getenv(
            "PREFERRED_PROVIDER", "deepseek"
        )  # Default to DeepSeek

        # API clients
        self.openai_client = (
            OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
            if os.getenv("OPENAI_API_KEY")
            else None
        )

        # API keys
        self.deepseek_api_key = os.getenv("DEEPSEEK_API_KEY")
        self.openrouter_api_key = os.getenv("OPENROUTER_API_KEY")

        # Translation configuration
        self.translation_core_lang = os.getenv("TRANSLATION_CORE_LANG", "en")
        self.translator_priority = os.getenv("TRANSLATOR_PRIORITY", "gemma,nllb").split(",")
        self.nllb_model_name = os.getenv("NLLB_MODEL_NAME", "facebook/nllb-200-distilled-600M")
        
        # Translation models (lazy loaded)
        self._nllb_model = None
        self._nllb_tokenizer = None

        # Usage stats
        self.usage_stats: Dict[str, Dict] = {}
        self.logger = logging.getLogger("UnifiedAPIManager")
        self.logger.setLevel(logging.INFO)

        # Log initialization status
        self._log_provider_status()

    def _log_provider_status(self):
        """Log the status of all API providers."""
        self.logger.info(
            f"🔧 Unified API Manager initialized with preferred provider: {self.preferred_provider}"
        )

        # Check DeepSeek
        if self.deepseek_api_key:
            self.logger.info("✅ DeepSeek API key configured")
        else:
            self.logger.warning("⚠️ DeepSeek API key not configured")

        # Check OpenRouter
        if self.openrouter_api_key:
            self.logger.info("✅ OpenRouter API key configured (legacy)")
        else:
            self.logger.info("ℹ️ OpenRouter API key not configured (legacy)")

        # Check OpenAI
        if self.openai_client:
            self.logger.info("✅ OpenAI API key configured (legacy)")
        else:
            self.logger.info("ℹ️ OpenAI API key not configured (legacy)")

    def choose_model(self, prompt: str) -> str:
        """Chọn model tối ưu dựa trên prompt và model preferences."""
        prompt_lower = prompt.lower()
        prompt_len = len(prompt)

        # Rule 1: Câu hỏi đơn giản → dùng gemma2:2b (local)
        simple_keywords = ["chào", "xin chào", "bạn tên gì", "bạn là ai", "2+2", "bằng mấy", "thủ đô", "là gì"]
        if any(keyword in prompt_lower for keyword in simple_keywords):
            if "gemma2:2b" in self.model_preferences:
                return "gemma2:2b"

        # Rule 2: Câu hỏi về code → dùng deepseek-coder:6.7b (local)
        code_keywords = ["code", "lập trình", "python", "javascript", "viết code", "debug", "lỗi", "function", "class"]
        if any(keyword in prompt_lower for keyword in code_keywords):
            if "deepseek-coder:6.7b" in self.model_preferences:
                return "deepseek-coder:6.7b"

        # Rule 3: Prompt dài > 3000 token → dùng local model để tiết kiệm cost
        if prompt_len > 3000:
            if "deepseek-coder:6.7b" in self.model_preferences:
                return "deepseek-coder:6.7b"
            elif "gemma2:2b" in self.model_preferences:
                return "gemma2:2b"

        # Rule 4: AI-Powered Complexity Analysis
        complexity_score = self._analyze_complexity(prompt)
        self.logger.info(f"🧠 Complexity Analysis: {complexity_score:.2f} for prompt: {prompt[:50]}...")
        
        # High complexity (score >= 0.7) → use cloud model
        if complexity_score >= 0.7:
            if "deepseek-chat" in self.model_preferences:
                self.logger.info(f"🎯 Selected deepseek-chat (high complexity: {complexity_score:.2f})")
                return "deepseek-chat"
        
        # Medium complexity (score >= 0.4) → use local coder model
        elif complexity_score >= 0.4:
            if "deepseek-coder:6.7b" in self.model_preferences:
                self.logger.info(f"🎯 Selected deepseek-coder:6.7b (medium complexity: {complexity_score:.2f})")
                return "deepseek-coder:6.7b"
        
        # Low complexity → use simple local model
        else:
            if "gemma2:2b" in self.model_preferences:
                self.logger.info(f"🎯 Selected gemma2:2b (low complexity: {complexity_score:.2f})")
                return "gemma2:2b"

        # Rule 5: Fallback theo thứ tự ưu tiên (local first)
        for model in self.model_preferences:
            if model in ["gemma2:2b", "deepseek-coder:6.7b", "deepseek-chat"]:
                return model

        # Final fallback - ensure we always return a string
        return self.fallback_model

    def _analyze_complexity(self, prompt: str) -> float:
        """Analyze prompt complexity using multiple heuristics (0.0 = simple, 1.0 = complex)."""
        prompt_lower = prompt.lower()
        complexity_score = 0.0
        
        # Heuristic 1: Length analysis
        word_count = len(prompt.split())
        if word_count > 50:
            complexity_score += 0.3
        elif word_count > 20:
            complexity_score += 0.2
        elif word_count > 10:
            complexity_score += 0.1
        
        # Heuristic 2: Question complexity indicators
        complex_indicators = [
            "tại sao", "như thế nào", "phân tích", "so sánh", "đánh giá", 
            "giải thích", "mối quan hệ", "tác động", "ảnh hưởng", "nguyên nhân",
            "hậu quả", "xu hướng", "phát triển", "tiến hóa", "biến đổi"
        ]
        for indicator in complex_indicators:
            if indicator in prompt_lower:
                complexity_score += 0.1
        
        # Heuristic 3: Academic/scientific terms
        academic_terms = [
            "định lý", "định luật", "nguyên lý", "khái niệm", "lý thuyết",
            "phương pháp", "kỹ thuật", "công nghệ", "hệ thống", "mô hình",
            "thuật toán", "cấu trúc", "chức năng", "quy trình", "quy tắc"
        ]
        for term in academic_terms:
            if term in prompt_lower:
                complexity_score += 0.15
        
        # Heuristic 4: Abstract concepts
        abstract_concepts = [
            "ý nghĩa", "bản chất", "triết lý", "tư tưởng", "quan điểm", 
            "góc độ", "khía cạnh", "chiều sâu", "tầm nhìn", "viễn cảnh",
            "tương lai", "quá khứ", "hiện tại", "bối cảnh", "môi trường"
        ]
        for concept in abstract_concepts:
            if concept in prompt_lower:
                complexity_score += 0.2
        
        # Heuristic 5: Multi-part questions
        if "?" in prompt and prompt.count("?") > 1:
            complexity_score += 0.2
        
        # Heuristic 6: Conditional or hypothetical questions
        conditional_words = ["nếu", "giả sử", "trường hợp", "khi nào", "trong trường hợp"]
        for word in conditional_words:
            if word in prompt_lower:
                complexity_score += 0.15
        
        # Heuristic 7: Domain-specific complexity
        domain_terms = [
            "toán học", "triết học", "khoa học", "vật lý", "hóa học", "sinh học",
            "lịch sử", "văn học", "nghệ thuật", "âm nhạc", "kiến trúc", 
            "tâm lý học", "xã hội học", "kinh tế học", "chính trị", "luật pháp"
        ]
        for domain in domain_terms:
            if domain in prompt_lower:
                complexity_score += 0.25
        
        # Cap the score at 1.0
        return min(complexity_score, 1.0)

    def _ensure_nllb(self):
        """Lazy load NLLB model and tokenizer"""
        if getattr(self, "_nllb_model", None) is None:
            try:
                from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
                self.logger.info(f"🔄 Loading NLLB model: {self.nllb_model_name}")
                self._nllb_tokenizer = AutoTokenizer.from_pretrained(self.nllb_model_name)
                self._nllb_model = AutoModelForSeq2SeqLM.from_pretrained(self.nllb_model_name)
                self.logger.info("✅ NLLB model loaded successfully")
            except ImportError:
                self.logger.warning("⚠️ transformers not installed, NLLB translation unavailable")
                self._nllb_model = None
                self._nllb_tokenizer = None
            except Exception as e:
                self.logger.error(f"❌ Failed to load NLLB model: {e}")
                self._nllb_model = None
                self._nllb_tokenizer = None
        return self._nllb_model, self._nllb_tokenizer

    def _mask_code_and_urls(self, text: str) -> tuple:
        """Mask code blocks and URLs before translation"""
        import re
        
        # Mask code blocks
        code_pattern = r'```[\s\S]*?```'
        code_blocks = re.findall(code_pattern, text)
        masked_text = re.sub(code_pattern, 'CODE_BLOCK_PLACEHOLDER', text)
        
        # Mask URLs
        url_pattern = r'https?://[^\s]+'
        urls = re.findall(url_pattern, masked_text)
        masked_text = re.sub(url_pattern, 'URL_PLACEHOLDER', masked_text)
        
        return masked_text, code_blocks, urls

    def _unmask_code_and_urls(self, text: str, code_blocks: list, urls: list) -> str:
        """Restore code blocks and URLs after translation"""
        import re
        
        # Restore URLs first
        for url in urls:
            text = text.replace('URL_PLACEHOLDER', url, 1)
        
        # Restore code blocks
        for code_block in code_blocks:
            text = text.replace('CODE_BLOCK_PLACEHOLDER', code_block, 1)
        
        return text

    def _evaluate_translation_confidence(self, original: str, translated: str, src_lang: str, tgt_lang: str) -> float:
        """Evaluate translation confidence using heuristics"""
        if not translated or not original:
            return 0.0
        
        # Length ratio check
        length_ratio = len(translated) / len(original)
        if length_ratio < 0.5 or length_ratio > 1.8:
            return 0.3
        
        # Same text check (for different languages)
        if src_lang != tgt_lang and original.strip() == translated.strip():
            return 0.2
        
        # Basic confidence based on length ratio
        if 0.7 <= length_ratio <= 1.3:
            return 0.8
        elif 0.5 <= length_ratio <= 1.5:
            return 0.6
        else:
            return 0.4

    def translate(self, text: str, src_lang: str, tgt_lang: str, quality_hint: str = None) -> dict:
        """
        Translate text using local-first approach: Gemma -> NLLB fallback
        Returns: {"text": str, "engine": "gemma|nllb", "confidence": float}
        """
        if not text or src_lang == tgt_lang:
            return {"text": text, "engine": "none", "confidence": 1.0}
        
        # Mask code and URLs
        masked_text, code_blocks, urls = self._mask_code_and_urls(text)
        
        # Try Gemma first if in priority
        if "gemma" in self.translator_priority:
            try:
                # Use existing Gemma model for translation
                gemma_prompt = f"Translate the following {src_lang} text to {tgt_lang}: {masked_text}"
                gemma_response = self.call_ollama_api(gemma_prompt, model="gemma2:2b")
                
                if gemma_response and not gemma_response.startswith("Error:"):
                    # Unmask and evaluate
                    gemma_translated = self._unmask_code_and_urls(gemma_response, code_blocks, urls)
                    confidence = self._evaluate_translation_confidence(masked_text, gemma_response, src_lang, tgt_lang)
                    
                    if confidence >= 0.5:  # Acceptable confidence
                        return {"text": gemma_translated, "engine": "gemma", "confidence": confidence}
            except Exception as e:
                self.logger.warning(f"Gemma translation failed: {e}")
        
        # Fallback to NLLB
        if "nllb" in self.translator_priority:
            try:
                model, tokenizer = self._ensure_nllb()
                if model and tokenizer:
                    self.logger.info(f"🔄 NLLB: Translating from {src_lang} to {tgt_lang}")
                    
                    # NLLB language codes mapping
                    lang_codes = {
                        "en": "eng_Latn", "vi": "vie_Latn", "ja": "jpn_Jpan", 
                        "zh": "zho_Hans", "ko": "kor_Hang", "fr": "fra_Latn",
                        "de": "deu_Latn", "es": "spa_Latn", "ru": "rus_Cyrl"
                    }
                    
                    src_code = lang_codes.get(src_lang, "eng_Latn")
                    tgt_code = lang_codes.get(tgt_lang, "eng_Latn")
                    
                    self.logger.info(f"🔄 NLLB: Using codes {src_code} -> {tgt_code}")
                    
                    # Set source language
                    tokenizer.src_lang = src_code
                    
                    # Tokenize input
                    inputs = tokenizer(masked_text, return_tensors="pt")
                    self.logger.info(f"🔄 NLLB: Tokenized input, shape: {inputs['input_ids'].shape}")
                    
                    # Generate translation - simplified approach
                    generated_tokens = model.generate(
                        **inputs, 
                        max_length=512, 
                        num_beams=4, 
                        early_stopping=True,
                        do_sample=False
                    )
                    
                    self.logger.info(f"🔄 NLLB: Generated tokens, shape: {generated_tokens.shape}")
                    
                    # Decode translation
                    nllb_translated = tokenizer.batch_decode(generated_tokens, skip_special_tokens=True)[0]
                    self.logger.info(f"🔄 NLLB: Raw translation: {nllb_translated[:100]}...")
                    
                    # Unmask and evaluate
                    final_translated = self._unmask_code_and_urls(nllb_translated, code_blocks, urls)
                    confidence = self._evaluate_translation_confidence(masked_text, nllb_translated, src_lang, tgt_lang)
                    
                    self.logger.info(f"✅ NLLB: Final translation: {final_translated[:100]}... (confidence: {confidence:.2f})")
                    return {"text": final_translated, "engine": "nllb", "confidence": confidence}
            except Exception as e:
                self.logger.error(f"NLLB translation failed: {e}")
                import traceback
                self.logger.error(f"NLLB traceback: {traceback.format_exc()}")
        
        # Fallback: return original text
        return {"text": text, "engine": "none", "confidence": 0.0}

    def _translate_coding_prompt(self, prompt: str) -> str:
        """Translate Vietnamese coding prompts to English for better model performance."""
        # Simple translation mapping for common coding requests
        translations = {
            "viết code python để tính tổng 2 số": "write python code to add two numbers",
            "viết code python": "write python code",
            "tạo function": "create function",
            "tính tổng": "calculate sum",
            "tính toán": "calculate",
            "lập trình": "programming",
            "debug": "debug",
            "sửa lỗi": "fix error",
            "tối ưu": "optimize",
            "thuật toán": "algorithm"
        }
        
        # Check for exact matches first
        prompt_lower = prompt.lower()
        for vi, en in translations.items():
            if vi in prompt_lower:
                return prompt.replace(vi, en)
        
        # If no exact match, add English instruction
        return f"Please write code for: {prompt}. Respond in English with code examples."

    def call_deepseek_api(self, prompt: str) -> str:
        """
        Call DeepSeek API with synchronous requests.

        Args:
            prompt: Input prompt

        Returns:
            API response content
        """
        if not self.deepseek_api_key:
            return "Error: DEEPSEEK_API_KEY not found in environment"

        try:
            url = "https://api.deepseek.com/v1/chat/completions"
            headers = {
                "Authorization": f"Bearer {self.deepseek_api_key}",
                "Content-Type": "application/json",
            }

            # Check if prompt already contains system prompt
            if "Bạn là StillMe AI" in prompt:
                # Prompt already has system prompt, use it as user message
                messages = [{"role": "user", "content": prompt}]
            else:
                # Add system prompt
                messages = [
                    {
                        "role": "system",
                        "content": "Bạn là StillMe AI, một trợ lý AI thân thiện và hữu ích.\n\nQUAN TRỌNG: \n- Trả lời ngắn gọn, tự nhiên, không dài dòng\n- Dùng xưng hô trung tính 'mình/bạn'\n- KHÔNG giới thiệu về nguồn gốc, OpenAI, Google, DeepSeek\n- KHÔNG nói về \"được khởi xướng bởi Anh Nguyễn\"\n- Chỉ trả lời câu hỏi một cách đơn giản và hữu ích\n\nVí dụ: Khi người dùng chào, chỉ trả lời \"Mình chào bạn! Rất vui được gặp bạn.\"",
                    },
                    {"role": "user", "content": prompt},
                ]

            payload = {
                "model": "deepseek-chat",
                "messages": messages,
                "temperature": 0.7,
                "max_tokens": 500,
                "stream": False,
            }

            self.logger.info(f"Calling DeepSeek API with prompt: {prompt[:50]}...")

            # Use synchronous requests for compatibility
            import requests

            response = requests.post(url, headers=headers, json=payload, timeout=30)
            response.raise_for_status()

            data = response.json()
            if data and "choices" in data and len(data["choices"]) > 0:
                content = data["choices"][0]["message"]["content"]
            else:
                content = "No response content available"

            self.logger.info("DeepSeek API call successful")
            return content

        except APIError as e:
            self.logger.error(f"DeepSeek API error: {e}")
            return "Error: DeepSeek API failed"

        except NetworkError as e:
            self.logger.error(f"DeepSeek network error: {e}")
            return "Error: Network issue with DeepSeek API"

        except Exception as e:
            self.logger.error(f"DeepSeek unexpected error: {e}")
            return "Error: Unexpected error with DeepSeek API"

    def get_response(self, prompt: str, max_retries: int = 2) -> str:
        """
        Get AI response using intelligent model routing.

        Args:
            prompt: Input prompt
            max_retries: Maximum retry attempts

        Returns:
            AI response or error message
        """
        optimized_prompt = (
            TokenOptimizer.optimize(prompt) if "TokenOptimizer" in globals() else prompt
        )

        # Use intelligent model selection
        selected_model = self.choose_model(optimized_prompt)
        self.logger.info(f"🧠 Selected model: {selected_model} for prompt: {optimized_prompt[:50]}...")

        # Route to appropriate provider based on selected model
        if selected_model == "gemma2:2b":
            return self.call_ollama_api(optimized_prompt)
        elif selected_model == "deepseek-coder:6.7b":
            return self.call_ollama_api(optimized_prompt)
        elif selected_model == "deepseek-chat":
            return self.call_deepseek_api(optimized_prompt)
        elif self.preferred_provider == "ollama":
            try:
                return self.call_ollama_api(optimized_prompt)
            except Exception as e:
                self.logger.warning(f"Ollama API failed, falling back to DeepSeek: {e}")
                return self.call_deepseek_api(optimized_prompt)
        else:
            # Fallback to DeepSeek if unknown provider
            self.logger.warning(
                f"Unknown provider: {self.preferred_provider}, falling back to DeepSeek"
            )
            return self.call_deepseek_api(optimized_prompt)

    def call_api(self, prompt: str, max_retries: int = 2) -> str:
        """
        Legacy method - redirects to get_response for backward compatibility.
        """
        return self.get_response(prompt, max_retries)

    def get_ai_response_stream(self, prompt: str) -> str:
        """
        Get AI response for streaming (compatibility method).
        """
        return self.get_response(prompt)

    def call_openrouter_api(self, prompt: str) -> str:
        """Call OpenRouter API (legacy method)."""
        return "Error: OpenRouter API not implemented in UnifiedAPIManager"

    def call_openai_api(self, prompt: str) -> str:
        """Call OpenAI API (legacy method)."""
        return "Error: OpenAI API not implemented in UnifiedAPIManager"

    def call_ollama_api(self, prompt: str, model: Optional[str] = None) -> str:
        """Call Ollama API using modern /api/chat endpoint."""
        try:
            # Determine model to use
            selected_model = model or self.choose_model(prompt)
            
            # For coding models, translate Vietnamese prompts to English
            processed_prompt = prompt
            if selected_model == "deepseek-coder:6.7b":
                processed_prompt = self._translate_coding_prompt(prompt)
            
            # Use modern /api/chat endpoint with proper payload
            payload = {
                "model": selected_model,
                "messages": [{"role": "user", "content": processed_prompt}],
                "stream": False,
            }

            self.logger.info(
                f"Ollama: Calling model {selected_model} with prompt: {prompt[:50]}..."
            )

            # Use synchronous requests for compatibility
            import requests

            response = requests.post(
                "http://localhost:11434/api/chat", 
                json=payload, 
                timeout=60
            )

            response.raise_for_status()
            data = response.json()

            self.logger.info(f"Ollama: Received response from {selected_model}")
            if data:
                return data.get("message", {}).get("content", "No response from Ollama")
            else:
                return "No response from Ollama"

        except NetworkError as e:
            self.logger.error(f"Ollama network error: {e}")
            return "Error: Failed to connect to Ollama API"
        except Exception as e:
            self.logger.error(f"Ollama error: {e}")
            return "Error: Unexpected error with Ollama API"

    def get_status(self) -> Dict[str, Any]:
        """Get API manager status."""
        return {
            "preferred_provider": self.preferred_provider,
            "deepseek_available": bool(self.deepseek_api_key),
            "openrouter_available": bool(self.openrouter_api_key),
            "openai_available": bool(self.openai_client),
            "model_preferences": self.model_preferences,
            "fallback_model": self.fallback_model,
        }

    def simulate_call(self, prompt: str) -> str:
        """Mock API response cho mục đích testing."""
        return f"Mock response for: {prompt[:50]}..."

    def analyze_usage(self) -> Dict[str, Dict]:
        """Phân tích thống kê sử dụng API."""
        return self.usage_stats

    def _log_call(
        self, model: str, prompt: str, response: str, elapsed_time: float, success: bool
    ):
        """Ghi log và cập nhật thống kê."""
        log_entry = {
            "model": model,
            "prompt_length": len(prompt),
            "response_length": len(response),
            "elapsed_time": elapsed_time,
            "success": success,
            "timestamp": time.time(),
        }

        if model not in self.usage_stats:
            self.usage_stats[model] = {
                "total_calls": 0,
                "total_time": 0.0,
                "success_calls": 0,
            }

        self.usage_stats[model]["total_calls"] += 1
        self.usage_stats[model]["total_time"] += elapsed_time
        if success:
            self.usage_stats[model]["success_calls"] += 1

        self.logger.info(
            f"API Call - Model: {model} | "
            f"Time: {elapsed_time:.2f}s | "
            f"Prompt: {len(prompt)} chars | "
            f"Success: {success}"
        )
