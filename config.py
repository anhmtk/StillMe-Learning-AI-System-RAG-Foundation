# StillMe V2 Configuration
import os
from typing import List

# =============================================================================
# CORE FRAMEWORK SETTINGS
# =============================================================================

# Dry Run Mode (for testing/development)
STILLME_DRY_RUN = os.getenv("STILLME_DRY_RUN", "1") == "1"

# Router Mode: stub (default), pro (requires stillme-private package)
STILLME_ROUTER_MODE = os.getenv("STILLME_ROUTER_MODE", "stub")

# Careful Mode (extra validation)
STILLME_CAREFUL_MODE = os.getenv("STILLME_CAREFUL_MODE", "false") == "true"

# Data Retention (days)
STILLME_DATA_RETENTION_DAYS = int(os.getenv("STILLME_DATA_RETENTION_DAYS", "30"))

# =============================================================================
# API KEYS (if using external services)
# =============================================================================

# DeepSeek API (for learning and chat)
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "sk-your-actual-deepseek-key")

# OpenAI API
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "sk-your-actual-openai-key")

# Anthropic API
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "sk-ant-xxxx")

# =============================================================================
# RUNTIME SETTINGS
# =============================================================================

# Runtime Base URL
RUNTIME_BASE_URL = os.getenv("RUNTIME_BASE_URL", "http://localhost:8000")

# Logging Level
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

# Privacy Mode: strict, balanced, permissive
PRIVACY_MODE = os.getenv("PRIVACY_MODE", "balanced")

# =============================================================================
# RSS SOURCES FOR LEARNING
# =============================================================================

# RSS Feeds for learning (comma-separated)
RSS_FEEDS = os.getenv("RSS_FEEDS", "https://feeds.bbci.co.uk/news/rss.xml,https://rss.cnn.com/rss/edition.rss,https://feeds.reuters.com/reuters/technologyNews").split(",")

# Learning Topics (comma-separated)
LEARNING_TOPICS = os.getenv("LEARNING_TOPICS", "technology,artificial intelligence,machine learning,programming,software development").split(",")

# =============================================================================
# EVOLUTION SYSTEM SETTINGS
# =============================================================================

# Auto-approval threshold (0.0-1.0)
AUTO_APPROVAL_THRESHOLD = float(os.getenv("AUTO_APPROVAL_THRESHOLD", "0.8"))

# Max proposals per session
MAX_PROPOSALS_PER_SESSION = int(os.getenv("MAX_PROPOSALS_PER_SESSION", "10"))

# Session timeout (minutes)
SESSION_TIMEOUT_MINUTES = int(os.getenv("SESSION_TIMEOUT_MINUTES", "30"))

# Learning history days
LEARNING_HISTORY_DAYS = int(os.getenv("LEARNING_HISTORY_DAYS", "7"))

# =============================================================================
# SECURITY SETTINGS
# =============================================================================

# PII Redaction
ENABLE_PII_REDACTION = os.getenv("ENABLE_PII_REDACTION", "true") == "true"

# Content Filtering
ENABLE_CONTENT_FILTERING = os.getenv("ENABLE_CONTENT_FILTERING", "true") == "true"

# =============================================================================
# PERFORMANCE SETTINGS
# =============================================================================

# Max Concurrent Requests
MAX_CONCURRENT_REQUESTS = int(os.getenv("MAX_CONCURRENT_REQUESTS", "10"))

# Request Timeout (seconds)
REQUEST_TIMEOUT = int(os.getenv("REQUEST_TIMEOUT", "30"))

# =============================================================================
# DEVELOPMENT SETTINGS
# =============================================================================

# Debug Mode
DEBUG = os.getenv("DEBUG", "false") == "true"

# Enable Metrics
ENABLE_METRICS = os.getenv("ENABLE_METRICS", "true") == "true"

# Offline Mode (for testing)
OFFLINE_MODE = os.getenv("OFFLINE_MODE", "false") == "true"

# Mock Providers (for testing)
MOCK_PROVIDERS = os.getenv("MOCK_PROVIDERS", "false") == "true"

# =============================================================================
# NOTIFICATION SETTINGS (Optional)
# =============================================================================

# Email Notifications
SMTP_HOST = os.getenv("SMTP_HOST", "")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USERNAME = os.getenv("SMTP_USERNAME", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
ALERT_EMAIL = os.getenv("ALERT_EMAIL", "")

# Telegram Notifications
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")

# =============================================================================
# EXTERNAL SERVICES (Optional)
# =============================================================================

# News API
NEWSAPI_KEY = os.getenv("NEWSAPI_KEY", "")

# GNews API
GNEWS_API_KEY = os.getenv("GNEWS_API_KEY", "")

# GitHub Token
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")
