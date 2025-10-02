#!/usr/bin/env python3
"""
StillMe AI - Optimized Ollama Client
===================================
High-performance Ollama client with timeout handling and fallback mechanisms.
"""

import json
import logging
import os
import threading
import time
from collections.abc import Generator
from typing import Any, Optional

import httpx
import requests

# Configuration
OLLAMA_HOST = os.getenv(
    "OLLAMA_HOST", "http://127.0.0.1:11434"
)  # Use 127.0.0.1 instead of localhost
OLLAMA_CONNECT_TIMEOUT = float(os.getenv("OLLAMA_CONNECT_TIMEOUT_SEC", "3"))
OLLAMA_READ_TIMEOUT = float(os.getenv("OLLAMA_READ_TIMEOUT_SEC", "30"))
OLLAMA_INIT_CHUNK_TIMEOUT = float(os.getenv("OLLAMA_INIT_CHUNK_TIMEOUT_SEC", "15"))
OLLAMA_NUM_PREDICT = int(os.getenv("RESPONSE_TOKENS", "256"))

logger = logging.getLogger(__name__)

# Global httpx client singleton with keep-alive
_http_client: Optional[httpx.Client] = None
_client_lock = threading.Lock()


def get_http_client() -> httpx.Client:
    """Get or create singleton httpx client with keep-alive."""
    global _http_client
    if _http_client is None:
        with _client_lock:
            if _http_client is None:
                _http_client = httpx.Client(
                    timeout=httpx.Timeout(connect=3.0, read=60.0, write=3.0, pool=3.0),
                    limits=httpx.Limits(
                        max_keepalive_connections=20, max_connections=50
                    ),
                    http2=False,  # Disable HTTP/2 to avoid h2 dependency
                    follow_redirects=True,
                )
    return _http_client


def _ollama_ping() -> bool:
    """Check if Ollama server is reachable."""
    try:
        r = requests.get(f"{OLLAMA_HOST}/api/tags", timeout=(OLLAMA_CONNECT_TIMEOUT, 3))
        r.raise_for_status()
        return True
    except Exception as e:
        logger.error("Ollama ping failed at %s: %s", OLLAMA_HOST, e)
        return False


def get_available_models() -> list[str]:
    """Get list of available Ollama models."""
    try:
        r = requests.get(f"{OLLAMA_HOST}/api/tags", timeout=(OLLAMA_CONNECT_TIMEOUT, 3))
        r.raise_for_status()
        data = r.json()
        models = [model["name"] for model in data.get("models", [])]
        logger.info(f"Available Ollama models: {models}")
        return models
    except Exception as e:
        logger.error("Failed to get Ollama models: %s", e)
        return []


def call_ollama_simple_stream(
    model: str, prompt: str, options: dict = None
) -> Generator[dict[str, Any], None, None]:
    """Simple streaming function using requests (more reliable than httpx)."""
    try:
        payload = {
            "model": model,
            "prompt": prompt,
            "stream": True,
            "keep_alive": "1h",
        }

        if options:
            payload.update(options)

        logger.info(f"Simple stream payload: {payload}")

        r = requests.post(
            f"{OLLAMA_HOST}/api/generate",
            json=payload,
            stream=True,
            timeout=(OLLAMA_CONNECT_TIMEOUT, OLLAMA_READ_TIMEOUT),
        )
        r.raise_for_status()

        for line in r.iter_lines():
            if line:
                try:
                    data = json.loads(line.decode("utf-8"))
                    yield data
                except json.JSONDecodeError:
                    continue
                except Exception:
                    continue

    except Exception as e:
        logger.error(f"Simple stream error: {e}")
        yield {"error": str(e), "done": True}


def _messages_to_prompt(messages: list[dict[str, str]]) -> str:
    """Convert messages to prompt format for /api/generate endpoint."""
    sys = "\n".join(
        m.get("content", "") for m in messages if m.get("role") == "system"
    ).strip()
    usr = "\n".join(
        m.get("content", "") for m in messages if m.get("role") == "user"
    ).strip()
    return (sys + ("\n\n" if sys and usr else "") + usr).strip() or usr


def _stream_post(url: str, payload: dict) -> Generator[dict[str, Any], None, None]:
    """Stream POST request with first chunk timeout detection."""
    with requests.post(
        url,
        json=payload,
        stream=True,
        timeout=(OLLAMA_CONNECT_TIMEOUT, OLLAMA_READ_TIMEOUT),
    ) as resp:
        resp.raise_for_status()
        t0 = time.time()
        yielded = False
        for raw in resp.iter_lines(decode_unicode=True):
            if not raw:
                # If no chunk received within timeout, consider it failed
                if not yielded and (time.time() - t0) > OLLAMA_INIT_CHUNK_TIMEOUT:
                    raise TimeoutError(
                        "No first chunk from Ollama within init-chunk timeout"
                    )
                continue
            yielded = True
            try:
                data = json.loads(raw)
                yield data
            except json.JSONDecodeError:
                continue
            except Exception:
                continue


def call_ollama_chat(
    model: str,
    messages: list[dict[str, str]],
    stream: bool = True,
    options: dict = None,
    timeout: float = None,
) -> Generator[dict[str, Any], None, None]:
    """
    Call Ollama with /api/generate using httpx singleton with real timeout.

    Args:
        model: Model name (e.g., "gemma2:2b")
        messages: List of message dicts with "role" and "content"
        stream: Whether to stream the response
        options: Additional options for the model (num_predict, temperature, etc.)
        timeout: Request timeout in seconds (overrides default)

    Yields:
        Dict: Response chunks from Ollama

    Raises:
        ConnectionError: If Ollama is not reachable
        TimeoutError: If no response within timeout
    """
    if not _ollama_ping():
        raise ConnectionError(f"Ollama not reachable at {OLLAMA_HOST}")

    logger.info(f"Ollama will use {OLLAMA_HOST}")

    # Convert messages to simple prompt
    prompt = _messages_to_prompt(messages)

    # Optimized payload with keep-alive
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": stream,
        "keep_alive": "1h",
    }

    # Add/override options if provided
    if options:
        payload.update(options)

    logger.info(f"Ollama payload: {payload}")

    # Use httpx client with per-request timeout
    client = get_http_client()
    request_timeout = timeout or OLLAMA_READ_TIMEOUT

    # Create per-request timeout object
    timeout_obj = httpx.Timeout(connect=1.0, read=request_timeout, write=1.0, pool=1.0)

    try:
        if stream:
            with client.stream(
                "POST", f"{OLLAMA_HOST}/api/generate", json=payload, timeout=timeout_obj
            ) as resp:
                resp.raise_for_status()

                t0 = time.time()
                yielded = False

                for line in resp.iter_lines():
                    if not line:
                        # If no chunk received within timeout, consider it failed
                        if (
                            not yielded
                            and (time.time() - t0) > OLLAMA_INIT_CHUNK_TIMEOUT
                        ):
                            raise TimeoutError(
                                "No first chunk from Ollama within init-chunk timeout"
                            )
                        continue

                    yielded = True
                    if not hasattr(call_ollama_chat, "_first_chunk_time"):
                        call_ollama_chat._first_chunk_time = time.time() - t0
                        logger.info(
                            f"First chunk in {call_ollama_chat._first_chunk_time:.2f}s"
                        )

                    try:
                        data = json.loads(line.decode("utf-8"))
                        yield data
                    except json.JSONDecodeError:
                        continue
                    except Exception:
                        continue
        else:
            # Non-streaming: use regular request
            resp = client.post(
                f"{OLLAMA_HOST}/api/generate", json=payload, timeout=timeout_obj
            )
            resp.raise_for_status()
            data = resp.json()
            logger.info(f"Ollama response: {data}")
            yield data

    except httpx.TimeoutException:
        logger.error("Ollama API timeout after %s seconds", request_timeout)
        raise TimeoutError(f"Ollama API timeout after {request_timeout} seconds")
    except httpx.RequestError as e:
        logger.error("Ollama API request failed: %s", e)
        raise ConnectionError(f"Ollama API request failed: {e}")
    except Exception as e:
        logger.error("Ollama /api/generate failed: %s", e)
        raise


def is_loaded(model: str) -> bool:
    """Check if model is currently loaded and warm."""
    try:
        client = get_http_client()
        r = client.get(f"{OLLAMA_HOST}/api/ps")
        r.raise_for_status()
        data = r.json()
        return any(
            p.get("model", "").startswith(model.split(":")[0])
            for p in data.get("models", [])
        )
    except Exception as e:
        logger.warning(f"Failed to check model status: {e}")
        return False


def generate(
    model: str, prompt: str, options=None, keep_alive="1h", stream=True
) -> str:
    """Generate response with optimized defaults."""
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": stream,
        "keep_alive": keep_alive,
    }
    if options:
        payload["options"] = options

    start_time = time.time()

    try:
        r = _http_client.post(f"{OLLAMA_HOST}/api/generate", json=payload, timeout=None)
        r.raise_for_status()

        # Handle streaming vs non-streaming response
        if stream:
            txt = ""
            ollama_meta = {}
            for line in r.iter_lines():
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                    txt += obj.get("response", "")

                    # Collect Ollama metadata from last chunk
                    if obj.get("done", False):
                        ollama_meta = {
                            "total_duration": obj.get("total_duration"),
                            "load_duration": obj.get("load_duration"),
                            "prompt_eval_count": obj.get("prompt_eval_count"),
                            "prompt_eval_duration": obj.get("prompt_eval_duration"),
                            "eval_count": obj.get("eval_count"),
                            "eval_duration": obj.get("eval_duration"),
                        }
                except json.JSONDecodeError:
                    continue

            # Log telemetry
            _log_telemetry(model, prompt, start_time, stream, ollama_meta)
            return txt
        else:
            data = r.json()

            # Collect Ollama metadata
            ollama_meta = {
                "total_duration": data.get("total_duration"),
                "load_duration": data.get("load_duration"),
                "prompt_eval_count": data.get("prompt_eval_count"),
                "prompt_eval_duration": data.get("prompt_eval_duration"),
                "eval_count": data.get("eval_count"),
                "eval_duration": data.get("eval_duration"),
            }

            # Log telemetry
            _log_telemetry(model, prompt, start_time, stream, ollama_meta)
            return data.get("response", "")
    except Exception as e:
        logger.error(f"Generate failed: {e}")
        raise


def _log_telemetry(
    model: str, prompt: str, start_time: float, stream: bool, ollama_meta: dict
):
    """Log telemetry data"""
    try:
        from modules.telemetry import log_event

        # Get route information if available
        route = "unknown"
        fast_lane = False
        try:
            from modules.intelligent_router import explain_last_route

            route_info = explain_last_route()
            if route_info:
                route = route_info.get("route", "unknown")
                fast_lane = route_info.get("fast_lane", False)
        except:
            pass

        # Calculate timing
        total_ms = int((time.time() - start_time) * 1000)

        # Extract timing from Ollama metadata
        generate_ms = 0
        if ollama_meta.get("total_duration"):
            generate_ms = int(
                ollama_meta["total_duration"] / 1000000
            )  # Convert from nanoseconds to ms

        # Log event
        event = {
            "model": model,
            "route": route,
            "fast_lane": fast_lane,
            "classify_ms": 0,  # Will be set by router
            "generate_ms": generate_ms,
            "total_ms": total_ms,
            "ollama_meta": ollama_meta,
            "prompt_len": len(prompt.split()),
            "stream": stream,
        }

        log_event(event)
    except Exception as e:
        logger.warning(f"Failed to log telemetry: {e}")


def warmup_blocking(model="gemma2:2b"):
    """Blocking warmup of model to ensure it's loaded and ready."""
    if is_loaded(model):
        logger.info("Warm: %s already loaded", model)
        return

    logger.info("🔥 Warming up %s ...", model)

    try:
        # Generate a few tokens to warm up the model
        _ = generate(
            model,
            "hi",
            options={"num_predict": 8, "temperature": 0.1},
            keep_alive="1h",
            stream=False,
        )

        # Wait for model to be confirmed loaded
        t0 = time.time()
        while not is_loaded(model) and time.time() - t0 < 10:
            time.sleep(0.5)

        logger.info("✅ %s warmed (ready=%s)", model, is_loaded(model))
    except Exception as e:
        logger.warning(f"Warmup failed for {model}: {e}")


def warmup_phi4_mini():
    """Specialized warmup for phi4-mini model."""
    model = "phi4-mini"
    logger.info("🔥 Warming up phi4-mini (specialized)...")

    try:
        # Use optimized settings for phi4-mini
        _ = generate(
            model,
            "Hello, how are you?",
            options={"num_predict": 8, "temperature": 0.1},
            keep_alive="1h",
            stream=False,
        )

        # Wait for model to be confirmed loaded
        t0 = time.time()
        while (
            not is_loaded(model) and time.time() - t0 < 15
        ):  # Longer timeout for phi4-mini
            time.sleep(0.5)

        if is_loaded(model):
            logger.info("✅ phi4-mini warmed and ready!")
            return True
        else:
            logger.warning("⚠️ phi4-mini warmup completed but not confirmed loaded")
            return False
    except Exception as e:
        logger.error(f"❌ phi4-mini warmup failed: {e}")
        return False
