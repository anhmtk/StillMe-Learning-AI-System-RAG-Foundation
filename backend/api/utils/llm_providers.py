"""
LLM Provider Abstraction Layer for StillMe
Supports multiple LLM providers: DeepSeek, OpenAI, Claude, Gemini, Ollama, Custom
"""

import os
import logging
import httpx
import json
from typing import Optional, Dict, Any, AsyncIterator
from backend.api.utils.chat_helpers import build_system_prompt_with_language

logger = logging.getLogger(__name__)


class InsufficientQuotaError(Exception):
    """Raised when OpenAI credit/quota is exhausted"""
    pass


class AuthenticationError(Exception):
    """Raised when API key is invalid"""
    pass


class AuthorizationError(Exception):
    """Raised when API access is forbidden"""
    pass


class LLMProvider:
    """Base class for LLM providers"""
    
    def __init__(self, api_key: str, model_name: Optional[str] = None, api_url: Optional[str] = None):
        self.api_key = api_key
        self.model_name = model_name
        self.api_url = api_url
    
    async def generate(self, prompt: str, detected_lang: str = 'en') -> str:
        """Generate response - must be implemented by subclasses"""
        raise NotImplementedError
    
    async def generate_stream(self, prompt: str, detected_lang: str = 'en') -> AsyncIterator[str]:
        """
        Generate streaming response (token-by-token)
        
        OPTIMIZATION: Streaming reduces perceived latency by returning tokens as they're generated.
        Default implementation falls back to non-streaming generate().
        Subclasses can override for native streaming support.
        
        Args:
            prompt: User prompt
            detected_lang: Detected language code
            
        Yields:
            Token strings as they're generated
        """
        # Default: fallback to non-streaming, then yield full response
        # Subclasses should override for true streaming
        full_response = await self.generate(prompt, detected_lang)
        # Yield response in chunks for backward compatibility
        chunk_size = 10  # Small chunks to simulate streaming
        for i in range(0, len(full_response), chunk_size):
            yield full_response[i:i + chunk_size]


class DeepSeekProvider(LLMProvider):
    """DeepSeek API provider"""
    
    async def generate_stream(self, prompt: str, detected_lang: str = 'en') -> AsyncIterator[str]:
        """Generate streaming response from DeepSeek API"""
        try:
            system_content = build_system_prompt_with_language(detected_lang)
            model = self.model_name or "deepseek-chat"
            
            async with httpx.AsyncClient(timeout=60.0) as client:
                async with client.stream(
                    "POST",
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
                        "stream": True
                    }
                ) as response:
                    if response.status_code == 200:
                        async for line in response.aiter_lines():
                            if line.startswith("data: "):
                                data_str = line[6:]  # Remove "data: " prefix
                                if data_str.strip() == "[DONE]":
                                    break
                                try:
                                    data = json.loads(data_str)
                                    if "choices" in data and len(data["choices"]) > 0:
                                        delta = data["choices"][0].get("delta", {})
                                        content = delta.get("content", "")
                                        if content:
                                            yield content
                                except json.JSONDecodeError:
                                    continue
                    else:
                        error_text = await response.aread()
                        yield f"DeepSeek API error: {response.status_code} - {error_text.decode()}"
        except Exception as e:
            logger.error(f"DeepSeek streaming error: {e}")
            yield f"DeepSeek streaming error: {str(e)}"
    
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


class OpenRouterProvider(LLMProvider):
    """OpenRouter API provider - Multi-model API aggregator"""
    
    async def generate_stream(self, prompt: str, detected_lang: str = 'en') -> AsyncIterator[str]:
        """Generate streaming response from OpenRouter API"""
        try:
            system_content = build_system_prompt_with_language(detected_lang)
            model = self.model_name or "openai/gpt-3.5-turbo"
            
            async with httpx.AsyncClient(timeout=60.0) as client:
                async with client.stream(
                    "POST",
                    "https://openrouter.ai/api/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                        "HTTP-Referer": "https://github.com/anhmtk/StillMe-Learning-AI-System-RAG-Foundation",
                        "X-Title": "StillMe RAG System"
                    },
                    json={
                        "model": model,
                        "messages": [
                            {"role": "system", "content": system_content},
                            {"role": "user", "content": prompt}
                        ],
                        "max_tokens": 1500,
                        "temperature": 0.7,
                        "stream": True
                    }
                ) as response:
                    if response.status_code == 200:
                        async for line in response.aiter_lines():
                            if line.startswith("data: "):
                                data_str = line[6:]  # Remove "data: " prefix
                                if data_str.strip() == "[DONE]":
                                    break
                                try:
                                    data = json.loads(data_str)
                                    if "choices" in data and len(data["choices"]) > 0:
                                        delta = data["choices"][0].get("delta", {})
                                        content = delta.get("content", "")
                                        if content:
                                            yield content
                                except json.JSONDecodeError:
                                    continue
                    else:
                        error_text = await response.aread()
                        yield f"OpenRouter API error: {response.status_code} - {error_text.decode()}"
        except Exception as e:
            logger.error(f"OpenRouter streaming error: {e}")
            yield f"OpenRouter streaming error: {str(e)}"
    
    async def generate(self, prompt: str, detected_lang: str = 'en') -> str:
        """Call OpenRouter API"""
        try:
            system_content = build_system_prompt_with_language(detected_lang)
            # OpenRouter uses model names like "openai/gpt-4", "anthropic/claude-3-opus", etc.
            # Default to a cost-effective model
            model = self.model_name or "openai/gpt-3.5-turbo"
            
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    "https://openrouter.ai/api/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                        "HTTP-Referer": "https://github.com/anhmtk/StillMe-Learning-AI-System-RAG-Foundation",
                        "X-Title": "StillMe RAG System"
                    },
                    json={
                        "model": model,
                        "messages": [
                            {"role": "system", "content": system_content},
                            {"role": "user", "content": prompt}
                        ],
                        "max_tokens": 1500,
                        "temperature": 0.7
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    if "choices" in data and len(data["choices"]) > 0:
                        return data["choices"][0]["message"]["content"]
                    else:
                        return "OpenRouter API returned unexpected response format"
                else:
                    # Parse error response for better error handling
                    error_text = response.text
                    try:
                        error_data = response.json()
                        error_code = error_data.get("error", {}).get("code", "")
                        error_message = error_data.get("error", {}).get("message", error_text)
                        
                        # Fix: error_code might be int, convert to string
                        error_code_str = str(error_code).lower() if error_code else ""
                        
                        # Check for credit/quota exhaustion
                        if response.status_code == 429 or "insufficient_quota" in error_code_str or "billing" in error_message.lower() or "credit" in error_message.lower():
                            raise InsufficientQuotaError(f"OpenRouter credit exhausted: {error_message}")
                        elif response.status_code == 401:
                            raise AuthenticationError(f"OpenRouter API key invalid: {error_message}")
                        elif response.status_code == 403:
                            raise AuthorizationError(f"OpenRouter API access forbidden: {error_message}")
                        else:
                            return f"OpenRouter API error: {response.status_code} - {error_message}"
                    except (ValueError, KeyError):
                        # If JSON parsing fails, return raw error
                        if response.status_code == 429 or "quota" in error_text.lower() or "billing" in error_text.lower() or "credit" in error_text.lower():
                            raise InsufficientQuotaError(f"OpenRouter credit exhausted: {error_text}")
                        return f"OpenRouter API error: {response.status_code} - {error_text}"
                    
        except InsufficientQuotaError:
            # Re-raise to be handled by caller for fallback
            raise
        except Exception as e:
            logger.error(f"OpenRouter API error: {e}")
            # Return error string for non-quota errors (will be handled by fallback)
            raise Exception(f"OpenRouter API error: {str(e)}")


class OpenAIProvider(LLMProvider):
    """OpenAI API provider"""
    
    async def generate_stream(self, prompt: str, detected_lang: str = 'en') -> AsyncIterator[str]:
        """Generate streaming response from OpenAI API"""
        try:
            system_content = build_system_prompt_with_language(detected_lang)
            model = self.model_name or "gpt-3.5-turbo"
            
            async with httpx.AsyncClient(timeout=60.0) as client:
                async with client.stream(
                    "POST",
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
                        "stream": True
                    }
                ) as response:
                    if response.status_code == 200:
                        async for line in response.aiter_lines():
                            if line.startswith("data: "):
                                data_str = line[6:]  # Remove "data: " prefix
                                if data_str.strip() == "[DONE]":
                                    break
                                try:
                                    data = json.loads(data_str)
                                    if "choices" in data and len(data["choices"]) > 0:
                                        delta = data["choices"][0].get("delta", {})
                                        content = delta.get("content", "")
                                        if content:
                                            yield content
                                except json.JSONDecodeError:
                                    continue
                    else:
                        error_text = await response.aread()
                        yield f"OpenAI API error: {response.status_code} - {error_text.decode()}"
        except Exception as e:
            logger.error(f"OpenAI streaming error: {e}")
            yield f"OpenAI streaming error: {str(e)}"
    
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
                    # Parse error response for better error handling
                    error_text = response.text
                    try:
                        error_data = response.json()
                        error_code = error_data.get("error", {}).get("code", "")
                        error_message = error_data.get("error", {}).get("message", error_text)
                        
                        # Check for credit/quota exhaustion
                        if response.status_code == 429 or "insufficient_quota" in error_code.lower() or "billing" in error_message.lower():
                            raise InsufficientQuotaError(f"OpenAI credit exhausted: {error_message}")
                        elif response.status_code == 401:
                            raise AuthenticationError(f"OpenAI API key invalid: {error_message}")
                        elif response.status_code == 403:
                            raise AuthorizationError(f"OpenAI API access forbidden: {error_message}")
                        else:
                            return f"OpenAI API error: {response.status_code} - {error_message}"
                    except (ValueError, KeyError):
                        # If JSON parsing fails, return raw error
                        if response.status_code == 429 or "quota" in error_text.lower() or "billing" in error_text.lower():
                            raise InsufficientQuotaError(f"OpenAI credit exhausted: {error_text}")
                        return f"OpenAI API error: {response.status_code} - {error_text}"
                    
        except InsufficientQuotaError:
            # Re-raise to be handled by caller
            raise
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
        'openrouter': OpenRouterProvider,
        'claude': ClaudeProvider,
        'gemini': GeminiProvider,
        'ollama': OllamaProvider,
        'custom': CustomProvider,
    }
    
    provider_class = provider_map.get(provider.lower())
    if not provider_class:
        raise ValueError(f"Unknown provider: {provider}. Supported: {', '.join(provider_map.keys())}")
    
    return provider_class(api_key=api_key, model_name=model_name, api_url=api_url)

