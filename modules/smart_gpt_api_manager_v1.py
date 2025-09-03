# modules/smart_gpt_api_manager_v1.py
import os
import logging
import time
from typing import List, Dict, Optional
from openai import OpenAI
import ollama

class TokenOptimizer:
    """Mock class nếu không import được từ token_optimizer_v1"""
    @staticmethod
    def optimize(prompt: str) -> str:
        return prompt[:5000]  # Giả lập cắt bớt prompt dài

class SmartGPTAPIManager:
    """Quản lý và tối ưu việc gọi các API AI model."""
    
    def __init__(self, model_preferences: List[str], fallback_model: str = "gpt-3.5-turbo"):
        """
        Khởi tạo API Manager.
        
        Args:
            model_preferences: Danh sách model ưu tiên (vd: ['deepseek-coder', 'gpt-4o'])
            fallback_model: Model dự phòng khi các model chính fail
        """
        self.model_preferences = model_preferences or ["gpt-3.5-turbo"]  # Ensure non-empty
        self.fallback_model = fallback_model or "gpt-3.5-turbo"  # Ensure non-None
        self.openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY")) if os.getenv("OPENAI_API_KEY") else None
        self.usage_stats: Dict[str, Dict] = {}
        self.logger = logging.getLogger("SmartGPTAPIManager")
        self.logger.setLevel(logging.INFO)
        
    def choose_model(self, prompt: str) -> str:
        """Chọn model tối ưu dựa trên prompt và model preferences."""
        prompt_len = len(prompt)
        
        # Rule 1: Prompt dài > 3000 token → dùng local model (DeepSeek) để tiết kiệm cost
        if prompt_len > 3000 and "deepseek-coder" in self.model_preferences:
            return "deepseek-coder"
            
        # Rule 2: Prompt yêu cầu sáng tạo → ưu tiên GPT-4o
        creative_keywords = ["viết", "sáng tạo", "nghĩ", "đề xuất"]
        if any(keyword in prompt.lower() for keyword in creative_keywords) and "gpt-4o" in self.model_preferences:
            return "gpt-4o"
            
        # Rule 3: Fallback theo thứ tự ưu tiên
        for model in self.model_preferences:
            if model in ["deepseek-coder", "gpt-4o", "gpt-3.5-turbo"]:
                return model
                
        # Final fallback - ensure we always return a string
        return self.fallback_model
    
    def call_api(self, prompt: str, max_retries: int = 2) -> str:
        """
        Gọi API model với retry mechanism.
        
        Args:
            prompt: Câu hỏi/đầu vào cho AI
            max_retries: Số lần thử lại tối đa
            
        Returns:
            Câu trả lời từ AI hoặc thông báo lỗi
        """
        model = self.choose_model(prompt)
        optimized_prompt = TokenOptimizer.optimize(prompt) if 'TokenOptimizer' in globals() else prompt
        
        for attempt in range(max_retries + 1):
            try:
                start_time = time.time()
                
                if model == "deepseek-coder":
                    response = ollama.generate(
                        model="deepseek-coder:6.7b",
                        prompt=optimized_prompt,
                        options={"temperature": 0.7}
                    )
                    result = response.get("response", "No response from DeepSeek")
                elif model.startswith("gpt-"):
                    if not self.openai_client:
                        raise RuntimeError("OpenAI client chưa được cấu hình")
                    response = self.openai_client.chat.completions.create(
                        model=model,
                        messages=[{"role": "user", "content": optimized_prompt}],
                        temperature=0.7
                    )
                    result = response.choices[0].message.content
                else:
                    result = self.simulate_call(optimized_prompt)
                
                elapsed_time = time.time() - start_time
                self._log_call(model, prompt, result, elapsed_time, success=True)
                return result
                
            except Exception as e:
                self.logger.error(f"Attempt {attempt + 1} failed with {model}: {str(e)}")
                if attempt == max_retries:
                    self._log_call(model, prompt, str(e), 0, success=False)
                    return f"Error after {max_retries} retries: {str(e)}"
                
                # Fallback logic
                if model != self.fallback_model:
                    model = self.fallback_model
    
    def simulate_call(self, prompt: str) -> str:
        """Mock API response cho mục đích testing."""
        return f"Mock response for: {prompt[:50]}..."
    
    def analyze_usage(self) -> Dict[str, Dict]:
        """Phân tích thống kê sử dụng API."""
        return self.usage_stats
    
    def _log_call(self, model: str, prompt: str, response: str, elapsed_time: float, success: bool):
        """Ghi log và cập nhật thống kê."""
        log_entry = {
            "model": model,
            "prompt_length": len(prompt),
            "response_length": len(response),
            "elapsed_time": elapsed_time,
            "success": success,
            "timestamp": time.time()
        }
        
        if model not in self.usage_stats:
            self.usage_stats[model] = {"total_calls": 0, "total_time": 0.0, "success_calls": 0}
            
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