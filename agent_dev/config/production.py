#!/usr/bin/env python3
"""
AgentDev Production Configuration
=================================

Production configuration for AgentDev Self-Improvement Loop.
"""

import os
from pathlib import Path
from typing import Dict, Any

# Production database configuration
PRODUCTION_DB_CONFIG = {
    "database_url": os.getenv("AGENTDEV_DATABASE_URL", "sqlite:///agentdev_prod.db"),
    "pool_size": int(os.getenv("AGENTDEV_POOL_SIZE", "10")),
    "max_overflow": int(os.getenv("AGENTDEV_MAX_OVERFLOW", "20")),
    "pool_timeout": int(os.getenv("AGENTDEV_POOL_TIMEOUT", "30")),
    "pool_recycle": int(os.getenv("AGENTDEV_POOL_RECYCLE", "3600")),
}

# Self-Improvement Loop configuration
AUTOFIX_CONFIG = {
    "max_tries": int(os.getenv("AGENTDEV_MAX_TRIES", "3")),
    "timeout_seconds": int(os.getenv("AGENTDEV_TIMEOUT", "300")),
    "enable_learning": os.getenv("AGENTDEV_ENABLE_LEARNING", "true").lower() == "true",
    "enable_anomaly_detection": os.getenv("AGENTDEV_ENABLE_ANOMALY", "true").lower()
    == "true",
    "anomaly_threshold": float(os.getenv("AGENTDEV_ANOMALY_THRESHOLD", "10.0")),
}

# Monitoring configuration
MONITORING_CONFIG = {
    "log_level": os.getenv("AGENTDEV_LOG_LEVEL", "INFO"),
    "log_file": os.getenv("AGENTDEV_LOG_FILE", "logs/agentdev_prod.log"),
    "metrics_retention_days": int(os.getenv("AGENTDEV_METRICS_RETENTION", "30")),
    "enable_jsonl_logging": os.getenv("AGENTDEV_JSONL_LOGGING", "true").lower()
    == "true",
}

# Rule engine configuration
RULE_ENGINE_CONFIG = {
    "rules_file": os.getenv("AGENTDEV_RULES_FILE", "rulesets/agentdev_rules.yaml"),
    "enable_rule_learning": os.getenv("AGENTDEV_RULE_LEARNING", "true").lower()
    == "true",
    "rule_priority_threshold": float(os.getenv("AGENTDEV_RULE_THRESHOLD", "0.5")),
    "max_rules_per_run": int(os.getenv("AGENTDEV_MAX_RULES", "10")),
}

# Security configuration
SECURITY_CONFIG = {
    "enable_security_scan": os.getenv("AGENTDEV_SECURITY_SCAN", "true").lower()
    == "true",
    "security_rules_file": os.getenv(
        "AGENTDEV_SECURITY_RULES", "rulesets/security_rules.yaml"
    ),
    "enable_secret_detection": os.getenv("AGENTDEV_SECRET_DETECTION", "true").lower()
    == "true",
}

# CI/CD configuration
CICD_CONFIG = {
    "enable_auto_pr": os.getenv("AGENTDEV_AUTO_PR", "true").lower() == "true",
    "pr_title_template": os.getenv("AGENTDEV_PR_TITLE", "🤖 Autofix: {timestamp}"),
    "pr_body_template": os.getenv("AGENTDEV_PR_BODY", "templates/pr_body.md"),
    "enable_artifacts": os.getenv("AGENTDEV_ARTIFACTS", "true").lower() == "true",
    "artifacts_retention_days": int(os.getenv("AGENTDEV_ARTIFACTS_RETENTION", "30")),
}

# Performance configuration
PERFORMANCE_CONFIG = {
    "max_concurrent_fixes": int(os.getenv("AGENTDEV_MAX_CONCURRENT", "3")),
    "fix_timeout_seconds": int(os.getenv("AGENTDEV_FIX_TIMEOUT", "60")),
    "enable_parallel_processing": os.getenv("AGENTDEV_PARALLEL", "true").lower()
    == "true",
    "memory_limit_mb": int(os.getenv("AGENTDEV_MEMORY_LIMIT", "1024")),
}

# Quality gates
QUALITY_GATES = {
    "min_coverage_overall": float(os.getenv("AGENTDEV_MIN_COVERAGE", "85.0")),
    "min_coverage_touched": float(os.getenv("AGENTDEV_MIN_COVERAGE_TOUCHED", "90.0")),
    "max_pyright_errors": int(os.getenv("AGENTDEV_MAX_PYRIGHT_ERRORS", "0")),
    "max_ruff_errors": int(os.getenv("AGENTDEV_MAX_RUFF_ERRORS", "0")),
    "require_all_tests_pass": os.getenv("AGENTDEV_REQUIRE_ALL_TESTS", "true").lower()
    == "true",
}

# Notification configuration
NOTIFICATION_CONFIG = {
    "enable_slack": os.getenv("AGENTDEV_SLACK_ENABLED", "false").lower() == "true",
    "slack_webhook": os.getenv("AGENTDEV_SLACK_WEBHOOK", ""),
    "enable_email": os.getenv("AGENTDEV_EMAIL_ENABLED", "false").lower() == "true",
    "email_recipients": os.getenv("AGENTDEV_EMAIL_RECIPIENTS", "").split(","),
    "enable_github_comment": os.getenv("AGENTDEV_GITHUB_COMMENT", "true").lower()
    == "true",
}


# Environment validation
def validate_environment() -> Dict[str, Any]:
    """Validate production environment configuration"""
    validation_results = {"valid": True, "errors": [], "warnings": [], "config": {}}

    # Check required environment variables
    required_vars = [
        "AGENTDEV_DATABASE_URL",
        "AGENTDEV_LOG_LEVEL",
    ]

    for var in required_vars:
        if not os.getenv(var):
            validation_results["warnings"].append(
                f"Optional environment variable {var} not set"
            )

    # Validate database URL
    db_url = PRODUCTION_DB_CONFIG["database_url"]
    if not db_url.startswith(("sqlite://", "postgresql://", "mysql://")):
        validation_results["errors"].append("Invalid database URL format")
        validation_results["valid"] = False

    # Validate log level
    log_level = MONITORING_CONFIG["log_level"]
    valid_log_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
    if log_level not in valid_log_levels:
        validation_results["errors"].append(f"Invalid log level: {log_level}")
        validation_results["valid"] = False

    # Validate coverage thresholds
    min_coverage = QUALITY_GATES["min_coverage_overall"]
    if not 0 <= min_coverage <= 100:
        validation_results["errors"].append(
            "Coverage threshold must be between 0 and 100"
        )
        validation_results["valid"] = False

    # Check if log directory exists
    log_file = MONITORING_CONFIG["log_file"]
    log_dir = Path(log_file).parent
    if not log_dir.exists():
        try:
            log_dir.mkdir(parents=True, exist_ok=True)
            validation_results["warnings"].append(f"Created log directory: {log_dir}")
        except Exception as e:
            validation_results["errors"].append(f"Cannot create log directory: {e}")
            validation_results["valid"] = False

    # Validate rules file exists
    rules_file = RULE_ENGINE_CONFIG["rules_file"]
    if not Path(rules_file).exists():
        validation_results["errors"].append(f"Rules file not found: {rules_file}")
        validation_results["valid"] = False

    # Compile configuration
    validation_results["config"] = {
        "database": PRODUCTION_DB_CONFIG,
        "autofix": AUTOFIX_CONFIG,
        "monitoring": MONITORING_CONFIG,
        "rule_engine": RULE_ENGINE_CONFIG,
        "security": SECURITY_CONFIG,
        "cicd": CICD_CONFIG,
        "performance": PERFORMANCE_CONFIG,
        "quality_gates": QUALITY_GATES,
        "notifications": NOTIFICATION_CONFIG,
    }

    return validation_results


# Production deployment helper
def get_production_config() -> Dict[str, Any]:
    """Get validated production configuration"""
    validation = validate_environment()

    if not validation["valid"]:
        raise ValueError(f"Invalid production configuration: {validation['errors']}")

    return validation["config"]


# Health check configuration
HEALTH_CHECK_CONFIG = {
    "database_timeout": 5,
    "rule_engine_timeout": 3,
    "monitoring_timeout": 2,
    "autofix_timeout": 10,
    "enable_health_endpoint": os.getenv("AGENTDEV_HEALTH_ENDPOINT", "true").lower()
    == "true",
    "health_port": int(os.getenv("AGENTDEV_HEALTH_PORT", "8080")),
}

# Export configuration
__all__ = [
    "PRODUCTION_DB_CONFIG",
    "AUTOFIX_CONFIG",
    "MONITORING_CONFIG",
    "RULE_ENGINE_CONFIG",
    "SECURITY_CONFIG",
    "CICD_CONFIG",
    "PERFORMANCE_CONFIG",
    "QUALITY_GATES",
    "NOTIFICATION_CONFIG",
    "HEALTH_CHECK_CONFIG",
    "validate_environment",
    "get_production_config",
]
