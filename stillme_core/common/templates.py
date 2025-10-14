#!/usr/bin/env python3
"""
Template Management for StillMe AI Framework
Quản lý Template cho StillMe AI Framework

This module provides secure template management with validation and sanitization.
Module này cung cấp quản lý template an toàn với xác thực và làm sạch.

SECURITY PRINCIPLES / NGUYÊN TẮC BẢO MẬT:
- Input sanitization and validation
- Xác thực và làm sạch input
- Template injection prevention
- Ngăn chặn template injection
- Content filtering and escaping
- Lọc nội dung và escape
- Audit logging for security events
- Ghi log audit cho các sự kiện bảo mật
"""

import hashlib
import html
import json
import re
from collections.abc import Callable
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any

import bleach
import jinja2
from jinja2 import Environment, Template, TemplateSyntaxError, UndefinedError

from .config import load_module_config
from .errors import SecurityError, StillMeException, ValidationError
from .io import FileFormat, FileManager, FileOperation
from .logging import get_module_logger

logger = get_module_logger("templates")


class TemplateType(Enum):
    """Template types - Các loại template"""

    RESPONSE = "response"
    PROMPT = "prompt"
    EMAIL = "email"
    NOTIFICATION = "notification"
    LOG_MESSAGE = "log_message"
    API_RESPONSE = "api_response"
    SECURITY_RESPONSE = "security_response"


class SecurityLevel(Enum):
    """Security levels - Các mức bảo mật"""

    LOW = "low"  # Basic escaping
    MEDIUM = "medium"  # HTML sanitization + escaping
    HIGH = "high"  # Strict validation + sanitization
    CRITICAL = "critical"  # Maximum security for sensitive data


@dataclass
class TemplateConfig:
    """Template configuration - Cấu hình template"""

    name: str
    template_type: TemplateType
    security_level: SecurityLevel
    allowed_variables: set[str] | None = None
    max_length: int | None = None
    required_variables: set[str] | None = None
    custom_validators: list[Callable] | None = None
    cache_enabled: bool = True
    audit_logging: bool = True


@dataclass
class TemplateContext:
    """Template rendering context - Context render template"""

    variables: dict[str, Any]
    metadata: dict[str, Any] | None = None
    security_context: dict[str, Any] | None = None


class SecurityValidator:
    """
    Security validation utilities
    Tiện ích xác thực bảo mật
    """

    # Dangerous patterns that should be blocked
    DANGEROUS_PATTERNS = [
        r"<script[^>]*>.*?</script>",  # Script tags
        r"javascript:",  # JavaScript URLs
        r"data:text/html",  # Data URLs
        r"vbscript:",  # VBScript
        r"on\w+\s*=",  # Event handlers
        r"expression\s*\(",  # CSS expressions
        r"@import",  # CSS imports
        r"url\s*\(",  # CSS URLs
        r"<iframe[^>]*>",  # Iframe tags
        r"<object[^>]*>",  # Object tags
        r"<embed[^>]*>",  # Embed tags
        r"<form[^>]*>",  # Form tags
        r"<input[^>]*>",  # Input tags
        r"<textarea[^>]*>",  # Textarea tags
        r"<select[^>]*>",  # Select tags
        r"<button[^>]*>",  # Button tags
        r"<link[^>]*>",  # Link tags
        r"<meta[^>]*>",  # Meta tags
        r"<style[^>]*>",  # Style tags
        r"<link[^>]*>",  # Link tags
    ]

    # Allowed HTML tags for different security levels
    ALLOWED_TAGS = {
        SecurityLevel.LOW: ["b", "i", "u", "em", "strong", "p", "br"],
        SecurityLevel.MEDIUM: [
            "b",
            "i",
            "u",
            "em",
            "strong",
            "p",
            "br",
            "a",
            "ul",
            "ol",
            "li",
        ],
        SecurityLevel.HIGH: ["b", "i", "em", "strong", "p"],
        SecurityLevel.CRITICAL: [],  # No HTML allowed
    }

    # Allowed HTML attributes
    ALLOWED_ATTRIBUTES = {
        SecurityLevel.LOW: {"a": ["href", "title"]},
        SecurityLevel.MEDIUM: {"a": ["href", "title"], "img": ["src", "alt", "title"]},
        SecurityLevel.HIGH: {"a": ["href"]},
        SecurityLevel.CRITICAL: {},
    }

    @staticmethod
    def validate_input(text: str, security_level: SecurityLevel) -> str:
        """
        Validate and sanitize input text
        Xác thực và làm sạch text input

        Args:
            text: Input text to validate
            security_level: Security level for validation

        Returns:
            Sanitized text

        Raises:
            SecurityError: If dangerous content is detected
        """
        if not isinstance(text, str):
            raise ValidationError("Input must be a string")

        # Check for dangerous patterns
        for pattern in SecurityValidator.DANGEROUS_PATTERNS:
            if re.search(pattern, text, re.IGNORECASE | re.DOTALL):
                logger.warning(
                    f"Dangerous pattern detected: {pattern}",
                    input_hash=hashlib.sha256(text.encode()).hexdigest()[:8],
                )
                raise SecurityError(f"Dangerous content detected: {pattern}")

        # Apply security level specific sanitization
        if security_level == SecurityLevel.CRITICAL:
            # No HTML allowed, escape everything
            return html.escape(text)
        elif security_level == SecurityLevel.HIGH:
            # Strict HTML sanitization
            allowed_tags = SecurityValidator.ALLOWED_TAGS[SecurityLevel.HIGH]
            allowed_attrs = SecurityValidator.ALLOWED_ATTRIBUTES[SecurityLevel.HIGH]
            return bleach.clean(
                text, tags=allowed_tags, attributes=allowed_attrs, strip=True
            )
        elif security_level == SecurityLevel.MEDIUM:
            # Moderate HTML sanitization
            allowed_tags = SecurityValidator.ALLOWED_TAGS[SecurityLevel.MEDIUM]
            allowed_attrs = SecurityValidator.ALLOWED_ATTRIBUTES[SecurityLevel.MEDIUM]
            return bleach.clean(
                text, tags=allowed_tags, attributes=allowed_attrs, strip=True
            )
        else:  # LOW
            # Basic HTML sanitization
            allowed_tags = SecurityValidator.ALLOWED_TAGS[SecurityLevel.LOW]
            allowed_attrs = SecurityValidator.ALLOWED_ATTRIBUTES[SecurityLevel.LOW]
            return bleach.clean(
                text, tags=allowed_tags, attributes=allowed_attrs, strip=True
            )

    @staticmethod
    def validate_variables(
        variables: dict[str, Any],
        allowed_variables: set[str] | None = None,
        required_variables: set[str] | None = None,
    ) -> None:
        """
        Validate template variables
        Xác thực biến template

        Args:
            variables: Variables to validate
            allowed_variables: Set of allowed variable names
            required_variables: Set of required variable names

        Raises:
            ValidationError: If validation fails
        """
        if not isinstance(variables, dict):
            raise ValidationError("Variables must be a dictionary")

        # Check required variables
        if required_variables:
            missing = required_variables - set(variables.keys())
            if missing:
                raise ValidationError(f"Missing required variables: {missing}")

        # Check allowed variables
        if allowed_variables:
            invalid = set(variables.keys()) - allowed_variables
            if invalid:
                raise ValidationError(f"Invalid variables: {invalid}")

        # Validate variable values
        for key, value in variables.items():
            if isinstance(value, str):
                # Check for dangerous patterns in string values
                for pattern in SecurityValidator.DANGEROUS_PATTERNS:
                    if re.search(pattern, value, re.IGNORECASE | re.DOTALL):
                        raise SecurityError(
                            f"Dangerous content in variable '{key}': {pattern}"
                        )


class TemplateManager:
    """
    Secure template management system
    Hệ thống quản lý template an toàn
    """

    def __init__(self, config_path: str | None = None):
        """
        Initialize template manager
        Khởi tạo template manager

        Args:
            config_path: Path to template configuration file
        """
        self.logger = get_module_logger("template_manager")
        self.config = load_module_config(
            "templates", config_path or "config/templates_config.json"
        )
        self.file_manager = FileManager()

        # Template cache
        self.template_cache: dict[str, Template] = {}
        self.template_configs: dict[str, TemplateConfig] = {}

        # Jinja2 environment with security settings
        self.jinja_env = Environment(
            autoescape=True,
            undefined=jinja2.StrictUndefined,  # Raise error for undefined variables
            trim_blocks=True,
            lstrip_blocks=True,
        )

        # Security filters
        self.jinja_env.filters["secure"] = self._secure_filter
        self.jinja_env.filters["escape_html"] = html.escape
        self.jinja_env.filters["escape_json"] = self._escape_json_filter

        # Load template configurations
        self._load_template_configs()

        self.logger.info(
            "Template manager initialized",
            cache_enabled=True,
            security_levels=len(SecurityLevel),
        )

    def _load_template_configs(self) -> None:
        """Load template configurations - Tải cấu hình template"""
        try:
            configs_data = self.config.get("template_configs", {})
            for name, config_data in configs_data.items():
                self.template_configs[name] = TemplateConfig(
                    name=name,
                    template_type=TemplateType(config_data.get("type", "response")),
                    security_level=SecurityLevel(
                        config_data.get("security_level", "medium")
                    ),
                    allowed_variables=set(config_data.get("allowed_variables", [])),
                    max_length=config_data.get("max_length"),
                    required_variables=set(config_data.get("required_variables", [])),
                    cache_enabled=config_data.get("cache_enabled", True),
                    audit_logging=config_data.get("audit_logging", True),
                )

            self.logger.info(
                "Template configurations loaded", count=len(self.template_configs)
            )
        except Exception as e:
            self.logger.error(f"Failed to load template configurations: {e}")
            raise StillMeException(f"Template configuration error: {e}") from e

    def _secure_filter(self, value: Any, security_level: str = "medium") -> str:
        """
        Security filter for Jinja2 templates
        Filter bảo mật cho Jinja2 templates

        Args:
            value: Value to filter
            security_level: Security level

        Returns:
            Sanitized value
        """
        if not isinstance(value, str):
            value = str(value)

        try:
            level = SecurityLevel(security_level)
            return SecurityValidator.validate_input(value, level)
        except Exception as e:
            self.logger.warning(f"Security filter error: {e}")
            return html.escape(str(value))

    def _escape_json_filter(self, value: Any) -> str:
        """
        JSON escape filter for Jinja2 templates
        Filter escape JSON cho Jinja2 templates

        Args:
            value: Value to escape

        Returns:
            JSON-escaped value
        """
        try:
            return json.dumps(str(value))
        except Exception:
            return json.dumps("")

    def load_template(
        self,
        template_name: str,
        template_content: str,
        config: TemplateConfig | None = None,
    ) -> Template:
        """
        Load and compile template
        Tải và biên dịch template

        Args:
            template_name: Name of the template
            template_content: Template content
            config: Template configuration

        Returns:
            Compiled Jinja2 template

        Raises:
            ValidationError: If template is invalid
            SecurityError: If template contains dangerous content
        """
        try:
            # Validate template content
            if config:
                SecurityValidator.validate_input(
                    template_content, config.security_level
                )

            # Compile template
            template = self.jinja_env.from_string(template_content)

            # Cache template if enabled
            if not config or config.cache_enabled:
                self.template_cache[template_name] = template

            self.logger.debug(f"Template loaded: {template_name}")
            return template

        except TemplateSyntaxError as e:
            self.logger.error(f"Template syntax error in '{template_name}': {e}")
            raise ValidationError(f"Invalid template syntax: {e}") from e
        except Exception as e:
            self.logger.error(f"Template loading error for '{template_name}': {e}")
            raise StillMeException(f"Template loading failed: {e}") from e

    def render_template(
        self,
        template_name: str,
        context: TemplateContext,
        config: TemplateConfig | None = None,
    ) -> str:
        """
        Render template with context
        Render template với context

        Args:
            template_name: Name of the template
            context: Template context
            config: Template configuration

        Returns:
            Rendered template

        Raises:
            ValidationError: If validation fails
            SecurityError: If security check fails
        """
        try:
            # Get template configuration
            if not config:
                config = self.template_configs.get(template_name)

            # Validate context
            if config:
                SecurityValidator.validate_variables(
                    context.variables,
                    config.allowed_variables,
                    config.required_variables,
                )

            # Get template
            template = self.template_cache.get(template_name)
            if not template:
                raise ValidationError(f"Template '{template_name}' not found")

            # Render template
            rendered = template.render(**context.variables)

            # Apply security validation to rendered content
            if config:
                rendered = SecurityValidator.validate_input(
                    rendered, config.security_level
                )

                # Check length limit
                if config.max_length and len(rendered) > config.max_length:
                    raise ValidationError(
                        f"Rendered content exceeds maximum length: {config.max_length}"
                    )

            # Audit logging
            if not config or config.audit_logging:
                self.logger.info(
                    f"Template rendered: {template_name}",
                    context_hash=hashlib.sha256(
                        str(context.variables).encode()
                    ).hexdigest()[:8],
                    output_length=len(rendered),
                )

            return rendered

        except UndefinedError as e:
            self.logger.error(f"Undefined variable in template '{template_name}': {e}")
            raise ValidationError(f"Undefined variable: {e}") from e
        except Exception as e:
            self.logger.error(f"Template rendering error for '{template_name}': {e}")
            raise StillMeException(f"Template rendering failed: {e}") from e

    def load_template_from_file(
        self, file_path: str, template_name: str | None = None
    ) -> Template:
        """
        Load template from file
        Tải template từ file

        Args:
            file_path: Path to template file
            template_name: Name for the template (defaults to filename)

        Returns:
            Compiled template
        """
        try:
            if not template_name:
                template_name = Path(file_path).stem

            # Read template content
            content = self.file_manager.read_file(file_path, FileFormat.TXT)

            # Load template
            return self.load_template(template_name, content)

        except Exception as e:
            self.logger.error(f"Failed to load template from file '{file_path}': {e}")
            raise StillMeException(f"Template file loading failed: {e}") from e

    def save_template_to_file(
        self, template_name: str, template_content: str, file_path: str
    ) -> None:
        """
        Save template to file
        Lưu template vào file

        Args:
            template_name: Name of the template
            template_content: Template content
            file_path: Path to save template
        """
        try:
            # Validate template content
            SecurityValidator.validate_input(template_content, SecurityLevel.MEDIUM)

            # Save to file
            self.file_manager.safe_write(
                file_path,
                template_content,
                FileOperation(
                    source=file_path, create_dirs=True, overwrite=True, validate=True
                ),
            )

            self.logger.info(f"Template saved to file: {file_path}")

        except Exception as e:
            self.logger.error(f"Failed to save template to file '{file_path}': {e}")
            raise StillMeException(f"Template file saving failed: {e}") from e

    def get_template_config(self, template_name: str) -> TemplateConfig | None:
        """
        Get template configuration
        Lấy cấu hình template

        Args:
            template_name: Name of the template

        Returns:
            Template configuration or None
        """
        return self.template_configs.get(template_name)

    def list_templates(self) -> list[str]:
        """
        List all loaded templates
        Liệt kê tất cả templates đã tải

        Returns:
            List of template names
        """
        return list(self.template_cache.keys())

    def clear_cache(self) -> None:
        """Clear template cache - Xóa cache template"""
        self.template_cache.clear()
        self.logger.info("Template cache cleared")

    def validate_template_syntax(self, template_content: str) -> bool:
        """
        Validate template syntax
        Xác thực cú pháp template

        Args:
            template_content: Template content to validate

        Returns:
            True if syntax is valid
        """
        try:
            self.jinja_env.from_string(template_content)
            return True
        except TemplateSyntaxError:
            return False


# Convenience functions - Các hàm tiện ích


def create_response_template(
    template_name: str,
    content: str,
    security_level: SecurityLevel = SecurityLevel.MEDIUM,
) -> TemplateManager:
    """
    Create a response template
    Tạo template phản hồi

    Args:
        template_name: Name of the template
        content: Template content
        security_level: Security level

    Returns:
        Template manager instance
    """
    manager = TemplateManager()
    config = TemplateConfig(
        name=template_name,
        template_type=TemplateType.RESPONSE,
        security_level=security_level,
        cache_enabled=True,
        audit_logging=True,
    )
    manager.load_template(template_name, content, config)
    return manager


def render_secure_response(
    template_name: str,
    variables: dict[str, Any],
    security_level: SecurityLevel = SecurityLevel.MEDIUM,
) -> str:
    """
    Render a secure response template
    Render template phản hồi an toàn

    Args:
        template_name: Name of the template
        variables: Template variables
        security_level: Security level

    Returns:
        Rendered response
    """
    manager = TemplateManager()
    context = TemplateContext(variables=variables)
    config = TemplateConfig(
        name=template_name,
        template_type=TemplateType.RESPONSE,
        security_level=security_level,
    )
    return manager.render_template(template_name, context, config)