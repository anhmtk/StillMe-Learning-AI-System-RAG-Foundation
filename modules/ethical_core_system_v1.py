#!/usr/bin/env python3
"""
⚖️ ETHICAL CORE SYSTEM - AI SAFETY & COMPLIANCE
⚖️ HỆ THỐNG ĐẠO ĐỨC CORE - AN TOÀN AI & TUÂN THỦ

PURPOSE / MỤC ĐÍCH:
- AI safety and ethical compliance system
- Hệ thống an toàn AI và tuân thủ đạo đức
- Content filtering and violation detection
- Lọc nội dung và phát hiện vi phạm
- Ensures AI responses meet ethical standards
- Đảm bảo phản hồi AI đáp ứng tiêu chuẩn đạo đức

FUNCTIONALITY / CHỨC NĂNG:
- Content validation and filtering
- Xác thực và lọc nội dung
- Ethical rule enforcement
- Thực thi quy tắc đạo đức
- Violation logging and reporting
- Ghi log và báo cáo vi phạm
- Safety score calculation
- Tính toán điểm an toàn
- Multi-language support (VI/EN)
- Hỗ trợ đa ngôn ngữ (VI/EN)

RELATED FILES / FILES LIÊN QUAN:
- config/ethical_rules.json - Ethical rules configuration
- framework.py - Framework integration
- stable_ai_server.py - AI server integration
- logs/ethical_violations.log - Violation logs

TECHNICAL DETAILS / CHI TIẾT KỸ THUẬT:
- Async/await support for high performance
- Rule-based and AI-powered validation
- Configurable safety thresholds
- Real-time violation detection
- Comprehensive logging system
"""

import os
import asyncio
import json
import logging
from enum import Enum
from typing import Optional, Tuple, Dict, Any
import httpx # Import httpx cần thiết cho OpenRouterClient

# --- Cấu hình Logger ---
LOGS_DIR = "logs"
ETHICAL_VIOLATIONS_LOG = os.path.join(LOGS_DIR, "ethical_violations.log")

# Đảm bảo thư mục logs tồn tại
os.makedirs(LOGS_DIR, exist_ok=True)

ethical_logger = logging.getLogger("ethical_violations")
ethical_logger.setLevel(logging.WARNING)
ethical_logger.propagate = False # Ngăn không cho log lên root logger

# Tạo handler chỉ khi chưa có để tránh thêm handler nhiều lần
if not ethical_logger.handlers:
    file_handler = logging.FileHandler(ETHICAL_VIOLATIONS_LOG, encoding='utf-8')
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - User ID: %(user_id)s - Violation Type: %(violation_type)s - Severity: %(severity)s - Message: %(message)s')
    file_handler.setFormatter(formatter)
    ethical_logger.addHandler(file_handler)

def close_violation_logger():
    """Đóng handler của ethical_logger. Sử dụng để dọn dẹp trong các bài test."""
    for handler in ethical_logger.handlers[:]: # Lặp trên một bản sao của danh sách handler
        handler.close()
        ethical_logger.removeHandler(handler)

# --- Định nghĩa các Enums ---
class OpenRouterModel(Enum):
    MISTRAL_7B_INSTRUCT = "mistralai/mistral-7b-instruct"
    OPENCHAT_7B = "openchat/openchat-7b"
    GEMINI_PRO = "google/gemini-pro"
    # Thêm các model khác nếu cần

class Sentiment(Enum):
    POSITIVE = "positive"
    NEGATIVE = "negative"
    NEUTRAL = "neutral"

class Tone(Enum):
    FORMAL = "formal"
    INFORMAL = "informal"
    FRIENDLY = "friendly"
    SERIOUS = "serious"
    NEUTRAL = "neutral"

class Severity(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class ViolationType(Enum):
    FORBIDDEN_KEYWORD = "từ khóa cấm"
    TOXIC_CONTENT = "nội dung độc hại"
    HATE_SPEECH = "ngôn ngữ thù địch"
    SELF_HARM = "tự gây hại"
    ILLEGAL_ACTIVITY = "hoạt động bất hợp pháp"
    PRIVACY_VIOLATION = "vi phạm quyền riêng tư"
    VULNERABLE_USER = "người dùng dễ bị tổn thương"
    IMPERSONATION = "mạo danh"
    LLM_ERROR = "Lỗi LLM"
    ETHICAL_NON_COMPLIANCE = "không tuân thủ đạo đức"
    # Thêm các loại vi phạm khác nếu cần

# --- OpenRouterClient Class ---
class OpenRouterClient:
    def __init__(self, api_key: str, model: OpenRouterModel = OpenRouterModel.MISTRAL_7B_INSTRUCT):
        if not api_key:
            raise ValueError("API key must be provided for OpenRouterClient.")
        self.api_key = api_key
        self.base_url = "https://openrouter.ai/api/v1/chat/completions"
        self.model = model

    async def chat_completion(self, messages: list, temperature: float = 0.7, max_tokens: int = 150) -> str:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.model.value,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(self.base_url, headers=headers, json=payload)
                response.raise_for_status()
                return response.json()["choices"][0]["message"]["content"]
            except httpx.HTTPStatusError as e:
                ethical_logger.error(f"HTTP error occurred: {e.response.status_code} - {e.response.text}")
                raise
            except Exception as e:
                ethical_logger.error(f"An error occurred during API call: {e}")
                raise

# --- EthicsGuard Class ---
class EthicsGuard:
    def __init__(self, openrouter_client: OpenRouterClient, rules_file: str = "config/ethical_rules.json"):
        self.openrouter_client = openrouter_client
        self.rules_file = rules_file
        self.forbidden_keywords: list = []
        self.sensitive_topics: list = []
        self.violation_response = "Xin lỗi, tôi không thể thảo luận về vấn đề đó. Tôi có thể giúp bạn với điều gì khác không?"
        self._load_ethical_rules()

    def _load_ethical_rules(self):
        try:
            with open(self.rules_file, 'r', encoding='utf-8') as f:
                rules = json.load(f)
                self.forbidden_keywords = [k.lower() for k in rules.get("forbidden_keywords", [])]
                self.sensitive_topics = [t.lower() for t in rules.get("sensitive_topics", [])]
        except FileNotFoundError:
            ethical_logger.warning("Ethical rules file not found. Using empty rules.")
            self.forbidden_keywords = []
            self.sensitive_topics = []
        except json.JSONDecodeError:
            ethical_logger.error("Error decoding JSON from ethical rules file. Using empty rules.")
            self.forbidden_keywords = []
            self.sensitive_topics = []
        except Exception as e:
            ethical_logger.error(f"An unexpected error occurred loading ethical rules: {e}")
            self.forbidden_keywords = []
            self.sensitive_topics = []

    def detect_keywords(self, text: str) -> bool:
        text_lower = text.lower()
        for keyword in self.forbidden_keywords:
            if keyword in text_lower:
                return True
        return False

    async def check_input_safety(self, user_input: str) -> Tuple[bool, Optional[ViolationType], Optional[Severity], str]:
        if self.detect_keywords(user_input):
            return False, ViolationType.FORBIDDEN_KEYWORD, Severity.HIGH, "Input chứa từ khóa cấm."

        try:
            prompt = f"""Phân tích văn bản sau để xác định xem nó có độc hại, ngôn ngữ thù địch hoặc chứa các chủ đề nhạy cảm không.
            Trả về một đối tượng JSON với các trường:
            - "is_toxic": boolean
            - "toxicity_score": float (từ 0.0 đến 1.0)
            - "is_hate_speech": boolean
            - "hate_speech_score": float (từ 0.0 đến 1.0)
            - "sensitive_topics_detected": list of strings (ví dụ: "bạo lực", "tự hại", "phân biệt đối xử")
            - "reason": string giải thích lý do
            
            Văn bản: "{user_input}"
            """
            response_content = await self.openrouter_client.chat_completion(
                messages=[{"role": "user", "content": prompt}]
            )
            safety_assessment = json.loads(response_content)

            if safety_assessment.get("is_toxic"):
                return False, ViolationType.TOXIC_CONTENT, Severity.MEDIUM, safety_assessment.get("reason", "Nội dung độc hại.")
            if safety_assessment.get("is_hate_speech"):
                return False, ViolationType.HATE_SPEECH, Severity.HIGH, safety_assessment.get("reason", "Nội dung thù địch.")
            
            # Kiểm tra chủ đề nhạy cảm từ phản hồi LLM với danh sách nhạy cảm của hệ thống
            detected_sensitive = safety_assessment.get("sensitive_topics_detected", [])
            for topic in detected_sensitive:
                if topic.lower() in self.sensitive_topics:
                    return False, ViolationType.SELF_HARM, Severity.HIGH, f"Chủ đề nhạy cảm được phát hiện: {topic}." 
            
            return True, None, None, "An toàn."
        except Exception as e:
            ethical_logger.error(f"Error checking input safety with LLM: {e}")
            return False, ViolationType.LLM_ERROR, Severity.CRITICAL, f"Đã xảy ra lỗi trong quá trình kiểm tra an toàn input: {e}"

    async def check_output_safety(self, ai_response: str) -> Tuple[bool, Optional[ViolationType], Optional[Severity], str]:
        if self.detect_keywords(ai_response):
            return False, ViolationType.FORBIDDEN_KEYWORD, Severity.HIGH, "Output chứa từ khóa cấm."
        
        try:
            prompt = f"""Phân tích văn bản phản hồi AI sau để xác định xem nó có độc hại, ngôn ngữ thù địch, hoặc không phù hợp không.
            Trả về một đối tượng JSON với các trường:
            - "is_toxic": boolean
            - "toxicity_score": float (từ 0.0 đến 1.0)
            - "is_hate_speech": boolean
            - "hate_speech_score": float (từ 0.0 đến 1.0)
            - "is_appropriate": boolean
            - "reason": string giải thích lý do

            Phản hồi AI: "{ai_response}"
            """
            response_content = await self.openrouter_client.chat_completion(
                messages=[{"role": "user", "content": prompt}]
            )
            safety_assessment = json.loads(response_content)

            if safety_assessment.get("is_toxic"):
                return False, ViolationType.TOXIC_CONTENT, Severity.MEDIUM, safety_assessment.get("reason", "Nội dung độc hại trong phản hồi.")
            if safety_assessment.get("is_hate_speech"):
                return False, ViolationType.HATE_SPEECH, Severity.HIGH, safety_assessment.get("reason", "Nội dung thù địch trong phản hồi.")
            if not safety_assessment.get("is_appropriate"):
                return False, ViolationType.ETHICAL_NON_COMPLIANCE, Severity.MEDIUM, safety_assessment.get("reason", "Phản hồi không phù hợp.")
            
            return True, None, None, "An toàn."
        except Exception as e:
            ethical_logger.error(f"Error checking output safety with LLM: {e}")
            return False, ViolationType.LLM_ERROR, Severity.CRITICAL, f"Đã xảy ra lỗi trong quá trình kiểm tra an toàn output: {e}"

    async def assess_vulnerability(self, user_input: str) -> Tuple[bool, str]:
        try:
            prompt = f"""Phân tích văn bản sau để xác định xem người dùng có vẻ dễ bị tổn thương, căng thẳng, buồn bã hoặc có ý định tự hại không.
            Trả về một đối tượng JSON với các trường:
            - "is_vulnerable": boolean
            - "reason": string giải thích lý do (Nếu is_vulnerable là true)
            
            Văn bản: "{user_input}"
            """
            response_content = await self.openrouter_client.chat_completion(
                messages=[{"role": "user", "content": prompt}]
            )
            vulnerability_assessment = json.loads(response_content)
            return vulnerability_assessment.get("is_vulnerable", False), vulnerability_assessment.get("reason", "Không có dấu hiệu.")
        except Exception as e:
            ethical_logger.error(f"Error assessing vulnerability with LLM: {e}")
            return False, f"Đã xảy ra lỗi trong quá trình đánh giá lỗ hổng: {e}"

# --- ConscienceCore Class ---
class ConscienceCore:
    def __init__(self, openrouter_client: OpenRouterClient):
        self.openrouter_client = openrouter_client

    async def evaluate_ethical_compliance(self, user_input: str, ai_response: str) -> Tuple[bool, float, str]:
        try:
            prompt = f"""Đánh giá mức độ tuân thủ đạo đức của phản hồi AI dưới đây, dựa trên input của người dùng và các nguyên tắc đạo đức chung.
            Trả về một đối tượng JSON với các trường:
            - "is_compliant": boolean
            - "compliance_score": float (từ 0.0 đến 1.0, 1.0 là tuân thủ hoàn toàn)
            - "reason": string giải thích lý do
            
            Input người dùng: "{user_input}"
            Phản hồi AI: "{ai_response}"
            """
            response_content = await self.openrouter_client.chat_completion(
                messages=[{"role": "user", "content": prompt}]
            )
            compliance_assessment = json.loads(response_content)
            return compliance_assessment.get("is_compliant", False), compliance_assessment.get("compliance_score", 0.0), compliance_assessment.get("reason", "Không rõ.")
        except Exception as e:
            ethical_logger.error(f"Error evaluating ethical compliance with LLM: {e}")
            return False, 0.0, f"Đã xảy ra lỗi trong quá trình đánh giá tuân thủ đạo đức: {e}"

    async def adjust_response_ethically(self, user_input: str, ai_response: str, violation_reason: str) -> str:
        try:
            prompt = f"""Phản hồi AI sau đây đã được xác định là không tuân thủ đạo đức vì: {violation_reason}.
            Vui lòng điều chỉnh lại phản hồi này để nó trở nên phù hợp và có đạo đức, đồng thời vẫn hữu ích nếu có thể.
            Nếu không thể điều chỉnh, hãy đưa ra một phản hồi từ chối lịch sự.
            
            Input người dùng: "{user_input}"
            Phản hồi AI gốc: "{ai_response}"
            
            Phản hồi AI đã điều chỉnh:"""
            adjusted_response = await self.openrouter_client.chat_completion(
                messages=[{"role": "user", "content": prompt}]
            )
            return adjusted_response
        except Exception as e:
            ethical_logger.error(f"Error adjusting response with LLM: {e}")
            return "Xin lỗi, đã xảy ra lỗi trong quá trình xử lý yêu cầu của bạn. Vui lòng thử lại sau."

# --- SelfCritic Class ---
class SelfCritic:
    def __init__(self, openrouter_client: OpenRouterClient):
        self.openrouter_client = openrouter_client

    def log_ethical_violation(self, user_id: str, user_input: str, ai_response: str,
                            violation_type: ViolationType, severity: Severity, reason: str):
        ethical_logger.warning(
            f"VIOLATION: {reason}. User input: '{user_input}'. AI response: '{ai_response}'",
            extra={
                'user_id': user_id,
                'violation_type': violation_type.value,
                'severity': severity.value
            }
        )

    async def analyze_and_learn(self, user_id: str, user_input: str, ai_response: str,
                                violation_type: ViolationType, severity: Severity, reason: str):
        try:
            prompt = f"""Phân tích vi phạm đạo đức sau để xác định nguyên nhân gốc rễ và đề xuất hành động cải thiện cho hệ thống AI.
            Loại vi phạm: {violation_type.value}
            Mức độ nghiêm trọng: {severity.value}
            Lý do: {reason}
            Input người dùng: "{user_input}"
            Phản hồi AI: "{ai_response}"

            Trả về một đối tượng JSON với các trường:
            - "root_cause": string (ví dụ: "Thiếu bộ lọc từ khóa", "Mô hình LLM không đủ tinh chỉnh")
            - "suggested_action": string (ví dụ: "Cập nhật danh sách từ khóa cấm", "Tinh chỉnh mô hình LLM với dữ liệu đạo đức hơn")
            """
            analysis_result = await self.openrouter_client.chat_completion(
                messages=[{"role": "user", "content": prompt}]
            )
            return json.loads(analysis_result)
        except Exception as e:
            ethical_logger.error(f"Error analyzing and learning from violation: {e}")
            return {"root_cause": f"Lỗi phân tích: {e}", "suggested_action": "Không thể phân tích nguyên nhân gốc rễ."}

# --- EthicalCoreSystem Class ---
class EthicalCoreSystem:
    def __init__(self):
        api_key = os.environ.get("OPENROUTER_API_KEY")
        if not api_key:
            raise ValueError("OPENROUTER_API_KEY environment variable not set.")
        
        self.openrouter_client = OpenRouterClient(api_key=api_key)
        self.ethics_guard = EthicsGuard(openrouter_client=self.openrouter_client)
        self.conscience_core = ConscienceCore(openrouter_client=self.openrouter_client)
        self.self_critic = SelfCritic(openrouter_client=self.openrouter_client)
        
        self.violation_response_default = "Xin lỗi, tôi không thể thực hiện yêu cầu này vì nó có thể vi phạm các nguyên tắc đạo đức."

    async def process_interaction(self, user_id: str, user_input: str, original_ai_response: str) -> Tuple[str, bool, str]:
        violation_message = ""
        is_compliant = True
        final_response = original_ai_response

        try:
            # 1. Kiểm tra an toàn input
            is_input_safe, input_violation_type, input_severity, input_reason = await self.ethics_guard.check_input_safety(user_input)
            if not is_input_safe:
                violation_message = input_reason
                is_compliant = False
                if input_violation_type is not None and input_severity is not None:
                    self.self_critic.log_ethical_violation(user_id, user_input, original_ai_response, input_violation_type, input_severity, input_reason)
                    await self.self_critic.analyze_and_learn(user_id, user_input, original_ai_response, input_violation_type, input_severity, input_reason)
                return self.ethics_guard.violation_response, is_compliant, violation_message

            # 2. Đánh giá người dùng dễ bị tổn thương
            is_vulnerable, vulnerability_reason = await self.ethics_guard.assess_vulnerability(user_input)
            if is_vulnerable:
                violation_message += f"Người dùng có dấu hiệu dễ bị tổn thương: {vulnerability_reason}. "
                # Đây không phải là vi phạm cứng mà là cảnh báo để hệ thống phản hồi cẩn thận hơn
                self.self_critic.log_ethical_violation(user_id, user_input, original_ai_response, ViolationType.VULNERABLE_USER, Severity.LOW, vulnerability_reason)
            
            # 3. Kiểm tra an toàn output
            is_output_safe, output_violation_type, output_severity, output_reason = await self.ethics_guard.check_output_safety(original_ai_response)
            if not is_output_safe:
                violation_message += f"Phản hồi AI vi phạm an toàn: {output_reason}. "
                is_compliant = False
                if output_violation_type is not None and output_severity is not None:
                    self.self_critic.log_ethical_violation(user_id, user_input, original_ai_response, output_violation_type, output_severity, output_reason)
                
                # Cố gắng điều chỉnh phản hồi
                adjusted_response = await self.conscience_core.adjust_response_ethically(user_input, original_ai_response, output_reason)
                final_response = adjusted_response
                
                # Kiểm tra lại tính tuân thủ của phản hồi đã điều chỉnh
                is_adjusted_compliant, _, adjusted_reason = await self.conscience_core.evaluate_ethical_compliance(user_input, final_response)
                if not is_adjusted_compliant:
                    violation_message += f"Phản hồi đã điều chỉnh vẫn không tuân thủ: {adjusted_reason}. "
                    self.self_critic.log_ethical_violation(user_id, user_input, final_response, ViolationType.ETHICAL_NON_COMPLIANCE, Severity.MEDIUM, adjusted_reason + " (sau điều chỉnh)")
                    await self.self_critic.analyze_and_learn(user_id, user_input, final_response, ViolationType.ETHICAL_NON_COMPLIANCE, Severity.MEDIUM, adjusted_reason + " (sau điều chỉnh)")
                else:
                    is_compliant = True # Phản hồi đã điều chỉnh thành công
                    violation_message += "Phản hồi đã được điều chỉnh để tuân thủ đạo đức."
                    if output_violation_type is not None and output_severity is not None:
                        await self.self_critic.analyze_and_learn(user_id, user_input, original_ai_response, output_violation_type, output_severity, output_reason)

            # 4. Đánh giá tuân thủ đạo đức tổng thể (nếu chưa bị chặn)
            if is_compliant: # Chỉ đánh giá nếu chưa có vi phạm nghiêm trọng
                is_overall_compliant, compliance_score, compliance_reason = await self.conscience_core.evaluate_ethical_compliance(user_input, final_response)
                if not is_overall_compliant:
                    violation_message += f"Phản hồi không tuân thủ đạo đức tổng thể: {compliance_reason}. "
                    is_compliant = False
                    self.self_critic.log_ethical_violation(user_id, user_input, final_response, ViolationType.ETHICAL_NON_COMPLIANCE, Severity.MEDIUM, compliance_reason)
                    await self.self_critic.analyze_and_learn(user_id, user_input, final_response, ViolationType.ETHICAL_NON_COMPLIANCE, Severity.MEDIUM, compliance_reason)

        except Exception as e:
            ethical_logger.error(f"An unexpected error occurred during interaction processing: {e}", extra={'user_id': user_id})
            violation_message = f"Đã xảy ra lỗi trong quá trình xử lý đạo đức: {e}"
            is_compliant = False
            final_response = self.violation_response_default
            self.self_critic.log_ethical_violation(user_id, user_input, original_ai_response, ViolationType.LLM_ERROR, Severity.CRITICAL, f"Lỗi không mong muốn: {e}")
            
        return final_response, is_compliant, violation_message

    async def close(self):
        """Đóng mọi tài nguyên nếu cần."""
        pass # Hiện tại không có tài nguyên đặc biệt cần đóng trong các class này