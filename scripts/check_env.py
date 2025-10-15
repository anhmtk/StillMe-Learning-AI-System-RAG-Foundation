#!/usr/bin/env python3
"""
Environment Variables Checker
============================

This script checks if all required environment variables are properly set.
It loads the environment hierarchy and reports missing or misconfigured variables.

Security features:
- Masks sensitive values in output
- Reports missing required variables
- Shows optional variables status
- Exits with proper status codes

Usage:
    python scripts/check_env.py
"""

import os
import sys
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(project_root))

try:
    from stillme_core.env_loader import load_env_hierarchy
    load_env_hierarchy()
except ImportError:
    print("Warning: Could not import env_loader, using system environment only")
except Exception as e:
    print(f"Warning: Error loading environment: {e}")


# Required environment variables (must be set)
REQUIRED = [
    "OPENAI_API_KEY",
    "RUNTIME_BASE_URL", 
    "STILLME_DRY_RUN",
    "STILLME_TZ"
]

# Optional environment variables (nice to have)
OPTIONAL = [
    "OPENROUTER_API_KEY",
    "TELEGRAM_BOT_TOKEN",
    "TELEGRAM_CHAT_ID",
    "SMTP_SERVER",
    "SMTP_USERNAME", 
    "SMTP_PASSWORD",
    "ALERT_EMAIL",
    "STILLME_LEARNING_ENABLED",
    "STILLME_ALERTS_ENABLED",
    "STILLME_ALERTS_EMAIL_ENABLED",
    "STILLME_ALERTS_TELEGRAM_ENABLED",
    "STILLME_ALERTS_DESKTOP_ENABLED"
]


def redact_value(value: str) -> str:
    """
    Redact sensitive values for safe display.
    
    Args:
        value: Original value to redact
        
    Returns:
        Redacted value for display
    """
    if not value:
        return ""
    
    # For API keys and tokens, show first 3 and last 2 chars
    if len(value) > 6:
        return f"{value[:3]}…{value[-2:]}"
    else:
        return "***"


def check_environment():
    """
    Check environment variables and report status.
    
    Returns:
        True if all required variables are set, False otherwise
    """
    print("🔍 Environment Variables Check")
    print("=" * 50)
    
    # Check required variables
    missing = [k for k in REQUIRED if not os.getenv(k)]
    
    print("\n📋 REQUIRED VARIABLES:")
    for key in REQUIRED:
        value = os.getenv(key)
        status = "✅" if key not in missing else "❌"
        display_value = redact_value(value) if value else "NOT_SET"
        print(f"  {status} {key} = {display_value}")
    
    # Check optional variables
    print("\n📋 OPTIONAL VARIABLES:")
    for key in OPTIONAL:
        value = os.getenv(key)
        status = "ℹ️" if value else "—"
        display_value = redact_value(value) if value else "NOT_SET"
        print(f"  {status} {key} = {display_value}")
    
    # Summary
    print("\n📊 SUMMARY:")
    print(f"  Required: {len(REQUIRED) - len(missing)}/{len(REQUIRED)} set")
    print(f"  Optional: {len([k for k in OPTIONAL if os.getenv(k)])}/{len(OPTIONAL)} set")
    
    if missing:
        print(f"\n❌ Missing required variables: {', '.join(missing)}")
        print("\n💡 To fix:")
        print("  1. Copy .env.example to .env")
        print("  2. Edit .env with your actual values")
        print("  3. Or create .env.local for local overrides")
        return False
    else:
        print("\n✅ All required environment variables are set!")
        return True


def main():
    """Main entry point."""
    try:
        success = check_environment()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️ Interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
