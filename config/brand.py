#!/usr/bin/env python3
"""
StillMe Branding Configuration
Cấu hình thương hiệu StillMe
"""

# Brand Identity
BRAND_NAME = "StillMe"
BRAND_TAGLINE = "Intelligent Personal Companion (IPC)"
BRAND_DESCRIPTION = """
Intelligent Personal Companion (IPC): Nâng cấp từ "assistant" thành "companion" –
đồng hành thông minh, khiêm tốn, học từ bạn; kết hợp multi-agent (MAS) +
cá nhân hoá (Adaptive) + đạo đức (Ethical). Tránh vòng lặp phản tư vô tận,
khuyến khích tương tác tôn trọng.
"""

# UI Text
WINDOW_TITLE = f"{BRAND_NAME} – {BRAND_TAGLINE}"
HEADER_TITLE = BRAND_NAME
HEADER_SUBTITLE = BRAND_TAGLINE
ABOUT_TITLE = f"{BRAND_NAME} – {BRAND_TAGLINE}"
ABOUT_DESCRIPTION = f"""{BRAND_NAME} is your {BRAND_TAGLINE}.

{BRAND_DESCRIPTION}

Key Features:
• Intelligent Personal Companion (IPC) – Đồng hành thông minh, khiêm tốn, học từ bạn
• Multi-Agent Systems (MAS) integration
• Personalized and Adaptive AI
• Ethical AI principles
• Comprehensive performance tracking
• FlutterFlow-style modern UI
• Session-based conversation management

{BRAND_NAME} is designed to be a helpful and engaging partner in your daily life, providing intelligent support while respecting your privacy and preferences."""

# Settings
SETTINGS_TITLE = f"{BRAND_NAME} Settings"
SETTINGS_DESCRIPTION = f"Configure your {BRAND_TAGLINE}"

# Status Messages
STATUS_READY = "Ready"
STATUS_SENDING = "Sending..."
STATUS_CONNECTED = "● Connected"
STATUS_DISCONNECTED = "● Disconnected"

# Language Support
DEFAULT_LANGUAGE = "vi-VN"
SUPPORTED_LANGUAGES = {
    "vi-VN": "Tiếng Việt",
    "en-US": "English",
    "ja-JP": "日本語",
    "zh-CN": "中文",
    "ko-KR": "한국어"
}

# Version Information
VERSION = "2.1.1"
BUILD_DATE = "2025-09-22"
FRAMEWORK_VERSION = "Enterprise Grade"

# Contact Information
WEBSITE = "https://stillme-ai.com"
SUPPORT_EMAIL = "support@stillme-ai.com"
DOCUMENTATION_URL = "https://docs.stillme-ai.com"

# Feature Flags
FEATURES = {
    "web_search": True,
    "language_detection": True,
    "persona_enforcement": True,
    "multi_agent": True,
    "adaptive_learning": True,
    "ethical_ai": True
}

# Color Scheme
COLORS = {
    "primary": "#1a1a2e",
    "secondary": "#0f0f23",
    "accent": "#ffb74d",
    "success": "#4caf50",
    "warning": "#ff9800",
    "error": "#f44336",
    "text_primary": "#ffffff",
    "text_secondary": "#a0a0a0",
    "text_muted": "#888888"
}

# Icons
ICONS = {
    "brand": "🌟",
    "settings": "⚙️",
    "language": "🌐",
    "connection": "●",
    "success": "✅",
    "error": "❌",
    "warning": "⚠️",
    "info": "ℹ️"
}

def get_brand_info():
    """Get complete brand information"""
    return {
        "name": BRAND_NAME,
        "tagline": BRAND_TAGLINE,
        "description": BRAND_DESCRIPTION,
        "version": VERSION,
        "build_date": BUILD_DATE,
        "framework_version": FRAMEWORK_VERSION,
        "features": FEATURES,
        "colors": COLORS,
        "icons": ICONS
    }

def get_window_title():
    """Get window title"""
    return WINDOW_TITLE

def get_header_text():
    """Get header text"""
    return {
        "title": HEADER_TITLE,
        "subtitle": HEADER_SUBTITLE
    }

def get_about_text():
    """Get about dialog text"""
    return {
        "title": ABOUT_TITLE,
        "description": ABOUT_DESCRIPTION
    }

def get_settings_text():
    """Get settings dialog text"""
    return {
        "title": SETTINGS_TITLE,
        "description": SETTINGS_DESCRIPTION
    }

if __name__ == "__main__":
    # Test brand configuration
    print("StillMe Brand Configuration")
    print("=" * 50)
    print(f"Name: {BRAND_NAME}")
    print(f"Tagline: {BRAND_TAGLINE}")
    print(f"Version: {VERSION}")
    print(f"Window Title: {WINDOW_TITLE}")
    print(f"Header: {HEADER_TITLE} - {HEADER_SUBTITLE}")
    print(f"About: {ABOUT_TITLE}")
    print(f"Features: {list(FEATURES.keys())}")
    print(f"Colors: {list(COLORS.keys())}")
    print(f"Icons: {list(ICONS.keys())}")
