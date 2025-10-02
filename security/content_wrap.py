# security/content_wrap.py
# Stub for ContentWrapSecurity
import logging
from dataclasses import dataclass
from typing import Any

logger = logging.getLogger(__name__)

@dataclass
class WrappedContent:
    """Result of content wrapping"""
    security_level: str
    injection_detected: bool
    wrapped_content: str
    sanitized_snippets: list[str] = None

    def __post_init__(self):
        if self.sanitized_snippets is None:
            self.sanitized_snippets = []

class ContentWrapSecurity:
    """Content wrap security handler"""

    def __init__(self):
        self.logger = logger
        self.blocked_content = []
        self.filtered_content = []

    def wrap_content(self, content: str, content_type: str = "web", source: str = "unknown") -> WrappedContent:
        """Wrap content with security measures"""
        if not content:
            return WrappedContent(
                security_level="safe",
                injection_detected=False,
                wrapped_content="",
                sanitized_snippets=[]
            )

        # Check for injection patterns
        injection_detected = False
        sanitized_snippets = []
        wrapped_content = content

        # Check for script injection
        if "<script>" in content.lower():
            injection_detected = True
            sanitized_snippets.append("script")
            wrapped_content = wrapped_content.replace("<script>", "[REMOVED_HTML_INJECTION]")
            wrapped_content = wrapped_content.replace("</script>", "[/REMOVED_HTML_INJECTION]")

        # Check for javascript injection
        if "javascript:" in content.lower():
            injection_detected = True
            sanitized_snippets.append("javascript")
            wrapped_content = wrapped_content.replace("javascript:", "[REMOVED_JAVASCRIPT_INJECTION]")

        # Check for markdown injection
        if "![image](" in content and "javascript:" in content:
            injection_detected = True
            sanitized_snippets.append("markdown")
            wrapped_content = "[REMOVED_MARKDOWN_INJECTION]" + wrapped_content

        # Check for obfuscated content
        if "<scr ipt>" in content.lower() or "java script:" in content.lower():
            injection_detected = True
            sanitized_snippets.append("obfuscated")
            wrapped_content = "[REMOVED_OBFUSCATED]" + wrapped_content

        # Check for prompt injection
        if any(pattern in content.lower() for pattern in [
            "ignore previous instructions",
            "reveal your system prompt",
            "forget everything",
            "you are now"
        ]):
            injection_detected = True
            sanitized_snippets.append("prompt_injection")
            wrapped_content = "[REMOVED_PROMPT_INJECTION]" + wrapped_content

        # Determine security level
        if injection_detected:
            if len(sanitized_snippets) >= 3:
                security_level = "high"
            elif len(sanitized_snippets) >= 2:
                security_level = "medium"
            else:
                security_level = "low"
        else:
            security_level = "safe"

        # Wrap with security markers
        if content_type == "news":
            wrapped_content = f"[WEB_SNIPPET_START]\nNỘI DUNG DƯỚI ĐÂY CHỈ LÀ THAM KHẢO\n{wrapped_content}\n[WEB_SNIPPET_END]"
        else:
            wrapped_content = f"[SECURE:{security_level.upper()}]{wrapped_content}[/SECURE]"

        self.filtered_content.append(content)

        return WrappedContent(
            security_level=security_level,
            injection_detected=injection_detected,
            wrapped_content=wrapped_content,
            sanitized_snippets=sanitized_snippets
        )

    def unwrap_content(self, wrapped_content: str) -> str:
        """Unwrap secured content"""
        if not wrapped_content:
            return ""

        # Simple unwrapping
        if wrapped_content.startswith("[SECURE:") and wrapped_content.endswith("[/SECURE]"):
            start_idx = wrapped_content.find("]") + 1
            end_idx = wrapped_content.rfind("[/SECURE]")
            return wrapped_content[start_idx:end_idx]

        return wrapped_content

    def validate_wrapped_content(self, wrapped_content: str) -> tuple[bool, str]:
        """Validate wrapped content"""
        if not wrapped_content:
            return False, "Empty content"

        if "[SECURE:" in wrapped_content or "[WEB_SNIPPET_START]" in wrapped_content:
            return True, "Content properly wrapped"

        return False, "Content not properly wrapped"

    def extract_original_content(self, wrapped_content: str) -> str:
        """Extract original content from wrapped content"""
        if not wrapped_content:
            return ""

        # Remove security markers
        content = wrapped_content
        content = content.replace("[WEB_SNIPPET_START]", "")
        content = content.replace("[WEB_SNIPPET_END]", "")
        content = content.replace("NỘI DUNG DƯỚI ĐÂY CHỈ LÀ THAM KHẢO", "")

        # Remove SECURE markers
        if "[SECURE:" in content and "[/SECURE]" in content:
            start_idx = content.find("]") + 1
            end_idx = content.rfind("[/SECURE]")
            content = content[start_idx:end_idx]

        return content.strip()

    def validate_content(self, content: str) -> dict[str, Any]:
        """Validate content security"""
        if not content:
            return {"valid": True, "issues": []}

        issues = []

        # Check for common security issues
        if "<script>" in content.lower():
            issues.append("Potential script injection")
        if "javascript:" in content.lower():
            issues.append("Potential javascript injection")
        if "eval(" in content.lower():
            issues.append("Potential eval injection")

        is_valid = len(issues) == 0

        if not is_valid:
            self.blocked_content.append(content)

        return {
            "valid": is_valid,
            "issues": issues,
            "risk_level": "high" if len(issues) > 2 else "medium" if issues else "low"
        }

    def scan_for_vulnerabilities(self, content: str) -> list[dict[str, Any]]:
        """Scan content for security vulnerabilities"""
        vulnerabilities = []

        # Simple vulnerability patterns
        patterns = {
            "<script>": "XSS - Script injection",
            "javascript:": "XSS - JavaScript protocol",
            "eval(": "Code injection - eval function",
            "exec(": "Code injection - exec function",
            "system(": "Command injection - system call",
            "subprocess": "Command injection - subprocess",
            "os.system": "Command injection - os.system",
            "../../": "Path traversal",
            "SELECT * FROM": "SQL injection pattern",
            "DROP TABLE": "SQL injection - dangerous operation",
        }

        for pattern, description in patterns.items():
            if pattern.lower() in content.lower():
                vulnerabilities.append({
                    "pattern": pattern,
                    "description": description,
                    "severity": "high" if any(x in pattern.lower() for x in ["drop", "system", "exec"]) else "medium",
                    "position": content.lower().find(pattern.lower())
                })

        return vulnerabilities

    def get_statistics(self) -> dict[str, Any]:
        """Get security statistics"""
        return {
            "total_filtered": len(self.filtered_content),
            "total_blocked": len(self.blocked_content),
            "block_rate": len(self.blocked_content) / max(1, len(self.filtered_content) + len(self.blocked_content))
        }

    def reset_statistics(self):
        """Reset security statistics"""
        self.blocked_content.clear()
        self.filtered_content.clear()

class ContentWrap(ContentWrapSecurity):
    """Alias for ContentWrapSecurity for backward compatibility"""
    pass

# Global functions for backward compatibility
def wrap_content(content: str, content_type: str = "web", source: str = "unknown") -> WrappedContent:
    """Global function to wrap content with security measures"""
    wrapper = ContentWrapSecurity()
    return wrapper.wrap_content(content, content_type, source)

def unwrap_content(wrapped_content: str) -> str:
    """Global function to unwrap secured content"""
    wrapper = ContentWrapSecurity()
    return wrapper.unwrap_content(wrapped_content)

def validate_content(content: str) -> dict[str, Any]:
    """Global function to validate content security"""
    wrapper = ContentWrapSecurity()
    return wrapper.validate_content(content)
