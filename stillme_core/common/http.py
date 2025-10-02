#!/usr/bin/env python3
"""
HTTP Utilities for StillMe AI Framework
Tiện ích HTTP cho StillMe AI Framework

This module provides async HTTP client utilities with retry, timeout, and error handling.
Module này cung cấp các tiện ích HTTP client bất đồng bộ với retry, timeout và xử lý lỗi.
"""

import json
import time
from dataclasses import dataclass
from enum import Enum
from typing import Any, Optional, Union
from urllib.parse import urljoin

import httpx

from .errors import APIError, NetworkError, StillMeException, ValidationError
from .logging import get_module_logger
from .retry import RetryConfig, RetryManager

logger = get_module_logger("http")


class HTTPMethod(Enum):
    """HTTP Methods - Các phương thức HTTP"""

    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    DELETE = "DELETE"
    PATCH = "PATCH"
    HEAD = "HEAD"
    OPTIONS = "OPTIONS"


@dataclass
class HTTPRequest:
    """HTTP Request configuration - Cấu hình HTTP Request"""

    method: HTTPMethod
    url: str
    headers: Optional[dict[str, str]] = None
    params: Optional[dict[str, Any]] = None
    data: Optional[Union[dict[str, Any], str, bytes]] = None
    json_data: Optional[dict[str, Any]] = None
    timeout: Optional[float] = None
    follow_redirects: bool = True
    verify_ssl: bool = True


@dataclass
class HTTPResponse:
    """HTTP Response wrapper - Wrapper HTTP Response"""

    status_code: int
    headers: dict[str, str]
    content: bytes
    text: str
    url: str
    elapsed_time: float
    request: HTTPRequest
    json_data: Optional[dict[str, Any]] = None

    def is_success(self) -> bool:
        """Check if response is successful - Kiểm tra response có thành công không"""
        return 200 <= self.status_code < 300

    def is_client_error(self) -> bool:
        """Check if response is client error - Kiểm tra response có lỗi client không"""
        return 400 <= self.status_code < 500

    def is_server_error(self) -> bool:
        """Check if response is server error - Kiểm tra response có lỗi server không"""
        return 500 <= self.status_code < 600

    def raise_for_status(self) -> None:
        """Raise exception if response is not successful - Ném exception nếu response không thành công"""
        if not self.is_success():
            raise APIError(
                f"HTTP {self.status_code}: {self.text[:200]}",
                status_code=self.status_code,
                endpoint=self.url,
            )


@dataclass
class HTTPClientConfig:
    """HTTP Client configuration - Cấu hình HTTP Client"""

    base_url: Optional[str] = None
    default_headers: Optional[dict[str, str]] = None
    timeout: float = 30.0
    max_retries: int = 3
    retry_delay: float = 1.0
    follow_redirects: bool = True
    verify_ssl: bool = True
    user_agent: str = "StillMe-AI-Framework/2.1.1"


class AsyncHttpClient:
    """
    Async HTTP Client with retry, timeout, and error handling
    HTTP Client bất đồng bộ với retry, timeout và xử lý lỗi
    """

    def __init__(self, config: Optional[HTTPClientConfig] = None):
        """
        Initialize HTTP client - Khởi tạo HTTP client

        Args:
            config: HTTP client configuration
        """
        self.config = config or HTTPClientConfig()
        self.retry_manager = RetryManager(
            RetryConfig(
                max_attempts=self.config.max_retries,
                base_delay=self.config.retry_delay,
                exceptions=(
                    httpx.RequestError,
                    httpx.HTTPStatusError,
                    httpx.TimeoutException,
                ),
            )
        )

        # Default headers
        self.default_headers = {
            "User-Agent": self.config.user_agent,
            "Accept": "application/json",
            "Content-Type": "application/json",
        }
        if self.config.default_headers:
            self.default_headers.update(self.config.default_headers)

        logger.info(
            "HTTP client initialized",
            base_url=self.config.base_url,
            timeout=self.config.timeout,
            max_retries=self.config.max_retries,
        )

    def _build_url(self, url: str) -> str:
        """Build full URL - Xây dựng URL đầy đủ"""
        if self.config.base_url:
            return urljoin(self.config.base_url, url)
        return url

    def _prepare_headers(self, request: HTTPRequest) -> dict[str, str]:
        """Prepare headers for request - Chuẩn bị headers cho request"""
        headers = self.default_headers.copy()
        if request.headers:
            headers.update(request.headers)
        return headers

    def _prepare_data(
        self, request: HTTPRequest
    ) -> Optional[Union[dict[str, Any], str, bytes]]:
        """Prepare data for request - Chuẩn bị data cho request"""
        if request.json_data:
            return json.dumps(request.json_data)
        return request.data

    async def _make_request(self, request: HTTPRequest) -> HTTPResponse:
        """Make HTTP request - Thực hiện HTTP request"""
        start_time = time.time()

        # Build full URL
        full_url = self._build_url(request.url)

        # Prepare headers and data
        headers = self._prepare_headers(request)
        data = self._prepare_data(request)

        # Prepare timeout
        timeout = request.timeout or self.config.timeout

        logger.debug(
            "Making HTTP request",
            method=request.method.value,
            url=full_url,
            timeout=timeout,
        )

        try:
            async with httpx.AsyncClient(
                timeout=timeout,
                follow_redirects=request.follow_redirects,
                verify=request.verify_ssl,
            ) as client:
                response = await client.request(
                    method=request.method.value,
                    url=full_url,
                    headers=headers,
                    params=request.params,
                    content=data,
                )

                # Parse response
                elapsed_time = time.time() - start_time

                # Try to parse JSON
                json_data = None
                try:
                    if response.headers.get("content-type", "").startswith(
                        "application/json"
                    ):
                        json_data = response.json()
                except (json.JSONDecodeError, ValueError):
                    pass

                http_response = HTTPResponse(
                    status_code=response.status_code,
                    headers=dict(response.headers),
                    content=response.content,
                    text=response.text,
                    json_data=json_data,
                    url=str(response.url),
                    elapsed_time=elapsed_time,
                    request=request,
                )

                logger.info(
                    "HTTP request completed",
                    method=request.method.value,
                    url=full_url,
                    status_code=response.status_code,
                    elapsed_time=elapsed_time,
                )

                return http_response

        except httpx.TimeoutException as e:
            elapsed_time = time.time() - start_time
            logger.error(
                "HTTP request timeout",
                method=request.method.value,
                url=full_url,
                timeout=timeout,
                elapsed_time=elapsed_time,
            )
            raise NetworkError(
                f"Request timeout after {timeout}s", url=full_url, timeout=timeout
            ) from e

        except httpx.RequestError as e:
            elapsed_time = time.time() - start_time
            logger.error(
                "HTTP request error",
                method=request.method.value,
                url=full_url,
                error=str(e),
                elapsed_time=elapsed_time,
            )
            raise NetworkError(f"Request failed: {e!s}", url=full_url) from e

        except Exception as e:
            elapsed_time = time.time() - start_time
            logger.error(
                "Unexpected HTTP error",
                method=request.method.value,
                url=full_url,
                error=str(e),
                elapsed_time=elapsed_time,
            )
            raise StillMeException(f"Unexpected HTTP error: {e!s}") from e

    async def request(self, request: HTTPRequest) -> HTTPResponse:
        """
        Make HTTP request with retry - Thực hiện HTTP request với retry

        Args:
            request: HTTP request configuration

        Returns:
            HTTP response

        Raises:
            APIError: If request fails after retries
            NetworkError: If network error occurs
            ValidationError: If request is invalid
        """
        # Validate request
        if not request.url:
            raise ValidationError("URL is required", field="url")

        if not request.method:
            raise ValidationError("HTTP method is required", field="method")

        # Make request with retry
        try:
            response = await self.retry_manager.retry_async(
                lambda: self._make_request(request)
            )
            return response
        except Exception as e:
            logger.error(
                "HTTP request failed after retries",
                method=request.method.value,
                url=request.url,
                error=str(e),
            )
            raise

    async def get(self, url: str, **kwargs) -> HTTPResponse:
        """Make GET request - Thực hiện GET request"""
        request = HTTPRequest(method=HTTPMethod.GET, url=url, **kwargs)
        return await self.request(request)

    async def post(self, url: str, **kwargs) -> HTTPResponse:
        """Make POST request - Thực hiện POST request"""
        request = HTTPRequest(method=HTTPMethod.POST, url=url, **kwargs)
        return await self.request(request)

    async def put(self, url: str, **kwargs) -> HTTPResponse:
        """Make PUT request - Thực hiện PUT request"""
        request = HTTPRequest(method=HTTPMethod.PUT, url=url, **kwargs)
        return await self.request(request)

    async def delete(self, url: str, **kwargs) -> HTTPResponse:
        """Make DELETE request - Thực hiện DELETE request"""
        request = HTTPRequest(method=HTTPMethod.DELETE, url=url, **kwargs)
        return await self.request(request)

    async def patch(self, url: str, **kwargs) -> HTTPResponse:
        """Make PATCH request - Thực hiện PATCH request"""
        request = HTTPRequest(method=HTTPMethod.PATCH, url=url, **kwargs)
        return await self.request(request)


class HttpRequestBuilder:
    """
    Builder pattern for HTTP requests
    Builder pattern cho HTTP requests
    """

    def __init__(self, client: AsyncHttpClient):
        """
        Initialize builder - Khởi tạo builder

        Args:
            client: HTTP client instance
        """
        self.client = client
        self._request = HTTPRequest(method=HTTPMethod.GET, url="")

    def method(self, method: HTTPMethod) -> "HttpRequestBuilder":
        """Set HTTP method - Thiết lập HTTP method"""
        self._request.method = method
        return self

    def url(self, url: str) -> "HttpRequestBuilder":
        """Set URL - Thiết lập URL"""
        self._request.url = url
        return self

    def headers(self, headers: dict[str, str]) -> "HttpRequestBuilder":
        """Set headers - Thiết lập headers"""
        self._request.headers = headers
        return self

    def header(self, key: str, value: str) -> "HttpRequestBuilder":
        """Add single header - Thêm header đơn"""
        if self._request.headers is None:
            self._request.headers = {}
        self._request.headers[key] = value
        return self

    def params(self, params: dict[str, Any]) -> "HttpRequestBuilder":
        """Set query parameters - Thiết lập query parameters"""
        self._request.params = params
        return self

    def param(self, key: str, value: Any) -> "HttpRequestBuilder":
        """Add single parameter - Thêm parameter đơn"""
        if self._request.params is None:
            self._request.params = {}
        self._request.params[key] = value
        return self

    def data(self, data: Union[dict[str, Any], str, bytes]) -> "HttpRequestBuilder":
        """Set request data - Thiết lập request data"""
        self._request.data = data
        return self

    def json(self, json_data: dict[str, Any]) -> "HttpRequestBuilder":
        """Set JSON data - Thiết lập JSON data"""
        self._request.json_data = json_data
        return self

    def timeout(self, timeout: float) -> "HttpRequestBuilder":
        """Set timeout - Thiết lập timeout"""
        self._request.timeout = timeout
        return self

    def follow_redirects(self, follow: bool) -> "HttpRequestBuilder":
        """Set follow redirects - Thiết lập follow redirects"""
        self._request.follow_redirects = follow
        return self

    def verify_ssl(self, verify: bool) -> "HttpRequestBuilder":
        """Set SSL verification - Thiết lập SSL verification"""
        self._request.verify_ssl = verify
        return self

    async def execute(self) -> HTTPResponse:
        """Execute request - Thực hiện request"""
        return await self.client.request(self._request)


class ResponseValidator:
    """
    Response validation utilities
    Tiện ích xác thực response
    """

    @staticmethod
    def validate_json_response(
        response: HTTPResponse, required_fields: Optional[list[str]] = None
    ) -> dict[str, Any]:
        """
        Validate JSON response - Xác thực JSON response

        Args:
            response: HTTP response
            required_fields: List of required fields

        Returns:
            Parsed JSON data

        Raises:
            ValidationError: If validation fails
        """
        if not response.is_success():
            raise ValidationError(f"Response not successful: {response.status_code}")

        if response.json_data is None:
            raise ValidationError("Response is not valid JSON")

        if required_fields:
            missing_fields = [
                field for field in required_fields if field not in response.json_data
            ]
            if missing_fields:
                raise ValidationError(f"Missing required fields: {missing_fields}")

        return response.json_data

    @staticmethod
    def validate_status_code(response: HTTPResponse, expected_codes: list[int]) -> None:
        """
        Validate status code - Xác thực status code

        Args:
            response: HTTP response
            expected_codes: List of expected status codes

        Raises:
            ValidationError: If status code is not expected
        """
        if response.status_code not in expected_codes:
            raise ValidationError(
                f"Unexpected status code: {response.status_code}, expected: {expected_codes}"
            )


# Convenience functions - Các hàm tiện ích


async def get_json(url: str, **kwargs) -> dict[str, Any]:
    """
    Make GET request and return JSON - Thực hiện GET request và trả về JSON

    Args:
        url: Request URL
        **kwargs: Additional request parameters

    Returns:
        Parsed JSON data
    """
    client = AsyncHttpClient()
    response = await client.get(url, **kwargs)
    response.raise_for_status()
    return ResponseValidator.validate_json_response(response)


async def post_json(url: str, data: dict[str, Any], **kwargs) -> dict[str, Any]:
    """
    Make POST request with JSON data - Thực hiện POST request với JSON data

    Args:
        url: Request URL
        data: JSON data to send
        **kwargs: Additional request parameters

    Returns:
        Parsed JSON response
    """
    client = AsyncHttpClient()
    response = await client.post(url, json_data=data, **kwargs)
    response.raise_for_status()
    return ResponseValidator.validate_json_response(response)


async def download_file(url: str, file_path: str, **kwargs) -> None:
    """
    Download file from URL - Tải file từ URL

    Args:
        url: File URL
        file_path: Local file path
        **kwargs: Additional request parameters
    """
    client = AsyncHttpClient()
    response = await client.get(url, **kwargs)
    response.raise_for_status()

    with open(file_path, "wb") as f:
        f.write(response.content)

    logger.info("File downloaded successfully", url=url, file_path=file_path)


class SecureHttpClient(AsyncHttpClient):
    """
    Secure HTTP Client with additional security features
    HTTP Client bảo mật với các tính năng bảo mật bổ sung
    """

    def __init__(self, config: Optional[HTTPClientConfig] = None):
        """Initialize secure HTTP client"""
        if config is None:
            config = HTTPClientConfig()

        # Add security headers
        if config.default_headers is None:
            config.default_headers = {}

        config.default_headers.update({
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
            "X-XSS-Protection": "1; mode=block",
            "Strict-Transport-Security": "max-age=31536000; includeSubDomains"
        })

        super().__init__(config)
        logger.info("Secure HTTP client initialized with security headers")

    async def __aenter__(self):
        """Async context manager entry"""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        # Clean up resources if needed
        pass
