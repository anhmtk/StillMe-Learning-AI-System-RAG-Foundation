#!/usr/bin/env python3
"""
StillMe Design Tokens
FlutterFlow-style design system with colors, typography, and layout tokens
"""

from typing import Any


class DesignTokens:
    """FlutterFlow-style design tokens for StillMe IPC"""

    # Color Palette
    COLORS = {
        # Background gradients
        "backgroundGradient": ["#0F0C29", "#302B63", "#24243E"],
        "backgroundPrimary": "#0F0C29",
        "backgroundSecondary": "#1a1a2e",
        "backgroundTertiary": "#16213e",
        # Accent colors
        "accentViolet": "#6D28D9",
        "accentCyan": "#06B6D4",
        "accentPurple": "#8B5CF6",
        "accentBlue": "#3B82F6",
        # Text colors
        "textPrimary": "#FFFFFF",
        "textSecondary": "#D1D5DB",
        "textMuted": "#9CA3AF",
        "textAccent": "#06B6D4",
        # Status colors
        "success": "#10B981",
        "warning": "#F59E0B",
        "error": "#EF4444",
        "info": "#3B82F6",
        # Interactive colors
        "buttonPrimary": "#6D28D9",
        "buttonSecondary": "#1a1a2e",
        "buttonHover": "#7C3AED",
        "buttonActive": "#5B21B6",
        # Border and shadow
        "border": "#374151",
        "borderLight": "#4B5563",
        "shadow": "0 4px 30px rgba(0,0,0,0.3)",
        "shadowLight": "0 2px 15px rgba(0,0,0,0.2)",
        "shadowHeavy": "0 8px 40px rgba(0,0,0,0.4)",
    }

    # Typography
    TYPOGRAPHY = {
        "fontFamily": "Manrope, Inter, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif",
        "fontFamilyMono": "'JetBrains Mono', 'Fira Code', 'Consolas', monospace",
        # Font weights
        "headingWeight": 700,
        "subheadingWeight": 600,
        "bodyWeight": 400,
        "captionWeight": 500,
        # Font sizes
        "fontSizeXs": "0.75rem",  # 12px
        "fontSizeSm": "0.875rem",  # 14px
        "fontSizeBase": "1rem",  # 16px
        "fontSizeLg": "1.125rem",  # 18px
        "fontSizeXl": "1.25rem",  # 20px
        "fontSize2xl": "1.5rem",  # 24px
        "fontSize3xl": "1.875rem",  # 30px
        "fontSize4xl": "2.25rem",  # 36px
        # Line heights
        "lineHeightTight": 1.25,
        "lineHeightNormal": 1.5,
        "lineHeightRelaxed": 1.75,
    }

    # Layout
    LAYOUT = {
        "containerMaxWidth": "1200px",
        "sectionPadding": "80px",
        "cardRadius": "1.25rem",  # 20px
        "buttonRadius": "0.75rem",  # 12px
        "inputRadius": "0.5rem",  # 8px
        # Spacing
        "spacingXs": "0.25rem",  # 4px
        "spacingSm": "0.5rem",  # 8px
        "spacingMd": "1rem",  # 16px
        "spacingLg": "1.5rem",  # 24px
        "spacingXl": "2rem",  # 32px
        "spacing2xl": "3rem",  # 48px
        "spacing3xl": "4rem",  # 64px
        # Grid
        "gridGap": "1.5rem",
        "gridColumns": 12,
    }

    # Motion and Animation
    MOTION = {
        "hoverScale": 1.02,
        "activeScale": 0.98,
        "transitionFast": "all 0.15s ease-in-out",
        "transitionNormal": "all 0.3s ease-in-out",
        "transitionSlow": "all 0.5s ease-in-out",
        # Easing functions
        "easeInOut": "cubic-bezier(0.4, 0, 0.2, 1)",
        "easeOut": "cubic-bezier(0, 0, 0.2, 1)",
        "easeIn": "cubic-bezier(0.4, 0, 1, 1)",
        # Animation durations
        "durationFast": "150ms",
        "durationNormal": "300ms",
        "durationSlow": "500ms",
        # Fade and slide animations
        "fadeInSlide": {
            "from": {"opacity": 0, "transform": "translateY(20px)"},
            "to": {"opacity": 1, "transform": "translateY(0)"},
        },
        "fadeOutSlide": {
            "from": {"opacity": 1, "transform": "translateY(0)"},
            "to": {"opacity": 0, "transform": "translateY(-20px)"},
        },
    }

    # Component-specific tokens
    COMPONENTS = {
        "chatBubble": {
            "user": {
                "background": "#6D28D9",
                "textColor": "#FFFFFF",
                "borderRadius": "1.25rem 1.25rem 0.25rem 1.25rem",
            },
            "assistant": {
                "background": "#1a1a2e",
                "textColor": "#FFFFFF",
                "borderRadius": "1.25rem 1.25rem 1.25rem 0.25rem",
            },
            "system": {
                "background": "#374151",
                "textColor": "#D1D5DB",
                "borderRadius": "0.75rem",
            },
        },
        "button": {
            "primary": {
                "background": "#6D28D9",
                "backgroundHover": "#7C3AED",
                "backgroundActive": "#5B21B6",
                "textColor": "#FFFFFF",
                "borderRadius": "0.75rem",
                "padding": "0.75rem 1.5rem",
                "fontWeight": 600,
            },
            "secondary": {
                "background": "#1a1a2e",
                "backgroundHover": "#374151",
                "backgroundActive": "#4B5563",
                "textColor": "#FFFFFF",
                "borderRadius": "0.75rem",
                "padding": "0.75rem 1.5rem",
                "fontWeight": 500,
            },
        },
        "input": {
            "background": "#1a1a2e",
            "backgroundFocus": "#374151",
            "textColor": "#FFFFFF",
            "placeholderColor": "#9CA3AF",
            "borderColor": "#374151",
            "borderColorFocus": "#6D28D9",
            "borderRadius": "0.5rem",
            "padding": "0.75rem 1rem",
        },
    }

    @classmethod
    def get_gradient_css(cls, gradient_name: str) -> str:
        """Get CSS gradient string"""
        if gradient_name == "background":
            colors = cls.COLORS["backgroundGradient"]
            return f"linear-gradient(135deg, {colors[0]} 0%, {colors[1]} 50%, {colors[2]} 100%)"
        elif gradient_name == "accent":
            return f"linear-gradient(135deg, {cls.COLORS['accentViolet']} 0%, {cls.COLORS['accentCyan']} 100%)"
        return ""

    @classmethod
    def get_component_style(
        cls, component: str, variant: str = "default"
    ) -> dict[str, Any]:
        """Get component style configuration"""
        if component in cls.COMPONENTS:
            if variant in cls.COMPONENTS[component]:
                return cls.COMPONENTS[component][variant]
            elif "default" in cls.COMPONENTS[component]:
                return cls.COMPONENTS[component]["default"]
        return {}

    @classmethod
    def get_tkinter_color(cls, color_name: str) -> str:
        """Convert color name to Tkinter-compatible format"""
        if color_name in cls.COLORS:
            return cls.COLORS[color_name]
        return "#000000"  # Fallback to black


# Global instance
design_tokens = DesignTokens()
