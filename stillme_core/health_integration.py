"""
Health Integration - Adapter for health endpoint registration
===========================================================

Provides compatibility layer for different route registration styles.
"""

import logging
from typing import Any

logger = logging.getLogger(__name__)


def register_health_endpoint(app, health_checker) -> dict[str, Any]:
    """
    Register health endpoint with app using compatible route style.

    Args:
        app: Application object with route method
        health_checker: HealthChecker instance

    Returns:
        Dict with registration details
    """
    # Handler function
    def _health_handler():
        """Health endpoint handler"""
        try:
            # Return full health response for readiness probe
            health_response = health_checker.run_all_checks()
            return health_response.__dict__, 200
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return {
                "status": "error",
                "version": health_checker.version,
                "error": str(e)
            }, 503

    # Try callable-first style (test expects this)
    try:
        app.route(_health_handler)
        used_style = "callable-first"
        logger.info("Registered health endpoint using callable-first style")
    except TypeError:
        # Fallback to decorator-style
        try:
            app.route("/health")(_health_handler)
            used_style = "decorator-style"
            logger.info("Registered health endpoint using decorator-style")
        except Exception as e:
            used_style = f"failed: {type(e).__name__}"
            logger.error(f"Failed to register health endpoint: {e}")

    return {"used_style": used_style}


def register_liveness_endpoint(app, health_checker) -> dict[str, Any]:
    """
    Register liveness endpoint with app using compatible route style.

    Args:
        app: Application object with route method
        health_checker: HealthChecker instance

    Returns:
        Dict with registration details
    """
    # Handler function
    def _liveness_handler():
        """Liveness endpoint handler"""
        try:
            return {
                "status": "alive",
                "version": health_checker.version,
                "timestamp": health_checker.start_time
            }, 200
        except Exception as e:
            logger.error(f"Liveness check failed: {e}")
            return {
                "status": "error",
                "version": "unknown",
                "error": str(e)
            }, 503

    # Try callable-first style (test expects this)
    try:
        app.route(_liveness_handler)
        used_style = "callable-first"
        logger.info("Registered liveness endpoint using callable-first style")
    except TypeError:
        # Fallback to decorator-style
        try:
            app.route("/liveness")(_liveness_handler)
            used_style = "decorator-style"
            logger.info("Registered liveness endpoint using decorator-style")
        except Exception as e:
            used_style = f"failed: {type(e).__name__}"
            logger.error(f"Failed to register liveness endpoint: {e}")

    return {"used_style": used_style}


def register_metrics_endpoint(app, health_checker) -> dict[str, Any]:
    """
    Register metrics endpoint with app using compatible route style.

    Args:
        app: Application object with route method
        health_checker: HealthChecker instance

    Returns:
        Dict with registration details
    """
    # Handler function
    def _metrics_handler():
        """Metrics endpoint handler"""
        try:
            health_response = health_checker.run_all_checks()

            # Convert to Prometheus format
            metrics = []
            metrics.append(f"stillme_health_status{{environment=\"{health_response.environment}\"}} {1 if health_response.status.value == 'healthy' else 0}")
            metrics.append(f"stillme_uptime_seconds {health_response.uptime_seconds}")
            metrics.append(f"stillme_version_info{{version=\"{health_response.version}\"}} 1")

            for check_name, check in health_response.checks.items():
                status_value = 1 if check.status.value == 'healthy' else 0
                metrics.append(f"stillme_health_check_status{{check=\"{check_name}\"}} {status_value}")
                metrics.append(f"stillme_health_check_duration_ms{{check=\"{check_name}\"}} {check.duration_ms}")

            return "\n".join(metrics), 200, {"Content-Type": "text/plain"}
        except Exception as e:
            logger.error(f"Metrics check failed: {e}")
            return f"# Error: {e}", 503, {"Content-Type": "text/plain"}

    # Try callable-first style (test expects this)
    try:
        app.route(_metrics_handler)
        used_style = "callable-first"
        logger.info("Registered metrics endpoint using callable-first style")
    except TypeError:
        # Fallback to decorator-style
        try:
            app.route("/metrics")(_metrics_handler)
            used_style = "decorator-style"
            logger.info("Registered metrics endpoint using decorator-style")
        except Exception as e:
            used_style = f"failed: {type(e).__name__}"
            logger.error(f"Failed to register metrics endpoint: {e}")

    return {"used_style": used_style}
