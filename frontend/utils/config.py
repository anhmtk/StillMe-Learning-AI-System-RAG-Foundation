"""
Configuration settings for the Streamlit frontend
"""

import os
from typing import Dict, Any

# API Configuration
API_BASE_URL = os.getenv("EVOLUTION_API_URL", "http://localhost:8000/api")
REFRESH_INTERVAL = 30  # seconds

# UI Configuration
UI_CONFIG = {
    "theme": {
        "primary_color": "#1f77b4",
        "backgroundColor": "#ffffff",
        "secondaryBackgroundColor": "#f0f2f6",
        "textColor": "#262730",
        "font": "sans serif"
    },
    "layout": {
        "sidebar_width": "expanded",
        "main_max_width": "1200px"
    }
}

# Notification Configuration
NOTIFICATION_CONFIG = {
    "channels": {
        "email": {
            "enabled": False,
            "smtp_server": "smtp.gmail.com",
            "smtp_port": 587,
            "sender_email": "",
            "sender_password": "",
            "admin_emails": ["admin@example.com"]
        },
        "telegram": {
            "enabled": False,
            "bot_token": "",
            "chat_id": ""
        },
        "dashboard": {
            "enabled": True,
            "show_toasts": True
        }
    },
    "triggers": {
        "learning_session_started": True,
        "learning_session_completed": True, 
        "evolution_stage_changed": True,
        "system_errors": True,
        "proposals_need_review": True,
        "community_votes_threshold": True
    }
}

# Evolution Stages Configuration
EVOLUTION_STAGES = {
    "infant": {
        "emoji": "👶",
        "description": "Basic learning capabilities",
        "color": "#ffb3ba"
    },
    "child": {
        "emoji": "🧒", 
        "description": "Expanding knowledge base",
        "color": "#ffdfba"
    },
    "adolescent": {
        "emoji": "👦",
        "description": "Advanced reasoning emerging", 
        "color": "#ffffba"
    },
    "adult": {
        "emoji": "👨",
        "description": "Full cognitive capabilities",
        "color": "#baffc9"
    },
    "expert": {
        "emoji": "🧠",
        "description": "Specialized knowledge domains",
        "color": "#bae1ff"
    },
    "sage": {
        "emoji": "🎓",
        "description": "Wisdom and deep understanding",
        "color": "#d9baff"
    }
}

# Feature Flags
FEATURE_FLAGS = {
    "admin_approval": True,
    "community_voting": True,
    "telegram_notifications": False,
    "email_notifications": False,
    "auto_learning_sessions": True,
    "manual_proposal_approval": True
}
