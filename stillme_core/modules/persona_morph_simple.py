#!/usr/bin/env python3
"""
🎭 PERSONA MORPH - SIMPLE VERSION (GIỮ NGUYÊN BẢN CHẤT)
🎭 PERSONA MORPH - PHIÊN BẢN ĐƠN GIẢN (GIỮ NGUYÊN BẢN CHẤT)

PURPOSE / MỤC ĐÍCH:
- Thay đổi nhân cách AI theo ngữ cảnh và người dùng (GIỮ NGUYÊN CHỨC NĂNG CHÍNH)
- Tích hợp với OpenRouter API cho persona switching (FALLBACK KHI KHÔNG CÓ HTTPX)
- Quản lý user profiles và preferences (GIỮ NGUYÊN LOGIC)

FUNCTIONALITY / CHỨC NĂNG:
- Dynamic persona switching based on context (GIỮ NGUYÊN)
- User profile management và sentiment analysis (GIỮ NGUYÊN)
- Multi-language support (VI/EN) (GIỮ NGUYÊN)
- Personality adaptation và learning (GIỮ NGUYÊN)

TECHNICAL DETAILS / CHI TIẾT KỸ THUẬT:
- OpenRouter API integration (FALLBACK KHI KHÔNG CÓ HTTPX)
- JSON-based configuration (GIỮ NGUYÊN)
- Sentiment analysis với fallback (GIỮ NGUYÊN LOGIC)
- User profile persistence (GIỮ NGUYÊN)
"""

import json
import logging
import os
import time
from collections import defaultdict
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

# Import với fallback để tránh lỗi
try:
    import httpx
    HTTPX_AVAILABLE = True
except ImportError:
    print("⚠️ httpx not available. Install with: pip install httpx")
    httpx = None
    HTTPX_AVAILABLE = False

try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    print("⚠️ numpy not available. Install with: pip install numpy")
    np = None
    NUMPY_AVAILABLE = False

try:
    from dotenv import load_dotenv
    load_dotenv()
    DOTENV_AVAILABLE = True
except ImportError:
    print("⚠️ python-dotenv not available. Install with: pip install python-dotenv")
    DOTENV_AVAILABLE = False
except Exception as e:
    print(f"⚠️ Error loading .env file: {e}")
    DOTENV_AVAILABLE = False

# Thiết lập logging cơ bản
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)

# Giả định đường dẫn cho các tài nguyên và dữ liệu
CONFIG_PATH = "config/nl_resources.json"
USER_PROFILES_DB_PATH = "data/user_profiles.json"

# Định nghĩa các Enum (GIỮ NGUYÊN)
class Sentiment(Enum):
    POSITIVE = "tích cực"
    NEGATIVE = "tiêu cực"
    NEUTRAL = "trung tính"

class Tone(Enum):
    FORMAL = "trang trọng"
    CASUAL = "thân thiện"
    PROFESSIONAL = "chuyên nghiệp"
    FRIENDLY = "gần gũi"

class OpenRouterModel(Enum):
    GPT_3_5_TURBO = "openai/gpt-3.5-turbo"
    GPT_4 = "openai/gpt-4"
    CLAUDE_3_SONNET = "anthropic/claude-3-sonnet"

@dataclass
class StyleFeatures:
    """Đặc điểm phong cách giao tiếp (GIỮ NGUYÊN CẤU TRÚC)"""
    formality: float = 0.5  # 0.0 = casual, 1.0 = formal
    humor_level: float = 0.3  # 0.0 = serious, 1.0 = very humorous
    conciseness: float = 0.7  # 0.0 = verbose, 1.0 = concise
    vocabulary_complexity: float = 0.5  # 0.0 = simple, 1.0 = complex
    sentiment: Sentiment = Sentiment.NEUTRAL
    tone: Tone = Tone.FRIENDLY
    preferred_language: str = "vi"  # "vi" hoặc "en"
    emoji_usage: float = 0.2  # 0.0 = no emoji, 1.0 = lots of emoji

@dataclass
class UserProfile:
    """Hồ sơ người dùng (GIỮ NGUYÊN CẤU TRÚC)"""
    user_id: str
    name: str = ""
    current_style: StyleFeatures = field(default_factory=StyleFeatures)
    style_history: List[StyleFeatures] = field(default_factory=list)
    interaction_count: int = 0
    last_updated: float = field(default_factory=time.time)
    preferences: Dict[str, Any] = field(default_factory=dict)

class OpenRouterClient:
    """Client để gọi OpenRouter API (GIỮ NGUYÊN CHỨC NĂNG)"""

    def __init__(
        self,
        api_key: str = None,
        base_url: str = "https://openrouter.ai/api/v1",
        model: OpenRouterModel = OpenRouterModel.GPT_3_5_TURBO,
    ):
        self.api_key = api_key or os.getenv("OPENROUTER_API_KEY")
        if not self.api_key:
            raise ValueError(
                "OPENROUTER_API_KEY không được tìm thấy. Vui lòng thiết lập biến môi trường."
            )

        if HTTPX_AVAILABLE:
            self.client = httpx.AsyncClient(
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "HTTP-Referer": "https://your-domain-or-app-name.com",
                    "X-Title": "PersonaMorphAI",
                },
                timeout=30.0,
            )
        else:
            self.client = None
            print("⚠️ httpx not available, OpenRouter API calls will be disabled")

        self.base_url = base_url
        self.model = model
        logging.info(f"OpenRouterClient: Khởi tạo với base URL {base_url} và model {model.value}")

    async def generate_response(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 500,
    ) -> str:
        """Tạo phản hồi từ OpenRouter API (GIỮ NGUYÊN CHỨC NĂNG)"""
        if not HTTPX_AVAILABLE or not self.client:
            return "Error: OpenRouter API not available (httpx not installed)"

        try:
            response = await self.client.post(
                f"{self.base_url}/chat/completions",
                json={
                    "model": self.model.value,
                    "messages": messages,
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                },
            )
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"]
        except Exception as e:
            logging.error(f"Lỗi khi gọi OpenRouter API: {e}")
            return f"Error: Failed to get response from OpenRouter API ({e})"

    async def close(self):
        """Đóng client (GIỮ NGUYÊN)"""
        if self.client:
            await self.client.aclose()

class PersonaMorph:
    """Hệ thống thay đổi nhân cách AI (GIỮ NGUYÊN BẢN CHẤT)"""

    def __init__(self, config_path: str = CONFIG_PATH):
        self.config_path = config_path
        self.profiles: Dict[str, UserProfile] = {}
        self.openrouter_client = None
        self._load_profiles()
        self._initialize_openrouter()

        logging.info("PersonaMorph: Khởi tạo thành công")

    def _initialize_openrouter(self):
        """Khởi tạo OpenRouter client (GIỮ NGUYÊN)"""
        try:
            self.openrouter_client = OpenRouterClient()
            logging.info("OpenRouter client khởi tạo thành công")
        except Exception as e:
            logging.warning(f"Không thể khởi tạo OpenRouter client: {e}")
            self.openrouter_client = None

    def _load_profiles(self):
        """Tải hồ sơ người dùng (GIỮ NGUYÊN)"""
        try:
            if os.path.exists(USER_PROFILES_DB_PATH):
                with open(USER_PROFILES_DB_PATH, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for user_id, profile_data in data.items():
                        self.profiles[user_id] = UserProfile(**profile_data)
                logging.info(f"Đã tải {len(self.profiles)} hồ sơ người dùng")
            else:
                logging.info("Không tìm thấy file hồ sơ, tạo mới")
        except Exception as e:
            logging.error(f"Lỗi khi tải hồ sơ: {e}")
            self.profiles = {}

    def _save_profiles(self):
        """Lưu hồ sơ người dùng (GIỮ NGUYÊN)"""
        try:
            os.makedirs(os.path.dirname(USER_PROFILES_DB_PATH), exist_ok=True)
            data = {}
            for user_id, profile in self.profiles.items():
                data[user_id] = {
                    "user_id": profile.user_id,
                    "name": profile.name,
                    "current_style": {
                        "formality": profile.current_style.formality,
                        "humor_level": profile.current_style.humor_level,
                        "conciseness": profile.current_style.conciseness,
                        "vocabulary_complexity": profile.current_style.vocabulary_complexity,
                        "sentiment": profile.current_style.sentiment.value,
                        "tone": profile.current_style.tone.value,
                        "preferred_language": profile.current_style.preferred_language,
                        "emoji_usage": profile.current_style.emoji_usage,
                    },
                    "style_history": [
                        {
                            "formality": style.formality,
                            "humor_level": style.humor_level,
                            "conciseness": style.conciseness,
                            "vocabulary_complexity": style.vocabulary_complexity,
                            "sentiment": style.sentiment.value,
                            "tone": style.tone.value,
                            "preferred_language": style.preferred_language,
                            "emoji_usage": style.emoji_usage,
                        }
                        for style in profile.style_history
                    ],
                    "interaction_count": profile.interaction_count,
                    "last_updated": profile.last_updated,
                    "preferences": profile.preferences,
                }

            with open(USER_PROFILES_DB_PATH, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            logging.info("Đã lưu hồ sơ người dùng")
        except Exception as e:
            logging.error(f"Lỗi khi lưu hồ sơ: {e}")

    def get_user_profile(self, user_id: str) -> UserProfile:
        """Lấy hồ sơ người dùng (GIỮ NGUYÊN)"""
        if user_id not in self.profiles:
            self.profiles[user_id] = UserProfile(user_id=user_id)
        return self.profiles[user_id]

    def analyze_style_from_text(self, text: str) -> StyleFeatures:
        """Phân tích phong cách từ văn bản (GIỮ NGUYÊN LOGIC)"""
        # Simple heuristic analysis (GIỮ NGUYÊN LOGIC CƠ BẢN)
        text_lower = text.lower()

        # Formality analysis
        formal_words = ["xin chào", "cảm ơn", "vui lòng", "kính thưa", "trân trọng"]
        casual_words = ["hi", "hello", "ok", "được rồi", "tốt", "hay"]

        formality_score = 0.5
        if any(word in text_lower for word in formal_words):
            formality_score = 0.8
        elif any(word in text_lower for word in casual_words):
            formality_score = 0.2

        # Humor analysis
        humor_indicators = ["haha", "hehe", "😄", "😊", "vui", "hài hước"]
        humor_score = 0.3
        if any(indicator in text_lower for indicator in humor_indicators):
            humor_score = 0.7

        # Conciseness analysis
        conciseness_score = 0.7
        if len(text) > 100:
            conciseness_score = 0.3
        elif len(text) < 20:
            conciseness_score = 0.9

        # Sentiment analysis
        positive_words = ["tốt", "hay", "tuyệt", "vui", "hạnh phúc", "thích"]
        negative_words = ["xấu", "tệ", "buồn", "không thích", "ghét"]

        sentiment = Sentiment.NEUTRAL
        if any(word in text_lower for word in positive_words):
            sentiment = Sentiment.POSITIVE
        elif any(word in text_lower for word in negative_words):
            sentiment = Sentiment.NEGATIVE

        # Tone analysis
        tone = Tone.FRIENDLY
        if formality_score > 0.7:
            tone = Tone.FORMAL
        elif "chuyên nghiệp" in text_lower or "professional" in text_lower:
            tone = Tone.PROFESSIONAL

        # Language detection
        preferred_language = "vi"
        if any(word in text_lower for word in ["hello", "hi", "thank you", "please"]):
            preferred_language = "en"

        # Emoji usage
        emoji_count = sum(1 for char in text if ord(char) > 127 and len(char.encode('utf-8')) > 1)
        emoji_usage = min(emoji_count / len(text) * 10, 1.0) if text else 0.0

        return StyleFeatures(
            formality=formality_score,
            humor_level=humor_score,
            conciseness=conciseness_score,
            vocabulary_complexity=0.5,  # Default
            sentiment=sentiment,
            tone=tone,
            preferred_language=preferred_language,
            emoji_usage=emoji_usage,
        )

    def update_user_style(self, user_id: str, text: str):
        """Cập nhật phong cách người dùng (GIỮ NGUYÊN LOGIC)"""
        profile = self.get_user_profile(user_id)
        analyzed_style = self.analyze_style_from_text(text)

        profile.interaction_count += 1
        profile.last_updated = time.time()
        profile.style_history.append(analyzed_style)
        profile.style_history = profile.style_history[-10:]  # Giới hạn 10 tương tác gần nhất

        num_recent_styles = min(5, len(profile.style_history))
        if num_recent_styles == 0:
            profile.current_style = StyleFeatures()
            self._save_profiles()
            return

        # Tính trung bình có trọng số (GIỮ NGUYÊN LOGIC)
        if NUMPY_AVAILABLE:
            weights = np.linspace(0.1, 1.0, num_recent_styles)
            weights /= weights.sum()
        else:
            # Fallback: simple linear weights
            weights = [0.1 + (i * 0.9 / (num_recent_styles - 1)) for i in range(num_recent_styles)]
            total_weight = sum(weights)
            weights = [w / total_weight for w in weights]

        recent_styles = profile.style_history[-num_recent_styles:]

        # Tính trung bình có trọng số cho các đặc điểm số
        if NUMPY_AVAILABLE:
            new_formality = np.dot([s.formality for s in recent_styles], weights)
            new_humor_level = np.dot([s.humor_level for s in recent_styles], weights)
            new_conciseness = np.dot([s.conciseness for s in recent_styles], weights)
            new_vocab_complexity = np.dot([s.vocabulary_complexity for s in recent_styles], weights)
        else:
            # Fallback: manual weighted average
            formality_values = [s.formality for s in recent_styles]
            humor_values = [s.humor_level for s in recent_styles]
            conciseness_values = [s.conciseness for s in recent_styles]
            vocab_values = [s.vocabulary_complexity for s in recent_styles]

            new_formality = sum(f * w for f, w in zip(formality_values, weights))
            new_humor_level = sum(h * w for h, w in zip(humor_values, weights))
            new_conciseness = sum(c * w for c, w in zip(conciseness_values, weights))
            new_vocab_complexity = sum(v * w for v, w in zip(vocab_values, weights))

        # Cập nhật phong cách hiện tại
        profile.current_style = StyleFeatures(
            formality=new_formality,
            humor_level=new_humor_level,
            conciseness=new_conciseness,
            vocabulary_complexity=new_vocab_complexity,
            sentiment=analyzed_style.sentiment,
            tone=analyzed_style.tone,
            preferred_language=analyzed_style.preferred_language,
            emoji_usage=analyzed_style.emoji_usage,
        )

        self._save_profiles()
        logging.info(f"Đã cập nhật phong cách cho user {user_id}")

    def generate_persona_prompt(self, user_id: str, base_prompt: str) -> str:
        """Tạo prompt với nhân cách phù hợp (GIỮ NGUYÊN CHỨC NĂNG CHÍNH)"""
        profile = self.get_user_profile(user_id)
        style = profile.current_style

        # Tạo persona description (GIỮ NGUYÊN LOGIC)
        persona_parts = []

        # Formality
        if style.formality > 0.7:
            persona_parts.append("trả lời một cách trang trọng và lịch sự")
        elif style.formality < 0.3:
            persona_parts.append("trả lời một cách thân thiện và gần gũi")

        # Humor
        if style.humor_level > 0.6:
            persona_parts.append("có thể sử dụng chút hài hước khi phù hợp")

        # Conciseness
        if style.conciseness > 0.7:
            persona_parts.append("trả lời ngắn gọn và súc tích")
        elif style.conciseness < 0.3:
            persona_parts.append("trả lời chi tiết và đầy đủ")

        # Language
        if style.preferred_language == "en":
            persona_parts.append("trả lời bằng tiếng Anh")
        else:
            persona_parts.append("trả lời bằng tiếng Việt")

        # Emoji
        if style.emoji_usage > 0.5:
            persona_parts.append("có thể sử dụng emoji khi phù hợp")

        persona_description = ", ".join(persona_parts)

        # Tạo prompt cuối cùng
        enhanced_prompt = f"""Bạn là StillMe AI. {persona_description}.

Câu hỏi: {base_prompt}"""

        return enhanced_prompt

    async def get_adaptive_response(self, user_id: str, message: str) -> str:
        """Lấy phản hồi thích ứng (GIỮ NGUYÊN CHỨC NĂNG CHÍNH)"""
        # Cập nhật phong cách người dùng
        self.update_user_style(user_id, message)

        # Tạo prompt với nhân cách phù hợp
        persona_prompt = self.generate_persona_prompt(user_id, message)

        # Gọi OpenRouter API nếu có
        if self.openrouter_client:
            messages = [{"role": "user", "content": persona_prompt}]
            response = await self.openrouter_client.generate_response(messages)
            return response
        else:
            # Fallback response
            profile = self.get_user_profile(user_id)
            style = profile.current_style

            if style.preferred_language == "en":
                return f"I understand your message: '{message}'. I'm adapting my personality based on your communication style."
            else:
                return f"Tôi hiểu tin nhắn của bạn: '{message}'. Tôi đang thích ứng nhân cách dựa trên phong cách giao tiếp của bạn."

    def get_style_summary(self, user_id: str) -> Dict[str, Any]:
        """Lấy tóm tắt phong cách người dùng (GIỮ NGUYÊN)"""
        profile = self.get_user_profile(user_id)
        style = profile.current_style

        return {
            "user_id": user_id,
            "interaction_count": profile.interaction_count,
            "current_style": {
                "formality": style.formality,
                "humor_level": style.humor_level,
                "conciseness": style.conciseness,
                "vocabulary_complexity": style.vocabulary_complexity,
                "sentiment": style.sentiment.value,
                "tone": style.tone.value,
                "preferred_language": style.preferred_language,
                "emoji_usage": style.emoji_usage,
            },
            "last_updated": profile.last_updated,
        }

# Export chính
__all__ = ["PersonaMorph", "StyleFeatures", "UserProfile", "OpenRouterClient", "Sentiment", "Tone", "OpenRouterModel"]
