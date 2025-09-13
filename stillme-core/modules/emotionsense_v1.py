#!/usr/bin/env python3
"""
EmotionSenseV1 - AI Cảm xúc thông minh
Module nhận diện cảm xúc người dùng qua văn bản tiếng Việt
Tích hợp seamless với StillMe Framework
"""

import json
import os
import re

# Import common utilities
import sys
import time
from collections import defaultdict, deque
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

# Add project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from common import (
    AsyncHttpClient,
    ConfigManager,
    FileManager,
    get_logger,
)

# Import các thư viện được phép (không xung đột)
try:
    import torch
    from transformers import AutoModel, AutoTokenizer

    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False
    # Will initialize logger later

try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity

    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    # Will initialize logger later

# Constants
EMOTION_CATEGORIES = {
    "happy": "vui vẻ, tích cực, phấn khởi",
    "sad": "buồn bã, thất vọng, chán nản",
    "angry": "tức giận, bực bội, khó chịu",
    "fear": "sợ hãi, lo lắng, bất an",
    "surprise": "ngạc nhiên, bất ngờ",
    "neutral": "trung lập, khách quan",
    "confused": "bối rối, không hiểu",
}

LANGUAGE_SUPPORT = {
    "vi": "Tiếng Việt (ưu tiên cao)",
    "en": "Tiếng Anh (hỗ trợ cơ bản)",
    "auto": "Tự động phát hiện ngôn ngữ",
}

ERROR_CODES = {
    "EMOTION_001": "Model loading failed",
    "EMOTION_002": "Inference error",
    "EMOTION_003": "Language detection failed",
    "EMOTION_004": "Memory allocation failed",
    "EMOTION_005": "Integration timeout",
}


class EmotionSenseV1:
    """
    Module nhận diện cảm xúc thông minh
    Hỗ trợ tiếng Việt với độ chính xác cao
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Khởi tạo EmotionSense module"""
        # Initialize common utilities
        self.config_manager = ConfigManager("config/emotion_sense_config.json", {})
        self.logger = get_logger(
            "StillMe.EmotionSense", log_file="logs/emotion_sense.log", json_format=True
        )
        self.http_client = AsyncHttpClient()
        self.file_manager = FileManager()

        self.config = config or self._load_default_config()
        self.emotion_model = None
        self.tokenizer = None
        self.language_detector = None
        self.emotion_history: Dict[str, deque] = defaultdict(
            lambda: deque(maxlen=self.config.get("max_history_size", 1000))
        )
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.cache_size = self.config.get("cache_size", 10000)
        self.confidence_threshold = self.config.get("confidence_threshold", 0.6)

        # Log warnings for missing dependencies
        if not TORCH_AVAILABLE:
            self.logger.warning("PyTorch not available, using rule-based fallback")
        if not SKLEARN_AVAILABLE:
            self.logger.warning(
                "Scikit-learn not available, using basic keyword matching"
            )

        # Setup logging
        self._setup_logging()

        # Performance tracking
        self.performance_metrics = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "avg_inference_time": 0.0,
            "memory_usage": 0.0,
        }

        self.logger.info("EmotionSenseV1 initialized")

    def _load_default_config(self) -> Dict[str, Any]:
        """Load default configuration"""
        try:
            config_path = Path("config/emotion_config.json")
            if config_path.exists():
                with open(config_path, encoding="utf-8") as f:
                    return json.load(f).get("emotion_sense", {})
        except Exception as e:
            print(f"Failed to load config: {e}")

        # Return default config
        return {
            "confidence_threshold": 0.6,
            "max_history_size": 1000,
            "cache_size": 10000,
            "fallback_strategy": "neutral",
        }

    def _setup_logging(self):
        """Setup logging configuration using common logging"""
        from common.logging import get_module_logger

        self.logger = get_module_logger("emotionsense")

    async def initialize(self) -> bool:
        """Khởi tạo model và dependencies"""
        try:
            self.logger.info("Initializing EmotionSense models...")
            start_time = time.time()

            # Initialize language detector
            await self._initialize_language_detector()

            # Initialize emotion model
            if TORCH_AVAILABLE:
                await self._initialize_torch_models()
            else:
                await self._initialize_rule_based_models()

            # Initialize fallback models
            await self._initialize_fallback_models()

            init_time = time.time() - start_time
            self.logger.info(f"EmotionSense initialized in {init_time:.2f}s")

            return True

        except Exception as e:
            self.logger.error(f"Initialization failed: {e}")
            return False

    async def _initialize_language_detector(self):
        """Khởi tạo language detector"""
        try:
            # Simple language detection based on character patterns
            self.language_detector = self._detect_language_simple
            self.logger.info("Language detector initialized (simple pattern-based)")
        except Exception as e:
            self.logger.warning(f"Language detector initialization failed: {e}")
            self.language_detector = lambda x: "vi"  # Default to Vietnamese

    async def _initialize_torch_models(self):
        """Khởi tạo PyTorch models"""
        try:
            model_config = self.config.get("model_config", {})
            primary_model = model_config.get("primary_model", "phobert-base")

            # Try to load PhoBERT (Vietnamese-focused)
            try:
                self.tokenizer = AutoTokenizer.from_pretrained(primary_model)
                self.emotion_model = AutoModel.from_pretrained(primary_model)
                self.logger.info(f"Primary model loaded: {primary_model}")
            except Exception as e:
                self.logger.warning(f"Primary model failed: {e}")
                # Fallback to multilingual BERT
                fallback_model = model_config.get(
                    "fallback_model", "bert-base-multilingual-cased"
                )
                self.tokenizer = AutoTokenizer.from_pretrained(fallback_model)
                self.emotion_model = AutoModel.from_pretrained(fallback_model)
                self.logger.info(f"Fallback model loaded: {fallback_model}")

        except Exception as e:
            self.logger.error(f"PyTorch model initialization failed: {e}")
            raise

    async def _initialize_rule_based_models(self):
        """Khởi tạo rule-based models khi PyTorch không có sẵn"""
        try:
            # Initialize keyword-based emotion detection
            self.emotion_keywords = self.config.get("emotion_categories", {})

            if SKLEARN_AVAILABLE:
                # Initialize TF-IDF vectorizer for better matching
                self.vectorizer = TfidfVectorizer(
                    max_features=1000, stop_words=None, ngram_range=(1, 2)
                )
                self.logger.info("Rule-based model initialized with TF-IDF")
            else:
                self.logger.info(
                    "Rule-based model initialized (basic keyword matching)"
                )

        except Exception as e:
            self.logger.error(f"Rule-based model initialization failed: {e}")
            raise

    async def _initialize_fallback_models(self):
        """Khởi tạo fallback models"""
        try:
            # Basic fallback using keyword matching
            self.fallback_emotion_detector = self._detect_emotion_keyword_based
            self.logger.info("Fallback models initialized")
        except Exception as e:
            self.logger.warning(f"Fallback model initialization failed: {e}")

    def _detect_language_simple(self, text: str) -> str:
        """Simple language detection based on character patterns"""
        if not text:
            return "vi"

        # Vietnamese-specific characters
        vietnamese_chars = set(
            "àáạảãâầấậẩẫăằắặẳẵèéẹẻẽêềếệểễìíịỉĩòóọỏõôồốộổỗơờớợởỡùúụủũưừứựửữỳýỵỷỹđ"
        )

        # Count Vietnamese characters
        vi_count = sum(1 for char in text if char in vietnamese_chars)

        # Simple heuristic: if more than 20% are Vietnamese chars, it's Vietnamese
        if vi_count > len(text) * 0.2:
            return "vi"
        elif re.search(r"[a-zA-Z]", text):
            return "en"
        else:
            return "vi"  # Default to Vietnamese

    def detect_emotion(
        self, text: str, language: str = "auto", user_id: str = "default"
    ) -> Dict[str, Any]:
        """Nhận diện cảm xúc từ text"""
        start_time = time.time()

        try:
            # Update performance metrics
            self.performance_metrics["total_requests"] += 1

            # Validate input
            if not text or not text.strip():
                return self._create_emotion_result(
                    "neutral", 0.0, "Empty text", language
                )

            # Detect language if auto
            if language == "auto":
                language = (
                    self.language_detector(text) if self.language_detector else "vi"
                )

            # Try ML-based detection first
            if TORCH_AVAILABLE and self.emotion_model:
                result = self._detect_emotion_ml(text, language)
            else:
                result = self._detect_emotion_keyword_based(text, language)

            # Add to history
            self._add_to_history(user_id, text, result, language)

            # Update cache
            self._update_cache(text, result)

            # Update performance metrics
            inference_time = (time.time() - start_time) * 1000
            self._update_performance_metrics(inference_time, True)

            return result

        except Exception as e:
            self.logger.error(f"Emotion detection failed: {e}")
            self._update_performance_metrics(0, False)

            # Return fallback result
            return self._create_emotion_result(
                "neutral", 0.0, f"Error: {e!s}", language, error_code="EMOTION_002"
            )

    def _detect_emotion_ml(self, text: str, language: str) -> Dict[str, Any]:
        """Detect emotion using ML models"""
        try:
            # Tokenize input
            if not self.tokenizer:
                return self._create_emotion_result(
                    "neutral", 0.0, "Tokenizer not available", language
                )

            inputs = self.tokenizer(
                text, return_tensors="pt", max_length=512, truncation=True, padding=True
            )

            # Get embeddings
            if not self.emotion_model:
                return self._create_emotion_result(
                    "neutral", 0.0, "Emotion model not available", language
                )

            with torch.no_grad():
                outputs = self.emotion_model(**inputs)
                embeddings = outputs.last_hidden_state.mean(dim=1)

            # Simple emotion classification based on embeddings
            # This is a simplified version - in production, you'd have a trained classifier
            emotion_scores = self._classify_emotion_from_embeddings(
                embeddings, text, language
            )

            # Get best emotion
            best_emotion = max(emotion_scores.items(), key=lambda x: x[1])

            return self._create_emotion_result(
                best_emotion[0], best_emotion[1], "ML-based detection", language
            )

        except Exception as e:
            self.logger.warning(
                f"ML detection failed: {e}, falling back to keyword-based"
            )
            return self._detect_emotion_keyword_based(text, language)

    def _classify_emotion_from_embeddings(
        self, embeddings, text: str, language: str
    ) -> Dict[str, float]:
        """Classify emotion from embeddings using keyword enhancement"""
        emotion_scores = dict.fromkeys(EMOTION_CATEGORIES.keys(), 0.0)

        # Get emotion keywords for the detected language
        emotion_keywords = self.config.get("emotion_categories", {})

        # Enhance scores based on keywords
        for emotion, config in emotion_keywords.items():
            keywords = config.get(f"keywords_{language}", [])
            if not keywords:
                keywords = config.get("keywords_vi", [])  # Fallback to Vietnamese

            # Count keyword matches
            keyword_count = sum(
                1 for keyword in keywords if keyword.lower() in text.lower()
            )
            if keyword_count > 0:
                emotion_scores[emotion] += keyword_count * 0.3

        # Normalize scores
        max_score = max(emotion_scores.values()) if emotion_scores.values() else 1.0
        if max_score > 0:
            emotion_scores = {k: v / max_score for k, v in emotion_scores.items()}

        return emotion_scores

    def _detect_emotion_keyword_based(self, text: str, language: str) -> Dict[str, Any]:
        """Detect emotion using keyword-based approach"""
        try:
            emotion_scores = dict.fromkeys(EMOTION_CATEGORIES.keys(), 0.0)
            emotion_keywords = self.config.get("emotion_categories", {})

            # Convert text to lowercase for matching
            text_lower = text.lower()

            # Score each emotion based on keyword matches
            for emotion, config in emotion_keywords.items():
                keywords = config.get(f"keywords_{language}", [])
                if not keywords:
                    keywords = config.get("keywords_vi", [])  # Fallback to Vietnamese

                # Count keyword matches
                keyword_count = sum(
                    1 for keyword in keywords if keyword.lower() in text_lower
                )
                if keyword_count > 0:
                    emotion_scores[emotion] += keyword_count * 0.3

                # Additional scoring for emotional intensity words
                intensity_words = [
                    "rất",
                    "cực kỳ",
                    "vô cùng",
                    "tuyệt vời",
                    "kinh khủng",
                ]
                for intensity_word in intensity_words:
                    if intensity_word in text_lower:
                        emotion_scores[emotion] += 0.2

            # Get best emotion
            best_emotion = max(emotion_scores.items(), key=lambda x: x[1])

            # Apply confidence threshold
            if best_emotion[1] < self.confidence_threshold:
                best_emotion = ("neutral", 0.5)

            return self._create_emotion_result(
                best_emotion[0], best_emotion[1], "Keyword-based detection", language
            )

        except Exception as e:
            self.logger.error(f"Keyword-based detection failed: {e}")
            return self._create_emotion_result(
                "neutral", 0.0, f"Error: {e!s}", language
            )

    def _create_emotion_result(
        self,
        emotion: str,
        confidence: float,
        method: str,
        language: str,
        error_code: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Create standardized emotion result"""
        result = {
            "emotion": emotion,
            "confidence": confidence,
            "method": method,
            "language": language,
            "timestamp": datetime.now().isoformat(),
            "success": error_code is None,
        }

        if error_code:
            result["error_code"] = error_code
            result["error_message"] = ERROR_CODES.get(error_code, "Unknown error")

        return result

    def _add_to_history(
        self, user_id: str, text: str, result: Dict[str, Any], language: str
    ):
        """Add emotion detection result to user history"""
        try:
            history_entry = {
                "text": text,
                "emotion": result["emotion"],
                "confidence": result["confidence"],
                "language": language,
                "timestamp": datetime.now().isoformat(),
            }

            self.emotion_history[user_id].append(history_entry)

        except Exception as e:
            self.logger.warning(f"Failed to add to history: {e}")

    def _update_cache(self, text: str, result: Dict[str, Any]):
        """Update emotion detection cache"""
        try:
            # Simple text hash for cache key
            cache_key = str(hash(text))[:20]

            if len(self.cache) >= self.cache_size:
                # Remove oldest entries
                oldest_key = next(iter(self.cache))
                del self.cache[oldest_key]

            self.cache[cache_key] = result

        except Exception as e:
            self.logger.warning(f"Failed to update cache: {e}")

    def _update_performance_metrics(self, inference_time: float, success: bool):
        """Update performance metrics"""
        try:
            if success:
                self.performance_metrics["successful_requests"] += 1

                # Update average inference time
                total_successful = self.performance_metrics["successful_requests"]
                current_avg = self.performance_metrics["avg_inference_time"]
                self.performance_metrics["avg_inference_time"] = (
                    current_avg * (total_successful - 1) + inference_time
                ) / total_successful
            else:
                self.performance_metrics["failed_requests"] += 1

        except Exception as e:
            self.logger.warning(f"Failed to update performance metrics: {e}")

    def get_emotion_history(
        self, user_id: str, limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Lấy lịch sử cảm xúc của user"""
        try:
            if user_id not in self.emotion_history:
                return []

            history = list(self.emotion_history[user_id])
            return history[-limit:] if limit > 0 else history

        except Exception as e:
            self.logger.error(f"Failed to get emotion history: {e}")
            return []

    def analyze_emotion_pattern(self, user_id: str, days: int = 7) -> Dict[str, Any]:
        """Phân tích pattern cảm xúc theo thời gian"""
        try:
            if user_id not in self.emotion_history:
                return {"error": "No history found for user"}

            # Get recent history
            cutoff_date = datetime.now() - timedelta(days=days)
            recent_history = [
                entry
                for entry in self.emotion_history[user_id]
                if datetime.fromisoformat(entry["timestamp"]) > cutoff_date
            ]

            if not recent_history:
                return {"error": "No recent history found"}

            # Analyze patterns
            emotion_counts = defaultdict(int)
            confidence_sum = defaultdict(float)
            language_distribution = defaultdict(int)

            for entry in recent_history:
                emotion = entry["emotion"]
                emotion_counts[emotion] += 1
                confidence_sum[emotion] += entry["confidence"]
                language_distribution[entry["language"]] += 1

            # Calculate averages
            emotion_averages = {}
            for emotion, count in emotion_counts.items():
                emotion_averages[emotion] = {
                    "count": count,
                    "average_confidence": confidence_sum[emotion] / count,
                    "percentage": (count / len(recent_history)) * 100,
                }

            # Find dominant emotions
            dominant_emotions = sorted(
                emotion_averages.items(), key=lambda x: x[1]["percentage"], reverse=True
            )

            return {
                "analysis_period_days": days,
                "total_entries": len(recent_history),
                "emotion_distribution": dict(emotion_averages),
                "dominant_emotions": dominant_emotions[:3],
                "language_distribution": dict(language_distribution),
                "analysis_timestamp": datetime.now().isoformat(),
            }

        except Exception as e:
            self.logger.error(f"Failed to analyze emotion pattern: {e}")
            return {"error": f"Analysis failed: {e!s}"}

    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get performance metrics"""
        return {
            **self.performance_metrics,
            "cache_size": len(self.cache),
            "history_users": len(self.emotion_history),
            "uptime": "active",
        }

    async def shutdown(self) -> None:
        """Dọn dẹp resources"""
        try:
            self.logger.info("Shutting down EmotionSense...")

            # Clear caches
            self.cache.clear()
            self.emotion_history.clear()

            # Clear models if using PyTorch
            if TORCH_AVAILABLE and self.emotion_model:
                del self.emotion_model
                del self.tokenizer

            self.logger.info("EmotionSense shutdown completed")

        except Exception as e:
            self.logger.error(f"Shutdown failed: {e}")

    def health_check(self) -> Dict[str, Any]:
        """Health check for the module"""
        try:
            return {
                "status": "healthy",
                "module": "EmotionSenseV1",
                "version": "1.0.0",
                "models_loaded": self.emotion_model is not None,
                "torch_available": TORCH_AVAILABLE,
                "sklearn_available": SKLEARN_AVAILABLE,
                "performance_metrics": self.get_performance_metrics(),
                "timestamp": datetime.now().isoformat(),
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
            }


# Module metadata for framework integration
ModuleMeta = type(
    "ModuleMeta",
    (),
    {
        "version": "1.0.0",
        "description": "AI Cảm xúc thông minh - Nhận diện cảm xúc qua văn bản tiếng Việt",
        "author": "StillMe Framework Team",
        "requirements": [
            "torch>=1.9.0",
            "transformers>=4.20.0",
            "scikit-learn>=1.0.0",
            "numpy>=1.21.0",
        ],
        "dependencies": [],
        "api_prefix": "/emotion",
    },
)
