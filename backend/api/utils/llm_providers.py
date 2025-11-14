"""
LLM Provider Abstraction Layer for StillMe
Supports multiple LLM providers: DeepSeek, OpenAI, Claude, Gemini, Ollama, Custom
"""

import os
import logging
import httpx
from typing import Optional, Dict, Any
from backend.api.utils.chat_helpers import build_system_prompt_with_language

logger = logging.getLogger(__name__)


class LLMProvider:
    """Base class for LLM providers"""
    
    def __init__(self, api_key: str, model_name: Optional[str] = None, api_url: Optional[str] = None):
        self.api_key = api_key
        self.model_name = model_name
        self.api_url = api_url
    
    async def generate(self, prompt: str, detected_lang: str = 'en') -> str:
        """Generate response - must be implemented by subclasses"""
        raise NotImplementedError


class DeepSeekProvider(LLMProvider):
    """DeepSeek API provider"""
    
    async def generate(self, prompt: str, detected_lang: str = 'en') -> str:
        """Call DeepSeek API"""
        try:
            system_content = build_system_prompt_with_language(detected_lang)
            model = self.model_name or "deepseek-chat"
            
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    "https://api.deepseek.com/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": model,
                        "messages": [
                            {"role": "system", "content": system_content},
                            {"role": "user", "content": prompt}
                        ],
                        "max_tokens": 1500,
                        "temperature": 0.7,
                        "stream": False
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    if "choices" in data and len(data["choices"]) > 0:
                        return data["choices"][0]["message"]["content"]
                    else:
                        return "DeepSeek API returned unexpected response format"
                else:
                    return f"DeepSeek API error: {response.status_code} - {response.text}"
                    
        except Exception as e:
            logger.error(f"DeepSeek API error: {e}")
            return f"DeepSeek API error: {str(e)}"


class OpenAIProvider(LLMProvider):
    """OpenAI API provider"""
    
    async def generate(self, prompt: str, detected_lang: str = 'en') -> str:
        """Call OpenAI API"""
        try:
            system_content = build_system_prompt_with_language(detected_lang)
            model = self.model_name or "gpt-3.5-turbo"
            
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    "https://api.openai.com/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": model,
                        "messages": [
                            {"role": "system", "content": system_content},
                            {"role": "user", "content": prompt}
                        ],
                        "max_tokens": 1500,
                        "temperature": 0.7,
                        "stream": False
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    if "choices" in data and len(data["choices"]) > 0:
                        return data["choices"][0]["message"]["content"]
                    else:
                        return "OpenAI API returned unexpected response format"
                else:
                    return f"OpenAI API error: {response.status_code} - {response.text}"
                    
        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
            return f"OpenAI API error: {str(e)}"


class ClaudeProvider(LLMProvider):
    """Anthropic Claude API provider"""
    
    async def generate(self, prompt: str, detected_lang: str = 'en') -> str:
        """Call Claude API"""
        try:
            system_content = build_system_prompt_with_language(detected_lang)
            model = self.model_name or "claude-3-sonnet-20240229"
            
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    "https://api.anthropic.com/v1/messages",
                    headers={
                        "x-api-key": self.api_key,
                        "anthropic-version": "2023-06-01",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": model,
                        "max_tokens": 1500,
                        "system": system_content,
                        "messages": [
                            {"role": "user", "content": prompt}
                        ]
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    if "content" in data and len(data["content"]) > 0:
                        # Claude returns content as array of text blocks
                        return data["content"][0]["text"]
                    else:
                        return "Claude API returned unexpected response format"
                else:
                    return f"Claude API error: {response.status_code} - {response.text}"
                    
        except Exception as e:
            logger.error(f"Claude API error: {e}")
            return f"Claude API error: {str(e)}"


class GeminiProvider(LLMProvider):
    """Google Gemini API provider"""
    
    async def generate(self, prompt: str, detected_lang: str = 'en') -> str:
        """Call Gemini API"""
        try:
            system_content = build_system_prompt_with_language(detected_lang)
            model = self.model_name or "gemini-pro"
            
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={self.api_key}",
                    headers={"Content-Type": "application/json"},
                    json={
                        "contents": [{
                            "parts": [{"text": f"{system_content}\n\n{prompt}"}]
                        }]
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    if "candidates" in data and len(data["candidates"]) > 0:
                        if "content" in data["candidates"][0] and "parts" in data["candidates"][0]["content"]:
                            return data["candidates"][0]["content"]["parts"][0]["text"]
                    return "Gemini API returned unexpected response format"
                else:
                    return f"Gemini API error: {response.status_code} - {response.text}"
                    
        except Exception as e:
            logger.error(f"Gemini API error: {e}")
            return f"Gemini API error: {str(e)}"


class OllamaProvider(LLMProvider):
    """Ollama local provider"""
    
    async def generate(self, prompt: str, detected_lang: str = 'en') -> str:
        """Call Ollama API (local)"""
        try:
            system_content = build_system_prompt_with_language(detected_lang)
            model = self.model_name or "llama2"
            api_url = self.api_url or "http://localhost:11434"
            
            async with httpx.AsyncClient(timeout=120.0) as client:  # Longer timeout for local
                response = await client.post(
                    f"{api_url}/api/generate",
                    json={
                        "model": model,
                        "prompt": f"{system_content}\n\n{prompt}",
                        "stream": False
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    if "response" in data:
                        return data["response"]
                    else:
                        return "Ollama API returned unexpected response format"
                else:
                    return f"Ollama API error: {response.status_code} - {response.text}"
                    
        except Exception as e:
            logger.error(f"Ollama API error: {e}")
            return f"Ollama API error: {str(e)}"


class CustomProvider(LLMProvider):
    """Custom/Generic OpenAI-compatible API provider"""
    
    async def generate(self, prompt: str, detected_lang: str = 'en') -> str:
        """Call custom OpenAI-compatible API"""
        try:
            system_content = build_system_prompt_with_language(detected_lang)
            api_url = self.api_url or "http://localhost:8000/v1/chat/completions"
            model = self.model_name or "custom-model"
            
            headers = {"Content-Type": "application/json"}
            if self.api_key:
                headers["Authorization"] = f"Bearer {self.api_key}"
            
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    api_url,
                    headers=headers,
                    json={
                        "model": model,
                        "messages": [
                            {"role": "system", "content": system_content},
                            {"role": "user", "content": prompt}
                        ],
                        "max_tokens": 1500,
                        "temperature": 0.7,
                        "stream": False
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    if "choices" in data and len(data["choices"]) > 0:
                        return data["choices"][0]["message"]["content"]
                    else:
                        return "Custom API returned unexpected response format"
                else:
                    return f"Custom API error: {response.status_code} - {response.text}"
                    
        except Exception as e:
            logger.error(f"Custom API error: {e}")
            return f"Custom API error: {str(e)}"


def create_llm_provider(
    provider: str,
    api_key: str,
    model_name: Optional[str] = None,
    api_url: Optional[str] = None
) -> LLMProvider:
    """
    Factory function to create LLM provider instance
    
    Args:
        provider: Provider name ('deepseek', 'openai', 'claude', 'gemini', 'ollama', 'custom')
        api_key: API key for the provider
        model_name: Optional model name (e.g., 'gpt-4', 'claude-3-opus')
        api_url: Optional custom API URL (for Ollama or custom providers)
        
    Returns:
        LLMProvider instance
    """
    provider_map = {
        'deepseek': DeepSeekProvider,
        'openai': OpenAIProvider,
        'claude': ClaudeProvider,
        'gemini': GeminiProvider,
        'ollama': OllamaProvider,
        'custom': CustomProvider,
    }
    
    provider_class = provider_map.get(provider.lower())
    if not provider_class:
        raise ValueError(f"Unknown provider: {provider}. Supported: {', '.join(provider_map.keys())}")
    
    return provider_class(api_key=api_key, model_name=model_name, api_url=api_url)

