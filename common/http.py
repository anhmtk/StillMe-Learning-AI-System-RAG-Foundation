#!/usr/bin/env python3
"""
StillMe Secure HTTP Client
AsyncHttpClient với các ràng buộc bảo mật nghiêm ngặt
"""

import asyncio
import json
import logging
import time
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import httpx

logger = logging.getLogger(__name__)


class SecureHttpClient:
    """HTTP Client với bảo mật nghiêm ngặt"""

    def __init__(self):
        # Cấu hình bảo mật
        self.timeout = 5.0  # Timeout ≤ 5s
        self.max_retries = 2  # Retry ≤ 2
        self.max_response_size = 2 * 1024 * 1024  # 2MB limit

        # MIME allowlist
        self.allowed_mime_types = [
            "application/json",
            "text/plain",
            "text/html",
            "text/xml",
            "text/csv",
        ]

        # Domain allowlist
        self.allowed_domains = {
            "api.github.com",
            "newsapi.org",
            "gnews.io",
            "hn.algolia.com",
            "trends.google.com",
            "reddit.com",
            "api.openrouter.ai",
            "api.deepseek.com",
            "api.openai.com",
        }

        # Log file cho web access
        self.log_file = Path("logs/web_access.log")
        self.log_file.parent.mkdir(exist_ok=True)

        # Client instance
        self._client: httpx.AsyncClient | None = None

    async def __aenter__(self):
        """Async context manager entry"""
        await self._ensure_client()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self._client:
            await self._client.aclose()

    async def _ensure_client(self):
        """Đảm bảo client được khởi tạo"""
        if not self._client:
            self._client = httpx.AsyncClient(
                timeout=httpx.Timeout(self.timeout),
                limits=httpx.Limits(max_keepalive_connections=5, max_connections=10),
                headers={
                    "User-Agent": "StillMe-IPC/2.1.1 (Secure HTTP Client)",
                    "Accept": "application/json, text/*",
                },
            )

    def _validate_url(self, url: str) -> bool:
        """Validate URL có trong allowlist không"""
        try:
            parsed = urlparse(url)
            domain = parsed.netloc.lower()

            if domain not in self.allowed_domains:
                logger.warning(f"🚫 Blocked request to unauthorized domain: {domain}")
                return False

            if parsed.scheme != "https" and domain not in ["localhost", "127.0.0.1"]:
                logger.warning(f"🚫 Blocked non-HTTPS request to: {url}")
                return False

            return True
        except Exception as e:
            logger.error(f"❌ URL validation error: {e}")
            return False

    def _validate_response(self, response: httpx.Response) -> bool:
        """Validate response content"""
        try:
            content_type = response.headers.get("content-type", "").lower()
            if not any(mime in content_type for mime in self.allowed_mime_types):
                logger.warning(
                    f"🚫 Blocked response with disallowed content-type: {content_type}"
                )
                return False

            content_length = response.headers.get("content-length")
            if content_length and int(content_length) > self.max_response_size:
                logger.warning(f"🚫 Blocked oversized response: {content_length} bytes")
                return False

            return True
        except Exception as e:
            logger.error(f"❌ Response validation error: {e}")
            return False

    def _sanitize_content(self, content: str) -> str:
        """Sanitize content để loại bỏ mã độc"""
        import re

        dangerous_patterns = [
            r"<script[^>]*>.*?</script>",
            r"javascript:",
            r"data:text/html",
            r"vbscript:",
            r"onload\s*=",
            r"onerror\s*=",
            r"onclick\s*=",
            r"eval\s*\(",
            r"expression\s*\(",
            r"url\s*\(",
            r"@import",
            r"<iframe[^>]*>",
            r"<object[^>]*>",
            r"<embed[^>]*>",
            r"<link[^>]*>",
            r"<meta[^>]*>",
        ]

        sanitized = content
        for pattern in dangerous_patterns:
            sanitized = re.sub(pattern, "", sanitized, flags=re.IGNORECASE | re.DOTALL)

        return sanitized

    async def _log_request(
        self,
        method: str,
        url: str,
        status_code: int,
        response_time: float,
        success: bool,
        error: str = None,
    ):
        """Log web access request"""
        try:
            timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
            log_entry = {
                "timestamp": timestamp,
                "method": method,
                "url": url,
                "status_code": status_code,
                "response_time_ms": round(response_time * 1000, 2),
                "success": success,
                "error": error,
            }

            with open(self.log_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(log_entry) + "\n")

        except Exception as e:
            logger.error(f"❌ Failed to log request: {e}")

    async def get(
        self, url: str, headers: dict[str, str] | None = None
    ) -> dict[str, Any]:
        """GET request với bảo mật"""
        return await self._make_request("GET", url, headers=headers)

    async def post(
        self,
        url: str,
        data: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        """POST request với bảo mật"""
        return await self._make_request("POST", url, data=data, headers=headers)

    async def _make_request(
        self,
        method: str,
        url: str,
        data: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        """Thực hiện HTTP request với bảo mật"""
        start_time = time.time()

        try:
            if not self._validate_url(url):
                await self._log_request(
                    method,
                    url,
                    0,
                    time.time() - start_time,
                    False,
                    "URL not in allowlist",
                )
                return {"success": False, "error": "URL not allowed", "data": None}

            await self._ensure_client()

            request_headers = {}
            if headers:
                request_headers.update(headers)

            last_error = None
            for attempt in range(self.max_retries + 1):
                try:
                    if method.upper() == "GET":
                        response = await self._client.get(url, headers=request_headers)
                    elif method.upper() == "POST":
                        response = await self._client.post(
                            url, json=data, headers=request_headers
                        )
                    else:
                        raise ValueError(f"Unsupported HTTP method: {method}")

                    if not self._validate_response(response):
                        await self._log_request(
                            method,
                            url,
                            response.status_code,
                            time.time() - start_time,
                            False,
                            "Response validation failed",
                        )
                        return {
                            "success": False,
                            "error": "Response validation failed",
                            "data": None,
                        }

                    content = response.text
                    sanitized_content = self._sanitize_content(content)

                    try:
                        parsed_data = json.loads(sanitized_content)
                    except json.JSONDecodeError:
                        parsed_data = sanitized_content

                    await self._log_request(
                        method,
                        url,
                        response.status_code,
                        time.time() - start_time,
                        True,
                    )

                    return {
                        "success": True,
                        "data": parsed_data,
                        "status_code": response.status_code,
                        "headers": dict(response.headers),
                    }

                except httpx.TimeoutException:
                    last_error = "Request timeout"
                    if attempt < self.max_retries:
                        await asyncio.sleep(0.5 * (attempt + 1))
                        continue
                except httpx.RequestError as e:
                    last_error = f"Request error: {str(e)}"
                    if attempt < self.max_retries:
                        await asyncio.sleep(0.5 * (attempt + 1))
                        continue
                except Exception as e:
                    last_error = f"Unexpected error: {str(e)}"
                    break

            await self._log_request(
                method, url, 0, time.time() - start_time, False, last_error
            )

            return {"success": False, "error": last_error, "data": None}

        except Exception as e:
            error_msg = f"Critical error: {str(e)}"
            await self._log_request(
                method, url, 0, time.time() - start_time, False, error_msg
            )
            logger.error(f"❌ Critical error in HTTP request: {e}")

            return {"success": False, "error": error_msg, "data": None}

    def add_allowed_domain(self, domain: str):
        """Thêm domain vào allowlist"""
        self.allowed_domains.add(domain.lower())
        logger.info(f"✅ Added domain to allowlist: {domain}")

    def get_allowed_domains(self) -> list[str]:
        """Lấy danh sách allowed domains"""
        return list(self.allowed_domains)


# Global instance
secure_http_client = SecureHttpClient()
