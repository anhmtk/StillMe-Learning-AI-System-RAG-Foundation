"""
OpenAI provider implementation for StillMe AI Framework.
"""

import asyncio
import logging

import httpx

from .llm_base import LLMProviderBase, LLMRequest, LLMResponse, ProviderConfig

logger = logging.getLogger(__name__)


class OpenAIProvider(LLMProviderBase):
    """OpenAI API provider implementation."""

    def __init__(self, config: ProviderConfig):
        super().__init__(config)
        self._client: httpx.AsyncClient | None = None

    async def initialize(self) -> bool:
        """Initialize the OpenAI client."""
        try:
            self._client = httpx.AsyncClient(
                base_url=self.config.base_url,
                headers={
                    "Authorization": f"Bearer {self.config.api_key}",
                    "Content-Type": "application/json",
                },
                timeout=self.config.timeout,
            )

            # Test the connection
            await self.health_check()
            return True
        except Exception as e:
            logger.error(f"Failed to initialize OpenAI provider: {e}")
            return False

    async def generate(self, request: LLMRequest) -> LLMResponse:
        """Generate a response using OpenAI API."""
        if not self._client:
            raise RuntimeError("OpenAI provider not initialized")

        # Prepare the request payload
        payload = {
            "model": self.config.model,
            "messages": [{"role": "user", "content": request.prompt}],
            "temperature": request.temperature,
            "top_p": request.top_p,
            "frequency_penalty": request.frequency_penalty,
            "presence_penalty": request.presence_penalty,
        }

        if request.max_tokens:
            payload["max_tokens"] = request.max_tokens

        if request.stop:
            payload["stop"] = request.stop

        if request.user:
            payload["user"] = request.user

        # Make the request with retries
        for attempt in range(self.config.max_retries):
            try:
                response = await self._client.post("/v1/chat/completions", json=payload)
                response.raise_for_status()

                data = response.json()

                # Extract the response
                choice = data["choices"][0]
                message = choice["message"]

                return LLMResponse(
                    content=message["content"],
                    model=data["model"],
                    provider=self.config.name,
                    usage=data.get("usage", {}),
                    finish_reason=choice.get("finish_reason", "stop"),
                    response_time=0.0,  # Will be updated by the manager
                    metadata={
                        "openai_response_id": data.get("id"),
                        "openai_created": data.get("created"),
                        "openai_system_fingerprint": data.get("system_fingerprint"),
                    },
                )

            except httpx.HTTPStatusError as e:
                if e.response.status_code == 429:  # Rate limit
                    if attempt < self.config.max_retries - 1:
                        wait_time = 2**attempt  # Exponential backoff
                        logger.warning(
                            f"Rate limited, waiting {wait_time}s before retry {attempt + 1}"
                        )
                        await asyncio.sleep(wait_time)
                        continue
                raise e
            except Exception as e:
                if attempt < self.config.max_retries - 1:
                    wait_time = 2**attempt
                    logger.warning(f"Request failed, retrying in {wait_time}s: {e}")
                    await asyncio.sleep(wait_time)
                    continue
                raise e

        raise Exception(
            f"Failed to generate response after {self.config.max_retries} attempts"
        )

    async def health_check(self) -> bool:
        """Check if the OpenAI API is healthy."""
        if not self._client:
            return False

        try:
            # Simple health check using models endpoint
            response = await self._client.get("/v1/models")
            return response.status_code == 200
        except Exception as e:
            logger.warning(f"OpenAI health check failed: {e}")
            return False

    async def cleanup(self):
        """Cleanup the OpenAI client."""
        await super().cleanup()
        if self._client:
            await self._client.aclose()
            self._client = None