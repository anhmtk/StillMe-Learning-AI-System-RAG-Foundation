"""
DeepSeek API Client for StillMe V2
Handles all AI interactions with rate limiting and error handling
"""

import logging
import time
from dataclasses import dataclass
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class ChatMessage:
    """Chat message"""

    role: str
    content: str


@dataclass
class ChatResponse:
    """Chat response from DeepSeek"""

    content: str
    model: str
    tokens_used: int
    finish_reason: str


class RateLimiter:
    """Simple rate limiter"""

    def __init__(self, max_requests_per_minute: int = 60):
        self.max_requests = max_requests_per_minute
        self.requests_window: list[float] = []

    def wait_if_needed(self):
        """Wait if rate limit would be exceeded"""
        now = time.time()
        
        self.requests_window = [
            req_time for req_time in self.requests_window if now - req_time < 60
        ]

        if len(self.requests_window) >= self.max_requests:
            oldest_request = self.requests_window[0]
            wait_time = 60 - (now - oldest_request)
            
            if wait_time > 0:
                logger.info(f"⏳ Rate limit reached, waiting {wait_time:.1f}s...")
                time.sleep(wait_time)

        self.requests_window.append(now)


class DeepSeekClient:
    """
    DeepSeek API Client
    Manages AI requests with rate limiting and error handling
    """

    def __init__(self, api_key: str, model: str = "deepseek-chat"):
        self.api_key = api_key
        self.model = model
        self.rate_limiter = RateLimiter(max_requests_per_minute=60)
        self.total_tokens_used = 0
        self.total_requests = 0
        logger.info(f"✅ DeepSeek client initialized (model: {model})")

    def chat(
        self,
        messages: list[ChatMessage],
        temperature: float = 0.7,
        max_tokens: int = 1000,
    ) -> ChatResponse:
        """
        Send chat request to DeepSeek API

        Args:
            messages: List of chat messages
            temperature: Sampling temperature (0.0 to 2.0)
            max_tokens: Maximum tokens in response

        Returns:
            ChatResponse with AI response
        """
        self.rate_limiter.wait_if_needed()

        try:
            import openai

            openai.api_key = self.api_key
            openai.api_base = "https://api.deepseek.com/v1"

            messages_dict = [{"role": msg.role, "content": msg.content} for msg in messages]

            logger.debug(f"🤖 Sending request to DeepSeek ({len(messages)} messages)")

            response = openai.ChatCompletion.create(
                model=self.model,
                messages=messages_dict,
                temperature=temperature,
                max_tokens=max_tokens,
            )

            content = response.choices[0].message.content
            tokens_used = response.usage.total_tokens
            finish_reason = response.choices[0].finish_reason

            self.total_tokens_used += tokens_used
            self.total_requests += 1

            logger.debug(f"✅ Response received ({tokens_used} tokens)")

            return ChatResponse(
                content=content,
                model=self.model,
                tokens_used=tokens_used,
                finish_reason=finish_reason,
            )

        except ImportError:
            logger.error("❌ openai package not installed. Install: pip install openai")
            raise
        except Exception as e:
            logger.error(f"❌ DeepSeek API error: {e}")
            raise

    def analyze_content(self, content: str, analysis_type: str = "quality") -> dict[str, Any]:
        """
        Analyze content using DeepSeek

        Args:
            content: Content to analyze
            analysis_type: Type of analysis (quality, relevance, safety)

        Returns:
            Analysis results
        """
        prompts = {
            "quality": f"""Analyze the quality of this content. Rate it 0.0-1.0 on:
- Accuracy
- Clarity
- Usefulness
- Completeness

Content: {content[:1000]}

Response format (JSON):
{{"quality_score": 0.0-1.0, "reasons": ["reason1", "reason2"]}}""",
            "relevance": f"""Rate how relevant this content is for AI/ML learning (0.0-1.0).

Content: {content[:1000]}

Response format (JSON):
{{"relevance_score": 0.0-1.0, "topics": ["topic1", "topic2"]}}""",
            "safety": f"""Check if this content is safe for AI learning (no misinformation, hate speech, harmful content).

Content: {content[:1000]}

Response format (JSON):
{{"is_safe": true/false, "concerns": ["concern1"] or []}}""",
        }

        prompt = prompts.get(analysis_type, prompts["quality"])

        try:
            messages = [
                ChatMessage(role="system", content="You are a content analyst. Always respond with valid JSON."),
                ChatMessage(role="user", content=prompt),
            ]

            response = self.chat(messages, temperature=0.3, max_tokens=500)

            import json
            result = json.loads(response.content)
            return result

        except Exception as e:
            logger.error(f"❌ Content analysis failed: {e}")
            return {"error": str(e)}

    def generate_summary(self, content: str, max_length: int = 200) -> str:
        """Generate a summary of content"""
        try:
            messages = [
                ChatMessage(
                    role="system",
                    content="You are a helpful assistant that creates concise summaries.",
                ),
                ChatMessage(
                    role="user",
                    content=f"Summarize this in {max_length} words or less:\n\n{content}",
                ),
            ]

            response = self.chat(messages, temperature=0.5, max_tokens=max_length * 2)
            return response.content

        except Exception as e:
            logger.error(f"❌ Summary generation failed: {e}")
            return content[:max_length] + "..."

    def get_stats(self) -> dict[str, Any]:
        """Get client usage statistics"""
        return {
            "model": self.model,
            "total_requests": self.total_requests,
            "total_tokens_used": self.total_tokens_used,
            "estimated_cost_usd": self.total_tokens_used / 1_000_000,
        }

