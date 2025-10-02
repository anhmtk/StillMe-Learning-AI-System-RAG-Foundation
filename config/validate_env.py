#!/usr/bin/env python3
"""
StillMe Environment Validation
Kiểm tra các API keys và cấu hình khi khởi động
"""
import logging
import os

from dotenv import load_dotenv

logger = logging.getLogger(__name__)

class EnvironmentValidator:
    """Validator cho environment variables"""

    def __init__(self):
        # Load .env file
        load_dotenv()

        # Required API keys cho internet access
        self.required_keys = {
            "NEWSAPI_KEY": "News API cho tin tức",
            "GNEWS_API_KEY": "GNews API cho tin tức thay thế",
            "OPENROUTER_API_KEY": "OpenRouter API cho LLM",
            "DEEPSEEK_API_KEY": "DeepSeek Cloud API",
            "OPENAI_API_KEY": "OpenAI API (optional)"
        }

        # Optional keys
        self.optional_keys = {
            "OLLAMA_URL": "Ollama local server URL",
            "REDDIT_CLIENT_ID": "Reddit API client ID",
            "REDDIT_CLIENT_SECRET": "Reddit API client secret",
            "GITHUB_TOKEN": "GitHub API token"
        }

        # Validation results
        self.validation_results: dict[str, bool] = {}
        self.missing_keys: list[str] = []
        self.warnings: list[str] = []

    def validate_all(self) -> tuple[bool, list[str]]:
        """Validate tất cả environment variables"""
        logger.info("🔍 Validating environment variables...")

        all_valid = True

        # Check required keys
        for key, description in self.required_keys.items():
            if self._validate_key(key, description, required=True):
                self.validation_results[key] = True
            else:
                self.validation_results[key] = False
                self.missing_keys.append(key)
                all_valid = False

        # Check optional keys
        for key, description in self.optional_keys.items():
            if self._validate_key(key, description, required=False):
                self.validation_results[key] = True
            else:
                self.validation_results[key] = False
                self.warnings.append(f"Optional key missing: {key} ({description})")

        # Log results
        self._log_validation_results()

        return all_valid, self.missing_keys

    def _validate_key(self, key: str, description: str, required: bool = True) -> bool:
        """Validate một key cụ thể"""
        value = os.getenv(key)

        if not value:
            if required:
                logger.warning(f"❌ Missing required key: {key} ({description})")
            else:
                logger.info(f"ℹ️  Optional key not set: {key} ({description})")
            return False

        # Check if value is not just placeholder
        if value.lower() in ["your_api_key_here", "placeholder", "xxx", "sk-xxx"]:
            if required:
                logger.warning(f"❌ Key {key} contains placeholder value: {value}")
            else:
                logger.info(f"ℹ️  Key {key} contains placeholder value: {value}")
            return False

        # Check minimum length for API keys
        if "API_KEY" in key and len(value) < 10:
            logger.warning(f"❌ Key {key} seems too short: {len(value)} characters")
            return False

        logger.info(f"✅ Key validated: {key}")
        return True

    def _log_validation_results(self):
        """Log kết quả validation"""
        logger.info("=" * 60)
        logger.info("📋 ENVIRONMENT VALIDATION RESULTS")
        logger.info("=" * 60)

        # Required keys status
        logger.info("🔑 Required API Keys:")
        for key, description in self.required_keys.items():
            status = "✅" if self.validation_results.get(key, False) else "❌"
            logger.info(f"  {status} {key}: {description}")

        # Optional keys status
        logger.info("\n🔧 Optional Configuration:")
        for key, description in self.optional_keys.items():
            status = "✅" if self.validation_results.get(key, False) else "ℹ️ "
            logger.info(f"  {status} {key}: {description}")

        # Summary
        total_required = len(self.required_keys)
        valid_required = sum(1 for k in self.required_keys.keys() if self.validation_results.get(k, False))

        logger.info("\n📊 Summary:")
        logger.info(f"  Required keys: {valid_required}/{total_required}")
        logger.info(f"  Missing keys: {len(self.missing_keys)}")
        logger.info(f"  Warnings: {len(self.warnings)}")

        if self.missing_keys:
            logger.warning(f"\n⚠️  Missing required keys: {', '.join(self.missing_keys)}")
            logger.warning("   Internet access features may be limited.")

        if self.warnings:
            logger.info(f"\nℹ️  Warnings: {len(self.warnings)}")
            for warning in self.warnings:
                logger.info(f"   - {warning}")

        logger.info("=" * 60)

    def get_validation_summary(self) -> dict:
        """Lấy tóm tắt validation results"""
        return {
            "all_valid": len(self.missing_keys) == 0,
            "missing_keys": self.missing_keys,
            "warnings": self.warnings,
            "validation_results": self.validation_results,
            "total_required": len(self.required_keys),
            "valid_required": sum(1 for k in self.required_keys.keys() if self.validation_results.get(k, False))
        }

    def check_internet_access_ready(self) -> bool:
        """Kiểm tra xem có đủ keys để truy cập internet không"""
        internet_keys = ["NEWSAPI_KEY", "GNEWS_API_KEY", "OPENROUTER_API_KEY"]
        return all(self.validation_results.get(key, False) for key in internet_keys)

# Global instance
env_validator = EnvironmentValidator()

def validate_environment() -> tuple[bool, list[str]]:
    """Convenience function để validate environment"""
    return env_validator.validate_all()

def is_internet_access_ready() -> bool:
    """Convenience function để check internet access readiness"""
    return env_validator.check_internet_access_ready()

if __name__ == "__main__":
    # Test validation
    print("🔍 Testing Environment Validation...")
    is_valid, missing = validate_environment()

    if is_valid:
        print("✅ All required environment variables are set!")
    else:
        print(f"❌ Missing {len(missing)} required keys: {', '.join(missing)}")

    print(f"\n🌐 Internet access ready: {is_internet_access_ready()}")

    # Show summary
    summary = env_validator.get_validation_summary()
    print("\n📊 Validation Summary:")
    print(f"  Valid required: {summary['valid_required']}/{summary['total_required']}")
    print(f"  Missing: {len(summary['missing_keys'])}")
    print(f"  Warnings: {len(summary['warnings'])}")
