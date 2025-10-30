# modules/api_provider_manager.py
import logging
import os

# Import common utilities
import sys
import time
from typing import Any

try:
    from openai import OpenAI
except ImportError:
    print("⚠️ OpenAI not available. Install with: pip install openai")
    OpenAI = None

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


class ComplexityAnalyzer:
    """Optimized complexity analyzer with weighted scoring and fallback mechanism."""

    def __init__(self):
        # Pre-compile keyword sets for O(1) lookup performance
        self.complex_indicators: set[str] = {
            "tại sao",
            "như thế nào",
            "phân tích",
            "so sánh",
            "đánh giá",
            "giải thích",
            "mối quan hệ",
            "tác động",
            "ảnh hưởng",
            "nguyên nhân",
            "hậu quả",
            "xu hướng",
            "phát triển",
            "tiến hóa",
            "biến đổi",
            "tối ưu",
            "tối ưu hóa",
            "performance",
            "efficiency",
            "algorithm",
        }

        self.academic_terms: set[str] = {
            "định lý",
            "định luật",
            "nguyên lý",
            "khái niệm",
            "lý thuyết",
            "phương pháp",
            "kỹ thuật",
            "công nghệ",
            "hệ thống",
            "mô hình",
            "thuật toán",
            "cấu trúc",
            "chức năng",
            "quy trình",
            "quy tắc",
            "bất toàn",
            "gödel",
            "turing",
            "einstein",
            "newton",
            "darwin",
            "hypothesis",
            "theorem",
            "proof",
            "axiom",
            "paradigm",
            "giai thừa",
            "factorial",
            "recursion",
            "iteration",
            "loop",
        }

        self.abstract_concepts: set[str] = {
            "ý nghĩa",
            "bản chất",
            "triết lý",
            "tư tưởng",
            "quan điểm",
            "góc độ",
            "khía cạnh",
            "chiều sâu",
            "tầm nhìn",
            "viễn cảnh",
            "tương lai",
            "quá khứ",
            "hiện tại",
            "bối cảnh",
            "môi trường",
        }

        self.conditional_words: set[str] = {
            "nếu",
            "giả sử",
            "trường hợp",
            "khi nào",
            "trong trường hợp",
        }

        self.domain_terms: set[str] = {
            "toán học",
            "triết học",
            "khoa học",
            "vật lý",
            "hóa học",
            "sinh học",
            "lịch sử",
            "văn học",
            "nghệ thuật",
            "âm nhạc",
            "kiến trúc",
            "tâm lý học",
            "xã hội học",
            "kinh tế học",
            "chính trị",
            "luật pháp",
        }

        # Weighted scoring system (configurable via environment)
        self.weights = {
            "length": float(os.getenv("COMPLEXITY_WEIGHT_LENGTH", "0.15")),
            "complex_indicators": float(
                os.getenv("COMPLEXITY_WEIGHT_INDICATORS", "0.25")
            ),
            "academic_terms": float(os.getenv("COMPLEXITY_WEIGHT_ACADEMIC", "0.35")),
            "abstract_concepts": float(os.getenv("COMPLEXITY_WEIGHT_ABSTRACT", "0.3")),
            "multi_part": float(os.getenv("COMPLEXITY_WEIGHT_MULTIPART", "0.15")),
            "conditional": float(os.getenv("COMPLEXITY_WEIGHT_CONDITIONAL", "0.2")),
            "domain_specific": float(os.getenv("COMPLEXITY_WEIGHT_DOMAIN", "0.4")),
        }

        # Thresholds for model selection (configurable)
        self.thresholds = {
            "simple": float(os.getenv("COMPLEXITY_THRESHOLD_SIMPLE", "0.4")),
            "medium": float(os.getenv("COMPLEXITY_THRESHOLD_MEDIUM", "0.7")),
        }

        # Fallback tracking
        self.fallback_log: list[dict] = []
        self.max_fallback_log = 1000

        # Performance tracking
        self.analysis_times: list[float] = []
        self.max_performance_log = 100

    def analyze_complexity(
        self, prompt: str, debug: bool = False
    ) -> tuple[float, dict[str, float]]:
        """
        Analyze prompt complexity using weighted heuristics.

        Args:
            prompt: Input prompt to analyze
            debug: Whether to return detailed breakdown

        Returns:
            Tuple of (complexity_score, detailed_scores)
        """
        start_time = time.time()

        prompt_lower = prompt.lower()
        detailed_scores = {}

        # Heuristic 1: Length analysis (weighted)
        word_count = len(prompt.split())
        if word_count > 50:
            length_score = 0.8
        elif word_count > 20:
            length_score = 0.5
        elif word_count > 10:
            length_score = 0.3
        else:
            length_score = 0.0
        detailed_scores["length"] = length_score

        # Heuristic 2: Complex indicators (weighted)
        indicator_count = sum(
            1 for indicator in self.complex_indicators if indicator in prompt_lower
        )
        indicator_score = min(indicator_count * 0.3, 1.0)
        detailed_scores["complex_indicators"] = indicator_score

        # Heuristic 3: Academic terms (weighted)
        academic_count = sum(1 for term in self.academic_terms if term in prompt_lower)
        academic_score = min(academic_count * 0.4, 1.0)
        detailed_scores["academic_terms"] = academic_score

        # Heuristic 4: Abstract concepts (weighted)
        abstract_count = sum(
            1 for concept in self.abstract_concepts if concept in prompt_lower
        )
        abstract_score = min(abstract_count * 0.5, 1.0)
        detailed_scores["abstract_concepts"] = abstract_score

        # Heuristic 5: Multi-part questions (weighted)
        question_count = prompt.count("?")
        multipart_score = 0.8 if question_count > 1 else 0.0
        detailed_scores["multi_part"] = multipart_score

        # Heuristic 6: Conditional questions (weighted)
        conditional_count = sum(
            1 for word in self.conditional_words if word in prompt_lower
        )
        conditional_score = min(conditional_count * 0.4, 1.0)
        detailed_scores["conditional"] = conditional_score

        # Heuristic 7: Domain-specific terms (weighted)
        domain_count = sum(1 for domain in self.domain_terms if domain in prompt_lower)
        domain_score = min(domain_count * 0.5, 1.0)
        detailed_scores["domain_specific"] = domain_score

        # Calculate weighted final score
        final_score = (
            self.weights["length"] * length_score
            + self.weights["complex_indicators"] * indicator_score
            + self.weights["academic_terms"] * academic_score
            + self.weights["abstract_concepts"] * abstract_score
            + self.weights["multi_part"] * multipart_score
            + self.weights["conditional"] * conditional_score
            + self.weights["domain_specific"] * domain_score
        )

        # Cap the score at 1.0
        final_score = min(final_score, 1.0)

        # Track performance
        elapsed_time = time.time() - start_time
        self.analysis_times.append(elapsed_time)
        if len(self.analysis_times) > self.max_performance_log:
            self.analysis_times.pop(0)

        return final_score, detailed_scores

    def should_trigger_fallback(
        self,
        user_feedback: str,
        original_prompt: str,
        selected_model: str,
        response_quality: str = "unknown",
    ) -> bool:
        """
        Determine if fallback should be triggered based on user feedback.

        Args:
            user_feedback: User's response after AI answer
            original_prompt: Original user prompt
            selected_model: Model that was used
            response_quality: Quality assessment of the response

        Returns:
            True if fallback should be triggered
        """
        if not user_feedback:
            return False

        feedback_lower = user_feedback.lower()

        # Negative feedback indicators
        negative_indicators = {
            "sai",
            "không đúng",
            "không chính xác",
            "không hiểu",
            "???",
            "??",
            "không phải",
            "không đúng rồi",
            "sai rồi",
            "không đúng ý",
            "chưa đúng",
            "chưa chính xác",
            "thiếu",
            "không đầy đủ",
        }

        # Check for negative feedback
        has_negative = any(
            indicator in feedback_lower for indicator in negative_indicators
        )

        # Check for question marks (confusion)
        has_confusion = feedback_lower.count("?") >= 2

        # Check for very short responses (likely dissatisfaction)
        is_very_short = (
            len(user_feedback.strip()) < 10
            and any(word in feedback_lower for word in ["không", "sai"])
            and not any(
                word in feedback_lower for word in ["đúng", "ok", "cảm ơn", "tốt"]
            )
        )

        should_fallback = has_negative or has_confusion or is_very_short

        # Log fallback decision
        if should_fallback:
            fallback_entry = {
                "timestamp": time.time(),
                "original_prompt": original_prompt[:100],
                "selected_model": selected_model,
                "user_feedback": user_feedback[:100],
                "response_quality": response_quality,
                "trigger_reason": "negative"
                if has_negative
                else "confusion"
                if has_confusion
                else "short_response",
            }
            self.fallback_log.append(fallback_entry)

            # Keep log size manageable
            if len(self.fallback_log) > self.max_fallback_log:
                self.fallback_log.pop(0)

        return should_fallback

    def get_performance_stats(self) -> dict[str, Any]:
        """Get performance statistics for the analyzer."""
        if not self.analysis_times:
            return {"avg_time_ms": 0, "max_time_ms": 0, "min_time_ms": 0}

        avg_time = sum(self.analysis_times) / len(self.analysis_times)
        return {
            "avg_time_ms": round(avg_time * 1000, 2),
            "max_time_ms": round(max(self.analysis_times) * 1000, 2),
            "min_time_ms": round(min(self.analysis_times) * 1000, 2),
            "total_analyses": len(self.analysis_times),
        }

    def get_fallback_stats(self) -> dict[str, Any]:
        """Get fallback statistics."""
        if not self.fallback_log:
            return {"total_fallbacks": 0, "recent_fallbacks": []}

        # Group by model
        model_fallbacks = {}
        for entry in self.fallback_log:
            model = entry["selected_model"]
            model_fallbacks[model] = model_fallbacks.get(model, 0) + 1

        return {
            "total_fallbacks": len(self.fallback_log),
            "model_fallbacks": model_fallbacks,
            "recent_fallbacks": self.fallback_log[-10:],  # Last 10 fallbacks
        }

    def calibrate_weights(self, test_results: list[dict]) -> dict[str, float]:
        """
        Calibrate weights based on test results.

        Args:
            test_results: List of test cases with expected vs actual results

        Returns:
            Suggested new weights
        """
        # Simple calibration logic - can be enhanced with ML
        # For now, return current weights
        return self.weights.copy()


class UnifiedAPIManager:
    """Unified API Manager for multiple providers (DeepSeek, OpenRouter, OpenAI, Ollama)."""

    def __init__(
        self,
        model_preferences: list[str] | None = None,
        fallback_model: str = "gpt-3.5-turbo",
    ):
        """
        Initialize Unified API Manager.

        Args:
            model_preferences: List of preferred models (e.g., ['deepseek-coder', 'gpt-4o'])
            fallback_model: Fallback model when main models fail
        """
        self.model_preferences = model_preferences or [
            "gemma2:2b",  # Local model for simple questions
            "deepseek-coder:6.7b",  # Local model for coding questions
            "deepseek-chat",  # Cloud model for complex questions
        ]  # Default to local models first
        self.fallback_model = fallback_model or "gemma2:2b"

        # Initialize complexity analyzer
        self.complexity_analyzer = ComplexityAnalyzer()

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
        self.translator_priority = os.getenv("TRANSLATOR_PRIORITY", "gemma,nllb").split(
            ","
        )
        self.nllb_model_name = os.getenv(
            "NLLB_MODEL_NAME", "facebook/nllb-200-distilled-600M"
        )

        # Translation models (lazy loaded)
        self._nllb_model = None
        self._nllb_tokenizer = None

        # Usage stats
        self.usage_stats: dict[str, dict] = {}
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

    def choose_model(self, prompt: str, debug: bool = False) -> str:
        """Chọn model tối ưu dựa trên prompt và model preferences."""
        prompt_lower = prompt.lower()
        prompt_len = len(prompt)

        # Rule 1: Câu hỏi đơn giản → dùng gemma2:2b (local)
        simple_keywords = [
            "chào",
            "xin chào",
            "bạn tên gì",
            "bạn là ai",
            "2+2",
            "bằng mấy",
            "thủ đô",
            "là gì",
        ]
        if any(keyword in prompt_lower for keyword in simple_keywords):
            if "gemma2:2b" in self.model_preferences:
                self.logger.info("🎯 Selected gemma2:2b (simple keyword match)")
                return "gemma2:2b"

        # Rule 2: Câu hỏi về code → dùng deepseek-coder:6.7b (local)
        code_keywords = [
            "code",
            "lập trình",
            "python",
            "javascript",
            "viết code",
            "debug",
            "lỗi",
            "function",
            "class",
        ]
        if any(keyword in prompt_lower for keyword in code_keywords):
            if "deepseek-coder:6.7b" in self.model_preferences:
                self.logger.info("🎯 Selected deepseek-coder:6.7b (code keyword match)")
                return "deepseek-coder:6.7b"

        # Rule 3: Prompt dài > 3000 token → dùng local model để tiết kiệm cost
        if prompt_len > 3000:
            if "deepseek-coder:6.7b" in self.model_preferences:
                self.logger.info(
                    f"🎯 Selected deepseek-coder:6.7b (long prompt: {prompt_len} chars)"
                )
                return "deepseek-coder:6.7b"
            elif "gemma2:2b" in self.model_preferences:
                self.logger.info(
                    f"🎯 Selected gemma2:2b (long prompt: {prompt_len} chars)"
                )
                return "gemma2:2b"

        # Rule 4: AI-Powered Complexity Analysis (OPTIMIZED)
        complexity_score, detailed_scores = self.complexity_analyzer.analyze_complexity(
            prompt, debug
        )

        if debug:
            self.logger.info(f"🧠 Complexity Analysis (DEBUG): {complexity_score:.3f}")
            for heuristic, score in detailed_scores.items():
                self.logger.info(f"   {heuristic}: {score:.3f}")
        else:
            self.logger.info(
                f"🧠 Complexity Analysis: {complexity_score:.3f} for prompt: {prompt[:50]}..."
            )

        # High complexity (score >= 0.7) → use cloud model
        if complexity_score >= self.complexity_analyzer.thresholds["medium"]:
            if "deepseek-chat" in self.model_preferences:
                self.logger.info(
                    f"🎯 Selected deepseek-chat (high complexity: {complexity_score:.3f})"
                )
                return "deepseek-chat"

        # Medium complexity (score >= 0.4) → use local coder model
        elif complexity_score >= self.complexity_analyzer.thresholds["simple"]:
            if "deepseek-coder:6.7b" in self.model_preferences:
                self.logger.info(
                    f"🎯 Selected deepseek-coder:6.7b (medium complexity: {complexity_score:.3f})"
                )
                return "deepseek-coder:6.7b"

        # Low complexity → use simple local model
        else:
            if "gemma2:2b" in self.model_preferences:
                self.logger.info(
                    f"🎯 Selected gemma2:2b (low complexity: {complexity_score:.3f})"
                )
                return "gemma2:2b"

        # Rule 5: Fallback theo thứ tự ưu tiên (local first)
        for model in self.model_preferences:
            if model in ["gemma2:2b", "deepseek-coder:6.7b", "deepseek-chat"]:
                self.logger.info(f"🎯 Selected {model} (fallback)")
                return model

        # Final fallback - ensure we always return a string
        self.logger.warning(f"🎯 Using final fallback: {self.fallback_model}")
        return self.fallback_model

    def _analyze_complexity(self, prompt: str) -> float:
        """Legacy method - redirects to optimized analyzer."""
        complexity_score, _ = self.complexity_analyzer.analyze_complexity(prompt)
        return complexity_score

    def handle_fallback(
        self,
        original_prompt: str,
        user_feedback: str,
        selected_model: str,
        response_quality: str = "unknown",
    ) -> str | None:
        """
        Handle fallback when user feedback indicates poor response quality.

        Args:
            original_prompt: Original user prompt
            user_feedback: User's feedback after AI response
            selected_model: Model that was originally used
            response_quality: Quality assessment of the response

        Returns:
            New response from fallback model, or None if no fallback needed
        """
        if not self.complexity_analyzer.should_trigger_fallback(
            user_feedback, original_prompt, selected_model, response_quality
        ):
            return None

        self.logger.warning(f"🔄 Triggering fallback for model {selected_model}")

        # Use cloud model as fallback for better quality
        if (
            "deepseek-chat" in self.model_preferences
            and selected_model != "deepseek-chat"
        ):
            self.logger.info("🔄 Fallback: Using deepseek-chat for better quality")
            return self.call_deepseek_api(original_prompt)

        # If already using cloud model, try local coder model
        elif (
            "deepseek-coder:6.7b" in self.model_preferences
            and selected_model != "deepseek-coder:6.7b"
        ):
            self.logger.info("🔄 Fallback: Using deepseek-coder:6.7b")
            return self.call_ollama_api(original_prompt, model="deepseek-coder:6.7b")

        # Final fallback to simple model
        elif "gemma2:2b" in self.model_preferences and selected_model != "gemma2:2b":
            self.logger.info("🔄 Fallback: Using gemma2:2b")
            return self.call_ollama_api(original_prompt, model="gemma2:2b")

        return None

    def get_analyzer_stats(self) -> dict[str, Any]:
        """Get complexity analyzer statistics."""
        return {
            "performance": self.complexity_analyzer.get_performance_stats(),
            "fallback": self.complexity_analyzer.get_fallback_stats(),
            "weights": self.complexity_analyzer.weights,
            "thresholds": self.complexity_analyzer.thresholds,
        }

    def _ensure_nllb(self):
        """Lazy load NLLB model and tokenizer"""
        if getattr(self, "_nllb_model", None) is None:
            try:
                from transformers import AutoModelForSeq2SeqLM, AutoTokenizer

                self.logger.info(f"🔄 Loading NLLB model: {self.nllb_model_name}")
                self._nllb_tokenizer = AutoTokenizer.from_pretrained(
                    self.nllb_model_name
                )
                self._nllb_model = AutoModelForSeq2SeqLM.from_pretrained(
                    self.nllb_model_name
                )
                self.logger.info("✅ NLLB model loaded successfully")
            except ImportError:
                self.logger.warning(
                    "⚠️ transformers not installed, NLLB translation unavailable"
                )
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
        code_pattern = r"```[\s\S]*?```"
        code_blocks = re.findall(code_pattern, text)
        masked_text = re.sub(code_pattern, "CODE_BLOCK_PLACEHOLDER", text)

        # Mask URLs
        url_pattern = r"https?://[^\s]+"
        urls = re.findall(url_pattern, masked_text)
        masked_text = re.sub(url_pattern, "URL_PLACEHOLDER", masked_text)

        return masked_text, code_blocks, urls

    def _unmask_code_and_urls(self, text: str, code_blocks: list, urls: list) -> str:
        """Restore code blocks and URLs after translation"""

        # Restore URLs first
        for url in urls:
            text = text.replace("URL_PLACEHOLDER", url, 1)

        # Restore code blocks
        for code_block in code_blocks:
            text = text.replace("CODE_BLOCK_PLACEHOLDER", code_block, 1)

        return text

    def _evaluate_translation_confidence(
        self, original: str, translated: str, src_lang: str, tgt_lang: str
    ) -> float:
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

    def translate(
        self,
        text: str,
        src_lang: str,
        tgt_lang: str,
        quality_hint: str | None = None,
    ) -> dict:
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
                    gemma_translated = self._unmask_code_and_urls(
                        gemma_response, code_blocks, urls
                    )
                    confidence = self._evaluate_translation_confidence(
                        masked_text, gemma_response, src_lang, tgt_lang
                    )

                    if confidence >= 0.5:  # Acceptable confidence
                        return {
                            "text": gemma_translated,
                            "engine": "gemma",
                            "confidence": confidence,
                        }
            except Exception as e:
                self.logger.warning(f"Gemma translation failed: {e}")

        # Fallback to NLLB
        if "nllb" in self.translator_priority:
            try:
                model, tokenizer = self._ensure_nllb()
                if model and tokenizer:
                    self.logger.info(
                        f"🔄 NLLB: Translating from {src_lang} to {tgt_lang}"
                    )

                    # NLLB language codes mapping
                    lang_codes = {
                        "en": "eng_Latn",
                        "vi": "vie_Latn",
                        "ja": "jpn_Jpan",
                        "zh": "zho_Hans",
                        "ko": "kor_Hang",
                        "fr": "fra_Latn",
                        "de": "deu_Latn",
                        "es": "spa_Latn",
                        "ru": "rus_Cyrl",
                    }

                    src_code = lang_codes.get(src_lang, "eng_Latn")
                    tgt_code = lang_codes.get(tgt_lang, "eng_Latn")

                    self.logger.info(f"🔄 NLLB: Using codes {src_code} -> {tgt_code}")

                    # Set source language
                    tokenizer.src_lang = src_code

                    # Tokenize input
                    inputs = tokenizer(masked_text, return_tensors="pt")
                    self.logger.info(
                        f"🔄 NLLB: Tokenized input, shape: {inputs['input_ids'].shape}"
                    )

                    # Generate translation - simplified approach
                    generated_tokens = model.generate(
                        **inputs,
                        max_length=512,
                        num_beams=4,
                        early_stopping=True,
                        do_sample=False,
                    )

                    self.logger.info(
                        f"🔄 NLLB: Generated tokens, shape: {generated_tokens.shape}"
                    )

                    # Decode translation
                    nllb_translated = tokenizer.batch_decode(
                        generated_tokens, skip_special_tokens=True
                    )[0]
                    self.logger.info(
                        f"🔄 NLLB: Raw translation: {nllb_translated[:100]}..."
                    )

                    # Unmask and evaluate
                    final_translated = self._unmask_code_and_urls(
                        nllb_translated, code_blocks, urls
                    )
                    confidence = self._evaluate_translation_confidence(
                        masked_text, nllb_translated, src_lang, tgt_lang
                    )

                    self.logger.info(
                        f"✅ NLLB: Final translation: {final_translated[:100]}... (confidence: {confidence:.2f})"
                    )
                    return {
                        "text": final_translated,
                        "engine": "nllb",
                        "confidence": confidence,
                    }
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
            "thuật toán": "algorithm",
        }

        # Check for exact matches first
        prompt_lower = prompt.lower()
        for vi, en in translations.items():
            if vi in prompt_lower:
                return prompt.replace(vi, en)

        # If no exact match, add English instruction
        return (
            f"Please write code for: {prompt}. Respond in English with code examples."
        )

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
                        "content": 'Bạn là StillMe AI, một trợ lý AI thân thiện và hữu ích.\n\nQUAN TRỌNG: \n- Trả lời ngắn gọn, tự nhiên, không dài dòng\n- Dùng xưng hô trung tính \'mình/bạn\'\n- KHÔNG giới thiệu về nguồn gốc, OpenAI, Google, DeepSeek\n- KHÔNG nói về "được khởi xướng bởi Anh Nguyễn"\n- Chỉ trả lời câu hỏi một cách đơn giản và hữu ích\n\nVí dụ: Khi người dùng chào, chỉ trả lời "Mình chào bạn! Rất vui được gặp bạn."',
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
            try:
                import requests
            except ImportError:
                self.logger.error(
                    "❌ requests not available. Install with: pip install requests"
                )
                return "Error: requests library not available"

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
        self.logger.info(
            f"🧠 Selected model: {selected_model} for prompt: {optimized_prompt[:50]}..."
        )

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

    def call_ollama_api(self, prompt: str, model: str | None = None) -> str:
        """Call Ollama API using modern /api/chat endpoint."""
        try:
            # Determine model to use
            selected_model = model if model is not None else self.choose_model(prompt)

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
            try:
                import requests
            except ImportError:
                self.logger.error(
                    "❌ requests not available. Install with: pip install requests"
                )
                return "Error: requests library not available"

            response = requests.post(
                "http://localhost:11434/api/chat", json=payload, timeout=60
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

    def get_status(self) -> dict[str, Any]:
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

    def analyze_usage(self) -> dict[str, dict]:
        """Phân tích thống kê sử dụng API."""
        return self.usage_stats

    def _log_call(
        self, model: str, prompt: str, response: str, elapsed_time: float, success: bool
    ):
        """Ghi log và cập nhật thống kê."""
        {
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
