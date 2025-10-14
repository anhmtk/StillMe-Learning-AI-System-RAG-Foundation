import json
import logging
import os
from collections import defaultdict
from dataclasses import dataclass, field
from enum import Enum

import httpx  # Thư viện để gọi API
import numpy as np
from dotenv import load_dotenv  # Để load biến môi trường

# Load biến môi trường từ file .env
load_dotenv()

# Thiết lập logging cơ bản
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)

# Giả định đường dẫn cho các tài nguyên và dữ liệu
CONFIG_PATH = "config/nl_resources.json"  # Vẫn giữ để chứa các cấu hình khác
USER_PROFILES_DB_PATH = "data/user_profiles.json"


# Định nghĩa các Enum
class Sentiment(Enum):
    POSITIVE = "tích cực"
    NEGATIVE = "tiêu cực"
    NEUTRAL = "trung lập"
    MIXED = "pha trộn"


class Tone(Enum):
    FRIENDLY = "thân thiện"
    SERIOUS = "nghiêm túc"
    PLAYFUL = "hài hước"
    ASSERTIVE = "quả quyết"
    PASSIVE = "thụ động"
    EMPATHETIC = "đồng cảm"
    FORMAL = "trang trọng"


class OpenRouterModel(Enum):
    # Một số mô hình phổ biến trên OpenRouter. Bạn có thể thay đổi/thêm bớt tùy nhu cầu.
    GPT_3_5_TURBO = "openai/gpt-3.5-turbo"
    GPT_4O = "openai/gpt-4o"
    GEMINI_PRO = "google/gemini-pro"
    MISTRAL_7B_INSTRUCT = "mistralai/mistral-7b-instruct-v0.2"
    LLAMA_3_8B = "meta-llama/llama-3-8b-instruct"
    CLAUDE_3_HAIKU = "anthropic/claude-3-haiku"  # Thêm mô hình Claude 3 Haiku


@dataclass
class StyleFeatures:
    formality: float = 0.5
    sentiment: Sentiment = Sentiment.NEUTRAL
    humor_level: float = 0.0
    conciseness: float = 0.5
    vocabulary_complexity: float = 0.5
    tone: Tone = Tone.FRIENDLY
    keywords: list[str] = field(default_factory=list)  # Sử dụng list thay vì List

    def to_dict(self):
        return {
            "formality": self.formality,
            "sentiment": (
                self.sentiment.value
                if hasattr(self.sentiment, "value")
                else self.sentiment
            ),
            "humor_level": self.humor_level,
            "conciseness": self.conciseness,
            "vocabulary_complexity": self.vocabulary_complexity,
            "tone": self.tone.value if hasattr(self.tone, "value") else self.tone,
            "keywords": self.keywords,
        }

    @classmethod
    def from_dict(cls, data: dict):
        sentiment = Sentiment(data.get("sentiment", "trung lập"))
        tone = Tone(data.get("tone", "thân thiện"))
        return cls(
            formality=data.get("formality", 0.5),
            sentiment=sentiment,
            humor_level=data.get("humor_level", 0.0),
            conciseness=data.get("conciseness", 0.5),
            vocabulary_complexity=data.get("vocabulary_complexity", 0.5),
            tone=tone,
            keywords=data.get("keywords", []),
        )


class OpenRouterClient:
    """
    Client để tương tác với OpenRouter API.
    """

    def __init__(
        self,
        api_key: str,
        base_url: str = "https://openrouter.ai/api/v1/chat/completions",
        model: OpenRouterModel = OpenRouterModel.GPT_3_5_TURBO,
    ):
        if not api_key:
            raise ValueError(
                "OPENROUTER_API_KEY không được tìm thấy. Vui lòng thiết lập biến môi trường."
            )
        self.client = httpx.AsyncClient(
            headers={
                "Authorization": f"Bearer {api_key}",
                "HTTP-Referer": "https://your-domain-or-app-name.com",  # Thay thế bằng domain/tên app của bạn
                "X-Title": "PersonaMorphAI",  # Tên ứng dụng của bạn
            },
            timeout=30.0,
        )  # Tăng timeout để tránh lỗi kết nối
        self.base_url = base_url
        self.model = model
        logging.info(
            f"OpenRouterClient: Khởi tạo với base URL {base_url} và model {model.value}"
        )

    async def chat_completion(
        self, messages: list, temperature: float = 0.7, max_tokens: int = 500
    ) -> str:
        """
        Gửi yêu cầu chat completion tới OpenRouter API.
        """
        try:
            response = await self.client.post(
                self.base_url,
                json={
                    "model": self.model.value,
                    "messages": messages,
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                },
            )
            response.raise_for_status()  # Raise an exception for HTTP errors (4xx or 5xx)
            data = response.json()
            return data["choices"][0]["message"]["content"]
        except httpx.HTTPStatusError as e:
            logging.error(
                f"Lỗi HTTP khi gọi OpenRouter API: {e.response.status_code} - {e.response.text}"
            )
            return f"Error: Failed to get response from OpenRouter API ({e.response.status_code})"
        except httpx.RequestError as e:
            logging.error(f"Lỗi mạng khi gọi OpenRouter API: {e}")
            return f"Error: Network issue connecting to OpenRouter API ({e})"
        except Exception as e:
            logging.error(f"Lỗi không xác định khi gọi OpenRouter API: {e}")
            return f"Error: An unexpected error occurred ({e})"

    async def close(self):
        await self.client.aclose()


class PersonaAnalyzer:
    """
    Phân tích văn bản đầu vào của người dùng bằng cách sử dụng LLM.
    """

    def __init__(self, openrouter_client: OpenRouterClient):
        self.client = openrouter_client
        self.analysis_model = (
            OpenRouterModel.CLAUDE_3_HAIKU
        )  # Chọn một mô hình cho việc phân tích
        logging.info(
            f"PersonaAnalyzer: Khởi tạo với mô hình phân tích {self.analysis_model.value}."
        )

    async def analyze_user_style(self, user_text: str) -> StyleFeatures:
        """
        Phân tích phong cách của văn bản người dùng sử dụng LLM.
        LLM sẽ trả về một chuỗi JSON chứa các đặc điểm.
        """
        if not user_text.strip():
            logging.info("Input trống, trả về StyleFeatures mặc định.")
            return StyleFeatures()

        prompt = f"""
        Phân tích văn bản sau của người dùng để trích xuất các đặc điểm phong cách.
        Văn bản: "{user_text}"

        Hãy trả về kết quả dưới dạng JSON với các trường sau (dạng tiếng Việt, giá trị số từ 0.0 đến 1.0):
        - "formality": Mức độ trang trọng (0.0: rất thân mật, 1.0: rất trang trọng)
        - "sentiment": Cảm xúc chung (chỉ một trong các giá trị: "tích cực", "tiêu cực", "trung lập", "pha trộn")
        - "humor_level": Mức độ hài hước (0.0: không hài hước, 1.0: rất hài hước)
        - "conciseness": Mức độ ngắn gọn (0.0: dài dòng, 1.0: rất ngắn gọn)
        - "vocabulary_complexity": Độ phức tạp từ vựng (0.0: rất đơn giản, 1.0: rất phức tạp)
        - "tone": Giọng điệu chính (chỉ một trong các giá trị: "thân thiện", "nghiêm túc", "hài hước", "quả quyết", "thụ động", "đồng cảm", "trang trọng")
        - "keywords": 5 từ khóa/cụm từ chính thể hiện nội dung hoặc phong cách.

        Ví dụ JSON:
        {{
            "formality": 0.7,
            "sentiment": "trung lập",
            "humor_level": 0.1,
            "conciseness": 0.6,
            "vocabulary_complexity": 0.8,
            "tone": "nghiêm túc",
            "keywords": ["dự án", "hiệu suất", "tối ưu"]
        }}
        """

        messages = [{"role": "user", "content": prompt}]

        try:
            raw_analysis = await self.client.chat_completion(
                messages, temperature=0.2, max_tokens=300
            )
            logging.info(f"Raw LLM response: {raw_analysis}")

            # Kiểm tra nếu response bắt đầu với "Error:"
            if raw_analysis.startswith("Error:"):
                logging.error(f"LLM API error: {raw_analysis}. Trả về mặc định.")
                return StyleFeatures()

            # Extract chỉ phần JSON từ response (có thể có text giải thích sau)
            json_start = raw_analysis.find("{")
            json_end = raw_analysis.rfind("}") + 1

            if json_start == -1 or json_end == 0:
                logging.error(
                    f"Không tìm thấy JSON trong response: {raw_analysis}. Trả về mặc định."
                )
                return StyleFeatures()

            json_str = raw_analysis[json_start:json_end]
            logging.info(f"Extracted JSON string: {json_str}")

            analysis_data = json.loads(json_str)
            logging.info(f"Parsed JSON data: {analysis_data}")

            features = StyleFeatures.from_dict(analysis_data)
            logging.info(f"Created StyleFeatures: {features.to_dict()}")

        except json.JSONDecodeError as e:
            logging.error(
                f"Không thể phân tích JSON từ phản hồi LLM: {raw_analysis}. Error: {e}. Trả về mặc định."
            )
            features = StyleFeatures()
        except Exception as e:
            logging.error(
                f"Lỗi khi phân tích phong cách bằng LLM: {e}. Trả về mặc định."
            )
            features = StyleFeatures()

        logging.info(f"Phân tích phong cách người dùng (LLM): {features.to_dict()}")
        return features


class PersonaManager:
    """
    Quản lý hồ sơ phong cách của từng người dùng và quyết định persona của AI.
    Logic này được giữ lại vì nó quản lý trạng thái và thích ứng lâu dài.
    """

    def __init__(self, user_profiles_db_path=USER_PROFILES_DB_PATH):
        self.user_profiles_db_path = user_profiles_db_path
        self.user_profiles = defaultdict(dict)
        self._load_profiles()
        logging.info(
            f"PersonaManager: Khởi tạo với DB hồ sơ người dùng tại {user_profiles_db_path}"
        )

    def _load_profiles(self):
        """Tải hồ sơ người dùng từ file JSON."""
        if not os.path.exists(os.path.dirname(self.user_profiles_db_path)):
            os.makedirs(os.path.dirname(self.user_profiles_db_path), exist_ok=True)
        if os.path.exists(self.user_profiles_db_path):
            with open(self.user_profiles_db_path, encoding="utf-8") as f:
                try:
                    profiles = json.load(f)
                    for user_id, profile_data in profiles.items():
                        self.user_profiles[user_id] = {
                            "style_history": [
                                StyleFeatures.from_dict(f)
                                for f in profile_data.get("style_history", [])
                            ],
                            "current_style": StyleFeatures.from_dict(
                                profile_data.get("current_style", {})
                            ),
                        }
                except json.JSONDecodeError:
                    logging.warning(
                        f"Lỗi đọc file JSON {self.user_profiles_db_path}. Tạo lại file trống."
                    )
                    self.user_profiles = defaultdict(dict)
        else:
            logging.info(
                f"File hồ sơ người dùng {self.user_profiles_db_path} không tồn tại, sẽ tạo mới."
            )

    def _save_profiles(self):
        """Lưu hồ sơ người dùng vào file JSON."""
        profiles_to_save = {}
        for user_id, profile in self.user_profiles.items():
            profiles_to_save[user_id] = {
                "style_history": [
                    f.to_dict() for f in profile.get("style_history", [])
                ],
                "current_style": profile.get(
                    "current_style", StyleFeatures()
                ).to_dict(),
            }
        try:
            with open(self.user_profiles_db_path, "w", encoding="utf-8") as f:
                json.dump(profiles_to_save, f, indent=2, ensure_ascii=False)
            logging.info(f"Đã lưu hồ sơ người dùng vào {self.user_profiles_db_path}")
        except OSError as e:
            logging.error(
                f"Không thể lưu hồ sơ người dùng vào {self.user_profiles_db_path}: {e}"
            )

    def load_user_profile(self, user_id: str) -> dict:
        """Tải hồ sơ phong cách của người dùng. Nếu chưa có, tạo hồ sơ mặc định."""
        if user_id not in self.user_profiles:
            self.user_profiles[user_id] = {
                "style_history": [],
                "current_style": StyleFeatures(),  # Default style
            }
            logging.info(f"Tạo hồ sơ mặc định cho người dùng {user_id}.")
        return self.user_profiles[user_id]

    def update_user_profile(self, user_id: str, analyzed_style: StyleFeatures):
        """
        Cập nhật hồ sơ phong cách của người dùng dựa trên phân tích mới nhất.
        Sử dụng cơ chế làm mượt (trung bình cộng có trọng số).
        """
        profile = self.load_user_profile(user_id)

        profile["style_history"].append(analyzed_style)
        profile["style_history"] = profile["style_history"][
            -10:
        ]  # Giới hạn 10 tương tác gần nhất

        num_recent_styles = min(5, len(profile["style_history"]))
        if num_recent_styles == 0:
            profile["current_style"] = StyleFeatures()
            self._save_profiles()
            return

        weights = np.linspace(0.1, 1.0, num_recent_styles)
        weights /= weights.sum()

        recent_styles = profile["style_history"][-num_recent_styles:]

        # Tính trung bình có trọng số cho các đặc điểm số
        new_formality = np.dot([s.formality for s in recent_styles], weights)
        new_humor_level = np.dot([s.humor_level for s in recent_styles], weights)
        new_conciseness = np.dot([s.conciseness for s in recent_styles], weights)
        new_vocab_complexity = np.dot(
            [s.vocabulary_complexity for s in recent_styles], weights
        )

        # Đối với Sentiment và Tone, có thể lấy của lần gần nhất hoặc mode nếu muốn làm mượt.
        # Ở đây vẫn ưu tiên tính thích ứng nhanh bằng cách lấy cái gần nhất từ LLM.
        new_sentiment = analyzed_style.sentiment
        new_tone = analyzed_style.tone
        new_keywords = analyzed_style.keywords

        new_style = StyleFeatures(
            formality=new_formality,
            sentiment=new_sentiment,
            humor_level=new_humor_level,
            conciseness=new_conciseness,
            vocabulary_complexity=new_vocab_complexity,
            tone=new_tone,
            keywords=new_keywords,
        )

        profile["current_style"] = new_style
        logging.info(f"Đã cập nhật hồ sơ người dùng {user_id}: {new_style.to_dict()}")
        self._save_profiles()

    def determine_ai_persona(self, user_id: str) -> StyleFeatures:
        """
        Xác định persona mà AI nên áp dụng cho phản hồi tiếp theo dựa trên hồ sơ người dùng.
        Áp dụng các luật tùy chỉnh và điều chỉnh.
        """
        user_profile = self.load_user_profile(user_id)
        user_style = user_profile["current_style"]

        ai_persona = StyleFeatures(**user_style.to_dict())

        # Luật tùy chỉnh: Nếu người dùng tiêu cực, AI nên đồng cảm
        if user_style.sentiment == Sentiment.NEGATIVE:
            ai_persona.sentiment = Sentiment.NEUTRAL  # AI không nên phản hồi tiêu cực
            ai_persona.tone = Tone.EMPATHETIC  # AI thể hiện sự đồng cảm
            ai_persona.formality = min(1.0, user_style.formality + 0.2)
            ai_persona.humor_level = 0.0
            ai_persona.conciseness = max(0.0, user_style.conciseness - 0.2)

        # Nếu người dùng rất hài hước, AI có thể bớt hài hước một chút để không lấn át
        elif user_style.humor_level > 0.8:
            ai_persona.humor_level = max(0.2, user_style.humor_level - 0.3)

        # Nếu người dùng rất trang trọng, AI có thể bớt trang trọng một chút để không quá cứng nhắc
        elif user_style.formality > 0.8:
            ai_persona.formality = max(0.5, user_style.formality - 0.1)

        logging.info(f"Persona AI được xác định cho {user_id}: {ai_persona.to_dict()}")
        return ai_persona


class PersonaGenerator:
    """
    Chuyển đổi văn bản phản hồi gốc của AI sang phong cách đã chọn bằng cách sử dụng LLM.
    """

    def __init__(self, openrouter_client: OpenRouterClient):
        self.client = openrouter_client
        self.generation_model = (
            OpenRouterModel.GPT_3_5_TURBO
        )  # Chọn một mô hình cho việc sinh văn bản
        logging.info(
            f"PersonaGenerator: Khởi tạo với mô hình sinh văn bản {self.generation_model.value}."
        )

    async def generate_styled_response(
        self, original_response: str, ai_persona: StyleFeatures
    ) -> str:
        """
        Yêu cầu LLM chuyển đổi văn bản phản hồi gốc sang phong cách đã chọn.
        """
        prompt = f"""
        Bạn là một trợ lý AI. Hãy điều chỉnh phản hồi sau đây để phù hợp với các đặc điểm phong cách được chỉ định.
        Hãy đảm bảo phản hồi vẫn tự nhiên và giữ nguyên ý nghĩa cốt lõi.

        Phản hồi gốc: "{original_response}"

        Đặc điểm phong cách mong muốn:
        - Mức độ trang trọng: {ai_persona.formality:.1f} (0.0=thân mật, 1.0=trang trọng)
        - Cảm xúc: {ai_persona.sentiment.value if hasattr(ai_persona.sentiment, 'value') else ai_persona.sentiment}
        - Mức độ hài hước: {ai_persona.humor_level:.1f} (0.0=không hài hước, 1.0=rất hài hước)
        - Mức độ ngắn gọn: {ai_persona.conciseness:.1f} (0.0=dài dòng, 1.0=ngắn gọn)
        - Độ phức tạp từ vựng: {ai_persona.vocabulary_complexity:.1f} (0.0=đơn giản, 1.0=phức tạp)
        - Giọng điệu: {ai_persona.tone.value if hasattr(ai_persona.tone, 'value') else ai_persona.tone}
        - Từ khóa ưu tiên: {', '.join(ai_persona.keywords) if ai_persona.keywords else 'Không có'}

        Hãy tạo ra phản hồi đã điều chỉnh phong cách bằng tiếng Việt.
        """

        messages = [{"role": "user", "content": prompt}]

        try:
            styled_response = await self.client.chat_completion(
                messages, temperature=0.7
            )
        except Exception as e:
            logging.error(
                f"Lỗi khi sinh phản hồi đã điều chỉnh bằng LLM: {e}. Trả về phản hồi gốc."
            )
            styled_response = original_response

        logging.info(
            f"Phản hồi đã điều chỉnh theo persona {ai_persona.tone.value if hasattr(ai_persona.tone, 'value') else ai_persona.tone} (LLM): \"{styled_response}\""
        )
        return styled_response


class PersonaMorph:
    """
    Module chính điều phối hoạt động của PersonaAnalyzer, PersonaManager, và PersonaGenerator.
    """

    def __init__(self):
        # Đảm bảo thư mục data và config tồn tại
        os.makedirs(os.path.dirname(USER_PROFILES_DB_PATH), exist_ok=True)
        os.makedirs(os.path.dirname(CONFIG_PATH), exist_ok=True)

        # Khởi tạo OpenRouter client
        openrouter_api_key = os.getenv("OPENROUTER_API_KEY")
        if not openrouter_api_key:
            raise ValueError("OPENROUTER_API_KEY environment variable not set.")
        self.openrouter_client = OpenRouterClient(api_key=openrouter_api_key)

        self.analyzer = PersonaAnalyzer(openrouter_client=self.openrouter_client)
        self.manager = PersonaManager()
        self.generator = PersonaGenerator(openrouter_client=self.openrouter_client)
        logging.info("PersonaMorph: Khởi tạo hoàn tất.")

    async def process_interaction(
        self, user_id: str, user_text: str, original_ai_response: str
    ) -> str:
        """
        Xử lý một tương tác, phân tích phong cách người dùng, cập nhật hồ sơ,
        xác định persona của AI và tạo phản hồi đã điều chỉnh phong cách.
        """
        logging.info(f"\n--- Bắt đầu xử lý tương tác cho User: {user_id} ---")
        logging.info(f'Người dùng nói: "{user_text}"')
        logging.info(f'Phản hồi AI gốc: "{original_ai_response}"')

        # 1. Phân tích phong cách người dùng
        analyzed_style = await self.analyzer.analyze_user_style(user_text)

        # 2. Cập nhật hồ sơ người dùng
        self.manager.update_user_profile(user_id, analyzed_style)

        # 3. Xác định persona AI
        ai_persona = self.manager.determine_ai_persona(user_id)

        # 4. Tạo phản hồi AI đã điều chỉnh phong cách
        styled_response = await self.generator.generate_styled_response(
            original_ai_response, ai_persona
        )

        logging.info(f"--- Kết thúc xử lý tương tác cho User: {user_id} ---\n")
        return styled_response

    async def close(self):
        """Đóng client HTTP khi không còn sử dụng."""
        await self.openrouter_client.close()
        logging.info("PersonaMorph: Đã đóng OpenRouter client.")