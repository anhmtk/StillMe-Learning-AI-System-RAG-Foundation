# modules/api_provider_manager.py
import os
import logging
import time
import requests
from typing import List, Dict, Optional, Any
from openai import OpenAI
import ollama

# CRITICAL: Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()  # Load .env file into os.environ
    print("✅ API Provider Manager: Environment variables loaded from .env file")
except ImportError:
    print("⚠️ API Provider Manager: python-dotenv not installed. Install with: pip install python-dotenv")
except Exception as e:
    print(f"⚠️ API Provider Manager: Error loading .env file: {e}")

class TokenOptimizer:
    """Mock class nếu không import được từ token_optimizer_v1"""
    @staticmethod
    def optimize(prompt: str) -> str:
        return prompt[:5000]  # Giả lập cắt bớt prompt dài

class UnifiedAPIManager:
    """Unified API Manager for multiple providers (DeepSeek, OpenRouter, OpenAI, Ollama)."""
    
    def __init__(self, model_preferences: Optional[List[str]] = None, fallback_model: str = "gpt-3.5-turbo"):
        """
        Initialize Unified API Manager.
        
        Args:
            model_preferences: List of preferred models (e.g., ['deepseek-coder', 'gpt-4o'])
            fallback_model: Fallback model when main models fail
        """
        self.model_preferences = model_preferences or ["deepseek-chat"]  # Default to DeepSeek
        self.fallback_model = fallback_model or "deepseek-chat"
        
        # Provider configuration
        self.preferred_provider = os.getenv('PREFERRED_PROVIDER', 'deepseek')  # Default to DeepSeek
        
        # API clients
        self.openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY")) if os.getenv("OPENAI_API_KEY") else None
        
        # API keys
        self.deepseek_api_key = os.getenv("DEEPSEEK_API_KEY")
        self.openrouter_api_key = os.getenv("OPENROUTER_API_KEY")
        
        # Usage stats
        self.usage_stats: Dict[str, Dict] = {}
        self.logger = logging.getLogger("UnifiedAPIManager")
        self.logger.setLevel(logging.INFO)
        
        # Log initialization status
        self._log_provider_status()
    
    def _log_provider_status(self):
        """Log the status of all API providers."""
        self.logger.info(f"🔧 Unified API Manager initialized with preferred provider: {self.preferred_provider}")
        
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
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": "deepseek-chat",
                "messages": [
                    {
                        "role": "system",
                        "content": "Bạn là StillMe AI, một trợ lý AI thông minh và thân thiện. Hãy trả lời câu hỏi của người dùng một cách tự nhiên và hữu ích."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                "temperature": 0.7,
                "max_tokens": 500,
                "stream": False
            }
            
            self.logger.info(f"Calling DeepSeek API with prompt: {prompt[:50]}...")
            
            response = requests.post(url, headers=headers, json=payload, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            content = data["choices"][0]["message"]["content"]
            
            self.logger.info("DeepSeek API call successful")
            return content
            
        except requests.exceptions.HTTPError as e:
            error_msg = f"DeepSeek HTTP error: {e.response.status_code}"
            if hasattr(e, 'response') and e.response is not None:
                try:
                    error_details = e.response.json()
                    error_msg += f" - {error_details}"
                except:
                    error_msg += f" - {e.response.text}"
            
            self.logger.error(error_msg)
            return f"Error: DeepSeek API failed ({e.response.status_code})"
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"DeepSeek request error: {e}")
            return f"Error: Network issue with DeepSeek API"
            
        except Exception as e:
            self.logger.error(f"DeepSeek unexpected error: {e}")
            return f"Error: Unexpected error with DeepSeek API"
    
    def get_response(self, prompt: str, max_retries: int = 2) -> str:
        """
        Get AI response using unified provider routing.
        
        Args:
            prompt: Input prompt
            max_retries: Maximum retry attempts
            
        Returns:
            AI response or error message
        """
        optimized_prompt = TokenOptimizer.optimize(prompt) if 'TokenOptimizer' in globals() else prompt
        
        # Route to preferred provider with fallback
        if self.preferred_provider == "deepseek":
            return self.call_deepseek_api(optimized_prompt)
        elif self.preferred_provider == "openrouter":
            return self.call_openrouter_api(optimized_prompt)
        elif self.preferred_provider == "openai":
            return self.call_openai_api(optimized_prompt)
        elif self.preferred_provider == "ollama":
            try:
                return self.call_ollama_api(optimized_prompt)
            except Exception as e:
                self.logger.warning(f"Ollama API failed, falling back to DeepSeek: {e}")
                return self.call_deepseek_api(optimized_prompt)
        else:
            # Fallback to DeepSeek if unknown provider
            self.logger.warning(f"Unknown provider: {self.preferred_provider}, falling back to DeepSeek")
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
    
    def call_ollama_api(self, prompt: str) -> str:
        """Call Ollama API using modern /api/chat endpoint."""
        try:
            # Use modern /api/chat endpoint with proper payload (matching working diagnostic)
            payload = {
                "model": "gemma2:2b",  # Default model
                "messages": [
                    {"role": "user", "content": prompt}
                ],
                "stream": False
            }
            
            self.logger.info(f"Ollama: Calling model gemma2:2b with prompt: {prompt[:50]}...")
            
            response = requests.post(
                "http://localhost:11434/api/chat",
                json=payload,
                timeout=60
            )
            
            response.raise_for_status()
            data = response.json()
            
            self.logger.info("Ollama: Received response from gemma2:2b")
            return data.get("message", {}).get("content", "No response from Ollama")
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Ollama request error: {e}")
            if hasattr(e, 'response') and e.response is not None:
                self.logger.error(f"Ollama error details: {e.response.text}")
            return f"Error: Failed to connect to Ollama API"
        except Exception as e:
            self.logger.error(f"Ollama error: {e}")
            return f"Error: Unexpected error with Ollama API"
    
    def get_status(self) -> Dict[str, Any]:
        """Get API manager status."""
        return {
            "preferred_provider": self.preferred_provider,
            "deepseek_available": bool(self.deepseek_api_key),
            "openrouter_available": bool(self.openrouter_api_key),
            "openai_available": bool(self.openai_client),
            "model_preferences": self.model_preferences,
            "fallback_model": self.fallback_model
        }
    
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