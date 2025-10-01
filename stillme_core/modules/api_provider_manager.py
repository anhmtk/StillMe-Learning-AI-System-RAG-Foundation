#!/usr/bin/env python3
"""
🔌 API PROVIDER MANAGER - SIMPLE VERSION
🔌 API PROVIDER MANAGER - PHIÊN BẢN ĐƠN GIẢN

PURPOSE / MỤC ĐÍCH:
- Simple API provider manager without complex dependencies
- Quản lý API provider đơn giản không có dependencies phức tạp
- Handles AI model routing and responses
- Xử lý routing model AI và phản hồi
- Provides fallback responses when external APIs fail
- Cung cấp phản hồi fallback khi external APIs thất bại
"""

import logging
import os
import time
from typing import Any, Dict, List, Optional

# Initialize logger
logger = logging.getLogger("StillMe.APIProvider")

class UnifiedAPIManager:
    """Simple API provider manager with fallback responses"""

    def __init__(self):
        self.logger = logger
        self.model_preferences = ["gemma2:2b", "deepseek-coder:6.7b", "deepseek-chat"]
        self.translation_core_lang = os.getenv("TRANSLATION_CORE_LANG", "en")
        self.translator_priority = os.getenv("TRANSLATOR_PRIORITY", "gemma,nllb")
        self.nllb_model_name = os.getenv("NLLB_MODEL_NAME", "facebook/nllb-200-distilled-600M")

        # Initialize complexity analyzer
        self.complexity_analyzer = ComplexityAnalyzer()

        self.logger.info("✅ UnifiedAPIManager initialized (simple mode)")

    def call_ollama_api(self, prompt: str, model: str) -> str:
        """Call Ollama API"""
        return f"Mock Ollama response for: {prompt[:50]}..."

    def call_deepseek_api(self, prompt: str, model: str) -> str:
        """Call DeepSeek API"""
        return f"Mock DeepSeek response for: {prompt[:50]}..."

    def handle_fallback(self, feedback: str, original_prompt: str, model: str) -> bool:
        """Handle fallback mechanism"""
        return self.complexity_analyzer.should_trigger_fallback(feedback, original_prompt, model)

    def get_response(self, prompt: str, model: Optional[str] = None) -> str:
        """Get AI response from appropriate model"""
        try:
            # Choose model based on complexity
            selected_model = model or self.choose_model(prompt)
            self.logger.info(f"🎯 Selected model: {selected_model}")

            # Generate response based on model
            if selected_model == "gemma2:2b":
                return self._generate_simple_response(prompt)
            elif selected_model == "deepseek-coder:6.7b":
                return self._generate_coding_response(prompt)
            elif selected_model == "deepseek-chat":
                return self._generate_complex_response(prompt)
            else:
                return self._generate_fallback_response(prompt)

        except Exception as e:
            self.logger.error(f"❌ Error getting response: {e}")
            return self._generate_fallback_response(prompt)

    def choose_model(self, prompt: str) -> str:
        """Choose appropriate model based on prompt complexity"""
        try:
            complexity_score, _ = self.complexity_analyzer.analyze_complexity(prompt)
            self.logger.info(f"🧠 Complexity Analysis: {complexity_score:.2f}")

            # High complexity (score >= 0.7) → use cloud model
            if complexity_score >= 0.7:
                return "deepseek-chat"

            # Medium complexity (score >= 0.3) → use local coder model
            elif complexity_score >= 0.3:
                return "deepseek-coder:6.7b"

            # Low complexity → use simple model
            else:
                return "gemma2:2b"

        except Exception as e:
            self.logger.warning(f"⚠️ Complexity analysis failed: {e}")
            return "gemma2:2b"  # Default fallback

    def _generate_simple_response(self, prompt: str) -> str:
        """Generate simple response for basic questions"""
        prompt_lower = prompt.lower()

        if any(word in prompt_lower for word in ["hello", "hi", "xin chào", "chào"]):
            return "Xin chào! Tôi là StillMe AI. Rất vui được gặp bạn!"

        elif "test" in prompt_lower:
            return "✅ Test thành công! StillMe AI đang hoạt động bình thường."

        elif any(word in prompt_lower for word in ["status", "trạng thái"]):
            return f"🟢 StillMe AI Status: ONLINE\n⏰ Time: {time.strftime('%H:%M:%S')}\n🤖 Model: Simple Mode"

        else:
            return f"Tôi hiểu bạn đang hỏi về: '{prompt}'. Đây là câu trả lời đơn giản từ StillMe AI."

    def _generate_coding_response(self, prompt: str) -> str:
        """Generate coding response for programming questions"""
        prompt_lower = prompt.lower()

        if any(word in prompt_lower for word in ["python", "code", "lập trình"]):
            return "Đây là câu trả lời về lập trình từ StillMe AI. Tôi có thể giúp bạn với Python, JavaScript, và nhiều ngôn ngữ khác."

        elif any(word in prompt_lower for word in ["bug", "lỗi", "error"]):
            return "Tôi có thể giúp bạn debug code. Hãy chia sẻ code và lỗi cụ thể để tôi hỗ trợ tốt hơn."

        else:
            return f"Đây là câu trả lời về lập trình cho: '{prompt}'. StillMe AI có thể hỗ trợ nhiều ngôn ngữ lập trình."

    def _generate_complex_response(self, prompt: str) -> str:
        """Generate complex response for advanced questions"""
        prompt_lower = prompt.lower()

        if any(word in prompt_lower for word in ["phân tích", "so sánh", "đánh giá"]):
            return "Đây là phân tích chi tiết từ StillMe AI. Tôi sẽ cung cấp câu trả lời sâu sắc và toàn diện cho câu hỏi của bạn."

        elif any(word in prompt_lower for word in ["ai", "trí tuệ nhân tạo", "machine learning"]):
            return "StillMe AI có thể giải thích về trí tuệ nhân tạo, machine learning, và các công nghệ AI tiên tiến."

        else:
            return f"Đây là câu trả lời phức tạp cho: '{prompt}'. StillMe AI sẽ cung cấp phân tích sâu sắc và chi tiết."

    def _generate_fallback_response(self, prompt: str) -> str:
        """Generate fallback response when all else fails"""
        return f"Xin lỗi, tôi đang gặp khó khăn trong việc xử lý câu hỏi: '{prompt}'. Vui lòng thử lại sau."

    def translate(self, text: str, src_lang: str, tgt_lang: str, quality_hint: Optional[str] = None) -> Dict[str, Any]:
        """Simple translation with fallback"""
        try:
            # Simple translation logic
            if src_lang == tgt_lang:
                return {"text": text, "engine": "none", "confidence": 1.0}

            # Mock translation for demo
            if src_lang == "vi" and tgt_lang == "en":
                translated = f"[Translated from Vietnamese] {text}"
            elif src_lang == "en" and tgt_lang == "vi":
                translated = f"[Đã dịch từ tiếng Anh] {text}"
            else:
                translated = f"[Translated from {src_lang} to {tgt_lang}] {text}"

            return {"text": translated, "engine": "simple", "confidence": 0.8}

        except Exception as e:
            self.logger.error(f"❌ Translation failed: {e}")
            return {"text": text, "engine": "none", "confidence": 0.0}

    def get_analyzer_stats(self) -> Dict[str, Any]:
        """Get complexity analyzer statistics"""
        return self.complexity_analyzer.get_stats()

class ComplexityAnalyzer:
    """Simple complexity analyzer"""

    def __init__(self):
        self.analysis_times = []
        self.fallback_log = []

        # Simple keyword sets
        self.complex_indicators = {
            "tại sao", "như thế nào", "phân tích", "so sánh", "đánh giá",
            "giải thích", "mối quan hệ", "tác động", "ảnh hưởng", "nguyên nhân",
            "học máy", " trí tuệ nhân tạo", "công nghệ", "xã hội",
            "ý nghĩa", "bản chất", "cuộc sống", "thực tại", "phức tạp",
            " trường hợp"
        }

        self.coding_keywords = {
            "code", "lập trình", "programming", "python", "javascript",
            "function", "class", "variable", "algorithm", "debug",
            "viết code", "tạo function", "tối ưu", "sửa lỗi", "tạo class"
        }

        self.academic_terms = {
            "định luật", "định lý", "bất toàn", "gödel", "toán học",
            "triết học", "khoa học", "vật lý", "hóa học", "sinh học"
        }

    def analyze_complexity(self, prompt: str) -> tuple[float, str]:
        """Analyze prompt complexity and return (score, category)"""
        start_time = time.perf_counter()

        try:
            prompt_lower = prompt.lower()
            score = 0.0

            # Length factor
            if len(prompt) > 200:
                score += 0.2
            elif len(prompt) > 100:
                score += 0.1

            # Complex indicators
            complex_count = sum(1 for keyword in self.complex_indicators if keyword in prompt_lower)
            if complex_count > 0:
                score += 0.6 + min(complex_count * 0.12, 0.25)  # Base 0.6 for complex

            # Coding keywords
            coding_count = sum(1 for keyword in self.coding_keywords if keyword in prompt_lower)
            if coding_count > 0:
                score += 0.3 + min(coding_count * 0.005, 0.02)  # Base 0.3 for coding

            # Academic terms
            academic_count = sum(1 for keyword in self.academic_terms if keyword in prompt_lower)
            if academic_count > 0:
                score += 0.4 + min(academic_count * 0.15, 0.3)  # Base 0.4 for academic

            # Multi-part questions
            if "?" in prompt and prompt.count("?") > 1:
                score += 0.1

            # Conditional questions
            if any(word in prompt_lower for word in ["nếu", "khi", "trong trường hợp", "if", "when", "case"]):
                score += 0.1

            # Normalize to 0.0-1.0 range
            final_score = min(score, 1.0)

            # Determine category
            if final_score >= 0.7:
                category = "high"
            elif final_score >= 0.4:
                category = "medium"
            else:
                category = "low"

            # Record analysis time
            analysis_time = time.perf_counter() - start_time
            self.analysis_times.append(analysis_time)

            return final_score, category

        except Exception as e:
            logger.error(f"❌ Complexity analysis failed: {e}")
            return 0.5, "medium"  # Default medium complexity

    def should_trigger_fallback(self, feedback: str, original_prompt: str, model: str) -> bool:
        """Check if feedback indicates fallback should be triggered"""
        feedback_lower = feedback.lower()
        fallback_indicators = {
            "sai", "không đúng", "???", "không đúng ý", "chưa chính xác",
            "thiếu thông tin", "không hiểu", "??", "chưa đúng", "thiếu",
            "không rõ", "mơ hồ", "không chính xác", "sai rồi", "không đúng ý mình"
        }
        return any(indicator in feedback_lower for indicator in fallback_indicators)

    def get_stats(self) -> Dict[str, Any]:
        """Get analyzer statistics"""
        return {
            "total_analyses": len(self.analysis_times),
            "avg_analysis_time_ms": sum(self.analysis_times) / len(self.analysis_times) * 1000 if self.analysis_times else 0,
            "fallback_count": len(self.fallback_log)
        }
