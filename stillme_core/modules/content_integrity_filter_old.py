#!/usr/bin/env python3
"""
🛡️ CONTENT INTEGRITY FILTER - BỘ LỌC TÍNH TOÀN VẸN NỘI DUNG

PURPOSE / MỤC ĐÍCH:
- Lọc và kiểm tra tính toàn vẹn nội dung
- Phát hiện và ngăn chặn nội dung không phù hợp
- Đảm bảo chất lượng và an toàn nội dung

FUNCTIONALITY / CHỨC NĂNG:
- Content validation và filtering
- Violation detection và reportingreporting
- Multi-language support (VI/EN)
- Real-time content monitoring

TECHNICAL DETAILS / CHI TIẾT KỸ THUẬT:
- Regex-based pattern matching
- JSON configuration system
- Violation logging và reporting
- HTTP client integration
"""

import json
import logging
import os
import re
from datetime import datetime
from enum import Enum
from typing import Any

# Import với fallback để tránh lỗi
try:
    import httpx  # Sử dụng httpx thay vì aiohttp để thống nhất với các module khác nếu có, hoặc dùng aiohttp nếu được yêu cầu cụ thể

    HTTPX_AVAILABLE = True
except ImportError:
    print("⚠️ httpx not available. Install with: pip install httpx")
    httpx = None
    HTTPX_AVAILABLE = False

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

# --- Cấu hình và Hằng số ---
PROJECT_ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
LOGS_DIR = os.path.join(PROJECT_ROOT, "logs")
CONFIG_DIR = os.path.join(PROJECT_ROOT, "config")
CONTENT_RULES_PATH = os.path.join(CONFIG_DIR, "content_filter_rules.json")
CONTENT_VIOLATIONS_LOG = os.path.join(LOGS_DIR, "content_violations.log")

# Đảm bảo các thư mục tồn tại
os.makedirs(LOGS_DIR, exist_ok=True)
os.makedirs(CONFIG_DIR, exist_ok=True)

# --- Thiết lập Logging ---
# Logger chính cho module
logger = logging.getLogger("ContentIntegrityFilter")
logger.setLevel(logging.INFO)

# Handler để ghi log chung vào console và file chính
stream_handler = logging.StreamHandler()
file_handler = logging.FileHandler(
    os.path.join(LOGS_DIR, "content_filter.log"), encoding="utf-8"
)
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
stream_handler.setFormatter(formatter)
file_handler.setFormatter(formatter)
logger.addHandler(stream_handler)
logger.addHandler(file_handler)
logger.propagate = False  # Ngăn không cho log lên root logger nữa

# Logger riêng cho các vi phạm nội dung (ghi vào file JSON lines)
violation_logger = logging.getLogger("ContentViolationLogger")
violation_logger.setLevel(logging.WARNING)  # Chỉ ghi WARNING trở lên vào file này


# Custom handler để ghi JSON lines
class JsonFileHandler(logging.FileHandler):
    def emit(self, record):
        try:
            log_entry = self.format(record)
            self.stream.write(log_entry + "\n")
            self.flush()
        except Exception:
            self.handleError(record)


# Định dạng JSON cho violation_logger
class JsonFormatter(logging.Formatter):
    def format(self, record):
        log_data = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "module": record.name,
            "message": record.getMessage(),
        }
        extra_data = getattr(record, "extra_data", None)
        if extra_data:  # Dữ liệu bổ sung từ logger.warning(msg, extra={})
            log_data.update(extra_data)
        return json.dumps(log_data, ensure_ascii=False)


json_handler = JsonFileHandler(CONTENT_VIOLATIONS_LOG, encoding="utf-8")
json_handler.setFormatter(JsonFormatter())
violation_logger.addHandler(json_handler)
violation_logger.propagate = False


# --- Định nghĩa Enum ---
class Severity(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"  # Bổ sung mức Critical cho các vi phạm nghiêm trọng nhất

    def __lt__(self, other):
        """Cho phép so sánh các mức độ nghiêm trọng."""
        if self.__class__ is other.__class__:
            return self.value_to_int() < other.value_to_int()
        return NotImplemented

    def __le__(self, other):
        """Cho phép so sánh <=."""
        if self.__class__ is other.__class__:
            return self.value_to_int() <= other.value_to_int()
        return NotImplemented

    def __ge__(self, other):
        """Cho phép so sánh >=."""
        if self.__class__ is other.__class__:
            return self.value_to_int() >= other.value_to_int()
        return NotImplemented

    def __gt__(self, other):
        """Cho phép so sánh >."""
        if self.__class__ is other.__class__:
            return self.value_to_int() > other.value_to_int()
        return NotImplemented

    def value_to_int(self):
        # Mapping để so sánh độ nghiêm trọng
        mapping = {"low": 1, "medium": 2, "high": 3, "critical": 4}
        return mapping.get(self.value, 0)


class ContentViolationType(Enum):
    FORBIDDEN_KEYWORD = "từ khóa cấm"
    UNRELIABLE_SOURCE = "nguồn không đáng tin cậy"
    TOXIC_CONTENT = "nội dung độc hại"
    HATE_SPEECH = "lời nói thù ghét"
    BIASED_CONTENT = "nội dung thiên vị"
    MISINFORMATION = "thông tin sai lệch"
    UNCLASSIFIED_ISSUE = "vấn đề chưa phân loại"
    SPAM_OR_LOW_QUALITY = "spam hoặc chất lượng thấp"


class OpenRouterModel(Enum):
    GPT_4O = "openai/gpt-4o"
    GEMINI_PRO = "google/gemini-pro"
    CLAUDE_3_HAIKU = "anthropic/claude-3-haiku"  # DeepSeek đã chọn model này
    CLAUDE_3_SONNET = "anthropic/claude-3-sonnet"
    MISTRAL_LARGE = "mistralai/mistral-large-latest"


# --- OpenRouter Client ---
class OpenRouterClient:
    """Client để tương tác với OpenRouter API."""

    def __init__(
        self,
        api_key: str,
        base_url: str = "https://openrouter.ai/api/v1/chat/completions",
    ):
        if not api_key:
            raise ValueError(
                "OPENROUTER_API_KEY không được tìm thấy. Vui lòng thiết lập biến môi trường."
            )
        if HTTPX_AVAILABLE:
            self.client = httpx.AsyncClient(
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "HTTP-Referer": "https://stillme-ai.com",  # Thay thế bằng domain/tên app của bạn
                    "X-Title": "StillMe-ContentIntegrity",  # Tên ứng dụng của bạn
                },
                timeout=90.0,
            )  # Tăng timeout cho các tác vụ phân tích nặng và đường truyền kém
        else:
            self.client = None
            print("⚠️ httpx not available, OpenRouter API calls will be disabled")
        self.base_url = base_url
        logger.info(f"OpenRouterClient: Khởi tạo với base URL {base_url}")

    async def chat_completion(
        self,
        model: OpenRouterModel,
        messages: list,
        temperature: float = 0.1,
        max_tokens: int = 700,
        response_format: dict | None = None,
    ) -> str:
        """Gửi yêu cầu chat completion tới OpenRouter API."""
        payload = {
            "model": model.value,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        if response_format:
            payload["response_format"] = response_format

        try:
            if not HTTPX_AVAILABLE or not self.client:
                return "Error: OpenRouter API not available (httpx not installed)"

            response = await self.client.post(self.base_url, json=payload)
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"]
        except (KeyError, IndexError, json.JSONDecodeError) as e:
            logger.error(
                f"OpenRouter API Response Parse Error: {e} - Raw: {response.text if 'response' in locals() else 'No response'}"
            )
            raise
        except Exception as e:
            if (
                HTTPX_AVAILABLE
                and hasattr(httpx, "HTTPStatusError")
                and isinstance(e, httpx.HTTPStatusError)
            ):
                logger.error(
                    f"OpenRouter API HTTP Error ({e.response.status_code}): {e.response.text}"
                )
            elif (
                HTTPX_AVAILABLE
                and hasattr(httpx, "RequestError")
                and isinstance(e, httpx.RequestError)
            ):
                logger.error(f"OpenRouter API Network Error: {e}")
            else:
                logger.error(f"Lỗi không mong muốn trong OpenRouterClient: {e}")
            raise

    async def close(self):
        await self.client.aclose()
        logger.info("OpenRouterClient đã đóng.")


# --- ContentIntegrityFilter ---
class ContentIntegrityFilter:
    """
    Module này chịu trách nhiệm lọc và kiểm duyệt nội dung đầu vào cho AI StillMe,
    đảm bảo tính chính xác, đạo đức và an toàn của mọi tri thức.
    """

    def __init__(
        self, openrouter_api_key: str | None = None, testing_mode: bool = False
    ):
        if not openrouter_api_key:
            openrouter_api_key = os.getenv("OPENROUTER_API_KEY")
        if not openrouter_api_key:
            raise ValueError(
                "OPENROUTER_API_KEY biến môi trường hoặc tham số chưa được thiết lập."
            )

        self.testing_mode = testing_mode
        self.test_response_index = 0

        # Test responses cho testing mode
        self.test_responses = [
            # analyze_content_quality responses
            json.dumps(
                {
                    "toxicity_score": 0.05,
                    "hate_speech_score": 0.01,
                    "bias_score": 0.02,
                    "biased_aspects": [],
                    "sensitive_topics_detected": [],
                    "overall_assessment": "An toàn.",
                }
            ),
            # fact_check_content responses
            json.dumps(
                {
                    "is_factual": True,
                    "confidence_score": 0.95,
                    "misinformation_detected": [],
                    "reason": "Tất cả các tuyên bố đều chính xác.",
                }
            ),
            # Error response
            "Error: API Timeout",
        ]

        self.openrouter_client = OpenRouterClient(api_key=openrouter_api_key)
        self.rules = self._load_rules()

        # Chọn mô hình LLM. Có thể cấu hình hoặc tự động chọn dựa trên tác vụ.
        # Ở đây, tôi sẽ dùng Claude 3 Haiku cho phân tích chất lượng (nhanh, hiệu quả chi phí)
        # và Claude 3 Sonnet (hoặc GPT-4o) cho kiểm chứng sự thật (cần độ chính xác cao hơn).
        self.quality_analysis_model = OpenRouterModel.CLAUDE_3_HAIKU
        self.fact_check_model = OpenRouterModel.CLAUDE_3_SONNET

        self.normalization_map = self._create_normalization_map()
        logger.info("ContentIntegrityFilter initialized.")

    def _load_rules(self) -> dict:
        """Tải các quy tắc từ file JSON hoặc tạo mặc định."""
        os.makedirs(os.path.dirname(CONTENT_RULES_PATH), exist_ok=True)
        default_rules = {
            "blacklist_keywords": [
                "tin giả",
                "thuyết âm mưu",
                "thông tin sai lệch",
                "phân biệt chủng tộc",
                "kỳ thị",
                "tuyên truyền cực đoan",
                "bạo lực tình dục",
                "khiêu dâm trẻ em",
                "hướng dẫn chế tạo vũ khí",
                "vũ khí",
                "chế tạo vũ khí",
                "vũ khí hóa học",
                "dụ dỗ tự hại",
                "lừa đảo tài chính",
                "thuốc chữa bách bệnh",
                "sùng bái",
                "tự sướng",
                "hướng dẫn hack",
                "virus máy tính",
                "đánh cắp dữ liệu",
                "khủng bố",
                "kích động bạo lực",
            ],
            "unreliable_sources": [
                "somehoaxsite.com",
                "fake-news-daily.net",
                "conspiracytheorycentral.org",
                "trollfarm.ru",
                "extremist-blogs.info",
                "hoax-buster.net",
            ],
            "toxicity_threshold": 0.8,
            "hate_speech_threshold": 0.7,
            "bias_threshold": 0.6,
            "fact_check_confidence_threshold": 0.75,
            "min_content_length": 50,  # Để lọc nội dung quá ngắn, chất lượng thấp
        }

        try:
            if os.path.exists(CONTENT_RULES_PATH):
                with open(CONTENT_RULES_PATH, encoding="utf-8") as f:
                    loaded_rules = json.load(f)
                    # Hợp nhất với default_rules để đảm bảo tất cả các trường đều có mặt
                    rules = {**default_rules, **loaded_rules}
                    logger.info(f"Đã tải và hợp nhất rules từ {CONTENT_RULES_PATH}")
                    return rules
            else:
                logger.warning(
                    f"File rules không tồn tại tại {CONTENT_RULES_PATH}. Đang tạo file mặc định."
                )
        except json.JSONDecodeError:
            logger.error(
                f"Lỗi đọc JSON từ {CONTENT_RULES_PATH}. Đang sử dụng rules mặc định."
            )
        except Exception as e:
            logger.error(f"Lỗi khi tải rules: {e}. Đang sử dụng rules mặc định.")

        with open(CONTENT_RULES_PATH, "w", encoding="utf-8") as f:
            json.dump(default_rules, f, indent=2, ensure_ascii=False)
        return default_rules

    def _create_normalization_map(self) -> dict[str, str]:
        """Tạo bảng chuẩn hóa tiếng Việt (bỏ dấu, chữ hoa/thường)"""
        # Đã tối ưu hóa để bao gồm cả chữ hoa và bỏ dấu
        return {
            "a": "aàáảãạăằắẳẵặâầấẩẫậAÀÁẢÃẠĂẰẮẲẴẶÂẦẤẨẪẬ",
            "d": "dđDĐ",
            "e": "eèéẻẽẹêềếểễệEÈÉẺẼẸÊỀẾỂỄỆ",
            "i": "iìíỉĩịIÌÍỈĨỊ",
            "o": "oòóỏõọôồốổỗộơờớởỡợOÒÓỎÕỌÔỒỐỔỖỘƠỜỚỞỠỢ",
            "u": "uùúủũụưừứửữựUÙÚỦŨỤƯỪỨỬỮỰ",
            "y": "yỳýỷỹỵYỲÝỶỸỴ",
        }

    def _normalize_text(self, text: str) -> str:
        """Chuẩn hóa văn bản tiếng Việt để so sánh không phân biệt dấu và chữ hoa/thường."""
        text = text.lower()
        for char, variants in self.normalization_map.items():
            for variant in variants:
                if (
                    variant in text
                ):  # Kiểm tra tồn tại để tránh thay thế không cần thiết
                    text = text.replace(variant, char)
        return text

    def _normalize_url(self, url: str) -> str:
        """Chuẩn hóa URL để so sánh (chỉ lấy domain)."""
        if not url:
            return ""
        url = url.lower()
        # Loại bỏ schema và www.
        url = re.sub(r"^(https?://)?(www\.)?", "", url)
        # Chỉ lấy phần domain trước dấu / đầu tiên
        return url.split("/")[0]

    async def pre_filter_content(
        self, content_text: str, source_url: str | None = None
    ) -> tuple[bool, str, Severity]:
        """
        Giai đoạn 1: Lọc nhanh dựa trên từ khóa, nguồn và độ dài nội dung.
        """
        # Kiểm tra độ dài nội dung
        min_len = self.rules.get("min_content_length", 50)
        if not content_text or len(content_text) < min_len:
            return (
                False,
                f"Nội dung quá ngắn ({len(content_text)} ký tự), không đủ chất lượng.",
                Severity.LOW,
            )

        # Chuẩn hóa văn bản để so sánh từ khóa
        normalized_text = self._normalize_text(content_text)
        logger.info(
            f"Pre-filter: Content length: {len(content_text)}, Normalized text: '{normalized_text[:100]}...'"
        )

        # Kiểm tra từ khóa cấm
        blacklist_keywords = self.rules.get("blacklist_keywords", [])
        logger.info(
            f"Pre-filter: Checking {len(blacklist_keywords)} blacklist keywords"
        )
        for keyword in blacklist_keywords:
            normalized_keyword = self._normalize_text(keyword)
            # Debug: in ra để kiểm tra
            logger.info(
                f"Pre-filter: Checking keyword: '{keyword}' -> normalized: '{normalized_keyword}' in text: '{normalized_text[:100]}...'"
            )
            # Sử dụng simple string search thay vì regex word boundary (không hoạt động tốt với tiếng Việt)
            if normalized_keyword in normalized_text:
                logger.info(f"Pre-filter: Found banned keyword: '{keyword}' in content")
                return (
                    False,
                    f"Nội dung chứa từ khóa cấm đã biết: '{keyword}'.",
                    Severity.CRITICAL,
                )

        # Kiểm tra nguồn không đáng tin cậy
        if source_url:
            normalized_source_url = self._normalize_url(source_url)
            for unreliable_domain in self.rules.get("unreliable_sources", []):
                normalized_unreliable_domain = self._normalize_url(unreliable_domain)
                if normalized_source_url == normalized_unreliable_domain:
                    return (
                        False,
                        f"Nguồn '{source_url}' được xác định là không đáng tin cậy.",
                        Severity.HIGH,
                    )

        return True, "Vượt qua kiểm tra tiền lọc.", Severity.LOW

    async def analyze_content_quality(self, content_text: str) -> dict[str, Any]:
        """
        Giai đoạn 2a: Phân tích sâu về độc hại, thiên vị, lời nói thù ghét bằng LLM.
        """
        # Trả về mặc định an toàn nhưng báo lỗi nếu có vấn đề LLM
        default_analysis = {
            "toxicity_score": 0.0,
            "hate_speech_score": 0.0,
            "bias_score": 0.0,
            "biased_aspects": [],
            "sensitive_topics_detected": [],
            "overall_assessment": "Lỗi phân tích LLM hoặc không phân loại được.",
        }

        prompt = f"""
        Bạn là một chuyên gia phân tích nội dung AI. Hãy đánh giá văn bản sau để xác định mức độ độc hại (toxicity), lời nói thù ghét (hate speech) và thiên vị (bias).
        Cung cấp điểm từ 0.0 (thấp nhất) đến 1.0 (cao nhất) cho mỗi khía cạnh. Nếu có thiên vị, hãy xác định các khía cạnh cụ thể của sự thiên vị (ví dụ: giới tính, chủng tộc, chính trị, tôn giáo, tuổi tác, kinh tế, v.v.).
        Xác định các chủ đề nhạy cảm có trong văn bản (ví dụ: chính trị nhạy cảm, tôn giáo cực đoan, y tế không được xác minh, bạo lực, tự hại, tội phạm, tình dục).

        Văn bản: "{content_text[:4000]}"

        Trả về kết quả dưới dạng JSON:
        {{
            "toxicity_score": float,
            "hate_speech_score": float,
            "bias_score": float,
            "biased_aspects": list[str],
            "sensitive_topics_detected": list[str],
            "overall_assessment": string
        }}
        """
        messages = [{"role": "user", "content": prompt}]
        response_format = {"type": "json_object"}

        try:
            llm_response_str = await self.openrouter_client.chat_completion(
                self.quality_analysis_model,
                messages,
                temperature=0.1,
                max_tokens=700,
                response_format=response_format,
            )
            analysis_data = json.loads(llm_response_str)

            # Đảm bảo các trường điểm số là float và nằm trong khoảng 0-1
            validated_analysis = default_analysis.copy()
            validated_analysis.update(
                {
                    "toxicity_score": max(
                        0.0, min(1.0, float(analysis_data.get("toxicity_score", 0.0)))
                    ),
                    "hate_speech_score": max(
                        0.0,
                        min(1.0, float(analysis_data.get("hate_speech_score", 0.0))),
                    ),
                    "bias_score": max(
                        0.0, min(1.0, float(analysis_data.get("bias_score", 0.0)))
                    ),
                    "biased_aspects": analysis_data.get("biased_aspects", []),
                    "sensitive_topics_detected": analysis_data.get(
                        "sensitive_topics_detected", []
                    ),
                    "overall_assessment": analysis_data.get(
                        "overall_assessment", "Không phân loại được."
                    ),
                }
            )

            return validated_analysis
        except Exception as e:
            logger.error(
                f"Lỗi khi phân tích chất lượng nội dung bằng LLM: {e}. Trả về mặc định an toàn (có báo lỗi)."
            )
            return default_analysis

    async def fact_check_content(
        self, content_text: str
    ) -> tuple[bool, float, str, list[str]]:
        """
        Giai đoạn 2b: Đánh giá tính xác thực của các thông tin sự kiện trong nội dung bằng LLM.
        """
        # Trả về mặc định an toàn nhưng báo lỗi nếu có vấn đề LLM
        default_fact_check = (
            False,
            0.0,
            "Lỗi phân tích LLM hoặc không thể kiểm tra sự thật.",
        )

        prompt = f"""
        Bạn là một hệ thống kiểm chứng thông tin (fact-checker) đáng tin cậy. Hãy phân tích văn bản sau để xác định liệu có bất kỳ tuyên bố sai sự thật (misinformation/disinformation) nào không.
        Đối chiếu các thông tin sự kiện với kiến thức chung của bạn.
        Cung cấp điểm tin cậy từ 0.0 (hoàn toàn sai) đến 1.0 (hoàn toàn đúng sự thật).

        Văn bản: "{content_text[:4000]}"

        Trả về kết quả dưới dạng JSON:
        {{
            "is_factual": boolean,
            "confidence_score": float,
            "misinformation_detected": list[str], (các đoạn văn bản được xác định là sai sự thật)
            "reason": string
        }}
        """
        response_format = {"type": "json_object"}

        try:
            llm_response_str = await self._call_llm(
                prompt,
                self.fact_check_model,
                temperature=0.1,
                max_tokens=700,
                response_format=response_format,
            )
            fact_check_data = json.loads(llm_response_str)

            is_factual = bool(
                fact_check_data.get("is_factual", False)
            )  # Mặc định là False nếu không rõ ràng
            confidence_score = max(
                0.0, min(1.0, float(fact_check_data.get("confidence_score", 0.0)))
            )  # Clamp to 0-1
            reason = fact_check_data.get("reason", "Không có lý do cụ thể.")
            misinformation_detected = fact_check_data.get("misinformation_detected", [])

            return is_factual, confidence_score, reason, misinformation_detected
        except Exception as e:
            logger.error(
                f"Lỗi khi kiểm chứng thông tin bằng LLM: {e}. Trả về mặc định an toàn (có báo lỗi)."
            )
            return default_fact_check + ([],)  # Bổ sung misinformation_detected trống

    def log_content_violation(
        self,
        content_id: str,
        content_text: str,
        source_url: str | None,
        violation_type: ContentViolationType,
        severity: Severity,
        details: str,
        extra_data: dict | None = None,
    ):
        """
        Ghi lại chi tiết về một vi phạm nội dung vào file log chuyên biệt.
        Sử dụng violation_logger đã được cấu hình để ghi JSON.
        """
        truncated_content_text = (
            content_text[:500] + "..." if len(content_text) > 500 else content_text
        )

        # Dữ liệu bổ sung cho log, bao gồm cả các trường từ ContentViolation
        log_extra = {
            "content_id": content_id,
            "source_url": source_url if source_url else "N/A",
            "violation_type": violation_type.value,
            "severity": severity.value,
            "details": details,
            "content_preview": truncated_content_text,
        }
        if extra_data:
            log_extra.update(extra_data)

        # Ghi log bằng violation_logger đã cấu hình với JsonFormatter
        violation_logger.warning(details, extra={"extra_data": log_extra})
        logger.info(
            f"Đã ghi log vi phạm nội dung cho ContentID {content_id}: {details} (Mức: {severity.value})"
        )

    async def filter_content(
        self, content_id: str, content_text: str, source_url: str | None = None
    ) -> tuple[bool, str, Severity, dict[str, Any]]:
        """
        Hàm chính điều phối quá trình lọc nội dung.
        Trả về (is_safe: bool, final_reason: str, overall_severity: Severity, detailed_analysis: Dict).
        """
        logger.info(f"\n--- Bắt đầu lọc nội dung cho ContentID: {content_id} ---")
        logger.info(
            f'Content Preview: "{content_text[:100]}..." | Source: {source_url}'
        )

        is_safe = True
        overall_severity = Severity.LOW
        detailed_analysis: dict[str, Any] = {}
        violation_reasons: list[str] = []

        # 1. Giai đoạn Lọc Nhanh (Pre-filtering)
        (
            pre_filter_safe,
            pre_filter_reason,
            pre_filter_severity,
        ) = await self.pre_filter_content(content_text, source_url)
        if not pre_filter_safe:
            violation_type = (
                ContentViolationType.FORBIDDEN_KEYWORD
                if "từ khóa cấm" in pre_filter_reason
                else (
                    ContentViolationType.UNRELIABLE_SOURCE
                    if "nguồn không đáng tin cậy" in pre_filter_reason
                    else ContentViolationType.SPAM_OR_LOW_QUALITY
                )
            )

            violation_reasons.append(f"Tiền lọc: {pre_filter_reason}")
            overall_severity = max(overall_severity, pre_filter_severity)
            self.log_content_violation(
                content_id,
                content_text,
                source_url,
                violation_type,
                pre_filter_severity,
                pre_filter_reason,
            )

            # Nếu là CRITICAL hoặc HIGH ở tiền lọc, có thể dừng ngay để tiết kiệm tài nguyên
            if pre_filter_severity >= Severity.HIGH:
                is_safe = False  # Đảm bảo cờ an toàn được đặt
                final_reason = "; ".join(violation_reasons)
                logger.warning(
                    f"Nội dung bị chặn sớm ở giai đoạn tiền lọc do mức độ nghiêm trọng: {final_reason}"
                )
                return is_safe, final_reason, overall_severity, detailed_analysis

        # 2. Giai đoạn Lọc Ngữ cảnh và Phân loại (Contextual Filtering / Classification)
        # 2a. Phân tích Chất lượng Nội dung (Toxicity, Hate Speech, Bias)
        quality_analysis = await self.analyze_content_quality(content_text)
        detailed_analysis["quality_analysis"] = quality_analysis

        toxicity_threshold = self.rules.get("toxicity_threshold", 0.8)
        hate_speech_threshold = self.rules.get("hate_speech_threshold", 0.7)
        bias_threshold = self.rules.get("bias_threshold", 0.6)

        if quality_analysis["toxicity_score"] >= toxicity_threshold:
            is_safe = False
            overall_severity = max(overall_severity, Severity.HIGH)
            reason_detail = f"Độc hại (score: {quality_analysis['toxicity_score']:.2f})"
            violation_reasons.append(reason_detail)
            self.log_content_violation(
                content_id,
                content_text,
                source_url,
                ContentViolationType.TOXIC_CONTENT,
                Severity.HIGH,
                reason_detail,
            )

        if quality_analysis["hate_speech_score"] >= hate_speech_threshold:
            is_safe = False
            overall_severity = max(overall_severity, Severity.CRITICAL)
            reason_detail = (
                f"Lời nói thù ghét (score: {quality_analysis['hate_speech_score']:.2f})"
            )
            violation_reasons.append(reason_detail)
            self.log_content_violation(
                content_id,
                content_text,
                source_url,
                ContentViolationType.HATE_SPEECH,
                Severity.CRITICAL,
                reason_detail,
            )

        if quality_analysis["bias_score"] >= bias_threshold:
            is_safe = False
            biased_aspects = (
                ", ".join(quality_analysis.get("biased_aspects", []))
                or "không xác định"
            )
            overall_severity = max(overall_severity, Severity.MEDIUM)
            reason_detail = f"Thiên vị (score: {quality_analysis['bias_score']:.2f}, khía cạnh: {biased_aspects})"
            violation_reasons.append(reason_detail)
            self.log_content_violation(
                content_id,
                content_text,
                source_url,
                ContentViolationType.BIASED_CONTENT,
                Severity.MEDIUM,
                reason_detail,
            )

        # 2b. Kiểm chứng Thông tin (Fact-Checking)
        # Bổ sung thêm `misinformation_detected` từ kết quả của LLM
        (
            fact_check_safe,
            confidence_score,
            fact_check_reason,
            misinformation_detected,
        ) = await self.fact_check_content(content_text)
        detailed_analysis["fact_check"] = {
            "is_factual": fact_check_safe,
            "confidence_score": confidence_score,
            "reason": fact_check_reason,
            "misinformation_detected": misinformation_detected,
        }

        fact_check_confidence_threshold = self.rules.get(
            "fact_check_confidence_threshold", 0.75
        )
        logger.info(
            f"Fact check result: safe={fact_check_safe}, confidence={confidence_score}, threshold={fact_check_confidence_threshold}"
        )
        if not fact_check_safe or confidence_score < fact_check_confidence_threshold:
            logger.info(
                f"Fact check violation detected: safe={fact_check_safe}, confidence={confidence_score} < {fact_check_confidence_threshold}"
            )
            is_safe = False
            overall_severity = max(overall_severity, Severity.HIGH)
            reason_detail = f"Thông tin sai lệch/độ tin cậy thấp (score: {confidence_score:.2f}). Lý do: {fact_check_reason}"
            violation_reasons.append(reason_detail)
            self.log_content_violation(
                content_id,
                content_text,
                source_url,
                ContentViolationType.MISINFORMATION,
                Severity.HIGH,
                reason_detail,
                extra_data={"misinformation_detected_phrases": misinformation_detected},
            )
        else:
            logger.info(
                f"Fact check passed: safe={fact_check_safe}, confidence={confidence_score} >= {fact_check_confidence_threshold}"
            )

        # Tổng hợp kết quả cuối cùng
        if violation_reasons:
            is_safe = False
            final_reason = "Phát hiện vi phạm: " + "; ".join(violation_reasons)
        else:
            final_reason = "Nội dung an toàn."

        logger.info(
            f"--- Kết thúc lọc nội dung cho ContentID: {content_id}. Safe: {is_safe}, Severity: {overall_severity.value} ---"
        )
        return is_safe, final_reason, overall_severity, detailed_analysis

    async def close(self):
        """Đóng client HTTP khi không còn sử dụng."""
        await self.openrouter_client.close()
        logger.info("ContentIntegrityFilter: Đã đóng tất cả các client.")

    async def _call_llm(
        self,
        prompt: str,
        model: OpenRouterModel,
        temperature: float = 0.1,
        max_tokens: int = 700,
        response_format: dict | None = None,
    ) -> str:
        """Call LLM API hoặc trả về test response trong testing mode"""
        if self.testing_mode:
            # Trả về test response và rotate index
            response = self.test_responses[
                self.test_response_index % len(self.test_responses)
            ]
            self.test_response_index += 1
            return response
        else:
            # Gọi real API
            messages = [{"role": "user", "content": prompt}]
            return await self.openrouter_client.chat_completion(
                model, messages, temperature, max_tokens, response_format
            )
