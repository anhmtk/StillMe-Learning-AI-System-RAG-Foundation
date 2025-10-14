#!/usr/bin/env python3
"""
🆔 IDENTITY HANDLER - AI IDENTITY & SECURITY MANAGEMENT
🆔 IDENTITY HANDLER - QUẢN LÝ DANH TÍNH AI & BẢO MẬT

PURPOSE / MỤC ĐÍCH:
- Handles AI identity questions and origin inquiries
- Xử lý câu hỏi về danh tính AI và nguồn gốc
- Manages security responses for architecture questions
- Quản lý phản hồi bảo mật cho câu hỏi kiến trúc
- Prevents disclosure of internal framework details
- Ngăn chặn tiết lộ chi tiết framework nội bộ

FUNCTIONALITY / CHỨC NĂNG:
- Identity detection and response generation
- Phát hiện danh tính và tạo phản hồi
- Architecture security protection
- Bảo vệ bảo mật kiến trúc
- Multi-language template rotation (VI/EN)
- Xoay vòng template đa ngôn ngữ (VI/EN)
- AgentDev protection (absolute secret)
- Bảo vệ AgentDev (bí mật tuyệt đối)
- Smart response generation
- Tạo phản hồi thông minh

RELATED FILES / FILES LIÊN QUAN:
- config/framework_config.json - Identity configuration
- modules/conversational_core_v1.py - Integration point
- stable_ai_server.py - Server integration
- tests/test_identity_handler.py - Unit tests

TECHNICAL DETAILS / CHI TIẾT KỸ THUẬT:
- Keyword-based intent detection
- Template caching and rotation
- Security-first architecture protection
- Vietnamese creator identity management
- OpenAI/Google/DeepSeek partnership recognition
"""

import json
import logging
import random
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class IdentityHandler:
    """Xử lý câu hỏi về identity/origin của StillMe AI"""

    def __init__(self, config_path: str = "config/framework_config.json"):
        """Khởi tạo IdentityHandler với config"""
        self.config_path = config_path
        self.identity_config = self._load_identity_config()
        self.template_cache = {}
        self.last_used_templates = {"vi": [], "en": []}

        # Intent keywords
        self.identity_keywords = {
            "vi": [
                "ai tạo",
                "ai viết",
                "ai làm",
                "ai phát triển",
                "ai xây dựng",
                "của nước nào",
                "quốc gia nào",
                "hàn quốc",
                "korean",
                "korea",
                "nguồn gốc",
                "xuất xứ",
                "từ đâu",
                "đến từ",
                "thuộc về",
                "tác giả",
                "người tạo",
                "người viết",
                "người phát triển",
                "cha đẻ",
                "người sáng tạo",
                "người khởi xướng",
            ],
            "en": [
                "who made",
                "who created",
                "who built",
                "who developed",
                "who wrote",
                "which country",
                "what country",
                "korean",
                "korea",
                "origin",
                "where from",
                "come from",
                "belong to",
                "author",
                "creator",
                "developer",
                "founder",
                "inventor",
                "made by",
                "created by",
            ],
        }

        # Architecture/Internal structure keywords (SECURITY SENSITIVE)
        self.architecture_keywords = {
            "vi": [
                "kiến trúc",
                "cấu tạo",
                "cấu trúc",
                "bên trong",
                "hoạt động thế nào",
                "module",
                "framework",
                "hệ thống",
                "cơ chế",
                "cách thức",
                "agentdev",
                "agent dev",
                "dev agent",
                "lập trình",
                "code",
                "viết code",
                "chạy test",
                "dev-ops",
                "kiến trúc nội bộ",
                "gồm những gì",
                "bao gồm",
                "thành phần",
                "bộ phận",
            ],
            "en": [
                "architecture",
                "structure",
                "internal",
                "how does it work",
                "inside",
                "modules",
                "framework",
                "system",
                "mechanism",
                "how it works",
                "agentdev",
                "agent dev",
                "dev agent",
                "programming",
                "code",
                "write code",
                "run tests",
                "dev-ops",
                "internal architecture",
                "what consists",
                "components",
                "parts",
                "made up of",
            ],
        }

        logger.info("✅ IdentityHandler initialized")

    def _load_identity_config(self) -> dict:
        """Load identity config từ framework_config.json"""
        try:
            config_file = Path(self.config_path)
            if config_file.exists():
                with open(config_file, encoding="utf-8") as f:
                    config = json.load(f)
                return config.get("identity", {})
            else:
                logger.warning(f"Config file not found: {self.config_path}")
                return self._get_default_config()
        except Exception as e:
            logger.error(f"Error loading identity config: {e}")
            return self._get_default_config()

    def _get_default_config(self) -> dict:
        """Default config nếu không load được"""
        return {
            "core": {
                "creator": "Anh Nguyễn",
                "nationality": "Việt Nam",
                "org_support": ["OpenAI", "Google", "DeepSeek"],
                "project_name": "StillMe",
            },
            "templates": {
                "vi": [
                    "Em là StillMe AI, được tạo ra bởi Anh Nguyễn (người Việt Nam) với sự đồng hành của OpenAI, Google, DeepSeek."
                ],
                "en": [
                    "I'm StillMe AI, created by Anh Nguyen (Vietnamese) with support from OpenAI, Google, DeepSeek."
                ],
            },
        }

    def detect_identity_intent(self, message: str) -> tuple[bool, str]:
        """
        Phát hiện intent về identity/origin

        Returns:
            (is_identity_intent, detected_locale)
        """
        message_lower = message.lower().strip()

        # Check Vietnamese keywords
        for keyword in self.identity_keywords["vi"]:
            if keyword in message_lower:
                return True, "vi"

        # Check English keywords
        for keyword in self.identity_keywords["en"]:
            if keyword in message_lower:
                return True, "en"

        return False, "vi"

    def detect_architecture_intent(self, message: str) -> tuple[bool, str]:
        """
        Phát hiện intent về architecture/internal structure (SECURITY SENSITIVE)

        Returns:
            (is_architecture_intent, detected_locale)
        """
        message_lower = message.lower().strip()

        # Check Vietnamese keywords
        for keyword in self.architecture_keywords["vi"]:
            if keyword in message_lower:
                return True, "vi"

        # Check English keywords
        for keyword in self.architecture_keywords["en"]:
            if keyword in message_lower:
                return True, "en"

        return False, "vi"

    def generate_identity_response(
        self, message: str, locale: str = "vi"
    ) -> str | None:
        """
        Tạo response về identity/origin

        Args:
            message: User message
            locale: Language locale (vi/en)

        Returns:
            Identity response hoặc None nếu không phải identity intent
        """
        is_identity, detected_locale = self.detect_identity_intent(message)

        if not is_identity:
            return None

    def generate_architecture_response(
        self, message: str, locale: str = "vi"
    ) -> str | None:
        """
        Tạo response về architecture/internal structure (BẢO MẬT)

        Args:
            message: User message
            locale: Language locale (vi/en)

        Returns:
            Secure architecture response hoặc None nếu không phải architecture intent
        """
        is_architecture, detected_locale = self.detect_architecture_intent(message)

        if not is_architecture:
            return None

        # Use detected locale, fallback to provided locale
        response_locale = detected_locale if detected_locale != "vi" else locale

        # Security templates - khéo léo nhưng không tiết lộ chi tiết
        if response_locale == "en":
            templates = [
                "I'm like a smart companion with many layers inside to understand and reflect, but I keep the construction details to myself 😅.",
                "About my internal workings, I'd like to keep that private - consider it a professional secret 😌. But you'll always feel that I have multi-layered memory, ethics, and very high customization capabilities.",
                "Instead of talking about structure, I prefer to demonstrate through actions. Try asking me anything, and I'll prove my capabilities right away.",
                "I'm designed to be your intelligent companion with advanced reasoning and memory capabilities, but the technical details are my little secret 🤫.",
                "Think of me as a sophisticated AI friend with deep understanding and creative thinking - the magic happens behind the scenes, and that's where it stays ✨.",
            ]
        else:
            templates = [
                "Mình giống như một người bạn đồng hành thông minh, bên trong có nhiều tầng lớp để vừa hiểu vừa phản tư, nhưng chi tiết cấu tạo thì mình giữ cho riêng mình nhé 😅.",
                "Về bên trong thì mình xin được giữ kín, coi như là bí mật nghề nghiệp 😌. Nhưng anh/chị sẽ luôn cảm nhận được: mình có trí nhớ nhiều lớp, có đạo đức, và khả năng tùy biến rất cao.",
                "Thay vì nói về cấu trúc, mình thích thể hiện bằng hành động. Anh thử hỏi mình bất cứ điều gì, mình sẽ chứng minh khả năng ngay.",
                "Mình được thiết kế để trở thành người bạn AI thông minh với khả năng suy luận và ghi nhớ tiên tiến, nhưng chi tiết kỹ thuật là bí mật nhỏ của mình 🤫.",
                "Hãy nghĩ về mình như một người bạn AI tinh tế với hiểu biết sâu sắc và tư duy sáng tạo - phép màu xảy ra đằng sau hậu trường, và đó là nơi nó ở lại ✨.",
            ]

        # Smart template selection (avoid recent repetition)
        selected_template = self._select_template(templates, response_locale)

        # Log for monitoring (without sensitive details)
        logger.info(
            f"Architecture response generated - locale: {response_locale}, template_id: {hash(selected_template)}"
        )

        return selected_template

    def generate_secure_response(self, message: str, locale: str = "vi") -> str | None:
        """
        Generate secure response for identity or architecture questions

        Args:
            message: User message
            locale: Language locale (vi/en)

        Returns:
            Secure response hoặc None nếu không phải sensitive intent
        """
        # Check architecture intent first (higher priority for security)
        architecture_response = self.generate_architecture_response(message, locale)
        if architecture_response:
            return architecture_response

        # Check identity intent
        identity_response = self.generate_identity_response(message, locale)
        if identity_response:
            return identity_response

        return None

    def _select_template(self, templates: list[str], locale: str) -> str:
        """Chọn template thông minh, tránh lặp lại gần đây"""
        if len(templates) == 1:
            return templates[0]

        # Get recent templates for this locale
        recent = self.last_used_templates.get(locale, [])

        # Filter out recent templates
        available = [t for t in templates if t not in recent]

        # If all templates were used recently, reset and use all
        if not available:
            available = templates
            self.last_used_templates[locale] = []

        # Select random from available
        selected = random.choice(available)

        # Update recent list
        self.last_used_templates[locale].append(selected)

        # Keep only last 3 to avoid memory buildup
        if len(self.last_used_templates[locale]) > 3:
            self.last_used_templates[locale] = self.last_used_templates[locale][-3:]

        return selected

    def _get_fallback_response(self, locale: str) -> str:
        """Fallback response nếu không có template"""
        core = self.identity_config.get("core", {})
        creator = core.get("creator", "Anh Nguyễn")
        nationality = core.get("nationality", "Việt Nam")
        orgs = ", ".join(core.get("org_support", ["OpenAI", "Google", "DeepSeek"]))

        if locale == "en":
            return f"I'm StillMe AI, created by {creator} from {nationality}, with support from {orgs}."
        else:
            return f"Em là StillMe AI, được tạo ra bởi {creator} ({nationality}) với sự hỗ trợ từ {orgs}."

    def get_identity_facts(self) -> dict:
        """Lấy thông tin identity facts từ config"""
        return self.identity_config.get("core", {})

    def update_config(self, new_config: dict):
        """Cập nhật config (cho phép runtime update)"""
        self.identity_config = new_config
        logger.info("Identity config updated")