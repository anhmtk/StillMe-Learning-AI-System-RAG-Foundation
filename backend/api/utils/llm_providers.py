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

# Import unified PHILOSOPHY_LITE_SYSTEM_PROMPT from identity module
# CRITICAL: This is now the SINGLE SOURCE OF TRUTH - do not define here
from backend.identity.philosophy_lite import PHILOSOPHY_LITE_SYSTEM_PROMPT

# Legacy prompt definition removed - now imported from backend.identity.philosophy_lite
# This ensures single source of truth and prevents drift between files


def smart_truncate_prompt_for_philosophy(prompt_text: str, max_tokens: int) -> str:
    """
    Smart truncation that preserves philosophical instructions and removes provenance/metrics first.
    
    For philosophical questions, this function:
    1. Preserves the entire philosophical instructions block
    2. Removes provenance/metrics sections first
    3. Truncates from the end if still too long
    
    Args:
        prompt_text: The prompt text to truncate
        max_tokens: Maximum tokens allowed
        
    Returns:
        Truncated prompt with philosophical instructions preserved
    """
    def estimate_tokens(text: str) -> int:
        return len(text) // 4 if text else 0
    
    def truncate_text(text: str, max_tokens: int) -> str:
        if not text:
            return text
        estimated = estimate_tokens(text)
        if estimated <= max_tokens:
            return text
        max_chars = max_tokens * 4
        if len(text) <= max_chars:
            return text
        truncated = text[:max_chars].rsplit('\n', 1)[0]
        return truncated + "\n\n[Note: Content truncated to fit context limits.]"
    
    # Detect if prompt contains philosophical instructions
    philo_markers = [
        "PHILOSOPHICAL FRAMING INSTRUCTION",
        "PHILOSOPHICAL QUESTION DETECTED",
        "MANDATORY OUTPUT RULES",
        "MANDATORY: MINIMUM 2 CONTRASTING POSITIONS"
    ]
    
    has_philosophical = any(marker in prompt_text for marker in philo_markers)
    
    if not has_philosophical:
        # Normal truncation for non-philosophical prompts
        return truncate_text(prompt_text, max_tokens)
    
    # Find philosophical instructions block
    philo_start = -1
    philo_end = -1
    for marker in philo_markers:
        marker_pos = prompt_text.find(marker)
        if marker_pos >= 0:
            philo_start = marker_pos
            # Find end of philosophical block (before "Context:" or "User Question")
            end_markers = ["Context:", "User Question", "CRITICAL: USER QUESTION"]
            for end_marker in end_markers:
                end_pos = prompt_text.find(end_marker, philo_start)
                if end_pos > philo_start:
                    philo_end = end_pos
                    break
            if philo_end == -1:
                philo_end = len(prompt_text)
            break
    
    if philo_start >= 0 and philo_end > philo_start:
        # Extract philosophical instructions
        philo_block = prompt_text[philo_start:philo_end]
        
        # Remove provenance/metrics sections before philosophical block
        before_philo = prompt_text[:philo_start]
        # Remove sections that contain provenance/metrics keywords
        provenance_keywords = ["PROVENANCE", "provenance", "learning metrics", "Learning Metrics", 
                              "learning sources", "Learning Sources", "Learning Metrics Instruction",
                              "Learning Sources Instruction"]
        lines_before = before_philo.split('\n')
        filtered_lines = []
        skip_section = False
        for i, line in enumerate(lines_before):
            # Check if line starts a provenance/metrics section
            if any(keyword in line for keyword in provenance_keywords):
                skip_section = True
                continue
            # Check if line starts a new major section (## or **) - end of provenance/metrics section
            if (line.strip().startswith('##') or 
                (line.strip().startswith('**') and line.strip().endswith('**')) or
                line.strip().startswith('🧠') or  # Philosophical section starts
                line.strip().startswith('⚠️⚠️⚠️')):  # Warning section
                skip_section = False
            if not skip_section:
                filtered_lines.append(line)
        before_philo_cleaned = '\n'.join(filtered_lines)
        
        # After philosophical block
        after_philo = prompt_text[philo_end:]
        
        # Reconstruct: cleaned before + philosophical block + after
        reconstructed = before_philo_cleaned + philo_block + after_philo
        
        # Now truncate if still too long, but preserve philosophical block
        estimated = estimate_tokens(reconstructed)
        if estimated <= max_tokens:
            return reconstructed
        
        # Truncate from end (after philosophical block) first
        max_chars = max_tokens * 4
        philo_block_size = len(philo_block)
        before_size = len(before_philo_cleaned)
        available_for_after = max_chars - philo_block_size - before_size
        
        if available_for_after > 0:
            truncated_after = after_philo[:available_for_after].rsplit('\n', 1)[0]
            return before_philo_cleaned + philo_block + truncated_after
        else:
            # Even philosophical block is too large, but preserve it anyway (truncate from end of block)
            truncated_philo = philo_block[:max_chars - before_size].rsplit('\n', 1)[0]
            return before_philo_cleaned + truncated_philo
    
    # Fallback: normal truncation if philosophical block not found
    return truncate_text(prompt_text, max_tokens)


class InsufficientQuotaError(Exception):
    """Raised when OpenAI credit/quota is exhausted"""
    pass


class AuthenticationError(Exception):
    """Raised when API key is invalid"""
    pass


class AuthorizationError(Exception):
    """Raised when API access is forbidden"""
    pass


class ContextOverflowError(Exception):
    """Raised when prompt exceeds maximum context length"""
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
    """DeepSeek API provider with intelligent model routing"""
    
    async def generate_stream(
        self, 
        prompt: str, 
        detected_lang: str = 'en',
        question: Optional[str] = None,
        task_type: str = "chat",
        is_philosophical: Optional[bool] = None
    ) -> AsyncIterator[str]:
        """Generate streaming response from DeepSeek API with model routing"""
        try:
            system_content = build_system_prompt_with_language(detected_lang)
            
            # Use model router to select optimal model
            from backend.core.model_router import get_model_router
            router = get_model_router()
            model = router.select_model(
                question=question or prompt[:500],  # Use question if provided, else extract from prompt
                task_type=task_type,
                is_philosophical=is_philosophical
            )
            
            # Override with explicit model_name if set (for backward compatibility)
            if self.model_name:
                model = self.model_name
                logger.debug(f"Using explicit model_name: {model} (overriding router)")
            else:
                logger.info(f"🤖 Model router selected: {model} for task_type={task_type}, is_philosophical={is_philosophical}")
            
            # Adjust max_tokens based on model (reasoner supports up to 64K)
            max_tokens = 1500 if model == "deepseek-chat" else 8000
            
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
                        "max_tokens": max_tokens,
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
    
    async def generate(
        self, 
        prompt: str, 
        detected_lang: str = 'en',
        question: Optional[str] = None,
        task_type: str = "chat",
        is_philosophical: Optional[bool] = None
    ) -> str:
        """Call DeepSeek API with intelligent model routing"""
        try:
            system_content = build_system_prompt_with_language(detected_lang)
            
            # Use model router to select optimal model
            from backend.core.model_router import get_model_router
            router = get_model_router()
            model = router.select_model(
                question=question or prompt[:500],  # Use question if provided, else extract from prompt
                task_type=task_type,
                is_philosophical=is_philosophical
            )
            
            # Override with explicit model_name if set (for backward compatibility)
            if self.model_name:
                model = self.model_name
                logger.debug(f"Using explicit model_name: {model} (overriding router)")
            else:
                logger.info(f"🤖 Model router selected: {model} for task_type={task_type}, is_philosophical={is_philosophical}")
            
            # Adjust max_tokens based on model and question type
            max_tokens = 1500  # Default for chat
            
            # Detect codebase/technical questions that need longer responses
            is_codebase_question = question and any(
                keyword in question.lower() 
                for keyword in ["codebase", "code", "file", "function", "class", "implementation", "architecture", "how does", "how is"]
            ) if question else False
            
            if model == "deepseek-reasoner":
                # Reasoner supports up to 64K output, but we'll use 8K for now to balance latency
                # Can increase later if needed for very long philosophical responses
                max_tokens = 8000
                logger.debug(f"Using reasoner model - max_tokens set to {max_tokens}")
            elif is_codebase_question:
                # Codebase questions often need longer responses with code snippets and detailed explanations
                max_tokens = 4000  # Increased from 1500 to 4000 for codebase questions
                logger.debug(f"Codebase question detected - max_tokens set to {max_tokens}")
            
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
                        "max_tokens": max_tokens,
                        "temperature": 0.7,
                        "stream": False
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    if "choices" in data and len(data["choices"]) > 0:
                        content = data["choices"][0]["message"].get("content")
                        # CRITICAL: Ensure content is never None or empty
                        if not content or not content.strip():
                            logger.warning("DeepSeek API returned empty or None content")
                            return "DeepSeek API returned empty response"
                        
                        # Track cost if usage information available
                        if "usage" in data:
                            usage = data["usage"]
                            input_tokens = usage.get("prompt_tokens", 0)
                            output_tokens = usage.get("completion_tokens", 0)
                            
                            # Track cost (optional - only if cost monitor is available)
                            try:
                                from backend.services.cost_monitor import get_cost_monitor
                                cost_monitor = get_cost_monitor()
                                tracking_info = cost_monitor.track_usage(
                                    question=question or prompt[:500],
                                    input_tokens=input_tokens,
                                    output_tokens=output_tokens,
                                    model=model
                                )
                                logger.debug(f"💰 Cost tracked: ${tracking_info['cost']:.4f} (philosophical={tracking_info['is_philosophical']})")
                            except Exception as e:
                                logger.debug(f"Cost tracking not available: {e}")
                        
                        return content
                    else:
                        return "DeepSeek API returned unexpected response format"
                else:
                    return f"DeepSeek API error: {response.status_code} - {response.text}"
                    
        except Exception as e:
            # CRITICAL: Log full exception details for debugging
            import traceback
            error_details = traceback.format_exc()
            logger.error(f"DeepSeek API error: {e}\n{error_details}")
            
            # Return detailed error message
            error_msg = str(e) if str(e) else type(e).__name__
            if not error_msg or error_msg == "":
                error_msg = "Unknown error (no error message available)"
            return f"DeepSeek API error: {error_msg}"


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
            # CRITICAL: Detect philosophical non-RAG mode
            # If prompt is very short and only contains "User Question: ...", use philosophy-lite system prompt
            user_question_marker = "User Question"
            is_philosophy_lite_mode = False
            
            if user_question_marker in prompt:
                # Check if prompt is very short (only user question, no other instructions)
                prompt_stripped = prompt.strip()
                if prompt_stripped.startswith(user_question_marker) and len(prompt_stripped) < 5000:
                    # This is likely philosophy-lite mode from non-RAG path
                    is_philosophy_lite_mode = True
                    logger.info("📊 [PHILO-LITE] Detected philosophy-lite mode - using minimal system prompt")
            
            # Use philosophy-lite system prompt if detected, otherwise use full system prompt
            if is_philosophy_lite_mode:
                system_content = PHILOSOPHY_LITE_SYSTEM_PROMPT
            else:
                system_content = build_system_prompt_with_language(detected_lang)
            
            # OpenRouter uses model names like "openai/gpt-4", "anthropic/claude-3-opus", etc.
            # Default to a cost-effective model
            model = self.model_name or "openai/gpt-3.5-turbo"
            
            # CRITICAL: Truncate system_content and prompt to prevent context overflow
            # BUT preserve user question - it's the most important part
            def estimate_tokens(text: str) -> int:
                return len(text) // 4 if text else 0
            
            def truncate_text(text: str, max_tokens: int) -> str:
                if not text:
                    return text
                estimated = estimate_tokens(text)
                if estimated <= max_tokens:
                    return text
                max_chars = max_tokens * 4
                if len(text) <= max_chars:
                    return text
                truncated = text[:max_chars].rsplit('\n', 1)[0]
                return truncated + "\n\n[Note: Content truncated to fit context limits.]"
            
            # CRITICAL: Extract and preserve user question before truncating
            # User question is usually at the end after "User Question:" marker
            user_question = ""
            prompt_without_question = prompt
            
            if user_question_marker in prompt:
                question_start = prompt.find(user_question_marker)
                if question_start != -1:
                    question_section = prompt[question_start:]
                    colon_pos = question_section.find(":")
                    if colon_pos != -1:
                        user_question = question_section[colon_pos + 1:].strip()
                        prompt_without_question = prompt[:question_start].strip()
            
            # For philosophy-lite mode: prompt is just user question, no truncation needed
            if is_philosophy_lite_mode:
                # In lite mode, prompt is already just "User Question: ...", use it directly
                prompt = prompt.strip()
                # Ensure user_question is extracted for logging
                if not user_question and user_question_marker in prompt:
                    colon_pos = prompt.find(":")
                    if colon_pos != -1:
                        user_question = prompt[colon_pos + 1:].strip()
            else:
                # Only truncate system_content if not in lite mode
                # Truncate system_content to ~3500 tokens (reduced from 4000 to prevent overflow)
                system_content = truncate_text(system_content, max_tokens=3500)
                
                # Fix: Smart truncate for philosophical questions - preserve philosophical instructions, remove provenance/metrics first
                prompt_without_question = smart_truncate_prompt_for_philosophy(prompt_without_question, max_tokens=6000)
                
                # Preserve user question (up to 2500 tokens, reduced from 3000) - CRITICAL for correct answers
                if user_question:
                    user_question = truncate_text(user_question, max_tokens=2500)
                    prompt = prompt_without_question + "\n\n" + user_question_marker + ": " + user_question
                else:
                    # Fallback: truncate entire prompt if we couldn't extract user question
                    prompt = smart_truncate_prompt_for_philosophy(prompt, max_tokens=7000)
            
            # Log token counts for debugging
            system_tokens = estimate_tokens(system_content)
            prompt_tokens = estimate_tokens(prompt)
            user_q_tokens = estimate_tokens(user_question) if user_question else 0
            total_tokens = system_tokens + prompt_tokens
            log_prefix = "📊 [PHILO-LITE]" if is_philosophy_lite_mode else "📊"
            logger.info(f"{log_prefix} Token counts - System: {system_tokens}, Prompt: {prompt_tokens}, User Question: {user_q_tokens}, Total: {total_tokens}")
            
            if total_tokens > 15000:
                logger.warning(f"⚠️ Total tokens ({total_tokens}) still high, may cause context overflow")
            
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
                        content = data["choices"][0]["message"].get("content")
                        # CRITICAL: Ensure content is never None or empty
                        if not content or not content.strip():
                            logger.warning("OpenRouter API returned empty or None content")
                            return "OpenRouter API returned empty response"
                        # CRITICAL: Log successful response to trace
                        logger.info(f"🔍 [TRACE] OpenRouter returned content: length={len(content)}, preview={content[:200]}")
                        return content
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
                        elif response.status_code == 400 and (
                            "context length" in error_message.lower() or 
                            "maximum context" in error_message.lower() or
                            "context length is" in error_message.lower() or
                            "requested about" in error_message.lower() and "tokens" in error_message.lower()
                        ):
                            raise ContextOverflowError(f"OpenRouter context overflow: {error_message}")
                        else:
                            # Raise exception instead of returning error string to prevent it from passing through validators
                            raise Exception(f"OpenRouter API error: {response.status_code} - {error_message}")
                    except (ValueError, KeyError):
                        # If JSON parsing fails, check for specific errors
                        if response.status_code == 429 or "quota" in error_text.lower() or "billing" in error_text.lower() or "credit" in error_text.lower():
                            raise InsufficientQuotaError(f"OpenRouter credit exhausted: {error_text}")
                        elif response.status_code == 400 and (
                            "context length" in error_text.lower() or 
                            "maximum context" in error_text.lower() or
                            "context length is" in error_text.lower() or
                            "requested about" in error_text.lower() and "tokens" in error_text.lower()
                        ):
                            raise ContextOverflowError(f"OpenRouter context overflow: {error_text}")
                        # Raise exception instead of returning error string
                        raise Exception(f"OpenRouter API error: {response.status_code} - {error_text}")
                    
        except (InsufficientQuotaError, ContextOverflowError, AuthenticationError, AuthorizationError):
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
            
            # CRITICAL: Truncate system_content and prompt to prevent context overflow
            # BUT preserve user question - it's the most important part
            def estimate_tokens(text: str) -> int:
                return len(text) // 4 if text else 0
            
            def truncate_text(text: str, max_tokens: int) -> str:
                if not text:
                    return text
                estimated = estimate_tokens(text)
                if estimated <= max_tokens:
                    return text
                max_chars = max_tokens * 4
                if len(text) <= max_chars:
                    return text
                truncated = text[:max_chars].rsplit('\n', 1)[0]
                return truncated + "\n\n[Note: Content truncated to fit context limits.]"
            
            # CRITICAL: Extract and preserve user question before truncating
            # User question is usually at the end after "User Question:" marker
            user_question_marker = "User Question"
            user_question = ""
            prompt_without_question = prompt
            
            if user_question_marker in prompt:
                question_start = prompt.find(user_question_marker)
                if question_start != -1:
                    question_section = prompt[question_start:]
                    colon_pos = question_section.find(":")
                    if colon_pos != -1:
                        user_question = question_section[colon_pos + 1:].strip()
                        prompt_without_question = prompt[:question_start].strip()
            
            # Truncate system_content to ~3500 tokens (reduced from 4000 to prevent overflow)
            system_content = truncate_text(system_content, max_tokens=3500)
            
            # Fix: Smart truncate for philosophical questions - preserve philosophical instructions, remove provenance/metrics first
            prompt_without_question = smart_truncate_prompt_for_philosophy(prompt_without_question, max_tokens=6000)
            
            # Preserve user question (up to 2500 tokens, reduced from 3000) - CRITICAL for correct answers
            if user_question:
                user_question = truncate_text(user_question, max_tokens=2500)
                prompt = prompt_without_question + "\n\n" + user_question_marker + ": " + user_question
            else:
                # Fallback: truncate entire prompt if we couldn't extract user question
                prompt = smart_truncate_prompt_for_philosophy(prompt, max_tokens=7000)
            
            # Log token counts for debugging
            system_tokens = estimate_tokens(system_content)
            prompt_tokens = estimate_tokens(prompt)
            user_q_tokens = estimate_tokens(user_question) if user_question else 0
            total_tokens = system_tokens + prompt_tokens
            logger.info(f"📊 Token counts - System: {system_tokens}, Prompt: {prompt_tokens}, User Question: {user_q_tokens}, Total: {total_tokens}")
            
            if total_tokens > 15000:
                logger.warning(f"⚠️ Total tokens ({total_tokens}) still high, may cause context overflow")
            
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
                        content = data["choices"][0]["message"].get("content")
                        # CRITICAL: Ensure content is never None or empty
                        if not content or not content.strip():
                            logger.warning("OpenAI API returned empty or None content")
                            return "OpenAI API returned empty response"
                        return content
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
                        elif response.status_code == 400 and (
                            "context length" in error_message.lower() or 
                            "maximum context" in error_message.lower() or
                            "context length is" in error_message.lower() or
                            "requested about" in error_message.lower() and "tokens" in error_message.lower()
                        ):
                            raise ContextOverflowError(f"OpenAI context overflow: {error_message}")
                        else:
                            # Raise exception instead of returning error string to prevent it from passing through validators
                            raise Exception(f"OpenAI API error: {response.status_code} - {error_message}")
                    except (ValueError, KeyError):
                        # If JSON parsing fails, check for specific errors
                        if response.status_code == 429 or "quota" in error_text.lower() or "billing" in error_text.lower():
                            raise InsufficientQuotaError(f"OpenAI credit exhausted: {error_text}")
                        elif response.status_code == 400 and (
                            "context length" in error_text.lower() or 
                            "maximum context" in error_text.lower() or
                            "context length is" in error_text.lower() or
                            "requested about" in error_text.lower() and "tokens" in error_text.lower()
                        ):
                            raise ContextOverflowError(f"OpenAI context overflow: {error_text}")
                        # Raise exception instead of returning error string
                        raise Exception(f"OpenAI API error: {response.status_code} - {error_text}")
                    
        except (InsufficientQuotaError, ContextOverflowError, AuthenticationError, AuthorizationError):
            # Re-raise to be handled by caller (for fallback to other providers)
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
                        content = data["choices"][0]["message"].get("content")
                        # CRITICAL: Ensure content is never None or empty
                        if not content or not content.strip():
                            logger.warning("Custom API returned empty or None content")
                            return "Custom API returned empty response"
                        return content
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

