"""
Local LLM provider implementation for StillMe AI Framework.
Supports Ollama and other local LLM servers.
"""

import asyncio
import logging

import httpx

from .llm_base import LLMProviderBase, LLMRequest, LLMResponse, ProviderConfig

logger = logging.getLogger(__name__)


class LocalLLMProvider(LLMProviderBase):
    """Local LLM provider implementation (Ollama, etc.)."""

    def __init__(self, config: ProviderConfig):
        super().__init__(config)
        self._client: httpx.AsyncClient | None = None

    async def initialize(self) -> bool:
        """Initialize the local LLM client."""
        try:
            self._client = httpx.AsyncClient(
                base_url=self.config.base_url, timeout=self.config.timeout
            )

            # Test the connection
            await self.health_check()
            return True
        except Exception as e:
            logger.error(f"Failed to initialize local LLM provider: {e}")
            return False

    async def generate(self, request: LLMRequest) -> LLMResponse:
        """Generate a response using local LLM API."""
        if not self._client:
            raise RuntimeError("Local LLM provider not initialized")

        # Prepare the request payload (Ollama format)
        payload = {
            "model": self.config.model,
            "prompt": request.prompt,
            "stream": False,
            "options": {
                "temperature": request.temperature,
                "top_p": request.top_p,
                "frequency_penalty": request.frequency_penalty,
                "presence_penalty": request.presence_penalty,
            },
        }

        if request.max_tokens:
            payload["options"]["num_predict"] = request.max_tokens

        if request.stop:
            payload["options"]["stop"] = request.stop

        # Make the request with retries
        for attempt in range(self.config.max_retries):
            try:
                response = await self._client.post("/api/generate", json=payload)
                response.raise_for_status()

                data = response.json()

                return LLMResponse(
                    content=data["response"],
                    model=data["model"],
                    provider=self.config.name,
                    usage={
                        "prompt_tokens": data.get("prompt_eval_count", 0),
                        "completion_tokens": data.get("eval_count", 0),
                        "total_tokens": data.get("prompt_eval_count", 0)
                        + data.get("eval_count", 0),
                    },
                    finish_reason="stop",
                    response_time=data.get("total_duration", 0)
                    / 1_000_000_000,  # Convert nanoseconds to seconds
                    metadata={
                        "local_llm_response_id": data.get("created_at"),
                        "local_llm_load_duration": data.get("load_duration", 0),
                        "local_llm_prompt_eval_duration": data.get(
                            "prompt_eval_duration", 0
                        ),
                        "local_llm_eval_duration": data.get("eval_duration", 0),
                    },
                )

            except httpx.HTTPStatusError as e:
                if e.response.status_code == 429:  # Rate limit
                    if attempt < self.config.max_retries - 1:
                        wait_time = 2**attempt
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
        """Check if the local LLM server is healthy."""
        if not self._client:
            return False

        try:
            # Simple health check using models endpoint
            response = await self._client.get("/api/tags")
            return response.status_code == 200
        except Exception as e:
            logger.warning(f"Local LLM health check failed: {e}")
            return False

    async def cleanup(self):
        """Cleanup the local LLM client."""
        await super().cleanup()
        if self._client:
            await self._client.aclose()
            self._client = None