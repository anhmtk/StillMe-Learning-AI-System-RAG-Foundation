#!/usr/bin/env python3
"""
StillMe Content Integrity Filter
Lọc và sanitize nội dung từ internet để đảm bảo an toàn
"""

import json
import logging
import re
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class ContentIntegrityFilter:
    """Filter để đảm bảo tính toàn vẹn nội dung"""

    def __init__(self):
        # Dangerous patterns
        self.dangerous_patterns = [
            # Script tags
            r"<script[^>]*>.*?</script>",
            r"<script[^>]*/>",
            # JavaScript protocols
            r"javascript:",
            r"vbscript:",
            r"data:text/html",
            r"data:application/javascript",
            # Event handlers
            r"onload\s*=",
            r"onerror\s*=",
            r"onclick\s*=",
            r"onmouseover\s*=",
            r"onfocus\s*=",
            r"onblur\s*=",
            r"onchange\s*=",
            r"onsubmit\s*=",
            r"onreset\s*=",
            r"onselect\s*=",
            r"onkeydown\s*=",
            r"onkeyup\s*=",
            r"onkeypress\s*=",
            # Dangerous functions
            r"eval\s*\(",
            r"expression\s*\(",
            r"url\s*\(",
            r"@import",
            r"@charset",
            # Dangerous HTML elements
            r"<iframe[^>]*>",
            r"<object[^>]*>",
            r"<embed[^>]*>",
            r"<applet[^>]*>",
            r"<form[^>]*>",
            r"<input[^>]*>",
            r"<button[^>]*>",
            r"<select[^>]*>",
            r"<textarea[^>]*>",
            # Meta tags that could be dangerous
            r"<meta[^>]*http-equiv[^>]*>",
            r"<meta[^>]*content[^>]*>",
            # Link tags
            r"<link[^>]*>",
            # Style tags with expressions
            r"<style[^>]*>.*?expression\s*\(.*?</style>",
            # Base64 encoded content
            r"data:image/[^;]+;base64,",
            r"data:application/[^;]+;base64,",
            # File protocols
            r"file://",
            r"ftp://",
            # SQL injection patterns
            r"union\s+select",
            r"drop\s+table",
            r"delete\s+from",
            r"insert\s+into",
            r"update\s+set",
            # Command injection
            r";\s*rm\s+",
            r";\s*cat\s+",
            r";\s*ls\s+",
            r";\s*whoami",
            r";\s*id\s+",
            r";\s*ps\s+",
            r";\s*kill\s+",
            # Path traversal
            r"\.\./",
            r"\.\.\\",
            r"%2e%2e%2f",
            r"%2e%2e%5c",
        ]

        # Compile patterns for better performance
        self.compiled_patterns = [
            re.compile(pattern, re.IGNORECASE | re.DOTALL)
            for pattern in self.dangerous_patterns
        ]

        # Log file
        self.log_file = Path("logs/content_filter.log")
        self.log_file.parent.mkdir(exist_ok=True)

        # Statistics
        self.stats = {
            "total_processed": 0,
            "blocked_content": 0,
            "sanitized_content": 0,
            "clean_content": 0,
        }

    def filter_content(self, content: str, source: str = "unknown") -> dict[str, Any]:
        """Filter và sanitize content"""
        try:
            self.stats["total_processed"] += 1

            # Check if content is empty
            if not content or not content.strip():
                return {
                    "success": True,
                    "filtered": False,
                    "content": content,
                    "warnings": [],
                }

            # Detect dangerous patterns
            warnings = []
            blocked_patterns = []

            for i, pattern in enumerate(self.compiled_patterns):
                matches = pattern.findall(content)
                if matches:
                    blocked_patterns.append(
                        {
                            "pattern_index": i,
                            "pattern": self.dangerous_patterns[i],
                            "matches": len(matches),
                        }
                    )
                    warnings.append(
                        f"Blocked dangerous pattern: {self.dangerous_patterns[i]}"
                    )

            # If dangerous patterns found, sanitize content
            if blocked_patterns:
                self.stats["blocked_content"] += 1
                sanitized_content = self._sanitize_content(content)

                # Log the filtering
                self._log_filtering(
                    source, blocked_patterns, content[:200], sanitized_content[:200]
                )

                return {
                    "success": True,
                    "filtered": True,
                    "content": sanitized_content,
                    "warnings": warnings,
                    "blocked_patterns": blocked_patterns,
                }
            else:
                self.stats["clean_content"] += 1
                return {
                    "success": True,
                    "filtered": False,
                    "content": content,
                    "warnings": [],
                }

        except Exception as e:
            logger.error(f"❌ Content filtering error: {e}")
            return {
                "success": False,
                "error": f"Content filtering failed: {str(e)}",
                "content": content,
                "filtered": False,
            }

    def _sanitize_content(self, content: str) -> str:
        """Sanitize content bằng cách loại bỏ dangerous patterns"""
        try:
            sanitized = content

            # Remove dangerous patterns
            for pattern in self.compiled_patterns:
                sanitized = pattern.sub("", sanitized)

            # Additional cleaning
            # Remove excessive whitespace
            sanitized = re.sub(r"\s+", " ", sanitized)

            # Remove empty tags
            sanitized = re.sub(r"<[^>]*>\s*</[^>]*>", "", sanitized)

            # Remove suspicious attributes
            sanitized = re.sub(
                r'\s+on\w+\s*=\s*["\'][^"\']*["\']', "", sanitized, flags=re.IGNORECASE
            )

            # Remove javascript: and data: URLs
            sanitized = re.sub(
                r'href\s*=\s*["\']javascript:[^"\']*["\']',
                'href="#"',
                sanitized,
                flags=re.IGNORECASE,
            )
            sanitized = re.sub(
                r'src\s*=\s*["\']data:[^"\']*["\']',
                'src=""',
                sanitized,
                flags=re.IGNORECASE,
            )

            self.stats["sanitized_content"] += 1

            return sanitized.strip()

        except Exception as e:
            logger.error(f"❌ Content sanitization error: {e}")
            return content  # Return original if sanitization fails

    def _log_filtering(
        self,
        source: str,
        blocked_patterns: list[dict],
        original_preview: str,
        sanitized_preview: str,
    ):
        """Log filtering activity"""
        try:
            log_entry = {
                "timestamp": self._get_timestamp(),
                "source": source,
                "blocked_patterns": blocked_patterns,
                "original_preview": original_preview,
                "sanitized_preview": sanitized_preview,
            }

            with open(self.log_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(log_entry) + "\n")

        except Exception as e:
            logger.error(f"❌ Failed to log filtering: {e}")

    def _get_timestamp(self) -> str:
        """Get current timestamp"""
        from datetime import datetime

        return datetime.now().isoformat()

    def filter_json_response(
        self, response_data: dict[str, Any], source: str = "unknown"
    ) -> dict[str, Any]:
        """Filter JSON response data"""
        try:
            if not isinstance(response_data, dict):
                return self.filter_content(str(response_data), source)

            filtered_data = {}
            warnings = []

            for key, value in response_data.items():
                if isinstance(value, str):
                    # Filter string values
                    result = self.filter_content(value, f"{source}.{key}")
                    filtered_data[key] = result["content"]
                    if result["warnings"]:
                        warnings.extend(result["warnings"])

                elif isinstance(value, list):
                    # Filter list items
                    filtered_list = []
                    for i, item in enumerate(value):
                        if isinstance(item, str):
                            result = self.filter_content(item, f"{source}.{key}[{i}]")
                            filtered_list.append(result["content"])
                            if result["warnings"]:
                                warnings.extend(result["warnings"])
                        elif isinstance(item, dict):
                            result = self.filter_json_response(
                                item, f"{source}.{key}[{i}]"
                            )
                            filtered_list.append(result["content"])
                            if result["warnings"]:
                                warnings.extend(result["warnings"])
                        else:
                            filtered_list.append(item)
                    filtered_data[key] = filtered_list

                elif isinstance(value, dict):
                    # Recursively filter nested objects
                    result = self.filter_json_response(value, f"{source}.{key}")
                    filtered_data[key] = result["content"]
                    if result["warnings"]:
                        warnings.extend(result["warnings"])

                else:
                    # Keep non-string values as-is
                    filtered_data[key] = value

            return {
                "success": True,
                "content": filtered_data,
                "warnings": warnings,
                "filtered": len(warnings) > 0,
            }

        except Exception as e:
            logger.error(f"❌ JSON filtering error: {e}")
            return {
                "success": False,
                "error": f"JSON filtering failed: {str(e)}",
                "content": response_data,
                "filtered": False,
            }

    def get_stats(self) -> dict[str, Any]:
        """Lấy thống kê filtering"""
        return {
            "total_processed": self.stats["total_processed"],
            "blocked_content": self.stats["blocked_content"],
            "sanitized_content": self.stats["sanitized_content"],
            "clean_content": self.stats["clean_content"],
            "block_rate": (
                self.stats["blocked_content"] / max(self.stats["total_processed"], 1)
            )
            * 100,
        }

    def reset_stats(self):
        """Reset thống kê"""
        self.stats = {
            "total_processed": 0,
            "blocked_content": 0,
            "sanitized_content": 0,
            "clean_content": 0,
        }


# Global instance
content_filter = ContentIntegrityFilter()


def filter_web_content(content: str, source: str = "unknown") -> dict[str, Any]:
    """Convenience function để filter content"""
    return content_filter.filter_content(content, source)


def filter_web_json(data: dict[str, Any], source: str = "unknown") -> dict[str, Any]:
    """Convenience function để filter JSON data"""
    return content_filter.filter_json_response(data, source)


if __name__ == "__main__":
    # Test content filtering
    print("🧪 Testing Content Integrity Filter...")

    # Test clean content
    clean_content = "This is a clean article about AI technology."
    result = content_filter.filter_content(clean_content, "test")
    print(f"Clean content: {result['success']}, filtered: {result['filtered']}")

    # Test dangerous content
    dangerous_content = """
    <script>alert('XSS')</script>
    <img src="javascript:alert('XSS')">
    <a href="javascript:void(0)">Click me</a>
    This is some text with dangerous content.
    """
    result = content_filter.filter_content(dangerous_content, "test")
    print(f"Dangerous content: {result['success']}, filtered: {result['filtered']}")
    print(f"Warnings: {len(result['warnings'])}")

    # Test JSON filtering
    json_data = {
        "title": "AI News",
        "content": "<script>alert('XSS')</script>This is safe content.",
        "url": "https://example.com",
        "articles": [
            {"title": "Safe article", "content": "Clean content"},
            {"title": "Dangerous article", "content": "<script>alert('XSS')</script>"},
        ],
    }
    result = content_filter.filter_json_response(json_data, "test")
    print(f"JSON filtering: {result['success']}, filtered: {result['filtered']}")
    print(f"Warnings: {len(result['warnings'])}")

    # Show stats
    stats = content_filter.get_stats()
    print("\n📊 Filtering Stats:")
    print(f"  Total processed: {stats['total_processed']}")
    print(f"  Blocked content: {stats['blocked_content']}")
    print(f"  Sanitized content: {stats['sanitized_content']}")
    print(f"  Clean content: {stats['clean_content']}")
    print(f"  Block rate: {stats['block_rate']:.1f}%")
