#!/usr/bin/env python3
"""
Validation Utilities for StillMe AI Framework
Tiện ích Xác thực cho StillMe AI Framework

This module provides comprehensive input validation and sanitization.
Module này cung cấp xác thực input toàn diện và làm sạch.

SECURITY PRINCIPLES / NGUYÊN TẮC BẢO MẬT:
- Input validation and sanitization
- Xác thực và làm sạch input
- SQL injection prevention
- Ngăn chặn SQL injection
- XSS prevention
- Ngăn chặn XSS
- Data type validation
- Xác thực kiểu dữ liệu
- Length and format validation
- Xác thực độ dài và định dạng
"""

import html
import ipaddress
import json
import re
import urllib.parse
import uuid
from dataclasses import dataclass
from datetime import date, datetime
from enum import Enum
from typing import Any, Callable, Optional, Union

import phonenumbers
from email_validator import EmailNotValidError, validate_email

from .errors import SecurityError, StillMeException, ValidationError
from .logging import get_module_logger

logger = get_module_logger("validation")


class ValidationSeverity(Enum):
    """Validation severity levels - Mức độ nghiêm trọng xác thực"""

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class DataType(Enum):
    """Supported data types - Các kiểu dữ liệu được hỗ trợ"""

    STRING = "string"
    INTEGER = "integer"
    FLOAT = "float"
    BOOLEAN = "boolean"
    EMAIL = "email"
    URL = "url"
    PHONE = "phone"
    IP_ADDRESS = "ip_address"
    UUID = "uuid"
    DATE = "date"
    DATETIME = "datetime"
    JSON = "json"
    HTML = "html"
    XML = "xml"
    CSV = "csv"


@dataclass
class ValidationRule:
    """Validation rule configuration - Cấu hình quy tắc xác thực"""

    field_name: str
    data_type: DataType
    required: bool = True
    min_length: Optional[int] = None
    max_length: Optional[int] = None
    pattern: Optional[str] = None
    allowed_values: Optional[list[Any]] = None
    custom_validator: Optional[Callable] = None
    sanitize: bool = True
    severity: ValidationSeverity = ValidationSeverity.ERROR


@dataclass
class ValidationResult:
    """Validation result - Kết quả xác thực"""

    is_valid: bool
    errors: list[str]
    warnings: list[str]
    sanitized_data: dict[str, Any]
    original_data: dict[str, Any]
    validation_time: float


class InputSanitizer:
    """
    Input sanitization utilities
    Tiện ích làm sạch input
    """

    # Dangerous SQL patterns
    SQL_INJECTION_PATTERNS = [
        r"(\b(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|EXEC|EXECUTE)\b)",
        r"(\b(UNION|OR|AND)\b.*\b(SELECT|INSERT|UPDATE|DELETE)\b)",
        r"(\b(SCRIPT|JAVASCRIPT|VBSCRIPT)\b)",
        r"(\b(CHAR|ASCII|SUBSTRING|LEN|LENGTH)\b)",
        r"(\b(WAITFOR|DELAY|SLEEP)\b)",
        r"(\b(INFORMATION_SCHEMA|SYSOBJECTS|SYSCOLUMNS)\b)",
        r"(\b(CAST|CONVERT)\b)",
        r"(\b(OPENROWSET|OPENDATASOURCE)\b)",
        r"(\b(BULK|BULKINSERT)\b)",
        r"(\b(SP_|XP_)\w+)",
    ]

    # XSS patterns
    XSS_PATTERNS = [
        r"<script[^>]*>.*?</script>",
        r"javascript:",
        r"vbscript:",
        r"on\w+\s*=",
        r"<iframe[^>]*>",
        r"<object[^>]*>",
        r"<embed[^>]*>",
        r"<form[^>]*>",
        r"<input[^>]*>",
        r"<textarea[^>]*>",
        r"<select[^>]*>",
        r"<button[^>]*>",
        r"<link[^>]*>",
        r"<meta[^>]*>",
        r"<style[^>]*>",
        r"expression\s*\(",
        r"@import",
        r"url\s*\(",
    ]

    @staticmethod
    def sanitize_string(value: str, max_length: Optional[int] = None) -> str:
        """
        Sanitize string input
        Làm sạch input string

        Args:
            value: String to sanitize
            max_length: Maximum length

        Returns:
            Sanitized string
        """
        if not isinstance(value, str):
            value = str(value)

        # Remove null bytes
        value = value.replace("\x00", "")

        # Normalize whitespace
        value = " ".join(value.split())

        # Truncate if too long
        if max_length and len(value) > max_length:
            value = value[:max_length]

        return value.strip()

    @staticmethod
    def sanitize_html(value: str, allowed_tags: Optional[list[str]] = None) -> str:
        """
        Sanitize HTML input
        Làm sạch input HTML

        Args:
            value: HTML to sanitize
            allowed_tags: List of allowed HTML tags

        Returns:
            Sanitized HTML
        """
        if not isinstance(value, str):
            value = str(value)

        # Check for dangerous patterns
        for pattern in InputSanitizer.XSS_PATTERNS:
            if re.search(pattern, value, re.IGNORECASE | re.DOTALL):
                logger.warning(f"XSS pattern detected: {pattern}")
                raise SecurityError(f"XSS pattern detected: {pattern}")

        # Basic HTML escaping if no allowed tags
        if not allowed_tags:
            return html.escape(value)

        # Use bleach for more sophisticated sanitization
        try:
            import bleach

            return bleach.clean(value, tags=allowed_tags, strip=True)
        except ImportError:
            # Fallback to basic escaping
            return html.escape(value)

    @staticmethod
    def sanitize_sql_input(value: str) -> str:
        """
        Sanitize SQL input
        Làm sạch input SQL

        Args:
            value: String to sanitize for SQL

        Returns:
            Sanitized string

        Raises:
            SecurityError: If SQL injection pattern detected
        """
        if not isinstance(value, str):
            value = str(value)

        # Check for SQL injection patterns
        for pattern in InputSanitizer.SQL_INJECTION_PATTERNS:
            if re.search(pattern, value, re.IGNORECASE):
                logger.warning(f"SQL injection pattern detected: {pattern}")
                raise SecurityError(f"SQL injection pattern detected: {pattern}")

        # Escape single quotes
        value = value.replace("'", "''")

        # Remove dangerous characters
        value = re.sub(r"[;]", "", value)
        value = re.sub(r"--", "", value)

        return value

    @staticmethod
    def sanitize_url(value: str) -> str:
        """
        Sanitize URL input
        Làm sạch input URL

        Args:
            value: URL to sanitize

        Returns:
            Sanitized URL
        """
        if not isinstance(value, str):
            value = str(value)

        # Parse URL
        try:
            parsed = urllib.parse.urlparse(value)

            # Check for dangerous schemes
            dangerous_schemes = ["javascript", "vbscript", "data", "file"]
            if parsed.scheme.lower() in dangerous_schemes:
                raise SecurityError(f"Dangerous URL scheme: {parsed.scheme}")

            # Reconstruct URL
            return urllib.parse.urlunparse(parsed)

        except Exception as e:
            logger.warning(f"URL sanitization error: {e}")
            raise ValidationError(f"Invalid URL format: {e}")


class DataValidator:
    """
    Data validation utilities
    Tiện ích xác thực dữ liệu
    """

    @staticmethod
    def validate_string(
        value: Any,
        min_length: Optional[int] = None,
        max_length: Optional[int] = None,
        pattern: Optional[str] = None,
    ) -> str:
        """
        Validate string data
        Xác thực dữ liệu string

        Args:
            value: Value to validate
            min_length: Minimum length
            max_length: Maximum length
            pattern: Regex pattern

        Returns:
            Validated string

        Raises:
            ValidationError: If validation fails
        """
        if not isinstance(value, str):
            value = str(value)

        # Check length
        if min_length and len(value) < min_length:
            raise ValidationError(f"String too short: minimum {min_length} characters")

        if max_length and len(value) > max_length:
            raise ValidationError(f"String too long: maximum {max_length} characters")

        # Check pattern
        if pattern and not re.match(pattern, value):
            raise ValidationError(f"String does not match required pattern: {pattern}")

        return value

    @staticmethod
    def validate_email(value: str) -> str:
        """
        Validate email address
        Xác thực địa chỉ email

        Args:
            value: Email to validate

        Returns:
            Validated email

        Raises:
            ValidationError: If email is invalid
        """
        try:
            validated = validate_email(value, check_deliverability=False)
            return validated.email
        except EmailNotValidError as e:
            raise ValidationError(f"Invalid email address: {e}")

    @staticmethod
    def validate_url(value: str) -> str:
        """
        Validate URL
        Xác thực URL

        Args:
            value: URL to validate

        Returns:
            Validated URL

        Raises:
            ValidationError: If URL is invalid
        """
        try:
            parsed = urllib.parse.urlparse(value)
            if not parsed.scheme or not parsed.netloc:
                raise ValidationError("Invalid URL format")
            return value
        except Exception as e:
            raise ValidationError(f"Invalid URL: {e}")

    @staticmethod
    def validate_phone(value: str, country_code: str = "VN") -> str:
        """
        Validate phone number
        Xác thực số điện thoại

        Args:
            value: Phone number to validate
            country_code: Country code for validation

        Returns:
            Validated phone number

        Raises:
            ValidationError: If phone number is invalid
        """
        try:
            parsed = phonenumbers.parse(value, country_code)
            if not phonenumbers.is_valid_number(parsed):
                raise ValidationError("Invalid phone number")
            return phonenumbers.format_number(
                parsed, phonenumbers.PhoneNumberFormat.E164
            )
        except Exception as e:
            raise ValidationError(f"Invalid phone number: {e}")

    @staticmethod
    def validate_ip_address(value: str) -> str:
        """
        Validate IP address
        Xác thực địa chỉ IP

        Args:
            value: IP address to validate

        Returns:
            Validated IP address

        Raises:
            ValidationError: If IP address is invalid
        """
        try:
            ipaddress.ip_address(value)
            return value
        except ValueError as e:
            raise ValidationError(f"Invalid IP address: {e}")

    @staticmethod
    def validate_uuid(value: str) -> str:
        """
        Validate UUID
        Xác thực UUID

        Args:
            value: UUID to validate

        Returns:
            Validated UUID

        Raises:
            ValidationError: If UUID is invalid
        """
        try:
            uuid.UUID(value)
            return value
        except ValueError as e:
            raise ValidationError(f"Invalid UUID: {e}")

    @staticmethod
    def validate_date(value: Union[str, date], format: str = "%Y-%m-%d") -> date:
        """
        Validate date
        Xác thực ngày

        Args:
            value: Date to validate
            format: Date format string

        Returns:
            Validated date

        Raises:
            ValidationError: If date is invalid
        """
        if isinstance(value, date):
            return value

        try:
            return datetime.strptime(value, format).date()
        except ValueError as e:
            raise ValidationError(f"Invalid date format: {e}")

    @staticmethod
    def validate_datetime(
        value: Union[str, datetime], format: str = "%Y-%m-%d %H:%M:%S"
    ) -> datetime:
        """
        Validate datetime
        Xác thực datetime

        Args:
            value: Datetime to validate
            format: Datetime format string

        Returns:
            Validated datetime

        Raises:
            ValidationError: If datetime is invalid
        """
        if isinstance(value, datetime):
            return value

        try:
            return datetime.strptime(value, format)
        except ValueError as e:
            raise ValidationError(f"Invalid datetime format: {e}")

    @staticmethod
    def validate_json(value: Union[str, dict, list]) -> Union[dict, list]:
        """
        Validate JSON
        Xác thực JSON

        Args:
            value: JSON to validate

        Returns:
            Validated JSON object

        Raises:
            ValidationError: If JSON is invalid
        """
        if isinstance(value, (dict, list)):
            return value

        try:
            return json.loads(value)
        except json.JSONDecodeError as e:
            raise ValidationError(f"Invalid JSON: {e}")

    @staticmethod
    def validate_integer(
        value: Any, min_value: Optional[int] = None, max_value: Optional[int] = None
    ) -> int:
        """
        Validate integer
        Xác thực integer

        Args:
            value: Value to validate
            min_value: Minimum value
            max_value: Maximum value

        Returns:
            Validated integer

        Raises:
            ValidationError: If validation fails
        """
        try:
            int_value = int(value)
        except (ValueError, TypeError):
            raise ValidationError(f"Invalid integer: {value}")

        if min_value is not None and int_value < min_value:
            raise ValidationError(f"Integer too small: minimum {min_value}")

        if max_value is not None and int_value > max_value:
            raise ValidationError(f"Integer too large: maximum {max_value}")

        return int_value

    @staticmethod
    def validate_float(
        value: Any, min_value: Optional[float] = None, max_value: Optional[float] = None
    ) -> float:
        """
        Validate float
        Xác thực float

        Args:
            value: Value to validate
            min_value: Minimum value
            max_value: Maximum value

        Returns:
            Validated float

        Raises:
            ValidationError: If validation fails
        """
        try:
            float_value = float(value)
        except (ValueError, TypeError):
            raise ValidationError(f"Invalid float: {value}")

        if min_value is not None and float_value < min_value:
            raise ValidationError(f"Float too small: minimum {min_value}")

        if max_value is not None and float_value > max_value:
            raise ValidationError(f"Float too large: maximum {max_value}")

        return float_value

    @staticmethod
    def validate_boolean(value: Any) -> bool:
        """
        Validate boolean
        Xác thực boolean

        Args:
            value: Value to validate

        Returns:
            Validated boolean

        Raises:
            ValidationError: If validation fails
        """
        if isinstance(value, bool):
            return value

        if isinstance(value, str):
            if value.lower() in ("true", "1", "yes", "on"):
                return True
            elif value.lower() in ("false", "0", "no", "off"):
                return False

        if isinstance(value, (int, float)):
            return bool(value)

        raise ValidationError(f"Invalid boolean: {value}")


class ValidationEngine:
    """
    Main validation engine
    Engine xác thực chính
    """

    def __init__(self):
        """Initialize validation engine - Khởi tạo engine xác thực"""
        self.logger = get_module_logger("validation_engine")
        self.validator = DataValidator()
        self.sanitizer = InputSanitizer()

        self.logger.info("Validation engine initialized")

    def validate_data(
        self, data: dict[str, Any], rules: list[ValidationRule]
    ) -> ValidationResult:
        """
        Validate data against rules
        Xác thực dữ liệu theo quy tắc

        Args:
            data: Data to validate
            rules: Validation rules

        Returns:
            Validation result
        """
        import time

        start_time = time.time()

        errors = []
        warnings = []
        sanitized_data = {}

        try:
            for rule in rules:
                field_name = rule.field_name
                field_value = data.get(field_name)

                # Check required fields
                if rule.required and field_value is None:
                    error_msg = f"Required field '{field_name}' is missing"
                    if rule.severity == ValidationSeverity.CRITICAL:
                        errors.append(error_msg)
                    else:
                        warnings.append(error_msg)
                    continue

                # Skip validation if field is None and not required
                if field_value is None:
                    sanitized_data[field_name] = None
                    continue

                try:
                    # Sanitize input
                    if rule.sanitize:
                        if rule.data_type == DataType.STRING:
                            field_value = self.sanitizer.sanitize_string(
                                field_value, rule.max_length
                            )
                        elif rule.data_type == DataType.HTML:
                            field_value = self.sanitizer.sanitize_html(field_value)
                        elif rule.data_type == DataType.URL:
                            field_value = self.sanitizer.sanitize_url(field_value)

                    # Validate data type
                    validated_value = self._validate_by_type(field_value, rule)

                    # Check allowed values
                    if (
                        rule.allowed_values
                        and validated_value not in rule.allowed_values
                    ):
                        error_msg = (
                            f"Field '{field_name}' has invalid value: {validated_value}"
                        )
                        if rule.severity == ValidationSeverity.CRITICAL:
                            errors.append(error_msg)
                        else:
                            warnings.append(error_msg)
                        continue

                    # Custom validation
                    if rule.custom_validator:
                        try:
                            rule.custom_validator(validated_value)
                        except Exception as e:
                            error_msg = (
                                f"Custom validation failed for '{field_name}': {e}"
                            )
                            if rule.severity == ValidationSeverity.CRITICAL:
                                errors.append(error_msg)
                            else:
                                warnings.append(error_msg)
                            continue

                    sanitized_data[field_name] = validated_value

                except ValidationError as e:
                    error_msg = f"Validation error for '{field_name}': {e}"
                    if rule.severity == ValidationSeverity.CRITICAL:
                        errors.append(error_msg)
                    else:
                        warnings.append(error_msg)
                except SecurityError as e:
                    error_msg = f"Security error for '{field_name}': {e}"
                    errors.append(error_msg)
                except Exception as e:
                    error_msg = f"Unexpected error for '{field_name}': {e}"
                    errors.append(error_msg)

            validation_time = time.time() - start_time
            is_valid = len(errors) == 0

            result = ValidationResult(
                is_valid=is_valid,
                errors=errors,
                warnings=warnings,
                sanitized_data=sanitized_data,
                original_data=data,
                validation_time=validation_time,
            )

            self.logger.info(
                "Validation completed",
                is_valid=is_valid,
                errors_count=len(errors),
                warnings_count=len(warnings),
                validation_time=validation_time,
            )

            return result

        except Exception as e:
            self.logger.error(f"Validation engine error: {e}")
            raise StillMeException(f"Validation failed: {e}")

    def _validate_by_type(self, value: Any, rule: ValidationRule) -> Any:
        """
        Validate value by data type
        Xác thực giá trị theo kiểu dữ liệu

        Args:
            value: Value to validate
            rule: Validation rule

        Returns:
            Validated value
        """
        if rule.data_type == DataType.STRING:
            return self.validator.validate_string(
                value, rule.min_length, rule.max_length, rule.pattern
            )
        elif rule.data_type == DataType.INTEGER:
            return self.validator.validate_integer(value)
        elif rule.data_type == DataType.FLOAT:
            return self.validator.validate_float(value)
        elif rule.data_type == DataType.BOOLEAN:
            return self.validator.validate_boolean(value)
        elif rule.data_type == DataType.EMAIL:
            return self.validator.validate_email(value)
        elif rule.data_type == DataType.URL:
            return self.validator.validate_url(value)
        elif rule.data_type == DataType.PHONE:
            return self.validator.validate_phone(value)
        elif rule.data_type == DataType.IP_ADDRESS:
            return self.validator.validate_ip_address(value)
        elif rule.data_type == DataType.UUID:
            return self.validator.validate_uuid(value)
        elif rule.data_type == DataType.DATE:
            return self.validator.validate_date(value)
        elif rule.data_type == DataType.DATETIME:
            return self.validator.validate_datetime(value)
        elif rule.data_type == DataType.JSON:
            return self.validator.validate_json(value)
        else:
            raise ValidationError(f"Unsupported data type: {rule.data_type}")


# Convenience functions - Các hàm tiện ích


def validate_user_input(
    data: dict[str, Any],
    required_fields: Optional[list[str]] = None,
    string_fields: Optional[list[str]] = None,
    email_fields: Optional[list[str]] = None,
) -> ValidationResult:
    """
    Validate user input with common rules
    Xác thực input người dùng với quy tắc chung

    Args:
        data: Data to validate
        required_fields: List of required field names
        string_fields: List of string field names
        email_fields: List of email field names

    Returns:
        Validation result
    """
    engine = ValidationEngine()
    rules = []

    # Add required field rules
    if required_fields:
        for field in required_fields:
            rules.append(
                ValidationRule(
                    field_name=field,
                    data_type=DataType.STRING,
                    required=True,
                    min_length=1,
                    max_length=1000,
                )
            )

    # Add string field rules
    if string_fields:
        for field in string_fields:
            rules.append(
                ValidationRule(
                    field_name=field,
                    data_type=DataType.STRING,
                    required=False,
                    max_length=5000,
                    sanitize=True,
                )
            )

    # Add email field rules
    if email_fields:
        for field in email_fields:
            rules.append(
                ValidationRule(
                    field_name=field,
                    data_type=DataType.EMAIL,
                    required=False,
                    sanitize=True,
                )
            )

    return engine.validate_data(data, rules)


def sanitize_user_input(data: dict[str, Any]) -> dict[str, Any]:
    """
    Sanitize user input
    Làm sạch input người dùng

    Args:
        data: Data to sanitize

    Returns:
        Sanitized data
    """
    sanitizer = InputSanitizer()
    sanitized = {}

    for key, value in data.items():
        if isinstance(value, str):
            sanitized[key] = sanitizer.sanitize_string(value)
        else:
            sanitized[key] = value

    return sanitized
